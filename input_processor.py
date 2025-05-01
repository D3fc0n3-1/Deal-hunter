import json
import logging
import os

log = logging.getLogger(__name__)

def read_input_file(file_path):
    """
    Reads the JSON input file containing items to search for.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        list: A list of dictionaries, where each dictionary represents an item.
              Returns an empty list if the file is not found, empty, or invalid.
    """
    if not os.path.exists(file_path):
        log.error(f"Input file not found: {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Handle potentially empty file
            if not content.strip():
                log.warning(f"Input file is empty: {file_path}")
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                log.error(f"Input file does not contain a valid JSON list: {file_path}")
                return []
            log.info(f"Successfully read {len(data)} items from {file_path}")
            # Basic validation of item structure (optional but recommended)
            valid_items = []
            for i, item in enumerate(data):
                if isinstance(item, dict) and 'name' in item and 'max_price' in item:
                     # Ensure max_price is a number, default min_seller_rating if missing
                    try:
                        item['max_price'] = float(item['max_price'])
                    except (ValueError, TypeError):
                         log.warning(f"Item {i} in {file_path} has invalid 'max_price'. Skipping.")
                         continue
                    item.setdefault('min_seller_rating', 0) # Default to 0 if missing
                    try:
                         item['min_seller_rating'] = float(item['min_seller_rating'])
                    except (ValueError, TypeError):
                        log.warning(f"Item {i} in {file_path} has invalid 'min_seller_rating'. Using 0.")
                        item['min_seller_rating'] = 0.0
                    valid_items.append(item)
                else:
                    log.warning(f"Skipping invalid item structure at index {i} in {file_path}")
            return valid_items

    except json.JSONDecodeError as e:
        log.error(f"Error decoding JSON from {file_path}: {e}")
        return []
    except Exception as e:
        log.error(f"An unexpected error occurred while reading {file_path}: {e}")
        return []

if __name__ == '__main__':
    # Example usage if run directly
    logging.basicConfig(level=logging.INFO)
    # Assumes input.json exists in the same directory for testing
    test_items = read_input_file('input.json')
    if test_items:
        print("Items read successfully:")
        for item in test_items:
            print(item)
    else:
        print("No items read or error occurred.")