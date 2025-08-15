#!/usr/bin/env python3
"""Export and display functionality for contributor statistics"""

import csv
import json
from typing import Dict, List, Any
from datetime import datetime


def display_summary(stats: Dict[str, List[Dict]], weeks_count: int):
    """Display contributor statistics summary to console"""
    print(f"\nFound {len(stats)} contributors with activity in the last {weeks_count} weeks\n")
    
    for username, weeks in stats.items():
        total_commits = sum(w['commits'] for w in weeks)
        total_additions = sum(w['additions'] for w in weeks)
        total_deletions = sum(w['deletions'] for w in weeks)
        
        print(f"{username}:")
        print(f"  Total commits: {total_commits}")
        print(f"  Total additions: {total_additions}")
        print(f"  Total deletions: {total_deletions}")
        print(f"  Active weeks: {len(weeks)}")
        print()


def save_to_csv(stats: Dict[str, List[Dict]], filename: str = "contributor_stats.csv"):
    """Save statistics to CSV file"""
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


def save_to_json(stats: Dict[str, List[Dict]], filename: str = "contributor_stats.json"):
    """Save statistics to JSON file"""
    with open(filename, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to {filename}")


def export_all(stats: Dict[str, List[Dict]], weeks_count: int):
    """Export statistics in all available formats"""
    display_summary(stats, weeks_count)
    save_to_csv(stats)
    save_to_json(stats)


def display_weekly_summary(weekly_stats: Dict[str, Dict], trends: Dict[str, Any] = None):
    """Display weekly aggregated statistics to console"""
    print("\n" + "=" * 60)
    print("GitHub Repository Statistics - Weekly View")
    print("=" * 60)
    
    if trends:
        print(f"Period: {trends['period']['start']} to {trends['period']['end']}")
        print(f"Weeks analyzed: {trends['period']['weeks_analyzed']}")
        print()
    
    # Sort weeks chronologically
    sorted_weeks = sorted(weekly_stats.keys())
    
    for week in sorted_weeks:
        week_data = weekly_stats[week]
        print(f"\nWeek of {week}:")
        print(f"  Total Commits:     {week_data['total_commits']}")
        print(f"  Total Additions:   {week_data['total_additions']:,} lines")
        print(f"  Total Deletions:   {week_data['total_deletions']:,} lines")
        print(f"  Active Contributors: {week_data['contributor_count']}")
        
        if 'top_contributor' in week_data:
            print(f"  Most Active: {week_data['top_contributor']} ({week_data['top_contributor_commits']} commits)")
    
    if trends:
        print("\n" + "-" * 60)
        print("Summary Statistics:")
        print("-" * 60)
        print(f"  Total Commits: {trends['totals']['commits']}")
        print(f"  Average Weekly Commits: {trends['averages']['weekly_commits']}")
        print(f"  Peak Week: {trends['peak_week']['date']} ({trends['peak_week']['commits']} commits)")
        
        if trends['most_consistent_contributors']:
            print("\n  Most Consistent Contributors:")
            for contributor in trends['most_consistent_contributors'][:3]:
                percentage = round(contributor['weeks_active'] / trends['period']['weeks_analyzed'] * 100, 1)
                print(f"    - {contributor['username']} (active in {contributor['weeks_active']} weeks, {percentage}%)")
        
        if 'commit_growth_rate' in trends:
            growth_pct = trends['commit_growth_rate'] * 100
            if growth_pct > 0:
                print(f"\n  Commit Growth Rate: +{growth_pct:.1f}%")
            else:
                print(f"\n  Commit Growth Rate: {growth_pct:.1f}%")
    
    print()


def save_weekly_csv(weekly_stats: Dict[str, Dict], filename: str = "weekly_stats.csv"):
    """Export weekly statistics to CSV"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'week', 'total_commits', 'total_additions', 'total_deletions',
            'contributor_count', 'top_contributor', 'avg_commits_per_contributor'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Sort weeks chronologically
        sorted_weeks = sorted(weekly_stats.keys())
        
        for week in sorted_weeks:
            week_data = weekly_stats[week]
            writer.writerow({
                'week': week,
                'total_commits': week_data['total_commits'],
                'total_additions': week_data['total_additions'],
                'total_deletions': week_data['total_deletions'],
                'contributor_count': week_data['contributor_count'],
                'top_contributor': week_data.get('top_contributor', ''),
                'avg_commits_per_contributor': week_data.get('avg_commits_per_contributor', 0)
            })
    
    print(f"Weekly statistics saved to {filename}")


def save_weekly_json(weekly_stats: Dict[str, Dict], trends: Dict[str, Any] = None, 
                    filename: str = "weekly_stats.json"):
    """Export weekly statistics to JSON with detailed breakdown"""
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat() + 'Z'
        },
        "weekly_stats": weekly_stats
    }
    
    if trends:
        output["metadata"]["period"] = trends['period']
        output["trends"] = {
            "totals": trends['totals'],
            "averages": trends['averages'],
            "peak_week": trends['peak_week'],
            "commit_growth_rate": trends['commit_growth_rate'],
            "most_consistent_contributors": trends['most_consistent_contributors']
        }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Weekly statistics saved to {filename}")


def export_weekly_stats(weekly_aggregates: Dict[str, Dict], trends: Dict[str, Any] = None,
                       export_format: str = 'all'):
    """Export weekly statistics in specified format(s)"""
    if export_format in ['console', 'all']:
        display_weekly_summary(weekly_aggregates, trends)
    
    if export_format in ['csv', 'all']:
        save_weekly_csv(weekly_aggregates)
    
    if export_format in ['json', 'all']:
        save_weekly_json(weekly_aggregates, trends)