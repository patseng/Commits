# Weekly Performance Statistics Aggregation Plan

## Overview
This document outlines the implementation plan for enhancing the GitHub contributor statistics tool to group and analyze performance metrics (commits, additions, deletions) by week rather than just by contributor.

## Current State
The existing codebase fetches GitHub contributor statistics and organizes them by individual contributors, showing each person's weekly activity. However, it lacks the capability to aggregate statistics across all contributors on a weekly basis, which would provide valuable insights into overall project momentum and activity patterns.

## Objectives
1. Group performance statistics by week across all contributors
2. Provide multiple output formats for weekly aggregated data
3. Maintain backward compatibility with existing user-centric views
4. Add visualization capabilities for trend analysis

## Implementation Details

### 1. Core Aggregation Logic

#### File: `github_stats.py`
Add new functions for weekly aggregation:

```python
def aggregate_by_week(contributors: List[Dict[str, Any]], num_weeks: int = 52) -> Dict[str, Dict]:
    """
    Aggregate contributor statistics by week
    
    Returns:
        Dictionary with week as key and aggregated stats as value
    """
    # Implementation details:
    # - Iterate through all contributors
    # - Group data by week timestamp
    # - Sum commits, additions, deletions for each week
    # - Track unique contributors per week
    # - Calculate weekly averages and percentiles
```

```python
def calculate_weekly_trends(weekly_aggregates: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calculate trend metrics for weekly performance
    
    Returns:
        Dictionary containing trend analysis (growth rate, moving averages, etc.)
    """
```

### 2. Export Enhancements

#### File: `exporters.py`
Add specialized export functions for weekly data:

```python
def display_weekly_summary(weekly_stats: Dict[str, Dict]):
    """Display weekly aggregated statistics to console"""
    # Format: Week | Commits | Additions | Deletions | Contributors
    
def save_weekly_csv(weekly_stats: Dict[str, Dict], filename: str = "weekly_stats.csv"):
    """Export weekly statistics to CSV"""
    # Columns: week, total_commits, total_additions, total_deletions, 
    #          contributor_count, top_contributor, average_commits_per_contributor
    
def save_weekly_json(weekly_stats: Dict[str, Dict], filename: str = "weekly_stats.json"):
    """Export weekly statistics to JSON with detailed breakdown"""
```

### 3. Visualization Module (Optional)

#### New File: `visualizer.py`
Create data visualization capabilities:

```python
def create_weekly_charts(weekly_stats: Dict[str, Dict], output_dir: str = "charts/"):
    """Generate charts for weekly statistics"""
    # Create:
    # - Stacked bar chart for commits/additions/deletions
    # - Line graph for trend over time
    # - Contributor activity heatmap
    # - Moving average overlay
```

### 4. Main Application Updates

#### File: `main.py`
Enhance the main entry point with new options:

```python
def main():
    # Add command-line argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--view', choices=['user', 'week', 'both'], default='both')
    parser.add_argument('--format', choices=['console', 'csv', 'json', 'all'], default='all')
    parser.add_argument('--visualize', action='store_true')
    
    # Process based on selected view
    if args.view in ['week', 'both']:
        weekly_aggregates = aggregate_by_week(contributors, WEEKS_TO_FETCH)
        export_weekly_stats(weekly_aggregates, args.format)
```

## Output Format Examples

### Weekly Summary Console Output
```
GitHub Repository Statistics - Weekly View
==========================================
Repository: Open-CA/iOS-Open
Period: 2025-02-15 to 2025-08-15

Week of 2025-02-15:
  Total Commits:     12
  Total Additions:   500 lines
  Total Deletions:   200 lines
  Active Contributors: 3 (denizsarac-open, user2, user3)
  Most Active: denizsarac-open (8 commits)

Week of 2025-02-22:
  Total Commits:     25
  Total Additions:   1,200 lines
  Total Deletions:   450 lines
  Active Contributors: 5
  Most Active: user1 (12 commits)

Summary Statistics:
  Average Weekly Commits: 18.5
  Peak Week: 2025-03-15 (45 commits)
  Most Consistent Contributor: denizsarac-open (present in 85% of weeks)
```

### Weekly CSV Format
```csv
week,total_commits,total_additions,total_deletions,contributor_count,top_contributor,avg_commits_per_contributor
2025-02-15,12,500,200,3,denizsarac-open,4.0
2025-02-22,25,1200,450,5,user1,5.0
2025-03-01,18,750,300,4,user2,4.5
```

### Weekly JSON Structure
```json
{
  "metadata": {
    "repository": "Open-CA/iOS-Open",
    "period": {
      "start": "2025-02-15",
      "end": "2025-08-15",
      "weeks_analyzed": 26
    },
    "generated_at": "2025-08-15T10:30:00Z"
  },
  "weekly_stats": {
    "2025-02-15": {
      "total_commits": 12,
      "total_additions": 500,
      "total_deletions": 200,
      "contributor_count": 3,
      "contributors": {
        "denizsarac-open": {
          "commits": 8,
          "additions": 350,
          "deletions": 150
        },
        "user2": {
          "commits": 3,
          "additions": 120,
          "deletions": 40
        },
        "user3": {
          "commits": 1,
          "additions": 30,
          "deletions": 10
        }
      },
      "metrics": {
        "avg_commits_per_contributor": 4.0,
        "code_churn_ratio": 2.5
      }
    }
  },
  "trends": {
    "commit_growth_rate": 0.15,
    "peak_week": "2025-03-15",
    "most_consistent_contributors": ["denizsarac-open", "user1"]
  }
}
```

## Implementation Priority

### Phase 1 (Core Functionality)
1. Implement `aggregate_by_week()` function
2. Add basic weekly console display
3. Create weekly CSV export

### Phase 2 (Enhanced Features)
1. Add detailed JSON export with metrics
2. Implement trend calculation
3. Add command-line arguments

### Phase 3 (Visualization)
1. Create visualization module (if matplotlib available)
2. Generate weekly trend charts
3. Add contributor heatmap

## Testing Considerations

1. **Unit Tests**
   - Test aggregation with various data patterns
   - Verify calculations for edge cases (empty weeks, single contributor)
   - Test date parsing and formatting

2. **Integration Tests**
   - Verify API data processing pipeline
   - Test all export formats
   - Validate command-line argument handling

3. **Performance Tests**
   - Test with large datasets (52+ weeks, 100+ contributors)
   - Measure memory usage during aggregation
   - Optimize for repositories with extensive history

## Backward Compatibility

- Maintain all existing functions and exports
- Default behavior shows both user-centric and week-centric views
- Existing output files remain unchanged (contributor_stats.csv/json)
- New weekly files use different names (weekly_stats.csv/json)

## Future Enhancements

1. **Advanced Analytics**
   - Contributor velocity trends
   - Code quality metrics integration
   - Sprint/milestone alignment

2. **Interactive Features**
   - Web dashboard for real-time viewing
   - Configurable aggregation periods (daily, monthly, quarterly)
   - Custom metric definitions

3. **Team Analytics**
   - Team-based grouping
   - Comparative analysis between periods
   - Productivity forecasting

## Dependencies

### Required
- `requests`: GitHub API interaction
- `datetime`: Date manipulation
- `csv`, `json`: Data export

### Optional
- `matplotlib`: Visualization (charts)
- `pandas`: Advanced data manipulation
- `numpy`: Statistical calculations

## Configuration

Add to `.credentials.json`:
```json
{
  "github_token": "your_token_here",
  "default_view": "both",
  "export_formats": ["console", "csv", "json"],
  "enable_charts": false
}
```

## Expected Benefits

1. **Project Management**
   - Track development velocity over time
   - Identify productive periods and bottlenecks
   - Resource allocation insights

2. **Team Analytics**
   - Understand contribution patterns
   - Recognize consistent contributors
   - Measure team growth

3. **Reporting**
   - Generate weekly status reports
   - Provide stakeholder updates
   - Track milestone progress

## Conclusion

This enhancement will transform the tool from a simple contributor statistics fetcher into a comprehensive project analytics platform, providing valuable insights into development patterns and team productivity while maintaining simplicity and backward compatibility.