#!/usr/bin/env python3
"""
Pull Request Metrics Module

This module provides functionality to fetch and analyze GitHub pull request
metrics using the GitHub Search API. It supports fetching PRs opened, merged,
and reviewed by users within specified date ranges.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import urllib.parse


class PRMetrics:
    """
    A class for fetching and analyzing GitHub pull request metrics.
    
    This class interfaces with the GitHub Search API to retrieve PR statistics
    including opened, merged, and reviewed pull requests, with support for
    date range filtering and day-of-week aggregation.
    """
    
    # API Configuration
    SEARCH_BASE = "https://api.github.com/search/issues"
    PER_PAGE = 100  # Maximum allowed by GitHub API
    
    # Query templates for different PR metrics
    QUERIES = {
        "opened": "repo:{owner}/{repo} type:pr author:{user} created:{start}..{end}",
        "merged": "repo:{owner}/{repo} type:pr is:merged merged:{start}..{end}",
        "reviewed": "repo:{owner}/{repo} type:pr reviewed-by:{user}"
    }
    
    def __init__(self, token: str):
        """
        Initialize the PRMetrics instance with GitHub authentication.
        
        Args:
            token: GitHub personal access token for API authentication
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_search_request(self, query: str, page: int = 1) -> Dict:
        """
        Make a search request to GitHub API with rate limiting and error handling.
        
        Args:
            query: The search query string
            page: Page number for pagination (default: 1)
            
        Returns:
            JSON response from the API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        params = {
            "q": query,
            "per_page": self.PER_PAGE,
            "page": page,
            "sort": "created",
            "order": "desc"
        }
        
        # Encode the query properly
        url = f"{self.SEARCH_BASE}?{urllib.parse.urlencode(params, safe=':/')}"
        
        # Make the request with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(self.SEARCH_BASE, params=params)
                
                # Handle rate limiting
                if response.status_code == 403:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    if reset_time:
                        sleep_time = max(reset_time - int(time.time()), 0) + 1
                        print(f"Rate limited. Waiting {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        continue
                
                # Handle other non-success status codes
                if response.status_code == 422:
                    # Validation failed, likely bad query
                    return {"items": [], "total_count": 0}
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
        
        return {"items": [], "total_count": 0}
    
    def _paginate_results(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Paginate through all search results for a given query.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to fetch (None for all)
            
        Returns:
            List of all items from paginated results
        """
        all_items = []
        page = 1
        
        while True:
            response = self._make_search_request(query, page)
            items = response.get("items", [])
            total_count = response.get("total_count", 0)
            
            if not items:
                break
                
            all_items.extend(items)
            
            # Check if we've fetched enough results
            if max_results and len(all_items) >= max_results:
                all_items = all_items[:max_results]
                break
            
            # Check if we've fetched all available results
            if len(all_items) >= total_count:
                break
            
            # GitHub API limits to 1000 results for search
            if len(all_items) >= 1000:
                print(f"Warning: GitHub API limits search results to 1000. Got {total_count} total.")
                break
            
            page += 1
            time.sleep(0.5)  # Be nice to the API
        
        return all_items
    
    def get_prs_opened(self, owner: str, repo: str, username: str, 
                       date_range: Optional[Tuple[str, str]] = None) -> List[Dict]:
        """
        Get pull requests opened by a specific user.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username of the PR author
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            List of PR data dictionaries
        """
        if date_range:
            start, end = date_range
        else:
            # Default to last 90 days
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        query = self.QUERIES["opened"].format(
            owner=owner, repo=repo, user=username, start=start, end=end
        )
        
        return self._paginate_results(query)
    
    def get_prs_merged(self, owner: str, repo: str, username: str = None,
                       date_range: Optional[Tuple[str, str]] = None) -> List[Dict]:
        """
        Get pull requests merged within a date range.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: Optional GitHub username to filter by author
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            List of PR data dictionaries
        """
        if date_range:
            start, end = date_range
        else:
            # Default to last 90 days
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        # Build query with optional author filter
        if username:
            query = f"repo:{owner}/{repo} type:pr is:merged author:{username} merged:{start}..{end}"
        else:
            query = self.QUERIES["merged"].format(
                owner=owner, repo=repo, user="", start=start, end=end
            ).replace(" author:", "")  # Remove empty author clause
        
        return self._paginate_results(query)
    
    def get_prs_reviewed(self, owner: str, repo: str, username: str,
                         date_range: Optional[Tuple[str, str]] = None) -> List[Dict]:
        """
        Get pull requests reviewed by a specific user.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username of the reviewer
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            List of PR data dictionaries
        """
        query = self.QUERIES["reviewed"].format(
            owner=owner, repo=repo, user=username
        )
        
        # Add date range to query if provided
        if date_range:
            start, end = date_range
            query += f" created:{start}..{end}"
        
        return self._paginate_results(query)
    
    def aggregate_by_day_of_week(self, prs: List[Dict], 
                                 date_field: str = "created_at") -> Dict[str, int]:
        """
        Aggregate pull requests by day of the week.
        
        Args:
            prs: List of PR data dictionaries
            date_field: Which date field to use for aggregation 
                       (created_at, closed_at, merged_at, etc.)
            
        Returns:
            Dictionary mapping day names to PR counts
        """
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                "Friday", "Saturday", "Sunday"]
        day_counts = {day: 0 for day in days}
        
        for pr in prs:
            # Get the relevant date field
            date_str = pr.get(date_field)
            if not date_str:
                continue
            
            # Parse the date and get day of week
            try:
                date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                day_name = days[date.weekday()]
                day_counts[day_name] += 1
            except (ValueError, IndexError):
                continue
        
        return day_counts
    
    def get_pr_events_by_day(self, owner: str, repo: str, username: str,
                            event_type: str = "opened",
                            date_range: Optional[Tuple[str, str]] = None) -> Dict[str, int]:
        """
        Get PR events aggregated by day of week for a specific event type.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username
            event_type: Type of event (opened, merged, reviewed)
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping day names to event counts
        """
        # Fetch PRs based on event type
        if event_type == "opened":
            prs = self.get_prs_opened(owner, repo, username, date_range)
            date_field = "created_at"
        elif event_type == "merged":
            prs = self.get_prs_merged(owner, repo, username, date_range)
            date_field = "closed_at"  # merged PRs have closed_at timestamp
        elif event_type == "reviewed":
            prs = self.get_prs_reviewed(owner, repo, username, date_range)
            date_field = "created_at"
        else:
            raise ValueError(f"Invalid event_type: {event_type}")
        
        return self.aggregate_by_day_of_week(prs, date_field)
    
    def get_user_pr_summary(self, owner: str, repo: str, username: str,
                           date_range: Optional[Tuple[str, str]] = None) -> Dict:
        """
        Get a comprehensive summary of PR metrics for a user.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            Dictionary containing PR metrics summary
        """
        summary = {
            "username": username,
            "repository": f"{owner}/{repo}",
            "date_range": date_range or "last_90_days",
            "metrics": {
                "total_opened": 0,
                "total_merged": 0,
                "total_reviewed": 0,
                "by_day_of_week": {
                    "opened": {},
                    "merged": {},
                    "reviewed": {}
                }
            }
        }
        
        # Fetch PR data
        opened_prs = self.get_prs_opened(owner, repo, username, date_range)
        merged_prs = self.get_prs_merged(owner, repo, username, date_range)
        reviewed_prs = self.get_prs_reviewed(owner, repo, username, date_range)
        
        # Calculate totals
        summary["metrics"]["total_opened"] = len(opened_prs)
        summary["metrics"]["total_merged"] = len(merged_prs)
        summary["metrics"]["total_reviewed"] = len(reviewed_prs)
        
        # Aggregate by day of week
        summary["metrics"]["by_day_of_week"]["opened"] = self.aggregate_by_day_of_week(
            opened_prs, "created_at"
        )
        summary["metrics"]["by_day_of_week"]["merged"] = self.aggregate_by_day_of_week(
            merged_prs, "closed_at"
        )
        summary["metrics"]["by_day_of_week"]["reviewed"] = self.aggregate_by_day_of_week(
            reviewed_prs, "created_at"
        )
        
        return summary
    
    def check_rate_limit(self) -> Dict:
        """
        Check the current rate limit status for the authenticated user.
        
        Returns:
            Dictionary containing rate limit information
        """
        response = self.session.get("https://api.github.com/rate_limit")
        response.raise_for_status()
        
        data = response.json()
        search_limit = data.get("resources", {}).get("search", {})
        
        return {
            "limit": search_limit.get("limit", 0),
            "remaining": search_limit.get("remaining", 0),
            "reset": datetime.fromtimestamp(search_limit.get("reset", 0)).strftime("%Y-%m-%d %H:%M:%S")
        }


def main():
    """
    Example usage and testing of the PRMetrics module.
    """
    import json
    import os
    
    # Load credentials
    creds_file = ".credentials.json"
    if not os.path.exists(creds_file):
        print(f"Error: {creds_file} not found. Please create it with your GitHub token.")
        return
    
    with open(creds_file, 'r') as f:
        credentials = json.load(f)
    
    token = credentials.get("github_token")
    if not token:
        print("Error: github_token not found in credentials file.")
        return
    
    # Initialize PRMetrics
    pr_metrics = PRMetrics(token)
    
    # Example: Get PR summary for a user
    owner = "Open-CA"
    repo = "iOS-Open"
    username = "brianaronowitzopen"
    
    # Check rate limit first
    rate_limit = pr_metrics.check_rate_limit()
    print(f"Rate Limit Status: {rate_limit['remaining']}/{rate_limit['limit']} (resets at {rate_limit['reset']})")
    
    # Get last 30 days of data
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    date_range = (start_date, end_date)
    
    print(f"\nFetching PR metrics for {username} in {owner}/{repo}")
    print(f"Date range: {start_date} to {end_date}")
    
    # Get comprehensive summary
    summary = pr_metrics.get_user_pr_summary(owner, repo, username, date_range)
    
    print(f"\nPR Metrics Summary:")
    print(f"Total PRs Opened: {summary['metrics']['total_opened']}")
    print(f"Total PRs Merged: {summary['metrics']['total_merged']}")
    print(f"Total PRs Reviewed: {summary['metrics']['total_reviewed']}")
    
    print(f"\nPRs Opened by Day of Week:")
    for day, count in summary['metrics']['by_day_of_week']['opened'].items():
        print(f"  {day}: {count}")
    
    # Save results to file
    output_file = f"pr_metrics_{username}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()