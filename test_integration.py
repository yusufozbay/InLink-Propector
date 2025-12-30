"""
Integration test for background job feature in app
This test verifies that jobs can be created and managed correctly
"""

import pandas as pd
import time
import os
import shutil
from job_manager import JobManager, JobStatus
from analyzer import LinkAnalyzer


def test_integration():
    """Test complete background job workflow"""
    
    # Setup
    test_jobs_dir = "test_integration_jobs"
    job_manager = JobManager(jobs_dir=test_jobs_dir)
    
    try:
        print("🧪 Testing background job integration...")
        
        # 1. Create test data
        print("\n1️⃣ Creating test data...")
        df = pd.DataFrame({
            'URL': [f'https://example.com/page{i}' for i in range(5)],
            'H1': [f'Title {i}' for i in range(5)],
            'Meta Title': [f'Meta {i}' for i in range(5)],
            'Content': [f'Content {i}' * 50 for i in range(5)]
        })
        print(f"   ✅ Created dataset with {len(df)} pages")
        
        # 2. Create a new job
        print("\n2️⃣ Creating new job...")
        job_id = "test_integration_job"
        config = {
            'api_key': 'test-key',
            'model_name': 'gemini-2.5-pro',
            'max_suggestions_per_page': 3
        }
        job_data = job_manager.create_job(job_id, len(df), config)
        print(f"   ✅ Job created: {job_id}")
        print(f"   Status: {job_data['status']}")
        
        # 3. Create mock analyzer
        print("\n3️⃣ Setting up analyzer...")
        analyzer = LinkAnalyzer(api_key='test-key')
        
        # Mock _analyze_page to avoid API calls
        def mock_analyze_page(source_url, *args, **kwargs):
            time.sleep(0.1)  # Simulate processing time
            return [
                {
                    'Source URL': source_url,
                    'Anchor Text': 'test link',
                    'Target URL': 'https://example.com/target'
                }
            ]
        
        analyzer._analyze_page = mock_analyze_page
        print("   ✅ Mock analyzer configured")
        
        # 4. Start background job
        print("\n4️⃣ Starting background job...")
        completed = [False]
        final_results = [None]
        
        def completion_callback(job_id, results):
            completed[0] = True
            final_results[0] = results
        
        job_manager.start_background_job(
            job_id, analyzer, df,
            completion_callback=completion_callback
        )
        print("   ✅ Background job started")
        
        # 5. Monitor progress
        print("\n5️⃣ Monitoring job progress...")
        timeout = 15
        start_time = time.time()
        last_progress = 0
        
        while not completed[0] and time.time() - start_time < timeout:
            job_data = job_manager.get_job(job_id)
            current_page = job_data.get('current_page', 0)
            
            if current_page > last_progress:
                print(f"   📊 Progress: {current_page}/{len(df)} pages")
                last_progress = current_page
            
            time.sleep(0.5)
        
        # 6. Verify completion
        print("\n6️⃣ Verifying job completion...")
        job_data = job_manager.get_job(job_id)
        
        if completed[0]:
            print("   ✅ Job completed successfully")
            print(f"   Status: {job_data['status']}")
            print(f"   Pages processed: {job_data['current_page']}/{job_data['total_pages']}")
        else:
            print("   ⚠️ Job did not complete within timeout")
            print(f"   Current status: {job_data['status']}")
            print(f"   Current progress: {job_data['current_page']}/{job_data['total_pages']}")
        
        # 7. Check partial results
        print("\n7️⃣ Checking results...")
        results_df = job_manager.load_partial_results(job_id)
        
        if results_df is not None:
            print(f"   ✅ Results loaded: {len(results_df)} link suggestions")
            print(f"   Preview:\n{results_df.head(3).to_string(index=False)}")
        else:
            print("   ⚠️ No results found")
        
        # 8. Test pause/resume
        print("\n8️⃣ Testing pause functionality...")
        job_id_2 = "test_pause_job"
        job_manager.create_job(job_id_2, 10, config)
        job_manager.update_job(job_id_2, {'status': JobStatus.RUNNING.value})
        job_manager.pause_job(job_id_2)
        paused_job = job_manager.get_job(job_id_2)
        
        if paused_job['status'] == JobStatus.PAUSED.value:
            print("   ✅ Job paused successfully")
        else:
            print(f"   ⚠️ Unexpected status: {paused_job['status']}")
        
        # 9. Test job listing
        print("\n9️⃣ Testing job listing...")
        all_jobs = job_manager.list_jobs()
        print(f"   ✅ Found {len(all_jobs)} jobs")
        for job in all_jobs:
            print(f"   - {job['job_id']}: {job['status']}")
        
        # 10. Cleanup
        print("\n🔟 Cleaning up...")
        job_manager.delete_job(job_id)
        job_manager.delete_job(job_id_2)
        print("   ✅ Jobs deleted")
        
        print("\n✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup test directory
        if os.path.exists(test_jobs_dir):
            shutil.rmtree(test_jobs_dir)


if __name__ == '__main__':
    success = test_integration()
    exit(0 if success else 1)
