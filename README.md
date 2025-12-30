# InLink-Prospector 🔗

An intelligent internal linking tool that crawls your website and uses AI to suggest relevant internal links to expand your site-wide linking strategy.

## Features

- 🕷️ **Web Crawler**: Crawls up to 5,000 pages and extracts:
  - URL Address
  - H1 Heading
  - Meta Title
  - First 500 characters of main content

- 🤖 **AI-Powered Analysis**: Uses LLM (OpenAI GPT) to generate intelligent internal link suggestions:
  - Source URL (where to add the link)
  - Anchor Text (exact match or semantically related)
  - Target URL (where the link should point)

- 📊 **CSV Export**: Export crawl data and link suggestions to CSV files

- 🎨 **Streamlit UI**: User-friendly web interface for the entire workflow

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yusufozbay/InLink-Prospector.git
cd InLink-Prospector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Running the Streamlit App

```bash
streamlit run app.py
```

This will open the app in your browser at `http://localhost:8501`

### Workflow

1. **Crawl Website** (Tab 1):
   - Enter your website URL
   - Set max pages to crawl (up to 5,000)
   - Click "Start Crawling"
   - Or upload an existing crawl CSV file

2. **Generate Link Suggestions** (Tab 2):
   - Enter your OpenAI API key (in sidebar)
   - Set max suggestions per page
   - Click "Generate Link Suggestions"
   - Wait for AI to analyze your content

3. **View Results** (Tab 3):
   - Review crawl statistics
   - View and download link suggestions
   - Export data as CSV files

### Using the Modules Programmatically

#### Web Crawler

```python
from crawler import WebCrawler

# Initialize crawler
crawler = WebCrawler('https://example.com', max_pages=100)

# Crawl the website
df = crawler.crawl()

# Save to CSV
crawler.save_to_csv(df, 'crawl_output.csv')
```

#### Link Analyzer

```python
from analyzer import LinkAnalyzer
import pandas as pd

# Load crawled data
df = pd.read_csv('crawl_output.csv')

# Initialize analyzer
analyzer = LinkAnalyzer(api_key='your-openai-api-key')

# Generate link suggestions
suggestions_df = analyzer.generate_link_suggestions(df, max_suggestions_per_page=5)

# Save to CSV
analyzer.save_to_csv(suggestions_df, 'link_suggestions.csv')
```

## Output Format

### Crawl Output CSV
| URL | H1 | Meta Title | Content (First 500 chars) |
|-----|----|-----------|-----------------------------|
| https://example.com/page1 | Page Title | SEO Title | Page content preview... |

### Link Suggestions CSV
| Source URL | Anchor Text | Target URL |
|-----------|-------------|-----------|
| https://example.com/page1 | relevant keyword | https://example.com/page2 |

## Configuration

### Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Crawler Settings

- `max_pages`: Maximum number of pages to crawl (default: 5000)
- Delay between requests: 0.5 seconds (to be polite)

### Analyzer Settings

- `max_suggestions_per_page`: Maximum link suggestions per page (default: 5)
- LLM Model: GPT-3.5-turbo (configurable in code)

## Requirements

- Python 3.8+
- streamlit >= 1.28.0
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- pandas >= 2.0.0
- openai >= 1.3.0
- lxml >= 4.9.0
- python-dotenv >= 1.0.0

## Use Cases

- **SEO Optimization**: Improve internal linking structure
- **Content Strategy**: Discover related content opportunities
- **Site Architecture**: Better understand content relationships
- **Link Building**: Scale internal linking across large sites

## How It Works

1. **Crawling Phase**:
   - Starts from the base URL
   - Follows internal links
   - Extracts SEO-relevant data
   - Respects crawl limits

2. **Analysis Phase**:
   - Sends page content to LLM
   - AI analyzes semantic relationships
   - Generates contextual anchor text
   - Suggests relevant target pages

3. **Output Phase**:
   - Presents suggestions in table format
   - Exports to CSV for implementation
   - Provides analytics and statistics

## Limitations

- Requires OpenAI API key (costs apply)
- Crawling large sites takes time
- Rate limits apply to API calls
- Best results with well-structured HTML

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using Streamlit and OpenAI