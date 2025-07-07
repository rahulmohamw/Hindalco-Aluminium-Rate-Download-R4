import os
import csv
import glob
from datetime import datetime
from PyPDF2 import PdfReader

CSV_DIR = "csv"

# Define the 7 product types based on your image
PRODUCT_MAPPING = {
    "P0406": "P0406_(Si_0.04%_max_Fe_0.06%_max)_99.95%_(min).csv",
    "P0610": "P0610_(99.85%_min)_P1020_EC_Grade_Ingot_&_Sow_99.7%_(min)_Cast_Bar.csv", 
    "CG_Grade": "CG_Grade_Ingot_&_Sow_99.5%_(min)_purity.csv",
    "EC_Grade_Wire": "EC_Grade_Wire_Rods_Dia_9.5_mm_Conductivity_61%_min.csv",
    "6201_Alloy": "6201_Alloy_Wire_Rod_Dia_9.5_mm_(HAC-1).csv",
    "Billets_7_8_9": "Billets_(AA6063)_Dia_7_8_&_9_subject_to_availability.csv",
    "Billets_5_6": "Billets_(AA6063)_Dia_5_6_subject_to_availability.csv"
}

def get_product_type(description):
    """Determine which product type this description belongs to"""
    desc_lower = description.lower()
    
    if "p0406" in desc_lower or ("si 0.04" in desc_lower and "fe 0.06" in desc_lower):
        return "P0406"
    elif "p0610" in desc_lower or ("99.85" in desc_lower and "p1020" in desc_lower):
        return "P0610"
    elif "cg grade" in desc_lower and ("ingot" in desc_lower or "sow" in desc_lower):
        return "CG_Grade"
    elif "ec grade" in desc_lower and "wire rod" in desc_lower:
        return "EC_Grade_Wire"
    elif "6201" in desc_lower and "alloy" in desc_lower:
        return "6201_Alloy"
    elif "billet" in desc_lower and ("7" in desc_lower or "8" in desc_lower or "9" in desc_lower):
        return "Billets_7_8_9"
    elif "billet" in desc_lower and ("5" in desc_lower or "6" in desc_lower):
        return "Billets_5_6"
    
    return None

def extract_date_from_text(text):
    import re
    match = re.search(r'w\.e\.f\.\s*(\d{2}\.\d{2}\.\d{4})', text)
    if match:
        date_obj = datetime.strptime(match.group(1), "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")

def clean_description(desc):
    """Clean the description by removing common unwanted patterns"""
    import re
    
    # Remove rate patterns like "249500", "252000", etc. (5-6 digit numbers)
    desc = re.sub(r'\b\d{5,6}\b', '', desc)
    
    # Remove standalone numbers that might be rates
    desc = re.sub(r'\b\d+\b(?=\s|$)', '', desc)
    
    # Remove extra whitespace
    desc = ' '.join(desc.split())
    
    # Remove trailing punctuation and whitespace
    desc = desc.strip(' .-_')
    
    return desc

def extract_table_data(pdf_path):
    reader = PdfReader(pdf_path)
    text = "\n".join([page.extract_text() for page in reader.pages])
    lines = text.splitlines()
    
    data_rows = []
    current_date = extract_date_from_text(text)
    
    # More precise line parsing
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for numbered items (1., 2., 3., etc.)
        if line and line[0].isdigit() and '.' in line[:3]:
            parts = line.split()
            
            if len(parts) >= 3:  # Minimum: number, description, price
                try:
                    # Try to find the price (last numeric value)
                    price_found = False
                    for j in range(len(parts) - 1, -1, -1):
                        try:
                            price = int(parts[j].replace(",", ""))
                            # Price should be reasonable (> 1000 for these items)
                            if price > 1000:
                                # Everything between item number and price is description
                                desc_parts = parts[1:j]
                                desc = " ".join(desc_parts)
                                desc = clean_description(desc)
                                
                                # Skip if description is too short or contains only numbers
                                if len(desc) > 5 and not desc.isdigit():
                                    data_rows.append((current_date, desc, price))
                                    price_found = True
                                    break
                        except (ValueError, IndexError):
                            continue
                    
                    # If we couldn't find a price in the current line, 
                    # check if it's split across lines
                    if not price_found and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        next_parts = next_line.split()
                        
                        if next_parts:
                            try:
                                price = int(next_parts[0].replace(",", ""))
                                if price > 1000:
                                    desc = " ".join(parts[1:])
                                    desc = clean_description(desc)
                                    
                                    if len(desc) > 5 and not desc.isdigit():
                                        data_rows.append((current_date, desc, price))
                            except (ValueError, IndexError):
                                continue
                                
                except Exception as e:
                    continue
    
    return data_rows

def append_to_csv(row):
    """Append data to the appropriate CSV file based on product type"""
    date, desc, price = row
    
    # Determine which product type this belongs to
    product_type = get_product_type(desc)
    
    if product_type is None:
        print(f"⚠️  Unknown product type for: {desc}")
        return
    
    filename = PRODUCT_MAPPING[product_type]
    csv_path = os.path.join(CSV_DIR, filename)
    os.makedirs(CSV_DIR, exist_ok=True)
    
    # Check if this date already exists in the file
    date_exists = False
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="") as f:
            reader = csv.reader(f)
            for existing_row in reader:
                if len(existing_row) > 0 and existing_row[0] == date:
                    date_exists = True
                    break
    
    if date_exists:
        print(f"📅 Date {date} already exists in {filename}, skipping")
        return
    
    # Write header if file doesn't exist
    write_header = not os.path.exists(csv_path)
    
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Date", "Description", "Price"])
        writer.writerow([date, desc, price])
    
    print(f"✅ Added to {filename}: {date} - {price}")

def process_pdf(pdf_path):
    """Process a single PDF file"""
    print(f"🔍 Processing: {pdf_path}")
    extracted_rows = extract_table_data(pdf_path)
    print(f"📊 Extracted {len(extracted_rows)} rows from PDF")
    
    for row in extracted_rows:
        date, desc, price = row
        print(f"   📝 {desc} → {price}")
        append_to_csv(row)

def process_all_existing_pdfs():
    """One-time function to process all existing PDFs in Downloads folder"""
    print("🔄 Processing all existing PDFs...")
    
    downloads_dir = "Downloads"
    if not os.path.exists(downloads_dir):
        print(f"❌ Downloads directory not found: {downloads_dir}")
        return
    
    # Find all Hindalco PDF files
    pdf_pattern = os.path.join(downloads_dir, "**", "Hindalco_Circular_*.pdf")
    pdf_files = glob.glob(pdf_pattern, recursive=True)
    
    if not pdf_files:
        print("❌ No Hindalco circular PDFs found")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files to process")
    
    for pdf_path in sorted(pdf_files):
        try:
            process_pdf(pdf_path)
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")
    
    print("✅ Finished processing all existing PDFs")

def process_todays_pdf():
    """Process today's PDF (original functionality)"""
    today = datetime.now()
    pdf_folder = os.path.join("Downloads", today.strftime("%Y"), today.strftime("%b"))
    
    # Target Hindalco circular files with format: Hindalco_Circular_DD_Mon_YY.pdf
    pdf_filename = f"Hindalco_Circular_{today.strftime('%d_%b_%y')}.pdf"
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    print(f"🔍 Looking for today's PDF: {pdf_path}")
    
    if os.path.exists(pdf_path):
        process_pdf(pdf_path)
        print(f"✅ Processed today's PDF: {pdf_path}")
    else:
        print("❌ Today's PDF not found.")
        
        # Debug: List available files in the directory
        if os.path.exists(pdf_folder):
            print(f"📁 Files in {pdf_folder}:")
            for file in os.listdir(pdf_folder):
                if file.endswith('.pdf') and 'Hindalco_Circular' in file:
                    print(f"   - {file}")
        else:
            print(f"📁 Directory {pdf_folder} does not exist")

def cleanup_old_csv_files():
    """Remove old CSV files that don't match the new naming convention"""
    if not os.path.exists(CSV_DIR):
        return
    
    valid_filenames = set(PRODUCT_MAPPING.values())
    
    for filename in os.listdir(CSV_DIR):
        if filename.endswith('.csv') and filename not in valid_filenames:
            old_path = os.path.join(CSV_DIR, filename)
            backup_path = os.path.join(CSV_DIR, f"backup_{filename}")
            os.rename(old_path, backup_path)
            print(f"📦 Moved old CSV to backup: {filename}")

if __name__ == "__main__":
    import sys
    
    print("🚀 Hindalco CSV Processor")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Process all existing PDFs (one-time operation)
        cleanup_old_csv_files()
        process_all_existing_pdfs()
    else:
        # Process today's PDF (regular operation)
        process_todays_pdf()
    
    print("\n📊 Current CSV files:")
    if os.path.exists(CSV_DIR):
        for filename in sorted(os.listdir(CSV_DIR)):
            if filename.endswith('.csv') and not filename.startswith('backup_'):
                filepath = os.path.join(CSV_DIR, filename)
                with open(filepath, 'r') as f:
                    line_count = sum(1 for line in f) - 1  # Subtract header
                print(f"   📄 {filename}: {line_count} records")
    else:
        print("   📁 CSV directory not found")
