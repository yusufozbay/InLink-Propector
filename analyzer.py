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
    
    def _extract_entities(self, url: str, h1: str, meta_title: str) -> List[str]:
        """
        Extract key entities from URL, H1, and Meta Title
        
        Args:
            url: Page URL
            h1: H1 heading
            meta_title: Meta title
            
        Returns:
            List of extracted entities (keywords/phrases)
        """
        entities = []
        
        # Extract from URL path (convert hyphens/underscores to spaces, remove domain)
        # Remove trailing slash and get last path segment
        url_path = url.rstrip('/').split('/')[-1] if '/' in url else ''
        # Remove common file extensions
        url_path = re.sub(r'\.(html?|php|aspx?)$', '', url_path, flags=re.IGNORECASE)
        # Convert hyphens/underscores to spaces
        url_words = re.sub(r'[_-]', ' ', url_path).strip()
        # Only add if it's not empty and doesn't look like a domain
        if url_words and '.' not in url_words:
            entities.append(url_words)
        
        # Extract from H1
        if h1 and isinstance(h1, str):
            entities.append(h1.strip())
        
        # Extract from Meta Title (remove site name if present)
        if meta_title and isinstance(meta_title, str):
            # Remove common separators and site names (fixed regex pattern)
            title_clean = re.split(r'[|–—]|-', meta_title)[0].strip()
            if title_clean:
                entities.append(title_clean)
        
        return entities
    
    def _build_url_database(self, df: pd.DataFrame) -> str:
        """
        Build a complete database of all URLs with their metadata for Gemini to read
        
        Args:
            df: DataFrame with all pages data
            
        Returns:
            Formatted string with all URLs and their metadata
        """
        url_database = []
        
        for idx, row in df.iterrows():
            url = row['URL']
            h1 = row['H1'] if pd.notna(row['H1']) else ''
            meta_title = row['Meta Title'] if pd.notna(row['Meta Title']) else ''
            
            # Extract entities for this page
            entities = self._extract_entities(url, h1, meta_title)
            
            url_entry = {
                'url': url,
                'h1': h1,
                'meta_title': meta_title,
                'entities': entities
            }
            url_database.append(url_entry)
        
        # Format as a clear, readable database for Gemini
        formatted_db = "COMPLETE URL DATABASE (Read this first):\n"
        formatted_db += "=" * 80 + "\n\n"
        
        for i, entry in enumerate(url_database, 1):
            formatted_db += f"{i}. URL: {entry['url']}\n"
            formatted_db += f"   H1: {entry['h1']}\n"
            formatted_db += f"   Meta Title: {entry['meta_title']}\n"
            formatted_db += f"   Key Entities: {', '.join(entry['entities'])}\n"
            formatted_db += "\n"
        
        formatted_db += "=" * 80 + "\n"
        
        return formatted_db
    
    def generate_link_suggestions(self, df: pd.DataFrame, max_suggestions_per_page: int = 5, 
                                  progress_callback=None, status_check_callback=None) -> pd.DataFrame:
        """
        Generate internal link suggestions for pages based on entity mapping
        
        Args:
            df: DataFrame with data (URL, H1, Meta Title, Content)
            max_suggestions_per_page: Maximum number of link suggestions per source page
            progress_callback: Optional callback function to report progress (page_index, total_pages)
            status_check_callback: Optional callback function that returns tuple (should_pause, should_stop)
            
        Returns:
            DataFrame with columns: Source URL, Anchor Text, Target URL, Entity Match
        """
        suggestions = []
        
        # CRITICAL: Build complete URL database first - Gemini must read ALL URLs before processing
        url_database = self._build_url_database(df)
        
        # Create a summary of all pages for context (keeping existing structure for compatibility)
        pages_summary = []
        for idx, row in df.iterrows():
            entities = self._extract_entities(
                row['URL'], 
                row['H1'] if pd.notna(row['H1']) else '',
                row['Meta Title'] if pd.notna(row['Meta Title']) else ''
            )
            pages_summary.append({
                'url': row['URL'],
                'h1': row['H1'] if pd.notna(row['H1']) else '',
                'meta_title': row['Meta Title'] if pd.notna(row['Meta Title']) else '',
                'entities': entities,
                'content_preview': row['Content'][:200] if pd.notna(row['Content']) else ''
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
            source_h1 = source_row['H1'] if pd.notna(source_row['H1']) else ''
            source_meta_title = source_row['Meta Title'] if pd.notna(source_row['Meta Title']) else ''
            source_content = source_row['Content'] if pd.notna(source_row['Content']) else ''
            
            # Extract entities for source page
            source_entities = self._extract_entities(source_url, source_h1, source_meta_title)
            
            # Generate suggestions for this source page (entity-based)
            page_suggestions = self._analyze_page(
                source_url=source_url,
                source_h1=source_h1,
                source_meta_title=source_meta_title,
                source_content=source_content,
                source_entities=source_entities,
                all_pages=pages_summary,
                url_database=url_database,
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
    
    def _analyze_page(self, source_url: str, source_h1: str, source_meta_title: str, 
                     source_content: str, source_entities: List[str], 
                     all_pages: List[Dict], url_database: str, max_suggestions: int) -> List[Dict]:
        """
        Analyze a single page and generate entity-based link suggestions
        
        Args:
            source_url: URL of the source page
            source_h1: H1 of the source page
            source_meta_title: Meta title of the source page
            source_content: Content of the source page
            source_entities: Extracted entities from source page
            all_pages: List of all pages with their metadata
            url_database: Complete formatted database of all URLs
            max_suggestions: Maximum number of suggestions to generate
        
        Returns:
            List of dicts with source_url, anchor_text, target_url, entity_match
        """
        
        prompt = f"""{url_database}

IMPORTANT INSTRUCTIONS - READ CAREFULLY:

1. You have been provided with the COMPLETE URL DATABASE above containing ALL available pages with their URLs, H1 headings, Meta Titles, and Key Entities.
2. You MUST use ONLY the URLs from this database when suggesting internal links.
3. Internal link suggestions MUST be based on ENTITY MAPPING - the suggested anchor text must contain an entity (exact match or semantically related) from the target page.

NOW ANALYZE THIS SOURCE PAGE:

SOURCE PAGE DETAILS:
- URL: {source_url}
- H1: {source_h1}
- Meta Title: {source_meta_title}
- Key Entities: {', '.join(source_entities)}
- Content: {source_content}

YOUR TASK:

Identify up to {max_suggestions} opportunities to add internal links from this source page to other pages in the URL database.

CRITICAL REQUIREMENTS FOR EACH SUGGESTION:

1. **Entity-Based Mapping**: The anchor text MUST contain an entity from the target page (exact match OR semantically related term)
   - For example, if target page has entity "SEO Guide", valid anchor texts include:
     * "SEO Guide" (exact match)
     * "search engine optimization guide" (semantic match)
     * "comprehensive SEO resource" (semantic match)
   
2. **Anchor Text Quality**: 
   - Must be a natural phrase from the source content OR a semantically relevant phrase
   - Must relate to the target page's entities (H1, Meta Title, or URL)
   - Should be 2-6 words long
   
3. **Target URL Validation**:
   - MUST be from the URL database provided above
   - MUST be different from the source URL
   - MUST be semantically relevant to the source content
   
4. **Context Relevance**:
   - The link must make sense in the context of the source page content
   - Should add value for users and improve SEO

Return your response as a JSON array with this structure:
[
  {{
    "anchor_text": "exact or semantic entity match phrase",
    "target_url": "https://example.com/target-page",
    "entity_match": "entity from target page that matches the anchor text",
    "relevance": "Brief explanation of why this link makes sense"
  }}
]

EXAMPLE (for illustration only):
If source page discusses "SEO strategies" and target page has entity "Link Building Tactics":
[
  {{
    "anchor_text": "link building strategies",
    "target_url": "https://example.com/link-building",
    "entity_match": "Link Building Tactics (semantic match)",
    "relevance": "Source discusses SEO strategies; link building is a core SEO tactic"
  }}
]

Return ONLY the JSON array, no additional text or formatting."""

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
            
            # Format the suggestions with entity match information
            formatted_suggestions = []
            for item in suggestions_data:
                if isinstance(item, dict) and 'anchor_text' in item and 'target_url' in item:
                    suggestion = {
                        'Source URL': source_url,
                        'Anchor Text': item['anchor_text'],
                        'Target URL': item['target_url']
                    }
                    # Add entity match if available
                    if 'entity_match' in item:
                        suggestion['Entity Match'] = item['entity_match']
                    formatted_suggestions.append(suggestion)
            
            return formatted_suggestions[:max_suggestions]
            
        except Exception as e:
            print(f"Error analyzing page {source_url}: {str(e)}")
            return []
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = 'link_suggestions.csv'):
        """Save link suggestions to CSV file"""
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
