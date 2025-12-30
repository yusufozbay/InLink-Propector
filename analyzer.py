"""
LLM Analyzer Module for InLink-Prospector
Uses LLM to generate internal linking suggestions
"""

import pandas as pd
from openai import OpenAI
import os
from typing import List, Dict
import json
import time


class LinkAnalyzer:
    """Analyzes crawled content and generates internal linking suggestions using LLM"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the analyzer
        
        Args:
            api_key: OpenAI API key (if not provided, will use environment variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_link_suggestions(self, df: pd.DataFrame, max_suggestions_per_page: int = 5) -> pd.DataFrame:
        """
        Generate internal link suggestions for crawled pages
        
        Args:
            df: DataFrame with crawled data (URL, H1, Meta Title, Content)
            max_suggestions_per_page: Maximum number of link suggestions per source page
            
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
                'content_preview': row['Content (First 500 chars)'][:200]
            })
        
        # Analyze each page
        for idx, source_row in df.iterrows():
            source_url = source_row['URL']
            source_title = source_row['Meta Title'] or source_row['H1']
            source_content = source_row['Content (First 500 chars)']
            
            # Generate suggestions for this source page
            page_suggestions = self._analyze_page(
                source_url=source_url,
                source_title=source_title,
                source_content=source_content,
                all_pages=pages_summary,
                max_suggestions=max_suggestions_per_page
            )
            
            suggestions.extend(page_suggestions)
            
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
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                suggestions_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                import re
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
