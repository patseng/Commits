#!/usr/bin/env python3
"""
GitHub Contributors Statistics Fetcher
Main entry point for fetching and exporting contributor statistics
"""

from github_stats import load_credentials, fetch_contributor_stats, process_statistics
from exporters import export_all


def main():
    """Main function"""
    # Configuration - Update these with your target repository
    OWNER = "Open-CA"
    REPO = "iOS-Open"
    WEEKS_TO_FETCH = 26  # About 6 months
    
    try:
        # Load credentials
        creds = load_credentials(".credentials.json")
        token = creds.get("github_token")
        
        if not token:
            raise ValueError("github_token not found in credentials file")
        
        print(f"Fetching contributor statistics for {OWNER}/{REPO}...")
        
        # Fetch statistics from GitHub
        contributors = fetch_contributor_stats(OWNER, REPO, token)
        
        # Process the statistics
        weekly_stats = process_statistics(contributors, WEEKS_TO_FETCH)
        
        # Export in all formats
        export_all(weekly_stats, WEEKS_TO_FETCH)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease create a .credentials.json file with your GitHub personal access token:")
        print('{"github_token": "your_token_here"}')
        print("\nYou can create a token at: https://github.com/settings/tokens")
        print("Required scopes: repo (for private repos) or public_repo (for public repos)")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())