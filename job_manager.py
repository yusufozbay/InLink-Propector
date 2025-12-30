"""
Job Manager Module for InLink-Prospector
Handles background job processing with state persistence
"""

import json
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import pandas as pd


class JobStatus(Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class JobManager:
    """Manages background jobs with persistence"""
    
    def __init__(self, jobs_dir: str = "jobs"):
        """
        Initialize job manager
        
        Args:
            jobs_dir: Directory to store job state files
        """
        self.jobs_dir = jobs_dir
        os.makedirs(jobs_dir, exist_ok=True)
        self.active_threads = {}
    
    def create_job(self, job_id: str, total_pages: int, config: Dict) -> Dict:
        """
        Create a new job
        
        Args:
            job_id: Unique job identifier
            total_pages: Total number of pages to process
            config: Job configuration (API key, model, max_suggestions, etc.)
            
        Returns:
            Job metadata dictionary
        """
        job_data = {
            'job_id': job_id,
            'status': JobStatus.QUEUED.value,
            'total_pages': total_pages,
            'current_page': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'config': config,
            'partial_results': [],
            'error': None
        }
        
        self._save_job(job_id, job_data)
        return job_data
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job metadata
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job metadata or None if not found
        """
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        if not os.path.exists(job_file):
            return None
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    def update_job(self, job_id: str, updates: Dict):
        """
        Update job metadata
        
        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update
        """
        job_data = self.get_job(job_id)
        if job_data:
            job_data.update(updates)
            job_data['updated_at'] = datetime.now().isoformat()
            self._save_job(job_id, job_data)
    
    def list_jobs(self) -> List[Dict]:
        """
        List all jobs
        
        Returns:
            List of job metadata dictionaries
        """
        jobs = []
        for filename in os.listdir(self.jobs_dir):
            if filename.endswith('.json'):
                job_id = filename[:-5]
                job_data = self.get_job(job_id)
                if job_data:
                    jobs.append(job_data)
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jobs
    
    def delete_job(self, job_id: str):
        """
        Delete a job and its data
        
        Args:
            job_id: Job identifier
        """
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        results_file = os.path.join(self.jobs_dir, f"{job_id}_results.csv")
        
        if os.path.exists(job_file):
            os.remove(job_file)
        if os.path.exists(results_file):
            os.remove(results_file)
    
    def save_partial_results(self, job_id: str, results_df: pd.DataFrame):
        """
        Save partial results to CSV
        
        Args:
            job_id: Job identifier
            results_df: DataFrame with partial results
        """
        results_file = os.path.join(self.jobs_dir, f"{job_id}_results.csv")
        results_df.to_csv(results_file, index=False)
    
    def load_partial_results(self, job_id: str) -> Optional[pd.DataFrame]:
        """
        Load partial results from CSV
        
        Args:
            job_id: Job identifier
            
        Returns:
            DataFrame with partial results or None
        """
        results_file = os.path.join(self.jobs_dir, f"{job_id}_results.csv")
        if os.path.exists(results_file):
            return pd.read_csv(results_file)
        return None
    
    def start_background_job(self, job_id: str, analyzer, df: pd.DataFrame, 
                           progress_callback: Optional[Callable] = None,
                           completion_callback: Optional[Callable] = None):
        """
        Start a job in background thread
        
        Args:
            job_id: Job identifier
            analyzer: LinkAnalyzer instance
            df: DataFrame with pages to analyze
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback when job completes
        """
        def run_job():
            try:
                job_data = self.get_job(job_id)
                if not job_data:
                    return
                
                # Update status to running
                self.update_job(job_id, {'status': JobStatus.RUNNING.value})
                
                # Get configuration
                config = job_data['config']
                max_suggestions = config.get('max_suggestions_per_page', 5)
                start_page = job_data.get('current_page', 0)
                
                # Load existing partial results if any
                all_suggestions = []
                existing_results = self.load_partial_results(job_id)
                if existing_results is not None and len(existing_results) > 0:
                    all_suggestions = existing_results.to_dict('records')
                
                # Status check callback
                def check_status():
                    current_job = self.get_job(job_id)
                    if not current_job:
                        return (False, True)  # Stop if job deleted
                    
                    status = current_job['status']
                    should_pause = (status == JobStatus.PAUSED.value)
                    should_stop = (status == JobStatus.STOPPED.value)
                    return (should_pause, should_stop)
                
                # Progress callback wrapper
                def update_progress(current, total):
                    # Update job state
                    self.update_job(job_id, {
                        'current_page': current,
                        'status': JobStatus.RUNNING.value
                    })
                    
                    # Call external progress callback if provided
                    if progress_callback:
                        progress_callback(current, total)
                
                # Wrap analyze to collect results
                original_analyze = analyzer._analyze_page
                
                def wrapped_analyze(*args, **kwargs):
                    result = original_analyze(*args, **kwargs)
                    all_suggestions.extend(result)
                    
                    # Save partial results periodically (every page)
                    if len(all_suggestions) > 0:
                        results_df = pd.DataFrame(all_suggestions)
                        self.save_partial_results(job_id, results_df)
                    
                    return result
                
                analyzer._analyze_page = wrapped_analyze
                
                # Process only remaining pages
                df_to_process = df.iloc[start_page:] if start_page > 0 else df
                
                # Generate suggestions
                suggestions_df = analyzer.generate_link_suggestions(
                    df_to_process,
                    max_suggestions_per_page=max_suggestions,
                    progress_callback=update_progress,
                    status_check_callback=check_status
                )
                
                # Check final status
                final_job = self.get_job(job_id)
                if final_job and final_job['status'] == JobStatus.STOPPED.value:
                    # Job was stopped
                    self.update_job(job_id, {
                        'status': JobStatus.STOPPED.value,
                        'current_page': final_job.get('current_page', 0)
                    })
                else:
                    # Job completed successfully
                    self.save_partial_results(job_id, suggestions_df)
                    self.update_job(job_id, {
                        'status': JobStatus.COMPLETED.value,
                        'current_page': len(df)
                    })
                
                # Call completion callback if provided
                if completion_callback:
                    completion_callback(job_id, suggestions_df)
                    
            except Exception as e:
                # Job failed
                self.update_job(job_id, {
                    'status': JobStatus.FAILED.value,
                    'error': str(e)
                })
                
                if completion_callback:
                    completion_callback(job_id, None)
        
        # Start thread
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        self.active_threads[job_id] = thread
    
    def pause_job(self, job_id: str):
        """
        Pause a running job
        
        Args:
            job_id: Job identifier
        """
        job_data = self.get_job(job_id)
        if job_data and job_data['status'] == JobStatus.RUNNING.value:
            self.update_job(job_id, {'status': JobStatus.PAUSED.value})
    
    def resume_job(self, job_id: str, analyzer, df: pd.DataFrame,
                   progress_callback: Optional[Callable] = None,
                   completion_callback: Optional[Callable] = None):
        """
        Resume a paused job
        
        Args:
            job_id: Job identifier
            analyzer: LinkAnalyzer instance
            df: DataFrame with pages to analyze
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback when job completes
        """
        job_data = self.get_job(job_id)
        if job_data and job_data['status'] == JobStatus.PAUSED.value:
            # Update status to running
            self.update_job(job_id, {'status': JobStatus.RUNNING.value})
            
            # Restart background processing
            self.start_background_job(job_id, analyzer, df, progress_callback, completion_callback)
    
    def stop_job(self, job_id: str):
        """
        Stop a running or paused job
        
        Args:
            job_id: Job identifier
        """
        job_data = self.get_job(job_id)
        if job_data and job_data['status'] in [JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            self.update_job(job_id, {'status': JobStatus.STOPPED.value})
    
    def cleanup_old_jobs(self, days: int = 7):
        """
        Clean up jobs older than specified days
        
        Args:
            days: Number of days to keep jobs
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for job in self.list_jobs():
            created_at = datetime.fromisoformat(job['created_at']).timestamp()
            if created_at < cutoff_time:
                self.delete_job(job['job_id'])
    
    def _save_job(self, job_id: str, job_data: Dict):
        """
        Save job metadata to file
        
        Args:
            job_id: Job identifier
            job_data: Job metadata dictionary
        """
        job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
