"""
Test entity extraction and URL database building
"""

import unittest
from analyzer import LinkAnalyzer
import pandas as pd


class TestEntityExtraction(unittest.TestCase):
    """Test cases for entity extraction and URL database building"""
    
    def setUp(self):
        """Set up test analyzer"""
        self.analyzer = LinkAnalyzer(api_key='test-key')
    
    def test_extract_entities_from_url(self):
        """Test entity extraction from URL"""
        url = "https://example.com/seo-guide"
        h1 = ""
        meta_title = ""
        
        entities = self.analyzer._extract_entities(url, h1, meta_title)
        
        # Should extract 'seo guide' from URL
        self.assertIn('seo guide', entities)
    
    def test_extract_entities_from_h1(self):
        """Test entity extraction from H1"""
        url = "https://example.com/page"
        h1 = "Complete SEO Guide"
        meta_title = ""
        
        entities = self.analyzer._extract_entities(url, h1, meta_title)
        
        # Should extract H1
        self.assertIn('Complete SEO Guide', entities)
    
    def test_extract_entities_from_meta_title(self):
        """Test entity extraction from Meta Title"""
        url = "https://example.com/page"
        h1 = ""
        meta_title = "SEO Guide - Best Practices | Example"
        
        entities = self.analyzer._extract_entities(url, h1, meta_title)
        
        # Should extract clean title (before separator)
        self.assertIn('SEO Guide', entities)
    
    def test_extract_entities_all_sources(self):
        """Test entity extraction from all sources"""
        url = "https://example.com/seo-guide"
        h1 = "Complete SEO Guide"
        meta_title = "SEO Guide - Best Practices | Example"
        
        entities = self.analyzer._extract_entities(url, h1, meta_title)
        
        # Should have entities from all sources
        self.assertEqual(len(entities), 3)
        self.assertIn('seo guide', entities)
        self.assertIn('Complete SEO Guide', entities)
        self.assertIn('SEO Guide', entities)
    
    def test_build_url_database(self):
        """Test URL database building"""
        # Create test data
        df = pd.DataFrame({
            'URL': [
                'https://example.com/seo-guide',
                'https://example.com/content-marketing'
            ],
            'H1': [
                'Complete SEO Guide',
                'Content Marketing Strategies'
            ],
            'Meta Title': [
                'SEO Guide - Best Practices | Example',
                'Content Marketing Guide | Example'
            ],
            'Content': [
                'SEO is important...',
                'Content marketing is crucial...'
            ]
        })
        
        url_database = self.analyzer._build_url_database(df)
        
        # Should contain formatted database
        self.assertIn('COMPLETE URL DATABASE', url_database)
        self.assertIn('https://example.com/seo-guide', url_database)
        self.assertIn('Complete SEO Guide', url_database)
        self.assertIn('SEO Guide - Best Practices | Example', url_database)
        self.assertIn('https://example.com/content-marketing', url_database)
        self.assertIn('Content Marketing Strategies', url_database)
        # Should NOT include pre-extracted entities (Gemini extracts from content now)
        self.assertNotIn('Key Entities:', url_database)
    
    def test_extract_entities_handles_none(self):
        """Test entity extraction handles None values"""
        url = "https://example.com/page"
        h1 = None
        meta_title = None
        
        entities = self.analyzer._extract_entities(url, h1, meta_title)
        
        # Should still extract from URL
        self.assertEqual(len(entities), 1)
        self.assertIn('page', entities)


if __name__ == '__main__':
    unittest.main()
