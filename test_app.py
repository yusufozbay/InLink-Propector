"""
Unit tests for InLink-Prospector
"""

import unittest
from crawler import WebCrawler
from analyzer import LinkAnalyzer
import pandas as pd
import os


class TestWebCrawler(unittest.TestCase):
    """Test cases for WebCrawler"""
    
    def test_crawler_initialization(self):
        """Test crawler can be initialized"""
        crawler = WebCrawler('https://example.com', max_pages=100)
        self.assertEqual(crawler.base_url, 'https://example.com')
        self.assertEqual(crawler.max_pages, 100)
        self.assertEqual(crawler.domain, 'example.com')
    
    def test_is_valid_url(self):
        """Test URL validation"""
        crawler = WebCrawler('https://example.com')
        
        # Valid URL from same domain
        self.assertTrue(crawler.is_valid_url('https://example.com/page'))
        
        # Invalid - different domain
        self.assertFalse(crawler.is_valid_url('https://other.com/page'))
        
        # Invalid - malformed
        self.assertFalse(crawler.is_valid_url('not-a-url'))
    
    def test_clean_text(self):
        """Test text cleaning"""
        crawler = WebCrawler('https://example.com')
        
        # Test whitespace removal
        self.assertEqual(crawler.clean_text('  Hello   World  '), 'Hello World')
        
        # Test empty string
        self.assertEqual(crawler.clean_text(''), '')
        
        # Test None
        self.assertEqual(crawler.clean_text(None), '')


class TestLinkAnalyzer(unittest.TestCase):
    """Test cases for LinkAnalyzer"""
    
    def test_analyzer_initialization_with_key(self):
        """Test analyzer initialization with API key"""
        analyzer = LinkAnalyzer(api_key='test-key')
        self.assertEqual(analyzer.api_key, 'test-key')
    
    def test_analyzer_initialization_without_key(self):
        """Test analyzer raises error without API key"""
        # Clear env var if exists
        original_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        with self.assertRaises(ValueError):
            LinkAnalyzer()
        
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
    
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


class TestCrawlerCSV(unittest.TestCase):
    """Test CSV functionality"""
    
    def test_save_to_csv(self):
        """Test crawler CSV export"""
        crawler = WebCrawler('https://example.com')
        
        # Create test dataframe
        df = pd.DataFrame({
            'URL': ['https://example.com/page1'],
            'H1': ['Test Page'],
            'Meta Title': ['Test | Example'],
            'Content (First 500 chars)': ['This is test content...']
        })
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            crawler.save_to_csv(df, temp_file)
            
            # Verify file exists and can be read
            loaded_df = pd.read_csv(temp_file)
            self.assertEqual(len(loaded_df), 1)
            self.assertEqual(loaded_df['URL'][0], 'https://example.com/page1')
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
