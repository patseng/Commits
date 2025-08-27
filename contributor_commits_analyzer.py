#!/usr/bin/env python3
"""
Analyze contributor commit statistics for GitHub repositories
Generates markdown table with commits and percentage contributions
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
from github_stats import load_credentials, fetch_contributor_stats


def analyze_contributor_commits(contributors: List[Dict[str, Any]], 
                               num_weeks: int = None) -> List[Dict[str, Any]]:
    """
    Analyze contributor statistics focusing on commit counts
    
    Args:
        contributors: Raw contributor data from GitHub API
        num_weeks: Number of recent weeks to analyze (None for all-time)
    
    Returns:
        List of contributor statistics sorted by total commits
    """
    contributor_commits = []
    
    for contributor in contributors:
        username = contributor['author']['login']
        # Use all weeks if num_weeks is None, otherwise last N weeks
        if num_weeks is None:
            weeks = contributor['weeks']
        else:
            weeks = contributor['weeks'][-num_weeks:]
        
        total_commits = sum(week['c'] for week in weeks)
        total_additions = sum(week['a'] for week in weeks)
        total_deletions = sum(week['d'] for week in weeks)
        
        # Calculate weeks active (weeks with at least 1 commit)
        active_weeks = sum(1 for week in weeks if week['c'] > 0)
        
        # Net lines contributed
        net_lines = total_additions - total_deletions
        
        if total_commits > 0:  # Only include active contributors
            contributor_commits.append({
                'username': username,
                'commits': total_commits,
                'additions': total_additions,
                'deletions': total_deletions,
                'net_lines': net_lines,
                'active_weeks': active_weeks,
                'avg_commits_per_week': round(total_commits / active_weeks, 1) if active_weeks > 0 else 0
            })
    
    # Sort by total commits (descending)
    contributor_commits.sort(key=lambda x: x['commits'], reverse=True)
    
    # Calculate percentages
    total_commits_all = sum(c['commits'] for c in contributor_commits)
    
    for contributor in contributor_commits:
        if total_commits_all > 0:
            contributor['percentage'] = round(
                (contributor['commits'] / total_commits_all) * 100, 2
            )
        else:
            contributor['percentage'] = 0.0
    
    return contributor_commits


def generate_markdown_table(contributor_stats: List[Dict[str, Any]], 
                           repo_name: str,
                           num_weeks: int = None) -> str:
    """
    Generate a markdown table of contributor commit statistics
    
    Args:
        contributor_stats: List of contributor statistics
        repo_name: Name of the repository (owner/repo)
        num_weeks: Number of weeks analyzed (None for all-time)
    
    Returns:
        Markdown formatted string with the table
    """
    # Calculate totals
    total_commits = sum(c['commits'] for c in contributor_stats)
    total_additions = sum(c['additions'] for c in contributor_stats)
    total_deletions = sum(c['deletions'] for c in contributor_stats)
    
    # Build markdown content
    md_lines = []
    md_lines.append(f"# Contributor Commit Statistics for {repo_name}")
    md_lines.append("")
    if num_weeks is None:
        md_lines.append(f"Analysis Period: All-time contributions")
    else:
        md_lines.append(f"Analysis Period: Last {num_weeks} weeks")
    md_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append("")
    
    # Summary section
    md_lines.append("## Summary")
    md_lines.append(f"- **Total Contributors**: {len(contributor_stats)}")
    md_lines.append(f"- **Total Commits**: {total_commits:,}")
    md_lines.append(f"- **Total Lines Added**: {total_additions:,}")
    md_lines.append(f"- **Total Lines Deleted**: {total_deletions:,}")
    md_lines.append(f"- **Net Lines Change**: {total_additions - total_deletions:+,}")
    
    # Calculate average commits per contributor
    avg_commits = round(total_commits / len(contributor_stats), 1) if contributor_stats else 0
    md_lines.append(f"- **Average Commits per Contributor**: {avg_commits}")
    md_lines.append("")
    
    # Contributor table sorted by commits
    md_lines.append("## Contributor Breakdown (Sorted by Commits)")
    md_lines.append("")
    md_lines.append("| Rank | Contributor | Commits | % of Total Commits | Active Weeks | Avg Commits/Week | Lines Added | Lines Deleted | Net Lines |")
    md_lines.append("|------|-------------|---------|-------------------|--------------|------------------|-------------|---------------|-----------|")
    
    for idx, contributor in enumerate(contributor_stats, 1):
        # Format numbers with commas for readability
        commits = f"{contributor['commits']:,}"
        percentage = f"{contributor['percentage']:.1f}%"
        active_weeks = contributor['active_weeks']
        avg_per_week = contributor['avg_commits_per_week']
        additions = f"{contributor['additions']:,}"
        deletions = f"{contributor['deletions']:,}"
        net_lines = f"{contributor['net_lines']:+,}"
        
        # Add row to table
        md_lines.append(
            f"| {idx} | {contributor['username']} | {commits} | {percentage} | "
            f"{active_weeks} | {avg_per_week} | {additions} | {deletions} | {net_lines} |"
        )
    
    # Add totals row
    total_active_weeks = max(c['active_weeks'] for c in contributor_stats) if contributor_stats else 0
    md_lines.append(f"| **Total** | **{len(contributor_stats)} contributors** | "
                   f"**{total_commits:,}** | **100.0%** | **{total_active_weeks} max** | **-** | "
                   f"**{total_additions:,}** | **{total_deletions:,}** | **{total_additions - total_deletions:+,}** |")
    
    # Add top contributors section
    md_lines.append("")
    md_lines.append("## Top Contributors")
    md_lines.append("")
    
    if len(contributor_stats) > 0:
        top_5 = contributor_stats[:5]
        md_lines.append("### By Commit Count")
        for idx, contributor in enumerate(top_5, 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][idx-1]
            md_lines.append(f"{emoji} **{contributor['username']}**: "
                          f"{contributor['commits']:,} commits ({contributor['percentage']:.1f}%) - "
                          f"Active {contributor['active_weeks']} weeks")
    
    # Add commit frequency analysis
    md_lines.append("")
    md_lines.append("### Commit Frequency Leaders")
    md_lines.append("")
    
    # Sort by average commits per week for frequency leaders
    frequent_contributors = sorted(contributor_stats, 
                                  key=lambda x: x['avg_commits_per_week'], 
                                  reverse=True)[:5]
    
    for idx, contributor in enumerate(frequent_contributors, 1):
        md_lines.append(f"{idx}. **{contributor['username']}**: "
                      f"{contributor['avg_commits_per_week']} commits/week average "
                      f"({contributor['commits']} total commits over {contributor['active_weeks']} weeks)")
    
    # Add cumulative percentage analysis
    md_lines.append("")
    md_lines.append("### Contribution Concentration (by Commits)")
    md_lines.append("")
    
    cumulative_pct = 0
    thresholds = [50, 80, 90]
    threshold_idx = 0
    
    for idx, contributor in enumerate(contributor_stats, 1):
        cumulative_pct += contributor['percentage']
        
        if threshold_idx < len(thresholds) and cumulative_pct >= thresholds[threshold_idx]:
            md_lines.append(f"- Top {idx} contributor(s) account for "
                          f"**{cumulative_pct:.1f}%** of all commits")
            threshold_idx += 1
            
            if threshold_idx >= len(thresholds):
                break
    
    # Add activity distribution
    md_lines.append("")
    md_lines.append("### Activity Distribution")
    md_lines.append("")
    
    # Categorize contributors by commit volume
    high_volume = [c for c in contributor_stats if c['commits'] >= 100]
    medium_volume = [c for c in contributor_stats if 20 <= c['commits'] < 100]
    low_volume = [c for c in contributor_stats if c['commits'] < 20]
    
    md_lines.append(f"- **High Volume** (100+ commits): {len(high_volume)} contributor(s)")
    if high_volume:
        md_lines.append(f"  - {', '.join(c['username'] for c in high_volume)}")
    
    md_lines.append(f"- **Medium Volume** (20-99 commits): {len(medium_volume)} contributor(s)")
    if medium_volume:
        md_lines.append(f"  - {', '.join(c['username'] for c in medium_volume)}")
    
    md_lines.append(f"- **Low Volume** (<20 commits): {len(low_volume)} contributor(s)")
    if low_volume:
        md_lines.append(f"  - {', '.join(c['username'] for c in low_volume)}")
    
    return "\n".join(md_lines)


def analyze_repository(owner: str, repo: str, token: str, 
                       num_weeks: int = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    Analyze a GitHub repository and generate contributor commit statistics
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token
        num_weeks: Number of weeks to analyze (None for all-time)
    
    Returns:
        Tuple of (contributor statistics, markdown report)
    """
    print(f"Fetching contributor statistics for {owner}/{repo}...")
    contributors = fetch_contributor_stats(owner, repo, token)
    
    if num_weeks is None:
        print(f"Analyzing all-time commit contributions...")
    else:
        print(f"Analyzing commit contributions from last {num_weeks} weeks...")
    contributor_stats = analyze_contributor_commits(contributors, num_weeks)
    
    print(f"Found {len(contributor_stats)} active contributors")
    
    # Generate markdown report
    markdown_report = generate_markdown_table(
        contributor_stats, 
        f"{owner}/{repo}",
        num_weeks
    )
    
    return contributor_stats, markdown_report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze GitHub repository contributor commits')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--weeks', type=int, default=52, help='Number of weeks to analyze (default: 52)')
    parser.add_argument('--all-time', action='store_true', help='Analyze all-time contributions (overrides --weeks)')
    parser.add_argument('--output', help='Output markdown file (default: <repo>_contributor_commits.md)')
    
    args = parser.parse_args()
    
    # Load credentials
    creds = load_credentials()
    token = creds.get("github_token")
    
    if not token:
        raise ValueError("github_token not found in credentials file")
    
    # Determine time period
    num_weeks = None if args.all_time else args.weeks
    
    # Analyze repository
    stats, markdown_report = analyze_repository(
        args.owner, 
        args.repo, 
        token,
        num_weeks
    )
    
    # Determine output filename
    output_file = args.output or f"{args.repo}_contributor_commits.md"
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(markdown_report)
    
    print(f"\nReport saved to: {output_file}")
    
    # Print summary
    if stats:
        print(f"\nTop 3 contributors by commits:")
        for idx, contributor in enumerate(stats[:3], 1):
            print(f"  {idx}. {contributor['username']}: "
                  f"{contributor['commits']:,} commits ({contributor['percentage']:.1f}%)")