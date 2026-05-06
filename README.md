# Job Scraper

A Python script to scrape job listings from multiple websites for entry-level software engineering and IT roles.

## Features

- Scrapes jobs from Indeed, Glassdoor, and Monster
- Searches for multiple relevant queries
- Filters results based on keywords
- Saves results to JSON file
- Prints results to console

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```bash
python job_scraper.py
```

The script will:
1. Search for predefined job queries across multiple sites
2. Filter for relevant entry-level positions
3. Display the first 20 results in the console
4. Save all results to `jobs.json`

## Customization

- Modify the `queries` list in `main()` to change search terms
- Change the `location` variable for location-specific searches
- Adjust filtering keywords in the `filter_jobs()` call
- Increase `pages` parameter for more results (be mindful of rate limits)

## Important Notes

- Web scraping may violate the terms of service of some websites
- This script includes rate limiting to be respectful to servers
- Glassdoor scraping may be less reliable due to dynamic content
- Consider using official APIs when available for production use
- Job site structures may change, requiring updates to the scraping logic

## Output

Results are saved to `jobs.json` with the following structure:
```json
[
  {
    "title": "Entry Level Software Engineer",
    "company": "Tech Company Inc.",
    "location": "San Francisco, CA",
    "link": "https://...",
    "source": "Indeed"
  }
]
```