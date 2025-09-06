import pandas as pd
import os

# Test reading the Excel file
excel_file = "PumpReport_2Sept.xlsx"

try:
    # Check if file exists
    if os.path.exists(excel_file):
        print(f"File {excel_file} exists")
        
        # Try to read the Excel file
        df_raw = pd.read_excel(excel_file, header=None)
        print(f"Excel file loaded successfully!")
        print(f"Shape: {df_raw.shape}")
        print("First few rows:")
        print(df_raw.head(10))
        
        # Find header row (looking for key columns)
        header_candidates = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains("Eff%P1|Pump Sr. No", na=False).any(), axis=1)]
        if not header_candidates.empty:
            header_row = header_candidates.index[0]
            print(f"\nFound header row at index: {header_row}")
            
            # Read with proper header
            df = pd.read_excel(excel_file, skiprows=header_row)
            df.columns = df.columns.astype(str).str.strip()
            print(f"\nColumns found: {list(df.columns)}")
            print(f"Data shape with header: {df.shape}")
            print("\nFirst few rows with proper headers:")
            print(df.head())
        else:
            print("No header row found with expected columns")
            
    else:
        print(f"File {excel_file} not found")
        
except Exception as e:
    print(f"Error reading Excel file: {e}")
