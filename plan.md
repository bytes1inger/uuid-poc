# ELT Pipeline Plan: User Data Consolidation with Global Unique Identifiers (UUIDs)

## Problem Statement

We have multiple source databases (A, B, C), each with their own `users` table using auto-incrementing IDs. When combining these in a data warehouse, we need to:

1. Create global unique identifiers for each user
2. Maintain referential integrity with related tables (logs, transactions, etc.)
3. Preserve source lineage information
4. Support future updates/additions from source systems

### ⚠️ Example: Potential ID Conflict
Database A and B both have a user with `user_id = 1`, name = "John Doe".
→ Without a global ID, their records would be incorrectly merged.

## Source Data Structure

```
Database A                    Database B                    Database C
+-----------------+           +-----------------+           +-----------------+
| databaseA.users |           | databaseB.users |           | databaseC.users |
+-----------------+           +-----------------+           +-----------------+
| user_id (PK)    |           | user_id (PK)    |           | user_id (PK)    |
| name            |           | name            |           | name            |
| email           |           | email           |           | email           |
| ...             |           | ...             |           | ...             |
+-----------------+           +-----------------+           +-----------------+
        |                             |                             |
        ↓                             ↓                             ↓
+-----------------+           +-----------------+           +-----------------+
| transactions    |           | orders          |           | logs            |
+-----------------+           +-----------------+           +-----------------+
| tx_id           |           | order_id        |           | log_id          |
| user_id (FK)    |           | user_id (FK)    |           | user_id (FK)    |
| amount          |           | total           |           | action          |
| ...             |           | ...             |           | ...             |
+-----------------+           +-----------------+           +-----------------+
```

## Proposed Solution Architecture

```
                             ELT Pipeline
+-------+   +-------+   +-------+          +-------------------+
| DB A  |   | DB B  |   | DB C  |  Extract | Staging Area      |
+-------+   +-------+   +-------+  ------> | (Raw data)        |
                                           +-------------------+
                                                    |
                                                    | Transform
                                                    ↓
                                           +-------------------+
                                           | User Mapping      |
                                           | Table             |
                                           +-------------------+
                                                    |
                                                    | Map via UUID
                                                    ↓
                                           +-------------------+
                                           | Data Warehouse    |
                                           | (Global IDs)      |
                                           +-------------------+
```

## Implementation Steps

### 1. Extract Phase

- Pull data from all source databases into a staging area
- Preserve all original IDs and metadata
- Add source identifier to each record
- Optionally: Capture extraction timestamp for auditing

### 2. Transform Phase: Creating Global User IDs

#### Step 2.1: Create User Mapping Table

```
+-------------------------+
| user_mapping            |
+-------------------------+
| global_user_id (UUID)   |
| source_database         |
| original_user_id        |
| created_at              |
| updated_at              |
+-------------------------+
```

This table serves as the bridge between original source IDs and global IDs.

#### Step 2.2: Generate User Mapping Records

For each user record from each source:
1. Generate a UUID/global ID
2. Create a mapping record with (source, original_id) → global_id

> ✅ Use a **deterministic UUID (UUID5)** or hash (e.g., SHA256 of source_name + original_user_id) to ensure consistent ID generation across reruns. Avoid random UUIDs (UUID4) unless they are stored and reused.

```python
# Example of deterministic UUID generation in Python
import uuid
import hashlib

def generate_deterministic_id(source_db, original_id):
    # Create a namespace UUID (can be any fixed UUID)
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    
    # Create the input string
    input_str = f"{source_db}:{original_id}"
    
    # Generate a UUID5 (SHA-1 based) from the namespace and input string
    return str(uuid.uuid5(namespace, input_str))
```

#### Step 2.3: Create Consolidated Users Table

```
+-------------------------+
| users                   |
+-------------------------+
| global_user_id (PK)     |
| name                    |
| email                   |
| source_database         |
| original_user_id        |
| data_hash               | # Optional: For change detection
| other_attributes...     |
+-------------------------+
```

### 3. Transform Phase: Related Tables

For each related table (transactions, logs, orders, etc.):

1. Add a global_user_id column
2. Join with the mapping table to populate global_user_id
3. Maintain original_user_id for lineage

> 🔁 For frequent updates, consider storing a version or hash of the user payload to detect changes efficiently.

Example:
```
+-------------------------+
| transactions            |
+-------------------------+
| transaction_id          |
| global_user_id          |
| original_user_id        |
| source_database         |
| amount                  |
| other_attributes...     |
+-------------------------+
```

### 4. Load Phase

Load the transformed data into the data warehouse with all references using global IDs.

> 📦 For incremental loads:
> - Use `source_database + original_user_id` as the key.
> - Merge/upsert into the `user_mapping` and `users` tables.

## Handling Updates and Incremental Loads

1. New records from source systems get new global IDs (deterministically or via lookup)
2. Updates to existing records are identified by (source, original_id)
3. The mapping table remains the source of truth for ID relationships
4. Optional: Use Change Data Capture (CDC) or last modified timestamps

Sample incremental load process:
```
For each source database:
    1. Extract modified records since last extraction
    2. For each record:
        a. Check if (source_db, original_id) exists in mapping table
        b. If exists, update corresponding record
        c. If not, generate new global ID and create mapping
    3. Update related tables using the mapping
```

## Handling Data Quality Issues

1. **Duplicate Detection**: Implement fuzzy matching to identify potential duplicates across sources
2. **Conflicting Data**: Create rules for resolving conflicts when the same user appears in multiple systems
3. **Data Validation**: Implement validation rules for critical fields
4. **Error Handling**: Create error tables to track records that fail processing

## Proof of Concept Implementation

For the POC using Pandas:

1. Create sample dataframes for each source database
2. Implement the transformation logic to generate global IDs (e.g., using UUID5)
3. Update related tables using the mapping table
4. Demonstrate querying across previously separate data sources

Optional: Simulate joins and constraints using SQLite or DuckDB for closer resemblance to production SQL behavior.

```python
# Sample implementation sketch
import pandas as pd
import uuid

# Create sample data
db_a_users = pd.DataFrame({
    'user_id': [1, 2, 3],
    'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
    'email': ['john@example.com', 'jane@example.com', 'bob@example.com']
})

db_a_transactions = pd.DataFrame({
    'tx_id': [101, 102, 103, 104],
    'user_id': [1, 1, 2, 3],
    'amount': [100, 200, 50, 75]
})

db_b_users = pd.DataFrame({
    'user_id': [1, 2, 4],
    'name': ['Alice Cooper', 'Bob Johnson', 'Carol Davis'],
    'email': ['alice@example.com', 'bob2@example.com', 'carol@example.com']
})

# Function to generate deterministic UUIDs
def generate_uuid(source, original_id):
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    return str(uuid.uuid5(namespace, f"{source}:{original_id}"))

# Create user mapping table
mapping_records = []

# Process Database A users
for _, user in db_a_users.iterrows():
    mapping_records.append({
        'global_user_id': generate_uuid('db_a', user['user_id']),
        'source_database': 'db_a',
        'original_user_id': user['user_id']
    })

# Process Database B users
for _, user in db_b_users.iterrows():
    mapping_records.append({
        'global_user_id': generate_uuid('db_b', user['user_id']),
        'source_database': 'db_b',
        'original_user_id': user['user_id']
    })

user_mapping = pd.DataFrame(mapping_records)

# Transform related tables (example for transactions)
transformed_transactions = db_a_transactions.copy()
transformed_transactions['source_database'] = 'db_a'
transformed_transactions['original_user_id'] = transformed_transactions['user_id']

# Map to global IDs
transaction_mapping = pd.merge(
    transformed_transactions,
    user_mapping,
    left_on=['source_database', 'original_user_id'],
    right_on=['source_database', 'original_user_id'],
    how='left'
)

# Final transactions table with global IDs
final_transactions = transaction_mapping[['tx_id', 'global_user_id', 'original_user_id', 'source_database', 'amount']]
```

## Scaling to Production

1. **Performance Optimization**: 
   - For large datasets, consider distributed processing with Spark or Dask
   - Add appropriate indexing on mapping tables
   - Partition data by source or date ranges

2. **Monitoring and Alerting**:
   - Track record counts at each stage
   - Monitor for mapping failures
   - Alert on unexpected data patterns

3. **Deployment Options**:
   - Cloud data warehouse (Snowflake, BigQuery, Redshift)
   - Data lakehouse architecture (Delta Lake, Iceberg)
   - ETL orchestration with Airflow, Prefect, or dbt

## Benefits of This Approach

1. Maintains referential integrity across all tables
2. Preserves original IDs for auditing and lineage
3. Supports incremental updates from source systems
4. Scales to handle large datasets in a distributed environment
5. Handles potential duplicates across source systems
6. Enables reproducibility and reprocessing with deterministic IDs
7. Provides a foundation for master data management
8. Supports future data quality initiatives 