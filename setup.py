import os
import sys
from pathlib import Path


def create_project_structure():
    """Create the project directory structure"""
    # List of directories to create
    directories = [
        'data/database_a',
        'data/database_b',
        'data/database_c',
        'src',
        'output/staging',
        'output/mapping',
        'output/warehouse',
        'output/final',
        'output/analysis',
        'notebooks',
        'tests',
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py files in all Python directories
    for directory in ['src', 'tests']:
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# This file makes the directory a Python package\n')
            print(f"Created file: {init_file}")
    
    print("\nProject structure created successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Generate sample data: python src/main.py --generate-data --sample-size 50")
    print("3. Run the ELT pipeline: python src/main.py --analyze")


if __name__ == "__main__":
    create_project_structure() 