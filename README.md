# Google Places API Lookup Tool

A robust Python script for looking up business information using the Google Places API (new v1). Retrieves ratings, review counts, Google Maps URLs, and recent review excerpts.

## Quick Start

```bash
# 1. Run setup (creates venv, installs dependencies, sets up API key)
./setup_env.sh

# 2. Run the script with default queries
./run.sh

# Or with custom queries
./run.sh "Business Name City" "Another Business Location"

# Generate a markdown report (great for sharing!)
./run.sh --markdown report.md
```

That's it! Results will be in `business_results.csv` and `reviews.txt` (and optionally `report.md`).

## Features

- ✅ Uses the **new Google Places API (v1)** with modern endpoints
- ✅ Searches businesses by name and location
- ✅ Retrieves ratings, review counts, and Maps URLs
- ✅ Extracts recent review excerpts (with API limitations noted)
- ✅ Exports results to CSV format
- ✅ Robust error handling and retry logic
- ✅ Rate limiting to respect API quotas
- ✅ Environment variable support for API keys (secure)
- ✅ Flexible input: command-line arguments or file-based queries
- ✅ Comprehensive logging

## Installation

1. **Clone or navigate to this directory:**
   ```bash
   cd /path/to/google-places-api
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   
   **Option A: Environment variable (recommended)**
   ```bash
   # Create a .env file
   cp .env.example .env
   # Edit .env and add your API key
   nano .env
   
   # Then export it
   export GOOGLE_PLACES_API_KEY="your_api_key_here"
   ```
   
   **Option B: Command-line argument**
   ```bash
   python google_places_lookup.py --api-key "your_api_key_here" "Business Name City"
   ```

## Usage

### Basic Usage

**Single query:**
```bash
python google_places_lookup.py "SLC Christmas Lights Salt Lake City"
```

**Multiple queries:**
```bash
python google_places_lookup.py \
    "SLC Christmas Lights Salt Lake City" \
    "Utah Holiday Lighting Salt Lake City" \
    "HighLighting Salt Lake City"
```

**From a file:**
```bash
python google_places_lookup.py --queries-file queries.txt
```

### Advanced Options

```bash
python google_places_lookup.py \
    --queries-file queries.txt \
    --output my_results.csv \
    --reviews my_reviews.txt \
    --markdown report.md \
    --delay 1.0 \
    --verbose
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `queries` | Business queries (use quotes for multi-word) | None |
| `--api-key` | Google Places API key (overrides env var) | From `GOOGLE_PLACES_API_KEY` |
| `--queries-file` | File with queries (one per line) | None |
| `--output` | Output CSV file for business data | `business_results.csv` |
| `--reviews` | Output text file for reviews | `reviews.txt` |
| `--markdown` | Output markdown file (formatted report) | None (optional) |
| `--no-reviews` | Skip fetching reviews | False |
| `--timeout` | Request timeout in seconds | 10 |
| `--delay` | Delay between requests in seconds | 0.5 |
| `--verbose` | Enable verbose logging | False |

## Output Format

### CSV Output (business_results.csv)
Contains the following columns:
- `query`: Original search query
- `place_id`: Google Place ID
- `name`: Business name
- `rating`: Average rating (e.g., 4.8)
- `user_ratings_total`: Total number of reviews
- `maps_url`: Google Maps URL
- `formatted_address`: Business address
- `error`: Error message (if any)

### Reviews Output (reviews.txt)
Contains formatted review excerpts with:
- Author name
- Star rating
- Relative publish time
- Review text (truncated if very long)

### Markdown Report (optional, use --markdown flag)
Beautiful formatted report with:
- Summary table with ratings overview
- Detailed business information cards
- Formatted reviews with star ratings
- Clickable Google Maps links
- Perfect for sharing or viewing in GitHub/IDEs

## Important API Limitations

⚠️ **Review Access is Limited**: Google's Places API does not provide access to all reviews. The API returns only a small, non-paginated set (typically ~5 reviews). This is a limitation of the API itself, not this script. Full review export is not possible without scraping (which violates Google's terms of service).

## Query Tips

For best results:
- Use format: `"Business Name City"` or `"Business Name Full Address"`
- For service-area businesses, try variations:
  - `"Business Name + ZIP code"`
  - `"Business Name + Phone number"`
  - `"Business Name + State"`

## API Key Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable the **Places API (New)**
4. Create credentials → API Key
5. Restrict the key (recommended):
   - API restrictions: Places API (New)
   - Application restrictions: IP addresses or referrer URLs

## Comparison with Shell Script

This Python script improves upon `xmas-lights.sh` with:

- **Better error handling**: Graceful degradation on failures
- **Retry logic**: Automatic retries on transient errors
- **Type safety**: Using dataclasses and type hints
- **Security**: Environment variable support for API keys
- **Flexibility**: Multiple input methods and output options
- **Logging**: Comprehensive progress and error logging
- **Rate limiting**: Built-in delays to respect API quotas
- **Maintainability**: Well-structured, documented code

## Example Workflow

```bash
# 1. Set up environment
export GOOGLE_PLACES_API_KEY="your_key_here"

# 2. Create or edit queries file
cat > queries.txt << EOF
SLC Christmas Lights Salt Lake City
Utah Holiday Lighting Salt Lake City
HighLighting Salt Lake City
Christmas Light Professionals Salt Lake City
EOF

# 3. Run the script
python google_places_lookup.py --queries-file queries.txt --verbose

# 4. Check results
cat business_results.csv
cat reviews.txt
```

## Troubleshooting

**"No API key provided" error:**
- Make sure you've set the `GOOGLE_PLACES_API_KEY` environment variable
- Or use the `--api-key` argument

**"No results found" for a business:**
- Try alternative query formats
- Verify the business exists on Google Maps
- Check the business name spelling

**API quota errors:**
- Increase the `--delay` value
- Check your API quota in Google Cloud Console

**Import errors:**
- Make sure you've run `pip install -r requirements.txt`

## License

This tool is provided as-is for personal and commercial use. Make sure to comply with Google's Places API Terms of Service.

