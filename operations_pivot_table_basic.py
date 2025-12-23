#!/usr/bin/env python3
"""
Operations Pivot Table Generator (Simplified Version)

This script generates a pivot table summarizing the number of operations per counterparty,
sorted in descending order. This version works with or without pandas for maximum compatibility.

Requirements:
- Input data should contain a 'counterparty' column  
- Can handle large datasets efficiently
- Outputs a clean result with 'counterparty' and 'operations' columns
"""

import csv
import json
import sys
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union


def create_operations_pivot_table_basic(data: List[Dict], counterparty_column: str = 'counterparty') -> List[Tuple[str, int]]:
    """
    Create a pivot table summarizing operations per counterparty using basic Python.
    
    Args:
        data (List[Dict]): Input data as list of dictionaries
        counterparty_column (str): Name of the counterparty column
    
    Returns:
        List[Tuple[str, int]]: List of (counterparty, operations_count) tuples, 
                              sorted by operations count in descending order
    """
    if not data:
        return []
    
    # Check if counterparty column exists
    if counterparty_column not in data[0]:
        available_columns = list(data[0].keys()) if data else []
        raise ValueError(f"Column '{counterparty_column}' not found. "
                        f"Available columns: {available_columns}")
    
    # Count operations per counterparty
    counterparty_counts = Counter()
    
    for row in data:
        counterparty = row.get(counterparty_column)
        if counterparty is not None and counterparty != '':
            # Handle various string representations of null
            if str(counterparty).strip().lower() not in ['nan', 'null', 'none', '']:
                counterparty_counts[str(counterparty).strip()] += 1
    
    # Sort by count in descending order
    sorted_results = counterparty_counts.most_common()
    
    return sorted_results


def load_csv_data(file_path: str) -> List[Dict]:
    """Load data from CSV file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def load_json_data(file_path: str) -> List[Dict]:
    """Load data from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # If it's a dict, try to find a list of records
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        raise ValueError("JSON structure not supported. Expected list of objects or dict with list of objects.")
    else:
        raise ValueError("JSON structure not supported. Expected list of objects.")


def generate_sample_data_basic(num_rows: int = 655586) -> List[Dict]:
    """
    Generate sample operations data using basic Python (no numpy).
    
    Args:
        num_rows (int): Number of rows to generate
    
    Returns:
        List[Dict]: Sample data as list of dictionaries
    """
    import random
    from datetime import datetime, timedelta
    
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
    
    # Create weighted distribution (some counterparties have more operations)
    weights = [random.expovariate(1) for _ in counterparties]
    total_weight = sum(weights)
    weights = [w/total_weight for w in weights]
    
    # Generate data
    data = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(num_rows):
        # Select counterparty based on weights
        counterparty = random.choices(counterparties, weights=weights)[0]
        
        # Generate random operation data
        operation = {
            'counterparty': counterparty,
            'operation_id': f'OP{i+1:07d}',
            'amount': round(random.uniform(1000, 1000000), 2),
            'currency': random.choice(['USD', 'EUR', 'ARS']),
            'operation_type': random.choice(['BUY', 'SELL', 'TRANSFER']),
            'timestamp': (start_date + timedelta(minutes=i)).isoformat()
        }
        
        data.append(operation)
        
        # Progress indicator for large datasets
        if i > 0 and i % 50000 == 0:
            print(f"Generated {i:,} rows...")
    
    return data


def save_results_csv(results: List[Tuple[str, int]], output_path: str):
    """Save results to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['counterparty', 'operations'])
        writer.writerows(results)


def save_results_json(results: List[Tuple[str, int]], output_path: str):
    """Save results to JSON file."""
    json_data = [{'counterparty': cp, 'operations': ops} for cp, ops in results]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)


def print_results_table(results: List[Tuple[str, int]], top_n: Optional[int] = None):
    """Print results in a formatted table."""
    if not results:
        print("No results to display.")
        return
    
    # Apply top N filter
    display_results = results[:top_n] if top_n else results
    
    print("Operations Pivot Table (sorted by operations count - descending):")
    print("=" * 70)
    print(f"{'Counterparty':<40} {'Operations':>10}")
    print("-" * 70)
    
    for counterparty, operations in display_results:
        print(f"{counterparty:<40} {operations:>10,}")
    
    # Summary statistics
    total_operations = sum(ops for _, ops in results)
    unique_counterparties = len(results)
    avg_operations = total_operations / unique_counterparties if unique_counterparties > 0 else 0
    
    print("-" * 70)
    print(f"Total operations: {total_operations:,}")
    print(f"Unique counterparties: {unique_counterparties:,}")
    print(f"Average operations per counterparty: {avg_operations:.1f}")
    
    if top_n and len(results) > top_n:
        print(f"(Showing top {top_n} of {len(results)} counterparties)")


def main():
    """Main function with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate operations pivot table by counterparty')
    parser.add_argument('--file', '-f', type=str, help='Path to data file (CSV or JSON)')
    parser.add_argument('--column', '-c', type=str, default='counterparty', 
                       help='Name of the counterparty column (default: counterparty)')
    parser.add_argument('--sample', '-s', action='store_true', 
                       help='Generate and use sample data for testing')
    parser.add_argument('--rows', '-r', type=int, default=655586, 
                       help='Number of sample rows to generate (default: 655586)')
    parser.add_argument('--output', '-o', type=str, help='Output file path (CSV or JSON)')
    parser.add_argument('--top', '-t', type=int, help='Show only top N counterparties')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Output format (default: csv)')
    
    args = parser.parse_args()
    
    try:
        # Load or generate data
        if args.sample:
            print(f"Generating sample data with {args.rows:,} rows...")
            data = generate_sample_data_basic(args.rows)
            print(f"Sample data generated successfully: {len(data):,} rows")
        elif args.file:
            print(f"Loading data from {args.file}...")
            file_path = Path(args.file)
            
            if not file_path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)
            
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.csv':
                data = load_csv_data(args.file)
            elif file_extension == '.json':
                data = load_json_data(args.file)
            else:
                print(f"Error: Unsupported file format: {file_extension}")
                print("Supported formats: .csv, .json")
                sys.exit(1)
            
            print(f"Data loaded successfully: {len(data):,} rows")
        else:
            print("Error: Please specify either --file or --sample")
            sys.exit(1)
        
        # Create pivot table
        print("Creating pivot table...")
        results = create_operations_pivot_table_basic(data, args.column)
        
        # Display results
        print_results_table(results, args.top)
        
        # Save output if specified
        if args.output:
            output_path = Path(args.output)
            
            if args.format == 'json' or output_path.suffix.lower() == '.json':
                save_results_json(results, args.output)
            else:
                save_results_csv(results, args.output)
            
            print(f"\nResults saved to: {args.output}")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# Test function for validation
def test_basic_functionality():
    """Test the basic functionality with sample data."""
    print("Running basic functionality test...")
    
    # Create small test dataset
    test_data = [
        {'counterparty': 'Bank A', 'amount': 1000},
        {'counterparty': 'Bank B', 'amount': 2000},
        {'counterparty': 'Bank A', 'amount': 1500},
        {'counterparty': 'Bank C', 'amount': 3000},
        {'counterparty': 'Bank A', 'amount': 2500},
        {'counterparty': 'Bank B', 'amount': 1800},
    ]
    
    results = create_operations_pivot_table_basic(test_data)
    
    expected = [('Bank A', 3), ('Bank B', 2), ('Bank C', 1)]
    
    if results == expected:
        print("✓ Basic functionality test passed")
        return True
    else:
        print(f"✗ Basic functionality test failed")
        print(f"Expected: {expected}")
        print(f"Got: {results}")
        return False


if __name__ == "__main__":
    # Run basic test first
    if len(sys.argv) == 1:
        # No arguments, run test
        test_basic_functionality()
        print("\nTo use the script:")
        print("python operations_pivot_table_basic.py --sample --rows 1000")
        print("python operations_pivot_table_basic.py --file data.csv")
    else:
        main()