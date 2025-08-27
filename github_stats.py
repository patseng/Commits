#!/usr/bin/env python3
"""GitHub API interface and statistics processing"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from urllib.parse import quote
import requests


def load_credentials(filepath: str = ".credentials.json") -> Dict[str, str]:
    """Load GitHub credentials from a JSON file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"{filepath} not found. Please create it with:\n"
            '{"github_token": "your_personal_access_token"}'
        )
    
    with open(filepath, 'r') as f:
        return json.load(f)


def fetch_contributor_stats(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    """
    Fetch contributor statistics from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token
    
    Returns:
        List of contributor statistics
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/contributors"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 202:
        # GitHub is calculating stats, wait and retry
        print("GitHub is calculating statistics, please wait...")
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


def process_statistics(contributors: List[Dict[str, Any]], num_weeks: int = 52) -> Dict[str, List[Dict]]:
    """
    Process contributor statistics into weekly format
    
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


def aggregate_by_week(contributors: List[Dict[str, Any]], num_weeks: int = 52) -> Dict[str, Dict]:
    """
    Aggregate contributor statistics by week
    
    Args:
        contributors: Raw contributor data from GitHub API
        num_weeks: Number of recent weeks to include
    
    Returns:
        Dictionary with week as key and aggregated stats as value
    """
    weekly_aggregates = {}
    
    for contributor in contributors:
        username = contributor['author']['login']
        weeks = contributor['weeks'][-num_weeks:]  # Get last N weeks
        
        for week in weeks:
            week_date = datetime.fromtimestamp(week['w']).strftime('%Y-%m-%d')
            
            if week_date not in weekly_aggregates:
                weekly_aggregates[week_date] = {
                    'total_commits': 0,
                    'total_additions': 0,
                    'total_deletions': 0,
                    'contributors': {},
                    'contributor_count': 0
                }
            
            # Add this contributor's stats to the week
            if week['c'] > 0:  # Only count if there's activity
                weekly_aggregates[week_date]['total_commits'] += week['c']
                weekly_aggregates[week_date]['total_additions'] += week['a']
                weekly_aggregates[week_date]['total_deletions'] += week['d']
                weekly_aggregates[week_date]['contributors'][username] = {
                    'commits': week['c'],
                    'additions': week['a'],
                    'deletions': week['d']
                }
    
    # Calculate derived metrics
    for week_date in weekly_aggregates:
        week_data = weekly_aggregates[week_date]
        week_data['contributor_count'] = len(week_data['contributors'])
        
        # Find top contributor
        if week_data['contributors']:
            top_contributor = max(
                week_data['contributors'].items(),
                key=lambda x: x[1]['commits']
            )
            week_data['top_contributor'] = top_contributor[0]
            week_data['top_contributor_commits'] = top_contributor[1]['commits']
        
        # Calculate average commits per contributor
        if week_data['contributor_count'] > 0:
            week_data['avg_commits_per_contributor'] = round(
                week_data['total_commits'] / week_data['contributor_count'], 2
            )
        else:
            week_data['avg_commits_per_contributor'] = 0
    
    # Remove weeks with no activity
    weekly_aggregates = {k: v for k, v in weekly_aggregates.items() 
                        if v['total_commits'] > 0}
    
    return weekly_aggregates


def calculate_weekly_trends(weekly_aggregates: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calculate trend metrics for weekly performance
    
    Args:
        weekly_aggregates: Dictionary of weekly aggregated statistics
    
    Returns:
        Dictionary containing trend analysis
    """
    if not weekly_aggregates:
        return {}
    
    sorted_weeks = sorted(weekly_aggregates.keys())
    
    # Calculate total metrics
    total_commits = sum(w['total_commits'] for w in weekly_aggregates.values())
    total_additions = sum(w['total_additions'] for w in weekly_aggregates.values())
    total_deletions = sum(w['total_deletions'] for w in weekly_aggregates.values())
    
    # Find peak week
    peak_week = max(weekly_aggregates.items(), 
                   key=lambda x: x[1]['total_commits'])
    
    # Calculate average weekly metrics
    avg_weekly_commits = round(total_commits / len(weekly_aggregates), 2)
    avg_weekly_additions = round(total_additions / len(weekly_aggregates), 2)
    avg_weekly_deletions = round(total_deletions / len(weekly_aggregates), 2)
    
    # Find most consistent contributors
    contributor_weeks = {}
    for week_data in weekly_aggregates.values():
        for contributor in week_data['contributors']:
            if contributor not in contributor_weeks:
                contributor_weeks[contributor] = 0
            contributor_weeks[contributor] += 1
    
    # Sort contributors by consistency (number of weeks active)
    most_consistent = sorted(contributor_weeks.items(), 
                           key=lambda x: x[1], reverse=True)[:5]
    
    # Calculate growth rate (comparing first half to second half)
    if len(sorted_weeks) >= 4:
        mid_point = len(sorted_weeks) // 2
        first_half_commits = sum(
            weekly_aggregates[w]['total_commits'] 
            for w in sorted_weeks[:mid_point]
        )
        second_half_commits = sum(
            weekly_aggregates[w]['total_commits'] 
            for w in sorted_weeks[mid_point:]
        )
        
        if first_half_commits > 0:
            growth_rate = round(
                (second_half_commits - first_half_commits) / first_half_commits, 
                2
            )
        else:
            growth_rate = 0
    else:
        growth_rate = 0
    
    return {
        'period': {
            'start': sorted_weeks[0],
            'end': sorted_weeks[-1],
            'weeks_analyzed': len(weekly_aggregates)
        },
        'totals': {
            'commits': total_commits,
            'additions': total_additions,
            'deletions': total_deletions
        },
        'averages': {
            'weekly_commits': avg_weekly_commits,
            'weekly_additions': avg_weekly_additions,
            'weekly_deletions': avg_weekly_deletions
        },
        'peak_week': {
            'date': peak_week[0],
            'commits': peak_week[1]['total_commits']
        },
        'most_consistent_contributors': [
            {'username': c[0], 'weeks_active': c[1]} 
            for c in most_consistent
        ],
        'commit_growth_rate': growth_rate
    }


def fetch_pull_requests_search(owner: str, repo: str, query: str, token: str) -> List[Dict[str, Any]]:
    """
    Wrapper for GitHub Search API to fetch pull requests
    
    Args:
        owner: Repository owner
        repo: Repository name
        query: Search query string
        token: GitHub personal access token
    
    Returns:
        List of pull request items from search results
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Build the full query including repo context
    full_query = f"repo:{owner}/{repo} {query}"
    encoded_query = quote(full_query)
    
    url = f"https://api.github.com/search/issues?q={encoded_query}&per_page=100"
    
    all_items = []
    page = 1
    
    while True:
        paginated_url = f"{url}&page={page}"
        response = requests.get(paginated_url, headers=headers)
        
        if response.status_code == 403 and 'rate limit' in response.text.lower():
            print("Rate limit reached, waiting 60 seconds...")
            time.sleep(60)
            response = requests.get(paginated_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Warning: Search API returned {response.status_code}")
            break
            
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            break
            
        all_items.extend(items)
        
        # Check if there are more pages
        if 'next' not in response.links:
            break
            
        page += 1
        
        # Respect rate limiting
        time.sleep(1)
    
    return all_items


def get_day_of_week_stats(timestamp: int) -> Dict[str, Any]:
    """
    Convert Unix timestamp to weekday information
    
    Args:
        timestamp: Unix timestamp (in UTC)
    
    Returns:
        Dictionary with day name, weekday number, and formatted date
    """
    if not timestamp:
        return {
            'day_name': 'Unknown',
            'weekday': -1,
            'date': 'Unknown'
        }
    
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return {
        'day_name': days[dt.weekday()],
        'weekday': dt.weekday(),
        'date': dt.strftime('%Y-%m-%d'),
        'week_start': dt.strftime('%Y-%m-%d')  # GitHub weeks start on Sunday
    }