import json
import logging
import os
from datetime import datetime # Ensure datetime is imported

log = logging.getLogger(__name__)

def write_output_file(file_path, results):
    """
    Writes the found results to the specified JSON output file.

    Args:
        file_path (str): The path to the output JSON file.
        results (list): A list of dictionaries representing the found items.
    """
    log.debug(f"Inside write_output_file. Received file_path: '{file_path}' (Type: {type(file_path)})") # Debug start of function

    # Basic check for empty path
    if not file_path or not isinstance(file_path, str):
        log.error(f"Output file path is invalid or empty ('{file_path}'). Cannot write results. Check 'output_file' in config.ini.")
        return

    output_data = {
        "last_updated": datetime.now().isoformat(),
        "total_results": len(results),
        "results": results
    }

    try:
        # --- REMOVED os.makedirs call for simplicity ---

        # --- ADDED Debug Log right before open ---
        log.info(f"Attempting to open and write to: '{os.path.abspath(file_path)}'") # Log absolute path

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)

        log.info(f"Successfully wrote {len(results)} results to {file_path}")

    except FileNotFoundError as e:
        log.error(f"FileNotFoundError writing output file '{file_path}'. Does the directory exist? Error: {e}", exc_info=True) # More specific error log
    except IOError as e:
        log.error(f"IOError writing output file '{file_path}': {e}", exc_info=True)
    except Exception as e:
        log.error(f"An unexpected error occurred while writing '{file_path}': {e}", exc_info=True)
