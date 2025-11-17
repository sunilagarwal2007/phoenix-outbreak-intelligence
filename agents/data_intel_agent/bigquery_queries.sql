-- BigQuery SQL queries for Phoenix Outbreak Intelligence
-- Data Intelligence Agent query library

-- Daily case counts with moving averages
-- Query: daily_cases_with_trends
SELECT 
    date,
    location_key,
    subregion1_name as state,
    subregion2_name as county,
    new_confirmed as daily_cases,
    cumulative_confirmed as total_cases,
    population,
    AVG(new_confirmed) OVER (
        PARTITION BY location_key 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as seven_day_avg,
    AVG(new_confirmed) OVER (
        PARTITION BY location_key 
        ORDER BY date 
        ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING
    ) as prev_seven_day_avg,
    SAFE_DIVIDE(new_confirmed, population) * 100000 as cases_per_100k
FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    AND country_code = 'US'
    AND subregion1_name = @state_name
    AND (@county_name IS NULL OR subregion2_name = @county_name)
ORDER BY date DESC, location_key;

-- Test positivity rates and trends
-- Query: positivity_rates_analysis
SELECT 
    date,
    location_key,
    subregion1_name as state,
    subregion2_name as county,
    new_tested as daily_tests,
    new_confirmed as daily_cases,
    cumulative_tested as total_tests,
    cumulative_confirmed as total_cases,
    SAFE_DIVIDE(new_confirmed, new_tested) as daily_positivity,
    AVG(SAFE_DIVIDE(new_confirmed, new_tested)) OVER (
        PARTITION BY location_key 
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as seven_day_positivity,
    -- CDC threshold analysis
    CASE 
        WHEN SAFE_DIVIDE(new_confirmed, new_tested) < 0.05 THEN 'LOW'
        WHEN SAFE_DIVIDE(new_confirmed, new_tested) < 0.10 THEN 'MODERATE'
        ELSE 'HIGH'
    END as cdc_risk_level
FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 21 DAY)
    AND country_code = 'US'
    AND subregion1_name = @state_name
    AND new_tested IS NOT NULL
    AND new_tested > 0
    AND (@county_name IS NULL OR subregion2_name = @county_name)
ORDER BY date DESC, location_key;

-- Hospital capacity and ICU utilization
-- Query: hospital_capacity_analysis
WITH hospital_metrics AS (
    SELECT 
        date,
        subregion1_name as state,
        subregion2_name as county,
        hospitalized_patients_covid as covid_hospitalized,
        icu_patients_covid as covid_icu,
        -- Estimate total capacity (actual data may require different source)
        COALESCE(hospitalized_patients_covid, 0) + 
        COALESCE(icu_patients_covid, 0) * 4 as estimated_total_beds,
        icu_patients_covid * 1.5 as estimated_total_icu
    FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
    WHERE country_code = 'US'
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
        AND subregion1_name = @state_name
        AND (@county_name IS NULL OR subregion2_name = @county_name)
        AND (hospitalized_patients_covid IS NOT NULL 
             OR icu_patients_covid IS NOT NULL)
)
SELECT 
    date,
    state,
    county,
    covid_hospitalized,
    covid_icu,
    estimated_total_beds,
    estimated_total_icu,
    SAFE_DIVIDE(covid_icu, estimated_total_icu) as icu_occupancy_rate,
    CASE 
        WHEN SAFE_DIVIDE(covid_icu, estimated_total_icu) > 0.85 THEN 'CRITICAL'
        WHEN SAFE_DIVIDE(covid_icu, estimated_total_icu) > 0.70 THEN 'HIGH'
        WHEN SAFE_DIVIDE(covid_icu, estimated_total_icu) > 0.50 THEN 'MODERATE'
        ELSE 'LOW'
    END as capacity_strain_level
FROM hospital_metrics
ORDER BY date DESC, state, county;

-- Vaccination coverage analysis
-- Query: vaccination_coverage
SELECT 
    date,
    location_key,
    subregion1_name as state,
    subregion2_name as county,
    cumulative_persons_vaccinated as total_vaccinated,
    cumulative_persons_fully_vaccinated as fully_vaccinated,
    cumulative_vaccine_doses_administered as total_doses,
    population,
    SAFE_DIVIDE(cumulative_persons_vaccinated, population) as vaccination_rate,
    SAFE_DIVIDE(cumulative_persons_fully_vaccinated, population) as full_vaccination_rate,
    -- Herd immunity estimation (simplified)
    CASE 
        WHEN SAFE_DIVIDE(cumulative_persons_fully_vaccinated, population) > 0.70 THEN 'HIGH_PROTECTION'
        WHEN SAFE_DIVIDE(cumulative_persons_fully_vaccinated, population) > 0.50 THEN 'MODERATE_PROTECTION'
        ELSE 'LOW_PROTECTION'
    END as community_immunity_level
FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
WHERE country_code = 'US'
    AND date = (SELECT MAX(date) FROM `bigquery-public-data.covid19_open_data.covid19_open_data`)
    AND subregion1_name = @state_name
    AND (@county_name IS NULL OR subregion2_name = @county_name)
    AND cumulative_persons_vaccinated IS NOT NULL
ORDER BY vaccination_rate DESC;

-- Growth rate and acceleration analysis
-- Query: outbreak_acceleration_detection
WITH daily_metrics AS (
    SELECT 
        date,
        location_key,
        subregion1_name as state,
        subregion2_name as county,
        new_confirmed as daily_cases,
        AVG(new_confirmed) OVER (
            PARTITION BY location_key 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as seven_day_avg,
        LAG(AVG(new_confirmed) OVER (
            PARTITION BY location_key 
            ORDER BY date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 7) OVER (PARTITION BY location_key ORDER BY date) as prev_seven_day_avg
    FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
    WHERE country_code = 'US'
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 21 DAY)
        AND subregion1_name = @state_name
        AND (@county_name IS NULL OR subregion2_name = @county_name)
)
SELECT 
    date,
    state,
    county,
    daily_cases,
    seven_day_avg,
    prev_seven_day_avg,
    SAFE_DIVIDE(
        (seven_day_avg - prev_seven_day_avg), 
        NULLIF(prev_seven_day_avg, 0)
    ) as week_over_week_growth,
    CASE 
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > 0.20 
        THEN 'RAPID_ACCELERATION'
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > 0.10 
        THEN 'MODERATE_GROWTH'
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > -0.10 
        THEN 'STABLE'
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > -0.20 
        THEN 'DECLINING'
        ELSE 'RAPID_DECLINE'
    END as trend_classification,
    -- Outbreak probability scoring
    CASE 
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > 0.15 
             AND seven_day_avg > 10 THEN 85
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > 0.10 
             AND seven_day_avg > 5 THEN 70
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > 0.05 THEN 50
        WHEN SAFE_DIVIDE((seven_day_avg - prev_seven_day_avg), prev_seven_day_avg) > -0.05 THEN 30
        ELSE 15
    END as outbreak_probability_score
FROM daily_metrics
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY date DESC, outbreak_probability_score DESC;

-- Multi-variant surveillance (if variant data available)
-- Query: variant_surveillance
SELECT 
    date,
    location_key,
    subregion1_name as state,
    subregion2_name as county,
    -- Note: Variant data might be in separate tables/datasets
    -- This is a template for when variant tracking is available
    'COVID-19' as pathogen,
    'Multiple' as variant_detected,
    new_confirmed as total_cases,
    -- Placeholder for variant-specific data
    NULL as dominant_variant,
    NULL as variant_percentage
FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
WHERE country_code = 'US'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND subregion1_name = @state_name
    AND (@county_name IS NULL OR subregion2_name = @county_name)
ORDER BY date DESC;

-- Regional comparison analysis
-- Query: regional_outbreak_comparison
WITH state_summary AS (
    SELECT 
        subregion1_name as state,
        AVG(new_confirmed) as avg_daily_cases,
        SUM(population) as total_population,
        AVG(SAFE_DIVIDE(new_confirmed, population) * 100000) as cases_per_100k
    FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
    WHERE country_code = 'US'
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND subregion1_name IS NOT NULL
    GROUP BY subregion1_name
),
national_avg AS (
    SELECT AVG(cases_per_100k) as national_cases_per_100k
    FROM state_summary
)
SELECT 
    s.state,
    s.avg_daily_cases,
    s.total_population,
    s.cases_per_100k,
    n.national_cases_per_100k,
    SAFE_DIVIDE(s.cases_per_100k, n.national_cases_per_100k) as relative_risk_ratio,
    CASE 
        WHEN s.cases_per_100k > n.national_cases_per_100k * 2 THEN 'WELL_ABOVE_NATIONAL'
        WHEN s.cases_per_100k > n.national_cases_per_100k * 1.5 THEN 'ABOVE_NATIONAL'
        WHEN s.cases_per_100k > n.national_cases_per_100k * 0.75 THEN 'NEAR_NATIONAL'
        ELSE 'BELOW_NATIONAL'
    END as risk_classification
FROM state_summary s
CROSS JOIN national_avg n
WHERE s.state = @state_name
ORDER BY s.cases_per_100k DESC;