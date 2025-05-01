import logging
from urllib.parse import quote_plus
import re # For extracting price from complex strings

# Ensure these imports are correct relative to this file's location
from .base_platform import BasePlatform
# from search_enhancer import check_title_relevance # Optional relevance check

log = logging.getLogger(__name__)

# --- Configuration ---
AMAZON_SEARCH_URL_TEMPLATE = "https://www.amazon.com/s?k={query}"

# --- Selectors (EXTREMELY LIKELY TO BREAK - These are examples ONLY) ---
RESULT_ITEM_SELECTOR = "div[data-component-type='s-search-result']"
TITLE_SELECTOR = "h2 a span.a-text-normal"
PRICE_WHOLE_SELECTOR = "span.a-price-whole"
PRICE_FRACTION_SELECTOR = "span.a-price-fraction"
LINK_SELECTOR = "h2 a.a-link-normal"

# --- Ensure class name is exactly AmazonPlatform ---
class AmazonPlatform(BasePlatform):
    """Amazon search implementation (using scraping - unstable)."""

    def __init__(self):
        super().__init__("Amazon")
        log.warning("[Amazon] Scraping Amazon is highly unreliable and may be blocked or return incorrect results. Selectors need frequent updates.")

    def search(self, item):
        """Searches Amazon for the item using web scraping."""
        search_term = item['name']
        max_price = item['max_price']

        query = quote_plus(search_term)
        search_url = AMAZON_SEARCH_URL_TEMPLATE.format(query=query)
        log.info(f"[Amazon] Searching for '{search_term}' (Max Price: ${max_price})")
        log.debug(f"[Amazon] Search URL: {search_url}")

        # Use headers defined in BasePlatform session
        response = self._make_request(search_url)
        if not response:
            return []

        if "captcha" in response.text.lower() or "robot check" in response.text.lower():
             log.error("[Amazon] Blocked by CAPTCHA or robot check. Scraping failed.")
             # Consider adding response.url to the log to see where it redirected
             log.debug(f"[Amazon] Blocked URL: {response.url}")
             return []

        soup = self._parse_html(response.text)
        if not soup:
            return []

        results = []
        list_items = soup.select(RESULT_ITEM_SELECTOR)
        log.info(f"[Amazon] Found {len(list_items)} potential listings on page using selector '{RESULT_ITEM_SELECTOR}'.")

        if not list_items:
             log.warning(f"[Amazon] No items found using selector '{RESULT_ITEM_SELECTOR}'. Amazon structure might have changed, or you might be blocked.")

        for list_item in list_items:
            try:
                # Check if it's an Ad / Sponsored item first (these often have different structures)
                # This selector needs verification by inspecting Amazon's HTML for ads
                sponsored_label = list_item.select_one('span[data-component-type="s-ads-indicator-text"]')
                if sponsored_label:
                     log.debug("[Amazon] Skipping sponsored listing.")
                     continue

                title_element = list_item.select_one(TITLE_SELECTOR)
                link_element = list_item.select_one(LINK_SELECTOR)
                price_whole_el = list_item.select_one(PRICE_WHOLE_SELECTOR)
                price_fraction_el = list_item.select_one(PRICE_FRACTION_SELECTOR)

                title = title_element.get_text(strip=True) if title_element else "N/A"
                link = None
                if link_element and link_element.has_attr('href'):
                    href = link_element['href']
                    # Basic check to form absolute URL
                    if href.startswith('/'):
                        link = f"https://www.amazon.com{href}"
                    elif href.startswith('http'):
                        link = href
                    # Add more checks if needed based on observed URL patterns

                price = None
                if price_whole_el and price_fraction_el:
                    # Ensure we extract only digits and decimal point if needed
                    price_str = f"{price_whole_el.get_text(strip=True)}{price_fraction_el.get_text(strip=True)}"
                    price = self._clean_price(price_str)
                else:
                    # Sometimes price might be in a single element, try finding that as a fallback
                    # Example: Look for elements with class 'a-price' containing 'a-offscreen'
                    price_container = list_item.select_one('span.a-price > span.a-offscreen')
                    if price_container:
                        price = self._clean_price(price_container.get_text(strip=True))


                # Skip if essential data is missing after trying to parse
                if title == "N/A" or price is None or link is None:
                    log.debug(f"[Amazon] Skipping item due to missing data: Title='{title}', Price={price}, Link={link}")
                    continue

                result = {
                    "platform": self.platform_name,
                    "item": search_term,
                    "title": title,
                    "price": price,
                    "seller_rating": None, # Not reliably available
                    "link": link
                }

                if self._apply_filters(result, item):
                     results.append(result)

            except Exception as e:
                log.warning(f"[Amazon] Error processing a listing item: {e}", exc_info=False)
                continue

        log.info(f"[Amazon] Found {len(results)} relevant listings for '{search_term}' after filtering.")
        return results