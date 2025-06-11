"""
Configuration file for Hindalco PDF Downloader
"""

import os

# Base configuration
BASE_URL = "https://www.hindalco.com/Upload/PDF/primary-ready-reckoner-{}-{}-{}.pdf"
DOWNLOAD_DIR = "downloads"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "downloader.log")

# Schedule configuration
DOWNLOAD_TIME = "16:00"  # 4 PM in 24-hour format

# File naming configuration
FILE_NAME_TEMPLATE = "Hindalco_Circular_{day}_{month}_{year}.pdf"

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create directories if they don't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
