"""
Test for pause/stop functionality in LinkAnalyzer
"""

import unittest
import pandas as pd
from analyzer import LinkAnalyzer
import time


class TestPauseStopFunctionality(unittest.TestCase):
    """Test cases for pause/stop functionality"""
    
    def test_stop_functionality(self):
        """Test that stop callback properly halts processing"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(10)],
            'H1': [f'Title {i}' for i in range(10)],
            'Meta Title': [f'Meta {i}' for i in range(10)],
            'Content': [f'Content {i}' * 100 for i in range(10)]
        })
        
        pages_processed = [0]
        stop_at = 3
        
        def status_callback():
            # Stop after processing 3 pages
            should_stop = pages_processed[0] >= stop_at
            return (False, should_stop)
        
        def progress_callback(current, total):
            pages_processed[0] = current
        
        # Mock the _analyze_page to not make actual API calls
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Run with stop callback
        result = analyzer.generate_link_suggestions(
            df,
            max_suggestions_per_page=5,
            progress_callback=progress_callback,
            status_check_callback=status_callback
        )
        
        # Should stop at page 3
        self.assertEqual(pages_processed[0], stop_at)
        print(f"✓ Stop test passed: Stopped at page {pages_processed[0]}")
    
    def test_pause_functionality(self):
        """Test that pause callback properly pauses and resumes processing"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(5)],
            'H1': [f'Title {i}' for i in range(5)],
            'Meta Title': [f'Meta {i}' for i in range(5)],
            'Content': [f'Content {i}' * 100 for i in range(5)]
        })
        
        pages_processed = [0]
        pause_state = {'paused': False, 'pause_count': 0}
        
        def status_callback():
            # Pause at page 2, then resume
            if pages_processed[0] == 2 and pause_state['pause_count'] < 1:
                pause_state['paused'] = True
                pause_state['pause_count'] += 1
                # Simulate resume after a short delay
                def resume_later():
                    time.sleep(0.1)
                    pause_state['paused'] = False
                import threading
                threading.Thread(target=resume_later).start()
            return (pause_state['paused'], False)
        
        def progress_callback(current, total):
            pages_processed[0] = current
        
        # Mock the _analyze_page to not make actual API calls
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Run with pause callback
        start_time = time.time()
        result = analyzer.generate_link_suggestions(
            df,
            max_suggestions_per_page=5,
            progress_callback=progress_callback,
            status_check_callback=status_callback
        )
        duration = time.time() - start_time
        
        # Should process all pages and pause was triggered
        self.assertEqual(pages_processed[0], 5)
        self.assertEqual(pause_state['pause_count'], 1)
        # Should take at least 0.1 seconds due to pause
        self.assertGreater(duration, 0.1)
        print(f"✓ Pause test passed: Paused {pause_state['pause_count']} time(s)")
    
    def test_progress_callback(self):
        """Test that progress callback is called correctly"""
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Create test data
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(3)],
            'H1': [f'Title {i}' for i in range(3)],
            'Meta Title': [f'Meta {i}' for i in range(3)],
            'Content': [f'Content {i}' * 100 for i in range(3)]
        })
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # Mock the _analyze_page to not make actual API calls
        def mock_analyze_page(*args, **kwargs):
            return []
        
        analyzer._analyze_page = mock_analyze_page
        
        # Run with progress callback
        result = analyzer.generate_link_suggestions(
            df,
            max_suggestions_per_page=5,
            progress_callback=progress_callback
        )
        
        # Should be called for each page
        self.assertEqual(len(progress_calls), 3)
        self.assertEqual(progress_calls[0], (1, 3))
        self.assertEqual(progress_calls[1], (2, 3))
        self.assertEqual(progress_calls[2], (3, 3))
        print(f"✓ Progress callback test passed: Called {len(progress_calls)} times")


if __name__ == '__main__':
    unittest.main()
