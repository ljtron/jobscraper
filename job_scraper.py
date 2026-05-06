import requests
import time
import json
import os
from datetime import datetime

class JobScraper:
    def __init__(self, api_key=None):
        """
        Initialize the job scraper with JSearch API credentials.
        
        Args:
            api_key (str): RapidAPI key for JSearch. If not provided, 
                          will try to read from JSEARCH_API_KEY environment variable.
        
        To get a free API key:
        1. Go to https://rapidapi.com/laimoon-laimoon-v1/api/jsearch
        2. Sign up for a free RapidAPI account
        3. Subscribe to JSearch (free tier available)
        4. Copy your API key
        5. Set it as environment variable: export JSEARCH_API_KEY="your_api_key"
        """
        self.api_key = api_key or os.getenv('JSEARCH_API_KEY')
        self.jobs = []
        
        if not self.api_key:
            print("⚠️  Warning: No API key provided!")
            print("Set your JSearch API key to use this scraper.")
            print("Set environment variable: export JSEARCH_API_KEY='your_key'")
        
        self.base_url = 'https://jsearch.p.rapidapi.com/search'
        self.headers = {
            'X-RapidAPI-Key': self.api_key or '',
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }

    def search_jobs(self, query, location='', num_pages=1, results_per_page=10):
        """
        Search for jobs across the entire internet using JSearch API.
        
        Args:
            query (str): Job search query (e.g., 'software engineer', 'IT specialist')
            location (str): Location filter (e.g., 'United States', 'New York', 'Remote')
            num_pages (int): Number of pages to fetch
            results_per_page (int): Results per page (max 10)
        """
        if not self.api_key:
            print("❌ Error: API key not configured. Cannot perform search.")
            return
        
        results_per_page = min(results_per_page, 10)  # API max is 10
        
        for page in range(num_pages):
            params = {
                'query': query,
                'page': page + 1,
                'num_pages': 1,
                'date_posted': 'last_24h'  # Optional: filter recent jobs
            }
            
            # Add location if provided
            if location:
                params['location'] = location
            
            try:
                print(f"🔍 Searching: '{query}'{f' in {location}' if location else ''} (page {page + 1})...")
                response = requests.get(self.base_url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'data' in data:
                    for job in data['data']:
                        job_entry = {
                            'title': job.get('job_title', ''),
                            'company': job.get('employer_name', ''),
                            'location': job.get('job_location', ''),
                            'salary': job.get('job_salary_currency_code', '') + ' ' + str(job.get('job_salary_max', '')) if job.get('job_salary_max') else 'Not specified',
                            'job_type': job.get('job_employment_type', 'Not specified'),
                            'description': job.get('job_description', '')[:500],  # First 500 chars
                            'link': job.get('job_apply_link', ''),
                            'posted_date': job.get('job_posted_at_datetime_utc', ''),
                            'source': 'Internet (JSearch)',
                            'job_id': job.get('job_id', '')
                        }
                        self.jobs.append(job_entry)
                        print(f"  ✓ Found: {job_entry['title']} at {job_entry['company']}")
                else:
                    print(f"  ⚠️  No results found for this page")
                
                # Rate limiting - be respectful to the API
                time.sleep(1)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"  ⚠️  Rate limited. Waiting 30 seconds...")
                    time.sleep(30)
                else:
                    print(f"  ❌ HTTP Error: {e}")
            except Exception as e:
                print(f"  ❌ Error searching page {page + 1}: {e}")

    def filter_jobs(self, keywords=None, exclude_keywords=None, min_salary=None, job_type=None):
        """
        Filter jobs based on keywords, salary, and job type.
        
        Args:
            keywords (list): Keywords to include in search
            exclude_keywords (list): Keywords to exclude
            min_salary (int): Minimum salary (if available)
            job_type (str): Filter by job type (e.g., 'FULLTIME', 'CONTRACT')
        """
        if not keywords and not exclude_keywords and not min_salary and not job_type:
            return self.jobs
        
        filtered = []
        for job in self.jobs:
            title_lower = job['title'].lower()
            company_lower = job['company'].lower()
            description_lower = job['description'].lower()
            text = f"{title_lower} {company_lower} {description_lower}"
            
            include = True
            
            # Check keywords
            if keywords:
                include = any(keyword.lower() in text for keyword in keywords)
            
            # Check exclusions
            if exclude_keywords and include:
                include = not any(excl.lower() in text for excl in exclude_keywords)
            
            # Check job type
            if job_type and include:
                include = job.get('job_type', '').upper() == job_type.upper()
            
            if include:
                filtered.append(job)
        
        return filtered

    def save_to_file(self, filename='jobs.json'):
        """Save jobs to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.jobs)} jobs to {filename}")

    def print_jobs(self, jobs=None, limit=10):
        """Print jobs to console"""
        if jobs is None:
            jobs = self.jobs
        
        for i, job in enumerate(jobs[:limit]):
            print(f"{i+1}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source']}")
            print(f"   Link: {job['link']}")
            print()

def main():
    # Get API key from environment or prompt user
    api_key = os.getenv('JSEARCH_API_KEY')
    
    if not api_key:
        print("\n" + "="*60)
        print("JOB SCRAPER - Internet-Wide Job Search")
        print("="*60)
        print("\n⚠️  API Key Required")
        print("\nTo use this scraper, you need a JSearch API key:")
        print("  1. Go to: https://rapidapi.com/laimoon-laimoon-v1/api/jsearch")
        print("  2. Click 'Subscribe' (free tier available)")
        print("  3. Copy your API key")
        print("  4. Set it: export JSEARCH_API_KEY='your_key_here'")
        print("\nOr provide it directly in the code.")
        print("="*60 + "\n")
        return
    
    scraper = JobScraper(api_key=api_key)
    
    # Search queries for different job types
    search_queries = [
        {
            'query': 'entry level software engineer',
            'location': 'United States',
            'pages': 2
        },
        {
            'query': 'junior developer jobs',
            'location': 'United States',
            'pages': 2
        },
        {
            'query': 'IT specialist entry level',
            'location': 'United States',
            'pages': 1
        },
        {
            'query': 'junior IT roles',
            'location': 'United States',
            'pages': 1
        }
    ]
    
    print("\n" + "="*60)
    print("🔍 SEARCHING THE INTERNET FOR COMPUTER SCIENCE JOBS")
    print("="*60 + "\n")
    
    # Perform searches
    for search in search_queries:
        scraper.search_jobs(
            query=search['query'],
            location=search['location'],
            num_pages=search['pages']
        )
        print()
    
    # Filter for relevant jobs
    print("\n" + "-"*60)
    print("📊 FILTERING RESULTS")
    print("-"*60 + "\n")
    
    relevant_jobs = scraper.filter_jobs(
        keywords=['software', 'engineer', 'developer', 'IT', 'programmer', 'code'],
        exclude_keywords=['senior', 'lead', 'manager', 'director', '10+ years']
    )
    
    print(f"\n✅ Found {len(scraper.jobs)} total jobs")
    print(f"✅ {len(relevant_jobs)} jobs match your criteria\n")
    
    # Display results
    print("="*60)
    print("📋 TOP RESULTS")
    print("="*60 + "\n")
    scraper.print_jobs(relevant_jobs, limit=20)
    
    # Save to file
    print("\n" + "-"*60)
    scraper.save_to_file()
    print("-"*60 + "\n")

if __name__ == '__main__':
    main()