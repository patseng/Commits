#!/usr/bin/env python3
"""Weekly Performance Analyzer - Core statistics module for commit and line statistics by day of week"""

import json
import csv
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from pathlib import Path

import github_stats
from author_mapper import AuthorMapper
from pr_metrics import PRMetrics


class WeeklyPerformanceAnalyzer:
    """Analyzes GitHub contributor statistics by day of week"""
    
    def __init__(self, owner: str, repos: List[str], token: str):
        """
        Initialize the analyzer
        
        Args:
            owner: GitHub organization or user
            repos: List of repository names
            token: GitHub personal access token
        """
        self.owner = owner
        self.repos = repos
        self.token = token
        
    def fetch_weekly_commits(self, repo: str, username: Optional[str] = None, num_weeks: int = 52) -> List[Dict[str, Any]]:
        """
        Fetch weekly commit statistics for a repository
        
        Args:
            repo: Repository name
            username: Optional specific username to filter by
            num_weeks: Number of recent weeks to include
            
        Returns:
            List of weekly statistics with commits, additions, deletions
        """
        stats = github_stats.fetch_contributor_stats(self.owner, repo, self.token)
        
        if username:
            # Filter for specific user
            for contributor in stats:
                if contributor.get('author', {}).get('login') == username:
                    # Get only the last N weeks
                    weeks = contributor.get('weeks', [])
                    return weeks[-num_weeks:] if num_weeks else weeks
            return []
        
        # Return all contributors' weekly data
        all_weeks = []
        for contributor in stats:
            author = contributor.get('author', {})
            author_login = author.get('login', 'unknown') if author else 'unknown'
            
            # Get only the last N weeks for this contributor
            weeks = contributor.get('weeks', [])
            recent_weeks = weeks[-num_weeks:] if num_weeks else weeks
            
            for week in recent_weeks:
                week_with_author = week.copy()
                week_with_author['author'] = author_login
                all_weeks.append(week_with_author)
                
        return all_weeks
    
    def aggregate_by_day_of_week(self, stats: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Aggregate statistics by day of week
        
        Args:
            stats: List of weekly statistics with 'w' (week timestamp) and metrics
            
        Returns:
            Dictionary mapping day names to aggregated statistics
        """
        # Initialize aggregation structure
        day_stats = {
            'Monday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Tuesday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Wednesday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Thursday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Friday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Saturday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Sunday': {'commits': 0, 'additions': 0, 'deletions': 0}
        }
        
        for week_data in stats:
            # Convert Unix timestamp to day of week
            day_name = self.get_day_name(week_data.get('w', 0))
            
            # GitHub stats show weekly totals starting on Sunday
            # For now, attribute all activity to the week's starting day
            # In a more sophisticated version, we'd need daily breakdown
            if day_name:
                day_stats[day_name]['commits'] += week_data.get('c', 0)
                day_stats[day_name]['additions'] += week_data.get('a', 0)
                day_stats[day_name]['deletions'] += week_data.get('d', 0)
                
        return day_stats
    
    @staticmethod
    def get_day_name(timestamp: int) -> str:
        """
        Convert Unix timestamp to day name (UTC)
        
        Args:
            timestamp: Unix timestamp (in UTC)
            
        Returns:
            Day name (e.g., "Monday", "Tuesday")
        """
        if not timestamp:
            return "Unknown"
            
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[dt.weekday()]
    
    @staticmethod
    def get_day_of_week_stats(timestamp: int) -> Tuple[str, int]:
        """
        Get day name and weekday number from timestamp (UTC)
        
        Args:
            timestamp: Unix timestamp (in UTC)
            
        Returns:
            Tuple of (day_name, weekday_number)
        """
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[dt.weekday()], dt.weekday()
    
    def analyze_all_repos(self, num_weeks: int = 52) -> Dict[str, Any]:
        """
        Analyze all configured repositories
        
        Args:
            num_weeks: Number of recent weeks to analyze
            
        Returns:
            Combined statistics for all repositories
        """
        combined_stats = defaultdict(lambda: defaultdict(lambda: {'commits': 0, 'additions': 0, 'deletions': 0}))
        
        for repo in self.repos:
            print(f"Fetching statistics for {self.owner}/{repo}...")
            weekly_stats = self.fetch_weekly_commits(repo, num_weeks=num_weeks)
            
            # Group by author first
            for week in weekly_stats:
                author = week.get('author', 'unknown')
                day_name = self.get_day_name(week.get('w', 0))
                
                if day_name != "Unknown":
                    combined_stats[author][day_name]['commits'] += week.get('c', 0)
                    combined_stats[author][day_name]['additions'] += week.get('a', 0)
                    combined_stats[author][day_name]['deletions'] += week.get('d', 0)
        
        return dict(combined_stats)
    
    def generate_day_breakdown(self, author_stats: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Generate a breakdown by day of week for a specific author
        
        Args:
            author_stats: Statistics for a specific author
            
        Returns:
            Day-of-week breakdown
        """
        day_totals = {
            'Monday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Tuesday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Wednesday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Thursday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Friday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Saturday': {'commits': 0, 'additions': 0, 'deletions': 0},
            'Sunday': {'commits': 0, 'additions': 0, 'deletions': 0}
        }
        
        for day, metrics in author_stats.items():
            if day in day_totals:
                day_totals[day] = metrics
                
        return day_totals


def analyze_weekly_performance(owner: str, repos: List[str], aliases_file: str = "author_aliases.json", 
                              date_range: Optional[Tuple[str, str]] = None, token: Optional[str] = None,
                              num_weeks: int = 52):
    """
    Main orchestration function for weekly performance analysis
    
    Args:
        owner: GitHub organization or user
        repos: List of repository names
        aliases_file: Path to author aliases JSON file
        date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
        token: GitHub personal access token (loads from credentials if not provided)
        num_weeks: Number of recent weeks to analyze
    
    Returns:
        Combined performance statistics organized by author and day of week
    """
    # Load credentials if token not provided
    if not token:
        credentials = github_stats.load_credentials()
        token = credentials['github_token']
    
    # Step 1: Initialize modules
    mapper = AuthorMapper(aliases_file)
    pr_metrics = PRMetrics(token)
    analyzer = WeeklyPerformanceAnalyzer(owner, repos, token)
    
    # Step 2: Fetch commit data for all repos
    print(f"Fetching commit statistics for last {num_weeks} weeks...")
    all_stats = {}
    
    for repo in repos:
        print(f"  Processing {owner}/{repo}...")
        weekly_stats = analyzer.fetch_weekly_commits(repo, num_weeks=num_weeks)
        
        # Group by author
        for week in weekly_stats:
            author = week.get('author', 'unknown')
            canonical_author = mapper.get_canonical_name(author)
            
            if canonical_author not in all_stats:
                all_stats[canonical_author] = {
                    'commits_by_day': defaultdict(lambda: {'commits': 0, 'additions': 0, 'deletions': 0}),
                    'pr_metrics': {'opened': 0, 'merged': 0, 'reviewed': 0},
                    'total_commits': 0,
                    'total_additions': 0,
                    'total_deletions': 0,
                    'aliases': set()
                }
            
            all_stats[canonical_author]['aliases'].add(author)
            
            # Aggregate by day of week
            day_name = analyzer.get_day_name(week.get('w', 0))
            if day_name != "Unknown":
                all_stats[canonical_author]['commits_by_day'][day_name]['commits'] += week.get('c', 0)
                all_stats[canonical_author]['commits_by_day'][day_name]['additions'] += week.get('a', 0)
                all_stats[canonical_author]['commits_by_day'][day_name]['deletions'] += week.get('d', 0)
                
                all_stats[canonical_author]['total_commits'] += week.get('c', 0)
                all_stats[canonical_author]['total_additions'] += week.get('a', 0)
                all_stats[canonical_author]['total_deletions'] += week.get('d', 0)
    
    # Step 3: Fetch PR metrics
    # If no date_range provided, calculate based on num_weeks
    if not date_range:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(weeks=num_weeks)).strftime('%Y-%m-%d')
        date_range = (start_date, end_date)
    else:
        start_date, end_date = date_range
    
    print(f"\nFetching PR metrics from {start_date} to {end_date}...")
    
    # Limit PR fetching to avoid timeout - only fetch for top contributors
    sorted_by_commits = sorted(all_stats.items(), key=lambda x: x[1]['total_commits'], reverse=True)
    top_contributors = sorted_by_commits[:5]  # Fetch PRs for top 5 contributors only to avoid timeout
    
    for canonical_author, author_data in top_contributors:
        # Skip bot accounts
        if canonical_author.lower() in ['o-p-e-n-ios', 'openengbot', 'bot', 'github-actions[bot]', 'claude[bot]']:
            continue
            
        for alias in author_data['aliases']:
            for repo in repos:
                try:
                    print(f"  Getting PRs for {alias} in {repo}...")
                    
                    # Get PRs opened
                    prs_opened = pr_metrics.get_prs_opened(owner, repo, alias, date_range)
                    author_data['pr_metrics']['opened'] += len(prs_opened)
                    
                    # Get PRs merged with author filter
                    prs_merged = pr_metrics.get_prs_merged(owner, repo, alias, date_range)
                    author_data['pr_metrics']['merged'] += len(prs_merged)
                    
                    # Get PRs reviewed (skip for efficiency if needed)
                    # PRs reviewed can be slower as it searches across all PRs
                    if author_data['pr_metrics']['opened'] > 0 or author_data['pr_metrics']['merged'] > 0:
                        prs_reviewed = pr_metrics.get_prs_reviewed(owner, repo, alias, date_range)
                        author_data['pr_metrics']['reviewed'] += len(prs_reviewed)
                    
                except Exception as e:
                    print(f"    Warning: Could not fetch PR metrics for {alias}: {str(e)}")
                    continue
    
    # Step 4: Generate performance table
    return generate_performance_table(all_stats)


def generate_performance_table(grouped_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a structured performance table from grouped statistics
    
    Args:
        grouped_stats: Statistics grouped by canonical author
    
    Returns:
        Formatted performance table data
    """
    performance_table = {
        'summary': {
            'total_authors': len(grouped_stats),
            'total_commits': sum(s['total_commits'] for s in grouped_stats.values()),
            'total_additions': sum(s['total_additions'] for s in grouped_stats.values()),
            'total_deletions': sum(s['total_deletions'] for s in grouped_stats.values())
        },
        'by_author': {},
        'by_day': defaultdict(lambda: {'commits': 0, 'additions': 0, 'deletions': 0})
    }
    
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for author, stats in grouped_stats.items():
        # Skip bot accounts
        if author.lower() in ['o-p-e-n-ios', 'openengbot', 'bot']:
            continue
        
        author_summary = {
            'total_commits': stats['total_commits'],
            'total_additions': stats['total_additions'],
            'total_deletions': stats['total_deletions'],
            'aliases': list(stats['aliases']),
            'by_day': {}
        }
        
        # Add PR metrics if available
        if stats['pr_metrics']['opened'] > 0 or stats['pr_metrics']['merged'] > 0:
            author_summary['pr_metrics'] = stats['pr_metrics']
        
        # Format day-by-day breakdown
        for day in days_of_week:
            if day in stats['commits_by_day']:
                day_stats = stats['commits_by_day'][day]
                if day_stats['commits'] > 0:
                    author_summary['by_day'][day] = day_stats
                    # Add to overall day totals
                    performance_table['by_day'][day]['commits'] += day_stats['commits']
                    performance_table['by_day'][day]['additions'] += day_stats['additions']
                    performance_table['by_day'][day]['deletions'] += day_stats['deletions']
        
        if author_summary['total_commits'] > 0:
            performance_table['by_author'][author] = author_summary
    
    return performance_table


def export_to_markdown(performance_data: Dict[str, Any], output_file: str = "weekly_performance.md"):
    """
    Export performance data to a markdown file with formatted tables
    
    Args:
        performance_data: Performance table data
        output_file: Output markdown file path
    """
    lines = []
    lines.append("# Weekly Performance Dashboard\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Summary section
    summary = performance_data['summary']
    lines.append("## Summary\n")
    lines.append(f"- **Total Authors**: {summary['total_authors']}")
    lines.append(f"- **Total Commits**: {summary['total_commits']:,}")
    lines.append(f"- **Total Additions**: {summary['total_additions']:,}")
    lines.append(f"- **Total Deletions**: {summary['total_deletions']:,}\n")
    
    # Day of week breakdown
    lines.append("## Activity by Day of Week\n")
    lines.append("| Day | Commits | Additions | Deletions |")
    lines.append("|-----|---------|-----------|-----------|")
    
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days_of_week:
        if day in performance_data['by_day']:
            stats = performance_data['by_day'][day]
            lines.append(f"| {day} | {stats['commits']} | {stats['additions']:,} | {stats['deletions']:,} |")
    lines.append("")
    
    # Author breakdown - Table format with authors as rows
    lines.append("## Performance by Author\n")
    
    # Sort authors by total commits
    sorted_authors = sorted(performance_data['by_author'].items(), 
                          key=lambda x: x[1]['total_commits'], 
                          reverse=True)
    
    # Create main performance table
    lines.append("| Author | Commits | Additions | Deletions | Lines Changed | PRs Opened | PRs Merged | PRs Reviewed |")
    lines.append("|--------|---------|-----------|-----------|---------------|------------|------------|--------------|")
    
    for author, author_data in sorted_authors:
        total_lines = author_data['total_additions'] + author_data['total_deletions']
        author_display = author
        
        # Add asterisk for authors with multiple aliases
        if len(author_data['aliases']) > 1:
            author_display = f"{author}*"
        
        # Get PR metrics if available
        prs_opened = "-"
        prs_merged = "-"
        prs_reviewed = "-"
        if 'pr_metrics' in author_data:
            prs_opened = str(author_data['pr_metrics']['opened'])
            prs_merged = str(author_data['pr_metrics']['merged'])
            prs_reviewed = str(author_data['pr_metrics']['reviewed'])
        
        lines.append(f"| {author_display} | {author_data['total_commits']} | "
                    f"{author_data['total_additions']:,} | {author_data['total_deletions']:,} | "
                    f"{total_lines:,} | {prs_opened} | {prs_merged} | {prs_reviewed} |")
    
    lines.append("")
    
    # Add aliases footnote if needed
    authors_with_aliases = [(author, data) for author, data in sorted_authors 
                           if len(data['aliases']) > 1]
    
    if authors_with_aliases:
        lines.append("_* Authors with multiple aliases:_")
        for author, data in authors_with_aliases:
            lines.append(f"- {author}: {', '.join(sorted(data['aliases']))}")
        lines.append("")
    
    # Add detailed day-of-week breakdown as separate section
    lines.append("## Detailed Activity by Author and Day\n")
    
    for author, author_data in sorted_authors[:10]:  # Show top 10 authors
        lines.append(f"### {author}\n")
        
        lines.append("| Mon | Tue | Wed | Thu | Fri | Sat | Sun | Total |")
        lines.append("|-----|-----|-----|-----|-----|-----|-----|-------|")
        
        day_commits = []
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in author_data['by_day']:
                day_commits.append(str(author_data['by_day'][day]['commits']))
            else:
                day_commits.append("0")
        
        day_commits.append(str(author_data['total_commits']))
        lines.append("| " + " | ".join(day_commits) + " |")
        lines.append("")
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines))
    print(f"Markdown report saved to: {output_file}")


def export_to_csv(performance_data: Dict[str, Any], output_file: str = "weekly_performance.csv"):
    """
    Export performance data to CSV format
    
    Args:
        performance_data: Performance table data
        output_file: Output CSV file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['Author', 'Day', 'Commits', 'Additions', 'Deletions', 'Aliases', 'PRs_Opened', 'PRs_Merged', 'PRs_Reviewed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for author, author_data in performance_data['by_author'].items():
            for day in days_of_week:
                if day in author_data['by_day']:
                    stats = author_data['by_day'][day]
                    row = {
                        'Author': author,
                        'Day': day,
                        'Commits': stats['commits'],
                        'Additions': stats['additions'],
                        'Deletions': stats['deletions'],
                        'Aliases': '|'.join(author_data['aliases'])
                    }
                    
                    if 'pr_metrics' in author_data:
                        row['PRs_Opened'] = author_data['pr_metrics']['opened']
                        row['PRs_Merged'] = author_data['pr_metrics']['merged']
                        row['PRs_Reviewed'] = author_data['pr_metrics']['reviewed']
                    
                    writer.writerow(row)
    
    print(f"CSV report saved to: {output_file}")


def export_to_json(performance_data: Dict[str, Any], output_file: str = "weekly_performance.json"):
    """
    Export performance data to JSON format
    
    Args:
        performance_data: Performance table data
        output_file: Output JSON file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert sets to lists for JSON serialization
    json_data = json.loads(json.dumps(performance_data, default=list))
    
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"JSON report saved to: {output_file}")


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(description='Analyze GitHub contributor performance by day of week')
    parser.add_argument('--owner', default='Open-CA', help='GitHub organization or user')
    parser.add_argument('--repos', nargs='+', default=['iOS-Open'], help='Repository names')
    parser.add_argument('--aliases', default='author_aliases.json', help='Author aliases JSON file')
    parser.add_argument('--format', choices=['markdown', 'csv', 'json', 'all'], default='markdown',
                       help='Output format')
    parser.add_argument('--output-dir', default='output', help='Output directory for reports')
    parser.add_argument('--start-date', help='Start date for PR metrics (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for PR metrics (YYYY-MM-DD)')
    parser.add_argument('--weeks', type=int, default=52, help='Number of weeks to analyze')
    
    args = parser.parse_args()
    
    # Set up date range if provided
    date_range = None
    if args.start_date and args.end_date:
        date_range = (args.start_date, args.end_date)
    elif args.start_date:
        # Default to 30 days from start date
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = start + timedelta(days=30)
        date_range = (args.start_date, end.strftime('%Y-%m-%d'))
    
    # Run analysis
    print(f"Analyzing weekly performance for {args.owner}/{', '.join(args.repos)}...")
    performance_data = analyze_weekly_performance(
        owner=args.owner,
        repos=args.repos,
        aliases_file=args.aliases,
        date_range=date_range,
        num_weeks=args.weeks
    )
    
    # Export in requested formats
    output_dir = Path(args.output_dir)
    
    if args.format in ['markdown', 'all']:
        export_to_markdown(performance_data, output_dir / 'weekly_performance.md')
    
    if args.format in ['csv', 'all']:
        export_to_csv(performance_data, output_dir / 'weekly_performance.csv')
    
    if args.format in ['json', 'all']:
        export_to_json(performance_data, output_dir / 'weekly_performance.json')
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()