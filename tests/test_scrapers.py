import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.scrapers.amazon_scraper import AmazonScraper

# Upload test data
TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture

# Reads HTML to simulate Amazon's response
def mock_amazon_html():
    html_path = TEST_DATA_DIR / "amazon_product.html"
    if not html_path.exists():
        pytest.skip("No test data found.")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# Returns the HTML
def test_amazon_extraction(mock_amazon_html):
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_amazon_html.encode("utf-8")
        mock_get.return_value = mock_response

        # Execute Scrapper
        scraper = AmazonScraper("https://fake-url.com")
        
        price = scraper.extract_price()
        name = scraper.extract_name()

        print(f"Test Price: {price}")
        print(f"Test Name: {name}")

        assert price > 0, "Price should be greater than 0"
        assert isinstance(name, str)
        assert name != "Unknown Product"
        assert name != "BLOCKED: CAPTCHA DETECTED"