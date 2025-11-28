import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Optional
from configs.rag_config import config
from shared.models.rag_models import CampaignMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CEPTETEBScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_campaign_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract campaign detail page links from list page"""
        links = []
        if not soup:
            return links
        
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            link_text = link.get_text(strip=True).lower()
            
            if "/kampanya" in href or "/campaign" in href.lower():
                full_url = href if href.startswith("http") else f"{config.cepteteb_base_url}{href}"
                if full_url not in links:
                    links.append(full_url)
        
        for article in soup.find_all(["article", "div"], class_=lambda x: x and ("campaign" in x.lower() or "kampanya" in x.lower())):
            link_tag = article.find("a", href=True)
            if link_tag:
                href = link_tag.get("href", "")
                if href:
                    full_url = href if href.startswith("http") else f"{config.cepteteb_base_url}{href}"
                    if full_url not in links:
                        links.append(full_url)
        
        return list(set(links))
    
    def extract_campaign_data(self, soup: BeautifulSoup, url: str) -> Optional[CampaignMetadata]:
        """Extract comprehensive campaign data from detail page"""
        if not soup:
            logger.warning(f"Empty soup for URL: {url}")
            return None
        
        try:
            campaign_id = self._extract_id(url, soup)
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            terms = self._extract_terms(soup)
            benefits = self._extract_benefits(soup)
            
            if not title:
                title = self._extract_title_fallback(soup, url)
            
            if not description or len(description.strip()) < 10:
                description = self._extract_description_fallback(soup)
            
            full_text = self._extract_full_content(soup)
            
            if not description and full_text:
                description = full_text[:500]
            
            return CampaignMetadata(
                campaign_id=campaign_id,
                title=title or "Untitled Campaign",
                description=description or "",
                terms=terms,
                benefits=benefits,
                raw_html=str(soup),
                cleaned_text=full_text
            )
        except Exception as e:
            logger.error(f"Error extracting campaign data from {url}: {e}", exc_info=True)
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract campaign title"""
        selectors = ["h1", "h1.title", ".campaign-title", ".title", "article h1", "main h1"]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 3:
                    return text
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract campaign description"""
        description_parts = []
        
        selectors = [".description", ".content", ".campaign-content", "article .content", "main .content"]
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=" ", strip=True)
                if text and len(text) > 20:
                    description_parts.append(text)
        
        if not description_parts:
            paragraphs = soup.find_all("p")
            for p in paragraphs[:5]:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    description_parts.append(text)
        
        return " ".join(description_parts[:3])
    
    def _extract_terms(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract campaign terms and conditions"""
        selectors = [".terms", ".conditions", ".sartlar", ".kampanya-sartlari", "[class*='term']", "[class*='condition']"]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=" ", strip=True)
                if text and len(text) > 10:
                    return text
        
        headings = soup.find_all(["h2", "h3", "h4"])
        for heading in headings:
            text = heading.get_text(strip=True).lower()
            if any(keyword in text for keyword in ["şart", "koşul", "term", "condition"]):
                next_sibling = heading.find_next_sibling()
                if next_sibling:
                    return next_sibling.get_text(separator=" ", strip=True)
        
        return None
    
    def _extract_benefits(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract campaign benefits"""
        selectors = [".benefits", ".faydalar", ".kampanya-faydalari", "[class*='benefit']", "[class*='fayda']"]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=" ", strip=True)
                if text and len(text) > 10:
                    return text
        
        headings = soup.find_all(["h2", "h3", "h4"])
        for heading in headings:
            text = heading.get_text(strip=True).lower()
            if any(keyword in text for keyword in ["fayda", "avantaj", "benefit", "advantage"]):
                next_sibling = heading.find_next_sibling()
                if next_sibling:
                    return next_sibling.get_text(separator=" ", strip=True)
        
        return None
    
    def _extract_title_fallback(self, soup: BeautifulSoup, url: str) -> str:
        """Fallback title extraction"""
        import re
        url_parts = url.split("/")
        last_part = url_parts[-1].replace(".html", "").replace(".htm", "").replace("-", " ").replace("_", " ")
        if last_part and last_part != "kampanya":
            return last_part.title()
        return "Untitled Campaign"
    
    def _extract_description_fallback(self, soup: BeautifulSoup) -> str:
        """Fallback description extraction"""
        paragraphs = soup.find_all("p")
        descriptions = []
        for p in paragraphs[:5]:
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                descriptions.append(text)
        return " ".join(descriptions)
    
    def _extract_full_content(self, soup: BeautifulSoup) -> str:
        """Extract all relevant content from the page"""
        content_parts = []
        
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=lambda x: x and ("content" in x.lower() or "main" in x.lower()))
        
        if main_content:
            for element in main_content.find_all(["p", "div", "li", "span"]):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(text)
        else:
            for element in soup.find_all(["p", "div"]):
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        full_text = " ".join(content_parts)
        return self._clean_text(full_text)
    
    def _extract_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract campaign ID from URL or page"""
        import re
        
        id_element = soup.find(attrs={"data-campaign-id": True})
        if id_element:
            campaign_id = id_element.get("data-campaign-id")
            if campaign_id:
                return str(campaign_id)
        
        match = re.search(r"/(\d+)/?$", url)
        if match:
            return match.group(1)
        
        url_parts = url.split("/")
        last_part = url_parts[-1].replace(".html", "").replace(".htm", "").replace(".php", "")
        
        if last_part and last_part != "kampanya" and last_part != "kampanyalar":
            return last_part
        
        match = re.search(r"kampanya[_-]?([\w-]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"campaign_{url_hash}"
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        return text.strip()
    
    def find_all_campaign_links(self) -> List[str]:
        """Find all campaign links across all pages"""
        all_links = set()
        base_url = f"{config.cepteteb_base_url}{config.campaigns_path}"
        visited_pages = set()
        pages_to_visit = [base_url]
        
        while pages_to_visit:
            current_url = pages_to_visit.pop(0)
            if current_url in visited_pages:
                continue
            
            visited_pages.add(current_url)
            logger.info(f"Scanning page: {current_url}")
            
            soup = self.fetch_page(current_url)
            if not soup:
                continue
            
            links = self.extract_campaign_links(soup)
            all_links.update(links)
            
            next_links = self._find_next_page_links(soup, current_url)
            for next_link in next_links:
                if next_link not in visited_pages:
                    pages_to_visit.append(next_link)
            
            time.sleep(config.scrape_delay)
        
        return list(all_links)
    
    def _find_next_page_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Find pagination links"""
        next_links = []
        base_url = config.cepteteb_base_url
        
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            
            if any(keyword in text for keyword in ["next", "sonraki", "ileri", ">"]) or \
               any(keyword in href.lower() for keyword in ["page", "sayfa", "p="]):
                full_url = href if href.startswith("http") else f"{base_url}{href}"
                if full_url not in next_links:
                    next_links.append(full_url)
        
        return next_links
    
    def scrape_campaigns(self) -> List[CampaignMetadata]:
        """Scrape all campaigns from CEPTETEB"""
        campaigns = []
        
        logger.info("Finding all campaign links...")
        campaign_links = self.find_all_campaign_links()
        logger.info(f"Found {len(campaign_links)} unique campaign links")
        
        for i, link in enumerate(campaign_links, 1):
            logger.info(f"Scraping campaign {i}/{len(campaign_links)}: {link}")
            
            soup = self.fetch_page(link)
            if soup:
                campaign = self.extract_campaign_data(soup, link)
                if campaign:
                    campaigns.append(campaign)
            
            time.sleep(config.scrape_delay)
        
        logger.info(f"Scraped {len(campaigns)} campaigns")
        return campaigns

