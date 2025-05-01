import logging
from urllib.parse import quote_plus
import json # Best Buy also sometimes uses embedded JSON

from .base_platform import BasePlatform

log = logging.getLogger(__name__)

# --- Configuration ---
BESTBUY_SEARCH_URL_TEMPLATE = "https://www.bestbuy.com/site/searchpage.jsp?st={query}"

# --- Selectors (LIKELY TO BREAK) ---
# Inspect Best Buy's search results. They have complex structures.
# Option 1: Embedded JSON (if available)
SCRIPT_SELECTOR_BB = "script[type='application/ld+json']" # Common for product schema data

# Option 2: Direct HTML scraping
RESULT_ITEM_SELECTOR_BB = "li.sku-item"
TITLE_SELECTOR_BB = "h4.sku-title a"
PRICE_SELECTOR_BB = "div.priceView-hero-price span[aria-hidden='true']" # Select the visually hidden span usually holding the number
LINK_SELECTOR_BB = "h4.sku-title a" # Link is often on the title


class BestbuyPlatform(BasePlatform):
    """Best Buy search implementation (using scraping - unstable)."""

    def __init__(self):
        super().__init__("BestBuy")
        log.warning("[BestBuy] Scraping Best Buy is unreliable and may be blocked. Use with caution.")

    def search(self, item):
        """Searches Best Buy for the item using web scraping."""
        search_term = item['name']
        max_price = item['max_price']

        query = quote_plus(search_term)
        search_url = BESTBUY_SEARCH_URL_TEMPLATE.format(query=query)
        log.info(f"[BestBuy] Searching for '{search_term}' (Max Price: ${max_price})")
        log.debug(f"[BestBuy] Search URL: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return []

        # Check for common blocking patterns if needed
        if "Access Denied" in response.text:
            log.error("[BestBuy] Access Denied. Scraping likely blocked.")
            return []

        soup = self._parse_html(response.text)
        if not soup:
            return []

        results = []

        # --- Strategy 1: Try embedded LD+JSON (often used for SEO) ---
        found_json = False
        scripts = soup.select(SCRIPT_SELECTOR_BB)
        for script in scripts:
            try:
                data = json.loads(script.text)
                # Check if it's a product list or individual product schema
                if isinstance(data, list): # Often a list of product schemas
                     items_data = data
                elif isinstance(data, dict) and data.get('@type') == 'ItemList':
                     items_data = data.get('itemListElement', []) # Navigate structure
                else:
                     items_data = [] # Not the format we expect

                if items_data:
                     log.info(f"[BestBuy] Found {len(items_data)} items in embedded LD+JSON.")
                     for item_entry in items_data:
                         # Extract data - structure depends on schema type (Product, ListItem)
                         item_data = item_entry.get('item', item_entry) # Handle ListItem structure
                         if item_data.get('@type') != 'Product': continue

                         try:
                             title = item_data.get('name')
                             offers = item_data.get('offers', {})
                             if isinstance(offers, list): # Sometimes offers is a list
                                offers = offers[0] if offers else {}

                             price = self._clean_price(offers.get('price'))
                             link = item_data.get('url')

                             if not title or price is None or not link:
                                 continue

                             # Ensure link is absolute
                             if link and not link.startswith('http'):
                                link = f"https://www.bestbuy.com{link}" if link.startswith('/') else f"https://www.bestbuy.com/{link}"


                             result = {
                                 "platform": self.platform_name, "item": search_term,
                                 "title": title, "price": price,
                                 "seller_rating": None, "link": link
                             }
                             if self._apply_filters(result, item):
                                 results.append(result)

                         except Exception as e:
                             log.warning(f"[BestBuy] Error processing item from JSON-LD data: {e}")
                     found_json = True
                     # Don't break here, there might be multiple LD+JSON blocks
            except json.JSONDecodeError:
                continue
            except Exception as e:
                log.error(f"[BestBuy] Error processing script tag (LD+JSON): {e}")

        # --- Strategy 2: Direct HTML scraping (fallback) ---
        if not found_json: # Only run if JSON method yielded no results
            log.warning("[BestBuy] Embedded JSON-LD data not found or failed to parse. Falling back to direct HTML scraping.")
            list_items = soup.select(RESULT_ITEM_SELECTOR_BB)
            log.info(f"[BestBuy] Found {len(list_items)} potential listings via HTML selectors.")

            if not list_items and not found_json:
                 log.warning(f"[BestBuy] No items found using selector '{RESULT_ITEM_SELECTOR_BB}'. Structure might have changed.")

            for list_item in list_items:
                try:
                    title_element = list_item.select_one(TITLE_SELECTOR_BB)
                    price_element = list_item.select_one(PRICE_SELECTOR_BB)
                    link_element = list_item.select_one(LINK_SELECTOR_BB) # Same as title link usually

                    title = title_element.get_text(strip=True) if title_element else "N/A"
                    link = None
                    if link_element and link_element.has_attr('href'):
                         href = link_element['href']
                         link = f"https://www.bestbuy.com{href}" if not href.startswith('http') else href

                    price = None
                    if price_element:
                        price_str = price_element.get_text(strip=True)
                        price = self._clean_price(price_str)

                    if title == "N/A" or price is None or link is None:
                        log.debug(f"[BestBuy] Skipping item due to missing data (HTML scrape): Title={title}, Price={price}, Link={link}")
                        continue

                    result = {
                        "platform": self.platform_name, "item": search_term,
                        "title": title, "price": price,
                        "seller_rating": None, "link": link
                    }

                    if self._apply_filters(result, item):
                         results.append(result)

                except Exception as e:
                    log.warning(f"[BestBuy] Error processing a listing item (HTML scrape): {e}", exc_info=False)
                    continue

        log.info(f"[BestBuy] Found {len(results)} relevant listings for '{search_term}' after filtering.")
        return results
