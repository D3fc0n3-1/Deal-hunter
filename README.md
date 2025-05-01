# AI Shopping Assistant

## Description

This program periodically searches online marketplaces for items specified in an input list (`input.json`). It filters the results based on maximum price and minimum seller rating (primarily for eBay) and outputs the findings to `output.json`.

It currently supports searching (via web scraping or simulated API structure):
*   eBay
*   Amazon *(Note: Highly prone to blocking)*
*   Walmart *(Note: Prone to breaking due to website changes)*
*   Best Buy *(Note: Prone to breaking due to website changes)*

The assistant runs on a schedule defined in the configuration file.

## Getting Started

### Prerequisites

*   **Python 3:** Version 3.8 or higher recommended. Verify your installation:
    ```bash
    python3 --version
    ```
*   **pip:** Python's package installer (usually comes with Python).

### Dependencies

The required Python libraries are listed in `requirements.txt`:
*   `requests`: For making HTTP requests.
*   `beautifulsoup4`: For parsing HTML content (web scraping).
*   `apscheduler`: For scheduling the search tasks.
*   `python-thefuzz[speedup]`: For fuzzy string matching (used in `search_enhancer`).

### Installation

1.  **Clone or Download:** Get the project files onto your local machine. If using Git:
    ```bash
    git clone <repository_url>
    cd ai-shopping-assistant
    ```
    Otherwise, download and extract the files into a directory named `ai-shopping-assistant` and navigate into it using your terminal:
    ```bash
    cd /path/to/ai-shopping-assistant/
    ```

2.  **Install Dependencies:** Run the following command in your terminal within the project's root directory (`ai-shopping-assistant/`):
    ```bash
    pip install -r requirements.txt
    ```
    *(Use `pip3` if `pip` defaults to Python 2 on your system)*

### Configuration

Before running the assistant, configure the following files:

1.  **`input.json`:** Define the items you want to search for. Edit this file to list your desired products, following this format:
    ```json
    [
      {
        "name": "Specific Product Name (e.g., NVIDIA RTX 3080 refurbished)",
        "max_price": 550.00,
        "min_seller_rating": 90
      },
      {
        "name": "Another Item (e.g., Logitech MX Master 3S)",
        "max_price": 90.00,
        "min_seller_rating": 0
      }
    ]
    ```
    *   `name`: The search query for the item.
    *   `max_price`: The maximum price (numeric) you're willing to pay. Items above this price will be filtered out.
    *   `min_seller_rating`: The minimum seller feedback percentage (0-100). Currently, this filter is primarily applied to eBay results. Set to `0` if not applicable.

2.  **`config.ini`:** Configure the assistant's behavior. Key settings include:
    *   `[General]`:
        *   `input_file`: Path to your input list (default: `input.json`).
        *   `output_file`: Path where results will be saved (default: `output.json`).
        *   `schedule_interval_minutes`: How often (in minutes) the search cycle runs (default: `60`).
        *   `log_level`: Set logging verbosity (e.g., `INFO`, `DEBUG`, `WARNING`, `ERROR`).
    *   `[Platforms]`:
        *   `enabled_platforms`: List the platforms to search. Add or remove platform names (e.g., `ebay`, `amazon`, `walmart`, `bestbuy`) on separate lines. Comment out lines with `;` to disable a platform.
    *   `[APIKeys]`:
        *   *(Optional)* Add API keys here if you implement official API support (e.g., for eBay). See comments in the file.
    *   `[Scraping]`:
        *   `request_timeout_seconds`: How long to wait for a website response.
        *   `delay_between_requests_seconds`: Wait time between requests to be polite to servers.
        *   `user_agent`: The browser identifier sent with requests.

### Running the Assistant

1.  Make sure you are in the project's root directory (`ai-shopping-assistant/`) in your terminal.
2.  Run the main script using Python 3:
    ```bash
    python3 main_shopper.py
    ```
3.  The assistant will start, perform an initial search cycle, and then run again based on the `schedule_interval_minutes` defined in `config.ini`.
4.  Log messages will be printed to the console indicating progress and any errors.
5.  Search results meeting your criteria will be saved to the `output.json` file (or the path specified in `config.ini`).

### Stopping the Assistant

Press `Ctrl + C` in the terminal where the script is running. The scheduler should shut down gracefully.

## Usage

*   Modify `input.json` whenever you want to change the items you are searching for. The script will pick up the changes on its next scheduled run.
*   Check `output.json` periodically for found deals. The file includes the platform, original search term, listing title, price, seller rating (if applicable), and a direct link.
*   Adjust `config.ini` to change the search frequency, enabled platforms, or scraping behavior.
*   Monitor the console output for errors, especially for scraping-based modules (Amazon, Walmart, Best Buy), as they might indicate that the website structure has changed or the script is being blocked.

## Important Notes on Web Scraping

*   **Fragility:** The modules for Amazon, Walmart, and Best Buy rely on web scraping (parsing HTML). Websites frequently change their structure, which **will break the scrapers**. You may need to manually update the CSS selectors (e.g., `RESULT_ITEM_SELECTOR`, `TITLE_SELECTOR`) inside the corresponding `platform_modules/*.py` files by inspecting the website's HTML in your browser's developer tools.
*   **Blocking:** Aggressive searching can lead to your IP address being temporarily or permanently blocked by these websites. The script includes delays, but blocking (like Amazon's 503 errors) can still occur.
*   **Terms of Service:** Automated scraping may violate the Terms of Service of some websites. Use responsibly.
*   **eBay API Recommended:** For reliable eBay results, consider registering for the eBay Developer Program, obtaining API keys, and modifying `ebay_module.py` to use the official eBay API instead of scraping.
