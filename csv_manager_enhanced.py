import os
import csv
import pandas as pd
from datetime import datetime
import pdfplumber
import re
from pathlib import Path
import shutil

CSV_DIR = "csv"
PDF_DIR = "pdf"
BACKUP_DIR = "backups"

# Expected 7 line items from your PDF
EXPECTED_PRODUCTS = [
    "P0405 (Si 0.04% max, Fe 0.06% max) 99.85% (min)",
    "P0610 (99.85% min) /P1020/ EC Grade Ingot & Sow 99.7% (min) / Cast Bar",
    "CG Grade Ingot & Sow 99.5% (min) purity",
    "EC Grade Wire Rods, Dia 9.5 mm - Conductivity 61% min",
    "6201 Alloy Wire Rod - Dia 9.5 mm (HAC-1)",
    "Billets (AA6063) Dia 7\", 8\" & 9\" - subject to availability",
    "Billets (AA6063) Dia 5\", 6\" - subject to availability"
]

def ensure_directories():
    """Create necessary directories if they don't exist"""
    for directory in [CSV_DIR, PDF_DIR, BACKUP_DIR]:
        os.makedirs(directory, exist_ok=True)

def extract_pdf_data(pdf_path):
    """Extract data from PDF file"""
    print(f"🔍 Extracting data from: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text() + "\n"
            
            # Extract date from filename or content
            pdf_name = os.path.basename(pdf_path)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', pdf_name)
            if date_match:
                extraction_date = date_match.group(1)
            else:
                extraction_date = datetime.now().strftime("%Y-%m-%d")
            
            # Extract product data
            products_data = []
            
            # Look for table-like structure
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table[1:]:  # Skip header
                        if len(row) >= 2 and row[0] and row[1]:
                            # Clean the data
                            description = str(row[0]).strip()
                            price_str = str(row[1]).strip()
                            
                            # Extract price (remove currency symbols, commas)
                            price_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', price_str)
                            if price_match:
                                price = int(price_match.group(1).replace(',', ''))
                                products_data.append({
                                    'date': extraction_date,
                                    'description': description,
                                    'price': price
                                })
            
            # If no table found, try text extraction
            if not products_data:
                lines = all_text.split('\n')
                for line in lines:
                    # Look for lines with product info and prices
                    if any(keyword in line.lower() for keyword in ['grade', 'alloy', 'billet', 'wire', 'ingot']):
                        # Extract price from the line
                        price_match = re.search(r'(\d+(?:,\d{3})*)', line)
                        if price_match:
                            price = int(price_match.group(1).replace(',', ''))
                            products_data.append({
                                'date': extraction_date,
                                'description': line.strip(),
                                'price': price
                            })
            
            return products_data
            
    except Exception as e:
        print(f"❌ Error extracting PDF data: {e}")
        return []

def create_csv_filename(description):
    """Create a safe filename from product description"""
    # Remove special characters and limit length
    safe_name = re.sub(r'[^\w\s-]', '', description)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name[:50]  # Limit length
    return f"{safe_name}.csv"

def save_to_csv(product_data, csv_filename):
    """Save product data to CSV file"""
    csv_path = os.path.join(CSV_DIR, csv_filename)
    
    # Check if file exists
    file_exists = os.path.exists(csv_path)
    
    # Read existing data if file exists
    existing_data = []
    if file_exists:
        try:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                existing_data = list(reader)
        except Exception as e:
            print(f"⚠️  Error reading existing CSV: {e}")
    
    # Check if this date already exists
    date_exists = any(row['Date'] == product_data['date'] for row in existing_data)
    
    if date_exists:
        print(f"⚠️  Date {product_data['date']} already exists in {csv_filename}")
        return False
    
    # Add new data
    new_row = {
        'Date': product_data['date'],
        'Description': product_data['description'],
        'Price': product_data['price']
    }
    
    existing_data.append(new_row)
    
    # Sort by date
    existing_data.sort(key=lambda x: x['Date'])
    
    # Write to CSV
    try:
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Date', 'Description', 'Price'])
            writer.writeheader()
            writer.writerows(existing_data)
        
        print(f"✅ Updated {csv_filename} with new data")
        return True
        
    except Exception as e:
        print(f"❌ Error writing to CSV: {e}")
        return False

def process_pdf_to_csv():
    """Main function to process PDF files and convert to CSV"""
    ensure_directories()
    
    print("📄 PDF TO CSV CONVERTER")
    print("=" * 60)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in pdf directory")
        return
    
    print(f"📋 Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        print(f"\n🔄 Processing: {pdf_file}")
        
        # Extract data from PDF
        products_data = extract_pdf_data(pdf_path)
        
        if not products_data:
            print(f"❌ No data extracted from {pdf_file}")
            continue
        
        print(f"📊 Extracted {len(products_data)} products")
        
        # Process each product
        for product in products_data:
            # Create filename based on description
            csv_filename = create_csv_filename(product['description'])
            
            # Check if this is a new product (not in expected list)
            is_new_product = not any(expected in product['description'] for expected in EXPECTED_PRODUCTS)
            
            if is_new_product:
                print(f"🆕 New product detected: {product['description']}")
            
            # Save to CSV
            save_to_csv(product, csv_filename)
        
        # Move processed PDF to backup
        backup_pdf_path = os.path.join(BACKUP_DIR, f"processed_{pdf_file}")
        shutil.move(pdf_path, backup_pdf_path)
        print(f"📁 Moved {pdf_file} to backup")

def view_csv_summary():
    """Display summary of all CSV files"""
    print("📊 CSV FILES SUMMARY")
    print("=" * 60)
    
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    total_records = 0
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv') and not f.startswith('backup_')]
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    for filename in sorted(csv_files):
        filepath = os.path.join(CSV_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) <= 1:  # Only header or empty
                    record_count = 0
                    date_range = "No data"
                    latest_price = "N/A"
                else:
                    record_count = len(rows) - 1  # Subtract header
                    dates = [row[0] for row in rows[1:] if len(row) > 0]
                    prices = [row[2] for row in rows[1:] if len(row) > 2]
                    
                    if dates:
                        date_range = f"{min(dates)} to {max(dates)}"
                        latest_price = prices[-1] if prices else "N/A"
                    else:
                        date_range = "No valid dates"
                        latest_price = "N/A"
                
                total_records += record_count
                print(f"📄 {filename}")
                print(f"   Records: {record_count}")
                print(f"   Date Range: {date_range}")
                print(f"   Latest Price: {latest_price}")
                print()
                
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
    
    print(f"📈 TOTAL RECORDS: {total_records}")

def view_csv_details(filename):
    """Display detailed content of a specific CSV file"""
    filepath = os.path.join(CSV_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filename}")
        return
    
    try:
        df = pd.read_csv(filepath)
        print(f"📄 DETAILS FOR: {filename}")
        print("=" * 60)
        print(f"Total Records: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        print("\nRecent Records:")
        print(df.tail(10).to_string(index=False))
        
        if 'Price' in df.columns:
            print(f"\nPrice Statistics:")
            print(f"   Min: {df['Price'].min():,}")
            print(f"   Max: {df['Price'].max():,}")
            print(f"   Average: {df['Price'].mean():,.2f}")
            print(f"   Latest: {df['Price'].iloc[-1]:,}")
            
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")

def backup_csv_files():
    """Create backup of all CSV files"""
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, f"csv_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ No CSV files to backup")
        return
    
    for filename in csv_files:
        src = os.path.join(CSV_DIR, filename)
        dst = os.path.join(backup_dir, filename)
        shutil.copy2(src, dst)
    
    print(f"✅ Backed up {len(csv_files)} CSV files to: {backup_dir}")

def validate_csv_structure():
    """Validate that all CSV files have the correct structure"""
    print("🔍 Validating CSV file structure...")
    
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    expected_columns = ["Date", "Description", "Price"]
    issues_found = False
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    for filename in csv_files:
        filepath = os.path.join(CSV_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
                if header != expected_columns:
                    print(f"❌ {filename}: Invalid header - {header}")
                    issues_found = True
                else:
                    # Check a few data rows
                    row_count = 0
                    for row in reader:
                        row_count += 1
                        if len(row) != 3:
                            print(f"❌ {filename}: Row {row_count + 1} has {len(row)} columns instead of 3")
                            issues_found = True
                            continue
                        
                        # Validate date format
                        try:
                            datetime.strptime(row[0], "%Y-%m-%d")
                        except ValueError:
                            print(f"❌ {filename}: Invalid date format in row {row_count + 1}: {row[0]}")
                            issues_found = True
                        
                        # Validate price is numeric
                        try:
                            int(row[2])
                        except ValueError:
                            print(f"❌ {filename}: Invalid price in row {row_count + 1}: {row[2]}")
                            issues_found = True
                        
                        if row_count > 10:  # Only check first 10 rows
                            break
                    
                    if row_count == 0:
                        print(f"⚠️  {filename}: No data rows found")
                
        except Exception as e:
            print(f"❌ Error validating {filename}: {e}")
            issues_found = True
    
    if not issues_found:
        print("✅ All CSV files have valid structure")

def create_workflow():
    """Create a one-time workflow for PDF processing"""
    print("🔄 CREATING WORKFLOW")
    print("=" * 60)
    
    # Step 1: Ensure directories exist
    ensure_directories()
    print("✅ Directories created/verified")
    
    # Step 2: Backup existing CSV files
    if os.path.exists(CSV_DIR) and os.listdir(CSV_DIR):
        backup_csv_files()
    
    # Step 3: Process PDF files
    process_pdf_to_csv()
    
    # Step 4: Validate results
    validate_csv_structure()
    
    # Step 5: Show summary
    view_csv_summary()
    
    print("\n🎉 WORKFLOW COMPLETED")
    print("=" * 60)
    print("✅ PDF files processed and moved to backup")
    print("✅ CSV files created/updated")
    print("✅ Data validated")
    print("✅ Summary displayed")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "workflow":
            create_workflow()
        elif command == "convert":
            process_pdf_to_csv()
        elif command == "summary":
            view_csv_summary()
        elif command == "details" and len(sys.argv) > 2:
            view_csv_details(sys.argv[2])
        elif command == "backup":
            backup_csv_files()
        elif command == "validate":
            validate_csv_structure()
        else:
            print("❌ Unknown command or missing filename")
            print("Usage:")
            print("  python csv_manager.py workflow   - Run complete workflow")
            print("  python csv_manager.py convert    - Convert PDF to CSV")
            print("  python csv_manager.py summary    - Show summary of all CSV files")
            print("  python csv_manager.py details <filename> - Show details of a specific CSV file")
            print("  python csv_manager.py backup     - Create backup of all CSV files")
            print("  python csv_manager.py validate   - Validate CSV file structure")
    else:
        print("🛠️  ENHANCED CSV MANAGER")
        print("=" * 40)
        print("Available commands:")
        print("  workflow - Run complete PDF to CSV workflow")
        print("  convert  - Convert PDF files to CSV")
        print("  summary  - Show summary of all CSV files")
        print("  details  - Show details of a specific CSV file")
        print("  backup   - Create backup of all CSV files")
        print("  validate - Validate CSV file structure")
        print("\nQuick Start:")
        print("  1. Place PDF files in 'pdf' folder")
        print("  2. Run: python csv_manager.py workflow")
        print("\nUsage: python csv_manager.py <command> [filename]")
