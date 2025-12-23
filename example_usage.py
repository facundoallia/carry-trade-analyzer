#!/usr/bin/env python3
"""
Example usage of the data processor left join functionality.

This script demonstrates how to use the DataProcessor class to perform
the left join operation between perimetro_clientes and query_results
dataframes as specified in the requirements.
"""

import pandas as pd
from backend.data_processor import DataProcessor


def main():
    """
    Example usage showing the exact code pattern requested in the problem statement.
    """
    
    print("=== DataProcessor Left Join Example ===")
    print()
    
    # Create example dataframes (in real usage, these would come from your data sources)
    perimetro_clientes = pd.DataFrame({
        'GLCS': ['GL001', 'GL002', 'GL003', 'GL004', 'GL005'],
        'cliente_nombre': ['Cliente Alpha', 'Cliente Beta', 'Cliente Gamma', 'Cliente Delta', 'Cliente Epsilon'],
        'sector': ['Financiero', 'Tecnología', 'Salud', 'Energía', 'Retail'],
        'estado_actual': ['Activo', 'Activo', 'Suspendido', 'Activo', 'Pendiente'],
        'fecha_alta': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12']
    })
    
    query_results = pd.DataFrame({
        'entityGLCS': ['GL001', 'GL003', 'GL005'],  # Only partial matches
        'aliasJ': ['ALPHA_ALIAS', 'GAMMA_ALIAS', 'EPSILON_ALIAS'],
        'SGC': ['SGC_ALPHA', 'SGC_GAMMA', 'SGC_EPSILON'],
        'Status_GBO': ['ACTIVE_GBO', 'INACTIVE_GBO', 'PENDING_GBO']
    })
    
    print("Original perimetro_clientes dataframe:")
    print(perimetro_clientes)
    print(f"Shape: {perimetro_clientes.shape}")
    print()
    
    print("Original query_results dataframe:")
    print(query_results)
    print(f"Shape: {query_results.shape}")
    print()
    
    # Method 1: Using the DataProcessor class (recommended for reusability)
    print("Method 1: Using DataProcessor class")
    processor = DataProcessor()
    perimetro_completo_v1 = processor.perform_left_join(perimetro_clientes, query_results)
    
    print("Result using DataProcessor:")
    print(perimetro_completo_v1)
    print(f"Shape: {perimetro_completo_v1.shape}")
    print()
    
    # Method 2: Direct pandas merge (as shown in the problem statement example)
    print("Method 2: Direct pandas merge (as specified in problem statement)")
    
    # Realizar el left join manteniendo todas las columnas de perimetro_clientes
    perimetro_completo_v2 = perimetro_clientes.merge(
        query_results[['entityGLCS', 'aliasJ', 'SGC', 'Status_GBO']], 
        left_on='GLCS',
        right_on='entityGLCS',
        how='left'
    )
    
    # Opcional: eliminar la columna entityGLCS si no se necesita (ya que es redundante con GLCS)
    perimetro_completo_v2 = perimetro_completo_v2.drop('entityGLCS', axis=1, errors='ignore')
    
    print("Result using direct pandas merge:")
    print(perimetro_completo_v2)
    print(f"Shape: {perimetro_completo_v2.shape}")
    print()
    
    # Verify both methods produce the same result
    print("Verification: Both methods produce identical results:")
    are_equal = perimetro_completo_v1.equals(perimetro_completo_v2.reindex(perimetro_completo_v1.columns, axis=1))
    print(f"Results are identical: {are_equal}")
    print()
    
    # Show validation statistics
    validation = processor.validate_join_result(
        perimetro_clientes,
        perimetro_completo_v1,
        ['aliasJ', 'SGC', 'Status_GBO']
    )
    
    print("Join validation statistics:")
    print(f"  - Rows preserved: {validation['rows_preserved']}")
    print(f"  - Original rows: {validation['original_row_count']}")
    print(f"  - Final rows: {validation['joined_row_count']}")
    print(f"  - Expected columns added: {validation['has_expected_columns']}")
    print(f"  - Columns added: {validation['added_columns']}")
    print(f"  - Null counts: {validation['null_counts']}")
    print(f"  - Join successful: {validation['join_success']}")
    print()
    
    # Show which records have missing data
    print("Records with missing data (NaN values):")
    missing_data = perimetro_completo_v1[perimetro_completo_v1[['aliasJ', 'SGC', 'Status_GBO']].isnull().any(axis=1)]
    if not missing_data.empty:
        print(missing_data[['GLCS', 'cliente_nombre', 'aliasJ', 'SGC', 'Status_GBO']])
    else:
        print("No records with missing data found.")


if __name__ == "__main__":
    main()