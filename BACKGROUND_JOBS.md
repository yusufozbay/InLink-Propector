# Background Job Processing Feature

## Overview
This document describes the background job processing feature added to InLink-Prospector, allowing analysis to continue even if the browser tab is closed.

## Key Features

### 1. Persistent Background Processing
- **Analysis runs in background threads**: Processing continues independently of the browser session
- **Job state persisted to disk**: All job metadata and progress saved to JSON files
- **Resume after tab closure**: Close your browser and come back later - your job will still be running!
- **Automatic checkpoint saving**: Partial results saved after each page is processed

### 2. Job Management
- **Multiple concurrent jobs**: Can manage multiple analysis jobs simultaneously
- **Job status tracking**: Real-time status updates (queued, running, paused, completed, failed, stopped)
- **Job recovery**: Automatically detect and recover ongoing jobs when reopening the app
- **Job history**: View all past and current jobs with their status

### 3. Enhanced Control
- **Pause/Resume**: Pause analysis at any time and resume later (even after closing the tab)
- **Stop**: Completely stop a job and download partial results
- **Delete**: Clean up completed or failed jobs
- **Progress tracking**: Real-time progress updates showing pages processed

## How It Works

### Architecture

1. **JobManager Class** (`job_manager.py`):
   - Manages job lifecycle (create, update, delete)
   - Persists job state to JSON files in `jobs/` directory
   - Runs analysis in background threads
   - Handles job recovery and resumption

2. **Job State Files**:
   - Each job has a JSON file: `jobs/{job_id}.json`
   - Contains: status, progress, configuration, timestamps, errors
   - Partial results saved to: `jobs/{job_id}_results.csv`

3. **Background Processing**:
   - Jobs run in daemon threads that persist after browser disconnection
   - Progress and results continuously saved to disk
   - App polls job status and auto-refreshes UI

### Job Lifecycle

```
QUEUED → RUNNING ⇄ PAUSED → COMPLETED
                ↓           ↓
              STOPPED     FAILED
```

## User Workflows

### Starting a New Analysis

1. Upload your website data (Step 1)
2. Go to "Generate Links" tab (Step 2)
3. Configure settings (API key, model, max suggestions)
4. Click "🤖 Start New Analysis"
5. Analysis begins in background

**You can now close the tab!** Analysis continues running.

### Resuming After Closing Tab

1. Reopen the app
2. Go to "Generate Links" tab
3. Your active job will be displayed with current progress
4. Click "▶️ Resume" to continue if paused
5. Or click "⏹️ Stop" to halt and download partial results

### Managing Jobs

In the "📋 All Analysis Jobs" section:
- **View all jobs**: See status, progress, creation time
- **Load a job**: Switch to view/control a different job
- **Delete jobs**: Clean up old or unwanted jobs

## Technical Details

### Job State Structure

```json
{
  "job_id": "job_abc123",
  "status": "running",
  "total_pages": 100,
  "current_page": 45,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:35:00",
  "config": {
    "api_key": "...",
    "model_name": "gemini-2.5-pro",
    "max_suggestions_per_page": 5
  },
  "error": null
}
```

### Resuming from Checkpoint

When resuming a job:
1. JobManager loads job state from JSON file
2. Loads existing partial results from CSV
3. Analyzer starts processing from `current_page` (skips already processed pages)
4. New results appended to existing partial results
5. Progress continues seamlessly

### Data Persistence

- **Job metadata**: `jobs/{job_id}.json`
- **Partial results**: `jobs/{job_id}_results.csv`
- **Auto-save**: After each page is processed
- **Recovery**: Automatic on app restart

## API Reference

### JobManager Methods

#### `create_job(job_id, total_pages, config)`
Create a new job with initial state.

#### `get_job(job_id)`
Retrieve job metadata.

#### `update_job(job_id, updates)`
Update job fields.

#### `start_background_job(job_id, analyzer, df, ...)`
Start job in background thread.

#### `pause_job(job_id)`
Pause a running job.

#### `resume_job(job_id, analyzer, df, ...)`
Resume a paused job.

#### `stop_job(job_id)`
Stop a running or paused job.

#### `delete_job(job_id)`
Delete job and its data.

#### `save_partial_results(job_id, results_df)`
Save partial results to CSV.

#### `load_partial_results(job_id)`
Load partial results from CSV.

## Performance Considerations

### Memory
- Job state files are small (< 1KB each)
- Partial results stored on disk, not in memory
- Minimal memory overhead for background threads

### Disk Space
- Each job: ~1KB JSON + variable CSV size
- Old jobs can be manually deleted
- Implement `cleanup_old_jobs(days)` for automatic cleanup

### Concurrency
- Background threads run independently
- Thread-safe file operations
- No race conditions in job state updates

## Differences from Previous Implementation

### Before (Session-Based)
- ❌ Progress lost when tab closed
- ❌ Must stay on page during processing
- ❌ No job history
- ❌ Single session only

### After (Background Jobs)
- ✅ Progress persisted across sessions
- ✅ Can close tab and come back later
- ✅ Full job history and management
- ✅ Multiple jobs supported
- ✅ Automatic recovery on restart

## Testing

Tests in `test_job_manager.py`:
- Job creation, retrieval, update, deletion
- Background job execution
- Pause/resume functionality
- Checkpoint recovery
- Partial results persistence

Run tests:
```bash
python -m unittest test_job_manager.TestJobManager -v
```

## Future Enhancements

Potential improvements:
- **Job scheduling**: Schedule jobs to run at specific times
- **Email notifications**: Notify when job completes
- **Progress webhooks**: Send progress updates to external systems
- **Job priorities**: Prioritize certain jobs over others
- **Resource limits**: Limit concurrent jobs to manage API costs
- **Job templates**: Save and reuse common job configurations

## Troubleshooting

### Job not resuming after restart
- Check that `jobs/` directory exists and is writable
- Verify job JSON file exists in `jobs/` directory
- Check app logs for errors

### Partial results not saving
- Ensure `jobs/` directory has write permissions
- Check disk space availability
- Verify CSV file is not locked by another process

### Job stuck in RUNNING state
- Job may have crashed - check for error in job JSON
- Stop the job and restart it
- Delete and recreate the job if necessary

## Best Practices

1. **Monitor job progress**: Check periodically to ensure jobs are progressing
2. **Clean up old jobs**: Delete completed jobs to save disk space
3. **Use meaningful job IDs**: Jobs auto-generate IDs, but you can track them
4. **Download results promptly**: Completed jobs can be deleted anytime
5. **Check for errors**: Review failed jobs to understand what went wrong

---

Built with ❤️ to make internal link analysis truly background-ready!
