import logging
from thefuzz import fuzz

log = logging.getLogger(__name__)

def get_search_variations(item_name):
    """
    Generates potential variations of the search term.
    (Currently very basic - just returns the original name).
    Future: Could generate synonyms, acronyms, remove/add terms like 'refurbished'.

    Args:
        item_name (str): The original item name from input.

    Returns:
        list: A list of search terms (currently just the original).
    """
    # Placeholder for more advanced logic
    # Example: could split "NVIDIA RTX 3080 refurbished" into
    # ["NVIDIA RTX 3080 refurbished", "NVIDIA RTX 3080", "RTX 3080 refurbished"]
    # For now, keep it simple
    variations = [item_name.lower()] # Use lower case for searching usually
    log.debug(f"Generated search variations for '{item_name}': {variations}")
    return variations


def check_title_relevance(original_item_name, result_title, min_ratio=70):
    """
    Checks if the result title is relevant to the original search item name
    using fuzzy string matching.

    Args:
        original_item_name (str): The name from the input file.
        result_title (str): The title of the found listing.
        min_ratio (int): The minimum fuzz ratio (0-100) to consider relevant.

    Returns:
        bool: True if relevant, False otherwise.
    """
    # Normalize strings for better comparison (lowercase, maybe remove common words)
    norm_original = original_item_name.lower()
    norm_title = result_title.lower()

    # Can use different fuzz methods:
    # ratio = fuzz.ratio(norm_original, norm_title) # Simple ratio
    ratio = fuzz.partial_ratio(norm_original, norm_title) # Good if original is substring of title
    # ratio = fuzz.token_sort_ratio(norm_original, norm_title) # Ignores word order
    # ratio = fuzz.token_set_ratio(norm_original, norm_title) # Handles common tokens

    log.debug(f"Fuzz check: Ratio={ratio} between '{norm_original}' and '{norm_title}' (Min: {min_ratio})")

    return ratio >= min_ratio

if __name__ == '__main__':
    # Example usage if run directly
    logging.basicConfig(level=logging.DEBUG)
    name1 = "NVIDIA RTX 3080 refurbished"
    title1 = "ASUS NVIDIA GeForce RTX 3080 TUF Gaming OC 10GB GDDR6X Graphics Card (USED)"
    title2 = "Gigabyte Gaming Monitor G27Q - 27 inch 144Hz QHD"
    title3 = "Nvidia RTX 3080 FE Founders Edition - Good condition, slightly refurbished"

    print(f"'{title1}' relevant to '{name1}'? {check_title_relevance(name1, title1)}")
    print(f"'{title2}' relevant to '{name1}'? {check_title_relevance(name1, title2)}")
    print(f"'{title3}' relevant to '{name1}'? {check_title_relevance(name1, title3, min_ratio=80)}")

    print(f"Search variations for '{name1}': {get_search_variations(name1)}")