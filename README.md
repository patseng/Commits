# GitHub Contributors Statistics Fetcher

This script fetches contributor statistics from GitHub repositories using the official GitHub API.

## Setup

1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" 
   - Select scopes: `public_repo` (or `repo` for private repositories)
   - Copy the generated token

2. Create a `.credentials.json` file:
   ```bash
   cp .credentials.json.example .credentials.json
   ```
   Then edit it and add your token.

3. Install dependencies:
   ```bash
   pip install requests
   ```

## Usage

Run the script:
```bash
python github_stats.py
```

The script will:
- Fetch contributor statistics for the Open-CA/iOS-Open repository
- Display a summary of each contributor's commits, additions, and deletions
- Save the data to both CSV and JSON formats

## Output Files

- `contributor_stats.csv` - Weekly statistics in CSV format
- `contributor_stats.json` - Weekly statistics in JSON format

## Customization

Edit the configuration variables in `github_stats.py`:
- `OWNER`: Repository owner
- `REPO`: Repository name  
- `WEEKS_TO_FETCH`: Number of weeks of history to fetch

## Why Use the API?

Using GitHub's official API is the proper way to access this data because:
- It's legal and complies with GitHub's Terms of Service
- It's more reliable and won't break when GitHub updates their UI
- It respects rate limits and won't get your IP blocked
- It provides structured data that's easier to process