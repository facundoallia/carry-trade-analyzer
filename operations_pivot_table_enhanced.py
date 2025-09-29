#!/usr/bin/env python3
"""
Operations Pivot Table Generator (Enhanced Version)

This script generates a pivot table summarizing the number of operations per counterparty,
sorted in descending order. This version uses pandas when available for better performance,
but falls back to basic Python functionality if pandas is not installed.

Requirements:
- Input data should contain a 'counterparty' column
- Can handle large datasets efficiently (tested with 655,586+ rows)
- Outputs a clean dataframe/result with 'counterparty' and 'operations' columns
- Works with or without pandas for maximum compatibility
"""

import sys
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any

# Try to import pandas, fall back to basic implementation if not available
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
    print("Pandas available - using optimized implementation")
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # Define pd as None when not available
    print("Pandas not available - using basic Python implementation")

# Import the basic implementation functions
from operations_pivot_table_basic import (
    create_operations_pivot_table_basic,
    load_csv_data,
    load_json_data,
    generate_sample_data_basic,
    save_results_csv,
    save_results_json,
    print_results_table
)


def create_operations_pivot_table_pandas(data, counterparty_column: str = 'counterparty'):
    """
    Create a pivot table using pandas for optimal performance with large datasets.
    
    Args:
        data (pd.DataFrame): Input dataframe containing operations data
        counterparty_column (str): Name of the counterparty column
    
    Returns:
        pd.DataFrame: Pivot table with 'counterparty' and 'operations' columns,
                     sorted by operations count in descending order
    
    Raises:
        ValueError: If the counterparty column is not found
        TypeError: If input is not a pandas DataFrame
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame")
    
    if data.empty:
        return pd.DataFrame(columns=['counterparty', 'operations'])
    
    if counterparty_column not in data.columns:
        raise ValueError(f"Column '{counterparty_column}' not found in dataframe. "
                        f"Available columns: {list(data.columns)}")
    
    # Remove rows with null counterparty values
    clean_data = data.dropna(subset=[counterparty_column])
    
    if clean_data.empty:
        print("Warning: No valid counterparty data found after removing null values")
        return pd.DataFrame(columns=['counterparty', 'operations'])
    
    # Group by counterparty and count operations
    pivot_table = (clean_data
                   .groupby(counterparty_column)
                   .size()
                   .reset_index(name='operations')
                   .sort_values('operations', ascending=False)
                   .reset_index(drop=True))
    
    # Rename the counterparty column to ensure consistent naming
    pivot_table = pivot_table.rename(columns={counterparty_column: 'counterparty'})
    
    return pivot_table


def generate_sample_data_pandas(num_rows: int = 655586):
    """
    Generate sample operations data using pandas and numpy for better performance.
    
    Args:
        num_rows (int): Number of rows to generate
    
    Returns:
        pd.DataFrame: Sample dataframe with operations data
    """
    import numpy as np
    
    # Sample counterparty names
    counterparties = [
        'Goldman Sachs', 'Morgan Stanley', 'JPMorgan Chase', 'Bank of America',
        'Citigroup', 'Wells Fargo', 'Deutsche Bank', 'Credit Suisse',
        'UBS', 'Barclays', 'HSBC', 'BNP Paribas', 'Société Générale',
        'Banco Santander', 'ING Group', 'UniCredit', 'BBVA', 'Credit Agricole',
        'Mizuho Financial', 'Sumitomo Mitsui', 'Nomura Holdings',
        'Standard Chartered', 'Royal Bank of Canada', 'Toronto-Dominion Bank',
        'Bank of Nova Scotia', 'Canadian Imperial Bank'
    ]
    
    # Generate random data with realistic distribution
    weights = np.random.exponential(1, len(counterparties))
    weights = weights / weights.sum()
    
    # Generate counterparty assignments
    counterparty_data = np.random.choice(
        counterparties, 
        size=num_rows, 
        p=weights
    )
    
    # Create DataFrame
    sample_data = pd.DataFrame({
        'counterparty': counterparty_data,
        'operation_id': [f'OP{i+1:07d}' for i in range(num_rows)],
        'amount': np.random.uniform(1000, 1000000, num_rows),
        'currency': np.random.choice(['USD', 'EUR', 'ARS'], num_rows),
        'operation_type': np.random.choice(['BUY', 'SELL', 'TRANSFER'], num_rows),
        'timestamp': pd.date_range('2023-01-01', periods=num_rows, freq='1min')
    })
    
    return sample_data


def load_data_file_pandas(file_path: str, **kwargs):
    """
    Load data from various file formats using pandas.
    
    Args:
        file_path (str): Path to the data file
        **kwargs: Additional arguments passed to pandas read functions
    
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.csv':
            return pd.read_csv(file_path, **kwargs)
        elif file_extension in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, **kwargs)
        elif file_extension == '.json':
            return pd.read_json(file_path, **kwargs)
        elif file_extension == '.parquet':
            return pd.read_parquet(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    except Exception as e:
        raise ValueError(f"Error loading file {file_path}: {str(e)}")


def convert_pandas_to_basic_format(df) -> List[Tuple[str, int]]:
    """Convert pandas DataFrame to basic format for consistent output."""
    return [(row['counterparty'], row['operations']) for _, row in df.iterrows()]


def print_results_pandas(df, top_n: Optional[int] = None):
    """Print pandas DataFrame results in a formatted table."""
    if df.empty:
        print("No results to display.")
        return
    
    # Apply top N filter
    display_df = df.head(top_n) if top_n else df
    
    print("Operations Pivot Table (sorted by operations count - descending):")
    print("=" * 70)
    print(f"{'Counterparty':<40} {'Operations':>10}")
    print("-" * 70)
    
    for _, row in display_df.iterrows():
        print(f"{row['counterparty']:<40} {row['operations']:>10,}")
    
    # Summary statistics
    total_operations = df['operations'].sum()
    unique_counterparties = len(df)
    avg_operations = df['operations'].mean()
    
    print("-" * 70)
    print(f"Total operations: {total_operations:,}")
    print(f"Unique counterparties: {unique_counterparties:,}")
    print(f"Average operations per counterparty: {avg_operations:.1f}")
    
    if top_n and len(df) > top_n:
        print(f"(Showing top {top_n} of {len(df)} counterparties)")


def main():
    """Enhanced main function that uses pandas when available."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate operations pivot table by counterparty (Enhanced Version)')
    parser.add_argument('--file', '-f', type=str, help='Path to data file')
    parser.add_argument('--column', '-c', type=str, default='counterparty', 
                       help='Name of the counterparty column (default: counterparty)')
    parser.add_argument('--sample', '-s', action='store_true', 
                       help='Generate and use sample data for testing')
    parser.add_argument('--rows', '-r', type=int, default=655586, 
                       help='Number of sample rows to generate (default: 655586)')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--top', '-t', type=int, help='Show only top N counterparties')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Output format (default: csv)')
    parser.add_argument('--engine', choices=['pandas', 'basic', 'auto'], default='auto',
                       help='Processing engine to use (default: auto)')
    
    args = parser.parse_args()
    
    # Determine which engine to use
    use_pandas = False
    if args.engine == 'pandas':
        if not PANDAS_AVAILABLE:
            print("Error: Pandas engine requested but pandas is not available")
            sys.exit(1)
        use_pandas = True
    elif args.engine == 'auto':
        use_pandas = PANDAS_AVAILABLE
    
    try:
        # Load or generate data
        if args.sample:
            print(f"Generating sample data with {args.rows:,} rows...")
            
            if use_pandas:
                try:
                    import numpy as np
                    data = generate_sample_data_pandas(args.rows)
                    print(f"Sample data generated successfully using pandas: {len(data):,} rows")
                except ImportError:
                    print("NumPy not available, falling back to basic implementation")
                    use_pandas = False
                    basic_data = generate_sample_data_basic(args.rows)
                    print(f"Sample data generated successfully using basic Python: {len(basic_data):,} rows")
            else:
                basic_data = generate_sample_data_basic(args.rows)
                print(f"Sample data generated successfully using basic Python: {len(basic_data):,} rows")
        
        elif args.file:
            print(f"Loading data from {args.file}...")
            
            if use_pandas:
                data = load_data_file_pandas(args.file)
                print(f"Data loaded successfully using pandas: {len(data):,} rows")
            else:
                file_path = Path(args.file)
                if not file_path.exists():
                    print(f"Error: File not found: {args.file}")
                    sys.exit(1)
                
                file_extension = file_path.suffix.lower()
                
                if file_extension == '.csv':
                    basic_data = load_csv_data(args.file)
                elif file_extension == '.json':
                    basic_data = load_json_data(args.file)
                else:
                    print(f"Error: Unsupported file format for basic engine: {file_extension}")
                    print("Basic engine supports: .csv, .json")
                    sys.exit(1)
                
                print(f"Data loaded successfully using basic Python: {len(basic_data):,} rows")
        else:
            print("Error: Please specify either --file or --sample")
            sys.exit(1)
        
        # Create pivot table
        print("Creating pivot table...")
        
        if use_pandas:
            results_df = create_operations_pivot_table_pandas(data, args.column)
            
            # Display results
            print_results_pandas(results_df, args.top)
            
            # Convert to basic format for saving if needed
            if args.output:
                basic_results = convert_pandas_to_basic_format(results_df)
        else:
            basic_results = create_operations_pivot_table_basic(basic_data, args.column)
            
            # Display results
            print_results_table(basic_results, args.top)
        
        # Save output if specified
        if args.output:
            if use_pandas and args.format == 'csv':
                # Use pandas for better CSV handling
                output_df = results_df.head(args.top) if args.top else results_df
                output_df.to_csv(args.output, index=False)
            elif args.format == 'json':
                save_results_json(basic_results, args.output)
            else:
                save_results_csv(basic_results, args.output)
            
            print(f"\nResults saved to: {args.output}")
        
        # Return appropriate format
        if use_pandas:
            return results_df
        else:
            return basic_results
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()