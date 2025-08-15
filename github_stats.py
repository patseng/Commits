#!/usr/bin/env python3
"""GitHub API interface and statistics processing"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
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