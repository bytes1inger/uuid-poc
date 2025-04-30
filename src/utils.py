import os
import uuid
import pandas as pd
import numpy as np
from pathlib import Path


def ensure_dir(directory):
    """
    Create directory if it doesn't exist.
    
    This utility function creates directories recursively, ensuring all parent
    directories also exist. Uses pathlib for cross-platform compatibility.
    
    Args:
        directory (str): Path to the directory to create
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def generate_deterministic_id(source_db, original_id):
    """
    Generate a deterministic UUID using UUID5 based on source and original ID.
    
    This is a crucial function that creates reproducible, globally unique IDs
    for each user by hashing the combination of source database and original ID.
    Using UUID5 (with SHA-1) ensures the same inputs always produce the same UUID,
    which is essential for reproducible data transformations and incremental updates.
    
    Args:
        source_db (str): Source database identifier (e.g., 'database_a')
        original_id (int/str): Original user ID in the source database
        
    Returns:
        str: A UUID string that uniquely identifies this user globally
    """
    # Create a namespace UUID (can be any fixed UUID)
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    
    # Create the input string by combining source and ID
    input_str = f"{source_db}:{original_id}"
    
    # Generate a UUID5 (SHA-1 based) from the namespace and input string
    return str(uuid.uuid5(namespace, input_str))


def generate_sample_data(base_dir="data", sample_size=100, seed=42):
    """
    Generate sample data for three different source databases with overlapping IDs.
    
    This function creates realistic test data that simulates three separate
    databases with their own user tables and related data (transactions, orders, logs).
    The IDs in each database intentionally overlap to demonstrate the problem
    this solution addresses. The function maintains referential integrity within
    each database, creating related records only for valid user IDs.
    
    Args:
        base_dir (str): Base directory to store the generated data
        sample_size (int): Number of user records to generate for each database
        seed (int): Random seed for reproducibility
    """
    np.random.seed(seed)
    
    # Ensure base directories exist
    for db in ['database_a', 'database_b', 'database_c']:
        ensure_dir(os.path.join(base_dir, db))
    
    # Common names and domains for generating realistic-looking data
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
                  "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
                  "Emma", "Noah", "Olivia", "Liam", "Ava", "Benjamin", "Sophia", "Lucas", "Isabella", "Mason"]
    
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                 "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
                 "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "King", "Wright"]
    
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "protonmail.com"]
    
    # Generate user data for each database
    for db_name in ['database_a', 'database_b', 'database_c']:
        # User IDs will have some overlap between databases
        # This is intentional to demonstrate the problem our solution addresses
        user_ids = np.arange(1, sample_size + 1)
        
        # Generate random names
        names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(sample_size)]
        
        # Generate emails with different patterns for realism
        emails = []
        for name in names:
            first, last = name.lower().split(' ')
            domain = np.random.choice(domains)
            # Create a few different email patterns
            if np.random.random() < 0.3:
                email = f"{first}.{last}@{domain}"
            elif np.random.random() < 0.6:
                email = f"{first[0]}{last}@{domain}"
            else:
                email = f"{first}{last[0]}@{domain}"
            emails.append(email)
        
        # Create users dataframe
        users_df = pd.DataFrame({
            'user_id': user_ids,
            'name': names,
            'email': emails,
            'age': np.random.randint(18, 80, size=sample_size),
            'signup_date': pd.date_range(start='2020-01-01', periods=sample_size, freq='D')
        })
        
        # Save to CSV
        users_df.to_csv(os.path.join(base_dir, db_name, 'users.csv'), index=False)
        
        # Generate related tables specific to each database
        # Each database has a different type of related table, simulating
        # different applications or systems with their own data models
        if db_name == 'database_a':
            # Create transactions table for database_a
            transactions = []
            for user_id in user_ids:
                # Each user has between 1-5 transactions
                num_transactions = np.random.randint(1, 6)
                for _ in range(num_transactions):
                    transactions.append({
                        'tx_id': len(transactions) + 1,
                        'user_id': user_id,  # Foreign key to users table
                        'amount': np.round(np.random.uniform(10, 1000), 2),
                        'transaction_date': pd.Timestamp('2022-01-01') + pd.Timedelta(days=np.random.randint(0, 365)),
                        'category': np.random.choice(['food', 'transport', 'entertainment', 'shopping', 'services'])
                    })
            
            transactions_df = pd.DataFrame(transactions)
            transactions_df.to_csv(os.path.join(base_dir, db_name, 'transactions.csv'), index=False)
            
        elif db_name == 'database_b':
            # Create orders table for database_b
            orders = []
            for user_id in user_ids:
                # Each user has between 0-3 orders
                num_orders = np.random.randint(0, 4)
                for _ in range(num_orders):
                    orders.append({
                        'order_id': len(orders) + 1,
                        'user_id': user_id,  # Foreign key to users table
                        'total': np.round(np.random.uniform(20, 500), 2),
                        'order_date': pd.Timestamp('2022-01-01') + pd.Timedelta(days=np.random.randint(0, 365)),
                        'status': np.random.choice(['pending', 'shipped', 'delivered', 'cancelled'])
                    })
            
            orders_df = pd.DataFrame(orders)
            orders_df.to_csv(os.path.join(base_dir, db_name, 'orders.csv'), index=False)
            
        elif db_name == 'database_c':
            # Create logs table for database_c
            logs = []
            for user_id in user_ids:
                # Each user has between 2-10 logs
                num_logs = np.random.randint(2, 11)
                for _ in range(num_logs):
                    logs.append({
                        'log_id': len(logs) + 1,
                        'user_id': user_id,  # Foreign key to users table
                        'action': np.random.choice(['login', 'logout', 'view_page', 'click_button', 'search']),
                        'timestamp': pd.Timestamp('2022-01-01') + pd.Timedelta(seconds=np.random.randint(0, 31536000)),
                        'ip_address': f"{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
                    })
            
            logs_df = pd.DataFrame(logs)
            logs_df.to_csv(os.path.join(base_dir, db_name, 'logs.csv'), index=False)
    
    print(f"Sample data generated successfully in '{base_dir}' directory.")


def hash_row(row):
    """
    Create a hash of the row data for change detection.
    
    This utility function is used to detect changes in user data for
    incremental updates. By comparing hashes rather than full records,
    we can efficiently identify records that have changed.
    
    Args:
        row (pd.Series): A row from a pandas DataFrame
        
    Returns:
        int: A hash value representing the content of the row
    """
    return hash(tuple(row.values))


if __name__ == "__main__":
    # Test the data generation when run directly
    generate_sample_data(sample_size=50) 