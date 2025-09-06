import pandas as pd
import os

# Analyze the Excel file structure
excel_file = "PumpReport_2Sept.xlsx"

try:
    # Read all sheets
    excel_data = pd.ExcelFile(excel_file)
    print(f"Sheet names: {excel_data.sheet_names}")
    
    for sheet_name in excel_data.sheet_names:
        print(f"\n=== Sheet: {sheet_name} ===")
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        print(f"Shape: {df.shape}")
        print("First 15 rows:")
        print(df.head(15))
        
        # Look for header row
        header_candidates = df[df.apply(lambda r: r.astype(str).str.contains("Eff%|Pump Sr. No", na=False).any(), axis=1)]
        if not header_candidates.empty:
            header_row = header_candidates.index[0]
            print(f"\nHeader row found at index: {header_row}")
            
            # Read with proper header
            df_with_header = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_row)
            print(f"Columns: {list(df_with_header.columns)}")
            print(f"Data rows: {len(df_with_header)}")
            
except Exception as e:
    print(f"Error: {e}")
