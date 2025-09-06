import pandas as pd
import sys
import os

# Test the smart pump analysis functionality
def test_pump_analysis():
    excel_file = "PumpReport_2Sept.xlsx"
    
    try:
        # Read all sheets from Excel file
        excel_data = pd.ExcelFile(excel_file)
        sheets = excel_data.sheet_names
        print(f"Found sheets: {sheets}")
        
        pump_data = {}
        total_pumps = 0
        
        for sheet_name in sheets:
            # Read sheet and find header row
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            
            # Find header row containing pump data columns
            header_candidates = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains("Eff%|Pump Sr. No", na=False).any(), axis=1)]
            
            if not header_candidates.empty:
                header_row = header_candidates.index[0]
                df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_row)
                df.columns = df.columns.astype(str).str.strip()
                
                # Determine pump type based on data
                p2_columns = [col for col in df.columns if 'P2' in col and 'Eff%P2' in col]
                
                if p2_columns:
                    # Count non-zero efficiency values in P2
                    non_zero_p2_eff = (df['Eff%P2'] > 0).sum() if 'Eff%P2' in df.columns else 0
                    
                    # If more than half of the pumps have P2 efficiency data, it's tandem
                    if non_zero_p2_eff > len(df) * 0.5:
                        pump_type = "Tandem"
                    else:
                        pump_type = "Single"
                else:
                    pump_type = "Single"
                
                pump_data[sheet_name] = {
                    'data': df,
                    'type': pump_type,
                    'count': len(df)
                }
                total_pumps += len(df)
                
                print(f"\nSheet: {sheet_name}")
                print(f"Type: {pump_type}")
                print(f"Count: {len(df)}")
        
        print(f"\nTotal pumps: {total_pumps}")
        
        # Test amperage analysis
        amp_analysis = {
            '0_bar': {'min': float('inf'), 'max': 0, 'pump_count': 0},
            '200_bar': {'min': float('inf'), 'max': 0, 'pump_count': 0}
        }
        
        for sheet_name, sheet_data in pump_data.items():
            df = sheet_data['data']
            
            # Analyze 0 Bar amperage
            for p_num in ['P1', 'P2']:
                col_name = f'0 Bar Amp {p_num}'
                if col_name in df.columns:
                    # Filter out zero values but count the pump
                    non_zero_values = df[df[col_name] > 0][col_name]
                    if not non_zero_values.empty:
                        amp_analysis['0_bar']['min'] = min(amp_analysis['0_bar']['min'], non_zero_values.min())
                        amp_analysis['0_bar']['max'] = max(amp_analysis['0_bar']['max'], non_zero_values.max())
                    
                    # Count pumps (including those with 0 readings)
                    amp_analysis['0_bar']['pump_count'] += len(df)
            
            # Analyze 200 Bar amperage
            for p_num in ['P1', 'P2']:
                col_name = f'200 Bar Amp {p_num}'
                if col_name in df.columns:
                    # Filter out zero values but count the pump
                    non_zero_values = df[df[col_name] > 0][col_name]
                    if not non_zero_values.empty:
                        amp_analysis['200_bar']['min'] = min(amp_analysis['200_bar']['min'], non_zero_values.min())
                        amp_analysis['200_bar']['max'] = max(amp_analysis['200_bar']['max'], non_zero_values.max())
                    
                    # Count pumps (including those with 0 readings)
                    amp_analysis['200_bar']['pump_count'] += len(df)
        
        # Handle case where no valid readings found
        for condition in ['0_bar', '200_bar']:
            if amp_analysis[condition]['min'] == float('inf'):
                amp_analysis[condition]['min'] = 0
        
        print(f"\nAmperage Analysis:")
        print(f"0 Bar - Min: {amp_analysis['0_bar']['min']:.2f}A, Max: {amp_analysis['0_bar']['max']:.2f}A, Count: {amp_analysis['0_bar']['pump_count']}")
        print(f"200 Bar - Min: {amp_analysis['200_bar']['min']:.2f}A, Max: {amp_analysis['200_bar']['max']:.2f}A, Count: {amp_analysis['200_bar']['pump_count']}")
        
        # Test efficiency analysis
        efficiency_ranges = {
            '90_to_92': 0,
            '92_to_94': 0,
            '94_plus': 0
        }
        
        all_efficiencies = []
        
        for sheet_name, sheet_data in pump_data.items():
            df = sheet_data['data']
            
            # Collect efficiency values from both P1 and P2 (if applicable)
            for p_num in ['P1', 'P2']:
                eff_col = f'Eff%{p_num}'
                if eff_col in df.columns:
                    # Only include non-zero efficiency values
                    valid_efficiencies = df[df[eff_col] > 0][eff_col]
                    all_efficiencies.extend(valid_efficiencies.tolist())
        
        # Categorize efficiencies (only for ranges 90+)
        for eff in all_efficiencies:
            if 90 <= eff < 92:
                efficiency_ranges['90_to_92'] += 1
            elif 92 <= eff < 94:
                efficiency_ranges['92_to_94'] += 1
            elif eff >= 94:
                efficiency_ranges['94_plus'] += 1
        
        print(f"\nEfficiency Distribution:")
        print(f"90-92%: {efficiency_ranges['90_to_92']} pumps")
        print(f"92-94%: {efficiency_ranges['92_to_94']} pumps")
        print(f"94%+: {efficiency_ranges['94_plus']} pumps")
        print(f"Total efficiency readings: {len(all_efficiencies)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_pump_analysis()
