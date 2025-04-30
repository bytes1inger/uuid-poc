import os
import sys
import uuid
import tempfile
import unittest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import ensure_dir, generate_deterministic_id, hash_row


class TestUtils(unittest.TestCase):
    
    def test_ensure_dir(self):
        """Test that ensure_dir creates directories correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, 'test_dir')
            nested_dir = os.path.join(test_dir, 'nested', 'dir')
            
            # Ensure directories don't exist yet
            self.assertFalse(os.path.exists(test_dir))
            self.assertFalse(os.path.exists(nested_dir))
            
            # Create the directories
            ensure_dir(test_dir)
            ensure_dir(nested_dir)
            
            # Verify directories were created
            self.assertTrue(os.path.exists(test_dir))
            self.assertTrue(os.path.exists(nested_dir))
            
            # Test that ensure_dir doesn't fail when directory already exists
            ensure_dir(test_dir)  # Should not raise an exception
    
    def test_generate_deterministic_id(self):
        """Test that generate_deterministic_id creates consistent UUIDs"""
        # Test with the same inputs produces the same UUID
        uuid1 = generate_deterministic_id('database_a', 1)
        uuid2 = generate_deterministic_id('database_a', 1)
        self.assertEqual(uuid1, uuid2)
        
        # Test that different inputs produce different UUIDs
        uuid3 = generate_deterministic_id('database_a', 2)
        self.assertNotEqual(uuid1, uuid3)
        
        uuid4 = generate_deterministic_id('database_b', 1)
        self.assertNotEqual(uuid1, uuid4)
        
        # Test that the function returns a valid UUID string
        try:
            uuid_obj = uuid.UUID(uuid1)
            self.assertEqual(str(uuid_obj), uuid1)
        except ValueError:
            self.fail("generate_deterministic_id did not return a valid UUID string")
    
    def test_hash_row(self):
        """Test that hash_row creates a hash of row values"""
        import pandas as pd
        import numpy as np
        
        # Create a sample row
        df = pd.DataFrame({
            'user_id': [1],
            'name': ['Test User'],
            'email': ['test@example.com']
        })
        
        row = df.iloc[0]
        
        # Test that the hash is consistent
        hash1 = hash_row(row)
        hash2 = hash_row(row)
        self.assertEqual(hash1, hash2)
        
        # Test that different rows produce different hashes
        df2 = pd.DataFrame({
            'user_id': [2],
            'name': ['Test User'],
            'email': ['test@example.com']
        })
        
        row2 = df2.iloc[0]
        hash3 = hash_row(row2)
        self.assertNotEqual(hash1, hash3)


if __name__ == '__main__':
    unittest.main() 