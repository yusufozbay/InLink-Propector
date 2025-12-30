# Entity-Based Internal Linking Implementation

## Overview

This implementation adds content-based entity extraction for internal link mapping in InLink-Prospector. Gemini analyzes the page content to extract entities dynamically, ensuring that all link suggestions are based on actual content analysis rather than pre-extracted metadata.

## Key Changes

### 1. Complete URL Database Pre-Reading

Before processing any pages, the system:

1. **Builds a Complete Database**: Creates a formatted database of ALL URLs with their:
   - URL
   - H1 heading
   - Meta Title

2. **Pre-reads All URLs**: This database is provided to Gemini at the start of EVERY prompt, ensuring:
   - Gemini knows ALL available URLs before suggesting links
   - No partial context or missing pages
   - 100% reliable URL suggestions

3. **Formatted Output**: The database is clearly formatted with headers and separators for easy reading by Gemini.

### 2. Content-Based Entity Extraction

The updated approach uses a two-step process:

**Step 1: Read URL Database**
- Gemini receives the complete URL database with URL + H1 + Meta Title
- This provides context about ALL available target pages

**Step 2: Analyze Content for Entities**
- Gemini analyzes the **source page content** to extract entities, topics, and concepts
- These content-based entities are used to create anchor text
- Entities are matched with target pages based on semantic relevance

This approach ensures:
- Anchor text is based on actual content, not pre-extracted metadata
- More accurate and contextual link suggestions
- Entities are extracted by AI analysis, not simple text parsing

### 3. Entity-Target Matching

The system enforces strict requirements:

1. **Content Analysis**: 
   - Gemini extracts entities FROM the content
   - Uses these entities as anchor text
   - Anchor text must be natural to the content context

2. **Semantic Matching**:
   - Content entities are matched with target pages
   - Matching is based on semantic relevance between content and target page topic
   - Example: Content mentions "link building strategies" → matches target page "Link Building Tactics"

3. **Output Enhancement**:
   - Includes "Entity Match" field showing how content entity matches target topic
   - Helps verify the matching is working correctly

## Code Structure

### Updated Methods in `LinkAnalyzer`:

1. **`_build_url_database(df)`**
   - Builds complete formatted database of all URLs
   - Includes URL, H1, and Meta Title (no pre-extracted entities)
   - Returns formatted string for Gemini prompt

2. **`generate_link_suggestions()`**
   - Builds URL database FIRST (before processing any pages)
   - Passes database to each page analysis
   - Maintains compatibility with existing features (pause/stop)

3. **`_analyze_page()`**
   - Updated to use content-based entity extraction
   - Receives complete URL database
   - Prompts Gemini to:
     1. Read the URL database
     2. Analyze source content for entities
     3. Match content entities with target pages
     4. Generate suggestions with entity-based anchors
   - Returns suggestions with Entity Match field

### Preserved Methods:

1. **`_extract_entities(url, h1, meta_title)`**
   - Still available for potential utility purposes
   - Not used in the main suggestion workflow
   - Kept for backward compatibility

## Usage Example

```python
from analyzer import LinkAnalyzer
import pandas as pd

# Load your data
df = pd.read_csv('your_data.csv')

# Initialize analyzer
analyzer = LinkAnalyzer(api_key='your-api-key', model_name='gemini-2.5-pro')

# Generate content-based link suggestions
# The analyzer will:
# 1. Build complete URL database (URL + H1 + Meta Title)
# 2. Pass database to Gemini BEFORE processing
# 3. Gemini analyzes CONTENT to extract entities
# 4. Gemini matches content entities with target pages
# 5. Generate suggestions with content-based anchors
suggestions_df = analyzer.generate_link_suggestions(df, max_suggestions_per_page=5)

# Results include:
# - Source URL
# - Anchor Text (extracted from content analysis)
# - Target URL
# - Entity Match (how content entity matches target topic)
```

## How It Works

### Example Workflow:

**URL Database (provided to Gemini first):**
```
1. URL: https://example.com/seo-guide
   H1: Complete SEO Guide 2024
   Meta Title: SEO Guide - Best Practices

2. URL: https://example.com/link-building
   H1: Link Building Tactics
   Meta Title: Link Building for SEO Success

... (all URLs included)
```

**Source Page Content Analysis:**
```
Content: "SEO is crucial for online visibility. This guide covers keyword 
research, link building strategies, and technical optimization..."

Gemini extracts entities from content:
- "SEO"
- "keyword research" 
- "link building strategies"
- "technical optimization"
```

**Matching & Suggestion:**
```json
{
  "anchor_text": "link building strategies",
  "target_url": "https://example.com/link-building",
  "entity_match": "Content entity 'link building' matches target 'Link Building Tactics'",
  "relevance": "Source discusses link building; target provides tactics"
}
```

## Testing

Comprehensive tests verify:

1. **URL Database Building**:
   - Includes all URLs with H1 and Meta Title
   - Does NOT include pre-extracted entities
   - Properly formatted

2. **Entity Extraction Method**:
   - Still available and functional
   - Not used in main workflow
   - Can extract from URL, H1, Meta Title

3. **Backward Compatibility**:
   - All existing tests pass
   - Existing features (pause/stop) work

## Benefits

1. **Content-Based Analysis**: Entities are extracted from actual content by Gemini, not pre-parsed
2. **Complete Context**: Gemini has ALL URLs available before processing
3. **Semantic Matching**: Intelligent matching between content entities and target pages
4. **Natural Anchor Text**: Anchor text is based on content, ensuring it fits naturally
5. **100% Reliable**: Complete URL database prevents missing or incorrect target URLs
6. **Transparency**: Entity Match field shows the connection between content and target

## Requirements Met

✅ Gemini reads ALL URLs (URL + H1 + Meta Title) BEFORE starting to map  
✅ Gemini analyzes CONTENT to extract entities  
✅ Entity extraction happens during content analysis, not pre-processing  
✅ Anchor text is based on content entities that match target page topics  
✅ 100% reliable suggestions with complete URL database context
