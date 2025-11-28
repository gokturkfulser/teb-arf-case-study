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
        """Extract campaign detail page links"""
        links = []
        if not soup:
            return links
        
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/kampanya" in href or "/campaign" in href.lower():
                full_url = href if href.startswith("http") else f"{config.cepteteb_base_url}{href}"
                links.append(full_url)
        
        return list(set(links))
    
    def extract_campaign_data(self, soup: BeautifulSoup, url: str) -> Optional[CampaignMetadata]:
        """Extract campaign data from detail page"""
        if not soup:
            return None
        
        try:
            title = self._extract_text(soup, ["h1", ".title", ".campaign-title"])
            description = self._extract_text(soup, [".description", ".content", "p"])
            terms = self._extract_text(soup, [".terms", ".conditions", ".sartlar"])
            benefits = self._extract_text(soup, [".benefits", ".faydalar", ".advantages"])
            
            campaign_id = self._extract_id(url, soup)
            
            return CampaignMetadata(
                campaign_id=campaign_id,
                title=title or "Untitled Campaign",
                description=description or "",
                terms=terms,
                benefits=benefits,
                raw_html=str(soup),
                cleaned_text=self._clean_text(soup.get_text())
            )
        except Exception as e:
            logger.error(f"Error extracting campaign data: {e}")
            return None
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selector strategies"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract campaign ID from URL or page"""
        import re
        match = re.search(r"/(\d+)/?$", url)
        if match:
            return match.group(1)
        
        id_element = soup.find(attrs={"data-campaign-id": True})
        if id_element:
            return id_element.get("data-campaign-id")
        
        return url.split("/")[-1].replace(".html", "").replace(".htm", "")
    
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

