import logging
from urllib.parse import quote_plus # For URL encoding search terms

# Ensure these imports are correct relative to this file's location
from .base_platform import BasePlatform
from config_manager import get_api_key # To potentially use API keys later
# Import the fuzzy matching utility if needed for title relevance
from search_enhancer import check_title_relevance


log = logging.getLogger(__name__)

# --- Configuration ---
EBAY_SEARCH_URL_TEMPLATE = "https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=0&LH_BIN=1&rt=1&_trksid=p2045573.m1684"
# LH_BIN=1 -> Buy It Now only

# --- Selectors (THESE WILL BREAK IF EBAY CHANGES ITS WEBSITE STRUCTURE) ---
RESULT_ITEM_SELECTOR = "li.s-item"
TITLE_SELECTOR = "div.s-item__title span[role='heading']" # Check actual element if needed
PRICE_SELECTOR = "span.s-item__price"
LINK_SELECTOR = "a.s-item__link"
SELLER_INFO_SELECTOR = "span.s-item__seller-info-text"

# --- Ensure class name is exactly EbayPlatform ---
class EbayPlatform(BasePlatform):
    """eBay search implementation (using scraping as fallback/example)."""

    def __init__(self):
        super().__init__("eBay")
        self.app_id = get_api_key('ebay_appid')
        if self.app_id:
            log.info("[eBay] API Key detected (though API logic not implemented in this example). Using scraping.")

    def search(self, item):
        """Searches eBay for the item using web scraping."""
        search_term = item['name']
        max_price = item['max_price']
        min_seller_rating = item['min_seller_rating']

        query = quote_plus(search_term)
        search_url = EBAY_SEARCH_URL_TEMPLATE.format(query=query)
        log.info(f"[eBay] Searching for '{search_term}' (Max Price: ${max_price}, Min Rating: {min_seller_rating}%)")
        log.debug(f"[eBay] Search URL: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return []

        soup = self._parse_html(response.text)
        if not soup:
            return []

        results = []
        # Make sure RESULT_ITEM_SELECTOR is correct for current eBay layout
        list_items = soup.select(RESULT_ITEM_SELECTOR)
        # Check if the selector is finding anything
        if not list_items:
            log.warning(f"[eBay] No items found using selector '{RESULT_ITEM_SELECTOR}'. Check eBay's HTML structure.")
            # Try alternative selectors if needed, e.g., based on data attributes
            # list_items = soup.select('div.s-item__wrapper') # Example alternative

        log.info(f"[eBay] Found {len(list_items)} potential listings on page using selector '{RESULT_ITEM_SELECTOR}'.")


        for list_item in list_items:
            try:
                title_element = list_item.select_one(TITLE_SELECTOR)
                price_element = list_item.select_one(PRICE_SELECTOR)
                link_element = list_item.select_one(LINK_SELECTOR)

                # Robust check for elements before accessing attributes/text
                title = "N/A"
                if title_element:
                    # Sometimes title is inside the link text itself
                    title_text = title_element.get_text(strip=True)
                    if not title_text and link_element: # Fallback to link text
                        title_text = link_element.get_text(strip=True)
                    title = title_text.replace('New Listing', '').strip()

                price_str = price_element.get_text(strip=True) if price_element else ""
                price = self._clean_price(price_str.split(' to ')[0]) # Take the lower price if range

                link = link_element['href'] if link_element and link_element.has_attr('href') else None

                seller_info_element = list_item.select_one(SELLER_INFO_SELECTOR)
                seller_rating = None
                if seller_info_element:
                     seller_text = seller_info_element.get_text(strip=True)
                     if '%' in seller_text:
                         try:
                             rating_part = seller_text.split('%')[0].split()[-1]
                             # Handle potential non-numeric values before conversion
                             cleaned_rating_part = ''.join(filter(lambda x: x.isdigit() or x == '.', rating_part))
                             if cleaned_rating_part:
                                 seller_rating = float(cleaned_rating_part)
                         except (ValueError, IndexError, TypeError):
                             log.debug(f"[eBay] Could not parse seller rating from: {seller_text}")


                if title == "N/A" or price is None or link is None:
                    log.debug(f"[eBay] Skipping item due to missing data: Title='{title}', Price={price}, Link={link}")
                    continue

                result = {
                    "platform": self.platform_name,
                    "item": search_term,
                    "title": title,
                    "price": price,
                    "seller_rating": seller_rating,
                    "link": link
                }

                if self._apply_filters(result, item) and self._apply_ebay_filters(result, item):
                    results.append(result)

            except Exception as e:
                log.warning(f"[eBay] Error processing a listing item: {e}", exc_info=False) # Keep log cleaner
                continue

        log.info(f"[eBay] Found {len(results)} relevant listings for '{search_term}' after filtering.")
        return results

    def _apply_ebay_filters(self, result, item):
        """Applies eBay-specific filters (seller rating)."""
        min_rating = item.get('min_seller_rating', 0) # Use .get for safety
        if min_rating > 0:
            # Ensure seller_rating is not None before comparison
            current_rating = result.get('seller_rating')
            if current_rating is None or current_rating < min_rating:
                log.debug(f"[eBay] Filtering out item (rating): {result.get('title')} Rating: {current_rating} (Min: {min_rating}%)")
                return False
        return True
