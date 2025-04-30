"""
main.py - Entry point for the User Data Consolidation POC

This is the main orchestration script for the ELT (Extract, Load, Transform) pipeline
that demonstrates a solution for consolidating user data from multiple sources with
potentially overlapping IDs. 

The script handles:
1. Command line argument parsing for flexible execution options
2. Orchestration of the complete ELT pipeline using the specialized components
3. Generation of sample data for demonstration purposes
4. Creation of necessary output directories
5. Summary reporting of the consolidated data
6. Simulation of incremental updates to demonstrate how the solution handles new data

Usage examples:
    # Run with existing data
    python src/main.py
    
    # Generate new sample data and run
    python src/main.py --generate-data --sample-size 100
    
    # Run with analysis queries
    python src/main.py --analyze
"""

import os
import argparse
import pandas as pd

from src.utils import ensure_dir, generate_sample_data
from src.extract import DatabaseExtractor
from src.transform import DataTransformer
from src.load import WarehouseLoader


def parse_args():
    """
    Parse command line arguments for configuring the pipeline execution.
    
    Returns:
        argparse.Namespace: Parsed command line arguments with the following attributes:
            - generate_data: Whether to generate sample data before running
            - sample_size: Number of user records to generate per database
            - data_dir: Directory containing source database files
            - output_dir: Base directory for output files
            - analyze: Whether to run analysis queries on the final data
    """
    parser = argparse.ArgumentParser(description='Run the ELT pipeline for user data consolidation')
    
    parser.add_argument('--generate-data', action='store_true',
                        help='Generate sample data before running the pipeline')
    parser.add_argument('--sample-size', type=int, default=50,
                        help='Sample size for data generation (default: 50)')
    parser.add_argument('--data-dir', type=str, default='data',
                        help='Directory containing source database files (default: data)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Base directory for output files (default: output)')
    parser.add_argument('--analyze', action='store_true',
                        help='Run analysis queries on the final data')
    
    return parser.parse_args()


def run_pipeline(args):
    """
    Run the complete ELT pipeline from extraction to loading with optional analysis.
    
    This function orchestrates the entire pipeline process:
    1. Optionally generates sample data
    2. Creates necessary output directories
    3. Extracts data from source databases
    4. Transforms data with global UUID generation
    5. Loads transformed data to the final destination
    6. Optionally runs analysis queries
    7. Provides a summary of the consolidated data
    
    Args:
        args (argparse.Namespace): Command line arguments
    """
    print("\n=== Starting ELT Pipeline for User Data Consolidation ===\n")
    
    # Generate sample data if requested
    if args.generate_data:
        print("Generating sample data...")
        generate_sample_data(base_dir=args.data_dir, sample_size=args.sample_size)
    
    # Create output directories
    staging_dir = os.path.join(args.output_dir, 'staging')
    mapping_dir = os.path.join(args.output_dir, 'mapping')
    warehouse_dir = os.path.join(args.output_dir, 'warehouse')
    final_dir = os.path.join(args.output_dir, 'final')
    
    ensure_dir(staging_dir)
    ensure_dir(mapping_dir)
    ensure_dir(warehouse_dir)
    ensure_dir(final_dir)
    
    # Extract data from sources
    print("\n=== Extract Phase ===")
    extractor = DatabaseExtractor(source_dir=args.data_dir, staging_dir=staging_dir)
    all_data = extractor.extract_all_databases()
    
    # Transform data
    print("\n=== Transform Phase ===")
    transformer = DataTransformer(staging_dir=staging_dir, mapping_dir=mapping_dir, warehouse_dir=warehouse_dir)
    transformed_tables = transformer.transform_all_tables(all_data)
    
    # Load data to final destination
    print("\n=== Load Phase ===")
    loader = WarehouseLoader(warehouse_dir=warehouse_dir, final_dir=final_dir)
    load_results = loader.load_all_tables()
    
    print(f"\nLoaded {sum(load_results.values())} tables successfully to {final_dir}")
    
    # Run analysis if requested
    if args.analyze:
        print("\n=== Analysis ===")
        query_results = loader.simulate_sql_queries()
        
        for query, result in query_results.items():
            if isinstance(result, pd.DataFrame) and not result.empty:
                print(f"\nResults for query: {query}")
                print(result.head())
                
                # Save analysis results
                analysis_dir = os.path.join(args.output_dir, 'analysis')
                ensure_dir(analysis_dir)
                result.to_csv(os.path.join(analysis_dir, f"{query}.csv"), index=False)
    
    print("\n=== Pipeline Complete ===")
    print(f"Final data available in: {final_dir}")
    
    # Provide summary of the data
    users_path = os.path.join(final_dir, "users.csv")
    if os.path.exists(users_path):
        users = pd.read_csv(users_path)
        print(f"\nTotal users: {len(users)}")
        print(f"Users by source:")
        print(users.groupby('source_database').size().reset_index(name='count'))
        
        # Check mapping consistency
        mapping_path = os.path.join(mapping_dir, "user_mapping.csv")
        if os.path.exists(mapping_path):
            mapping = pd.read_csv(mapping_path)
            print(f"\nMapping records: {len(mapping)}")
            
            # Check for unmapped users
            merged = pd.merge(
                users[['global_user_id', 'source_database', 'original_user_id']],
                mapping[['global_user_id', 'source_database', 'original_user_id']],
                on=['source_database', 'original_user_id'],
                how='left'
            )
            
            unmapped = merged[merged['global_user_id_y'].isna()]
            if len(unmapped) > 0:
                print(f"Warning: {len(unmapped)} users are not properly mapped!")
            else:
                print("All users are properly mapped with global IDs.")


def run_incremental_update(args):
    """
    Simulate an incremental update by adding new records to an existing database.
    
    This function demonstrates how the pipeline handles new data while maintaining
    existing mappings. It adds new users and related data to database_a, then
    runs the pipeline again to process these new records. This shows how:
    
    1. The system preserves existing ID mappings
    2. New records receive deterministic global IDs
    3. Referential integrity is maintained for related tables
    4. The incremental process is efficient by only processing new/changed data
    
    Args:
        args (argparse.Namespace): Command line arguments
    """
    print("\n=== Running Incremental Update Simulation ===\n")
    
    # Create a small dataframe with new users
    new_users = pd.DataFrame({
        'user_id': [101, 102, 103],  # New IDs outside the original range
        'name': ['New User 1', 'New User 2', 'New User 3'],
        'email': ['newuser1@example.com', 'newuser2@example.com', 'newuser3@example.com'],
        'age': [25, 30, 35],
        'signup_date': pd.date_range(start='2023-01-01', periods=3, freq='D')
    })
    
    # Add to database_a
    db_a_path = os.path.join(args.data_dir, 'database_a', 'users.csv')
    if os.path.exists(db_a_path):
        db_a_users = pd.read_csv(db_a_path)
        combined_users = pd.concat([db_a_users, new_users], ignore_index=True)
        combined_users.to_csv(db_a_path, index=False)
        print(f"Added {len(new_users)} new users to database_a")
        
        # Create a transaction for one of the new users
        new_tx = pd.DataFrame({
            'tx_id': [10000],  # High ID to avoid conflicts
            'user_id': [101],  # Reference to one of the new users
            'amount': [199.99],
            'transaction_date': ['2023-01-10'],
            'category': ['electronics']
        })
        
        tx_path = os.path.join(args.data_dir, 'database_a', 'transactions.csv')
        if os.path.exists(tx_path):
            tx_data = pd.read_csv(tx_path)
            combined_tx = pd.concat([tx_data, new_tx], ignore_index=True)
            combined_tx.to_csv(tx_path, index=False)
            print(f"Added a new transaction for user_id 101")
    
    # Run the pipeline again to process these new records
    run_pipeline(args)


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Run the initial pipeline
    run_pipeline(args)
    
    # Ask if user wants to simulate an incremental update
    if input("\nDo you want to simulate an incremental update? (y/n): ").lower() == 'y':
        run_incremental_update(args) 