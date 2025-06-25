import os
import csv
from datetime import datetime
from PyPDF2 import PdfReader

CSV_DIR = "csv"

def sanitize_filename(text):
    return text.replace("/", "-").replace("\"", "").replace(",", "").replace(":", "").replace(" ", "_")

def extract_date_from_text(text):
    import re
    match = re.search(r'w\.e\.f\.\s*(\d{2}\.\d{2}\.\d{4})', text)
    if match:
        date_obj = datetime.strptime(match.group(1), "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")

def extract_table_data(pdf_path):
    reader = PdfReader(pdf_path)
    text = "\n".join([page.extract_text() for page in reader.pages])
    lines = text.splitlines()

    data_rows = []
    current_date = extract_date_from_text(text)

    for line in lines:
        if line.strip()[:2] in {"1.", "2.", "3.", "4.", "5.", "6.", "7."}:
            parts = line.strip().split()
            try:
                price = int(parts[-1].replace(",", ""))
                desc = " ".join(parts[1:-1])
                data_rows.append((current_date, desc, price))
            except:
                continue

    return data_rows

def append_to_csv(row):
    date, desc, price = row
    filename = sanitize_filename(desc) + ".csv"
    csv_path = os.path.join(CSV_DIR, filename)
    os.makedirs(CSV_DIR, exist_ok=True)

    # Skip if this date already exists
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="") as f:
            if any(date in line for line in f):
                return

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, desc, price])

def process_pdf(pdf_path):
    extracted_rows = extract_table_data(pdf_path)
    for row in extracted_rows:
        append_to_csv(row)

if __name__ == "__main__":
    today = datetime.now()
    pdf_folder = os.path.join("Downloads", today.strftime("%Y"), today.strftime("%b"))
    pdf_filename = f"primary-ready-reckoner-{today.strftime('%d-%b-%Y').lower()}.pdf"
    pdf_path = os.path.join(pdf_folder, pdf_filename)

    print(f"🔍 Looking for: {pdf_path}")
    if os.path.exists(pdf_path):
        process_pdf(pdf_path)
        print(f"✅ Processed and updated CSVs from: {pdf_path}")
    else:
        print("❌ PDF not found. Skipping.")
        exit(0)  # Graceful exit with no error
