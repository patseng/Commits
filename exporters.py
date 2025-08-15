#!/usr/bin/env python3
"""Export and display functionality for contributor statistics"""

import csv
import json
from typing import Dict, List


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