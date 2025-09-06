# =============================================================================
# SMART PUMP PERFORMANCE REPORT GENERATOR
# =============================================================================
# This application analyzes pump test data from Excel files and generates
# intelligent reports based on pump configuration (Single vs Tandem pumps)

# Import required libraries
import streamlit as st  # For web interface
import pandas as pd     # For data manipulation and analysis
from fpdf import FPDF   # For PDF generation
import io              # For file input/output operations
import os              # For file system operations

# Configure Streamlit page settings
st.set_page_config(page_title="Smart Pump Test Report", layout="wide")

# Display main title
st.title("🔧 Smart Pump Performance Report Generator")

# =============================================================================
# MAIN DATA ANALYSIS FUNCTION
# =============================================================================
def analyze_pump_data(uploaded_file):
    """
    This is the core function that analyzes pump data from Excel files.
    
    How it works:
    1. Reads all sheets from the Excel file (e.g., SinglePump, TandemPump)
    2. For each sheet, finds the header row containing column names
    3. Determines if pumps are Single or Tandem based on P2 data
    4. Returns organized data structure with pump information
    
    Args:
        uploaded_file: Excel file uploaded by user through Streamlit
        
    Returns:
        pump_data: Dictionary containing data for each sheet
        total_pumps: Total number of pumps across all sheets
    """
    try:
        # Step 1: Read all sheet names from the Excel file
        # This allows us to handle files with multiple sheets (SinglePump, TandemPump, etc.)
        excel_data = pd.ExcelFile(uploaded_file)
        sheets = excel_data.sheet_names
        
        # Initialize variables to store pump data and count
        pump_data = {}  # Will store data for each sheet
        total_pumps = 0  # Running count of all pumps
        
        # Step 2: Process each sheet in the Excel file
        for sheet_name in sheets:
            # Read the sheet without assuming header location (header=None)
            # This is important because Excel files often have company headers above data
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
            
            # Step 3: Find the actual header row containing pump data columns
            # We look for key columns like "Eff%" or "Pump Sr. No" to identify data start
            header_candidates = df_raw[df_raw.apply(lambda r: r.astype(str).str.contains("Eff%|Pump Sr. No", na=False).any(), axis=1)]
            
            # Step 4: If we found a header row, process the data
            if not header_candidates.empty:
                header_row = header_candidates.index[0]  # Get the row index
                
                # Read the sheet again, but skip rows until we reach the header
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, skiprows=header_row)
                
                # Clean up column names (remove extra spaces)
                df.columns = df.columns.astype(str).str.strip()
                
                # Step 5: Determine if this is a Single or Tandem pump configuration
                pump_type = determine_pump_type(df, sheet_name)
                
                # Step 6: Store the processed data for this sheet
                pump_data[sheet_name] = {
                    'data': df,           # The actual pump test data
                    'type': pump_type,    # 'Single' or 'Tandem'
                    'count': len(df)      # Number of pumps in this sheet
                }
                
                # Add to total pump count
                total_pumps += len(df)
        
        return pump_data, total_pumps
        
    except Exception as e:
        # If anything goes wrong, show error message to user
        st.error(f"Error reading Excel file: {e}")
        return None, 0

# =============================================================================
# PUMP TYPE DETECTION FUNCTION
# =============================================================================
def determine_pump_type(df, sheet_name):
    """
    Determines if pumps are Single or Tandem based on P2 data analysis.
    
    Logic:
    - Single pumps: Only have P1 data, P2 columns are mostly zero/empty
    - Tandem pumps: Have both P1 and P2 meaningful data
    
    How it works:
    1. Look for P2 efficiency columns in the data
    2. Count how many pumps have non-zero P2 efficiency values
    3. If more than 50% have P2 data, classify as Tandem
    4. Otherwise, classify as Single
    
    Args:
        df: DataFrame containing pump data for one sheet
        sheet_name: Name of the sheet being analyzed
        
    Returns:
        String: "Single" or "Tandem"
    """
    # Step 1: Check sheet name first (explicit naming)
    if 'single' in sheet_name.lower():
        return "Single"
    elif 'tandem' in sheet_name.lower():
        return "Tandem"
    
    # Step 2: If sheet name doesn't give clear indication, analyze data
    # Find P2 efficiency columns
    p2_columns = [col for col in df.columns if 'P2' in col and 'Eff%P2' in col]
    
    if p2_columns:
        # Step 3: Count how many pumps have meaningful P2 efficiency data
        # We check for values greater than 0 because 0% efficiency means no operation
        non_zero_p2_eff = (df['Eff%P2'] > 0).sum() if 'Eff%P2' in df.columns else 0
        
        # Step 4: Decision logic - if more than half the pumps have P2 data, it's Tandem
        # This handles cases where some pumps might have failed P2 tests
        if non_zero_p2_eff > len(df) * 0.5:
            return "Tandem"
        else:
            return "Single"
    else:
        # No P2 columns found, definitely Single pump configuration
        return "Single"

# =============================================================================
# CORRECTED AMPERAGE ANALYSIS FUNCTION
# =============================================================================
def analyze_amperage(pump_data):
    """
    CORRECTED: Analyzes amperage with proper tandem pump logic.
    
    For Single Pumps: Normal min/max analysis
    For Tandem Pumps: Analyze P1 vs P2 matching + combined performance
    
    Key Changes:
    - Tandem pumps counted as UNITS (not individual pumps)
    - P1 vs P2 matching analysis for quality control
    - Mismatch detection for tandem pairs
    
    Args:
        pump_data: Dictionary containing data from all sheets
        
    Returns:
        amp_analysis: Dictionary with min/max/count + tandem analysis
    """
    # Step 1: Initialize data structure with tandem analysis capability
    amp_analysis = {
        '0_bar': {'min': float('inf'), 'max': 0, 'unit_count': 0, 'tandem_analysis': []},
        '200_bar': {'min': float('inf'), 'max': 0, 'unit_count': 0, 'tandem_analysis': []}
    }
    
    # Step 2: Process each sheet of pump data
    for sheet_name, sheet_data in pump_data.items():
        df = sheet_data['data']  # Get the actual data
        pump_type = sheet_data['type']  # Single or Tandem
        
        if pump_type == "Single":
            # Step 3: Handle Single Pumps (original logic)
            for condition in ['0_bar', '200_bar']:
                # Fix: Properly construct column names
                if condition == '0_bar':
                    col_name = '0 Bar Amp P1'
                else:  # 200_bar
                    col_name = '200 Bar Amp P1'
                
                if col_name in df.columns:
                    # Find non-zero values for min/max calculation
                    non_zero_values = df[df[col_name] > 0][col_name]
                    if not non_zero_values.empty:
                        amp_analysis[condition]['min'] = min(amp_analysis[condition]['min'], non_zero_values.min())
                        amp_analysis[condition]['max'] = max(amp_analysis[condition]['max'], non_zero_values.max())
                    
                    # Count units (each row = 1 unit for single pumps)
                    amp_analysis[condition]['unit_count'] += len(df)
        
        else:  # Step 4: Handle Tandem Pumps (NEW LOGIC)
            # For tandem pumps: each row is ONE unit with TWO pumps
            for condition in ['0_bar', '200_bar']:
                # Fix: Properly construct column names
                if condition == '0_bar':
                    p1_col = '0 Bar Amp P1'
                    p2_col = '0 Bar Amp P2'
                else:  # 200_bar
                    p1_col = '200 Bar Amp P1'
                    p2_col = '200 Bar Amp P2'
                
                if p1_col in df.columns and p2_col in df.columns:
                    # Step 4a: Analyze each tandem unit (row)
                    for idx, row in df.iterrows():
                        p1_amp = row[p1_col]
                        p2_amp = row[p2_col]
                        
                        # Step 4b: Analyze P1 vs P2 matching for quality control
                        if p1_amp > 0 and p2_amp > 0:
                            difference = abs(p1_amp - p2_amp)
                            percentage_diff = (difference / max(p1_amp, p2_amp)) * 100
                            
                            # Store tandem matching analysis
                            amp_analysis[condition]['tandem_analysis'].append({
                                'unit_id': row.get('Pump Sr. No', f'Unit_{idx+1}'),
                                'p1_amp': p1_amp,
                                'p2_amp': p2_amp,
                                'difference': difference,
                                'percentage_diff': percentage_diff
                            })
                            
                            # Step 4c: Update min/max with both P1 and P2 values
                            amp_analysis[condition]['min'] = min(amp_analysis[condition]['min'], p1_amp, p2_amp)
                            amp_analysis[condition]['max'] = max(amp_analysis[condition]['max'], p1_amp, p2_amp)
                    
                    # Step 4d: Count UNITS (not individual pumps)
                    amp_analysis[condition]['unit_count'] += len(df)
    
    # Step 5: Handle edge case where no valid readings were found
    for condition in ['0_bar', '200_bar']:
        if amp_analysis[condition]['min'] == float('inf'):
            amp_analysis[condition]['min'] = 0
    
    return amp_analysis

# =============================================================================
# CORRECTED EFFICIENCY DISTRIBUTION ANALYSIS FUNCTION
# =============================================================================
def analyze_efficiency_distribution(pump_data):
    """
    CORRECTED: Analyzes efficiency with proper tandem pump logic.
    
    For Single Pumps: Count individual pump efficiencies
    For Tandem Pumps: Analyze P1 vs P2 matching + individual performance
    
    Key Changes:
    - Separate tracking for individual pumps vs units
    - P1 vs P2 matching analysis for tandem pumps
    - Quality control metrics for tandem pairs
    
    Args:
        pump_data: Dictionary containing data from all sheets
        
    Returns:
        efficiency_ranges: Dictionary with counts for each efficiency range
        total_individual_pumps: Total number of individual pump readings
        tandem_matching_analysis: List of tandem P1 vs P2 comparisons
    """
    # Step 1: Initialize counters for efficiency ranges
    efficiency_ranges = {
        '90_to_92': 0,    # 90% ≤ efficiency < 92%
        '92_to_94': 0,    # 92% ≤ efficiency < 94%
        '94_plus': 0      # efficiency ≥ 94%
    }
    
    # Step 2: Initialize tandem analysis tracking
    tandem_matching_analysis = []  # List to store P1 vs P2 comparisons
    total_individual_pumps = 0     # Count of individual pump readings
    
    # Step 3: Process each sheet of pump data
    for sheet_name, sheet_data in pump_data.items():
        df = sheet_data['data']  # Get the actual data
        pump_type = sheet_data['type']  # Single or Tandem
        
        if pump_type == "Single":
            # Step 4: Handle Single Pumps (normal efficiency counting)
            if 'Eff%P1' in df.columns:
                valid_efficiencies = df[df['Eff%P1'] > 0]['Eff%P1']
                
                # Categorize each efficiency value
                for eff in valid_efficiencies:
                    if 90 <= eff < 92:
                        efficiency_ranges['90_to_92'] += 1
                    elif 92 <= eff < 94:
                        efficiency_ranges['92_to_94'] += 1
                    elif eff >= 94:
                        efficiency_ranges['94_plus'] += 1
                
                # Count individual pumps
                total_individual_pumps += len(valid_efficiencies)
        
        else:  # Step 5: Handle Tandem Pumps (NEW LOGIC)
            # For tandem pumps: analyze both P1 and P2, plus matching
            for idx, row in df.iterrows():
                p1_eff = row.get('Eff%P1', 0)
                p2_eff = row.get('Eff%P2', 0)
                
                if p1_eff > 0 and p2_eff > 0:
                    # Step 5a: Analyze P1 vs P2 matching for quality control
                    difference = abs(p1_eff - p2_eff)
                    average_eff = (p1_eff + p2_eff) / 2
                    
                    # Store tandem matching analysis
                    tandem_matching_analysis.append({
                        'unit_id': row.get('Pump Sr. No', f'Unit_{idx+1}'),
                        'p1_eff': p1_eff,
                        'p2_eff': p2_eff,
                        'difference': difference,
                        'average_eff': average_eff
                    })
                    
                    # Step 5b: Count individual pump efficiencies
                    # Each tandem unit contributes 2 individual pump readings
                    for eff in [p1_eff, p2_eff]:
                        if 90 <= eff < 92:
                            efficiency_ranges['90_to_92'] += 1
                        elif 92 <= eff < 94:
                            efficiency_ranges['92_to_94'] += 1
                        elif eff >= 94:
                            efficiency_ranges['94_plus'] += 1
                    
                    # Count individual pumps (2 per tandem unit)
                    total_individual_pumps += 2
    
    # Step 6: Return results with tandem analysis
    return efficiency_ranges, total_individual_pumps, tandem_matching_analysis

# =============================================================================
# REPORT CONTENT GENERATION FUNCTION
# =============================================================================
def generate_report_content(pump_data, total_pumps, amp_analysis, efficiency_ranges, total_efficiency_readings, tandem_matching_analysis=None):
    """
    CORRECTED: Generates report with proper tandem pump analysis
    
    This function creates a professional text report that includes:
    1. Pump configuration analysis (Units vs Individual Pumps)
    2. Amperage analysis with tandem matching
    3. Efficiency distribution with tandem quality control
    
    Args:
        pump_data: Dictionary containing data from all sheets
        total_pumps: Total number of pumps tested (individual pumps)
        amp_analysis: Dictionary with amperage statistics + tandem analysis
        efficiency_ranges: Dictionary with efficiency distribution
        total_efficiency_readings: Total efficiency values analyzed
        tandem_matching_analysis: List of tandem P1 vs P2 comparisons
        
    Returns:
        String containing the complete formatted report
    """
    report_lines = []  # List to build report line by line
    
    # =============================================================================
    # SECTION 1: REPORT HEADER
    # =============================================================================
    report_lines.append("PUMP PERFORMANCE TEST REPORT")
    report_lines.append("=" * 50)  # Decorative line
    report_lines.append("")  # Empty line for spacing
    
    # =============================================================================
    # SECTION 2: PUMP CONFIGURATION ANALYSIS (CORRECTED)
    # =============================================================================
    report_lines.append("PUMP CONFIGURATION ANALYSIS:")
    report_lines.append("-" * 28)  # Decorative underline
    
    total_units = 0
    has_tandem = False
    
    # Analyze each sheet configuration
    for sheet_name, data in pump_data.items():
        if data['type'] == 'Tandem':
            has_tandem = True
            report_lines.append(f"{sheet_name}: {data['count']} Tandem units (each with 2 pumps)")
            total_units += data['count']
        else:
            report_lines.append(f"{sheet_name}: {data['count']} Single pump units")
            total_units += data['count']
    
    report_lines.append(f"Total units tested: {total_units}")
    report_lines.append(f"Total individual pumps: {total_efficiency_readings}")
    report_lines.append("")
    
    # =============================================================================
    # SECTION 3: AMPERAGE ANALYSIS (CORRECTED)
    # =============================================================================
    report_lines.append("AMPERAGE ANALYSIS:")
    report_lines.append("-" * 18)  # Decorative underline
    
    for condition in ['0_bar', '200_bar']:
        condition_name = condition.replace('_', ' ').title()
        report_lines.append(f"{condition_name} Conditions:")
        
        if amp_analysis[condition]['unit_count'] > 0:
            if amp_analysis[condition]['max'] > 0:
                report_lines.append(f"  Minimum amperage: {amp_analysis[condition]['min']:.2f} A")
                report_lines.append(f"  Maximum amperage: {amp_analysis[condition]['max']:.2f} A")
            
            # Add tandem matching analysis if available
            if amp_analysis[condition]['tandem_analysis']:
                mismatched_units = [unit for unit in amp_analysis[condition]['tandem_analysis'] 
                                  if unit['percentage_diff'] > 10]  # 10% threshold for mismatch
                
                report_lines.append(f"  Tandem pump matching analysis:")
                report_lines.append(f"    - Total tandem units: {len(amp_analysis[condition]['tandem_analysis'])}")
                report_lines.append(f"    - Units with >10% P1/P2 difference: {len(mismatched_units)}")
                
                if mismatched_units:
                    worst_mismatch = max(mismatched_units, key=lambda x: x['percentage_diff'])
                    report_lines.append(f"    - Worst mismatch: {worst_mismatch['percentage_diff']:.1f}% (Unit {worst_mismatch['unit_id']})")
                else:
                    report_lines.append(f"    - All tandem units within 10% tolerance")
            
            report_lines.append(f"  Total units analyzed: {amp_analysis[condition]['unit_count']}")
        else:
            report_lines.append("  No data available")
        
        report_lines.append("")
    
    # =============================================================================
    # SECTION 4: EFFICIENCY ANALYSIS (CORRECTED)
    # =============================================================================
    report_lines.append("EFFICIENCY ANALYSIS:")
    report_lines.append("-" * 20)
    report_lines.append(f"Individual pump efficiencies analyzed: {total_efficiency_readings}")
    report_lines.append("")
    report_lines.append(f"90% - 92%:     {efficiency_ranges['90_to_92']} pumps")
    report_lines.append(f"92% - 94%:     {efficiency_ranges['92_to_94']} pumps")
    report_lines.append(f"94% and above: {efficiency_ranges['94_plus']} pumps")
    
    # Add tandem efficiency matching analysis
    if tandem_matching_analysis and has_tandem:
        report_lines.append("")
        report_lines.append("TANDEM PUMP MATCHING (P1 vs P2):")
        report_lines.append("-" * 33)
        
        if tandem_matching_analysis:
            avg_differences = [unit['difference'] for unit in tandem_matching_analysis]
            avg_diff = sum(avg_differences) / len(avg_differences)
            
            report_lines.append(f"Total tandem units analyzed: {len(tandem_matching_analysis)}")
            report_lines.append(f"Average efficiency difference: {avg_diff:.2f}%")
            
            # Count units with significant efficiency differences
            mismatched_eff_units = [unit for unit in tandem_matching_analysis if unit['difference'] > 3]
            report_lines.append(f"Units with >3% efficiency difference: {len(mismatched_eff_units)}")
            
            if mismatched_eff_units:
                worst_eff_mismatch = max(mismatched_eff_units, key=lambda x: x['difference'])
                report_lines.append(f"Worst efficiency mismatch: {worst_eff_mismatch['difference']:.2f}% (Unit {worst_eff_mismatch['unit_id']})")
            else:
                report_lines.append("All tandem units within 3% efficiency tolerance")
    
    # Join all report lines into a single string with newlines
    return "\n".join(report_lines)

# =============================================================================
# PDF REPORT GENERATION FUNCTION
# =============================================================================
def create_pdf_report(report_content, customer_name, order_no):
    """
    Creates a professional PDF report from the text content.
    
    This function:
    1. Creates a new PDF document with company branding
    2. Adds customer information and order details
    3. Formats the report content with appropriate fonts and styling
    4. Returns the PDF as bytes for download
    
    Args:
        report_content: String containing the formatted report text
        customer_name: Customer name for the header
        order_no: Order number for the header
        
    Returns:
        PDF file as bytes (ready for download)
    """
    # Step 1: Create a new PDF document
    pdf = FPDF()
    pdf.add_page()  # Add first page
    
    # Step 2: Set up company branding
    company_name = "VBC HYDRAULICS"
    logo_path = "assets/logo.png"  # Path to company logo
    
    # Add logo if it exists
    if os.path.exists(logo_path):
        pdf.image(logo_path, 10, 8, 33)  # x=10, y=8, width=33
    
    # Step 3: Add company name header
    pdf.set_font("Arial", "B", 16)  # Bold, 16pt font
    pdf.cell(200, 10, company_name, ln=True, align="C")  # Centered
    pdf.ln(5)  # Add some space
    
    # Step 4: Add customer information
    pdf.set_font("Arial", "", 12)  # Regular, 12pt font
    pdf.cell(200, 10, f"Customer: {customer_name}", ln=True)
    pdf.cell(200, 10, f"Order No.: {order_no}", ln=True)
    pdf.ln(10)  # Add more space before report content
    
    # Step 5: Process and add report content
    pdf.set_font("Arial", "", 10)  # Regular, 10pt font for body text
    
    # Split the report content into individual lines for processing
    lines = report_content.split('\n')
    
    # Process each line with appropriate formatting
    for line in lines:
        if line.startswith("PUMP PERFORMANCE TEST REPORT"):
            # Main title - larger, bold, centered
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 8, line, ln=True, align="C")
            pdf.set_font("Arial", "", 10)  # Reset to normal font
        elif line.startswith("="):
            # Decorative lines - just add some space
            pdf.ln(2)
        elif line.endswith(":") and not line.startswith(" "):
            # Section headers - bold
            pdf.set_font("Arial", "B", 11)
            pdf.cell(200, 6, line, ln=True)
            pdf.set_font("Arial", "", 10)  # Reset to normal font
        elif line.startswith("-"):
            # Underlines - just add minimal space
            pdf.ln(1)
        else:
            # Regular content lines
            pdf.cell(200, 5, line, ln=True)
    
    # Step 6: Return PDF as bytes for download
    # The 'dest="S"' parameter returns the PDF as a string instead of saving to file
    # encode("latin-1") converts it to bytes format required by Streamlit
    return pdf.output(dest="S").encode("latin-1")

# =============================================================================
# STREAMLIT USER INTERFACE
# =============================================================================
# This section creates the web interface that users interact with

# --- COMPANY INFORMATION SECTION ---
# Set up company branding and customer input fields
company_name = "VBC Hydraulics"  # Company name for reports
customer_name = st.text_input("Customer Name", "Customer XYZ")  # Input field for customer
order_no = st.text_input("Order No.", "ORD-1234")  # Input field for order number

# --- FILE UPLOAD SECTION ---
# Create file uploader widget that accepts Excel files
uploaded_file = st.file_uploader(
    "Upload Pump Test Report (Excel file with multiple sheets)", 
    type=["xlsx"]  # Only accept Excel files
)

# =============================================================================
# MAIN PROCESSING LOGIC
# =============================================================================
# This section runs when a file is uploaded

if uploaded_file:
    # Display section header
    st.subheader("📊 Smart Analysis Results")
    
    # --- STEP 1: ANALYZE THE UPLOADED DATA ---
    # Call our main analysis function to process the Excel file
    pump_data, total_pumps = analyze_pump_data(uploaded_file)
    
    # Check if we successfully extracted pump data
    if pump_data and total_pumps > 0:
        
        # --- STEP 2: PERFORM DETAILED ANALYSIS ---
        # Run amperage analysis (min/max for 0 bar and 200 bar + tandem matching)
        amp_analysis = analyze_amperage(pump_data)
        
        # Run efficiency distribution analysis (90-92%, 92-94%, 94%+ + tandem matching)
        efficiency_ranges, total_efficiency_readings, tandem_matching_analysis = analyze_efficiency_distribution(pump_data)
        
        # --- STEP 3: GENERATE WRITTEN REPORT ---
        # Create formatted text report with all analysis results (including tandem analysis)
        report_content = generate_report_content(
            pump_data, 
            total_pumps, 
            amp_analysis, 
            efficiency_ranges, 
            total_efficiency_readings,
            tandem_matching_analysis  # Pass tandem analysis results
        )
        
        # --- STEP 4: DISPLAY REPORT TO USER ---
        # Show the generated report in a text area (scrollable, read-only)
        st.text_area("Report Content", report_content, height=400)
        
        # --- STEP 5: OPTIONAL RAW DATA DISPLAY ---
        # Provide checkbox to show underlying data if user wants to see details
        if st.checkbox("Show Raw Data"):
            # Display data from each sheet separately
            for sheet_name, sheet_data in pump_data.items():
                st.subheader(f"📋 {sheet_name} Data ({sheet_data['type']} Pump)")
                st.dataframe(sheet_data['data'])  # Display as interactive table
        
        # --- STEP 6: PDF EXPORT FUNCTIONALITY ---
        # Provide button to generate and download PDF report
        if st.button("📥 Export PDF Report"):
            # Generate PDF with current report content and customer info
            pdf_bytes = create_pdf_report(report_content, customer_name, order_no)
            
            # Create download button for the PDF
            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"Smart_Pump_Report_{order_no}.pdf",  # Dynamic filename
                mime="application/pdf"
            )
    else:
        # Error handling: No valid pump data found
        st.error("No pump data found in the uploaded file. Please check the file format.")

else:
    # =============================================================================
    # HELP AND INSTRUCTIONS SECTION
    # =============================================================================
    # This section displays when no file is uploaded
    
    st.info("Please upload an Excel file with pump test data to generate a smart report.")
    
    # --- INSTRUCTIONS FOR USERS ---
    st.subheader("📋 Instructions")
    st.write("""
    **How to use this Smart Pump Report Generator:**
    
    1. **Upload Excel File**: Select an Excel file containing pump test data
    2. **Automatic Analysis**: The app will automatically:
       - Detect if pumps are Single or Tandem configuration
       - Analyze amperage data for 0 bar and 200 bar conditions
       - Categorize pumps by volumetric efficiency ranges
    3. **Review Report**: Check the generated written report
    4. **Export PDF**: Download a professional PDF report
    
    **File Requirements:**
    - Excel file (.xlsx) with pump test data
    - Data should include columns for efficiency, amperage, and pump serial numbers
    - The app supports multiple sheets (SinglePump, TandemPump, etc.)
    
    **Analysis Features:**
    - **Amperage Analysis**: Finds minimum and maximum amperage values (ignoring zeros)
    - **Efficiency Distribution**: Categorizes pumps into 90-92%, 92-94%, and 94%+ ranges
    - **Smart Detection**: Automatically determines Single vs Tandem pump configurations
    - **Professional Reports**: Generates formatted text and PDF reports
    """)

