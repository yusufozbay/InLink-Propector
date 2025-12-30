# Quick Start Guide - InLink-Prospector

## Installation

```bash
# Clone the repository
git clone https://github.com/yusufozbay/InLink-Prospector.git
cd InLink-Prospector

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Google API key
```

## Running the App

### Streamlit Web Interface (Recommended)

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

### Programmatic Usage

```python
from analyzer import LinkAnalyzer
import pandas as pd

# Load your website data
df = pd.read_csv('your_data.csv')

# Initialize analyzer with Google Gemini
analyzer = LinkAnalyzer(api_key='your-google-api-key', model_name='gemini-2.5-pro')

# Generate link suggestions
suggestions_df = analyzer.generate_link_suggestions(df, max_suggestions_per_page=5)

# Save to CSV
analyzer.save_to_csv(suggestions_df, 'link_suggestions.csv')
```

## Using the Streamlit App

### Step 1: Upload Your Data

1. Go to the **"Upload Data"** tab
2. Prepare a CSV file with these columns:
   - URL (page address)
   - H1 (H1 heading)
   - Meta Title (title tag)
   - Content (First 500 chars) (first 500 words of content)
3. Click the file uploader and select your CSV
4. Verify the data preview

### Step 2: Generate Link Suggestions

1. Go to the **"Generate Links"** tab
2. Enter your Google API key in the sidebar (or set it in `.env`)
3. Select the Gemini model (2.5 Pro recommended)
4. Set the maximum number of suggestions per page (default: 5)
5. Click **"Generate Link Suggestions"**
6. Wait for the AI to analyze your content (this may take several minutes)
7. Download the link suggestions CSV

### Step 3: Review Results

1. Go to the **"Results"** tab
2. Review statistics about your data and suggestions
3. Browse through the link suggestions table
4. Download both CSV files for implementation

## Sample Data

A sample crawl data file is included: `sample_crawl_data.csv`

You can upload this in the Streamlit app to test the link generation.

## CSV Format

### Required Input Format

Your CSV must have these exact column names:

```csv
URL,H1,Meta Title,Content (First 500 chars)
https://example.com/page1,Page Title,SEO Title,Page content preview...
```

### Output Format

The generated link suggestions will have:

```csv
Source URL,Anchor Text,Target URL
https://example.com/page1,relevant keyword,https://example.com/page2
https://example.com/page1,another link,https://example.com/page3
```

## Tips for Best Results

### Data Preparation
- Ensure all required columns are present
- Use actual content from your pages (not just meta descriptions)
- Include first 500 words of main content for better analysis
- More pages = better link suggestions (more opportunities)

### Model Selection
- **gemini-2.5-pro**: Best quality, recommended for most use cases
- **gemini-3.0-pro-preview**: Preview of next generation model

### API Costs
- Google Gemini has a free tier with generous limits
- Gemini 2.5 Pro: High quality, balanced cost
- Approximately $0.05-0.15 per 100 pages
- For 1000 pages: ~$0.50-1.50
- Much cheaper than OpenAI

## Troubleshooting

### "No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "Google API key is required"
- Add your API key in the sidebar, or
- Create a `.env` file with `GOOGLE_API_KEY=your_key`

### "Failed to parse JSON from response"
- Try a different model (switch between Flash and Pro)
- Reduce the number of pages being analyzed
- Check your API quota

### Missing columns error
- Ensure CSV has exact column names: `URL`, `H1`, `Meta Title`, `Content (First 500 chars)`
- Check for typos in column names
- Verify CSV is properly formatted

## Getting a Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy your API key
5. Add it to `.env` or paste it in the sidebar

## Advanced Configuration

### Customize Analysis

Edit `analyzer.py` to:
- Change the AI model (default: gemini-2.5-pro)
- Adjust the prompt for different link strategies
- Modify suggestions per page

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

1. **Prepare your data**: Export website data in the required CSV format
2. **Upload and analyze**: Use the Streamlit app to generate suggestions
3. **Implement links**: Add the suggested internal links to your pages
4. **Monitor results**: Track changes in SEO performance
5. **Iterate**: Re-run the analysis periodically for new opportunities

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the README.md for more details
- Review the code documentation

---

Happy linking! 🔗
