# Changelog

## Version 1.1.0 - 2025-09-30

### Major Improvements: Smart Matching Algorithm

#### What Changed
- **Multiple Results Search**: Now retrieves 5 candidates instead of just 1
- **Best Match Selection**: Uses fuzzy string matching (SequenceMatcher) to find the best business name match
- **Match Score Tracking**: Every result includes a confidence score (0.0 to 1.00)
- **Automatic Warnings**: Alerts when match confidence is low

#### How It Works

1. **Retrieves Multiple Candidates**
   ```
   Query: "Utah Holiday Lighting in Salt Lake City"
   Results: 4 candidates found
   ```

2. **Extracts Business Name from Query**
   ```
   Extracts: "utah holiday lighting" (removes "in Salt Lake City")
   ```

3. **Compares Each Candidate**
   ```
   Candidate: 'christmas light professionals' - Similarity: 0.40
   Candidate: 'christmas light professionals' - Similarity: 0.40
   Candidate: 'utah led lighting' - Similarity: 0.84  ← Best match!
   Candidate: 'brite nites' - Similarity: 0.25
   ```

4. **Selects Best Match**
   ```
   Best match: 'Utah LED Lighting' (score: 0.84)
   ```

#### Match Score Interpretation

| Score Range | Meaning | Status |
|-------------|---------|--------|
| 0.90 - 1.00 | Excellent match | ✅ Confident |
| 0.70 - 0.89 | Good match | ✅ Confident |
| 0.50 - 0.69 | Moderate match | ⚠️ Please verify |
| 0.00 - 0.49 | Poor match | ⚠️ Likely incorrect |

#### Example Results

From our test queries:

| Query | Found | Score | Status |
|-------|-------|-------|--------|
| SLC Christmas Lights | Christmas Light Professionals | 0.65 | ⚠️ Verify - moderate match |
| Utah Holiday Lighting | Utah LED Lighting | 0.84 | ✅ Good match! |
| HighLighting | Prodigy Salon SLC | 0.28 | ⚠️ Low match - hair salon (wrong) |
| Christmas Light Professionals | Christmas Light Professionals | 1.00 | ✅ Perfect match! |

#### Benefits

1. **More Accurate Results**: Finds the best matching business, not just the first result
2. **Transparency**: Match scores let you know confidence level
3. **Warnings**: Automatic alerts for questionable matches
4. **Better Data Quality**: Can filter/sort by match score in CSV

#### Output Changes

**CSV Output** - Added `match_score` column:
```csv
query,place_id,name,rating,user_ratings_total,maps_url,formatted_address,match_score,error
Utah Holiday Lighting in Salt Lake City,...,Utah LED Lighting,5,37,...,0.84,
```

**Markdown Report** - Added:
- Match Score column in summary table
- Match score and warnings in detailed view
- Visual status indicators (✅ / ⚠️)

**Console Output** - Shows:
- Number of candidates found
- Similarity score for each candidate (in verbose mode)
- Match score in results
- Warnings for low-confidence matches

---

## Version 1.0.0 - 2025-09-30

### Initial Release

- Google Places API (new v1) integration
- Text search and place details retrieval
- CSV and text output formats
- Review excerpt extraction
- Comprehensive error handling
- Retry logic with exponential backoff
- Rate limiting support
- Environment variable configuration
- Markdown report generation


