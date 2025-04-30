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