# Perimetro Clientes Merge Solution

This directory contains the solution for merging `perimetro_clientes` and `query_results` dataframes to create `perimetro_completo` with the columns `aliasJ`, `SGC`, and `Status_GBO`.

## Files

- **`perimetro_merge_analysis.ipynb`** - Jupyter notebook with complete analysis and merge functionality
- **`perimetro_merge_script.py`** - Standalone Python script version
- **`PERIMETRO_MERGE_README.md`** - This documentation file

## Solution Overview

The solution implements a pandas merge operation that performs a VLOOKUP-like join between two dataframes:

1. **Source DataFrames:**
   - `resultados_filtrados` (filtered query results) - contains `entityGLCS` column for matching
   - `perimetro_clientes` (client perimeter data) - contains `GLCS` column for matching and the required output columns

2. **Merge Logic:**
   - Match `query_results['entityGLCS']` with `perimetro_clientes['GLCS']`
   - Extract only the required columns: `aliasJ`, `SGC`, and `Status_GBO`
   - Use left join to preserve all records from `resultados_filtrados`

3. **Output:**
   - `perimetro_completo` - merged dataframe with original data plus client information

## Key Features

- ✅ **VLOOKUP-like pandas merge** using `left_on` and `right_on` parameters
- ✅ **Column selection** - extracts only required columns from perimetro_clientes
- ✅ **Left join** - preserves all records from resultados_filtrados
- ✅ **Error handling** - validates input columns and reports match statistics
- ✅ **Sample data** - includes demonstration data for testing
- ✅ **Reusable function** - parameterized function for different datasets

## Usage

### Option 1: Jupyter Notebook
```bash
jupyter notebook perimetro_merge_analysis.ipynb
```

### Option 2: Python Script
```bash
python perimetro_merge_script.py
```

### Option 3: Import as Module
```python
from perimetro_merge_script import merge_perimetro_data

# Load your data
# perimetro_clientes = pd.read_csv('your_perimetro_file.csv')
# resultados_filtrados = pd.read_csv('your_results_file.csv')

# Perform merge
perimetro_completo = merge_perimetro_data(
    resultados_filtrados, 
    perimetro_clientes
)
```

## Function Signature

```python
def merge_perimetro_data(
    query_results_df,           # The filtered query results dataframe
    perimetro_clientes_df,      # The client perimeter dataframe  
    query_glcs_col='entityGLCS', # Column name for GLCS in query_results
    perimetro_glcs_col='GLCS',  # Column name for GLCS in perimetro_clientes
    required_cols=['aliasJ', 'SGC', 'Status_GBO']  # Required output columns
)
```

## Sample Output

```
Merge completed: 3/5 records matched
Warning: 2 records could not be matched

  entityGLCS transaction_id     aliasJ        SGC Status_GBO
0    GLCS001         TXN001  Cliente_A  SGC_Alpha     Active
1    GLCS002         TXN002  Cliente_B   SGC_Beta   Inactive
2    GLCS003         TXN003  Cliente_C  SGC_Gamma    Pending
3    GLCS007         TXN004        NaN        NaN        NaN
4    GLCS008         TXN005        NaN        NaN        NaN
```

## Requirements

- Python 3.7+
- pandas
- numpy (optional, for enhanced functionality)

Install with:
```bash
pip install pandas numpy
```

## Integration with Existing Code

To integrate this solution into your existing notebook:

1. **Copy the merge function:**
   ```python
   def merge_perimetro_data(query_results_df, perimetro_clientes_df, ...):
       # Function code here
   ```

2. **Use with your existing variables:**
   ```python
   # Assuming you already have these variables in your notebook:
   # - perimetro_clientes
   # - resultados_filtrados (your filtered query_results)
   
   perimetro_completo = merge_perimetro_data(
       resultados_filtrados, 
       perimetro_clientes
   )
   ```

3. **Add as a new cell** in your existing notebook

## Error Handling

The solution includes comprehensive error handling:

- Validates that required columns exist in both dataframes
- Reports merge statistics (matched vs unmatched records)
- Handles missing matches gracefully with NaN values
- Provides clear error messages for common issues

## Customization

The solution is highly customizable:

- **Different column names:** Use `query_glcs_col` and `perimetro_glcs_col` parameters
- **Different output columns:** Modify the `required_cols` parameter
- **Different join types:** Change `how='left'` to 'inner', 'outer', or 'right'
- **Additional processing:** Extend the function for your specific needs

## Performance Notes

- Uses pandas' optimized merge operation
- Memory efficient with column selection before merge
- Scales well with large datasets
- Left join preserves original dataset size

---

*This solution implements the exact requirements specified: pandas merge operation, VLOOKUP-like join, column selection, and integration with existing filtered data.*