"""
Test to verify resume functionality with correct progress tracking
"""

import unittest
import pandas as pd
from analyzer import LinkAnalyzer


class TestResumeProgress(unittest.TestCase):
    """Test cases for resume functionality with correct progress tracking"""
    
    def test_resume_with_correct_progress(self):
        """Test that resuming from checkpoint reports correct progress"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data with 10 pages
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(10)],
            'H1': [f'Title {i}' for i in range(10)],
            'Meta Title': [f'Meta {i}' for i in range(10)],
            'Content': [f'Content {i}' * 100 for i in range(10)]
        })
        
        # Simulate resuming from page 5 (pages 0-4 already processed)
        df_to_process = df.iloc[5:]  # Process pages 5-9
        start_offset = 5  # We've already processed 5 pages
        total_pages_original = len(df)  # Total is 10
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # Mock the _analyze_page to not make actual API calls
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Run analysis on remaining pages
        result = analyzer.generate_link_suggestions(
            df_to_process,
            max_suggestions_per_page=5,
            progress_callback=progress_callback,
            start_offset=start_offset,
            total_pages=total_pages_original
        )
        
        # Verify progress tracking
        expected_progress = [(6, 10), (7, 10), (8, 10), (9, 10), (10, 10)]
        self.assertEqual(progress_calls, expected_progress)
        print(f"✓ Resume progress test passed: Progress correctly shows 6/10 to 10/10")
    
    def test_fresh_start_progress(self):
        """Test that fresh start (not resuming) still works correctly"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data with 5 pages
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(5)],
            'H1': [f'Title {i}' for i in range(5)],
            'Meta Title': [f'Meta {i}' for i in range(5)],
            'Content': [f'Content {i}' * 100 for i in range(5)]
        })
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # Mock the _analyze_page
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Run analysis from start (no offset or total_pages specified)
        result = analyzer.generate_link_suggestions(
            df,
            max_suggestions_per_page=5,
            progress_callback=progress_callback
        )
        
        # Verify progress tracking starts from 1
        expected_progress = [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
        self.assertEqual(progress_calls, expected_progress)
        print(f"✓ Fresh start progress test passed: Progress correctly shows 1/5 to 5/5")
    
    def test_resume_from_midpoint(self):
        """Test resuming from various checkpoints"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data with 20 pages
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(20)],
            'H1': [f'Title {i}' for i in range(20)],
            'Meta Title': [f'Meta {i}' for i in range(20)],
            'Content': [f'Content {i}' * 100 for i in range(20)]
        })
        
        # Mock the _analyze_page
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Test resume from page 12
        df_to_process = df.iloc[12:]
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        result = analyzer.generate_link_suggestions(
            df_to_process,
            max_suggestions_per_page=5,
            progress_callback=progress_callback,
            start_offset=12,
            total_pages=20
        )
        
        # Verify first and last progress calls
        self.assertEqual(progress_calls[0], (13, 20))  # First page after 12
        self.assertEqual(progress_calls[-1], (20, 20))  # Last page
        self.assertEqual(len(progress_calls), 8)  # Pages 12-19 (8 pages)
        print(f"✓ Resume from midpoint test passed: Progress correctly shows 13/20 to 20/20")


if __name__ == '__main__':
    unittest.main()
