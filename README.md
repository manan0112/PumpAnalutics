# VBC Hydraulics - Smart Pump Test Report Generator

## Overview
This application analyzes pump test data from Excel files and generates intelligent reports based on pump configuration (Single vs Tandem pumps).

## Features
- **Smart Pump Detection**: Automatically identifies Single vs Tandem pump configurations
- **Amperage Analysis**: Min/max amperage values with tandem pump matching analysis
- **Efficiency Distribution**: Categorizes pumps into 90-92%, 92-94%, and 94%+ ranges
- **Quality Control**: P1 vs P2 matching analysis for tandem pumps
- **Professional Reports**: Generated text and PDF reports with company branding

## How to Use
1. **Upload Excel File**: Select your pump test data file (.xlsx)
2. **Enter Customer Info**: Fill in customer name and order number
3. **Review Analysis**: Check the automatically generated report
4. **Export PDF**: Download professional PDF report

## File Requirements
- Excel file (.xlsx) with pump test data
- Data should include columns for efficiency, amperage, and pump serial numbers
- Supports multiple sheets (SinglePump, TandemPump, etc.)

## Technical Details
- Built with Streamlit for web interface
- Uses pandas for data analysis
- Generates PDF reports with fpdf library
- Handles both single and tandem pump configurations

## For QC Teams
- **Unit-based counting**: Tandem pumps counted as units (not individual pumps)
- **Mismatch detection**: Identifies pumps with >10% amperage or >3% efficiency differences
- **Tolerance checking**: Quality control metrics for tandem pairs
- **Professional output**: Clean reports suitable for customer delivery

## Company: VBC Hydraulics
Contact: [Your contact information]
