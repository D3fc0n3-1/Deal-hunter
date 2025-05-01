import logging
import time
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

# Import config settings needed by platforms
from config_manager import get_scraping_setting, get_float_setting, get_api_key

log = logging.getLogger(__name__)

class BasePlatform(ABC):
    """Abstract Base Class for all platform search modules."""

    def __init__(self, platform_name):
        self.platform_name = platform_name
        self.timeout = get_float_setting('Scraping', 'request_timeout_seconds', 10.0)
        self.delay = get_float_setting('Scraping', 'delay_between_requests_seconds', 2.0)
        self.headers = {'User-Agent': get_scraping_setting('User-Agent', 'Mozilla/5.0')}
        self.session = requests.Session() # Use session for potential cookie handling, connection reuse
        self.session.headers.update(self.headers)

    @abstractmethod
    def search(self, item):
        """
        Searches the platform for the given item.

        Args:
            item (dict): A dictionary containing item details like
                         'name', 'max_price', 'min_seller_rating'.

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  found listing matching the output format:
                  {'platform', 'item', 'title', 'price', 'seller_rating', 'link'}
                  Returns an empty list if no results found or an error occurs.
        """
        pass

    def _make_request(self, url, params=None):
        """Helper method to make HTTP GET requests with error handling and delay."""
        time.sleep(self.delay) # Respectful delay before each request
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            log.debug(f"Successfully fetched URL: {response.url}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[{self.platform_name}] Request failed for {url}: {e}")
            return None
        except Exception as e:
            log.error(f"[{self.platform_name}] An unexpected error occurred during request to {url}: {e}")
            return None

    def _parse_html(self, html_content):
        """Helper method to parse HTML content using BeautifulSoup."""
        if not html_content:
            return None
        try:
            return BeautifulSoup(html_content, 'html.parser') # Or 'lxml' if installed & preferred
        except Exception as e:
            log.error(f"[{self.platform_name}] Error parsing HTML: {e}")
            return None

    def _clean_price(self, price_str):
        """Helper method to clean and convert price string to float."""
        if not price_str:
            return None
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = ''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str).strip()))
            if cleaned:
                return float(cleaned)
            return None
        except (ValueError, TypeError):
            log.warning(f"[{self.platform_name}] Could not parse price: {price_str}")
            return None

    def _apply_filters(self, result, item):
         """Helper method to apply common filters (price). Specific filters (rating) in subclasses."""
         if not result or not isinstance(result, dict):
             return False

         # Price filter (mandatory)
         if result.get('price') is None or result['price'] > item['max_price']:
             log.debug(f"[{self.platform_name}] Filtering out item (price): {result.get('title')} @ {result.get('price')} (Max: {item['max_price']})")
             return False

         # Base implementation assumes other filters are handled by subclasses or not applicable
         return True
