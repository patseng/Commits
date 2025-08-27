#!/usr/bin/env python3
"""
Analyze contributor lines of code statistics for GitHub repositories
Generates markdown table with lines added and percentage contributions
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
from github_stats import load_credentials, fetch_contributor_stats


def analyze_contributor_lines(contributors: List[Dict[str, Any]], 
                             num_weeks: int = None) -> List[Dict[str, Any]]:
    """
    Analyze contributor statistics focusing on lines of code added
    
    Args:
        contributors: Raw contributor data from GitHub API
        num_weeks: Number of recent weeks to analyze (None for all-time)
    
    Returns:
        List of contributor statistics sorted by total lines added
    """
    contributor_lines = []
    
    for contributor in contributors:
        username = contributor['author']['login']
        # Use all weeks if num_weeks is None, otherwise last N weeks
        if num_weeks is None:
            weeks = contributor['weeks']
        else:
            weeks = contributor['weeks'][-num_weeks:]
        
        total_additions = sum(week['a'] for week in weeks)
        total_deletions = sum(week['d'] for week in weeks)
        total_commits = sum(week['c'] for week in weeks)
        
        # Net lines contributed (additions - deletions)
        net_lines = total_additions - total_deletions
        
        if total_commits > 0:  # Only include active contributors
            contributor_lines.append({
                'username': username,
                'commits': total_commits,
                'additions': total_additions,
                'deletions': total_deletions,
                'net_lines': net_lines
            })
    
    # Sort by total additions (descending)
    contributor_lines.sort(key=lambda x: x['additions'], reverse=True)
    
    # Calculate percentages
    total_additions_all = sum(c['additions'] for c in contributor_lines)
    
    for contributor in contributor_lines:
        if total_additions_all > 0:
            contributor['percentage'] = round(
                (contributor['additions'] / total_additions_all) * 100, 2
            )
        else:
            contributor['percentage'] = 0.0
    
    return contributor_lines


def generate_markdown_table(contributor_stats: List[Dict[str, Any]], 
                           repo_name: str,
                           num_weeks: int = None) -> str:
    """
    Generate a markdown table of contributor statistics
    
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
    md_lines.append(f"# Contributor Statistics for {repo_name}")
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
    md_lines.append("")
    
    # Contributor table
    md_lines.append("## Contributor Breakdown")
    md_lines.append("")
    md_lines.append("| Rank | Contributor | Commits | Lines Added | Lines Deleted | Net Lines | % of Total Lines Added |")
    md_lines.append("|------|-------------|---------|-------------|---------------|-----------|------------------------|")
    
    for idx, contributor in enumerate(contributor_stats, 1):
        # Format numbers with commas for readability
        commits = f"{contributor['commits']:,}"
        additions = f"{contributor['additions']:,}"
        deletions = f"{contributor['deletions']:,}"
        net_lines = f"{contributor['net_lines']:+,}"
        percentage = f"{contributor['percentage']:.1f}%"
        
        # Add row to table
        md_lines.append(
            f"| {idx} | {contributor['username']} | {commits} | "
            f"{additions} | {deletions} | {net_lines} | {percentage} |"
        )
    
    # Add totals row
    md_lines.append(f"| **Total** | **{len(contributor_stats)} contributors** | "
                   f"**{total_commits:,}** | **{total_additions:,}** | "
                   f"**{total_deletions:,}** | **{total_additions - total_deletions:+,}** | **100.0%** |")
    
    # Add top contributors section
    md_lines.append("")
    md_lines.append("## Top Contributors")
    md_lines.append("")
    
    if len(contributor_stats) > 0:
        top_5 = contributor_stats[:5]
        md_lines.append("### By Lines Added")
        for idx, contributor in enumerate(top_5, 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][idx-1]
            md_lines.append(f"{emoji} **{contributor['username']}**: "
                          f"{contributor['additions']:,} lines ({contributor['percentage']:.1f}%)")
    
    # Add cumulative percentage analysis
    md_lines.append("")
    md_lines.append("### Contribution Concentration")
    md_lines.append("")
    
    cumulative_pct = 0
    thresholds = [50, 80, 90]
    threshold_idx = 0
    
    for idx, contributor in enumerate(contributor_stats, 1):
        cumulative_pct += contributor['percentage']
        
        if threshold_idx < len(thresholds) and cumulative_pct >= thresholds[threshold_idx]:
            md_lines.append(f"- Top {idx} contributor(s) account for "
                          f"**{cumulative_pct:.1f}%** of all lines added")
            threshold_idx += 1
            
            if threshold_idx >= len(thresholds):
                break
    
    return "\n".join(md_lines)


def analyze_repository(owner: str, repo: str, token: str, 
                       num_weeks: int = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    Analyze a GitHub repository and generate contributor statistics
    
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
        print(f"Analyzing all-time contributions...")
    else:
        print(f"Analyzing contributions from last {num_weeks} weeks...")
    contributor_stats = analyze_contributor_lines(contributors, num_weeks)
    
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
    
    parser = argparse.ArgumentParser(description='Analyze GitHub repository contributor lines of code')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--weeks', type=int, default=52, help='Number of weeks to analyze (default: 52)')
    parser.add_argument('--all-time', action='store_true', help='Analyze all-time contributions (overrides --weeks)')
    parser.add_argument('--output', help='Output markdown file (default: <repo>_contributor_lines.md)')
    
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
    output_file = args.output or f"{args.repo}_contributor_lines.md"
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(markdown_report)
    
    print(f"\nReport saved to: {output_file}")
    
    # Print summary
    if stats:
        print(f"\nTop 3 contributors by lines added:")
        for idx, contributor in enumerate(stats[:3], 1):
            print(f"  {idx}. {contributor['username']}: "
                  f"{contributor['additions']:,} lines ({contributor['percentage']:.1f}%)")