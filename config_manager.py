import configparser
import logging
import os

# Basic logging setup for the config manager itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

CONFIG_FILE = 'config.ini'

def load_config():
    """Loads configuration from the config.ini file."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        log.error(f"Configuration file '{CONFIG_FILE}' not found.")
        # Create a default config file? Or raise error? For now, error.
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found.")

    try:
        config.read(CONFIG_FILE)
        log.info(f"Configuration loaded successfully from '{CONFIG_FILE}'.")

        # Basic validation/defaults can be added here if needed
        # Example: ensure schedule interval is a positive integer
        try:
            config.getint('General', 'schedule_interval_minutes')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            log.warning("Schedule interval missing or invalid in config. Setting default: 60 minutes.")
            if not config.has_section('General'):
                config.add_section('General')
            config.set('General', 'schedule_interval_minutes', '60')

        return config

    except configparser.Error as e:
        log.error(f"Error parsing configuration file '{CONFIG_FILE}': {e}")
        raise

# Load config once when the module is imported
try:
    config = load_config()
except Exception as e:
    log.critical(f"Failed to load configuration. Exiting. Error: {e}")
    # In a real app, might exit here, but for simplicity, let it continue
    # so other modules can be imported, though they might fail later.
    config = None # Indicate config failed to load

# --- Helper functions to access config values easily ---

def get_general_setting(key, fallback=None):
    """Gets a setting from the [General] section."""
    if not config: return fallback
    try:
        return config.get('General', key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        log.warning(f"Setting '[General]/{key}' not found in config. Returning fallback: {fallback}")
        return fallback

def get_int_setting(section, key, fallback=0):
    """Gets an integer setting from a specified section."""
    if not config: return fallback
    try:
        return config.getint(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        log.warning(f"Integer setting '[{section}]/{key}' not found or invalid. Returning fallback: {fallback}")
        return fallback

def get_float_setting(section, key, fallback=0.0):
    """Gets a float setting from a specified section."""
    if not config: return fallback
    try:
        return config.getfloat(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
         log.warning(f"Float setting '[{section}]/{key}' not found or invalid. Returning fallback: {fallback}")
         return fallback

def get_api_key(key, fallback=None):
    """Gets a setting from the [APIKeys] section."""
    if not config: return fallback
    # Optionally integrate python-dotenv here to check environment variables first
    # import os
    # value = os.getenv(key.upper()) # Check env var like EBAY_APPID
    # if value: return value
    try:
        return config.get('APIKeys', key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        # It's okay if API keys are missing, module might fall back to scraping
        log.debug(f"API Key '[APIKeys]/{key}' not found in config.")
        return fallback

def get_enabled_platforms():
    """Gets the list of enabled platforms."""
    if not config: return []
    try:
        platforms_str = config.get('Platforms', 'enabled_platforms', fallback='')
        # Split by newline, strip whitespace, filter out empty lines/comments
        platforms = [p.strip() for p in platforms_str.splitlines() if p.strip() and not p.strip().startswith(';')]
        log.info(f"Enabled platforms: {platforms}")
        return platforms
    except (configparser.NoSectionError, configparser.NoOptionError):
        log.warning("'[Platforms]/enabled_platforms' section/key not found. No platforms enabled.")
        return []

def get_scraping_setting(key, fallback=None):
    """Gets a setting from the [Scraping] section."""
    if not config: return fallback
    try:
        return config.get('Scraping', key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        log.warning(f"Setting '[Scraping]/{key}' not found in config. Returning fallback: {fallback}")
        return fallback

if __name__ == '__main__':
    # Example usage if run directly
    print("Loading config for testing...")
    if config:
        print(f"Input File: {get_general_setting('input_file')}")
        print(f"Output File: {get_general_setting('output_file')}")
        print(f"Interval (min): {get_int_setting('General', 'schedule_interval_minutes')}")
        print(f"Enabled Platforms: {get_enabled_platforms()}")
        print(f"User Agent: {get_scraping_setting('user_agent', 'DefaultAgent/1.0')}")
        print(f"eBay App ID (example): {get_api_key('ebay_appid')}") # Will likely be None
    else:
        print("Config could not be loaded.")