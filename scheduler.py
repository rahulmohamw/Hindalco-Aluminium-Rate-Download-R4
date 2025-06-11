"""
Scheduler for Hindalco PDF Downloader
Runs the downloader at specified time daily
"""

import schedule
import time
import logging
from datetime import datetime
from downloader import main as download_main
from config import DOWNLOAD_TIME, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def scheduled_download():
    """Wrapper function for scheduled download"""
    logger.info("=" * 50)
    logger.info("SCHEDULED DOWNLOAD STARTED")
    logger.info("=" * 50)
    
    try:
        download_main()
    except Exception as e:
        logger.error(f"Error during scheduled download: {str(e)}")
    
    logger.info("=" * 50)
    logger.info("SCHEDULED DOWNLOAD COMPLETED")
    logger.info("=" * 50)

def start_scheduler():
    """Start the scheduler"""
    logger.info(f"Starting scheduler - will run daily at {DOWNLOAD_TIME}")
    
    # Schedule the job
    schedule.every().day.at(DOWNLOAD_TIME).do(scheduled_download)
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")

if __name__ == "__main__":
    start_scheduler()
