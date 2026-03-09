from src.scrapers.base_scraper import BaseScraper
from src.scrapers.amazon_scraper import AmazonScraper

# Returns correct scraper based on the URL domain
def get_scraper(url: str) -> BaseScraper:
    if "amazon" in url:
        return AmazonScraper(url)
    
        
    raise ValueError(f"No scraper found for URL: {url}")