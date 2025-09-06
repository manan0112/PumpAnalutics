import pandas as pd

# Test the fixed pump type detection and amperage analysis
excel_file = "PumpReport_2Sept.xlsx"

def determine_pump_type(df, sheet_name):
    # Check sheet name first
    if 'single' in sheet_name.lower():
        return "Single"
    elif 'tandem' in sheet_name.lower():
        return "Tandem"
    
    # Analyze data if sheet name unclear
    p2_columns = [col for col in df.columns if 'P2' in col and 'Eff%P2' in col]
    
    if p2_columns:
        non_zero_p2_eff = (df['Eff%P2'] > 0).sum() if 'Eff%P2' in df.columns else 0
        if non_zero_p2_eff > len(df) * 0.5:
            return "Tandem"
        else:
            return "Single"
    else:
        return "Single"

# Test each sheet
pump_data = {}
for sheet_name in ['SinglePump', 'TandemPump']:
    print(f"\n=== Testing {sheet_name} ===")
    
    # Read sheet and find header row
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    header_candidates = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains("Eff%|Pump Sr. No", na=False).any(), axis=1)]
    
    if not header_candidates.empty:
        header_row = header_candidates.index[0]
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_row)
        df.columns = df.columns.astype(str).str.strip()
        
        pump_type = determine_pump_type(df, sheet_name)
        print(f"Pump type: {pump_type}")
        
        pump_data[sheet_name] = {
            'data': df,
            'type': pump_type,
            'count': len(df)
        }

# Test amperage analysis
print(f"\n=== AMPERAGE ANALYSIS TEST ===")

amp_analysis = {
    '0_bar': {'min': float('inf'), 'max': 0, 'unit_count': 0, 'tandem_analysis': []},
    '200_bar': {'min': float('inf'), 'max': 0, 'unit_count': 0, 'tandem_analysis': []}
}

for sheet_name, sheet_data in pump_data.items():
    df = sheet_data['data']
    pump_type = sheet_data['type']
    
    print(f"\nProcessing {sheet_name} ({pump_type})...")
    
    if pump_type == "Single":
        for condition in ['0_bar', '200_bar']:
            if condition == '0_bar':
                col_name = '0 Bar Amp P1'
            else:
                col_name = '200 Bar Amp P1'
            
            if col_name in df.columns:
                non_zero_values = df[df[col_name] > 0][col_name]
                print(f"  {col_name}: {len(non_zero_values)} non-zero values")
                
                if not non_zero_values.empty:
                    amp_analysis[condition]['min'] = min(amp_analysis[condition]['min'], non_zero_values.min())
                    amp_analysis[condition]['max'] = max(amp_analysis[condition]['max'], non_zero_values.max())
                
                amp_analysis[condition]['unit_count'] += len(df)
    
    else:  # Tandem
        for condition in ['0_bar', '200_bar']:
            if condition == '0_bar':
                p1_col = '0 Bar Amp P1'
                p2_col = '0 Bar Amp P2'
            else:
                p1_col = '200 Bar Amp P1'
                p2_col = '200 Bar Amp P2'
            
            if p1_col in df.columns and p2_col in df.columns:
                non_zero_p1 = (df[p1_col] > 0).sum()
                non_zero_p2 = (df[p2_col] > 0).sum()
                print(f"  {p1_col}: {non_zero_p1} non-zero values")
                print(f"  {p2_col}: {non_zero_p2} non-zero values")
                
                for idx, row in df.iterrows():
                    p1_amp = row[p1_col]
                    p2_amp = row[p2_col]
                    
                    if p1_amp > 0 and p2_amp > 0:
                        amp_analysis[condition]['min'] = min(amp_analysis[condition]['min'], p1_amp, p2_amp)
                        amp_analysis[condition]['max'] = max(amp_analysis[condition]['max'], p1_amp, p2_amp)
                
                amp_analysis[condition]['unit_count'] += len(df)

# Handle edge case
for condition in ['0_bar', '200_bar']:
    if amp_analysis[condition]['min'] == float('inf'):
        amp_analysis[condition]['min'] = 0

print(f"\n=== RESULTS ===")
for condition in ['0_bar', '200_bar']:
    print(f"{condition.replace('_', ' ').title()} Conditions:")
    print(f"  Min: {amp_analysis[condition]['min']:.2f} A")
    print(f"  Max: {amp_analysis[condition]['max']:.2f} A")
    print(f"  Unit count: {amp_analysis[condition]['unit_count']}")
