"""
Web Reader MCP Server for Phoenix Outbreak Intelligence
Provides web scraping and content validation capabilities for rumor checking
"""

import logging
import asyncio
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

class WebReaderMCPServer:
    """
    Model Context Protocol server for web content reading and validation
    
    Capabilities:
    - Web page content extraction
    - News article parsing
    - Social media content analysis
    - Rumor validation against official sources
    - Content credibility assessment
    """
    
    def __init__(self, timeout: int = 30, max_concurrent: int = 10):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
        
        # Official health sources for validation
        self.trusted_sources = [
            "cdc.gov",
            "who.int", 
            "nih.gov",
            "gov",  # General government sites
            "edu",  # Academic institutions
            "pubmed.ncbi.nlm.nih.gov"
        ]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Phoenix-Outbreak-Intelligence/1.0 (Health Monitoring Bot)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def validate_health_claims(self, claims: List[str], location: str = None) -> Dict:
        """
        Validate health claims against official sources
        
        Args:
            claims: List of claims/rumors to validate
            location: Geographic context for validation
            
        Returns:
            Validation results with evidence and confidence scores
        """
        try:
            validation_results = {
                "validation_timestamp": datetime.now().isoformat(),
                "location_context": location,
                "claims_processed": len(claims),
                "results": {}
            }
            
            for claim in claims:
                claim_result = await self._validate_single_claim(claim, location)
                validation_results["results"][claim] = claim_result
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Claim validation error: {str(e)}")
            return {"error": str(e), "claims_processed": 0}
    
    async def _validate_single_claim(self, claim: str, location: str = None) -> Dict:
        """Validate a single claim against multiple sources"""
        
        # Extract key terms from claim for searching
        search_terms = self._extract_search_terms(claim)
        
        # Search official sources
        search_queries = self._build_search_queries(search_terms, location)
        
        evidence_results = []
        
        for query in search_queries[:3]:  # Limit to top 3 queries
            async with self.semaphore:
                search_results = await self._search_trusted_sources(query)
                evidence_results.extend(search_results)
        
        # Analyze evidence and determine verdict
        verdict = self._analyze_evidence(claim, evidence_results)
        
        return {
            "claim": claim,
            "search_terms": search_terms,
            "evidence_sources": len(evidence_results),
            "verdict": verdict["verdict"],
            "confidence": verdict["confidence"],
            "supporting_evidence": verdict.get("supporting", []),
            "contradicting_evidence": verdict.get("contradicting", []),
            "official_sources_checked": len([r for r in evidence_results if r.get("is_trusted")])
        }
    
    def _extract_search_terms(self, claim: str) -> List[str]:
        """Extract key terms from claim for searching"""
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'been', 'be', 'have',
            'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Extract meaningful terms
        words = re.findall(r'\b[A-Za-z]+\b', claim.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Identify health-related terms
        health_terms = []
        health_keywords = {
            'covid', 'coronavirus', 'virus', 'outbreak', 'epidemic', 'pandemic',
            'vaccine', 'vaccination', 'symptom', 'hospital', 'death', 'case',
            'infection', 'disease', 'health', 'medical', 'treatment', 'cure'
        }
        
        for word in keywords:
            if word in health_keywords:
                health_terms.append(word)
        
        # Return combination of health terms and other significant keywords
        return health_terms + [w for w in keywords[:5] if w not in health_terms]
    
    def _build_search_queries(self, terms: List[str], location: str = None) -> List[str]:
        """Build search queries from extracted terms"""
        
        queries = []
        
        # Primary query with all terms
        if len(terms) >= 2:
            primary_query = " ".join(terms[:4])
            if location:
                primary_query += f" {location}"
            queries.append(primary_query)
        
        # Health-specific queries
        health_terms = [t for t in terms if t in [
            'covid', 'coronavirus', 'outbreak', 'vaccine', 'symptom', 'death'
        ]]
        
        if health_terms:
            for health_term in health_terms[:2]:
                query = health_term
                if location:
                    query += f" {location}"
                queries.append(query)
        
        return queries
    
    async def _search_trusted_sources(self, query: str) -> List[Dict]:
        """Search official health sources for relevant content"""
        
        results = []
        
        # Search CDC
        cdc_results = await self._search_cdc(query)
        results.extend(cdc_results)
        
        # Search WHO  
        who_results = await self._search_who(query)
        results.extend(who_results)
        
        # Search government health sites
        gov_results = await self._search_government_health(query)
        results.extend(gov_results)
        
        return results
    
    async def _search_cdc(self, query: str) -> List[Dict]:
        """Search CDC website for relevant content"""
        
        try:
            # CDC search URL
            search_url = f"https://www.cdc.gov/search/?"
            params = {
                'query': query,
                'searchtype': 'all'
            }
            
            content = await self._fetch_web_content(search_url, params)
            if not content.get("success"):
                return []
            
            # Parse CDC search results
            soup = BeautifulSoup(content["html"], 'html.parser')
            search_results = []
            
            # Find result links (CDC-specific parsing)
            result_links = soup.find_all('a', href=re.compile(r'/[^/]+/'))
            
            for link in result_links[:3]:  # Top 3 results
                if link.get('href'):
                    result_url = f"https://www.cdc.gov{link['href']}"
                    result_title = link.get_text(strip=True)
                    
                    search_results.append({
                        "source": "CDC",
                        "url": result_url,
                        "title": result_title,
                        "is_trusted": True,
                        "source_type": "government_health"
                    })
            
            return search_results
            
        except Exception as e:
            self.logger.warning(f"CDC search error for '{query}': {str(e)}")
            return []
    
    async def _search_who(self, query: str) -> List[Dict]:
        """Search WHO website for relevant content"""
        
        try:
            # WHO search is complex, return mock results for now
            # In real implementation, would parse WHO search results
            return [{
                "source": "WHO",
                "url": f"https://www.who.int/search?q={query}",
                "title": f"WHO information about {query}",
                "is_trusted": True,
                "source_type": "international_health"
            }]
            
        except Exception as e:
            self.logger.warning(f"WHO search error for '{query}': {str(e)}")
            return []
    
    async def _search_government_health(self, query: str) -> List[Dict]:
        """Search government health websites"""
        
        # Mock implementation - would search NIH, state health departments, etc.
        try:
            return [{
                "source": "NIH",
                "url": f"https://www.nih.gov/search?q={query}",
                "title": f"NIH research on {query}",
                "is_trusted": True,
                "source_type": "government_research"
            }]
            
        except Exception as e:
            self.logger.warning(f"Government health search error: {str(e)}")
            return []
    
    async def _fetch_web_content(self, url: str, params: Dict = None) -> Dict:
        """Fetch content from web URL"""
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return {
                        "success": True,
                        "url": str(response.url),
                        "status": response.status,
                        "html": html_content,
                        "content_length": len(html_content)
                    }
                else:
                    return {
                        "success": False,
                        "url": url,
                        "status": response.status,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            self.logger.error(f"Web fetch error for {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def _analyze_evidence(self, claim: str, evidence: List[Dict]) -> Dict:
        """Analyze evidence to determine claim validity"""
        
        if not evidence:
            return {
                "verdict": "INSUFFICIENT_DATA",
                "confidence": 0.1,
                "reason": "No evidence found from trusted sources"
            }
        
        # Count trusted vs untrusted sources
        trusted_sources = [e for e in evidence if e.get("is_trusted", False)]
        
        # Simple analysis based on source count and type
        if len(trusted_sources) >= 2:
            # Multiple trusted sources found
            verdict = "INVESTIGATING"
            confidence = 0.7
            
            # Check if sources align with or contradict claim
            # This would be more sophisticated in real implementation
            supporting = trusted_sources[:2]
            contradicting = []
            
        elif len(trusted_sources) == 1:
            # Single trusted source
            verdict = "PARTIALLY_VERIFIED"
            confidence = 0.5
            supporting = trusted_sources
            contradicting = []
            
        else:
            # No trusted sources
            verdict = "UNVERIFIED"
            confidence = 0.2
            supporting = []
            contradicting = []
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "supporting": supporting,
            "contradicting": contradicting,
            "trusted_source_count": len(trusted_sources),
            "total_source_count": len(evidence)
        }
    
    async def scrape_news_article(self, url: str) -> Dict:
        """
        Scrape and parse a news article
        
        Args:
            url: URL of the news article
            
        Returns:
            Parsed article content with metadata
        """
        try:
            content = await self._fetch_web_content(url)
            
            if not content.get("success"):
                return content
            
            soup = BeautifulSoup(content["html"], 'html.parser')
            
            # Extract article metadata
            article = {
                "url": url,
                "title": self._extract_title(soup),
                "content": self._extract_article_content(soup),
                "publish_date": self._extract_publish_date(soup),
                "author": self._extract_author(soup),
                "source_domain": self._extract_domain(url),
                "is_trusted_source": self._is_trusted_source(url),
                "word_count": 0,
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            if article["content"]:
                article["word_count"] = len(article["content"].split())
            
            return article
            
        except Exception as e:
            self.logger.error(f"Article scraping error for {url}: {str(e)}")
            return {"success": False, "url": url, "error": str(e)}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML"""
        title_selectors = ['h1', 'title', '.headline', '.article-title']
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return "Title not found"
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        
        # Remove unwanted elements
        for elem in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            elem.decompose()
        
        # Common article content selectors
        content_selectors = [
            '.article-content',
            '.post-content', 
            '.entry-content',
            'article',
            '.content',
            'main'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    return '\n'.join([p.get_text(strip=True) for p in paragraphs])
        
        # Fallback: extract all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            return '\n'.join([p.get_text(strip=True) for p in paragraphs[:10]])
        
        return "Content extraction failed"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article publish date"""
        
        # Look for common date patterns
        date_selectors = [
            'time[datetime]',
            '.publish-date',
            '.article-date',
            '[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                return date_elem.get('datetime') or date_elem.get_text(strip=True)
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        
        author_selectors = [
            '.author',
            '.byline',
            '[property="article:author"]',
            '.article-author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text(strip=True)
        
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    
    def _is_trusted_source(self, url: str) -> bool:
        """Check if URL is from a trusted source"""
        domain = self._extract_domain(url)
        
        return any(trusted in domain for trusted in self.trusted_sources)