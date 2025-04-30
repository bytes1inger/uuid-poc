import os
import pandas as pd
from src.utils import ensure_dir


class WarehouseLoader:
    """
    Handles loading transformed data to the data warehouse.
    
    This class is responsible for the Load phase of the ELT pipeline.
    It takes the transformed data with global unique identifiers and loads
    it into the final destination, which in this POC is represented by
    CSV files. In a production environment, this would typically involve
    loading to a database, data lake, or other storage system.
    
    The class also provides a method to simulate SQL queries that would
    be run against the data warehouse to demonstrate the value of the
    unified data model with global IDs.
    """
    def __init__(self, warehouse_dir="output/warehouse", final_dir="output/final"):
        """
        Initialize the loader with warehouse and final destination directories.
        
        Args:
            warehouse_dir (str): Directory containing transformed data
            final_dir (str): Directory to store final data
        """
        self.warehouse_dir = warehouse_dir
        self.final_dir = final_dir
        ensure_dir(final_dir)
    
    def load_table(self, table_name):
        """
        Load a specific table to the final destination.
        
        This method reads a transformed table from the warehouse directory,
        optionally applies any final transformations or quality checks,
        and loads it to the final destination. In a real scenario, this might
        involve loading to a database table with appropriate schema validation.
        
        Args:
            table_name (str): Name of the table to load
        
        Returns:
            bool: True if successful, False otherwise
        """
        source_path = os.path.join(self.warehouse_dir, f"{table_name}.csv")
        
        if not os.path.exists(source_path):
            print(f"Table {table_name} not found in warehouse")
            return False
        
        # Read the data
        df = pd.read_csv(source_path)
        
        # In a real scenario, you might apply final transformations,
        # data quality checks, or load to a database with appropriate
        # schema validation and error handling
        
        # Save to final directory
        final_path = os.path.join(self.final_dir, f"{table_name}.csv")
        df.to_csv(final_path, index=False)
        
        print(f"Loaded {table_name} to final destination with {len(df)} records")
        return True
    
    def load_all_tables(self):
        """
        Load all tables from the warehouse to the final destination.
        
        This method scans the warehouse directory for all CSV files
        and loads each one to the final destination. This provides
        a convenient way to load all transformed data in one operation.
        
        Returns:
            dict: Dictionary with table names and success status
        """
        results = {}
        
        # Find all CSV files in the warehouse directory
        for file in os.listdir(self.warehouse_dir):
            if file.endswith('.csv'):
                table_name = os.path.splitext(file)[0]
                results[table_name] = self.load_table(table_name)
        
        return results
    
    def simulate_sql_queries(self):
        """
        Simulate SQL queries that would be run in a real data warehouse.
        
        This method demonstrates the value of the unified data model with
        global IDs by simulating several analytical queries that would
        be challenging or impossible with the original separated data sources.
        It shows how we can now join data across previously separate tables
        and find insights that span multiple data sources.
        
        Returns:
            dict: Dictionary of query results for different analytical scenarios
        """
        results = {}
        
        # Load necessary tables
        users_path = os.path.join(self.warehouse_dir, "users.csv")
        if not os.path.exists(users_path):
            return {"error": "Users table not found"}
        
        users = pd.read_csv(users_path)
        
        # Example 1: Count of users by source database
        # This shows the distribution of users across source systems
        users_by_source = users.groupby('source_database').size().reset_index(name='count')
        results["users_by_source"] = users_by_source
        
        # Example 2: Find potentially duplicate users (same name and email across sources)
        # This demonstrates how we can identify potential duplicate user accounts
        # across previously separate systems
        if len(users) > 0:
            potential_duplicates = users[users.duplicated(subset=['name', 'email'], keep=False)]
            results["potential_duplicates"] = potential_duplicates
        
        # Example 3: Join with transactions if available
        # This shows how we can now analyze user activity across previously
        # separate systems using the global_user_id
        transactions_path = os.path.join(self.warehouse_dir, "transactions.csv")
        if os.path.exists(transactions_path):
            transactions = pd.read_csv(transactions_path)
            
            # Join users with their transactions using the global_user_id
            # This was previously impossible with separate systems and overlapping IDs
            user_transactions = pd.merge(
                users[['global_user_id', 'name', 'email']],
                transactions,
                on='global_user_id',
                how='inner'
            )
            
            # Group by user and calculate statistics
            # This provides insights into user transaction patterns
            tx_stats = user_transactions.groupby(['global_user_id', 'name'])\
                .agg({'amount': ['count', 'sum', 'mean']})\
                .reset_index()
            
            # Flatten the multi-level column index for easier interpretation
            tx_stats.columns = ['global_user_id', 'name', 'transaction_count', 'total_amount', 'avg_amount']
            
            results["transaction_stats"] = tx_stats
        
        return results


if __name__ == "__main__":
    # Test the loader when run directly
    loader = WarehouseLoader()
    load_results = loader.load_all_tables()
    print(f"Loaded {sum(load_results.values())} tables successfully")
    
    # Simulate SQL queries to demonstrate the value of the unified data model
    query_results = loader.simulate_sql_queries()
    for query, result in query_results.items():
        if isinstance(result, pd.DataFrame) and not result.empty:
            print(f"\nResults for query: {query}")
            print(result.head()) 