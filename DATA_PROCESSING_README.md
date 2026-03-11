# Data Processing Module

This module provides data processing utilities for joining dataframes, specifically implementing the left join functionality between `perimetro_clientes` and `query_results` dataframes.

## Overview

The `DataProcessor` class implements the requirement to perform a left join between two dataframes while:
- Keeping all records from the left dataframe (`perimetro_clientes`)
- Adding specific columns from the right dataframe (`query_results`)
- Filling non-matching entries with NaN
- Optionally removing redundant columns

## Key Features

- **Left Join Operation**: Preserves all rows from `perimetro_clientes`
- **Selective Column Addition**: Only adds `aliasJ`, `SGC`, and `Status_GBO` columns
- **GLCS-based Matching**: Joins on `GLCS` field from left and `entityGLCS` from right
- **NaN Filling**: Automatically fills non-matching entries with NaN values
- **Validation**: Includes comprehensive validation of join results
- **Error Handling**: Robust error handling for missing columns or invalid data

## Usage

### Method 1: Using DataProcessor Class (Recommended)

```python
from backend.data_processor import DataProcessor

# Initialize the processor
processor = DataProcessor()

# Perform the left join
result = processor.perform_left_join(perimetro_clientes, query_results)

# Validate the result
validation = processor.validate_join_result(
    perimetro_clientes, 
    result, 
    ['aliasJ', 'SGC', 'Status_GBO']
)
```

### Method 2: Direct Pandas Merge

```python
import pandas as pd

# Realizar el left join manteniendo todas las columnas de perimetro_clientes
perimetro_completo = perimetro_clientes.merge(
    query_results[['entityGLCS', 'aliasJ', 'SGC', 'Status_GBO']], 
    left_on='GLCS',
    right_on='entityGLCS',
    how='left'
)

# Opcional: eliminar la columna entityGLCS si no se necesita (ya que es redundante con GLCS)
perimetro_completo = perimetro_completo.drop('entityGLCS', axis=1, errors='ignore')
```

## Requirements

### Input DataFrames

#### perimetro_clientes
Must contain:
- `GLCS` column for joining
- Any additional columns (all will be preserved)

#### query_results
Must contain:
- `entityGLCS` column for joining (matches with `GLCS`)
- `aliasJ` column
- `SGC` column  
- `Status_GBO` column

## API Reference

### DataProcessor Class

#### `perform_left_join(perimetro_clientes, query_results, remove_redundant_column=True)`

Performs a left join between the two dataframes.

**Parameters:**
- `perimetro_clientes` (pd.DataFrame): Left dataframe with client perimeter data
- `query_results` (pd.DataFrame): Right dataframe with query results
- `remove_redundant_column` (bool): Whether to remove the redundant `entityGLCS` column (default: True)

**Returns:**
- `pd.DataFrame`: Result of the left join

**Raises:**
- `ValueError`: If required columns are missing or dataframes are empty

#### `validate_join_result(original_df, joined_df, expected_new_columns)`

Validates the result of a join operation.

**Parameters:**
- `original_df` (pd.DataFrame): The original left dataframe
- `joined_df` (pd.DataFrame): The result dataframe after join
- `expected_new_columns` (list): List of columns that should have been added

**Returns:**
- `dict`: Validation results with statistics

## Examples

### Basic Usage

```python
from backend.data_processor import DataProcessor, create_sample_dataframes

# Create sample data
perimetro_clientes, query_results = create_sample_dataframes()

# Perform join
processor = DataProcessor()
result = processor.perform_left_join(perimetro_clientes, query_results)

print(f"Original shape: {perimetro_clientes.shape}")
print(f"Result shape: {result.shape}")
print(f"New columns: {set(result.columns) - set(perimetro_clientes.columns)}")
```

### With Validation

```python
# Perform join with validation
result = processor.perform_left_join(perimetro_clientes, query_results)

# Validate the result
validation = processor.validate_join_result(
    perimetro_clientes, 
    result, 
    ['aliasJ', 'SGC', 'Status_GBO']
)

if validation['join_success']:
    print("Join completed successfully!")
    print(f"Rows preserved: {validation['rows_preserved']}")
    print(f"Null counts: {validation['null_counts']}")
else:
    print("Join validation failed!")
```

## Testing

Run the comprehensive test suite:

```bash
python3 test_data_processor.py
```

Run the example usage:

```bash
python3 example_usage.py
```

## Files

- `backend/data_processor.py`: Main implementation
- `test_data_processor.py`: Comprehensive test suite
- `example_usage.py`: Usage examples and demonstrations
- `DATA_PROCESSING_README.md`: This documentation

## Integration

This module is designed to integrate seamlessly with the existing carry trade analyzer infrastructure. The `DataProcessor` class can be imported and used alongside existing data processing workflows.

For questions or issues, refer to the test files for comprehensive usage examples.