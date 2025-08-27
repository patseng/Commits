# Claude Parallel Execution Guide for Weekly Performance Dashboard

## Corrected Multi-Step Claude Execution Instructions

### Overview
This guide provides the correct way to use Claude for parallel development tasks, replacing the incorrect `claude-agent` commands with proper multi-step Claude usage.

---

## How to Launch Multiple Claude Sessions

### Method 1: Multiple Terminal Windows

**Terminal 1 - Agent 1 (Core Statistics Developer)**
```bash
# Step 1: Launch Claude
claude

# Step 2: Once Claude is running, provide the task
"I need you to implement the Core Statistics Developer tasks from weekly_performance_parallel_execution_spec.md. 
Specifically, create weekly_performance_analyzer.py with:
- WeeklyPerformanceAnalyzer class
- fetch_weekly_commits() method
- aggregate_by_day_of_week() method
Focus on Agent 1 section of the spec."
```

**Terminal 2 - Agent 2 (Author Alias System)**
```bash
# Step 1: Launch Claude
claude

# Step 2: Assign the task
"Please implement the Author Alias System from weekly_performance_parallel_execution_spec.md Agent 2 section.
Create:
- author_mapper.py with AuthorMapper class
- author_aliases.json configuration file
- Methods for username mapping and statistics merging"
```

**Terminal 3 - Agent 3 (PR Metrics Specialist)**
```bash
# Step 1: Launch Claude
claude

# Step 2: Provide the specification
"Implement the PR Metrics module as described in weekly_performance_parallel_execution_spec.md Agent 3 section.
Build pr_metrics.py with:
- PRMetrics class
- GitHub Search API integration
- Methods for get_prs_opened(), get_prs_merged(), get_prs_reviewed()"
```

**Terminal 4 - Agent 4 (Integration Coordinator)**
```bash
# Step 1: Launch Claude (after others complete)
claude

# Step 2: Integration task
"The other agents have completed their modules. Please integrate them according to 
weekly_performance_parallel_execution_spec.md Agent 4 section:
- Update github_stats.py
- Create main orchestration logic
- Build output generators for markdown, CSV, and JSON"
```

---

## Alternative: Sequential Task Assignment in Single Session

If running multiple Claude instances isn't feasible, use a single Claude session with clear task boundaries:

```bash
# Launch Claude once
claude

# Then provide structured task sequence:
"I need help implementing a weekly performance dashboard. Let's work through this systematically:

TASK 1 - Core Statistics (Acting as Agent 1):
Create weekly_performance_analyzer.py with day-of-week aggregation logic.
[Complete this before moving to Task 2]

TASK 2 - Author Aliases (Acting as Agent 2):  
Create author_mapper.py and author_aliases.json for username mapping.
[Complete this before moving to Task 3]

TASK 3 - PR Metrics (Acting as Agent 3):
Build pr_metrics.py for GitHub PR search queries.
[Complete this before moving to Task 4]

TASK 4 - Integration (Acting as Agent 4):
Integrate all modules and create output generators.

Please start with TASK 1."
```

---

## Coordination Between Claude Sessions

### Using File-Based Communication

Each Claude session should create status files to communicate progress:

**In Claude Session 1:**
```python
# After completing a module, create status file
import json
from datetime import datetime

status = {
    "agent": 1,
    "module": "weekly_performance_analyzer.py",
    "status": "completed",
    "completed_functions": [
        "WeeklyPerformanceAnalyzer.__init__",
        "fetch_weekly_commits",
        "aggregate_by_day_of_week"
    ],
    "timestamp": datetime.now().isoformat()
}

with open("agent1_status.json", "w") as f:
    json.dump(status, f, indent=2)
```

**In Claude Session 4 (Integration):**
```python
# Check if other agents are ready
import json
import os

def check_agent_readiness():
    agents_ready = []
    for i in range(1, 4):
        status_file = f"agent{i}_status.json"
        if os.path.exists(status_file):
            with open(status_file) as f:
                status = json.load(f)
                if status["status"] == "completed":
                    agents_ready.append(i)
    
    return len(agents_ready) == 3

if check_agent_readiness():
    print("All agents complete. Starting integration...")
else:
    print("Waiting for other agents to complete...")
```

---

## Task Assignment Templates

### Template for Core Development Tasks

```markdown
Hello Claude,

I'm working on a weekly performance dashboard and need you to implement a specific module.

**Your Role**: [Agent Name]
**Module to Create**: [filename.py]
**Specification Location**: weekly_performance_parallel_execution_spec.md, [Agent N] section

**Key Requirements**:
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

**Dependencies**:
- You can import from: [existing modules]
- You should create: [new functions/classes]

**Testing Requirements**:
- Create unit tests in test_[module].py
- Include mock data for testing

Please implement this module following the specification.
```

### Template for Integration Tasks

```markdown
Hello Claude,

The following modules have been completed by other agents:
- weekly_performance_analyzer.py (core statistics)
- author_mapper.py (username aliasing)
- pr_metrics.py (PR metrics)

**Your Task**: Integrate these modules according to weekly_performance_parallel_execution_spec.md Agent 4 section.

**Integration Points**:
1. Update github_stats.py with wrapper functions
2. Create main orchestration in weekly_performance_analyzer.py
3. Build output generators for multiple formats

**Expected Output**:
- Markdown tables
- CSV export
- JSON structure

Please proceed with the integration.
```

---

## Progress Monitoring Commands

### Check Status Across Sessions

```bash
# In any terminal, monitor all agent status files
watch -n 5 'for f in agent*_status.json; do echo "=== $f ==="; cat $f | jq -r ".status"; done'

# Check which files have been created
ls -la *.py | grep -E "(weekly_performance|author_mapper|pr_metrics)"

# Monitor git status for changes
watch -n 10 'git status --short'
```

### Validate Module Completion

```bash
# Create a validation script
cat > validate_modules.sh << 'EOF'
#!/bin/bash

echo "Checking module completion..."

modules=("weekly_performance_analyzer.py" "author_mapper.py" "pr_metrics.py")
for module in "${modules[@]}"; do
    if [ -f "$module" ]; then
        echo "✓ $module exists"
        python3 -m py_compile "$module" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ Syntax valid"
        else
            echo "  ✗ Syntax errors"
        fi
    else
        echo "✗ $module missing"
    fi
done
EOF

chmod +x validate_modules.sh
./validate_modules.sh
```

---

## Context7 Usage Within Claude

When working in Claude, request documentation using context7 commands:

```markdown
"I need to implement date handling. Please use context7 to get datetime documentation:
mcp__context7__get-library-docs --library datetime

Then implement the day-of-week conversion function."
```

Or for discovering libraries:

```markdown
"I need to make GitHub API calls. Please:
1. Use mcp__context7__resolve-library-id --query 'python github api client'
2. Get documentation for the best library
3. Implement the PR search functionality"
```

---

## Best Practices for Parallel Claude Development

### 1. Clear Task Boundaries
- Each Claude session should have a well-defined scope
- Avoid overlapping responsibilities
- Use interface contracts between modules

### 2. Consistent Naming
All sessions should use these exact names:
```python
# Agreed upon class names
class WeeklyPerformanceAnalyzer  # Not WeeklyAnalyzer or PerformanceAnalyzer
class AuthorMapper               # Not AuthorAliasMapper or UserMapper
class PRMetrics                  # Not PullRequestMetrics or PRStats
```

### 3. Shared Constants
Create a shared file early:
```python
# shared_constants.py (any agent can create this)
GITHUB_API_BASE = "https://api.github.com"
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
```

### 4. Mock Data for Testing
Each agent should create mock data for their module:
```python
# mock_data_stats.py (Agent 1)
MOCK_CONTRIBUTOR_STATS = {...}

# mock_data_aliases.py (Agent 2)
MOCK_ALIASES = {...}

# mock_data_prs.py (Agent 3)
MOCK_PR_RESPONSE = {...}
```

---

## Troubleshooting

### If Claude Sessions Aren't Syncing

1. **Use explicit file paths**:
   ```python
   # Instead of relative imports
   import sys
   sys.path.append('/Users/username/Developer/scripts/commit-bot')
   from author_mapper import AuthorMapper
   ```

2. **Create interface stubs**:
   ```python
   # If author_mapper.py isn't ready yet, create a stub
   class AuthorMapper:
       def get_canonical_name(self, username):
           return username  # Stub implementation
   ```

3. **Use feature branches**:
   ```bash
   # Each agent works in their own branch
   git checkout -b feature/agent1-core-stats
   git checkout -b feature/agent2-author-aliases
   git checkout -b feature/agent3-pr-metrics
   git checkout -b feature/agent4-integration
   ```

---

## Quick Reference Card

| Agent | Module | Key Classes | Dependencies |
|-------|--------|-------------|--------------|
| 1 | weekly_performance_analyzer.py | WeeklyPerformanceAnalyzer | github_stats.py |
| 2 | author_mapper.py | AuthorMapper | json |
| 3 | pr_metrics.py | PRMetrics | requests |
| 4 | Integration | - | All above |

| Command | Purpose |
|---------|---------|
| `claude` | Launch Claude session |
| `cat agent*_status.json` | Check all agent statuses |
| `./validate_modules.sh` | Validate module syntax |
| `git branch -a` | View all feature branches |

---

## Example Full Workflow

```bash
# Terminal 1
claude
# Paste: "Implement Agent 1 from weekly_performance_parallel_execution_spec.md"
# Wait for completion
# Keep session open for fixes

# Terminal 2  
claude
# Paste: "Implement Agent 2 from weekly_performance_parallel_execution_spec.md"
# Wait for completion

# Terminal 3
claude  
# Paste: "Implement Agent 3 from weekly_performance_parallel_execution_spec.md"
# Wait for completion

# Terminal 4 (after 1-3 complete)
claude
# Paste: "Agents 1-3 are complete. Implement Agent 4 integration from spec"

# Terminal 5 (monitoring)
watch -n 5 './validate_modules.sh'
```

This corrected guide provides proper multi-step Claude execution instructions for parallel development of the weekly performance dashboard.