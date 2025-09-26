import pandas as pd
from typing import Optional


class DataProcessor:
    """
    Data processing utilities for joining dataframes and performing data operations.
    
    This module implements the left join functionality between perimetro_clientes
    and query_results dataframes as specified in the requirements.
    """
    
    @staticmethod
    def perform_left_join(
        perimetro_clientes: pd.DataFrame,
        query_results: pd.DataFrame,
        remove_redundant_column: bool = True
    ) -> pd.DataFrame:
        """
        Perform a left join between perimetro_clientes and query_results dataframes.
        
        Args:
            perimetro_clientes: Left dataframe containing client perimeter data
            query_results: Right dataframe containing query results with columns:
                          entityGLCS, aliasJ, SGC, Status_GBO
            remove_redundant_column: Whether to remove the redundant entityGLCS column
                                   after the join (default: True)
        
        Returns:
            pd.DataFrame: Result of the left join with all columns from perimetro_clientes
                         plus aliasJ, SGC, and Status_GBO from query_results.
                         Non-matching entries are filled with NaN.
        
        Raises:
            ValueError: If required columns are missing from the dataframes
        """
        
        # Validate input dataframes
        if perimetro_clientes.empty:
            raise ValueError("perimetro_clientes dataframe is empty")
            
        if query_results.empty:
            raise ValueError("query_results dataframe is empty")
        
        # Check for required columns
        if 'GLCS' not in perimetro_clientes.columns:
            raise ValueError("perimetro_clientes must contain 'GLCS' column")
            
        required_query_cols = ['entityGLCS', 'aliasJ', 'SGC', 'Status_GBO']
        missing_cols = [col for col in required_query_cols if col not in query_results.columns]
        if missing_cols:
            raise ValueError(f"query_results missing required columns: {missing_cols}")
        
        # Select only the required columns from query_results for the join
        query_subset = query_results[['entityGLCS', 'aliasJ', 'SGC', 'Status_GBO']].copy()
        
        # Perform the left join
        perimetro_completo = perimetro_clientes.merge(
            query_subset,
            left_on='GLCS',
            right_on='entityGLCS',
            how='left'
        )
        
        # Optionally remove the redundant entityGLCS column
        if remove_redundant_column:
            perimetro_completo = perimetro_completo.drop('entityGLCS', axis=1, errors='ignore')
        
        return perimetro_completo
    
    @staticmethod
    def validate_join_result(
        original_df: pd.DataFrame,
        joined_df: pd.DataFrame,
        expected_new_columns: list
    ) -> dict:
        """
        Validate the result of a dataframe join operation.
        
        Args:
            original_df: The original left dataframe
            joined_df: The result dataframe after join
            expected_new_columns: List of columns that should have been added
        
        Returns:
            dict: Validation results with statistics about the join
        """
        
        # Check row count preservation (left join should preserve all rows)
        rows_preserved = len(joined_df) == len(original_df)
        
        # Check if new columns were added
        original_cols = set(original_df.columns)
        joined_cols = set(joined_df.columns)
        added_cols = joined_cols - original_cols
        
        # Check for expected columns
        expected_cols = set(expected_new_columns)
        has_expected_cols = expected_cols.issubset(joined_cols)
        
        # Count non-null values in new columns
        null_counts = {}
        for col in expected_new_columns:
            if col in joined_df.columns:
                null_counts[col] = joined_df[col].isnull().sum()
        
        return {
            'rows_preserved': rows_preserved,
            'original_row_count': len(original_df),
            'joined_row_count': len(joined_df),
            'has_expected_columns': has_expected_cols,
            'added_columns': list(added_cols),
            'expected_columns': expected_new_columns,
            'null_counts': null_counts,
            'join_success': rows_preserved and has_expected_cols
        }


def create_sample_dataframes():
    """
    Create sample dataframes for testing the join functionality.
    
    Returns:
        tuple: (perimetro_clientes, query_results) sample dataframes
    """
    
    # Sample perimetro_clientes dataframe
    perimetro_clientes = pd.DataFrame({
        'GLCS': ['GLCS001', 'GLCS002', 'GLCS003', 'GLCS004', 'GLCS005'],
        'client_name': ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E'],
        'region': ['Norte', 'Sur', 'Este', 'Oeste', 'Centro'],
        'status': ['Active', 'Active', 'Inactive', 'Active', 'Pending']
    })
    
    # Sample query_results dataframe (some GLCs missing to test NaN filling)
    query_results = pd.DataFrame({
        'entityGLCS': ['GLCS001', 'GLCS002', 'GLCS004'],  # GLCS003 and GLCS005 missing
        'aliasJ': ['Alias_A', 'Alias_B', 'Alias_D'],
        'SGC': ['SGC_001', 'SGC_002', 'SGC_004'],
        'Status_GBO': ['Active_GBO', 'Pending_GBO', 'Active_GBO']
    })
    
    return perimetro_clientes, query_results


# Example usage function
def demonstrate_join():
    """
    Demonstrate the join functionality with sample data.
    """
    print("Creating sample dataframes...")
    perimetro_clientes, query_results = create_sample_dataframes()
    
    print("\nOriginal perimetro_clientes:")
    print(perimetro_clientes)
    print(f"Shape: {perimetro_clientes.shape}")
    
    print("\nOriginal query_results:")
    print(query_results)
    print(f"Shape: {query_results.shape}")
    
    # Perform the join
    processor = DataProcessor()
    result = processor.perform_left_join(perimetro_clientes, query_results)
    
    print("\nAfter left join:")
    print(result)
    print(f"Shape: {result.shape}")
    
    # Validate the result
    validation = processor.validate_join_result(
        perimetro_clientes, 
        result, 
        ['aliasJ', 'SGC', 'Status_GBO']
    )
    
    print("\nValidation results:")
    for key, value in validation.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demonstrate_join()