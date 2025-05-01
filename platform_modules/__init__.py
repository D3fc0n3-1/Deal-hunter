# This file makes Python treat the 'platform_modules' directory as a package.
# It can also be used to expose module elements at the package level if desired.

# Example: from .ebay_module import EbayPlatform
# This allows 'from platform_modules import EbayPlatform'

# For simplicity now, keep it empty or just list available modules for info.
AVAILABLE_MODULES = ['ebay_module', 'amazon_module', 'walmart_module', 'bestbuy_module']
print(f"Platform modules available: {', '.join(AVAILABLE_MODULES)}")
