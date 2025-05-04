import logging
import datetime
import time
import sys
import config_manager as cfg
import input_processor
from importlib import import_module # To dynamically import platform modules

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import core components
import config_manager as cfg
import input_processor
# import output_generator
import database_manager
from platform_modules.base_platform import BasePlatform # For type hinting/checking

# --- Logging Setup ---
log_level_str = cfg.get_general_setting('log_level', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# Silence overly verbose libraries if needed
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)

log = logging.getLogger("main_shopper")

# --- Platform Module Loading ---
def load_platform_modules():
    """Dynamically loads enabled platform modules."""
    platforms = {}
    enabled_platform_names = cfg.get_enabled_platforms()
    if not enabled_platform_names:
        log.warning("No platforms enabled in config.ini. Nothing to search.")
        return platforms

    for name in enabled_platform_names:
        module_name = f"platform_modules.{name}_module"
        class_name = f"{name.capitalize()}Platform" # Assumes ClassName format
        try:
            print(f"Attempting to import {module_name}...") # Add print statement
            module = import_module(module_name)
            print(f"Successfully imported {module_name}.") # Add success print
            
            platform_class = getattr(module, class_name)
            # Ensure it's a subclass of BasePlatform
            if issubclass(platform_class, BasePlatform):
                 platforms[name] = platform_class() # Instantiate the class
                 log.info(f"Successfully loaded platform module: {name}")
            else:
                 log.error(f"Class '{class_name}' in '{module_name}' does not inherit from BasePlatform. Skipping.")

        # --- MODIFICATION START ---
        # Catch specific ImportError and print more details
        except ImportError as e:
            log.error(f"ImportError importing module '{module_name}': {e}. Check file existence and dependencies. Skipping platform '{name}'.", exc_info=True)
        # except AttributeError:
        #    log.error(f"Could not find class '{class_name}' in module '{module_name}'. Check class naming. Skipping platform '{name}'.")
        except Exception as e: # Catch other potential errors during import/getattr
             log.error(f"Error loading platform module '{name}' (module='{module_name}', class='{class_name}'): {e}", exc_info=True) # Add exc_info=True 
    if not platforms:
        log.error("No platform modules loaded successfully. Check configuration and logs.")

    return platforms

# --- Main Search Cycle ---
def run_search_cycle(platform_instances):
    """Reads input, searches platforms, and saves results to database."""
    start_time = time.time()
    log.info("Starting new search cycle...")

    if not platform_instances:
        log.error("No platform instances available to run search cycle.")
        return

    input_file = cfg.get_general_setting('input_file', 'input.json')
    # output_file = cfg.get_general_setting('output_file', 'output.json')

    # 1. Read Input
    items_to_search = input_processor.read_input_file(input_file)
    if not items_to_search:
        log.warning(f"No valid items found in '{input_file}'. Cycle finished early.")
        return

    # 2. Search Platforms
    all_results = []
    for item in items_to_search:
        log.info(f"--- Processing item: {item['name']} ---")
        # Could add search term variations here using search_enhancer
        # search_terms = search_enhancer.get_search_variations(item['name'])
        # For now, just use the original name:
        current_search_term = item['name']

        for platform_name, platform_obj in platform_instances.items():
            log.info(f"Searching on {platform_name}...")
            try:
                platform_results = platform_obj.search(item) # Pass the whole item dict
                if platform_results:
                    log.info(f"Found {len(platform_results)} results on {platform_name} for '{current_search_term}'.")
                    all_results.extend(platform_results)
                else:
                    log.info(f"No results found on {platform_name} for '{current_search_term}'.")
            except Exception as e:
                log.error(f"Platform '{platform_name}' failed during search for '{current_search_term}': {e}", exc_info=True)
            # Optional: Add extra delay between platforms if needed
            # time.sleep(cfg.get_float_setting('Scraping', 'delay_between_platforms_seconds', 1.0))


    # 3. Write Output
    log.info(f"Total results found across all platforms: {len(all_results)}")
    # log.info(f"Attempting to write output to: '{output_file}' (Type: {type(output_file)})") # DEBUG LINE
    # output_generator.write_output_file(output_file, all_results)
    database_manager.save_results(all_results)

    end_time = time.time()
    log.info(f"Search cycle finished in {end_time - start_time:.2f} seconds.")


# --- Scheduler Setup and Main Execution ---
if __name__ == "__main__":
    log.info("Initializing AI Shopping Assistant...")

    if cfg.config is None:
        log.critical("Configuration loading failed. Cannot continue.")
        sys.exit(1) # Exit if config is fundamentally broken

    try:
        database_manager.init_db()
    except Exception as e: # Catch the re-raised exception
        log.critical(f"Database initialization failed. Cannot continue. Error: {e}")
        sys.exit(1) # Exit the script

    # Load platform modules based on config
    platform_instances = load_platform_modules()

    if not platform_instances:
         log.error("No platforms were loaded successfully. Exiting.")
         sys.exit(1)

    # Get schedule interval from config
    interval_minutes = cfg.get_int_setting('General', 'schedule_interval_minutes', 60)
    if interval_minutes <= 0:
        log.warning(f"Invalid schedule interval ({interval_minutes} minutes). Setting to 60 minutes.")
        interval_minutes = 60

    log.info(f"Scheduler interval set to {interval_minutes} minutes.")

    # Create and configure the scheduler
    scheduler = BlockingScheduler(timezone="UTC") # Or your local timezone string

    # Add the job to the scheduler
    scheduler.add_job(
        run_search_cycle,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[platform_instances], # Pass loaded platform instances to the job
        id='shopping_search_job',
        name='Periodic Shopping Search',
        replace_existing=True,
        next_run_time=datetime.datetime.now() # Run immediately the first time
    )

    log.info("Scheduler configured. Starting now...")
    print("---")
    print(f"Shopping Assistant started. Will run searches every {interval_minutes} minutes.")
    print("Press Ctrl+C to exit.")
    print("---")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped by user (Ctrl+C).")
    except Exception as e:
         log.critical(f"An unexpected error occurred in the scheduler: {e}", exc_info=True)
    finally:
        if scheduler.running:
            scheduler.shutdown()
        log.info("Shopping Assistant shut down.")
