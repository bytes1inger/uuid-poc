# User Data Consolidation POC

This proof of concept demonstrates an ELT pipeline for consolidating user data from multiple sources with potentially overlapping IDs. The solution generates global unique identifiers (UUIDs) while maintaining referential integrity across related tables.

## Folder Structure

```
uuid-poc/
│
├── data/                      # Sample input data
│   ├── database_a/            # Source database A
│   │   ├── users.csv
│   │   └── transactions.csv
│   ├── database_b/            # Source database B
│   │   ├── users.csv
│   │   └── orders.csv
│   └── database_c/            # Source database C
│       ├── users.csv
│       └── logs.csv
│
├── src/                       # Source code
│   ├── extract.py             # Data extraction routines
│   ├── transform.py           # Transformation logic including UUID generation
│   ├── load.py                # Data loading utilities
│   ├── utils.py               # Helper functions
│   └── main.py                # Main execution script
│
├── output/                    # Transformed output data
│   ├── mapping/               # ID mapping tables
│   │   └── user_mapping.csv
│   └── warehouse/             # Consolidated data
│       ├── users.csv
│       ├── transactions.csv
│       ├── orders.csv
│       └── logs.csv
│
├── notebooks/                 # Jupyter notebooks for analysis
│   └── data_exploration.ipynb
│
├── tests/                     # Unit tests
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
│
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the POC

There are several ways to run the proof of concept depending on your requirements:

### Basic Run

Execute the pipeline using existing data (if available):

```bash
python src/main.py
```

### Generate Sample Data

If you want to start fresh or don't have any data:

```bash
python src/main.py --generate-data
```

You can specify the number of sample records per database:

```bash
python src/main.py --generate-data --sample-size 100
```

### Run with Analysis

Run the pipeline and perform analytical queries on the consolidated data:

```bash
python src/main.py --analyze
```

You can combine options:

```bash
python src/main.py --generate-data --sample-size 75 --analyze
```

### Custom Directories

You can specify custom directories for input and output:

```bash
python src/main.py --data-dir custom_data --output-dir custom_output
```

### Incremental Updates

After running the pipeline initially, you'll be prompted to run an incremental update simulation:

```
Do you want to simulate an incremental update? (y/n):
```

Type `y` to see how the system handles new data while maintaining existing mappings.

## Exploring Results

After running the pipeline, you can explore the results in the following directories:

- `output/mapping/user_mapping.csv` - Maps original IDs to global IDs
- `output/warehouse/` - Consolidated data with global IDs
- `output/final/` - Final processed data ready for analysis
- `output/analysis/` - Results of analytical queries (if run with `--analyze`)

## Key Features

- Deterministic UUID generation for reproducible results
- Preservation of source database lineage
- Maintenance of referential integrity across tables
- Support for incremental updates
- Configurable data transformation

## Next Steps and Recommendations

This POC demonstrates core functionality for consolidating user data with UUIDs. Here are recommended next steps for extending and productionizing this solution:

### Data Quality Enhancements

- Implement data validation checks before transformation
- Add deduplication capabilities for identifying similar users across sources
- Create a robust error handling system with retry mechanisms
- Add logging and monitoring for pipeline performance and failures

### Scalability Improvements

- Migrate from CSV files to a proper database backend (PostgreSQL, MySQL, etc.)
- Implement parallel processing for large datasets using Dask or Spark
- Add support for streaming data sources for real-time consolidation
- Containerize the solution with Docker for easy deployment

### Additional Features

1. **Entity Resolution**: Enhance the system to detect and merge probable duplicate users across systems based on fuzzy matching of names, emails, etc.

2. **Web Interface**: Create a simple web dashboard to monitor the pipeline and explore the data visually.

3. **Scheduling**: Integrate with Airflow or other workflow tools to schedule regular updates.

4. **Change Data Capture**: Implement a CDC mechanism to only process changes from source systems.

5. **Master Data Management**: Extend to a full MDM solution with survivorship rules to determine which attributes from which sources should be considered authoritative.

### Suggested Extensions

You can extend this POC by implementing any of these features:

```bash
# Example: Add a simple web dashboard using Streamlit
pip install streamlit
python -m streamlit run dashboard.py
```

```python
# Example dashboard.py file structure
import streamlit as st
import pandas as pd
import os

st.title("User Data Consolidation Dashboard")

# Load data
users = pd.read_csv("output/final/users.csv")
mapping = pd.read_csv("output/mapping/user_mapping.csv")

# Display stats
st.metric("Total Consolidated Users", len(users))
st.metric("Total Source Systems", users['source_database'].nunique())

# Display data
st.subheader("User Sample")
st.dataframe(users.head(10))

st.subheader("ID Mapping Sample")
st.dataframe(mapping.head(10))

# Add visualizations
st.subheader("Users by Source")
st.bar_chart(users['source_database'].value_counts())
```

```bash
# Example: Add data quality checks using Great Expectations
pip install great_expectations
great_expectations init
```

These extensions would significantly enhance the practical applicability of this solution in real-world scenarios. 