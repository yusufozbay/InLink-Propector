# Quick Start Guide - InLink-Prospector

## Installation

```bash
# Clone the repository
git clone https://github.com/yusufozbay/InLink-Propector.git
cd InLink-Propector

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional for demo)
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Running the App

### Option 1: Streamlit Web Interface (Recommended)

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

### Option 2: Command Line Demo

```bash
python demo.py
```

Follow the prompts to crawl a website and generate link suggestions.

### Option 3: Programmatic Usage

```python
from crawler import WebCrawler
from analyzer import LinkAnalyzer

# Step 1: Crawl a website
crawler = WebCrawler('https://example.com', max_pages=100)
crawl_df = crawler.crawl()
crawler.save_to_csv(crawl_df, 'my_crawl.csv')

# Step 2: Generate link suggestions
analyzer = LinkAnalyzer(api_key='your-openai-key')
suggestions_df = analyzer.generate_link_suggestions(crawl_df)
analyzer.save_to_csv(suggestions_df, 'my_suggestions.csv')
```

## Using the Streamlit App

### Step 1: Crawl Your Website

1. Go to the **"Crawl Website"** tab
2. Enter your website URL (e.g., `https://yoursite.com`)
3. Set the maximum number of pages to crawl (up to 5,000)
4. Click **"Start Crawling"**
5. Wait for the crawler to finish
6. Download the crawl data CSV

**Alternative:** Upload an existing crawl CSV file if you already have the data.

### Step 2: Generate Link Suggestions

1. Go to the **"Generate Links"** tab
2. Enter your OpenAI API key in the sidebar (or set it in `.env`)
3. Set the maximum number of suggestions per page (default: 5)
4. Click **"Generate Link Suggestions"**
5. Wait for the AI to analyze your content (this may take several minutes)
6. Download the link suggestions CSV

### Step 3: Review Results

1. Go to the **"Results"** tab
2. Review statistics about your crawl and suggestions
3. Browse through the link suggestions table
4. Download both CSV files for implementation

## Sample Data

A sample crawl data file is included: `sample_crawl_data.csv`

You can upload this in the Streamlit app to test the link generation without crawling.

## Output Files

### Crawl Output (crawl_output.csv)
```csv
URL,H1,Meta Title,Content (First 500 chars)
https://example.com/page1,Page Title,SEO Title,Page content preview...
```

### Link Suggestions (link_suggestions.csv)
```csv
Source URL,Anchor Text,Target URL
https://example.com/page1,relevant keyword,https://example.com/page2
https://example.com/page1,another link,https://example.com/page3
```

## Tips for Best Results

### Crawling
- Start with a smaller number of pages (100-200) for testing
- Ensure your website is accessible and not behind authentication
- The crawler respects a 0.5-second delay between requests
- Check robots.txt compliance for your site

### Link Generation
- More pages = better link suggestions (more opportunities)
- The AI looks for semantic relationships between content
- Anchor text can be exact match or contextually related
- Review suggestions before implementation

### API Costs
- OpenAI API calls have associated costs
- Approximately $0.001-0.002 per page analyzed
- For 100 pages: ~$0.10-0.20
- For 1000 pages: ~$1-2
- Set appropriate limits to control costs

## Troubleshooting

### "No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "OpenAI API key is required"
- Add your API key in the sidebar, or
- Create a `.env` file with `OPENAI_API_KEY=your_key`

### Crawler not finding pages
- Check that the URL is correct and accessible
- Ensure the site has internal links to follow
- Check for JavaScript-rendered content (not supported)

### Rate limit errors
- The app includes delays to avoid rate limits
- For OpenAI, check your API quota
- Consider smaller batches for link generation

## Advanced Configuration

### Modify Crawler Behavior

Edit `crawler.py` to:
- Change the delay between requests (default: 0.5s)
- Customize content selectors for your site structure
- Adjust content extraction length

### Customize LLM Analysis

Edit `analyzer.py` to:
- Change the AI model (default: gpt-3.5-turbo)
- Adjust temperature for more/less creative suggestions
- Modify the prompt for different link strategies
- Change max tokens for longer responses

### Streamlit Theme

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## Next Steps

1. **Implement the suggestions**: Add the internal links to your pages
2. **Monitor results**: Track changes in SEO performance
3. **Iterate**: Re-run the analysis periodically to find new opportunities
4. **Scale**: Gradually increase to full site (5,000 pages)

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the README.md for more details
- Review the code documentation

---

Happy linking! 🔗
