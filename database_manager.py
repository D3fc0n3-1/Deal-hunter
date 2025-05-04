import sqlite3
import logging
import os
from datetime import datetime

# Import config getter
from config_manager import get_general_setting

log = logging.getLogger(__name__)

# --- Database Initialization ---
def init_db():
    """Initializes the database and creates the listings table if it doesn't exist."""
    db_path = get_general_setting('database_file', 'results.db')
    log.info(f"Initializing database at: {db_path}")

    # Ensure the directory for the database exists (optional, useful if path includes folders)
    # db_dir = os.path.dirname(db_path)
    # if db_dir and not os.path.exists(db_dir):
    #     try:
    #         os.makedirs(db_dir)
    #         log.info(f"Created directory for database: {db_dir}")
    #     except OSError as e:
    #         log.error(f"Failed to create directory {db_dir}: {e}")
    #         return # Cannot proceed if directory fails

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, timeout=10.0)
    try:
        # Connect (creates the file if it doesn't exist)
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()

        # SQL to create table - Using TEXT for flexibility, REAL for numbers
        # UNIQUE constraint on 'link' helps prevent exact duplicate entries
        # Added search_term and found_timestamp columns
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            search_term TEXT,
            title TEXT,
            price REAL,
            seller_rating REAL,
            link TEXT UNIQUE,
            found_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_sql)

        # Optional: Add indexes for faster querying later
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price ON listings (price);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON listings (platform);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_term ON listings (search_term);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON listings (found_timestamp);")


        conn.commit()
        log.info("Database initialized successfully. 'listings' table ensured.")

    except sqlite3.Error as e:
        log.critical(f"CRITICAL: Database initialization failed: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

# --- Saving Results ---
def save_results(results):
    """Saves a list of result dictionaries to the SQLite database."""
    if not results:
        log.info("No results to save to database.")
        return

    db_path = get_general_setting('database_file', 'results.db')
    conn = None
    inserted_count = 0
    ignored_count = 0

    # SQL for insertion - INSERT OR IGNORE skips rows where the UNIQUE constraint (link) fails
    insert_sql = """
    INSERT OR IGNORE INTO listings (
        platform, search_term, title, price, seller_rating, link
    ) VALUES (?, ?, ?, ?, ?, ?);
    """
    # Note: found_timestamp uses the default value

    try:
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, timeout=10.0)
        cursor = conn.cursor()

        for result in results:
            # Prepare data tuple matching the SQL placeholders
            data_tuple = (
                result.get('platform'),
                result.get('item'), # 'item' from the result dict holds the search term
                result.get('title'),
                result.get('price'),
                result.get('seller_rating'), # Handles None correctly (becomes NULL)
                result.get('link')
            )

            try:
                cursor.execute(insert_sql, data_tuple)
                # cursor.rowcount is 1 if inserted, 0 if ignored (due to unique link)
                if cursor.rowcount > 0:
                    inserted_count += 1
                else:
                    # Check if link was the reason for ignore (it should be)
                    if result.get('link'):
                        ignored_count += 1
                    else: # If link was None, something else happened, log it.
                       log.warning(f"Row ignore without link for title: {result.get('title')}")

            except sqlite3.Error as e:
                log.warning(f"Failed to insert row for '{result.get('title', 'N/A')}': {e}")
                # Optionally skip this row or handle differently

        conn.commit() # Commit all changes at once
        log.info(f"Database save complete. Inserted: {inserted_count}, Ignored (duplicate link): {ignored_count}")

    except sqlite3.Error as e:
        log.error(f"Database error during save: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

# --- Optional: Basic Query Function (Example) ---
def get_recent_results(limit=10):
    """Example function to retrieve the most recently found results."""
    db_path = get_general_setting('database_file', 'results.db')
    conn = None
    try:
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row # Return results as dictionary-like rows
        cursor = conn.cursor()

        query_sql = "SELECT * FROM listings ORDER BY found_timestamp DESC LIMIT ?;"
        cursor.execute(query_sql, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows] # Convert rows to standard dicts

    except sqlite3.Error as e:
        log.error(f"Database error fetching recent results: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Example usage if run directly
    logging.basicConfig(level=logging.INFO)
    print("Testing database manager...")
    init_db() # Ensure DB exists

    # Example save
    test_data = [
        {'platform': 'Test', 'item': 'TestItem', 'title': 'Unique Item 1', 'price': 10.0, 'seller_rating': 99.0, 'link': 'http://example.com/unique1'},
        {'platform': 'Test', 'item': 'TestItem', 'title': 'Unique Item 2', 'price': 20.0, 'seller_rating': None, 'link': 'http://example.com/unique2'},
        {'platform': 'Test', 'item': 'TestItem', 'title': 'Duplicate Item 1', 'price': 10.0, 'seller_rating': 99.0, 'link': 'http://example.com/unique1'} # Duplicate link
    ]
    save_results(test_data)

    # Example query
    print("\nRecent Results:")
    recent = get_recent_results(5)
    if recent:
        for row in recent:
            print(row)
    else:
        print("No recent results found or error occurred.")