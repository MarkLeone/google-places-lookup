# Usage Examples

This document provides practical examples for using the Google Places API lookup tool.

## Basic Examples

### 1. Quick Start (Default Queries)
```bash
./run.sh
```
Uses queries from `queries.txt` and outputs to `business_results.csv` and `reviews.txt`.

### 2. Single Business Lookup
```bash
./run.sh "Starbucks Seattle WA"
```

### 3. Multiple Businesses
```bash
./run.sh "Starbucks Seattle" "Blue Bottle Coffee Portland" "Philz Coffee San Francisco"
```

## Advanced Examples

### 4. Custom Query File
```bash
# Create a custom query file
cat > my_businesses.txt << 'EOF'
Ace Hardware Denver CO
Home Depot Boulder CO
Lowes Fort Collins CO
EOF

# Run with custom file
./run.sh --queries-file my_businesses.txt
```

### 5. Custom Output Files
```bash
./run.sh \
    --queries-file queries.txt \
    --output my_results.csv \
    --reviews my_reviews.txt
```

### 5b. Generate Markdown Report (NEW!)
```bash
# Beautiful formatted report perfect for sharing
./run.sh --queries-file queries.txt --markdown business_report.md

# Generate all formats
./run.sh \
    --queries-file queries.txt \
    --output results.csv \
    --reviews reviews.txt \
    --markdown report.md
```

### 6. Skip Reviews (Faster)
```bash
./run.sh --no-reviews "Business Name City"
```

### 7. Verbose Mode (Debugging)
```bash
./run.sh --verbose "Business Name City"
```

### 8. Adjust Rate Limiting
```bash
# Slower, more respectful to API (1 second delay)
./run.sh --delay 1.0 --queries-file queries.txt

# Faster (but may hit rate limits)
./run.sh --delay 0.1 --queries-file queries.txt
```

### 9. Longer Timeout for Slow Connections
```bash
./run.sh --timeout 30 "Business Name City"
```

## Query Best Practices

### Good Queries
```bash
# Format: "Business Name City State"
./run.sh "Pike Place Market Seattle WA"

# Format: "Business Name + Full Address"
./run.sh "1600 Pennsylvania Ave NW Washington DC"

# Format: "Business Name + ZIP"
./run.sh "Central Park New York 10024"
```

### Better Results with Specific Addresses
```bash
# Less specific (may return wrong business)
./run.sh "Joe's Pizza"

# More specific (better results)
./run.sh "Joe's Pizza New York NY"

# Most specific (best results)
./run.sh "Joe's Pizza 7 Carmine St New York NY"
```

## Working with Output

### 10. View CSV in Terminal
```bash
column -t -s, business_results.csv | less -S
```

### 11. Import to Excel/Google Sheets
```bash
# CSV file can be directly opened in:
# - Microsoft Excel
# - Google Sheets
# - LibreOffice Calc
```

### 12. Extract Specific Columns
```bash
# Get just names and ratings
cut -d',' -f3,4 business_results.csv
```

### 13. Filter High-Rated Businesses
```bash
# Businesses with rating >= 4.5
awk -F',' '$4 >= 4.5' business_results.csv
```

### 14. Count Successful vs Failed Queries
```bash
# Count successes (no error)
grep -v "error" business_results.csv | wc -l

# Count failures (has error)
grep -c "No match" business_results.csv
```

## Integration Examples

### 15. Process Results with Python
```python
import csv

with open('business_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if float(row['rating'] or 0) >= 4.5:
            print(f"{row['name']}: {row['rating']} stars ({row['user_ratings_total']} reviews)")
            print(f"  {row['maps_url']}\n")
```

### 16. Export to JSON
```bash
python3 << 'PYTHON'
import csv, json

with open('business_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = list(reader)

with open('business_results.json', 'w') as f:
    json.dump(data, f, indent=2)
print("Converted to JSON")
PYTHON
```

### 17. Send Results via Email (with mailx)
```bash
mail -s "Business Lookup Results" your@email.com < business_results.csv
```

### 18. Schedule Regular Updates with Cron
```bash
# Edit crontab
crontab -e

# Add line to run every Monday at 9 AM
0 9 * * 1 cd /home/mleone/src/google-places-api && ./run.sh --output weekly_results.csv
```

## Troubleshooting Examples

### 19. Test API Key
```bash
./run.sh "Starbucks Seattle" --verbose
# Look for "Found:" in output
```

### 20. Debug No Results
```bash
# Try more specific query
./run.sh --verbose "SLC Christmas Lights 805 E 18th Ave Salt Lake City"

# Check API key is set
echo $GOOGLE_PLACES_API_KEY
```

### 21. Handle Special Characters in Business Names
```bash
# Use quotes to escape
./run.sh "O'Reilly's Pub Boston MA"
./run.sh "Café Amélie New Orleans LA"
```

## Batch Processing Examples

### 22. Process Large List (with Progress)
```bash
# Create large query file
cat > big_list.txt << 'EOF'
Business 1
Business 2
...
Business 100
EOF

# Process with delay to avoid rate limits
./run.sh --queries-file big_list.txt --delay 1.0 --verbose
```

### 23. Split Processing Across Multiple Runs
```bash
# Split file into chunks
split -l 20 big_list.txt chunk_

# Process each chunk
for chunk in chunk_*; do
    echo "Processing $chunk..."
    ./run.sh --queries-file "$chunk" \
        --output "results_${chunk}.csv" \
        --reviews "reviews_${chunk}.txt"
    sleep 5  # Pause between batches
done

# Combine results
cat results_chunk_*.csv > all_results.csv
```

## API Key Management Examples

### 24. Use Different API Key Temporarily
```bash
GOOGLE_PLACES_API_KEY="your_other_key" ./run.sh "Business Name"
```

### 25. Multiple Projects with Different Keys
```bash
# Project 1
export GOOGLE_PLACES_API_KEY="key_for_project1"
./run.sh --queries-file project1_queries.txt --output project1_results.csv

# Project 2
export GOOGLE_PLACES_API_KEY="key_for_project2"
./run.sh --queries-file project2_queries.txt --output project2_results.csv
```

## Real-World Use Cases

### 26. Competitor Analysis
```bash
cat > competitors.txt << 'EOF'
Competitor 1 Location
Competitor 2 Location
Competitor 3 Location
Our Business Location
EOF

./run.sh --queries-file competitors.txt --output competitor_analysis.csv
```

### 27. Location Expansion Research
```bash
cat > potential_locations.txt << 'EOF'
Our Brand Name Los Angeles CA
Our Brand Name Chicago IL
Our Brand Name Miami FL
EOF

./run.sh --queries-file potential_locations.txt --no-reviews
```

### 28. Franchise Quality Check
```bash
cat > franchise_locations.txt << 'EOF'
Franchise Location 1
Franchise Location 2
Franchise Location 3
EOF

./run.sh --queries-file franchise_locations.txt
# Review ratings and recent reviews for each location
```

## Tips for Best Results

1. **Be Specific**: Include city and state/country
2. **Use Full Names**: Avoid abbreviations when possible
3. **Add Addresses**: For service-area businesses
4. **Verify Results**: Check Maps URLs to ensure correct business
5. **Respect Rate Limits**: Use `--delay` for large batches
6. **Save Queries**: Keep query files for repeat runs
7. **Check Logs**: Use `--verbose` when troubleshooting

## Command Reference

```bash
# Full syntax
python google_places_lookup.py [OPTIONS] [QUERIES...]

# Common options
--queries-file FILE     # Input file with queries
--output FILE          # CSV output file
--reviews FILE         # Reviews output file
--no-reviews          # Skip review fetching
--delay SECONDS       # Delay between requests
--timeout SECONDS     # Request timeout
--verbose             # Show debug information
--api-key KEY         # Override API key
```

## Getting Help

```bash
# Show all options
python google_places_lookup.py --help

# Or
./run.sh --help
```

