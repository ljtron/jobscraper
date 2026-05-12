import requests
import time
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from MongoDriver import MongoDBClient

class CSJobScraper:
    def __init__(self):
        """Initialize the CS/IT job scraper using free sources."""
        self.jobs = []
        self.mongo_client = MongoDBClient()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def job_entry(self, title, company, location, salary, job_type, description, link, posted_date, source):
        """Helper function to create a standardized job entry."""
        return {
            'title': title,
            'company': company,
            'location': location,
            'salary': salary,
            'job_type': job_type,
            'description': description,  # Limit description to 500 chars
            'link': link,
            'posted_date': posted_date,
            'source': source,
            'applied': False,
            'applied_date': None,
            'notes': ''
        }
    
    def search_remit(self, query='software developer'):
        """
        Search using Remotive's free API (no API key needed).
        Filters for US-based or remote US-eligible jobs.
        """
        print(f"🔍 Searching Remotive for '{query}'...")
        try:
            url = f'https://remotive.com/api/remote-jobs?search={query.replace(" ", "+")}'
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            if 'jobs' in data:
                count = 0
                for job in data['jobs']:
                    location = job.get('candidate_required_location', '')

                    # Filter for US locations only
                    if location and ('United States' in location or 'USA' in location or 'US' in location or 'Remote' in location):
                        job_entry = self.job_entry(
                            title=job.get('title', ''),
                            company=job.get('company_name', ''),
                            location=location if location else 'Remote (US)',
                            salary='Not specified',
                            job_type=job.get('job_type', 'Remote'),
                            description=BeautifulSoup(job.get('description', ''), 'html.parser').get_text()[:500],
                            link=job.get('url', ''),
                            posted_date=job.get('publication_date', ''),
                            source='Remotive'
                        )
                        self.jobs.append(job_entry)
                        count += 1
                        print(f"  ✓ Found: {job_entry['title']} at {job_entry['company']}")

                print(f"  📊 Found {count} US-eligible jobs")
            else:
                print(f"  ⚠️  No results from Remotive")

        except Exception as e:
            print(f"  ❌ Error searching Remotive: {e}")

    def search_usajobs(self, query='Computer Science'):
        """
        Search using USAJOBS API for government IT/CS positions.
        Get a free API key at: https://developer.usajobs.gov/
        """
        print(f"🔍 Searching USAJOBS for '{query}'...")
        try:
            api_key = os.getenv('USAJOBS_API_KEY')
            
            headers = {
                'User-Agent': 'Job Scraper (your-email@example.com)',
                'Accept': 'application/json',
                'Host': 'data.usajobs.gov'
            }
            
            if api_key:
                headers['Authorization-Key'] = api_key

            url = 'https://data.usajobs.gov/api/search'
            params = {
                'Keyword': query,
                'ResultsPerPage': 50,
                'Country': 'US'
            }

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 401:
                print(f"  ⚠️  USAJOBS requires a free API key")
                print(f"  📝 Get one at: https://developer.usajobs.gov/")
                print(f"  💡 Then run: export USAJOBS_API_KEY='your_key'")
                return

            response.raise_for_status()
            data = response.json()

            if 'SearchResult' in data:
                results = data['SearchResult'].get('SearchResultItems', [])
                count = 0
                for job in results[:50]:
                    job_data = job.get('MatchedObjectsDescriptor', {})
                    position = job_data.get('PositionTitle', '')
                    agency = job_data.get('AgencyName', '')
                    loc = job_data.get('PositionLocationDisplay', '')

                    if not loc:
                        locs = job_data.get('PositionLocations', [])
                        if locs:
                            loc = locs[0].get('LocationName', '')

                    link = job_data.get('ApplyURI', [{}])[0].get('Value', '') if job_data.get('ApplyURI') else ''
                    
                    salary_info = job_data.get('PositionCompensation', {})
                    if isinstance(salary_info, dict):
                        salary_min = salary_info.get('RangeMinimum', '')
                        salary_max = salary_info.get('RangeMaximum', '')
                        salary = f'${salary_min} - ${salary_max}' if salary_min and salary_max else 'Not specified'
                    else:
                        salary = 'Not specified'

                    job_entry = self.job_entry(
                        title=position,
                        company=agency,
                        location=loc,
                        salary=salary,
                        job_type=job_data.get('PositionSchedule', 'Full-time'),
                        description=job_data.get('PositionDescription', '')[:500],
                        link=link,
                        posted_date=job_data.get('PositionStartDate', ''),
                        source='USAJOBS'
                    )
                    self.jobs.append(job_entry)
                    count += 1

                print(f"  📊 Found {count} jobs from USAJOBS")
            else:
                print(f"  ⚠️  No results from USAJOBS")

        except Exception as e:
            print(f"  ❌ Error searching USAJOBS: {e}")

    def search_yc_startups(self):
        """
        Search Y Combinator's Work at a Startup for startup developer jobs.
        Uses the main jobs page and company-specific job pages since
        role-specific pages (/jobs/role/{role}) return 404.
        """
        print("🔍 Searching YC Work at a Startup...")
        try:
            url = 'https://www.ycombinator.com/jobs'
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('li', class_=re.compile(r'my-2.*flex'))

            count = 0
            for job in job_cards:
                title_tag = job.find('a', class_=re.compile(r'text-linkColor'))
                company_link = job.find('a', href=re.compile(r'/companies/[^/]+/jobs'))
                if not title_tag or not company_link:
                    continue

                title = title_tag.get_text(strip=True)
                company_path = company_link.get('href', '')
                company = company_path.split('/')[2].replace('-', ' ').title() if company_path else ''

                full_link = f'https://www.ycombinator.com{title_tag.get("href", "")}' if title_tag.get("href") else ''

                # Extract salary
                divs = job.find_all('div', class_='whitespace-nowrap')
                salary = 'Not specified'
                job_type = 'Not specified'
                for d in divs:
                    t = d.get_text(strip=True)
                    if '$' in t or 'K' in t:
                        salary = t
                    elif t in ['Full-time', 'Part-time', 'Contract', 'Internship']:
                        job_type = t

                # Extract location
                location_div = job.find('div', class_='break-all')
                location = location_div.get_text(strip=True) if location_div else ''

                # Filter for US only
                if location and not any(x in location.lower() for x in ['us', 'united states', 'remote', 'san francisco', 'new york', 'los angeles', 'boston', 'seattle', 'denver', 'chicago', 'austin', 'miami']):
                    continue

                job_entry = self.job_entry(
                    title=title,
                    company=company,
                    location=location if location else 'US',
                    salary=salary,
                    job_type=job_type,
                    description=f'{title} at {company} - YC backed startup',
                    link=full_link,
                    posted_date='',
                    source='YC Work at a Startup'
                )
                self.jobs.append(job_entry)
                count += 1
                print(f"  ✓ Found: {title} at {company}")

            print(f"  📊 Found {count} jobs")

        except Exception as e:
            print(f"  ❌ Error searching YC Startups: {e}")

    def search_github_jobs(self, query='software'):
        """
        Search using GitHub Jobs (via archived dataset mirror).
        Alternative free source for tech jobs.
        """
        print(f"🔍 Searching for '{query}' jobs...")
        try:
            # Using a working tech job API
            url = f'https://pythonprogramming.herokuapp.com/jobs?q={query}&location=US'
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                count = 0
                if isinstance(data, list):
                    for job in data[:50]:
                        job_entry = self.job_entry(
                            title=job.get('title', ''),
                            company=job.get('company', ''),
                            location=job.get('location', 'US'),
                            salary=job.get('salary', 'Not specified'),
                            job_type=job.get('type', 'Not specified'),
                            description=str(job.get('description', ''))[:500],
                            link=job.get('url', ''),
                            posted_date=job.get('posted_at', ''),
                            source='TechJobs'
                        )
                        self.jobs.append(job_entry)
                        count += 1

                print(f"  📊 Found {count} jobs")
            else:
                print(f"  ⚠️  No results")

        except Exception as e:
            print(f"  ❌ Error searching: {e}")

    def search_all_cs_it_jobs(self):
        """
        Search all sources for CS/IT jobs in America only.
        """
        queries = [
            'software developer',
            'software engineer',
            'computer science',
            'IT specialist',
            'systems administrator',
            'network engineer',
            'data analyst',
            'web developer',
            'devops',
            'cybersecurity',
            'help desk',
            'database administrator',
            'cloud engineer',
            'machine learning',
            'frontend developer',
            'backend developer',
            'full stack developer',
            'mobile developer',
            'QA engineer',
            'technical support'
        ]

        # Remotive searches (filters for US)
        print("\n" + "="*60)
        print("🔍 SEARCHING REMOTIVE (US-Eligible Remote Jobs)")
        print("="*60 + "\n")

        for query in queries[:5]:
            self.search_remit(query)
            time.sleep(1)
            print()

        # USAJOBS searches (US only by default)
        print("\n" + "="*60)
        print("🔍 SEARCHING USAJOBS (US Government Positions)")
        print("="*60 + "\n")

        for query in ['Computer Science', 'Information Technology', 'Software Engineering', 'Cybersecurity']:
            self.search_usajobs(query)
            time.sleep(1)
            print()

        # YC Work at a Startup searches (startup jobs)
        print("\n" + "="*60)
        print("🔍 SEARCHING YC WORK AT A STARTUP (Startup Jobs)")
        print("="*60 + "\n")

        self.search_yc_startups()
        print()

        # Additional tech job searches
        print("\n" + "="*60)
        print("🔍 SEARCHING TECH JOBS (US)")
        print("="*60 + "\n")

        for query in ['software', 'developer', 'IT']:
            self.search_github_jobs(query)
            time.sleep(1)
            print()

    def filter_us_only(self):
        """Filter jobs to only include US-based positions."""
        us_jobs = []
        for job in self.jobs:
            location = job.get('location', '').lower()
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            text = f"{location} {title} {description}"

            # USAJOBS and YC are US-only by default
            if job['source'] in ['USAJOBS', 'YC Work at a Startup']:
                us_jobs.append(job)
                continue

            # Check for US indicators
            us_indicators = ['united states', 'usa', 'us', 'america', 'remote', 'us-']
            state_codes = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
                          'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
                          'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
                          'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
                          'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy',
                          'dc', 'new york', 'california', 'texas', 'florida', 'chicago',
                          'seattle', 'boston', 'san francisco', 'los angeles', 'denver']

            if any(indicator in location for indicator in us_indicators):
                us_jobs.append(job)
            elif any(state in location for state in state_codes):
                us_jobs.append(job)

        self.jobs = us_jobs
        return us_jobs

    def filter_jobs(self, keywords=None, exclude_keywords=None, source=None):
        """
        Filter jobs based on keywords and exclusions.
        """
        if not keywords and not exclude_keywords and not source:
            return self.jobs

        filtered = []
        for job in self.jobs:
            title_lower = job['title'].lower()
            company_lower = job['company'].lower()
            description_lower = job['description'].lower()
            text = f"{title_lower} {company_lower} {description_lower}"

            include = True

            if keywords:
                include = any(keyword.lower() in text for keyword in keywords)

            if exclude_keywords and include:
                include = not any(excl.lower() in text for excl in exclude_keywords)

            if source and include:
                include = job['source'] == source

            if include:
                filtered.append(job)

        return filtered

    def remove_duplicates(self):
        """Remove duplicate jobs based on title + company."""
        seen = set()
        unique_jobs = []
        for job in self.jobs:
            key = f"{job['title'].lower()}|{job['company'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        self.jobs = unique_jobs
        return self.jobs

    def save_to_file(self, filename='jobs.json'):
        """Save jobs to JSON file"""
        with open(filename, 'a', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.jobs)} jobs to {filename}")

    def print_jobs(self, jobs=None, limit=20):
        """Print jobs to console"""
        if jobs is None:
            jobs = self.jobs

        if not jobs:
            print("No jobs found.")
            return

        for i, job in enumerate(jobs[:limit]):
            print(f"{i+1}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source']}")
            if job['salary'] != 'Not specified':
                print(f"   Salary: {job['salary']}")
            print(f"   Link: {job['link']}")
            print()

def main():
    print("\n" + "="*60)
    print("🔍 CS/IT JOB SCRAPER - US Only")
    print("="*60 + "\n")

    scraper = CSJobScraper()

    print("Searching for CS/IT jobs in America...")
    print("⏱️  This may take a minute or two.\n")

    # Run all searches
    scraper.search_all_cs_it_jobs()

    # Filter for US only
    print("\n" + "-"*60)
    print("🇺🇸 FILTERING FOR US JOBS ONLY")
    print("-"*60)
    before = len(scraper.jobs)
    scraper.filter_us_only()
    print(f"Kept {len(scraper.jobs)} US jobs (filtered out {before - len(scraper.jobs)})")

    # Remove duplicates
    print("\n" + "-"*60)
    print("🧹 REMOVING DUPLICATES")
    print("-"*60)
    before = len(scraper.jobs)
    scraper.remove_duplicates()
    print(f"Removed {before - len(scraper.jobs)} duplicates")

    # Filter for CS/IT jobs
    print("\n" + "-"*60)
    print("📊 FILTERING RESULTS")
    print("-"*60 + "\n")

    cs_it_keywords = [
        'software', 'developer', 'engineer', 'computer', 'IT',
        'programmer', 'analyst', 'systems', 'network', 'data',
        'web', 'devops', 'security', 'database', 'cloud',
        'machine learning', 'AI', 'frontend', 'backend', 'full stack',
        'mobile', 'QA', 'technical', 'support', 'administrator'
    ]

    relevant_jobs = scraper.filter_jobs(keywords=cs_it_keywords)

    print(f"\n✅ Found {len(scraper.jobs)} total US jobs")
    print(f"✅ {len(relevant_jobs)} jobs match CS/IT criteria\n")

    # Display results
    print("="*60)
    print("📋 TOP 20 RESULTS")
    print("="*60 + "\n")
    scraper.print_jobs(relevant_jobs, limit=20)

    # Save to file
    print("\n" + "-"*60)
    scraper.save_to_file()
    print("-"*60 + "\n")

if __name__ == '__main__':
    main()
