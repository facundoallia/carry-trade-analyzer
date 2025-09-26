#!/usr/bin/env python3
"""
Perimetro Clientes Merge Script

This script merges perimetro_clientes and query_results dataframes to create 
perimetro_completo with the columns aliasJ, SGC, and Status_GBO by matching 
query_results['entityGLCS'] with perimetro_clientes['GLCS'].

Usage:
    python perimetro_merge_script.py

Requirements:
    - pandas
    - numpy
"""

import pandas as pd
import numpy as np
from datetime import date, datetime


def merge_perimetro_data(query_results_df, perimetro_clientes_df, 
                        query_glcs_col='entityGLCS', perimetro_glcs_col='GLCS',
                        required_cols=['aliasJ', 'SGC', 'Status_GBO']):
    """
    Merge query results with perimetro clientes data.
    
    Parameters:
    -----------
    query_results_df : pd.DataFrame
        The filtered query results dataframe (resultados_filtrados)
    perimetro_clientes_df : pd.DataFrame
        The client perimeter dataframe
    query_glcs_col : str
        Column name in query_results_df for GLCS matching (default: 'entityGLCS')
    perimetro_glcs_col : str
        Column name in perimetro_clientes_df for GLCS matching (default: 'GLCS')
    required_cols : list
        List of columns to extract from perimetro_clientes_df
    
    Returns:
    --------
    pd.DataFrame
        Merged dataframe with all original columns from query_results_df 
        plus required columns from perimetro_clientes_df
    """
    
    # Validate inputs
    if query_glcs_col not in query_results_df.columns:
        raise ValueError(f"Column '{query_glcs_col}' not found in query_results_df")
    
    if perimetro_glcs_col not in perimetro_clientes_df.columns:
        raise ValueError(f"Column '{perimetro_glcs_col}' not found in perimetro_clientes_df")
    
    missing_cols = [col for col in required_cols if col not in perimetro_clientes_df.columns]
    if missing_cols:
        raise ValueError(f"Required columns {missing_cols} not found in perimetro_clientes_df")
    
    # Prepare columns to merge
    merge_cols = [perimetro_glcs_col] + required_cols
    
    # Perform the merge (VLOOKUP-like operation)
    merged_df = query_results_df.merge(
        perimetro_clientes_df[merge_cols],
        left_on=query_glcs_col,
        right_on=perimetro_glcs_col,
        how='left'  # Left join to keep all records from query_results_df
    )
    
    # Print merge statistics
    total_records = len(merged_df)
    successful_matches = merged_df[required_cols[0]].notna().sum()
    unmatched_records = total_records - successful_matches
    
    print(f"Merge completed: {successful_matches}/{total_records} records matched")
    if unmatched_records > 0:
        print(f"Warning: {unmatched_records} records could not be matched")
    
    return merged_df


def create_sample_data():
    """Create sample data for demonstration purposes."""
    
    # Sample perimetro_clientes dataframe
    perimetro_clientes = pd.DataFrame({
        'GLCS': ['GLCS001', 'GLCS002', 'GLCS003', 'GLCS004', 'GLCS005', 'GLCS006'],
        'aliasJ': ['Cliente_A', 'Cliente_B', 'Cliente_C', 'Cliente_D', 'Cliente_E', 'Cliente_F'],
        'SGC': ['SGC_Alpha', 'SGC_Beta', 'SGC_Gamma', 'SGC_Delta', 'SGC_Epsilon', 'SGC_Zeta'],
        'Status_GBO': ['Active', 'Inactive', 'Pending', 'Active', 'Suspended', 'Active'],
        'additional_field1': ['Info1', 'Info2', 'Info3', 'Info4', 'Info5', 'Info6'],
        'additional_field2': [100, 200, 300, 400, 500, 600]
    })
    
    # Sample resultados_filtrados dataframe (representing query_results)
    resultados_filtrados = pd.DataFrame({
        'entityGLCS': ['GLCS001', 'GLCS002', 'GLCS003', 'GLCS007', 'GLCS008'],  # Some don't match
        'transaction_id': ['TXN001', 'TXN002', 'TXN003', 'TXN004', 'TXN005'],
        'amount': [1000.50, 2500.75, 1750.25, 3200.00, 950.80],
        'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'status': ['Completed', 'Pending', 'Completed', 'Failed', 'Completed']
    })
    
    return perimetro_clientes, resultados_filtrados


def main():
    """Main function to demonstrate the merge functionality."""
    
    print("=" * 60)
    print("PERIMETRO CLIENTES MERGE SCRIPT")
    print("=" * 60)
    
    # Create sample data (replace this with your actual data loading)
    print("\n1. Loading sample data...")
    perimetro_clientes, resultados_filtrados = create_sample_data()
    
    print(f"   - perimetro_clientes: {perimetro_clientes.shape[0]} records, {perimetro_clientes.shape[1]} columns")
    print(f"   - resultados_filtrados: {resultados_filtrados.shape[0]} records, {resultados_filtrados.shape[1]} columns")
    
    # Perform the merge
    print("\n2. Performing merge operation...")
    perimetro_completo = merge_perimetro_data(resultados_filtrados, perimetro_clientes)
    
    # Display results
    print("\n3. Merge Results:")
    print(f"   - Final dataset: {perimetro_completo.shape[0]} records, {perimetro_completo.shape[1]} columns")
    print(f"   - Columns: {list(perimetro_completo.columns)}")
    
    # Show sample output
    print("\n4. Sample output (first 5 rows):")
    print(perimetro_completo[['entityGLCS', 'transaction_id', 'aliasJ', 'SGC', 'Status_GBO']].head())
    
    # Analysis
    print("\n5. Analysis:")
    matched_records = perimetro_completo['aliasJ'].notna()
    print(f"   - Records with complete client data: {matched_records.sum()}")
    print(f"   - Records missing client data: {(~matched_records).sum()}")
    
    if (~matched_records).any():
        print("\n   Unmatched entityGLCS values:")
        unmatched = perimetro_completo[~matched_records]['entityGLCS'].tolist()
        print(f"   {unmatched}")
    
    # Optional: Save to file
    # print("\n6. Saving results...")
    # perimetro_completo.to_csv('perimetro_completo.csv', index=False)
    # print("   Results saved to 'perimetro_completo.csv'")
    
    print("\n" + "=" * 60)
    print("MERGE OPERATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    return perimetro_completo


# Instructions for using with real data
def load_real_data():
    """
    Replace this function with your actual data loading logic.
    
    Example:
    --------
    # Load from CSV files
    perimetro_clientes = pd.read_csv('perimetro_clientes.csv')
    resultados_filtrados = pd.read_csv('resultados_filtrados.csv')
    
    # Or load from database
    # import sqlalchemy
    # engine = sqlalchemy.create_engine('your_connection_string')
    # perimetro_clientes = pd.read_sql('SELECT * FROM perimetro_clientes', engine)
    # resultados_filtrados = pd.read_sql('SELECT * FROM query_results WHERE ...', engine)
    
    return perimetro_clientes, resultados_filtrados
    """
    raise NotImplementedError("Replace this function with your actual data loading logic")


if __name__ == "__main__":
    # Run the main function
    perimetro_completo = main()
    
    # If you want to use real data instead of sample data, uncomment and modify:
    # perimetro_clientes, resultados_filtrados = load_real_data()
    # perimetro_completo = merge_perimetro_data(resultados_filtrados, perimetro_clientes)