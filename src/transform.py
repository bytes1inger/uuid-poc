import os
import pandas as pd
from src.utils import ensure_dir, generate_deterministic_id, hash_row


class DataTransformer:
    """
    Handles transformation of staged data including UUID generation and mapping.
    
    This class is responsible for the Transform phase of the ELT pipeline, which is
    the most critical part of solving the overlapping ID problem. It:
    1. Generates global unique identifiers (UUIDs) for users from different sources
    2. Creates and maintains a mapping table between original IDs and global IDs
    3. Transforms related tables to use the global IDs while preserving source info
    4. Handles both initial data loads and incremental updates
    
    The transformation maintains referential integrity across all tables while
    solving the problem of ID collisions across different source databases.
    """
    def __init__(self, staging_dir="output/staging", mapping_dir="output/mapping", warehouse_dir="output/warehouse"):
        """
        Initialize the transformer with directories for staged data, mapping tables, and transformed data.
        
        Args:
            staging_dir (str): Directory containing staged data from the extract phase
            mapping_dir (str): Directory to store mapping tables (crucial for ID relationships)
            warehouse_dir (str): Directory to store transformed data ready for loading
        """
        self.staging_dir = staging_dir
        self.mapping_dir = mapping_dir
        self.warehouse_dir = warehouse_dir
        
        # Create directories if they don't exist
        ensure_dir(staging_dir)
        ensure_dir(mapping_dir)
        ensure_dir(warehouse_dir)
        
        # Load existing mapping table if it exists (crucial for incremental updates)
        self.mapping_file = os.path.join(mapping_dir, "user_mapping.csv")
        if os.path.exists(self.mapping_file):
            self.user_mapping = pd.read_csv(self.mapping_file)
            print(f"Loaded existing mapping table with {len(self.user_mapping)} records")
        else:
            # Initialize empty mapping table with required columns
            self.user_mapping = pd.DataFrame(columns=['global_user_id', 'source_database', 'original_user_id', 'created_at'])
    
    def generate_user_mapping(self, users_dfs):
        """
        Generate a user mapping table from multiple user dataframes.
        
        This method is the core of the solution. It creates a mapping between 
        original source-specific user IDs and global UUIDs. For new users, it generates
        deterministic UUIDs that are consistent across pipeline runs. For existing users,
        it preserves their previously assigned UUIDs to maintain consistency.
        
        Args:
            users_dfs (dict): Dictionary of user dataframes from different sources,
                             organized as {source_database: dataframe}
            
        Returns:
            pd.DataFrame: Updated user mapping table that maps original IDs to global IDs
        """
        mapping_records = []
        current_mappings = set()
        
        # If we have an existing mapping, add them to the set to avoid duplicates
        # This is critical for incremental updates
        if not self.user_mapping.empty:
            for _, row in self.user_mapping.iterrows():
                current_mappings.add((row['source_database'], row['original_user_id']))
        
        # Process each source's users table
        for source, df in users_dfs.items():
            for _, user in df.iterrows():
                user_id = user['user_id']
                
                # Check if mapping already exists to handle incremental updates
                if (source, user_id) not in current_mappings:
                    # Generate a deterministic UUID - same inputs always produce same UUID
                    global_id = generate_deterministic_id(source, user_id)
                    
                    # Add to mapping records
                    mapping_records.append({
                        'global_user_id': global_id,
                        'source_database': source,
                        'original_user_id': user_id,
                        'created_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    # Add to set to avoid duplicates within this run
                    current_mappings.add((source, user_id))
        
        # Create new dataframe with new mappings
        new_mappings = pd.DataFrame(mapping_records)
        
        # Combine with existing mappings
        if not new_mappings.empty:
            self.user_mapping = pd.concat([self.user_mapping, new_mappings], ignore_index=True)
            print(f"Added {len(new_mappings)} new user mappings")
        
        # Save mapping table - critical to preserve for incremental updates
        self.user_mapping.to_csv(self.mapping_file, index=False)
        
        return self.user_mapping
    
    def transform_users_table(self, users_dfs):
        """
        Create a consolidated users table with global IDs.
        
        This method transforms and combines user data from all sources, 
        replacing source-specific IDs with global UUIDs while preserving
        the original ID and source information for lineage. It also adds
        a data hash for efficient change detection in future updates.
        
        Args:
            users_dfs (dict): Dictionary of user dataframes from different sources
            
        Returns:
            pd.DataFrame: Consolidated users table with global IDs
        """
        # Ensure we have the mapping table
        if self.user_mapping.empty:
            self.generate_user_mapping(users_dfs)
        
        consolidated_users = []
        
        # Process each source
        for source, df in users_dfs.items():
            # Add source columns to make each row uniquely identifiable
            df_copy = df.copy()
            df_copy['source_database'] = source
            df_copy['original_user_id'] = df_copy['user_id']
            
            # Create a data hash for change detection in incremental updates
            df_copy['data_hash'] = df_copy.apply(lambda row: hash_row(row), axis=1)
            
            # Merge with mapping table to add global IDs
            merged = pd.merge(
                df_copy,
                self.user_mapping,
                left_on=['source_database', 'original_user_id'],
                right_on=['source_database', 'original_user_id'],
                how='left'
            )
            
            # Add to consolidated users
            consolidated_users.append(merged)
        
        # Combine all sources
        if consolidated_users:
            all_users = pd.concat(consolidated_users, ignore_index=True)
            
            # Select and rename columns as needed for the final table
            final_users = all_users[['global_user_id', 'name', 'email', 'age', 'signup_date', 
                                    'source_database', 'original_user_id', 'data_hash']]
            
            # Save to warehouse
            warehouse_path = os.path.join(self.warehouse_dir, "users.csv")
            final_users.to_csv(warehouse_path, index=False)
            print(f"Created consolidated users table with {len(final_users)} records")
            
            return final_users
        
        return pd.DataFrame()
    
    def transform_related_table(self, table_name, related_dfs):
        """
        Transform a related table by adding global user IDs.
        
        This method takes tables that are related to users (transactions, orders, logs)
        and transforms them to use the global user IDs instead of the source-specific IDs.
        This maintains referential integrity across the consolidated data warehouse
        while preserving the original IDs and source information.
        
        Args:
            table_name (str): Name of the related table (e.g., 'transactions')
            related_dfs (dict): Dictionary of related table dataframes from different sources
            
        Returns:
            pd.DataFrame: Transformed related table with global user IDs
        
        Raises:
            ValueError: If user mapping table not generated first
        """
        # Ensure we have the mapping table
        if self.user_mapping.empty:
            raise ValueError("User mapping table not generated. Call generate_user_mapping first.")
        
        transformed_tables = []
        
        # Process each source
        for source, df in related_dfs.items():
            # Skip if dataframe is empty
            if df.empty:
                continue
                
            # Add source columns to track lineage
            df_copy = df.copy()
            df_copy['source_database'] = source
            df_copy['original_user_id'] = df_copy['user_id']
            
            # Merge with mapping table to map original user IDs to global user IDs
            merged = pd.merge(
                df_copy,
                self.user_mapping,
                left_on=['source_database', 'original_user_id'],
                right_on=['source_database', 'original_user_id'],
                how='left'
            )
            
            # Add to transformed tables
            transformed_tables.append(merged)
        
        # Combine all sources
        if transformed_tables:
            all_records = pd.concat(transformed_tables, ignore_index=True)
            
            # Drop the original user_id column and keep global_user_id
            # This is what enables combining data from different sources
            if 'user_id' in all_records.columns:
                all_records = all_records.drop(columns=['user_id'])
            
            # Save to warehouse
            warehouse_path = os.path.join(self.warehouse_dir, f"{table_name}.csv")
            all_records.to_csv(warehouse_path, index=False)
            print(f"Created transformed {table_name} table with {len(all_records)} records")
            
            return all_records
        
        return pd.DataFrame()
    
    def transform_all_tables(self, all_data):
        """
        Transform all tables from all sources in a unified process.
        
        This is the main method that orchestrates the entire transformation phase.
        It first generates the user mapping, then transforms the users table,
        and finally transforms all related tables to use the global IDs.
        
        Args:
            all_data (dict): Nested dictionary of dataframes from all sources,
                           organized as {source: {table_name: dataframe}}
            
        Returns:
            dict: Dictionary of transformed tables ready for loading
        """
        # Extract users tables from all sources
        users_dfs = {}
        for source, tables in all_data.items():
            if 'users' in tables:
                users_dfs[source] = tables['users']
        
        # Generate user mapping - this is the critical step for ID reconciliation
        self.generate_user_mapping(users_dfs)
        
        # Transform users table
        transformed_tables = {'users': self.transform_users_table(users_dfs)}
        
        # Transform related tables - any table that has a user_id foreign key
        related_tables = {'transactions', 'orders', 'logs'}
        
        for table in related_tables:
            # Extract the table from all sources
            table_dfs = {}
            for source, tables in all_data.items():
                if table in tables:
                    table_dfs[source] = tables[table]
            
            # Transform the table if it exists in any source
            if table_dfs:
                transformed_tables[table] = self.transform_related_table(table, table_dfs)
        
        return transformed_tables


if __name__ == "__main__":
    # Test the transformer with sample data when run directly
    from src.extract import DatabaseExtractor
    
    # Extract data from sources
    extractor = DatabaseExtractor()
    all_data = extractor.extract_all_databases()
    
    # Transform data
    transformer = DataTransformer()
    transformed_tables = transformer.transform_all_tables(all_data)
    
    print("Transformation complete!") 