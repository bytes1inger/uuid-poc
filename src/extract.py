import os
import pandas as pd
from src.utils import ensure_dir


class DatabaseExtractor:
    """
    Handles extraction of data from source databases.
    
    This class is responsible for the Extract phase of the ELT pipeline.
    It reads data from CSV files representing separate database sources,
    adds source identification metadata, and stages the data for transformation.
    The class supports extracting all tables from all databases or specific tables
    as needed.
    """
    def __init__(self, source_dir="data", staging_dir="output/staging"):
        """
        Initialize the extractor with source and staging directories.
        
        Args:
            source_dir (str): Directory containing source database files
            staging_dir (str): Directory to store staged data
        """
        self.source_dir = source_dir
        self.staging_dir = staging_dir
        # Ensure the staging directory exists
        ensure_dir(staging_dir)
        
    def extract_database(self, db_name):
        """
        Extract all tables from a specific source database.
        
        This method reads all CSV files in the specified database directory,
        adds source database metadata, and stages the data for transformation.
        Each table is stored in the staging area with the database name prefixed
        to avoid name collisions.
        
        Args:
            db_name (str): Name of the database to extract (e.g., 'database_a')
            
        Returns:
            dict: Dictionary containing dataframes for each table in the database
        
        Raises:
            ValueError: If the database path doesn't exist
        """
        db_path = os.path.join(self.source_dir, db_name)
        
        if not os.path.exists(db_path):
            raise ValueError(f"Database path not found: {db_path}")
        
        # Get all CSV files in the database directory
        tables = {}
        for file in os.listdir(db_path):
            if file.endswith('.csv'):
                table_name = os.path.splitext(file)[0]
                file_path = os.path.join(db_path, file)
                
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Add source database information to maintain lineage
                df['source_database'] = db_name
                
                # Store in dictionary
                tables[table_name] = df
                
                # Save to staging area with prefixed name to avoid collisions
                staging_path = os.path.join(self.staging_dir, f"{db_name}_{table_name}.csv")
                df.to_csv(staging_path, index=False)
                print(f"Extracted {table_name} from {db_name} with {len(df)} rows")
                
        return tables
    
    def extract_all_databases(self):
        """
        Extract all tables from all source databases.
        
        This method searches for directories in the source directory that
        represent databases (prefixed with 'database_'), and extracts all
        tables from each one. This provides a complete extraction of all
        available data for the ELT pipeline.
        
        Returns:
            dict: Nested dictionary containing dataframes for each table in each database,
                  organized as {database_name: {table_name: dataframe}}
        """
        all_data = {}
        
        # Look for directories in the source directory that represent databases
        for item in os.listdir(self.source_dir):
            db_path = os.path.join(self.source_dir, item)
            if os.path.isdir(db_path) and item.startswith('database_'):
                all_data[item] = self.extract_database(item)
                
        return all_data
    
    def extract_specific_table(self, table_name):
        """
        Extract a specific table from all databases.
        
        This method is useful when you only need to process a specific type of table
        (e.g., 'users') from all available databases. It searches for the specified
        table in each database directory and extracts only those tables.
        
        Args:
            table_name (str): Name of the table to extract (e.g., 'users')
            
        Returns:
            dict: Dictionary containing the specified table from each database
                 where it exists, organized as {database_name: dataframe}
        """
        tables = {}
        
        # Look for the specific table in each database directory
        for item in os.listdir(self.source_dir):
            db_path = os.path.join(self.source_dir, item)
            if os.path.isdir(db_path) and item.startswith('database_'):
                # Check if the table exists in this database
                table_path = os.path.join(db_path, f"{table_name}.csv")
                if os.path.exists(table_path):
                    # Read the table
                    df = pd.read_csv(table_path)
                    
                    # Add source database information
                    df['source_database'] = item
                    
                    # Store in dictionary
                    tables[item] = df
                    
                    # Save to staging area
                    staging_path = os.path.join(self.staging_dir, f"{item}_{table_name}.csv")
                    df.to_csv(staging_path, index=False)
                    print(f"Extracted {table_name} from {item} with {len(df)} rows")
        
        return tables


if __name__ == "__main__":
    # Test the extractor when run directly
    extractor = DatabaseExtractor()
    all_data = extractor.extract_all_databases()
    print(f"Extracted data from {len(all_data)} databases") 