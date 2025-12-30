"""
InLink-Prospector - Internal Linking Suggestion Tool
A Streamlit app for generating internal link suggestions using Google Gemini
"""

import streamlit as st
import pandas as pd
from analyzer import LinkAnalyzer
from job_manager import JobManager, JobStatus
import os
from dotenv import load_dotenv
import traceback
import uuid
import time

# Load environment variables
load_dotenv()

# Initialize job manager
job_manager = JobManager()

# Page configuration
st.set_page_config(
    page_title="InLink-Prospector",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🔗 InLink-Prospector</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Expand Internal Links Site-Wide with AI</div>', unsafe_allow_html=True)

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'link_suggestions' not in st.session_state:
    st.session_state.link_suggestions = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'partial_results' not in st.session_state:
    st.session_state.partial_results = None

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# Google API Key input
api_key = st.sidebar.text_input(
    "Google API Key",
    type="password",
    value=os.getenv('GOOGLE_API_KEY', ''),
    help="Enter your Google API key for Gemini"
)

# Model selection
model_choice = st.sidebar.selectbox(
    "Gemini Model",
    ["gemini-2.5-pro", "gemini-3.0-pro-preview"],
    help="Select the Gemini model to use"
)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "🤖 Generate Links", "📈 Results"])

# Tab 1: Upload Data
with tab1:
    st.header("Step 1: Upload Your Website Data")
    
    st.markdown("""
    <div class="info-box">
    <b>Required CSV Format:</b><br>
    Your CSV file must contain the following columns:
    <ul>
        <li><b>URL</b> - URL Address of the page</li>
        <li><b>H1</b> - H1 Heading</li>
        <li><b>Meta Title</b> - Meta Title tag</li>
        <li><b>Content</b> - First 500 words of main content</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload CSV
    uploaded_file = st.file_uploader(
        "Upload CSV file with your website data",
        type=['csv'],
        help="CSV must have columns: URL, H1, Meta Title, Content"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_columns = ['URL', 'H1', 'Meta Title', 'Content']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Please ensure your CSV has columns: URL, H1, Meta Title, Content")
            else:
                st.session_state.uploaded_data = df
                st.session_state.data_loaded = True
                st.success(f"✅ Loaded {len(df)} pages from CSV")
                
                # Show preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Download button for reference
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Current Data",
                    data=csv,
                    file_name="uploaded_data.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
    
    # Show sample format
    st.subheader("Sample CSV Format")
    sample_df = pd.DataFrame({
        'URL': ['https://example.com/page1', 'https://example.com/page2'],
        'H1': ['Complete SEO Guide', 'Content Marketing'],
        'Meta Title': ['SEO Guide - Best Practices', 'Content Marketing Guide'],
        'Content': [
            'Search Engine Optimization (SEO) is crucial for online visibility...',
            'Content marketing is the art of creating valuable content...'
        ]
    })
    st.dataframe(sample_df, use_container_width=True)

# Tab 2: Generate Link Suggestions
with tab2:
    st.header("Step 2: Generate Internal Link Suggestions")
    
    st.markdown("""
    <div class="info-box">
    <b>What this does:</b><br>
    Uses Google Gemini AI to analyze your content and suggest relevant internal links with:
    <ul>
        <li>Source URL (where to add the link)</li>
        <li>Anchor Text (exact match or semantically related)</li>
        <li>Target URL (where the link should point to)</li>
    </ul>
    <br>
    <b>🆕 Background Processing:</b> Analysis continues in background even if you close this tab!
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload your website data first (Step 1)")
    else:
        st.success(f"✅ Ready to analyze {len(st.session_state.uploaded_data)} pages")
        
        suggestions_per_page = st.slider(
            "Max suggestions per page",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum number of link suggestions to generate for each page"
        )
        
        # Check for existing/active jobs
        current_job = None
        if st.session_state.current_job_id:
            current_job = job_manager.get_job(st.session_state.current_job_id)
        
        # Auto-refresh for active jobs
        if current_job and current_job['status'] in [JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            time.sleep(1)
            st.rerun()
        
        # Control buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Start new job button
            if not current_job or current_job['status'] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.STOPPED.value]:
                if st.button("🤖 Start New Analysis", type="primary"):
                    if not api_key:
                        st.error("⚠️ Please enter your Google API Key in the sidebar")
                    else:
                        # Create new job
                        job_id = f"job_{uuid.uuid4().hex[:8]}"
                        config = {
                            'api_key': api_key,
                            'model_name': model_choice,
                            'max_suggestions_per_page': suggestions_per_page
                        }
                        job_manager.create_job(job_id, len(st.session_state.uploaded_data), config)
                        st.session_state.current_job_id = job_id
                        
                        # Start background job
                        analyzer = LinkAnalyzer(api_key=api_key, model_name=model_choice)
                        job_manager.start_background_job(job_id, analyzer, st.session_state.uploaded_data)
                        
                        st.rerun()
        
        with col2:
            # Pause/Resume button
            if current_job and current_job['status'] == JobStatus.RUNNING.value:
                if st.button("⏸️ Pause"):
                    job_manager.pause_job(st.session_state.current_job_id)
                    st.rerun()
            elif current_job and current_job['status'] == JobStatus.PAUSED.value:
                if st.button("▶️ Resume"):
                    analyzer = LinkAnalyzer(api_key=api_key, model_name=model_choice)
                    job_manager.resume_job(st.session_state.current_job_id, analyzer, st.session_state.uploaded_data)
                    st.rerun()
        
        with col3:
            # Stop button
            if current_job and current_job['status'] in [JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
                if st.button("⏹️ Stop"):
                    job_manager.stop_job(st.session_state.current_job_id)
                    st.rerun()
        
        with col4:
            # Delete job button
            if current_job and current_job['status'] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.STOPPED.value]:
                if st.button("🗑️ Delete"):
                    job_manager.delete_job(st.session_state.current_job_id)
                    st.session_state.current_job_id = None
                    st.session_state.partial_results = None
                    st.rerun()
        
        # Show job status
        if current_job:
            status = current_job['status']
            current_page = current_job.get('current_page', 0)
            total_pages = current_job['total_pages']
            
            # Status message
            if status == JobStatus.RUNNING.value:
                st.info(f"🔄 Analysis in progress... ({current_page}/{total_pages} pages processed)")
                # Show progress bar
                progress = current_page / max(1, total_pages)
                st.progress(progress)
            elif status == JobStatus.PAUSED.value:
                st.warning(f"⏸️ Analysis paused at page {current_page}/{total_pages}. Click 'Resume' to continue or close this tab - your progress is saved!")
                st.progress(current_page / max(1, total_pages))
            elif status == JobStatus.STOPPED.value:
                st.warning(f"⏹️ Analysis stopped at page {current_page}/{total_pages}.")
                st.progress(current_page / max(1, total_pages))
            elif status == JobStatus.COMPLETED.value:
                st.success(f"✅ Analysis complete! Processed all {total_pages} pages.")
                st.balloons()
            elif status == JobStatus.FAILED.value:
                st.error(f"❌ Analysis failed: {current_job.get('error', 'Unknown error')}")
            
            # Show partial/final results
            results_df = job_manager.load_partial_results(st.session_state.current_job_id)
            if results_df is not None and len(results_df) > 0:
                st.session_state.partial_results = results_df
                
                # Update link_suggestions if job completed
                if status == JobStatus.COMPLETED.value:
                    st.session_state.link_suggestions = results_df
                
                # Show results count
                st.info(f"📊 Results: {len(results_df)} link suggestions generated")
                
                # Show preview
                results_label = "Final Results" if status == JobStatus.COMPLETED.value else "Partial Results"
                st.subheader(f"{results_label} Preview")
                st.dataframe(results_df.head(20), use_container_width=True)
                
                # Download button
                csv = results_df.to_csv(index=False).encode('utf-8')
                filename = f"link_suggestions_{st.session_state.current_job_id}.csv"
                st.download_button(
                    label=f"📥 Download {results_label} (CSV)",
                    data=csv,
                    file_name=filename,
                    mime="text/csv",
                    key=f"download_{st.session_state.current_job_id}"
                )
        
        # Show all jobs section
        st.markdown("---")
        st.subheader("📋 All Analysis Jobs")
        
        all_jobs = job_manager.list_jobs()
        if all_jobs:
            for job in all_jobs:
                job_id = job['job_id']
                status = job['status']
                current_page = job.get('current_page', 0)
                total_pages = job['total_pages']
                created_at = job['created_at'][:19].replace('T', ' ')
                
                # Job card
                with st.expander(f"Job {job_id} - {status} ({current_page}/{total_pages} pages) - Created: {created_at}"):
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    
                    with col_a:
                        st.write(f"**Status:** {status}")
                        st.write(f"**Progress:** {current_page}/{total_pages} pages")
                        if job.get('error'):
                            st.write(f"**Error:** {job['error']}")
                    
                    with col_b:
                        if st.button("Load This Job", key=f"load_{job_id}"):
                            st.session_state.current_job_id = job_id
                            st.rerun()
                    
                    with col_c:
                        if st.button("Delete Job", key=f"del_{job_id}"):
                            job_manager.delete_job(job_id)
                            if st.session_state.current_job_id == job_id:
                                st.session_state.current_job_id = None
                            st.rerun()
        else:
            st.info("No jobs found. Start a new analysis to begin!")


# Tab 3: Results and Analytics
with tab3:
    st.header("Results & Analytics")
    
    if st.session_state.uploaded_data is not None:
        st.subheader("📊 Data Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pages", len(st.session_state.uploaded_data))
        
        with col2:
            pages_with_h1 = st.session_state.uploaded_data['H1'].notna().sum()
            st.metric("Pages with H1", pages_with_h1)
        
        with col3:
            pages_with_title = st.session_state.uploaded_data['Meta Title'].notna().sum()
            st.metric("Pages with Meta Title", pages_with_title)
        
        st.subheader("Uploaded Data")
        st.dataframe(st.session_state.uploaded_data, use_container_width=True)
        
        # Download data
        csv = st.session_state.uploaded_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data",
            data=csv,
            file_name="website_data.csv",
            mime="text/csv"
        )
    
    if st.session_state.link_suggestions is not None:
        st.subheader("🔗 Link Suggestions Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Suggestions", len(st.session_state.link_suggestions))
        
        with col2:
            unique_sources = st.session_state.link_suggestions['Source URL'].nunique()
            st.metric("Pages with Suggestions", unique_sources)
        
        with col3:
            avg_per_page = len(st.session_state.link_suggestions) / unique_sources if unique_sources > 0 else 0
            st.metric("Avg. Suggestions/Page", f"{avg_per_page:.1f}")
        
        st.subheader("Link Suggestions")
        st.dataframe(st.session_state.link_suggestions, use_container_width=True)
        
        # Download link suggestions
        csv = st.session_state.link_suggestions.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Link Suggestions",
            data=csv,
            file_name="link_suggestions.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>InLink-Prospector - Expand Your Internal Links Site-Wide 🔗</p>
    <p>Powered by Google Gemini AI | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
