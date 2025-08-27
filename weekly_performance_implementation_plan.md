# Weekly Performance Dashboard Implementation Plan

## Overview
Create a comprehensive weekly performance tracking system that analyzes contributor activity across both iOS-Open and OpenWeb repositories, with intelligent author grouping and username alias mapping.

## Implementation Plan

### 1. Create New File: `weekly_performance_analyzer.py`
Main analyzer with enhanced grouping capabilities:

#### Core Features:
- Fetch contributor statistics for multiple repositories (iOS-Open and OpenWeb)
- **Author grouping**: Sum contributions across multiple repos per author
- **Username alias mapping**: Combine multiple GitHub usernames for same person
- Analyze performance by day of week (Monday-Sunday)
- Track commits, lines added, lines deleted per day
- Track pull request metrics (opened, merged, reviewed)
- Generate consolidated reports with proper author attribution

#### Key Functions:
- `load_author_aliases()` - Load username mapping configuration
- `normalize_author()` - Map username to canonical author name
- `fetch_weekly_commits()` - Get commit activity by day of week
- `fetch_pr_metrics()` - Use Search API for PR metrics
- `aggregate_by_author_and_day()` - Group by canonical author name
- `combine_author_stats()` - Merge stats for aliased usernames
- `generate_performance_table()` - Create markdown table with grouped authors

### 2. Create New File: `author_aliases.json`
Configuration file for username mapping:
```json
{
  "brianaronowitz": [
    "brianaronowitzopen",
    "brianaronowitzopen2"
  ],
  "dan-wu": [
    "dan-wu-open",
    "im-danwu"
  ]
}
```

### 3. Create New File: `pr_metrics.py`
Dedicated module for PR-related API calls:
- `get_prs_opened_by_users()` - PRs opened by list of usernames
- `get_prs_merged_by_users()` - PRs merged by list of usernames
- `get_prs_reviewed_by_users()` - PRs reviewed by list of usernames
- `aggregate_pr_activity_by_day()` - Group PR events by day of week

### 4. Update `github_stats.py`
Add new API functions:
- `fetch_pull_requests_search()` - Search API for PR filtering
- `fetch_pr_reviews()` - Get PR review activity
- `get_day_of_week_stats()` - Convert timestamps to day-of-week

## Technical Implementation Details

### Enhanced Data Structure with Author Grouping:
```python
{
  "canonical_author_name": {
    "github_usernames": ["brianaronowitzopen", "brianaronowitzopen2"],
    "repositories": {
      "iOS-Open": {
        "Monday": {
          "commits": 15,
          "additions": 500,
          "deletions": 200,
          "prs_opened": 2,
          "prs_merged": 1,
          "prs_reviewed": 3
        },
        # ... other days
      },
      "OpenWeb": {
        # Same structure
      }
    },
    "combined_totals": {
      "Monday": {
        "commits": 25,  # Sum from all repos & usernames
        "additions": 800,
        "deletions": 350,
        "prs_opened": 4,
        "prs_merged": 2,
        "prs_reviewed": 5
      },
      # ... other days
    }
  }
}
```

### Author Mapping Logic:
```python
class AuthorMapper:
    def __init__(self, aliases_file="author_aliases.json"):
        self.aliases = self.load_aliases(aliases_file)
        self.username_to_canonical = self.build_reverse_mapping()
    
    def get_canonical_name(self, username):
        """Return canonical author name for a GitHub username"""
        return self.username_to_canonical.get(
            username.lower(), 
            username  # Use original if no mapping exists
        )
    
    def get_all_usernames(self, canonical_name):
        """Get all GitHub usernames for a canonical author"""
        return self.aliases.get(canonical_name, [canonical_name])
```

### Aggregation Process:
1. Fetch data for all usernames across all repositories
2. Map each username to its canonical author name
3. Sum statistics for same author across:
   - Multiple usernames (e.g., brianaronowitzopen + brianaronowitzopen2)
   - Multiple repositories (iOS-Open + OpenWeb)
4. Group by day of week
5. Generate unified report

## Expected Output Format

### Markdown Table with Grouped Authors:
```markdown
# Weekly Performance Report: Open-CA Repositories
Analysis Period: 2024-01-01 to 2024-12-31
Generated: 2024-01-15 10:00:00

## Author Username Mappings
- **brianaronowitz**: brianaronowitzopen, brianaronowitzopen2
- **dan-wu**: dan-wu-open, im-danwu

## Combined Performance by Author and Day of Week

| Author | Day | Total Commits | Total Lines+ | Total Lines- | PRs Opened | PRs Merged | PRs Reviewed |
|--------|-----|---------------|--------------|--------------|------------|------------|--------------|
| brianaronowitz | Mon | 45 | 25,230 | 18,450 | 8 | 5 | 15 |
| brianaronowitz | Tue | 52 | 28,940 | 19,200 | 10 | 7 | 18 |
| brianaronowitz | Wed | 38 | 21,500 | 15,300 | 6 | 4 | 12 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| **brianaronowitz Total** | **All** | **315** | **185,670** | **125,950** | **52** | **35** | **98** |
| | | | | | | | |
| dan-wu | Mon | 85 | 35,450 | 22,100 | 15 | 12 | 28 |
| dan-wu | Tue | 92 | 38,200 | 24,500 | 18 | 14 | 32 |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Repository Breakdown by Author

### iOS-Open Repository
| Author | Day | Commits | Lines+ | Lines- | PRs Opened | PRs Merged | PRs Reviewed |
|--------|-----|---------|--------|--------|------------|------------|--------------|
| brianaronowitz* | Mon | 20 | 12,000 | 8,000 | 3 | 2 | 7 |
...
* Includes: brianaronowitzopen, brianaronowitzopen2

### OpenWeb Repository
[Similar table structure]

## Day of Week Summary (All Authors)
| Day | Total Commits | Total Lines+ | Total Lines- | PRs Opened | PRs Merged | PRs Reviewed |
|-----|---------------|--------------|--------------|------------|------------|--------------|
| Monday | 425 | 125,450 | 85,200 | 45 | 35 | 98 |
| Tuesday | 468 | 138,940 | 92,500 | 52 | 40 | 112 |
...
```

## CLI Interface
```bash
# Basic usage with author grouping
python weekly_performance_analyzer.py \
  --owner Open-CA \
  --repos iOS-Open OpenWeb \
  --author-aliases author_aliases.json

# With specific authors and date range
python weekly_performance_analyzer.py \
  --owner Open-CA \
  --repos iOS-Open OpenWeb \
  --authors brianaronowitz dan-wu patseng \
  --date-range 2024-01-01:2024-12-31 \
  --output weekly_performance.md

# Export to multiple formats
python weekly_performance_analyzer.py \
  --owner Open-CA \
  --repos iOS-Open OpenWeb \
  --format markdown csv json \
  --group-by-author  # Groups all aliases together
```

## File Structure After Implementation
```
commit-bot/
├── weekly_performance_analyzer.py  # NEW: Main analyzer with grouping
├── author_aliases.json            # NEW: Username mapping config
├── pr_metrics.py                  # NEW: PR-specific API calls
├── github_stats.py                # UPDATED: Add PR functions
├── main.py                        # UPDATED: Add weekly performance
└── output/
    ├── weekly_performance_grouped.md
    ├── weekly_performance_by_repo.csv
    └── author_mappings_report.json
```

## Key Features
1. **Intelligent Author Grouping**: Automatically combines stats for users with multiple GitHub accounts
2. **Cross-Repository Aggregation**: Sums contributions across iOS and Web codebases
3. **Configurable Aliases**: Easy to maintain JSON file for username mappings
4. **Detailed Breakdown**: Shows both combined and per-repository statistics
5. **Day-of-Week Analysis**: Identifies productivity patterns throughout the week
6. **Comprehensive PR Metrics**: Tracks full PR lifecycle (opened, merged, reviewed)

## API Endpoints to Use
1. `/repos/{owner}/{repo}/stats/contributors` - Commit statistics with timestamps
2. `/search/issues?q=type:pr+repo:{owner}/{repo}` - PR metrics with advanced filters
3. `/repos/{owner}/{repo}/pulls/{pull_number}/reviews` - Review details

## GitHub Search API Query Examples

### Get PRs Opened by User in Date Range:
```
https://api.github.com/search/issues?q=repo:Open-CA/iOS-Open+type:pr+author:username+created:2024-01-01..2024-12-31
```

### Get PRs Reviewed by User:
```
https://api.github.com/search/issues?q=repo:Open-CA/OpenWeb+type:pr+reviewed-by:username
```

### Get Merged PRs:
```
https://api.github.com/search/issues?q=repo:Open-CA/iOS-Open+type:pr+is:merged+merged:2024-01-01..2024-12-31
```

## Testing Plan
1. Test with single contributor, single repo
2. Test with multiple contributors, single repo
3. Test username alias mapping (brianaronowitzopen + brianaronowitzopen2)
4. Test full implementation with both repos
5. Verify PR metrics accuracy against GitHub UI
6. Test date range filtering and day-of-week calculations
7. Validate cross-repository aggregation

## Implementation Priority
1. **Phase 1**: Basic commit statistics by day of week
2. **Phase 2**: Add username alias mapping
3. **Phase 3**: Implement PR metrics (opened, merged, reviewed)
4. **Phase 4**: Cross-repository aggregation
5. **Phase 5**: Advanced reporting and export formats