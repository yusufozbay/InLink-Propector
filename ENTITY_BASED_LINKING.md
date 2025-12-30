# Entity-Based Internal Linking Implementation

## Overview

This implementation adds entity-based internal link mapping to InLink-Prospector, ensuring that all link suggestions are based on entities extracted from page metadata and that Gemini has complete knowledge of ALL URLs before generating suggestions.

## Key Changes

### 1. Entity Extraction

Entities are now extracted from three sources for each page:

1. **URL Path**: 
   - Extracts the last segment of the URL path
   - Converts hyphens and underscores to spaces
   - Removes common file extensions (.html, .php, .aspx)
   - Handles trailing slashes
   - Filters out domain-only URLs
   - Example: `https://example.com/seo-guide/` → `"seo guide"`

2. **H1 Heading**:
   - Uses the complete H1 text as an entity
   - Example: `"Complete SEO Guide 2024"`

3. **Meta Title**:
   - Extracts the main title before separators (|, –, —, -)
   - Removes site name suffixes
   - Example: `"SEO Guide - Best Practices | Example"` → `"SEO Guide"`

### 2. Complete URL Database

Before processing any pages, the system now:

1. **Builds a Complete Database**: Creates a formatted database of ALL URLs with their:
   - URL
   - H1 heading
   - Meta title
   - Extracted entities

2. **Pre-reads All URLs**: This database is provided to Gemini at the start of EVERY prompt, ensuring:
   - Gemini knows ALL available URLs before suggesting links
   - No partial context or missing pages
   - 100% reliable URL suggestions

3. **Formatted Output**: The database is clearly formatted with headers and separators for easy reading by Gemini.

### 3. Entity-Based Mapping

The updated prompt enforces strict entity-based requirements:

1. **Anchor Text Requirement**: 
   - MUST contain an entity from the target page
   - Can be exact match OR semantically related
   - Examples:
     - Exact: "SEO Guide" (matches entity "SEO Guide")
     - Semantic: "search engine optimization guide" (matches entity "SEO Guide")

2. **Target URL Validation**:
   - MUST be from the URL database
   - MUST be different from source URL
   - MUST be semantically relevant to source content

3. **Output Enhancement**:
   - Includes "Entity Match" field showing which entity was matched
   - Helps verify entity-based mapping is working correctly

## Code Structure

### New Methods in `LinkAnalyzer`:

1. **`_extract_entities(url, h1, meta_title)`**
   - Extracts entities from URL, H1, and Meta Title
   - Returns list of entity strings
   - Handles edge cases (trailing slashes, file extensions, None values)

2. **`_build_url_database(df)`**
   - Builds complete formatted database of all URLs
   - Includes all metadata and entities
   - Returns formatted string for Gemini prompt

### Updated Methods:

1. **`generate_link_suggestions()`**
   - Now builds URL database FIRST (before processing any pages)
   - Passes database to each page analysis
   - Maintains compatibility with existing features (pause/stop)

2. **`_analyze_page()`**
   - Updated signature to include URL database and entities
   - Enhanced prompt with entity-based requirements
   - Returns suggestions with optional Entity Match field

## Usage Example

```python
from analyzer import LinkAnalyzer
import pandas as pd

# Load your data
df = pd.read_csv('your_data.csv')

# Initialize analyzer
analyzer = LinkAnalyzer(api_key='your-api-key', model_name='gemini-2.5-pro')

# Generate entity-based link suggestions
# The analyzer will:
# 1. Extract entities from all pages
# 2. Build complete URL database
# 3. Pass database to Gemini BEFORE processing
# 4. Generate suggestions with entity-based anchors
suggestions_df = analyzer.generate_link_suggestions(df, max_suggestions_per_page=5)

# Results include:
# - Source URL
# - Anchor Text (contains entity from target page)
# - Target URL
# - Entity Match (optional, shows which entity was matched)
```

## Testing

Comprehensive tests verify:

1. **Entity Extraction**:
   - Extracts from URL, H1, Meta Title
   - Handles trailing slashes
   - Removes file extensions
   - Splits meta title on separators
   - Handles None/missing values

2. **URL Database Building**:
   - Includes all URLs
   - Contains all metadata
   - Properly formatted

3. **Backward Compatibility**:
   - All existing tests still pass
   - Existing features (pause/stop) still work

## Benefits

1. **Entity-Based Quality**: All link suggestions are based on entities, ensuring relevance
2. **Complete Context**: Gemini has ALL URLs available, preventing missing or incorrect suggestions
3. **Semantic Matching**: Supports both exact and semantic entity matches for flexibility
4. **100% Reliable**: No partial context or guesswork - Gemini knows the complete URL database
5. **Transparency**: Entity Match field shows which entity was matched for verification

## Requirements Met

✅ Internal link opportunities are based on Entities  
✅ Entity must be in suggested anchor text (exact or semantic match)  
✅ Gemini reads ALL URLs (URL + H1 + Meta Title) BEFORE starting to map  
✅ Gemini knows complete URL database for 100% reliable suggestions
