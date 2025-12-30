"""
InLink-Prospector - Internal Linking Suggestion Tool
A Streamlit app for crawling websites and generating internal link suggestions using LLM
"""

import streamlit as st
import pandas as pd
from crawler import WebCrawler
from analyzer import LinkAnalyzer
import os
from dotenv import load_dotenv
import time

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
if 'crawled_data' not in st.session_state:
    st.session_state.crawled_data = None
if 'link_suggestions' not in st.session_state:
    st.session_state.link_suggestions = None
if 'crawl_completed' not in st.session_state:
    st.session_state.crawl_completed = False

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# OpenAI API Key input
api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    value=os.getenv('OPENAI_API_KEY', ''),
    help="Enter your OpenAI API key for LLM analysis"
)

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Crawl Website", "🤖 Generate Links", "📈 Results"])

# Tab 1: Crawl Website
with tab1:
    st.header("Step 1: Crawl Your Website")
    
    st.markdown("""
    <div class="info-box">
    <b>What this does:</b><br>
    Crawls your website and extracts:
    <ul>
        <li>URL Address</li>
        <li>H1 Heading</li>
        <li>Meta Title</li>
        <li>First 500 characters of main content</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        website_url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the base URL of your website"
        )
    
    with col2:
        max_pages = st.number_input(
            "Max Pages",
            min_value=1,
            max_value=5000,
            value=100,
            help="Maximum number of pages to crawl (default: 100, max: 5000)"
        )
    
    # Upload CSV option
    st.subheader("Or Upload Existing Crawl Data")
    uploaded_file = st.file_uploader(
        "Upload CSV file with columns: URL, H1, Meta Title, Content (First 500 chars)",
        type=['csv']
    )
    
    if uploaded_file is not None:
        try:
            st.session_state.crawled_data = pd.read_csv(uploaded_file)
            st.session_state.crawl_completed = True
            st.success(f"✅ Loaded {len(st.session_state.crawled_data)} pages from CSV")
            st.dataframe(st.session_state.crawled_data.head())
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
    
    # Crawl button
    if st.button("🚀 Start Crawling", type="primary", disabled=not website_url):
        if not website_url:
            st.warning("Please enter a website URL")
        else:
            try:
                with st.spinner(f"Crawling {website_url}... This may take a while."):
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total):
                        progress = min(current / total, 1.0)
                        progress_bar.progress(progress)
                        status_text.text(f"Crawled {current} of {total} pages...")
                    
                    # Create crawler and crawl
                    crawler = WebCrawler(website_url, max_pages=max_pages)
                    df = crawler.crawl(progress_callback=update_progress)
                    
                    # Save to session state
                    st.session_state.crawled_data = df
                    st.session_state.crawl_completed = True
                    
                    # Save to CSV
                    filename = crawler.save_to_csv(df)
                    
                    st.success(f"✅ Successfully crawled {len(df)} pages!")
                    st.balloons()
                    
                    # Show preview
                    st.subheader("Crawl Results Preview")
                    st.dataframe(df.head(10))
                    
                    # Download button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Crawl Data (CSV)",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"Error during crawling: {str(e)}")

# Tab 2: Generate Link Suggestions
with tab2:
    st.header("Step 2: Generate Internal Link Suggestions")
    
    st.markdown("""
    <div class="info-box">
    <b>What this does:</b><br>
    Uses AI (LLM) to analyze your content and suggest relevant internal links with:
    <ul>
        <li>Source URL (where to add the link)</li>
        <li>Anchor Text (exact match or semantically related)</li>
        <li>Target URL (where the link should point to)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.crawl_completed:
        st.warning("⚠️ Please crawl a website or upload crawl data first (Step 1)")
    else:
        st.success(f"✅ Ready to analyze {len(st.session_state.crawled_data)} pages")
        
        suggestions_per_page = st.slider(
            "Max suggestions per page",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum number of link suggestions to generate for each page"
        )
        
        if st.button("🤖 Generate Link Suggestions", type="primary"):
            if not api_key:
                st.error("⚠️ Please enter your OpenAI API Key in the sidebar")
            else:
                try:
                    with st.spinner("Analyzing content and generating suggestions... This may take several minutes."):
                        # Progress indicator
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_pages = len(st.session_state.crawled_data)
                        
                        # Create analyzer
                        analyzer = LinkAnalyzer(api_key=api_key)
                        
                        # Generate suggestions
                        status_text.text(f"Processing {total_pages} pages...")
                        suggestions_df = analyzer.generate_link_suggestions(
                            st.session_state.crawled_data,
                            max_suggestions_per_page=suggestions_per_page
                        )
                        progress_bar.progress(1.0)
                        
                        # Save to session state
                        st.session_state.link_suggestions = suggestions_df
                        
                        # Save to CSV
                        filename = analyzer.save_to_csv(suggestions_df)
                        
                        st.success(f"✅ Generated {len(suggestions_df)} link suggestions!")
                        st.balloons()
                        
                        # Show preview
                        st.subheader("Link Suggestions Preview")
                        st.dataframe(suggestions_df.head(20))
                        
                        # Download button
                        csv = suggestions_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Link Suggestions (CSV)",
                            data=csv,
                            file_name=filename,
                            mime="text/csv"
                        )
                        
                except Exception as e:
                    st.error(f"Error generating suggestions: {str(e)}")

# Tab 3: Results and Analytics
with tab3:
    st.header("Results & Analytics")
    
    if st.session_state.crawled_data is not None:
        st.subheader("📊 Crawl Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pages Crawled", len(st.session_state.crawled_data))
        
        with col2:
            pages_with_h1 = st.session_state.crawled_data['H1'].notna().sum()
            st.metric("Pages with H1", pages_with_h1)
        
        with col3:
            pages_with_title = st.session_state.crawled_data['Meta Title'].notna().sum()
            st.metric("Pages with Meta Title", pages_with_title)
        
        st.subheader("Crawled Data")
        st.dataframe(st.session_state.crawled_data, use_container_width=True)
        
        # Download crawled data
        csv = st.session_state.crawled_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Crawl Data",
            data=csv,
            file_name="crawl_output.csv",
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
    <p>Powered by AI | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
