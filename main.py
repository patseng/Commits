#!/usr/bin/env python3
"""
GitHub Contributors Statistics Fetcher
Main entry point for fetching and exporting contributor statistics
"""

import argparse
from github_stats import (
    load_credentials, 
    fetch_contributor_stats, 
    process_statistics,
    aggregate_by_week,
    calculate_weekly_trends
)
from exporters import export_all, export_weekly_stats


def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Fetch and analyze GitHub contributor statistics')
    parser.add_argument('--owner', default='Open-CA', help='Repository owner (default: Open-CA)')
    parser.add_argument('--repo', default='iOS-Open', help='Repository name (default: iOS-Open)')
    parser.add_argument('--weeks', type=int, default=26, help='Number of weeks to analyze (default: 26)')
    parser.add_argument('--view', choices=['user', 'week', 'both'], default='both',
                       help='View type: user-centric, week-centric, or both (default: both)')
    parser.add_argument('--format', choices=['console', 'csv', 'json', 'all'], default='all',
                       help='Export format(s) (default: all)')
    parser.add_argument('--chart', action='store_true',
                       help='Generate line chart of last N weeks')
    parser.add_argument('--chart-weeks', type=int, default=6,
                       help='Number of weeks to chart (default: 6)')
    parser.add_argument('--exclude-authors', nargs='+',
                       default=['o-p-e-n-ios', 'openEngBot'],
                       help='Authors to exclude from visualization')
    
    args = parser.parse_args()
    
    # Configuration from arguments
    OWNER = args.owner
    REPO = args.repo
    WEEKS_TO_FETCH = args.weeks
    
    try:
        # Load credentials
        creds = load_credentials(".credentials.json")
        token = creds.get("github_token")
        
        if not token:
            raise ValueError("github_token not found in credentials file")
        
        print(f"Fetching contributor statistics for {OWNER}/{REPO}...")
        print(f"Analyzing last {WEEKS_TO_FETCH} weeks of data...")
        
        # Fetch statistics from GitHub
        contributors = fetch_contributor_stats(OWNER, REPO, token)
        
        # Process based on selected view
        if args.view in ['user', 'both']:
            # Process user-centric statistics
            weekly_stats = process_statistics(contributors, WEEKS_TO_FETCH)
            
            # Export user-centric data
            if args.view == 'user':
                print("\n" + "=" * 60)
                print("User-Centric View")
                print("=" * 60)
            export_all(weekly_stats, WEEKS_TO_FETCH)
        
        if args.view in ['week', 'both']:
            # Process week-centric statistics
            weekly_aggregates = aggregate_by_week(contributors, WEEKS_TO_FETCH)
            trends = calculate_weekly_trends(weekly_aggregates)
            
            # Export weekly aggregated data
            if args.view == 'both':
                print("\n" + "=" * 60)
                print("Week-Centric View")
                print("=" * 60)
            export_weekly_stats(weekly_aggregates, trends, args.format)
        
        # Generate chart if requested
        if args.chart:
            print("\n" + "=" * 60)
            print("Generating Commit Activity Chart")
            print("=" * 60)
            try:
                from visualizer import generate_commit_line_chart, generate_console_table
                
                # Load existing stats if we didn't fetch them
                if args.view not in ['user', 'both']:
                    weekly_stats = process_statistics(contributors, WEEKS_TO_FETCH)
                
                # Generate console table
                generate_console_table(weekly_stats, 
                                     weeks=args.chart_weeks,
                                     exclude_authors=args.exclude_authors)
                
                # Try to generate chart
                try:
                    generate_commit_line_chart(weekly_stats,
                                             weeks=args.chart_weeks,
                                             exclude_authors=args.exclude_authors)
                except ImportError:
                    print("Note: Matplotlib not installed. Install with: pip install matplotlib")
                    print("Showing console table only.")
            except ImportError:
                print("Error: visualizer module not found")
        
        print("\nStatistics processing complete!")
        
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