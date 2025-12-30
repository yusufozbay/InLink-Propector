# InLink-Prospector 🔗

An intelligent internal linking tool that uses Google Gemini AI to suggest relevant internal links to expand your site-wide linking strategy.

## Features

- 📤 **CSV Upload**: Upload your website data with URL, H1, Meta Title, and content
- 🤖 **AI-Powered Analysis**: Uses Google Gemini (2.5 Pro or 3 Pro Preview) to generate intelligent internal link suggestions:
  - Source URL (where to add the link)
  - Anchor Text (exact match or semantically related)
  - Target URL (where the link should point)
- 📊 **CSV Export**: Export link suggestions to CSV files
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

3. Set up your Google API key:
```bash
cp .env.example .env
# Edit .env and add your Google API key
```

## Usage

### Running the Streamlit App

```bash
streamlit run app.py
```

This will open the app in your browser at `http://localhost:8501`

### Workflow

1. **Upload Data** (Tab 1):
   - Prepare a CSV file with columns: URL, H1, Meta Title, Content (First 500 chars)
   - Upload the CSV file
   - Verify the data preview

2. **Generate Link Suggestions** (Tab 2):
   - Enter your Google API key (in sidebar)
   - Select Gemini model (2.5 Pro or 3 Pro Preview)
   - Set max suggestions per page
   - Click "Generate Link Suggestions"
   - Wait for AI to analyze your content

3. **View Results** (Tab 3):
   - Review statistics
   - View and download link suggestions
   - Export data as CSV files

### Using the Module Programmatically

```python
from analyzer import LinkAnalyzer
import pandas as pd

# Load your data
df = pd.read_csv('your_data.csv')

# Initialize analyzer
analyzer = LinkAnalyzer(api_key='your-google-api-key', model_name='gemini-2.5-pro')

# Generate link suggestions
suggestions_df = analyzer.generate_link_suggestions(df, max_suggestions_per_page=5)

# Save to CSV
analyzer.save_to_csv(suggestions_df, 'link_suggestions.csv')
```

## Input CSV Format

Your CSV file must have these columns:

| Column | Description |
|--------|-------------|
| URL | URL Address of the page |
| H1 | H1 Heading |
| Meta Title | Meta Title tag |
| Content (First 500 chars) | First 500 words of main content |

### Example:

```csv
URL,H1,Meta Title,Content (First 500 chars)
https://example.com/seo-guide,Complete SEO Guide,SEO Best Practices,"Search Engine Optimization (SEO) is crucial..."
https://example.com/content-marketing,Content Marketing,Content Strategy Guide,"Content marketing is the art of creating..."
```

## Output Format

### Link Suggestions CSV

| Source URL | Anchor Text | Target URL |
|-----------|-------------|-----------|
| https://example.com/page1 | relevant keyword | https://example.com/page2 |

## Configuration

### Environment Variables

Create a `.env` file with:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### Gemini Models

Available models:
- `gemini-2.5-pro` (Recommended - Latest, high quality)
- `gemini-3.0-pro-preview` (Preview of next generation)

## Requirements

- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- google-genai >= 0.2.0
- python-dotenv >= 1.0.0

## Use Cases

- **SEO Optimization**: Improve internal linking structure
- **Content Strategy**: Discover related content opportunities
- **Site Architecture**: Better understand content relationships
- **Link Building**: Scale internal linking across large sites

## How It Works

1. **Upload Phase**:
   - User provides website data in CSV format
   - Data includes URL, titles, and content

2. **Analysis Phase**:
   - Google Gemini analyzes semantic relationships
   - AI generates contextual anchor text
   - Suggests relevant target pages

3. **Output Phase**:
   - Presents suggestions in table format
   - Exports to CSV for implementation
   - Provides analytics and statistics

## API Costs

Google Gemini API pricing:
- Free tier available with generous limits
- Gemini 2.5 Pro: High quality, balanced cost
- Gemini 3.0 Pro Preview: Preview version, may have different pricing

Estimated costs:
- 100 pages: ~$0.05-0.15
- 1000 pages: ~$0.50-1.50

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using Google Gemini AI and Streamlit