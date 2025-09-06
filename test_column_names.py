import pandas as pd

# Quick test to verify column name construction
excel_file = "PumpReport_2Sept.xlsx"

# Test both sheets
for sheet_name in ['SinglePump', 'TandemPump']:
    print(f"\n=== Testing {sheet_name} ===")
    
    # Read sheet and find header row
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    header_candidates = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains("Eff%|Pump Sr. No", na=False).any(), axis=1)]
    
    if not header_candidates.empty:
        header_row = header_candidates.index[0]
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_row)
        df.columns = df.columns.astype(str).str.strip()
        
        print("Available columns:")
        amperage_cols = [col for col in df.columns if 'Amp' in col]
        for col in amperage_cols:
            print(f"  - {col}")
        
        # Test our column name construction
        test_cols = ['0 Bar Amp P1', '0 Bar Amp P2', '200 Bar Amp P1', '200 Bar Amp P2']
        print("\nColumn existence check:")
        for col in test_cols:
            exists = col in df.columns
            print(f"  - {col}: {'✅' if exists else '❌'}")
        
        # Test data availability
        if '0 Bar Amp P1' in df.columns:
            non_zero_count = (df['0 Bar Amp P1'] > 0).sum()
            print(f"\n0 Bar Amp P1 non-zero values: {non_zero_count}")
            print(f"Sample values: {df['0 Bar Amp P1'].head(3).tolist()}")
        
        if '200 Bar Amp P1' in df.columns:
            non_zero_count = (df['200 Bar Amp P1'] > 0).sum()
            print(f"200 Bar Amp P1 non-zero values: {non_zero_count}")
            print(f"Sample values: {df['200 Bar Amp P1'].head(3).tolist()}")
