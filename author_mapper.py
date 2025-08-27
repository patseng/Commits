"""
Author Mapping System for GitHub Statistics

This module provides functionality to map multiple GitHub usernames to canonical author names,
allowing proper attribution and statistics aggregation for users with multiple accounts.
"""

import json
import os
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict


class AuthorMapper:
    """
    Maps GitHub usernames to canonical author names and merges statistics for aliased users.
    """
    
    def __init__(self, aliases_file: str = "author_aliases.json"):
        """
        Initialize the AuthorMapper with an aliases configuration file.
        
        Args:
            aliases_file: Path to JSON file containing author alias mappings
        """
        self.aliases_file = aliases_file
        self.aliases: Dict[str, List[str]] = self.load_aliases(aliases_file)
        self.username_to_canonical: Dict[str, str] = self.build_reverse_mapping()
    
    def load_aliases(self, aliases_file: str) -> Dict[str, List[str]]:
        """
        Load author aliases from a JSON configuration file.
        
        Args:
            aliases_file: Path to the JSON file containing aliases
            
        Returns:
            Dictionary mapping canonical names to lists of aliases
        """
        if not os.path.exists(aliases_file):
            print(f"Warning: Aliases file '{aliases_file}' not found. Using empty mappings.")
            return {}
        
        try:
            with open(aliases_file, 'r') as f:
                aliases = json.load(f)
                # Ensure all values are lists
                for key, value in aliases.items():
                    if not isinstance(value, list):
                        aliases[key] = [value]
                return aliases
        except json.JSONDecodeError as e:
            print(f"Error parsing aliases file: {e}")
            return {}
        except Exception as e:
            print(f"Error loading aliases file: {e}")
            return {}
    
    def build_reverse_mapping(self) -> Dict[str, str]:
        """
        Build a reverse mapping from usernames to canonical names.
        
        Returns:
            Dictionary mapping each username (including aliases) to its canonical name
        """
        username_to_canonical = {}
        
        for canonical_name, aliases in self.aliases.items():
            # Map each alias to the canonical name
            for alias in aliases:
                # Handle case-insensitive matching
                username_to_canonical[alias.lower()] = canonical_name
            
            # Also map the canonical name to itself (case-insensitive)
            username_to_canonical[canonical_name.lower()] = canonical_name
        
        return username_to_canonical
    
    def get_canonical_name(self, username: str) -> str:
        """
        Map a GitHub username to its canonical author name.
        
        Args:
            username: GitHub username to map
            
        Returns:
            Canonical author name (returns original username if no mapping exists)
        """
        if not username:
            return username
        
        # Check for case-insensitive match
        canonical = self.username_to_canonical.get(username.lower())
        
        if canonical:
            return canonical
        
        # If no mapping exists, return the original username
        return username
    
    def is_aliased(self, username: str) -> bool:
        """
        Check if a username has an alias mapping.
        
        Args:
            username: GitHub username to check
            
        Returns:
            True if the username has an alias mapping, False otherwise
        """
        return username.lower() in self.username_to_canonical
    
    def get_all_aliases(self, canonical_name: str) -> List[str]:
        """
        Get all aliases for a canonical author name.
        
        Args:
            canonical_name: Canonical author name
            
        Returns:
            List of all aliases (including the canonical name itself)
        """
        if canonical_name in self.aliases:
            aliases = self.aliases[canonical_name].copy()
            # Ensure canonical name is included
            if canonical_name not in aliases:
                aliases.append(canonical_name)
            return aliases
        return [canonical_name]
    
    def merge_author_stats(self, stats_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine statistics for aliased usernames.
        
        Args:
            stats_list: List of statistics dictionaries with 'author' field
            
        Returns:
            Merged statistics list with aliased authors combined
        """
        if not stats_list:
            return stats_list
        
        # Group statistics by canonical name
        grouped_stats: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for stats in stats_list:
            author = stats.get('author', stats.get('username', ''))
            if not author:
                continue
            
            canonical_name = self.get_canonical_name(author)
            grouped_stats[canonical_name].append(stats)
        
        # Merge statistics for each canonical author
        merged_results = []
        
        for canonical_name, author_stats_list in grouped_stats.items():
            if len(author_stats_list) == 1:
                # No merging needed, just update the author name
                merged_stat = author_stats_list[0].copy()
                merged_stat['author'] = canonical_name
                merged_stat['original_authors'] = [author_stats_list[0].get('author', canonical_name)]
                merged_results.append(merged_stat)
            else:
                # Merge multiple statistics
                merged_stat = self._merge_stats_entries(author_stats_list, canonical_name)
                merged_results.append(merged_stat)
        
        return merged_results
    
    def _merge_stats_entries(self, stats_entries: List[Dict[str, Any]], canonical_name: str) -> Dict[str, Any]:
        """
        Merge multiple statistics entries into a single entry.
        
        Args:
            stats_entries: List of statistics dictionaries to merge
            canonical_name: Canonical name for the merged entry
            
        Returns:
            Single merged statistics dictionary
        """
        # Start with a copy of the first entry as template
        merged = stats_entries[0].copy()
        merged['author'] = canonical_name
        merged['original_authors'] = []
        
        # Track which fields to sum
        numeric_fields = {'commits', 'additions', 'deletions', 'total_commits', 
                         'total_additions', 'total_deletions', 'lines_added', 
                         'lines_removed', 'net_lines'}
        
        # Initialize numeric fields to 0
        for field in numeric_fields:
            if field in merged:
                merged[field] = 0
        
        # Track weekly statistics if present
        weekly_stats_merged = defaultdict(lambda: {'commits': 0, 'additions': 0, 'deletions': 0})
        
        # Merge all entries
        for entry in stats_entries:
            # Track original authors
            original_author = entry.get('author', entry.get('username', ''))
            if original_author:
                merged['original_authors'].append(original_author)
            
            # Sum numeric fields
            for field in numeric_fields:
                if field in entry:
                    merged[field] += entry[field]
            
            # Merge weekly statistics if present
            if 'weeks' in entry:
                for week in entry['weeks']:
                    week_key = week.get('w', week.get('week', 0))
                    weekly_stats_merged[week_key]['commits'] += week.get('c', week.get('commits', 0))
                    weekly_stats_merged[week_key]['additions'] += week.get('a', week.get('additions', 0))
                    weekly_stats_merged[week_key]['deletions'] += week.get('d', week.get('deletions', 0))
        
        # Convert weekly stats back to list format if needed
        if weekly_stats_merged:
            merged['weeks'] = [
                {
                    'w': week_key,
                    'c': stats['commits'],
                    'a': stats['additions'],
                    'd': stats['deletions']
                }
                for week_key, stats in sorted(weekly_stats_merged.items())
            ]
        
        # Remove duplicates from original_authors
        merged['original_authors'] = list(set(merged['original_authors']))
        
        return merged
    
    def group_by_canonical_author(self, stats_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Group statistics by canonical author name.
        
        Args:
            stats_dict: Dictionary containing statistics with author information
            
        Returns:
            Dictionary with statistics grouped by canonical author names
        """
        grouped = defaultdict(list)
        
        for key, value in stats_dict.items():
            # Extract author from the key or value
            if isinstance(value, dict) and 'author' in value:
                author = value['author']
            elif isinstance(key, str) and '/' in key:
                # Assume format like "repo/author"
                author = key.split('/')[-1]
            else:
                author = key
            
            canonical_name = self.get_canonical_name(author)
            grouped[canonical_name].append((key, value))
        
        # Rebuild the result dictionary
        result = {}
        for canonical_name, entries in grouped.items():
            if len(entries) == 1:
                key, value = entries[0]
                if isinstance(value, dict):
                    value = value.copy()
                    value['author'] = canonical_name
                result[key] = value
            else:
                # Merge multiple entries
                values_to_merge = [entry[1] for entry in entries]
                if all(isinstance(v, dict) for v in values_to_merge):
                    merged_value = self._merge_stats_entries(values_to_merge, canonical_name)
                    # Use canonical name as key
                    result[canonical_name] = merged_value
                else:
                    # If not all values are dictionaries, just use the first one
                    result[canonical_name] = entries[0][1]
        
        return result
    
    def add_alias(self, canonical_name: str, new_alias: str) -> None:
        """
        Add a new alias for a canonical author name.
        
        Args:
            canonical_name: Canonical author name
            new_alias: New alias to add
        """
        if canonical_name not in self.aliases:
            self.aliases[canonical_name] = []
        
        if new_alias not in self.aliases[canonical_name]:
            self.aliases[canonical_name].append(new_alias)
            # Update reverse mapping
            self.username_to_canonical[new_alias.lower()] = canonical_name
    
    def save_aliases(self) -> None:
        """
        Save the current aliases back to the JSON file.
        """
        try:
            with open(self.aliases_file, 'w') as f:
                json.dump(self.aliases, f, indent=2, sort_keys=True)
                f.write('\n')
            print(f"Aliases saved to {self.aliases_file}")
        except Exception as e:
            print(f"Error saving aliases: {e}")
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current alias mappings.
        
        Returns:
            Dictionary containing mapping statistics
        """
        total_canonical = len(self.aliases)
        total_aliases = sum(len(aliases) for aliases in self.aliases.values())
        
        return {
            'total_canonical_authors': total_canonical,
            'total_aliases': total_aliases,
            'total_mappings': len(self.username_to_canonical),
            'authors_with_multiple_aliases': sum(
                1 for aliases in self.aliases.values() if len(aliases) > 1
            )
        }


def main():
    """
    Example usage and testing of the AuthorMapper.
    """
    # Create mapper instance
    mapper = AuthorMapper("author_aliases.json")
    
    # Test canonical name resolution
    test_usernames = [
        "brianaronowitzopen",
        "brianaronowitzopen2",
        "dan-wu-open",
        "patseng",
        "unknown-user"
    ]
    
    print("Username Mapping Tests:")
    print("-" * 40)
    for username in test_usernames:
        canonical = mapper.get_canonical_name(username)
        is_mapped = " (mapped)" if mapper.is_aliased(username) else " (no mapping)"
        print(f"{username:<25} -> {canonical}{is_mapped}")
    
    print("\nStatistics Summary:")
    print("-" * 40)
    summary = mapper.get_statistics_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Example of merging statistics
    sample_stats = [
        {'author': 'brianaronowitzopen', 'commits': 10, 'additions': 100, 'deletions': 50},
        {'author': 'brianaronowitzopen2', 'commits': 5, 'additions': 50, 'deletions': 25},
        {'author': 'dan-wu', 'commits': 15, 'additions': 150, 'deletions': 75},
        {'author': 'patseng', 'commits': 20, 'additions': 200, 'deletions': 100},
    ]
    
    print("\nMerging Statistics Example:")
    print("-" * 40)
    print("Before merging:")
    for stat in sample_stats:
        print(f"  {stat['author']}: {stat['commits']} commits")
    
    merged_stats = mapper.merge_author_stats(sample_stats)
    print("\nAfter merging:")
    for stat in merged_stats:
        print(f"  {stat['author']}: {stat['commits']} commits")
        if 'original_authors' in stat and len(stat['original_authors']) > 1:
            print(f"    (merged from: {', '.join(stat['original_authors'])})")


if __name__ == "__main__":
    main()