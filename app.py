"""
InLink-Prospector - Internal Linking Suggestion Tool
A Streamlit app for generating internal link suggestions using Google Gemini
"""

import streamlit as st
import pandas as pd
from analyzer import LinkAnalyzer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
if 'is_paused' not in st.session_state:
    st.session_state.is_paused = False
if 'should_stop' not in st.session_state:
    st.session_state.should_stop = False
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'partial_results' not in st.session_state:
    st.session_state.partial_results = None
if 'current_progress' not in st.session_state:
    st.session_state.current_progress = 0

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
        
        # Control buttons in columns
        col1, col2, col3 = st.columns([1.5, 1, 1])
        
        with col1:
            if not st.session_state.is_processing:
                if st.button("🤖 Generate Link Suggestions", type="primary"):
                    if not api_key:
                        st.error("⚠️ Please enter your Google API Key in the sidebar")
                    else:
                        st.session_state.is_processing = True
                        st.session_state.is_paused = False
                        st.session_state.should_stop = False
                        st.session_state.partial_results = None
                        st.session_state.current_progress = 0
                        st.rerun()
        
        with col2:
            if st.session_state.is_processing:
                if st.session_state.is_paused:
                    if st.button("▶️ Resume"):
                        st.session_state.is_paused = False
                        st.rerun()
                else:
                    if st.button("⏸️ Pause"):
                        st.session_state.is_paused = True
                        st.rerun()
        
        with col3:
            if st.session_state.is_processing:
                if st.button("⏹️ Stop"):
                    st.session_state.should_stop = True
                    st.rerun()
        
        # Show current status
        if st.session_state.is_processing:
            if st.session_state.is_paused:
                st.warning("⏸️ Processing is paused. Click 'Resume' to continue or 'Stop' to end.")
            else:
                st.info("🔄 Processing in progress...")
        
        # Show partial results download when paused or stopped
        if st.session_state.partial_results is not None and len(st.session_state.partial_results) > 0:
            total_pages = len(st.session_state.uploaded_data)
            st.info(f"📊 Partial results: {len(st.session_state.partial_results)} suggestions from {st.session_state.current_progress}/{total_pages} pages")
            
            # Show preview
            st.subheader("Partial Results Preview")
            st.dataframe(st.session_state.partial_results.head(20), use_container_width=True)
            
            # Download button for partial results
            partial_csv = st.session_state.partial_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Partial Results (CSV)",
                data=partial_csv,
                file_name="link_suggestions_partial.csv",
                mime="text/csv",
                key="partial_download_btn"
            )
        
        # Process if we're in processing state and not stopped
        if st.session_state.is_processing and not st.session_state.should_stop:
            try:
                # Progress indicators
                progress_bar = st.progress(st.session_state.current_progress / max(1, len(st.session_state.uploaded_data)))
                status_text = st.empty()
                
                total_pages = len(st.session_state.uploaded_data)
                
                # Create analyzer
                analyzer = LinkAnalyzer(api_key=api_key, model_name=model_choice)
                
                # Track suggestions
                all_suggestions = []
                
                # Progress callback
                def update_progress(current, total):
                    st.session_state.current_progress = current
                    progress_bar.progress(current / total)
                    status_text.text(f"Processing page {current} of {total}... (Click 'Pause' or 'Stop' to interrupt)")
                
                # Status check callback
                def check_status():
                    return (st.session_state.is_paused, st.session_state.should_stop)
                
                # Wrap _analyze_page to collect results
                original_analyze_page = analyzer._analyze_page
                
                def wrapped_analyze_page(*args, **kwargs):
                    result = original_analyze_page(*args, **kwargs)
                    all_suggestions.extend(result)
                    # Update partial results
                    if len(all_suggestions) > 0:
                        st.session_state.partial_results = pd.DataFrame(all_suggestions)
                    return result
                
                analyzer._analyze_page = wrapped_analyze_page
                
                # Generate suggestions
                status_text.text(f"Starting to process {total_pages} pages with {model_choice}...")
                suggestions_df = analyzer.generate_link_suggestions(
                    st.session_state.uploaded_data,
                    max_suggestions_per_page=suggestions_per_page,
                    progress_callback=update_progress,
                    status_check_callback=check_status
                )
                
                # Mark processing as complete
                st.session_state.is_processing = False
                
                if st.session_state.should_stop:
                    # Processing was stopped by user
                    st.warning(f"⏹️ Processing stopped by user. Generated {len(suggestions_df)} link suggestions from {st.session_state.current_progress} of {total_pages} pages.")
                    
                    if len(suggestions_df) > 0:
                        # Save to session state
                        st.session_state.link_suggestions = suggestions_df
                        st.session_state.partial_results = suggestions_df
                        
                        # Save to CSV
                        filename = analyzer.save_to_csv(suggestions_df, 'link_suggestions_partial.csv')
                        
                        st.success(f"✅ Partial results saved!")
                        
                        # Show preview
                        st.subheader("Link Suggestions (Partial)")
                        st.dataframe(suggestions_df.head(20), use_container_width=True)
                        
                        # Download button
                        csv = suggestions_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Partial Results (CSV)",
                            data=csv,
                            file_name=filename,
                            mime="text/csv",
                            key="stopped_final_download"
                        )
                    else:
                        st.info("No suggestions were generated before stopping.")
                else:
                    # Processing completed normally
                    progress_bar.progress(1.0)
                    status_text.text("✅ Processing complete!")
                    
                    # Save to session state
                    st.session_state.link_suggestions = suggestions_df
                    
                    # Save to CSV
                    filename = analyzer.save_to_csv(suggestions_df)
                    
                    st.success(f"✅ Generated {len(suggestions_df)} link suggestions!")
                    st.balloons()
                    
                    # Show preview
                    st.subheader("Link Suggestions Preview")
                    st.dataframe(suggestions_df.head(20), use_container_width=True)
                    
                    # Download button
                    csv = suggestions_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Link Suggestions (CSV)",
                        data=csv,
                        file_name=filename,
                        mime="text/csv",
                        key="complete_final_download"
                    )
                
                # Reset flags
                st.session_state.should_stop = False
                st.session_state.is_paused = False
                
            except Exception as e:
                st.session_state.is_processing = False
                st.session_state.should_stop = False
                st.session_state.is_paused = False
                st.error(f"Error generating suggestions: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

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
