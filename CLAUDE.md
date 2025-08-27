# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based GitHub statistics analyzer that fetches and visualizes contributor statistics from GitHub repositories using the GitHub API. The main purpose is to track commit activity, additions, and deletions over time.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

- **main.py**: Entry point with CLI argument parsing and orchestration
- **github_stats.py**: GitHub API interface for fetching contributor statistics
- **exporters.py**: Handles exporting data to various formats (CSV, JSON, console)
- **visualizer.py**: Matplotlib-based visualization including interactive charts, dashboards, and heatmaps
- **contributor_lines_analyzer.py**: Specialized analyzer for line contribution analysis

Data flow: GitHub API → github_stats → main.py → exporters/visualizer → output files

## Development Commands

### Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Basic usage - fetch stats for default repository (Open-CA/iOS-Open)
python main.py

# Fetch stats for a specific repository
python main.py --owner OWNER --repo REPO

# Generate visualization with specific weeks
python main.py --chart --chart-weeks 12

# Launch interactive visualizer
python main.py --visualize --viz-mode interactive

# Export to specific format
python main.py --format json  # Options: console, csv, json, all
```

### Common Development Tasks
```bash
# Run with different view modes
python main.py --view user    # User-centric view
python main.py --view week    # Week-centric view  
python main.py --view both    # Both views (default)

# Analyze specific number of weeks
python main.py --weeks 52

# Exclude specific authors from visualization
python main.py --chart --exclude-authors bot-user another-bot
```

## Configuration

### Required Credentials
Create `.credentials.json` in the project root:
```json
{
  "github_token": "your_github_personal_access_token"
}
```

Token scopes needed:
- `public_repo` for public repositories
- `repo` for private repositories

## Output Files

All outputs are saved to the `output/` directory:
- `contributor_stats.csv/json` - User-centric weekly statistics
- `weekly_stats.csv/json` - Week-centric aggregated statistics
- `commit_chart_*.png` - Generated visualization charts

## Key Implementation Details

- The GitHub API may return 202 status when calculating stats - the code handles retries automatically
- Default excludes `o-p-e-n-ios` and `openEngBot` from visualizations (bot accounts)
- Supports multiple visualization modes: interactive plots, comparison dashboards, and activity heatmaps
- Weekly statistics are aggregated from individual contributor data
- All timestamps are handled as Unix timestamps from the GitHub API