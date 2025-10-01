#!/usr/bin/env python3
"""
Google Places API Lookup Tool
Searches for businesses and retrieves ratings, reviews, and Maps URLs.
Uses the new Google Places API (v1).
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from difflib import SequenceMatcher

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class BusinessInfo:
    """Data class for business information."""
    query: str
    place_id: str
    name: str
    rating: Optional[float]
    user_ratings_total: Optional[int]
    maps_url: str
    formatted_address: Optional[str] = None
    match_score: Optional[float] = None
    error: Optional[str] = None


@dataclass
class Review:
    """Data class for review information."""
    author: str
    rating: int
    relative_time: str
    text: str
    publish_time: Optional[str] = None


class GooglePlacesClient:
    """Client for interacting with Google Places API (new v1)."""
    
    BASE_URL = "https://places.googleapis.com/v1"
    
    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 3):
        """
        Initialize the Google Places API client.
        
        Args:
            api_key: Google Places API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.timeout = timeout
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _get_headers(self, field_mask: Optional[str] = None) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Args:
            field_mask: Optional field mask for filtering response fields
            
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        if field_mask:
            headers["X-Goog-FieldMask"] = field_mask
        return headers
    
    def search_text(self, query: str, page_size: int = 5) -> Optional[Dict]:
        """
        Search for a place using text query.
        
        Args:
            query: Text query (business name + location)
            page_size: Number of results to return (default: 5 for better matching)
            
        Returns:
            API response as dictionary or None if error
        """
        url = f"{self.BASE_URL}/places:searchText"
        payload = {
            "textQuery": query,
            "pageSize": page_size,
            "languageCode": "en"
        }
        headers = self._get_headers(
            field_mask="places.id,places.displayName,places.formattedAddress"
        )
        
        try:
            logger.debug(f"Searching for: {query}")
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching for '{query}': {e}")
            return None
    
    def find_best_match(self, query: str, search_results: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching business from search results based on name similarity.
        
        Args:
            query: Original search query
            search_results: List of place results from search
            
        Returns:
            Tuple of (best_match_place, similarity_score)
        """
        if not search_results:
            return None, 0.0
        
        # Extract the business name from the query (before location info)
        # Common patterns: "Business Name City", "Business Name in City"
        query_lower = query.lower()
        for separator in [' in ', ', ']:
            if separator in query_lower:
                business_name = query_lower.split(separator)[0].strip()
                break
        else:
            # If no separator found, use the whole query minus common location words
            location_words = ['city', 'ut', 'utah', 'slc', 'salt lake city']
            words = query_lower.split()
            business_name = ' '.join(w for w in words if w not in location_words).strip()
        
        logger.debug(f"Extracted business name: '{business_name}' from query: '{query}'")
        
        best_match = None
        best_score = 0.0
        
        for place in search_results:
            place_name = place.get("displayName", {}).get("text", "").lower()
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, business_name, place_name).ratio()
            
            # Also check if business name is contained in place name (substring match)
            if business_name in place_name:
                similarity = max(similarity, 0.8)  # Boost score for substring matches
            
            logger.debug(f"  Candidate: '{place_name}' - Similarity: {similarity:.2f}")
            
            if similarity > best_score:
                best_score = similarity
                best_match = place
        
        if best_match:
            match_name = best_match.get('displayName', {}).get('text', '')
            logger.info(f"Best match: '{match_name}' (score: {best_score:.2f})")
            
            # Warn if match score is low
            if best_score < 0.5:
                logger.warning(f"⚠️  Low match score ({best_score:.2f}) - result may not be accurate")
            elif best_score < 0.7:
                logger.warning(f"⚠️  Moderate match score ({best_score:.2f}) - please verify result")
        
        return best_match, best_score
    
    def get_place_details(self, place_id: str, include_reviews: bool = True) -> Optional[Dict]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Place ID
            include_reviews: Whether to include reviews in response
            
        Returns:
            API response as dictionary or None if error
        """
        # Construct URL - place_id needs "places/" prefix
        url = f"{self.BASE_URL}/places/{place_id}"
        
        # Use GET with query params instead of headers for field mask
        params = {
            "fields": ",".join([
                "id",
                "displayName",
                "rating",
                "userRatingCount",
                "googleMapsUri",
                "formattedAddress"
            ] + (["reviews"] if include_reviews else []))
        }
        
        headers = {
            "X-Goog-Api-Key": self.api_key
        }
        
        try:
            logger.debug(f"Getting details for place_id: {place_id}")
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting details for place_id '{place_id}': {e}")
            return None
    
    def lookup_business(self, query: str, include_reviews: bool = True) -> Tuple[Optional[BusinessInfo], List[Review]]:
        """
        Complete lookup of a business: search + get details + parse reviews.
        
        Args:
            query: Text query (business name + location)
            include_reviews: Whether to fetch and parse reviews
            
        Returns:
            Tuple of (BusinessInfo, List of Review objects)
        """
        # Step 1: Search for the business
        search_response = self.search_text(query)
        
        if not search_response or "places" not in search_response or len(search_response["places"]) == 0:
            logger.warning(f"No results found for: {query}")
            return BusinessInfo(
                query=query,
                place_id="",
                name="",
                rating=None,
                user_ratings_total=None,
                maps_url="",
                error="No match found"
            ), []
        
        # Step 2: Find the best matching business from search results
        all_places = search_response["places"]
        logger.debug(f"Found {len(all_places)} candidates, finding best match...")
        
        best_match, similarity_score = self.find_best_match(query, all_places)
        
        if not best_match:
            logger.warning(f"Could not find good match for: {query}")
            return BusinessInfo(
                query=query,
                place_id="",
                name="",
                rating=None,
                user_ratings_total=None,
                maps_url="",
                error="No good match found"
            ), []
        
        # Extract place_id and name from best match
        place_id = best_match.get("id", "")
        name = best_match.get("displayName", {}).get("text", "Unknown")
        formatted_address = best_match.get("formattedAddress", "")
        
        logger.info(f"Found: {name} (ID: {place_id}, match score: {similarity_score:.2f})")
        
        # Step 3: Get detailed information
        details_response = self.get_place_details(place_id, include_reviews=include_reviews)
        
        if not details_response:
            logger.warning(f"Could not get details for: {name}")
            return BusinessInfo(
                query=query,
                place_id=place_id,
                name=name,
                rating=None,
                user_ratings_total=None,
                maps_url="",
                formatted_address=formatted_address,
                error="Could not retrieve details"
            ), []
        
        # Extract business information
        business_info = BusinessInfo(
            query=query,
            place_id=place_id,
            name=details_response.get("displayName", {}).get("text", name),
            rating=details_response.get("rating"),
            user_ratings_total=details_response.get("userRatingCount"),
            maps_url=details_response.get("googleMapsUri", ""),
            formatted_address=details_response.get("formattedAddress", formatted_address),
            match_score=similarity_score
        )
        
        # Step 4: Parse reviews if available
        reviews = []
        if include_reviews and "reviews" in details_response:
            for review_data in details_response["reviews"]:
                try:
                    author_name = review_data.get("authorAttribution", {}).get("displayName", "Anonymous")
                    rating = review_data.get("rating", 0)
                    relative_time = review_data.get("relativePublishTimeDescription", "")
                    
                    # Try to get text from originalText or text field
                    text = ""
                    if "originalText" in review_data:
                        text = review_data["originalText"].get("text", "")
                    elif "text" in review_data:
                        text = review_data["text"].get("text", "")
                    
                    publish_time = review_data.get("publishTime", "")
                    
                    reviews.append(Review(
                        author=author_name,
                        rating=rating,
                        relative_time=relative_time,
                        text=text,
                        publish_time=publish_time
                    ))
                except Exception as e:
                    logger.warning(f"Error parsing review: {e}")
                    continue
        
        return business_info, reviews


def load_queries_from_file(filename: str) -> List[str]:
    """
    Load queries from a text file (one per line).
    
    Args:
        filename: Path to file containing queries
        
    Returns:
        List of query strings
    """
    queries = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queries.append(line)
        logger.info(f"Loaded {len(queries)} queries from {filename}")
    except Exception as e:
        logger.error(f"Error loading queries from {filename}: {e}")
    return queries


def write_csv_output(businesses: List[BusinessInfo], output_file: str):
    """
    Write business information to CSV file.
    
    Args:
        businesses: List of BusinessInfo objects
        output_file: Path to output CSV file
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['query', 'place_id', 'name', 'rating', 'user_ratings_total', 'maps_url', 'formatted_address', 'match_score', 'error']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for business in businesses:
                writer.writerow(asdict(business))
        
        logger.info(f"CSV output written to: {output_file}")
    except Exception as e:
        logger.error(f"Error writing CSV output: {e}")


def write_reviews_output(all_reviews: Dict[str, List[Review]], output_file: str):
    """
    Write reviews to a text file.
    
    Args:
        all_reviews: Dictionary mapping business names to lists of reviews
        output_file: Path to output text file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RECENT REVIEWS\n")
            f.write("=" * 80 + "\n\n")
            f.write("NOTE: Google's API does not provide access to all reviews.\n")
            f.write("Only a small, non-paginated set (~5 reviews) is returned.\n\n")
            
            for business_name, reviews in all_reviews.items():
                f.write(f"\n{'=' * 80}\n")
                f.write(f"Business: {business_name}\n")
                f.write(f"{'=' * 80}\n\n")
                
                if not reviews:
                    f.write("No reviews available.\n\n")
                    continue
                
                for i, review in enumerate(reviews, 1):
                    stars = "★" * review.rating
                    f.write(f"Review #{i}:\n")
                    f.write(f"  Author: {review.author}\n")
                    f.write(f"  Rating: {stars} ({review.rating}/5)\n")
                    f.write(f"  Time: {review.relative_time}\n")
                    if review.text:
                        # Truncate long reviews for readability
                        text = review.text[:500] + "..." if len(review.text) > 500 else review.text
                        f.write(f"  Review: {text}\n")
                    f.write("\n")
        
        logger.info(f"Reviews written to: {output_file}")
    except Exception as e:
        logger.error(f"Error writing reviews output: {e}")


def write_markdown_output(businesses: List[BusinessInfo], all_reviews: Dict[str, List[Review]], output_file: str):
    """
    Write business information and reviews to a Markdown file.
    
    Args:
        businesses: List of BusinessInfo objects
        all_reviews: Dictionary mapping business names to lists of reviews
        output_file: Path to output Markdown file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Google Places Business Lookup Results\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            
            # Summary table
            f.write("## Summary\n\n")
            successful = sum(1 for b in businesses if not b.error)
            f.write(f"- **Total Queries:** {len(businesses)}\n")
            f.write(f"- **Successful:** {successful}\n")
            f.write(f"- **Failed:** {len(businesses) - successful}\n\n")
            
            # Business overview table
            f.write("## Business Overview\n\n")
            f.write("| Business | Rating | Reviews | Match Score | Status |\n")
            f.write("|----------|--------|---------|-------------|--------|\n")
            
            for business in businesses:
                if business.error:
                    f.write(f"| {business.query} | - | - | - | ❌ {business.error} |\n")
                else:
                    rating_stars = "⭐" * int(business.rating) if business.rating else ""
                    match_score_str = f"{business.match_score:.2f}" if business.match_score else "N/A"
                    
                    # Add warning indicator for low match scores
                    status = "✅"
                    if business.match_score and business.match_score < 0.5:
                        status = "⚠️ Low Match"
                    elif business.match_score and business.match_score < 0.7:
                        status = "⚠️ Verify"
                    
                    f.write(f"| {business.name} | {rating_stars} {business.rating}/5 | {business.user_ratings_total:,} | {match_score_str} | {status} |\n")
            
            f.write("\n---\n\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            
            for i, business in enumerate(businesses, 1):
                f.write(f"### {i}. {business.name if business.name else business.query}\n\n")
                
                if business.error:
                    f.write(f"**Status:** ❌ {business.error}\n\n")
                    f.write(f"**Query:** `{business.query}`\n\n")
                    continue
                
                # Business details
                f.write(f"**Query:** `{business.query}`\n\n")
                
                # Show match score warning if needed
                if business.match_score:
                    if business.match_score < 0.5:
                        f.write(f"⚠️ **Warning:** Low match score ({business.match_score:.2f}) - This may not be the correct business\n\n")
                    elif business.match_score < 0.7:
                        f.write(f"⚠️ **Note:** Moderate match score ({business.match_score:.2f}) - Please verify this is the correct business\n\n")
                    f.write(f"**Match Score:** {business.match_score:.2f}/1.00\n\n")
                
                rating_stars = "⭐" * int(business.rating) if business.rating else ""
                f.write(f"**Rating:** {rating_stars} **{business.rating}/5** ({business.user_ratings_total:,} reviews)\n\n")
                
                if business.formatted_address:
                    f.write(f"**Address:** {business.formatted_address}\n\n")
                
                f.write(f"**Google Maps:** [View on Maps]({business.maps_url})\n\n")
                
                if business.place_id:
                    f.write(f"**Place ID:** `{business.place_id}`\n\n")
                
                # Reviews
                reviews = all_reviews.get(business.name, [])
                if reviews:
                    f.write(f"#### Recent Reviews ({len(reviews)})\n\n")
                    f.write("*Note: Google's API returns only a limited set of reviews (~5). Full review export is not available.*\n\n")
                    
                    for j, review in enumerate(reviews, 1):
                        stars = "⭐" * review.rating
                        f.write(f"**Review {j}** by **{review.author}**\n\n")
                        f.write(f"{stars} **{review.rating}/5** • *{review.relative_time}*\n\n")
                        
                        if review.text:
                            # Truncate very long reviews
                            text = review.text[:500] + "..." if len(review.text) > 500 else review.text
                            # Escape markdown special characters in review text
                            text = text.replace('|', '\\|')
                            f.write(f"> {text}\n\n")
                
                f.write("---\n\n")
            
            # Footer
            f.write("## Notes\n\n")
            f.write("- This report was generated using the Google Places API (new v1)\n")
            f.write("- Review data is limited to what the API provides (typically ~5 reviews per business)\n")
            f.write("- Ratings and review counts are current as of the generation date\n")
            f.write("- Click the Google Maps links to view full business listings\n")
        
        logger.info(f"Markdown output written to: {output_file}")
    except Exception as e:
        logger.error(f"Error writing markdown output: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Look up business information using Google Places API (new v1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use queries from command line
  %(prog)s "SLC Christmas Lights Salt Lake City" "Utah Holiday Lighting SLC"
  
  # Use queries from a file
  %(prog)s --queries-file businesses.txt
  
  # Specify custom output files
  %(prog)s --output results.csv --reviews reviews.txt "Business Name City"
  
  # Set API key via command line (not recommended for security)
  %(prog)s --api-key YOUR_KEY "Business Name City"
  
Environment Variables:
  GOOGLE_PLACES_API_KEY: Your Google Places API key (recommended method)
        """
    )
    
    parser.add_argument(
        'queries',
        nargs='*',
        help='Business queries (name + location). Use quotes for multi-word queries.'
    )
    parser.add_argument(
        '--api-key',
        help='Google Places API key (overrides env var)'
    )
    parser.add_argument(
        '--queries-file',
        help='File containing queries (one per line)'
    )
    parser.add_argument(
        '--output',
        default='business_results.csv',
        help='Output CSV file for business data (default: business_results.csv)'
    )
    parser.add_argument(
        '--reviews',
        default='reviews.txt',
        help='Output text file for reviews (default: reviews.txt)'
    )
    parser.add_argument(
        '--markdown',
        help='Output markdown file (optional, generates formatted report)'
    )
    parser.add_argument(
        '--no-reviews',
        action='store_true',
        help='Skip fetching reviews'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Get API key
    api_key = args.api_key or os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logger.error("Error: No API key provided.")
        logger.error("Set GOOGLE_PLACES_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Collect queries
    queries = []
    if args.queries:
        queries.extend(args.queries)
    if args.queries_file:
        queries.extend(load_queries_from_file(args.queries_file))
    
    if not queries:
        logger.error("Error: No queries provided.")
        logger.error("Provide queries as arguments or use --queries-file")
        parser.print_help()
        sys.exit(1)
    
    logger.info(f"Processing {len(queries)} queries...")
    
    # Initialize client
    client = GooglePlacesClient(api_key, timeout=args.timeout)
    
    # Process each query
    businesses = []
    all_reviews = {}
    
    for i, query in enumerate(queries, 1):
        logger.info(f"\n[{i}/{len(queries)}] Processing: {query}")
        
        business_info, reviews = client.lookup_business(
            query,
            include_reviews=not args.no_reviews
        )
        
        businesses.append(business_info)
        
        if reviews:
            all_reviews[business_info.name] = reviews
            logger.info(f"  → Found {len(reviews)} reviews")
        
        # Add delay between requests to be respectful to the API
        if i < len(queries):
            time.sleep(args.delay)
    
    # Write outputs
    logger.info("\nWriting results...")
    write_csv_output(businesses, args.output)
    
    if not args.no_reviews and all_reviews:
        write_reviews_output(all_reviews, args.reviews)
    
    if args.markdown:
        write_markdown_output(businesses, all_reviews, args.markdown)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    successful = sum(1 for b in businesses if not b.error)
    logger.info(f"Total queries: {len(queries)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(queries) - successful}")
    logger.info(f"\nResults saved to:")
    logger.info(f"  Business data: {args.output}")
    if not args.no_reviews:
        logger.info(f"  Reviews: {args.reviews}")
    if args.markdown:
        logger.info(f"  Markdown report: {args.markdown}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

