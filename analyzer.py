"""
LLM Analyzer Module for InLink-Prospector
Uses Google Gemini to generate internal linking suggestions
"""

import pandas as pd
from google import genai
from google.genai import types
import os
from typing import List, Dict
import json
import re
import time


class LinkAnalyzer:
    """Analyzes content and generates internal linking suggestions using Google Gemini"""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-pro"):
        """
        Initialize the analyzer
        
        Args:
            api_key: Google API key (if not provided, will use environment variable)
            model_name: Gemini model to use (default: gemini-2.5-pro, also supports gemini-3.0-pro-preview)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass it directly.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
    
    def generate_link_suggestions(self, df: pd.DataFrame, max_suggestions_per_page: int = 5, 
                                  progress_callback=None, status_check_callback=None) -> pd.DataFrame:
        """
        Generate internal link suggestions for pages
        
        Args:
            df: DataFrame with data (URL, H1, Meta Title, Content)
            max_suggestions_per_page: Maximum number of link suggestions per source page
            progress_callback: Optional callback function to report progress (page_index, total_pages)
            status_check_callback: Optional callback function that returns tuple (should_pause, should_stop)
            
        Returns:
            DataFrame with columns: Source URL, Anchor Text, Target URL
        """
        suggestions = []
        
        # Create a summary of all pages for context
        pages_summary = []
        for idx, row in df.iterrows():
            pages_summary.append({
                'url': row['URL'],
                'title': row['Meta Title'] or row['H1'],
                'content_preview': row['Content'][:200]
            })
        
        total_pages = len(df)
        
        # Analyze each page
        for idx, source_row in df.iterrows():
            # Check if we should pause or stop
            if status_check_callback:
                should_pause, should_stop = status_check_callback()
                
                if should_stop:
                    # Stop processing immediately
                    break
                
                # Wait while paused (with reasonable delay to avoid busy wait)
                while should_pause:
                    time.sleep(1.0)  # Sleep for 1 second between checks
                    should_pause, should_stop = status_check_callback()
                    if should_stop:
                        break
                
                if should_stop:
                    break
            
            source_url = source_row['URL']
            source_title = source_row['Meta Title'] or source_row['H1']
            source_content = source_row['Content']
            
            # Generate suggestions for this source page
            page_suggestions = self._analyze_page(
                source_url=source_url,
                source_title=source_title,
                source_content=source_content,
                all_pages=pages_summary,
                max_suggestions=max_suggestions_per_page
            )
            
            suggestions.extend(page_suggestions)
            
            # Report progress if callback provided
            if progress_callback:
                progress_callback(idx + 1, total_pages)
            
            # Add delay to avoid rate limits
            time.sleep(0.5)
        
        # Convert to DataFrame
        result_df = pd.DataFrame(suggestions)
        return result_df
    
    def _analyze_page(self, source_url: str, source_title: str, source_content: str, 
                     all_pages: List[Dict], max_suggestions: int) -> List[Dict]:
        """
        Analyze a single page and generate link suggestions
        
        Returns:
            List of dicts with source_url, anchor_text, target_url
        """
        # Prepare the context with available pages
        pages_context = "\n".join([
            f"- URL: {p['url']}\n  Title: {p['title']}\n  Preview: {p['content_preview'][:150]}..."
            for p in all_pages[:50]  # Limit to prevent token overflow
        ])
        
        prompt = f"""You are an SEO expert specializing in internal linking strategies. Analyze the following page and suggest relevant internal links.

SOURCE PAGE:
URL: {source_url}
Title: {source_title}
Content: {source_content}

AVAILABLE PAGES FOR LINKING:
{pages_context}

Task: Identify up to {max_suggestions} opportunities to add internal links from the source page to other relevant pages on the website.

For each suggestion, provide:
1. Anchor text: The exact phrase from the source content OR a semantically related phrase that would work as anchor text
2. Target URL: The URL of the page to link to
3. Relevance: Brief explanation of why this link makes sense

Return your response as a JSON array with this structure:
[
  {{
    "anchor_text": "relevant keyword phrase",
    "target_url": "https://example.com/target-page",
    "relevance": "Brief explanation"
  }}
]

Focus on:
- Semantic relevance between content
- Natural anchor text that fits the context
- High-value internal links that help users and SEO
- Exact match keywords or semantically related terms

Return ONLY the JSON array, no additional text."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            try:
                suggestions_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    suggestions_data = json.loads(json_match.group())
                else:
                    print(f"Failed to parse JSON from response for {source_url}")
                    return []
            
            # Format the suggestions
            formatted_suggestions = []
            for item in suggestions_data:
                if isinstance(item, dict) and 'anchor_text' in item and 'target_url' in item:
                    formatted_suggestions.append({
                        'Source URL': source_url,
                        'Anchor Text': item['anchor_text'],
                        'Target URL': item['target_url']
                    })
            
            return formatted_suggestions[:max_suggestions]
            
        except Exception as e:
            print(f"Error analyzing page {source_url}: {str(e)}")
            return []
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = 'link_suggestions.csv'):
        """Save link suggestions to CSV file"""
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
