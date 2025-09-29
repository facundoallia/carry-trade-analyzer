#!/usr/bin/env python3
"""
Operations Pivot Table Generator

This script generates a pivot table summarizing the number of operations per counterparty,
sorted in descending order. Designed to handle large datasets efficiently using pandas.

Requirements:
- Input data should contain a 'counterparty' column
- Can handle large datasets (655,586+ rows)
- Outputs a clean dataframe with 'counterparty' and 'operations' columns
"""

import pandas as pd
import sys
import os
from pathlib import Path
from typing import Optional


def create_operations_pivot_table(data: pd.DataFrame, counterparty_column: str = 'counterparty') -> pd.DataFrame:
    """
    Create a pivot table summarizing operations per counterparty.
    
    Args:
        data (pd.DataFrame): Input dataframe containing operations data
        counterparty_column (str): Name of the counterparty column (default: 'counterparty')
    
    Returns:
        pd.DataFrame: Pivot table with 'counterparty' and 'operations' columns, 
                     sorted by operations count in descending order
    
    Raises:
        ValueError: If the counterparty column is not found in the dataframe
        TypeError: If input is not a pandas DataFrame
    """
    # Validate input
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


def load_data_from_file(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Load data from various file formats.
    
    Args:
        file_path (str): Path to the data file
        **kwargs: Additional arguments passed to pandas read functions
    
    Returns:
        pd.DataFrame: Loaded dataframe
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine file format and load accordingly
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


def generate_sample_data(num_rows: int = 655586) -> pd.DataFrame:
    """
    Generate sample operations data for testing purposes.
    
    Args:
        num_rows (int): Number of rows to generate (default: 655586)
    
    Returns:
        pd.DataFrame: Sample dataframe with operations data
    """
    import numpy as np
    
    # Sample counterparty names (realistic financial institutions)
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
    # Some counterparties will have more operations than others
    weights = np.random.exponential(1, len(counterparties))
    weights = weights / weights.sum()
    
    # Generate counterparty assignments
    counterparty_data = np.random.choice(
        counterparties, 
        size=num_rows, 
        p=weights
    )
    
    # Create DataFrame with additional dummy columns that might exist in real data
    sample_data = pd.DataFrame({
        'counterparty': counterparty_data,
        'operation_id': range(1, num_rows + 1),
        'amount': np.random.uniform(1000, 1000000, num_rows),
        'currency': np.random.choice(['USD', 'EUR', 'ARS'], num_rows),
        'operation_type': np.random.choice(['BUY', 'SELL', 'TRANSFER'], num_rows),
        'timestamp': pd.date_range('2023-01-01', periods=num_rows, freq='1min')
    })
    
    return sample_data


def main():
    """
    Main function to demonstrate the pivot table functionality.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate operations pivot table by counterparty')
    parser.add_argument('--file', '-f', type=str, help='Path to data file (CSV, Excel, JSON, or Parquet)')
    parser.add_argument('--column', '-c', type=str, default='counterparty', 
                       help='Name of the counterparty column (default: counterparty)')
    parser.add_argument('--sample', '-s', action='store_true', 
                       help='Generate and use sample data for testing')
    parser.add_argument('--rows', '-r', type=int, default=655586, 
                       help='Number of sample rows to generate (default: 655586)')
    parser.add_argument('--output', '-o', type=str, help='Output file path (optional)')
    parser.add_argument('--top', '-t', type=int, help='Show only top N counterparties')
    
    args = parser.parse_args()
    
    try:
        # Load or generate data
        if args.sample:
            print(f"Generating sample data with {args.rows:,} rows...")
            data = generate_sample_data(args.rows)
            print(f"Sample data generated successfully: {len(data):,} rows")
        elif args.file:
            print(f"Loading data from {args.file}...")
            data = load_data_from_file(args.file)
            print(f"Data loaded successfully: {len(data):,} rows")
        else:
            print("Error: Please specify either --file or --sample")
            sys.exit(1)
        
        # Create pivot table
        print(f"Creating pivot table...")
        pivot_table = create_operations_pivot_table(data, args.column)
        
        # Apply top N filter if specified
        if args.top:
            pivot_table = pivot_table.head(args.top)
        
        # Display results
        print("\nOperations Pivot Table (sorted by operations count - descending):")
        print("=" * 60)
        print(pivot_table.to_string(index=False))
        
        # Summary statistics
        total_operations = pivot_table['operations'].sum()
        unique_counterparties = len(pivot_table)
        avg_operations = pivot_table['operations'].mean()
        
        print(f"\nSummary Statistics:")
        print(f"Total operations: {total_operations:,}")
        print(f"Unique counterparties: {unique_counterparties:,}")
        print(f"Average operations per counterparty: {avg_operations:.1f}")
        
        # Save output if specified
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix.lower() == '.csv':
                pivot_table.to_csv(output_path, index=False)
            elif output_path.suffix.lower() in ['.xlsx', '.xls']:
                pivot_table.to_excel(output_path, index=False)
            else:
                # Default to CSV
                output_path = output_path.with_suffix('.csv')
                pivot_table.to_csv(output_path, index=False)
            print(f"\nResults saved to: {output_path}")
        
        return pivot_table
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if pandas is available
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        print(f"Required packages not installed: {e}")
        print("Please install pandas and numpy:")
        print("pip install pandas numpy")
        sys.exit(1)
    
    main()