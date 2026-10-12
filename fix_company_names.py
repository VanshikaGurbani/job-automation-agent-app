"""
Fix Company Names in scraped_jobs.csv
Extracts company names from job URLs and descriptions
"""
import pandas as pd
import re
from bs4 import BeautifulSoup


def extract_company_from_description(description):
    """Try to extract company name from job description"""
    if pd.isna(description) or not description:
        return None
    
    # Common patterns for company mentions
    patterns = [
        r"(?:at|@)\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+is|\s+we|\.|,)",
        r"Join\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+as|\s+team|\!)",
        r"([A-Z][A-Za-z0-9\s&\.]+?)\s+is\s+(?:looking|seeking|hiring)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description[:500])
        if match:
            company = match.group(1).strip()
            # Filter out common false positives
            if len(company) > 2 and company not in ['We', 'Our', 'The', 'This']:
                return company
    
    return None


def extract_company_from_title(title):
    """Try to extract company from title if it contains company info"""
    if pd.isna(title) or not title:
        return None
    
    # Sometimes titles include company name after a dash or pipe
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            potential_company = parts[-1].strip()
            if len(potential_company) < 50 and potential_company[0].isupper():
                return potential_company
    
    return None


def fix_csv(input_file='scraped_jobs.csv', output_file='scraped_jobs_fixed.csv'):
    """Fix company names in the CSV"""
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Total jobs: {len(df)}")
    
    # Count N/A companies
    na_count = df['company'].isna().sum() + (df['company'] == 'N/A').sum()
    print(f"Jobs with N/A company: {na_count}")
    
    if na_count == 0:
        print("No companies to fix!")
        return
    
    fixed_count = 0
    
    # Try to fix N/A companies
    for idx, row in df.iterrows():
        if pd.isna(row['company']) or row['company'] == 'N/A':
            # Try extracting from title first
            company = extract_company_from_title(row['title'])
            
            # Try extracting from description
            if not company:
                company = extract_company_from_description(row['description'])
            
            if company:
                df.at[idx, 'company'] = company
                fixed_count += 1
                print(f"  Fixed: {row['title'][:50]}... -> {company}")
    
    print(f"\n✓ Fixed {fixed_count} company names")
    print(f"✓ Saving to {output_file}...")
    
    df.to_csv(output_file, index=False)
    print(f"✓ Done! Use {output_file} in the app.")
    
    # Show summary
    remaining_na = df['company'].isna().sum() + (df['company'] == 'N/A').sum()
    print(f"\nSummary:")
    print(f"  Original N/A: {na_count}")
    print(f"  Fixed: {fixed_count}")
    print(f"  Remaining N/A: {remaining_na}")


if __name__ == "__main__":
    fix_csv()

