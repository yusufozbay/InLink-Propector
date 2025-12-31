"""
Test for race condition fix in job manager
"""

import unittest
import os
import shutil
import threading
import time
from job_manager import JobManager, JobStatus


class TestRaceCondition(unittest.TestCase):
    """Test cases for race condition handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_jobs_dir = "test_race_jobs"
        self.job_manager = JobManager(jobs_dir=self.test_jobs_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_jobs_dir):
            shutil.rmtree(self.test_jobs_dir)
    
    def test_concurrent_read_write(self):
        """Test that concurrent reads and writes don't cause JSONDecodeError"""
        job_id = "test_concurrent_job"
        config = {
            'api_key': 'test-key',
            'model_name': 'gemini-2.5-pro',
            'max_suggestions_per_page': 5
        }
        
        # Create initial job
        self.job_manager.create_job(job_id, 100, config)
        
        # Track errors
        errors = []
        successful_reads = [0]
        
        def reader_thread():
            """Continuously read job data"""
            for _ in range(50):
                try:
                    job_data = self.job_manager.get_job(job_id)
                    if job_data is not None:
                        successful_reads[0] += 1
                        # Verify job_id is present (basic validity check)
                        assert 'job_id' in job_data
                except Exception as e:
                    errors.append(f"Reader error: {e}")
                time.sleep(0.001)  # Small delay
        
        def writer_thread():
            """Continuously update job data"""
            for i in range(50):
                try:
                    self.job_manager.update_job(job_id, {
                        'status': JobStatus.RUNNING.value,
                        'current_page': i
                    })
                except Exception as e:
                    errors.append(f"Writer error: {e}")
                time.sleep(0.001)  # Small delay
        
        # Start multiple reader and writer threads
        threads = []
        for _ in range(3):
            t = threading.Thread(target=reader_thread)
            threads.append(t)
            t.start()
        
        for _ in range(2):
            t = threading.Thread(target=writer_thread)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify no errors occurred
        if errors:
            self.fail(f"Errors occurred during concurrent access: {errors}")
        
        # Verify we had successful reads
        self.assertGreater(successful_reads[0], 0, "Should have some successful reads")
        
        # Verify final job state is valid
        final_job = self.job_manager.get_job(job_id)
        self.assertIsNotNone(final_job)
        self.assertEqual(final_job['job_id'], job_id)
        print(f"✓ Concurrent read/write test passed with {successful_reads[0]} successful reads")
    
    def test_empty_file_handling(self):
        """Test that empty or corrupted JSON files are handled gracefully"""
        job_id = "test_corrupted_job"
        job_file = os.path.join(self.test_jobs_dir, f"{job_id}.json")
        
        # Create an empty file
        with open(job_file, 'w') as f:
            f.write('')
        
        # Should return None instead of raising JSONDecodeError
        job_data = self.job_manager.get_job(job_id)
        self.assertIsNone(job_data)
        print("✓ Empty file handling test passed")
    
    def test_corrupted_json_handling(self):
        """Test that corrupted JSON files are handled gracefully"""
        job_id = "test_invalid_json"
        job_file = os.path.join(self.test_jobs_dir, f"{job_id}.json")
        
        # Create a file with invalid JSON
        with open(job_file, 'w') as f:
            f.write('{"incomplete": ')
        
        # Should return None instead of raising JSONDecodeError
        job_data = self.job_manager.get_job(job_id)
        self.assertIsNone(job_data)
        print("✓ Corrupted JSON handling test passed")
    
    def test_atomic_write(self):
        """Test that atomic write ensures readers always see complete JSON"""
        job_id = "test_atomic_write"
        config = {'api_key': 'test-key'}
        
        # Create initial job
        self.job_manager.create_job(job_id, 10, config)
        
        read_errors = []
        
        def continuous_reader():
            """Read job data continuously"""
            for _ in range(100):
                job_data = self.job_manager.get_job(job_id)
                if job_data is not None:
                    # If we get data, it should be valid JSON with required fields
                    if 'job_id' not in job_data:
                        read_errors.append("Invalid job data: missing job_id")
                time.sleep(0.0001)
        
        # Start reader thread
        reader = threading.Thread(target=continuous_reader)
        reader.start()
        
        # Perform many writes
        for i in range(50):
            self.job_manager.update_job(job_id, {
                'current_page': i,
                'status': JobStatus.RUNNING.value
            })
            time.sleep(0.001)
        
        # Wait for reader to finish
        reader.join()
        
        # Verify no read errors
        if read_errors:
            self.fail(f"Reader saw invalid data: {read_errors}")
        
        print("✓ Atomic write test passed")


if __name__ == '__main__':
    unittest.main()
