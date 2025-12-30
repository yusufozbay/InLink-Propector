"""
Unit tests for InLink-Prospector
"""

import unittest
from analyzer import LinkAnalyzer
import pandas as pd
import os


class TestLinkAnalyzer(unittest.TestCase):
    """Test cases for LinkAnalyzer"""
    
    def test_analyzer_initialization_with_key(self):
        """Test analyzer initialization with API key"""
        analyzer = LinkAnalyzer(api_key='test-key')
        self.assertEqual(analyzer.api_key, 'test-key')
    
    def test_analyzer_initialization_without_key(self):
        """Test analyzer raises error without API key"""
        # Clear env var if exists
        original_key = os.environ.get('GOOGLE_API_KEY')
        if 'GOOGLE_API_KEY' in os.environ:
            del os.environ['GOOGLE_API_KEY']
        
        with self.assertRaises(ValueError):
            LinkAnalyzer()
        
        # Restore original key
        if original_key:
            os.environ['GOOGLE_API_KEY'] = original_key
    
    def test_save_to_csv(self):
        """Test CSV saving functionality"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test dataframe
        df = pd.DataFrame({
            'Source URL': ['https://example.com/page1'],
            'Anchor Text': ['test link'],
            'Target URL': ['https://example.com/page2']
        })
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            analyzer.save_to_csv(df, temp_file)
            
            # Verify file exists and can be read
            loaded_df = pd.read_csv(temp_file)
            self.assertEqual(len(loaded_df), 1)
            self.assertEqual(loaded_df['Source URL'][0], 'https://example.com/page1')
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
