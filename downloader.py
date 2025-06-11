"""
Hindalco PDF Downloader
Downloads daily PDF files from Hindalco website
"""

import os
import requests
import logging
from datetime import datetime
import time
from config import *

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

class HindalcoPDFDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def format_date_for_url(self, date):
        """Format date for URL construction"""
        day = date.strftime("%d").lstrip('0')  # Remove leading zero
        month = date.strftime("%B").lower()    # Full month name, lowercase
        year = date.strftime("%Y")
        return day, month, year
    
    def format_date_for_filename(self, date):
        """Format date for filename"""
        day = date.strftime("%d")
        month = date.strftime("%b")  # Abbreviated month name
        year = date.strftime("%y")   # 2-digit year
        return day, month, year
    
    def construct_url(self, date):
        """Construct the PDF URL for given date"""
        day, month, year = self.format_date_for_url(date)
        return BASE_URL.format(day, month, year)
    
    def construct_filename(self, date):
        """Construct the local filename for given date"""
        day, month, year = self.format_date_for_filename(date)
        return FILE_NAME_TEMPLATE.format(day=day, month=month, year=year)
    
    def create_directory_structure(self, date):
        """Create year/month directory structure"""
        year = date.strftime("%Y")
        month = date.strftime("%B")  # Full month name
        
        dir_path = os.path.join(DOWNLOAD_DIR, year, month)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    
    def download_pdf(self, url, filepath):
        """Download PDF with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempting to download from: {url} (Attempt {attempt + 1}/{MAX_RETRIES})")
                
                response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                
                if response.status_code == 200:
                    # Check if it's actually a PDF
                    content_type = response.headers.get('content-type', '').lower()
                    if 'pdf' not in content_type:
                        logger.warning(f"Response doesn't appear to be a PDF. Content-Type: {content_type}")
                    
                    # Write file
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = os.path.getsize(filepath)
                    logger.info(f"Successfully downloaded PDF: {filepath} ({file_size} bytes)")
                    return True
                
                elif response.status_code == 404:
                    logger.info(f"PDF not available for this date (404 Not Found)")
                    return False
                
                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return False
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("Max retries reached. Download failed.")
                    return False
            
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return False
        
        return False
    
    def download_today(self):
        """Download PDF for today's date"""
        today = datetime.now()
        return self.download_for_date(today)
    
    def download_for_date(self, date):
        """Download PDF for specific date"""
        logger.info(f"Checking for PDF for date: {date.strftime('%Y-%m-%d')}")
        
        # Construct URL and filename
        url = self.construct_url(date)
        filename = self.construct_filename(date)
        
        # Create directory structure
        dir_path = self.create_directory_structure(date)
        filepath = os.path.join(dir_path, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            logger.info(f"File already exists: {filepath}")
            return True
        
        # Download the PDF
        success = self.download_pdf(url, filepath)
        
        if success:
            logger.info(f"Download completed successfully for {date.strftime('%Y-%m-%d')}")
        else:
            logger.info(f"No PDF available for {date.strftime('%Y-%m-%d')}")
        
        return success

def main():
    """Main function to run the downloader"""
    logger.info("Starting Hindalco PDF Downloader")
    
    downloader = HindalcoPDFDownloader()
    success = downloader.download_today()
    
    if success:
        logger.info("Download process completed successfully")
    else:
        logger.info("No file downloaded (file may not be available for today)")
    
    logger.info("Hindalco PDF Downloader finished")

if __name__ == "__main__":
    main()
