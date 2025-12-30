"""
Demo script for InLink-Prospector
Shows how to use the crawler and analyzer programmatically
"""

from crawler import WebCrawler
from analyzer import LinkAnalyzer
import os


def demo_crawler():
    """Demo the web crawler functionality"""
    print("=" * 60)
    print("DEMO: Web Crawler")
    print("=" * 60)
    
    # Example: Crawl a website (use a small limit for demo)
    website_url = input("Enter website URL to crawl (or press Enter for demo): ").strip()
    if not website_url:
        website_url = "https://example.com"
        print(f"Using demo URL: {website_url}")
    
    max_pages = int(input("Enter max pages to crawl (default 10): ") or 10)
    
    print(f"\nCrawling {website_url}...")
    print(f"Max pages: {max_pages}")
    print("-" * 60)
    
    # Create crawler
    crawler = WebCrawler(website_url, max_pages=max_pages)
    
    # Crawl with progress
    def show_progress(current, total):
        print(f"Progress: {current}/{total} pages crawled", end='\r')
    
    df = crawler.crawl(progress_callback=show_progress)
    
    print(f"\n\n✓ Crawled {len(df)} pages successfully!")
    print("\nFirst 5 results:")
    print(df.head())
    
    # Save to CSV
    filename = crawler.save_to_csv(df, 'demo_crawl_output.csv')
    print(f"\n✓ Saved to {filename}")
    
    return df


def demo_analyzer(df):
    """Demo the link analyzer functionality"""
    print("\n" + "=" * 60)
    print("DEMO: Link Analyzer (LLM-based)")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("⚠️  No API key provided. Skipping analyzer demo.")
        return
    
    print(f"\nAnalyzing {len(df)} pages for link opportunities...")
    print("-" * 60)
    
    # Create analyzer
    analyzer = LinkAnalyzer(api_key=api_key)
    
    # Generate suggestions (limit to a few pages for demo)
    demo_df = df.head(3)  # Just analyze first 3 pages for demo
    print(f"Demo: Analyzing {len(demo_df)} pages (limited for demo)")
    
    suggestions_df = analyzer.generate_link_suggestions(demo_df, max_suggestions_per_page=3)
    
    print(f"\n✓ Generated {len(suggestions_df)} link suggestions!")
    print("\nSuggestions:")
    print(suggestions_df)
    
    # Save to CSV
    filename = analyzer.save_to_csv(suggestions_df, 'demo_link_suggestions.csv')
    print(f"\n✓ Saved to {filename}")


def main():
    """Run the demo"""
    print("\n" + "🔗" * 30)
    print("InLink-Prospector Demo")
    print("🔗" * 30 + "\n")
    
    # Demo crawler
    df = demo_crawler()
    
    # Ask if user wants to run analyzer
    if len(df) > 0:
        run_analyzer = input("\nRun link analyzer demo? (y/n): ").strip().lower()
        if run_analyzer == 'y':
            demo_analyzer(df)
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nCheck the generated CSV files:")
    print("- demo_crawl_output.csv")
    print("- demo_link_suggestions.csv (if analyzer was run)")
    print("\nTo run the full app: streamlit run app.py")


if __name__ == "__main__":
    main()
