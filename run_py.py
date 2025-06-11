"""
Main entry point for Hindalco PDF Downloader
Can be run manually or by automated systems
"""

import sys
import argparse
from datetime import datetime, timedelta
from downloader import HindalcoPDFDownloader
import logging

def main():
    parser = argparse.ArgumentParser(description='Hindalco PDF Downloader')
    parser.add_argument('--date', type=str, help='Download for specific date (YYYY-MM-DD format)')
    parser.add_argument('--scheduler', action='store_true', help='Run in scheduler mode (continuous)')
    parser.add_argument('--backfill', type=int, help='Download missing files for last N days')
    
    args = parser.parse_args()
    
    downloader = HindalcoPDFDownloader()
    
    if args.scheduler:
        # Start the scheduler
        from scheduler import start_scheduler
        start_scheduler()
    
    elif args.date:
        # Download for specific date
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            success = downloader.download_for_date(target_date)
            sys.exit(0 if success else 1)
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format")
            sys.exit(1)
    
    elif args.backfill:
        # Backfill missing files
        today = datetime.now()
        success_count = 0
        
        for i in range(args.backfill):
            date = today - timedelta(days=i)
            success = downloader.download_for_date(date)
            if success:
                success_count += 1
        
        print(f"Backfill completed: {success_count}/{args.backfill} files downloaded")
        sys.exit(0)
    
    else:
        # Default: download for today
        from downloader import main as download_main
        download_main()

if __name__ == "__main__":
    main()