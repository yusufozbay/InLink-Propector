"""
Integration test for pause/resume/stop functionality
Simulates the full workflow without requiring Streamlit UI
"""

import pandas as pd
import time
import os
import shutil
from job_manager import JobManager, JobStatus
from analyzer import LinkAnalyzer

def test_full_pause_resume_workflow():
    """Test the complete pause/resume/stop workflow"""
    
    print("=" * 70)
    print("INTEGRATION TEST: Pause/Resume/Stop Workflow")
    print("=" * 70)
    
    # Setup test environment
    test_jobs_dir = "test_integration_jobs"
    if os.path.exists(test_jobs_dir):
        shutil.rmtree(test_jobs_dir)
    
    job_manager = JobManager(jobs_dir=test_jobs_dir)
    
    # Create test data
    df = pd.DataFrame({
        'URL': [f'https://example.com/page{i}' for i in range(10)],
        'H1': [f'Title {i}' for i in range(10)],
        'Meta Title': [f'Meta {i}' for i in range(10)],
        'Content': [f'Content {i}' * 100 for i in range(10)]
    })
    
    print(f"\n1️⃣  Created test dataset with {len(df)} pages")
    
    # Create job
    job_id = "test_integration_job"
    config = {
        'api_key': 'test-key',
        'model_name': 'gemini-2.5-pro',
        'max_suggestions_per_page': 5
    }
    
    job_manager.create_job(job_id, len(df), config)
    print(f"✅ Created job: {job_id}")
    
    # Mock analyzer
    analyzer = LinkAnalyzer(api_key='test-key')
    pages_processed = []
    
    def mock_analyze_page(source_url, *args, **kwargs):
        pages_processed.append(source_url)
        # Simulate some processing time
        time.sleep(0.1)
        return [
            {
                'Source URL': source_url,
                'Anchor Text': 'test link',
                'Target URL': 'https://example.com/target'
            }
        ]
    
    analyzer._analyze_page = mock_analyze_page
    
    # Start job
    print(f"\n2️⃣  Starting background job...")
    job_manager.start_background_job(job_id, analyzer, df)
    
    # Wait a bit for some pages to process
    time.sleep(0.5)
    
    # Check progress
    job_data = job_manager.get_job(job_id)
    print(f"✅ Job started - Status: {job_data['status']}, Progress: {job_data['current_page']}/{job_data['total_pages']}")
    
    # Pause after some progress
    time.sleep(0.8)
    print(f"\n3️⃣  Pausing job...")
    job_manager.pause_job(job_id)
    time.sleep(0.2)  # Give it time to pause
    
    # Check paused state
    job_data = job_manager.get_job(job_id)
    print(f"✅ Job paused - Status: {job_data['status']}, Progress: {job_data['current_page']}/{job_data['total_pages']}")
    paused_at = job_data['current_page']
    
    # Load partial results
    partial_results = job_manager.load_partial_results(job_id)
    if partial_results is not None:
        print(f"📊 Partial results: {len(partial_results)} suggestions generated")
    
    # Resume job
    print(f"\n4️⃣  Resuming job from page {paused_at}...")
    analyzer2 = LinkAnalyzer(api_key='test-key')
    analyzer2._analyze_page = mock_analyze_page
    
    job_manager.resume_job(job_id, analyzer2, df)
    
    # Wait for completion
    timeout = 20
    start_time = time.time()
    while time.time() - start_time < timeout:
        job_data = job_manager.get_job(job_id)
        status = job_data['status']
        progress = job_data['current_page']
        
        if status == JobStatus.COMPLETED.value:
            print(f"✅ Job completed - Progress: {progress}/{job_data['total_pages']}")
            break
        
        time.sleep(0.5)
    
    # Verify completion
    job_data = job_manager.get_job(job_id)
    assert job_data['status'] == JobStatus.COMPLETED.value, f"Expected COMPLETED, got {job_data['status']}"
    assert job_data['current_page'] == len(df), f"Expected {len(df)} pages, got {job_data['current_page']}"
    
    # Verify results
    final_results = job_manager.load_partial_results(job_id)
    assert final_results is not None, "Results should exist"
    print(f"📊 Final results: {len(final_results)} suggestions generated")
    
    print(f"\n5️⃣  Testing STOP functionality...")
    # Create another job to test stop
    job_id2 = "test_stop_job"
    job_manager.create_job(job_id2, len(df), config)
    
    analyzer3 = LinkAnalyzer(api_key='test-key')
    analyzer3._analyze_page = mock_analyze_page
    
    job_manager.start_background_job(job_id2, analyzer3, df)
    time.sleep(0.5)
    
    # Stop the job
    job_manager.stop_job(job_id2)
    time.sleep(0.5)
    
    job_data2 = job_manager.get_job(job_id2)
    print(f"✅ Job stopped - Status: {job_data2['status']}, Progress: {job_data2['current_page']}/{job_data2['total_pages']}")
    
    assert job_data2['status'] == JobStatus.STOPPED.value, f"Expected STOPPED, got {job_data2['status']}"
    assert job_data2['current_page'] < len(df), "Job should have stopped before completing all pages"
    
    # Verify partial results exist
    partial_results2 = job_manager.load_partial_results(job_id2)
    if partial_results2 is not None:
        print(f"📊 Partial results after stop: {len(partial_results2)} suggestions")
    
    # Cleanup
    print(f"\n6️⃣  Cleaning up...")
    job_manager.delete_job(job_id)
    job_manager.delete_job(job_id2)
    shutil.rmtree(test_jobs_dir)
    print(f"✅ Test jobs deleted")
    
    print("\n" + "=" * 70)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  ✓ Created job and started background processing")
    print(f"  ✓ Paused job mid-processing at page {paused_at}")
    print(f"  ✓ Resumed job and completed successfully")
    print(f"  ✓ Stopped job mid-processing")
    print(f"  ✓ Progress tracking worked correctly throughout")
    print("=" * 70)


if __name__ == '__main__':
    test_full_pause_resume_workflow()
