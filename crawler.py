"""
Web Crawler Module for InLink-Prospector
Crawls websites and extracts URL, H1, Meta Title, and content
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import pandas as pd
from typing import List, Dict, Set
import re


class WebCrawler:
    """Crawls a website and extracts relevant SEO data"""
    
    def __init__(self, base_url: str, max_pages: int = 5000):
        """
        Initialize the crawler
        
        Args:
            base_url: The base URL of the website to crawl
            max_pages: Maximum number of pages to crawl (default: 5000)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[Dict] = []
        self.domain = urlparse(base_url).netloc
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.netloc == self.domain
        except:
            return False
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Try to find main content area
        main_content = None
        
        # Common content selectors
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.content',
            '#content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Remove script and style elements
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = main_content.get_text()
            text = self.clean_text(text)
            # Return first 500 characters
            return text[:500] if len(text) > 500 else text
        
        return ""
    
    def extract_page_data(self, url: str) -> Dict:
        """
        Extract data from a single page
        
        Returns:
            Dict with url, h1, meta_title, and content
        """
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract H1
            h1_tag = soup.find('h1')
            h1 = self.clean_text(h1_tag.get_text()) if h1_tag else ""
            
            # Extract Meta Title
            title_tag = soup.find('title')
            meta_title = self.clean_text(title_tag.get_text()) if title_tag else ""
            
            # Extract main content (first 500 chars)
            content = self.extract_main_content(soup)
            
            # Find all internal links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url) and full_url not in self.visited_urls:
                    links.append(full_url)
            
            return {
                'url': url,
                'h1': h1,
                'meta_title': meta_title,
                'content': content,
                'links': links
            }
            
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return None
    
    def crawl(self, start_url: str = None, progress_callback=None) -> pd.DataFrame:
        """
        Crawl the website starting from the given URL
        
        Args:
            start_url: URL to start crawling from (default: base_url)
            progress_callback: Optional callback function to report progress
            
        Returns:
            DataFrame with crawled data
        """
        if start_url is None:
            start_url = self.base_url
        
        urls_to_visit = [start_url]
        self.visited_urls = set()
        self.crawled_data = []
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            
            # Report progress
            if progress_callback:
                progress_callback(len(self.visited_urls), self.max_pages)
            
            # Extract page data
            page_data = self.extract_page_data(current_url)
            
            if page_data:
                # Store the data (without links)
                self.crawled_data.append({
                    'URL': page_data['url'],
                    'H1': page_data['h1'],
                    'Meta Title': page_data['meta_title'],
                    'Content (First 500 chars)': page_data['content']
                })
                
                # Add new links to visit
                urls_to_visit.extend(page_data['links'])
            
            # Be polite - add a small delay
            time.sleep(0.5)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.crawled_data)
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = 'crawl_output.csv'):
        """Save crawled data to CSV file"""
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
