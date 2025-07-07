import os
import csv
import pandas as pd
from datetime import datetime

CSV_DIR = "csv"

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
                else:
                    record_count = len(rows) - 1  # Subtract header
                    dates = [row[0] for row in rows[1:] if len(row) > 0]
                    if dates:
                        date_range = f"{min(dates)} to {max(dates)}"
                    else:
                        date_range = "No valid dates"
                
                total_records += record_count
                print(f"📄 {filename}")
                print(f"   Records: {record_count}")
                print(f"   Date Range: {date_range}")
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

def merge_duplicate_csvs():
    """Merge any duplicate CSV files that might exist"""
    print("🔄 Checking for duplicate CSV files...")
    
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    # Group files by similar names
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    # Look for files with similar product descriptions
    duplicates_found = False
    for file1 in csv_files:
        for file2 in csv_files:
            if file1 != file2 and file1 < file2:  # Avoid checking same pair twice
                # Check if files might be duplicates (similar names)
                base1 = file1.replace('.csv', '').replace('_', ' ').lower()
                base2 = file2.replace('.csv', '').replace('_', ' ').lower()
                
                # Simple similarity check
                if len(set(base1.split()) & set(base2.split())) > 2:
                    print(f"⚠️  Potential duplicates found:")
                    print(f"   - {file1}")
                    print(f"   - {file2}")
                    duplicates_found = True
    
    if not duplicates_found:
        print("✅ No duplicate CSV files found")

def backup_csv_files():
    """Create backup of all CSV files"""
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(CSV_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv') and not f.startswith('backup_')]
    
    if not csv_files:
        print("❌ No CSV files to backup")
        return
    
    for filename in csv_files:
        src = os.path.join(CSV_DIR, filename)
        dst = os.path.join(backup_dir, filename)
        
        with open(src, 'r') as f_src, open(dst, 'w') as f_dst:
            f_dst.write(f_src.read())
    
    print(f"✅ Backed up {len(csv_files)} CSV files to: {backup_dir}")

def validate_csv_structure():
    """Validate that all CSV files have the correct structure"""
    print("🔍 Validating CSV file structure...")
    
    if not os.path.exists(CSV_DIR):
        print("❌ CSV directory not found")
        return
    
    expected_columns = ["Date", "Description", "Price"]
    issues_found = False
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv') and not f.startswith('backup_')]
    
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

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            view_csv_summary()
        elif command == "details" and len(sys.argv) > 2:
            view_csv_details(sys.argv[2])
        elif command == "backup":
            backup_csv_files()
        elif command == "validate":
            validate_csv_structure()
        elif command == "merge":
            merge_duplicate_csvs()
        else:
            print("❌ Unknown command or missing filename")
            print("Usage:")
            print("  python csv_manager.py summary")
            print("  python csv_manager.py details <filename>")
            print("  python csv_manager.py backup")
            print("  python csv_manager.py validate")
            print("  python csv_manager.py merge")
    else:
        print("🛠️  CSV MANAGER")
        print("=" * 30)
        print("Available commands:")
        print("  summary  - Show summary of all CSV files")
        print("  details  - Show details of a specific CSV file")
        print("  backup   - Create backup of all CSV files")
        print("  validate - Validate CSV file structure")
        print("  merge    - Check for duplicate CSV files")
        print("\nUsage: python csv_manager.py <command> [filename]")
