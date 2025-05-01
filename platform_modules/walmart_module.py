import logging
from urllib.parse import quote_plus
import json # Walmart sometimes embeds data in JSON within script tags

from .base_platform import BasePlatform

log = logging.getLogger(__name__)

# --- Configuration ---
WALMART_SEARCH_URL_TEMPLATE = "https://www.walmart.com/search?q={query}"

# --- Selectors (LIKELY TO BREAK - Walmart uses complex/dynamic classes) ---
# These require inspection of Walmart's search results. They change frequently.
# Option 1: Find JSON data embedded in script tags (often more stable if available)
SCRIPT_SELECTOR = "script[type='application/json']" # Look for scripts containing product data

# Option 2: Direct element scraping (less reliable)
# These are illustrative examples ONLY
RESULT_ITEM_SELECTOR = "div[data-item-id]" # Or similar identifying attribute
TITLE_SELECTOR = "span[data-automation-id='product-title']" # Check dev tools
PRICE_SELECTOR = "div[data-automation-id='product-price'] .f1" # Example, find actual price element
LINK_SELECTOR = "a[link-identifier]" # Example, find actual link element


class WalmartPlatform(BasePlatform):
    """Walmart search implementation (using scraping - unstable)."""

    def __init__(self):
        super().__init__("Walmart")
        log.warning("[Walmart] Scraping Walmart is unreliable and may be blocked. Use with caution.")

    def search(self, item):
        """Searches Walmart for the item using web scraping."""
        search_term = item['name']
        max_price = item['max_price']
        # Seller rating not typically available on search page

        query = quote_plus(search_term)
        search_url = WALMART_SEARCH_URL_TEMPLATE.format(query=query)
        log.info(f"[Walmart] Searching for '{search_term}' (Max Price: ${max_price})")
        log.debug(f"[Walmart] Search URL: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return []

        # Check for blocking/errors
        if "error" in response.url.lower() or response.status_code != 200:
             log.error(f"[Walmart] Received status {response.status_code} or redirected to error page. Scraping failed.")
             return []

        soup = self._parse_html(response.text)
        if not soup:
            return []

        results = []

        # --- Strategy 1: Look for embedded JSON data (preferred if found) ---
        found_json = False
        scripts = soup.select(SCRIPT_SELECTOR)
        for script in scripts:
            try:
                # Check if script likely contains search results (e.g., look for keywords)
                if 'searchContent' in script.text:
                     data = json.loads(script.text)
                     # Navigate the JSON structure (requires inspection in browser tools)
                     # This path is HYPOTHETICAL and needs validation
                     items_data = data.get('searchContent', {}).get('preso', {}).get('items', [])
                     if items_data:
                         log.info(f"[Walmart] Found {len(items_data)} items in embedded JSON.")
                         for item_data in items_data:
                             try:
                                 title = item_data.get('title', '').strip()
                                 # Extract price - structure varies, might be under 'primaryOffer' etc.
                                 price_info = item_data.get('primaryOffer', {})
                                 price = self._clean_price(price_info.get('offerPrice') or price_info.get('minPrice'))

                                 link_path = item_data.get('canonicalUrl')
                                 link = f"https://www.walmart.com{link_path}" if link_path else None

                                 if not title or price is None or not link:
                                     continue

                                 result = {
                                     "platform": self.platform_name, "item": search_term,
                                     "title": title, "price": price,
                                     "seller_rating": None, "link": link
                                 }
                                 if self._apply_filters(result, item):
                                     results.append(result)

                             except Exception as e:
                                 log.warning(f"[Walmart] Error processing item from JSON data: {e}")
                         found_json = True
                         break # Stop after finding the relevant script
            except json.JSONDecodeError:
                continue # Not the JSON we are looking for
            except Exception as e:
                log.error(f"[Walmart] Error processing script tag: {e}")

        # --- Strategy 2: Direct HTML element scraping (fallback if JSON fails) ---
        if not found_json:
            log.warning("[Walmart] Embedded JSON data not found or failed to parse. Falling back to direct HTML scraping (less reliable).")
            list_items = soup.select(RESULT_ITEM_SELECTOR)
            log.info(f"[Walmart] Found {len(list_items)} potential listings via HTML selectors.")

            if not list_items and not found_json:
                log.warning(f"[Walmart] No items found using selector '{RESULT_ITEM_SELECTOR}'. Structure might have changed.")

            for list_item in list_items:
                try:
                    title_element = list_item.select_one(TITLE_SELECTOR)
                    price_element = list_item.select_one(PRICE_SELECTOR) # This might get complex (current, was, unit price)
                    link_element = list_item.select_one(LINK_SELECTOR)

                    title = title_element.get_text(strip=True) if title_element else "N/A"
                    link = None
                    if link_element and link_element.has_attr('href'):
                         href = link_element['href']
                         link = f"https://www.walmart.com{href}" if href.startswith('/') else href

                    price = None
                    if price_element:
                        # Price extraction needs careful handling of structure (e.g., "$199.99", "$19999")
                        price_str = price_element.get_text(strip=True)
                        price = self._clean_price(price_str)

                    if title == "N/A" or price is None or link is None:
                        log.debug(f"[Walmart] Skipping item due to missing data (HTML scrape): Title={title}, Price={price}, Link={link}")
                        continue

                    result = {
                        "platform": self.platform_name, "item": search_term,
                        "title": title, "price": price,
                        "seller_rating": None, "link": link
                    }

                    if self._apply_filters(result, item):
                         results.append(result)

                except Exception as e:
                    log.warning(f"[Walmart] Error processing a listing item (HTML scrape): {e}", exc_info=False)
                    continue

        log.info(f"[Walmart] Found {len(results)} relevant listings for '{search_term}' after filtering.")
        return results
