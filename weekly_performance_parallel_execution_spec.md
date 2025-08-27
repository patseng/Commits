# Weekly Performance Dashboard - Parallel Execution Specification

## Executive Summary
This specification enables parallel development of the weekly performance dashboard using multiple Claude agents with context7 for library documentation and task coordination.

## Progress Tracking Dashboard

### Phase Status
- [ ] **Phase 1**: Core Statistics Module (0% complete)
- [ ] **Phase 2**: Author Alias System (0% complete)  
- [ ] **Phase 3**: PR Metrics Module (0% complete)
- [ ] **Phase 4**: Integration Layer (0% complete)
- [ ] **Phase 5**: Output Generation (0% complete)

---

## Agent Task Allocation for Parallel Execution

### Agent 1: Core Statistics Developer
**Focus**: Build foundation for commit and line statistics

#### Tasks:
1. **Create `weekly_performance_analyzer.py`** (base structure)
   ```python
   # Core structure to implement:
   class WeeklyPerformanceAnalyzer:
       def __init__(self, owner, repos, token):
           self.owner = owner
           self.repos = repos
           self.token = token
           
       def fetch_weekly_commits(self, repo, username):
           # Use existing github_stats.fetch_contributor_stats()
           pass
           
       def aggregate_by_day_of_week(self, stats):
           # Convert timestamps to day names
           pass
   ```

2. **Implement day-of-week aggregation**
   - Parse Unix timestamps from contributor stats
   - Group by weekday (Monday-Sunday)
   - Calculate totals per day

#### Context7 Requirements:
```bash
# Agent 1 should fetch documentation for:
mcp__context7__get-library-docs --library requests  # For API calls
mcp__context7__get-library-docs --library datetime  # For date handling
mcp__context7__get-library-docs --library pandas    # For data aggregation
```

#### Deliverables:
- [ ] `weekly_performance_analyzer.py` with basic structure
- [ ] Day-of-week conversion utilities
- [ ] Basic aggregation functions
- [ ] Unit tests for date conversion

---

### Agent 2: Author Alias System Developer
**Focus**: Username mapping and author normalization

#### Tasks:
1. **Create `author_mapper.py`**
   ```python
   class AuthorMapper:
       def __init__(self, aliases_file="author_aliases.json"):
           self.aliases = self.load_aliases(aliases_file)
           self.username_to_canonical = self.build_reverse_mapping()
       
       def get_canonical_name(self, username):
           """Map GitHub username to canonical author name"""
           pass
       
       def merge_author_stats(self, stats_list):
           """Combine statistics for aliased usernames"""
           pass
   ```

2. **Create `author_aliases.json`**
   ```json
   {
     "brianaronowitz": [
       "brianaronowitzopen", 
       "brianaronowitzopen2"
     ],
     "dan-wu": [
       "dan-wu-open",
       "im-danwu"
     ],
     "patseng": ["patseng"],
     "malte": ["malte-open"],
     "ashoka": ["open-ashoka"]
   }
   ```

3. **Build merge logic for duplicate authors**
   - Sum commits, lines across usernames
   - Maintain attribution trail
   - Handle case-insensitive matching

#### Context7 Requirements:
```bash
# Agent 2 should fetch:
mcp__context7__get-library-docs --library json     # For config loading
mcp__context7__get-library-docs --library typing   # For type hints
```

#### Deliverables:
- [ ] `author_mapper.py` module
- [ ] `author_aliases.json` configuration
- [ ] Statistics merging functions
- [ ] Test cases for alias resolution

---

### Agent 3: PR Metrics Specialist
**Focus**: GitHub Search API integration for pull requests

#### Tasks:
1. **Create `pr_metrics.py`**
   ```python
   class PRMetrics:
       def __init__(self, token):
           self.token = token
           self.headers = {
               "Authorization": f"token {token}",
               "Accept": "application/vnd.github.v3+json"
           }
       
       def get_prs_opened(self, owner, repo, username, date_range):
           """Query: type:pr author:username created:date_range"""
           pass
       
       def get_prs_merged(self, owner, repo, username, date_range):
           """Query: type:pr is:merged merged:date_range"""
           pass
       
       def get_prs_reviewed(self, owner, repo, username, date_range):
           """Query: type:pr reviewed-by:username"""
           pass
   ```

2. **Implement Search API queries**
   - Build query strings programmatically
   - Handle pagination for large result sets
   - Parse PR events for day-of-week

3. **Create PR event aggregator**
   - Group PRs by day of week
   - Count opened/merged/reviewed per day
   - Handle rate limiting gracefully

#### Context7 Requirements:
```bash
# Agent 3 should fetch:
mcp__context7__get-library-docs --library requests      # For API calls
mcp__context7__resolve-library-id --query "github api"  # Find GitHub libraries
mcp__context7__get-library-docs --library urllib.parse  # For URL encoding
```

#### API Endpoints:
```python
# Search API base
SEARCH_BASE = "https://api.github.com/search/issues"

# Query templates
QUERIES = {
    "opened": "repo:{owner}/{repo} type:pr author:{user} created:{start}..{end}",
    "merged": "repo:{owner}/{repo} type:pr is:merged merged:{start}..{end}",
    "reviewed": "repo:{owner}/{repo} type:pr reviewed-by:{user}"
}
```

#### Deliverables:
- [ ] `pr_metrics.py` module
- [ ] Search API integration
- [ ] PR event aggregation functions
- [ ] Rate limit handling

---

### Agent 4: Integration Coordinator
**Focus**: Combine all modules and generate reports

#### Tasks:
1. **Update `github_stats.py`** with new functions:
   ```python
   def fetch_pull_requests_search(owner, repo, query, token):
       """Wrapper for GitHub Search API"""
       pass
   
   def get_day_of_week_stats(timestamp):
       """Convert Unix timestamp to weekday name"""
       pass
   ```

2. **Create main orchestration in `weekly_performance_analyzer.py`**:
   ```python
   def analyze_weekly_performance(owner, repos, aliases_file, date_range=None):
       # Step 1: Initialize modules
       mapper = AuthorMapper(aliases_file)
       pr_metrics = PRMetrics(token)
       
       # Step 2: Fetch data for all repos and users
       all_stats = {}
       
       # Step 3: Apply author mapping
       grouped_stats = mapper.group_by_canonical_author(all_stats)
       
       # Step 4: Generate reports
       return generate_performance_table(grouped_stats)
   ```

3. **Build output generators**:
   - Markdown table formatter
   - CSV exporter
   - JSON structure builder

#### Context7 Requirements:
```bash
# Agent 4 should fetch:
mcp__context7__get-library-docs --library csv        # For CSV export
mcp__context7__get-library-docs --library tabulate  # For table formatting
mcp__context7__get-library-docs --library argparse  # For CLI interface
```

#### Deliverables:
- [ ] Integration functions in `github_stats.py`
- [ ] Main orchestration logic
- [ ] Output formatters (MD, CSV, JSON)
- [ ] CLI argument parser

---

## Parallel Execution Instructions

### How to Deploy Multiple Agents

**Step 1: Launch Agents Simultaneously**
```bash
# Terminal 1 - Agent 1 (Core Stats)
claude-agent --task "Implement weekly_performance_analyzer.py focusing on commit statistics and day-of-week aggregation using the spec in weekly_performance_parallel_execution_spec.md Agent 1 section"

# Terminal 2 - Agent 2 (Author Aliases)  
claude-agent --task "Create author_mapper.py and author_aliases.json as specified in weekly_performance_parallel_execution_spec.md Agent 2 section"

# Terminal 3 - Agent 3 (PR Metrics)
claude-agent --task "Build pr_metrics.py module for GitHub PR search queries following weekly_performance_parallel_execution_spec.md Agent 3 section"

# Terminal 4 - Agent 4 (Integration)
claude-agent --task "After other agents complete, integrate modules and create output generators per weekly_performance_parallel_execution_spec.md Agent 4 section"
```

**Step 2: Context Sharing Between Agents**
```python
# Each agent should create a status file:
# agent1_status.json
{
  "agent": 1,
  "task": "Core Statistics",
  "status": "in_progress",
  "completed_functions": ["fetch_weekly_commits", "aggregate_by_day_of_week"],
  "blocking_issues": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Step 3: Synchronization Points**
1. Agents 1-3 can work fully in parallel
2. Agent 4 waits for Agents 1-3 to complete
3. All agents commit to feature branches
4. Final merge coordinated by Agent 4

---

## Testing Matrix for Parallel Development

### Independent Tests (Can Run in Parallel)

**Agent 1 Tests**:
```python
# test_weekly_stats.py
def test_day_of_week_conversion():
    assert get_day_name(1704067200) == "Monday"  # Jan 1, 2024

def test_aggregation():
    stats = {...}
    result = aggregate_by_day_of_week(stats)
    assert result["Monday"]["commits"] == expected_value
```

**Agent 2 Tests**:
```python
# test_author_mapper.py
def test_alias_resolution():
    mapper = AuthorMapper("test_aliases.json")
    assert mapper.get_canonical_name("brianaronowitzopen2") == "brianaronowitz"

def test_stats_merging():
    stats1 = {"commits": 10}
    stats2 = {"commits": 15}
    merged = mapper.merge_stats([stats1, stats2])
    assert merged["commits"] == 25
```

**Agent 3 Tests**:
```python
# test_pr_metrics.py
def test_search_query_builder():
    query = build_pr_query("opened", "user", "2024-01-01", "2024-12-31")
    assert "type:pr" in query
    assert "author:user" in query
```

### Integration Tests (Requires All Agents)
```python
# test_integration.py
def test_full_pipeline():
    # Requires all modules complete
    result = analyze_weekly_performance("Open-CA", ["iOS-Open"], "aliases.json")
    assert "Monday" in result
    assert "brianaronowitz" in result
```

---

## Progress Tracking Commands

### Check Individual Agent Progress
```bash
# For each agent, check their status
cat agent1_status.json | jq '.completed_functions'
cat agent2_status.json | jq '.status'
cat agent3_status.json | jq '.blocking_issues'

# Check git branches
git branch -a | grep feature/
```

### Validate Module Interfaces
```python
# validate_interfaces.py
import importlib

modules = [
    ("weekly_performance_analyzer", ["WeeklyPerformanceAnalyzer"]),
    ("author_mapper", ["AuthorMapper"]),
    ("pr_metrics", ["PRMetrics"])
]

for module_name, expected_classes in modules:
    try:
        module = importlib.import_module(module_name)
        for cls in expected_classes:
            assert hasattr(module, cls), f"Missing {cls} in {module_name}"
        print(f"✓ {module_name}")
    except ImportError:
        print(f"✗ {module_name} not found")
```

---

## Context7 Usage for Each Agent

### Optimal Context7 Queries

**For Date/Time Operations**:
```bash
mcp__context7__resolve-library-id --query "python datetime timezone"
mcp__context7__get-library-docs --library datetime --section "weekday"
```

**For API Integration**:
```bash
mcp__context7__resolve-library-id --query "requests authentication headers"
mcp__context7__get-library-docs --library requests --section "Session"
```

**For Data Processing**:
```bash
mcp__context7__resolve-library-id --query "pandas groupby aggregate"
mcp__context7__get-library-docs --library pandas --section "DataFrame.groupby"
```

---

## Coordination Protocol

### Communication Between Agents

1. **Shared Constants File** (`shared_constants.py`):
```python
# Created by any agent, used by all
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DATE_FORMAT = "%Y-%m-%d"
API_BASE = "https://api.github.com"
```

2. **Interface Contracts** (`interfaces.py`):
```python
from typing import Protocol, Dict, List

class StatsProvider(Protocol):
    def get_stats(self, username: str, repo: str) -> Dict:
        ...

class AuthorMapper(Protocol):
    def get_canonical_name(self, username: str) -> str:
        ...
```

3. **Mock Data for Testing** (`mock_data.py`):
```python
# Allows agents to test independently
MOCK_CONTRIBUTOR_STATS = {
    "brianaronowitzopen": {...},
    "dan-wu-open": {...}
}
```

---

## Success Criteria

### Individual Agent Success
- [ ] Agent 1: Day-of-week aggregation working with test data
- [ ] Agent 2: Alias resolution correctly maps all known duplicates
- [ ] Agent 3: PR queries return valid data from GitHub API
- [ ] Agent 4: Integration produces readable markdown table

### Overall Project Success
- [ ] All modules pass unit tests
- [ ] Integration tests pass
- [ ] Output matches expected format
- [ ] Performance: <30 seconds for full analysis
- [ ] Documentation complete for all modules

---

## Quick Start for Each Agent

```bash
# Agent 1 Quick Start
echo "Starting Core Statistics Development"
touch weekly_performance_analyzer.py
echo "# Weekly Performance Analyzer" > weekly_performance_analyzer.py
# Focus: Lines 11-27 of original spec

# Agent 2 Quick Start  
echo "Starting Author Alias System"
touch author_mapper.py author_aliases.json
echo "# Author Mapping System" > author_mapper.py
# Focus: Lines 29-42 of original spec

# Agent 3 Quick Start
echo "Starting PR Metrics Module"
touch pr_metrics.py
echo "# Pull Request Metrics" > pr_metrics.py
# Focus: Lines 44-49 of original spec

# Agent 4 Quick Start
echo "Waiting for other agents..."
# Watch for completion signals from agents 1-3
# Then begin integration
```

This specification enables true parallel development with clear boundaries, context7 integration points, and progress tracking mechanisms.