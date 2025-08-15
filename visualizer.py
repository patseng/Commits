#!/usr/bin/env python3
"""Visualization module for GitHub contributor statistics"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.table import Table
import numpy as np


EXCLUDED_AUTHORS = ['o-p-e-n-ios', 'openEngBot']


def load_stats_from_file(filename: str = "contributor_stats.json") -> Dict[str, List[Dict]]:
    """Load contributor statistics from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)


def filter_authors(stats: Dict[str, List[Dict]], 
                  exclude_authors: List[str] = None) -> Dict[str, List[Dict]]:
    """Filter out excluded authors from statistics"""
    if exclude_authors is None:
        exclude_authors = EXCLUDED_AUTHORS
    
    return {k: v for k, v in stats.items() if k not in exclude_authors}


def prepare_chart_data(stats: Dict[str, List[Dict]], 
                      weeks: int = 6,
                      exclude_authors: List[str] = None) -> Dict[str, Any]:
    """
    Prepare data for chart generation
    
    Returns dict with:
    - weeks: list of week dates
    - authors: list of author names
    - data: dict mapping author to list of commit counts
    """
    filtered_stats = filter_authors(stats, exclude_authors)
    
    all_weeks = set()
    for author_data in filtered_stats.values():
        for week_data in author_data:
            all_weeks.add(week_data['week'])
    
    sorted_weeks = sorted(list(all_weeks))
    
    if len(sorted_weeks) > weeks:
        sorted_weeks = sorted_weeks[-weeks:]
    
    chart_data = {
        'weeks': sorted_weeks,
        'authors': [],
        'data': {}
    }
    
    for author, author_weeks in filtered_stats.items():
        week_commits = {w['week']: w['commits'] for w in author_weeks}
        
        commit_counts = []
        has_activity = False
        for week in sorted_weeks:
            commits = week_commits.get(week, 0)
            commit_counts.append(commits)
            if commits > 0:
                has_activity = True
        
        if has_activity:
            chart_data['authors'].append(author)
            chart_data['data'][author] = commit_counts
    
    chart_data['authors'] = sorted(chart_data['authors'], 
                                  key=lambda a: sum(chart_data['data'][a]), 
                                  reverse=True)
    
    return chart_data


def generate_commit_line_chart(stats: Dict[str, List[Dict]], 
                              weeks: int = 6,
                              exclude_authors: List[str] = None,
                              output_file: str = "commit_chart_6weeks.png",
                              show_table: bool = True) -> None:
    """Generate line chart with commits per week per author"""
    
    chart_data = prepare_chart_data(stats, weeks, exclude_authors)
    
    if not chart_data['authors']:
        print("No data available for the specified period")
        return
    
    fig = plt.figure(figsize=(14, 10))
    
    if show_table:
        ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=7)
    else:
        ax1 = plt.subplot(111)
    
    colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(chart_data['authors']))))
    if len(chart_data['authors']) > 10:
        colors = plt.cm.tab20(np.linspace(0, 1, len(chart_data['authors'])))
    
    week_labels = [datetime.strptime(w, '%Y-%m-%d').strftime('%m/%d') 
                  for w in chart_data['weeks']]
    x_pos = np.arange(len(week_labels))
    
    for idx, author in enumerate(chart_data['authors']):
        color = colors[idx % len(colors)]
        commits = chart_data['data'][author]
        
        ax1.plot(x_pos, commits, 
                marker='o', 
                label=author, 
                color=color,
                linewidth=2,
                markersize=6)
    
    ax1.set_xlabel('Week', fontsize=12)
    ax1.set_ylabel('Number of Commits', fontsize=12)
    ax1.set_title(f'Last {weeks} Weeks Commit Activity (Human Contributors)', 
                 fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(week_labels, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
    
    y_max = max(max(commits) for commits in chart_data['data'].values())
    ax1.set_ylim(0, y_max * 1.1)
    
    if show_table:
        create_data_table(fig, chart_data, weeks)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {output_file}")
    
    plt.show()


def create_data_table(fig, chart_data: Dict[str, Any], weeks: int) -> None:
    """Create data table below the chart"""
    
    ax2 = plt.subplot2grid((10, 1), (7, 0), rowspan=3)
    ax2.axis('tight')
    ax2.axis('off')
    
    week_labels = [datetime.strptime(w, '%Y-%m-%d').strftime('%m/%d') 
                  for w in chart_data['weeks']]
    
    headers = ['Author'] + week_labels + ['Total']
    
    table_data = []
    weekly_totals = [0] * len(chart_data['weeks'])
    
    for author in chart_data['authors']:
        commits = chart_data['data'][author]
        row = [author] + commits + [sum(commits)]
        table_data.append(row)
        
        for i, c in enumerate(commits):
            weekly_totals[i] += c
    
    table_data.append(['Weekly Total'] + weekly_totals + [sum(weekly_totals)])
    
    table = ax2.table(cellText=table_data,
                     colLabels=headers,
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.15] + [0.1] * len(week_labels) + [0.1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(len(headers)):
        table[(len(table_data), i)].set_facecolor('#E0E0E0')
        table[(len(table_data), i)].set_text_props(weight='bold')
    
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            for j in range(len(headers)):
                table[(i, j)].set_facecolor('#F5F5F5')


def generate_console_table(stats: Dict[str, List[Dict]], 
                          weeks: int = 6,
                          exclude_authors: List[str] = None) -> None:
    """Generate a console-friendly table of commit data"""
    
    chart_data = prepare_chart_data(stats, weeks, exclude_authors)
    
    if not chart_data['authors']:
        print("No data available for the specified period")
        return
    
    week_labels = [datetime.strptime(w, '%Y-%m-%d').strftime('%m/%d') 
                  for w in chart_data['weeks']]
    
    col_width = 8
    author_width = 15
    
    print("\nLast {} Weeks Commit Activity (Human Contributors)".format(weeks))
    print("=" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    header = "Author".ljust(author_width) + " | "
    for week in week_labels:
        header += week.center(col_width) + " | "
    header += "Total".center(col_width)
    print(header)
    print("-" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    weekly_totals = [0] * len(chart_data['weeks'])
    
    for author in chart_data['authors']:
        commits = chart_data['data'][author]
        row = author[:author_width].ljust(author_width) + " | "
        for i, c in enumerate(commits):
            row += str(c).center(col_width) + " | "
            weekly_totals[i] += c
        row += str(sum(commits)).center(col_width)
        print(row)
    
    print("-" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    totals_row = "Weekly Total".ljust(author_width) + " | "
    for total in weekly_totals:
        totals_row += str(total).center(col_width) + " | "
    totals_row += str(sum(weekly_totals)).center(col_width)
    print(totals_row)
    print()


if __name__ == "__main__":
    stats = load_stats_from_file()
    
    generate_console_table(stats, weeks=6)
    
    try:
        generate_commit_line_chart(stats, weeks=6)
    except ImportError:
        print("Matplotlib not installed. Install with: pip install matplotlib")
        print("Showing console table only.")