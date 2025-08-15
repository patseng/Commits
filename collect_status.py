#!/usr/bin/env python3
"""
GitHub Contributors Statistics Fetcher
Uses GitHub API to fetch contributor statistics for a repository
"""

import json
import os
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any

def load_credentials(filepath: str = ".credentials.json") -> Dict[str, str]:
    """Load GitHub credentials from a JSON file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"{filepath} not found. Please create it with:\n"
            '{"github_token": "your_personal_access_token"}'
        )
    
    with open(filepath, 'r') as f:
        return json.load(f)

def get_contributor_stats(owner: str, repo: str, token: str, weeks: int = 52) -> List[Dict[str, Any]]:
    """
    Fetch contributor statistics from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token
        weeks: Number of weeks to fetch (default: 52)
    
    Returns:
        List of contributor statistics
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get contributor statistics
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 202:
        # GitHub is calculating stats, wait and retry
        print("GitHub is calculating statistics, please wait...")
        import time
        retries = 5
        for i in range(retries):
            time.sleep(3)
            response = requests.get(url, headers=headers)
            if response.status_code != 202:
                break
            print(f"Still calculating... retry {i+1}/{retries}")
    
    if response.status_code == 404:
        raise Exception(f"Repository {owner}/{repo} not found. Please check the repository name and ensure it's public or you have access.")
    elif response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")
    
    return response.json()

def parse_weekly_stats(contributors: List[Dict[str, Any]], num_weeks: int = 52) -> Dict[str, List[Dict]]:
    """
    Parse contributor statistics into weekly format
    
    Args:
        contributors: Raw contributor data from GitHub API
        num_weeks: Number of recent weeks to include
    
    Returns:
        Dictionary mapping usernames to their weekly statistics
    """
    weekly_stats = {}
    
    for contributor in contributors:
        username = contributor['author']['login']
        weeks = contributor['weeks'][-num_weeks:]  # Get last N weeks
        
        weekly_data = []
        for week in weeks:
            # Convert timestamp to readable date
            week_date = datetime.fromtimestamp(week['w']).strftime('%Y-%m-%d')
            
            # Only include weeks with activity
            if week['c'] > 0:
                weekly_data.append({
                    'week': week_date,
                    'commits': week['c'],
                    'additions': week['a'],
                    'deletions': week['d']
                })
        
        if weekly_data:  # Only include users with activity
            weekly_stats[username] = weekly_data
    
    return weekly_stats

def save_to_csv(stats: Dict[str, List[Dict]], filename: str = "contributor_stats.csv"):
    """Save statistics to CSV file"""
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['username', 'week', 'commits', 'additions', 'deletions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for username, weeks in stats.items():
            for week in weeks:
                writer.writerow({
                    'username': username,
                    **week
                })
    
    print(f"Statistics saved to {filename}")

def main():
    """Main function"""
    # Configuration - Update these with your target repository
    OWNER = "Open-CA"
    REPO = "iOS-Open"  # Using an actual Open-CA repository
    WEEKS_TO_FETCH = 26  # About 6 months
    
    try:
        # Load credentials
        creds = load_credentials(".credentials.json")
        token = creds.get("github_token")
        
        if not token:
            raise ValueError("github_token not found in credentials file")
        
        print(f"Fetching contributor statistics for {OWNER}/{REPO}...")
        
        # Fetch statistics
        contributors = get_contributor_stats(OWNER, REPO, token, WEEKS_TO_FETCH)
        
        # Parse weekly statistics
        weekly_stats = parse_weekly_stats(contributors, WEEKS_TO_FETCH)
        
        # Display summary
        print(f"\nFound {len(weekly_stats)} contributors with activity in the last {WEEKS_TO_FETCH} weeks\n")
        
        for username, weeks in weekly_stats.items():
            total_commits = sum(w['commits'] for w in weeks)
            total_additions = sum(w['additions'] for w in weeks)
            total_deletions = sum(w['deletions'] for w in weeks)
            
            print(f"{username}:")
            print(f"  Total commits: {total_commits}")
            print(f"  Total additions: {total_additions}")
            print(f"  Total deletions: {total_deletions}")
            print(f"  Active weeks: {len(weeks)}")
            print()
        
        # Save to CSV
        save_to_csv(weekly_stats)
        
        # Also save as JSON for easier processing
        with open("contributor_stats.json", "w") as f:
            json.dump(weekly_stats, f, indent=2)
        print("Statistics also saved to contributor_stats.json")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease create a .credentials.json file with your GitHub personal access token:")
        print('{"github_token": "your_token_here"}')
        print("\nYou can create a token at: https://github.com/settings/tokens")
        print("Required scopes: repo (for private repos) or public_repo (for public repos)")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())