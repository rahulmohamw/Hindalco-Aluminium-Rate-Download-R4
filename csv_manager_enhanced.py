name: PDF to CSV Conversion Workflow

on:
  push:
    paths:
      - 'pdf/**'
  workflow_dispatch:
    inputs:
      force_run:
        description: 'Force run even if no PDF changes'
        required: false
        default: 'false'

jobs:
  convert-pdf-to-csv:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pandas pdfplumber openpyxl pathlib2
        
    - name: Create necessary directories
      run: |
        mkdir -p pdf csv backups
        
    - name: Run PDF to CSV conversion
      run: |
        python csv_manager.py workflow
        
    - name: Check for changes
      id: check_changes
      run: |
        git diff --quiet csv/ || echo "changes=true" >> $GITHUB_OUTPUT
        
    - name: Commit and push changes
      if: steps.check_changes.outputs.changes == 'true'
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add csv/
        git add backups/
        git commit -m "Auto-update CSV files from PDF processing [$(date +'%Y-%m-%d %H:%M:%S')]"
        git push
        
    - name: Upload CSV files as artifact
      uses: actions/upload-artifact@v4
      with:
        name: csv-files
        path: csv/
        
    - name: Upload processing logs
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: processing-logs
        path: |
          *.log
          backups/
