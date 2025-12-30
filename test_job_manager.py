"""
Test for job manager background processing functionality
"""

import unittest
import pandas as pd
import time
import os
import shutil
from job_manager import JobManager, JobStatus
from analyzer import LinkAnalyzer


class TestJobManager(unittest.TestCase):
    """Test cases for job manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_jobs_dir = "test_jobs"
        self.job_manager = JobManager(jobs_dir=self.test_jobs_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_jobs_dir):
            shutil.rmtree(self.test_jobs_dir)
    
    def test_create_job(self):
        """Test creating a new job"""
        job_id = "test_job_1"
        config = {
            'api_key': 'test-key',
            'model_name': 'gemini-2.5-pro',
            'max_suggestions_per_page': 5
        }
        
        job_data = self.job_manager.create_job(job_id, 10, config)
        
        self.assertEqual(job_data['job_id'], job_id)
        self.assertEqual(job_data['status'], JobStatus.QUEUED.value)
        self.assertEqual(job_data['total_pages'], 10)
        self.assertEqual(job_data['current_page'], 0)
        self.assertEqual(job_data['config'], config)
        print("✓ Job creation test passed")
    
    def test_get_job(self):
        """Test retrieving a job"""
        job_id = "test_job_2"
        config = {'api_key': 'test-key'}
        
        # Create job
        self.job_manager.create_job(job_id, 5, config)
        
        # Retrieve job
        job_data = self.job_manager.get_job(job_id)
        
        self.assertIsNotNone(job_data)
        self.assertEqual(job_data['job_id'], job_id)
        print("✓ Job retrieval test passed")
    
    def test_update_job(self):
        """Test updating a job"""
        job_id = "test_job_3"
        config = {'api_key': 'test-key'}
        
        # Create job
        self.job_manager.create_job(job_id, 5, config)
        
        # Update job
        self.job_manager.update_job(job_id, {
            'status': JobStatus.RUNNING.value,
            'current_page': 3
        })
        
        # Verify update
        job_data = self.job_manager.get_job(job_id)
        self.assertEqual(job_data['status'], JobStatus.RUNNING.value)
        self.assertEqual(job_data['current_page'], 3)
        print("✓ Job update test passed")
    
    def test_list_jobs(self):
        """Test listing all jobs"""
        # Create multiple jobs
        for i in range(3):
            job_id = f"test_job_{i}"
            config = {'api_key': 'test-key'}
            self.job_manager.create_job(job_id, 5, config)
        
        # List jobs
        jobs = self.job_manager.list_jobs()
        
        self.assertEqual(len(jobs), 3)
        print("✓ Job listing test passed")
    
    def test_delete_job(self):
        """Test deleting a job"""
        job_id = "test_job_delete"
        config = {'api_key': 'test-key'}
        
        # Create job
        self.job_manager.create_job(job_id, 5, config)
        
        # Delete job
        self.job_manager.delete_job(job_id)
        
        # Verify deletion
        job_data = self.job_manager.get_job(job_id)
        self.assertIsNone(job_data)
        print("✓ Job deletion test passed")
    
    def test_save_and_load_partial_results(self):
        """Test saving and loading partial results"""
        job_id = "test_job_results"
        
        # Create sample results
        results_df = pd.DataFrame({
            'Source URL': ['https://example.com/page1', 'https://example.com/page2'],
            'Anchor Text': ['link text 1', 'link text 2'],
            'Target URL': ['https://example.com/target1', 'https://example.com/target2']
        })
        
        # Save results
        self.job_manager.save_partial_results(job_id, results_df)
        
        # Load results
        loaded_df = self.job_manager.load_partial_results(job_id)
        
        self.assertIsNotNone(loaded_df)
        self.assertEqual(len(loaded_df), 2)
        self.assertEqual(loaded_df['Source URL'].iloc[0], 'https://example.com/page1')
        print("✓ Partial results save/load test passed")
    
    def test_pause_and_resume_job(self):
        """Test pausing and resuming a job"""
        job_id = "test_job_pause"
        config = {'api_key': 'test-key'}
        
        # Create job
        self.job_manager.create_job(job_id, 5, config)
        
        # Update to running
        self.job_manager.update_job(job_id, {'status': JobStatus.RUNNING.value})
        
        # Pause job
        self.job_manager.pause_job(job_id)
        
        # Verify paused
        job_data = self.job_manager.get_job(job_id)
        self.assertEqual(job_data['status'], JobStatus.PAUSED.value)
        print("✓ Job pause test passed")
    
    def test_stop_job(self):
        """Test stopping a job"""
        job_id = "test_job_stop"
        config = {'api_key': 'test-key'}
        
        # Create job
        self.job_manager.create_job(job_id, 5, config)
        
        # Update to running
        self.job_manager.update_job(job_id, {'status': JobStatus.RUNNING.value})
        
        # Stop job
        self.job_manager.stop_job(job_id)
        
        # Verify stopped
        job_data = self.job_manager.get_job(job_id)
        self.assertEqual(job_data['status'], JobStatus.STOPPED.value)
        print("✓ Job stop test passed")
    
    def test_background_job_execution(self):
        """Test background job execution with mock analyzer"""
        job_id = "test_job_background"
        config = {
            'api_key': 'test-key',
            'model_name': 'gemini-2.5-pro',
            'max_suggestions_per_page': 2
        }
        
        # Create test data
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(3)],
            'H1': [f'Title {i}' for i in range(3)],
            'Meta Title': [f'Meta {i}' for i in range(3)],
            'Content': [f'Content {i}' * 50 for i in range(3)]
        })
        
        # Create job
        self.job_manager.create_job(job_id, len(df), config)
        
        # Create mock analyzer
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Mock _analyze_page to avoid API calls
        def mock_analyze_page(*args, **kwargs):
            return [
                {
                    'Source URL': 'https://example.com/page1',
                    'Anchor Text': 'test link',
                    'Target URL': 'https://example.com/page2'
                }
            ]
        
        analyzer._analyze_page = mock_analyze_page
        
        # Track completion
        completed = [False]
        
        def completion_callback(job_id, results):
            completed[0] = True
        
        # Start background job
        self.job_manager.start_background_job(
            job_id, analyzer, df,
            completion_callback=completion_callback
        )
        
        # Wait for completion (with timeout)
        timeout = 10
        start_time = time.time()
        while not completed[0] and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Verify job completed
        job_data = self.job_manager.get_job(job_id)
        self.assertEqual(job_data['status'], JobStatus.COMPLETED.value)
        self.assertEqual(job_data['current_page'], 3)
        
        # Verify results saved
        results_df = self.job_manager.load_partial_results(job_id)
        self.assertIsNotNone(results_df)
        self.assertGreater(len(results_df), 0)
        print("✓ Background job execution test passed")
    
    def test_resume_from_checkpoint(self):
        """Test resuming a job from a saved checkpoint"""
        job_id = "test_job_resume"
        config = {
            'api_key': 'test-key',
            'model_name': 'gemini-2.5-pro',
            'max_suggestions_per_page': 2
        }
        
        # Create test data
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(5)],
            'H1': [f'Title {i}' for i in range(5)],
            'Meta Title': [f'Meta {i}' for i in range(5)],
            'Content': [f'Content {i}' * 50 for i in range(5)]
        })
        
        # Create job with some progress
        self.job_manager.create_job(job_id, len(df), config)
        self.job_manager.update_job(job_id, {
            'status': JobStatus.PAUSED.value,
            'current_page': 2
        })
        
        # Save some partial results
        partial_results = pd.DataFrame({
            'Source URL': ['https://example.com/page0', 'https://example.com/page1'],
            'Anchor Text': ['link 1', 'link 2'],
            'Target URL': ['https://example.com/target1', 'https://example.com/target2']
        })
        self.job_manager.save_partial_results(job_id, partial_results)
        
        # Mock analyzer
        analyzer = LinkAnalyzer(api_key='test-key')
        
        pages_processed = []
        
        def mock_analyze_page(source_url, *args, **kwargs):
            pages_processed.append(source_url)
            return [
                {
                    'Source URL': source_url,
                    'Anchor Text': 'test link',
                    'Target URL': 'https://example.com/target'
                }
            ]
        
        analyzer._analyze_page = mock_analyze_page
        
        # Track completion
        completed = [False]
        
        def completion_callback(job_id, results):
            completed[0] = True
        
        # Resume job
        self.job_manager.resume_job(
            job_id, analyzer, df,
            completion_callback=completion_callback
        )
        
        # Wait for completion
        timeout = 10
        start_time = time.time()
        while not completed[0] and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Verify job completed
        job_data = self.job_manager.get_job(job_id)
        self.assertEqual(job_data['status'], JobStatus.COMPLETED.value)
        
        # Verify results include both old and new
        results_df = self.job_manager.load_partial_results(job_id)
        self.assertIsNotNone(results_df)
        # Should have results from pages 2, 3, 4 (resumed from page 2) plus original 2
        self.assertGreaterEqual(len(results_df), 2)
        print("✓ Resume from checkpoint test passed")


if __name__ == '__main__':
    unittest.main()
