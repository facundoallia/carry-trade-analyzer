#!/usr/bin/env python3
"""
Test script for the data processor functionality.

This script tests the left join functionality between perimetro_clientes
and query_results dataframes.
"""

import sys
import pandas as pd
from backend.data_processor import DataProcessor, create_sample_dataframes


def test_basic_join():
    """Test basic left join functionality."""
    print("=== Testing Basic Left Join ===")
    
    perimetro_clientes, query_results = create_sample_dataframes()
    processor = DataProcessor()
    
    result = processor.perform_left_join(perimetro_clientes, query_results)
    
    # Validate the result
    assert len(result) == len(perimetro_clientes), "Row count should be preserved"
    assert 'aliasJ' in result.columns, "aliasJ column should be added"
    assert 'SGC' in result.columns, "SGC column should be added"
    assert 'Status_GBO' in result.columns, "Status_GBO column should be added"
    assert 'entityGLCS' not in result.columns, "entityGLCS should be removed by default"
    
    # Check that all original columns are preserved
    for col in perimetro_clientes.columns:
        assert col in result.columns, f"Original column {col} should be preserved"
    
    # Check NaN values for non-matching records
    # GLCS003 and GLCS005 should have NaN values for the new columns
    glcs003_row = result[result['GLCS'] == 'GLCS003']
    glcs005_row = result[result['GLCS'] == 'GLCS005']
    
    assert pd.isna(glcs003_row['aliasJ'].iloc[0]), "GLCS003 should have NaN for aliasJ"
    assert pd.isna(glcs005_row['SGC'].iloc[0]), "GLCS005 should have NaN for SGC"
    
    print("✓ Basic left join test passed")
    return result


def test_keep_redundant_column():
    """Test keeping the redundant entityGLCS column."""
    print("\n=== Testing Keep Redundant Column ===")
    
    perimetro_clientes, query_results = create_sample_dataframes()
    processor = DataProcessor()
    
    result = processor.perform_left_join(
        perimetro_clientes, 
        query_results, 
        remove_redundant_column=False
    )
    
    assert 'entityGLCS' in result.columns, "entityGLCS should be kept when remove_redundant_column=False"
    
    print("✓ Keep redundant column test passed")


def test_validation():
    """Test the validation functionality."""
    print("\n=== Testing Validation Functionality ===")
    
    perimetro_clientes, query_results = create_sample_dataframes()
    processor = DataProcessor()
    
    result = processor.perform_left_join(perimetro_clientes, query_results)
    
    validation = processor.validate_join_result(
        perimetro_clientes,
        result,
        ['aliasJ', 'SGC', 'Status_GBO']
    )
    
    assert validation['rows_preserved'], "Rows should be preserved"
    assert validation['has_expected_columns'], "Should have expected columns"
    assert validation['join_success'], "Join should be successful"
    assert validation['original_row_count'] == 5, "Original should have 5 rows"
    assert validation['joined_row_count'] == 5, "Joined should have 5 rows"
    
    # Check null counts (GLCS003 and GLCS005 should have NaN values)
    expected_nulls = 2  # 2 rows without matches
    for col in ['aliasJ', 'SGC', 'Status_GBO']:
        assert validation['null_counts'][col] == expected_nulls, f"{col} should have {expected_nulls} null values"
    
    print("✓ Validation test passed")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Testing Error Handling ===")
    
    processor = DataProcessor()
    
    # Test empty dataframes
    try:
        empty_df = pd.DataFrame()
        sample_df = pd.DataFrame({'entityGLCS': [1], 'aliasJ': [1], 'SGC': [1], 'Status_GBO': [1]})
        processor.perform_left_join(empty_df, sample_df)
        assert False, "Should raise ValueError for empty perimetro_clientes"
    except ValueError as e:
        assert "empty" in str(e).lower()
    
    # Test missing required columns
    try:
        df1 = pd.DataFrame({'wrong_col': [1, 2]})
        df2 = pd.DataFrame({'entityGLCS': [1], 'aliasJ': [1], 'SGC': [1], 'Status_GBO': [1]})
        processor.perform_left_join(df1, df2)
        assert False, "Should raise ValueError for missing GLCS column"
    except ValueError as e:
        assert "GLCS" in str(e)
    
    # Test missing columns in query_results
    try:
        df1 = pd.DataFrame({'GLCS': [1, 2]})
        df2 = pd.DataFrame({'entityGLCS': [1], 'missing_col': [1]})
        processor.perform_left_join(df1, df2)
        assert False, "Should raise ValueError for missing required columns"
    except ValueError as e:
        assert "missing required columns" in str(e)
    
    print("✓ Error handling test passed")


def test_custom_data():
    """Test with custom data that matches the expected use case."""
    print("\n=== Testing Custom Data ===")
    
    # Create more realistic test data
    perimetro_clientes = pd.DataFrame({
        'GLCS': ['GL001', 'GL002', 'GL003', 'GL004'],
        'cliente_id': [101, 102, 103, 104],
        'nombre_cliente': ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D'],
        'segmento': ['Corporativo', 'PyME', 'Corporativo', 'PyME'],
        'region': ['CABA', 'Interior', 'CABA', 'Interior']
    })
    
    query_results = pd.DataFrame({
        'entityGLCS': ['GL001', 'GL003'],  # Only 2 out of 4 matches
        'aliasJ': ['ALIAS_001', 'ALIAS_003'],
        'SGC': ['SGC_A', 'SGC_C'],
        'Status_GBO': ['ACTIVO', 'INACTIVO']
    })
    
    processor = DataProcessor()
    result = processor.perform_left_join(perimetro_clientes, query_results)
    
    # Check results
    assert len(result) == 4, "Should preserve all 4 rows from perimetro_clientes"
    
    # Check matched data
    gl001_row = result[result['GLCS'] == 'GL001'].iloc[0]
    assert gl001_row['aliasJ'] == 'ALIAS_001', "GL001 should have correct aliasJ"
    assert gl001_row['SGC'] == 'SGC_A', "GL001 should have correct SGC"
    
    # Check unmatched data (should be NaN)
    gl002_row = result[result['GLCS'] == 'GL002'].iloc[0]
    assert pd.isna(gl002_row['aliasJ']), "GL002 should have NaN for aliasJ"
    assert pd.isna(gl002_row['Status_GBO']), "GL002 should have NaN for Status_GBO"
    
    print("✓ Custom data test passed")
    print(f"Final result shape: {result.shape}")
    print("Sample of final result:")
    print(result.head())


def main():
    """Run all tests."""
    print("Running Data Processor Tests...")
    print("=" * 50)
    
    try:
        test_basic_join()
        test_keep_redundant_column()
        test_validation()
        test_error_handling()
        test_custom_data()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        
        # Run the demonstration
        print("\n" + "=" * 50)
        print("DEMONSTRATION:")
        from backend.data_processor import demonstrate_join
        demonstrate_join()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()