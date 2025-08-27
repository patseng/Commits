#!/usr/bin/env python3
"""Unit tests for weekly performance analyzer date conversion utilities"""

import unittest
from datetime import datetime
from weekly_performance_analyzer import WeeklyPerformanceAnalyzer


class TestWeeklyStatsDateConversion(unittest.TestCase):
    """Test cases for day-of-week conversion functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = WeeklyPerformanceAnalyzer(
            owner="test",
            repos=["test-repo"],
            token="test-token"
        )
    
    def test_day_of_week_conversion(self):
        """Test converting Unix timestamp to day name"""
        # Test known dates (using UTC timestamps)
        # January 1, 2024 00:00 UTC was a Monday
        monday_timestamp = 1704067200  # This is actually Sunday in UTC, let's fix
        monday_timestamp = 1704096000  # Monday, January 1, 2024 00:00 UTC
        self.assertEqual(
            self.analyzer.get_day_name(monday_timestamp),
            "Monday"
        )
        
        # January 2, 2024 00:00 UTC was a Tuesday
        tuesday_timestamp = 1704182400
        self.assertEqual(
            self.analyzer.get_day_name(tuesday_timestamp),
            "Tuesday"
        )
        
        # January 3, 2024 00:00 UTC was a Wednesday
        wednesday_timestamp = 1704268800
        self.assertEqual(
            self.analyzer.get_day_name(wednesday_timestamp),
            "Wednesday"
        )
        
        # January 7, 2024 00:00 UTC was a Sunday
        sunday_timestamp = 1704614400
        self.assertEqual(
            self.analyzer.get_day_name(sunday_timestamp),
            "Sunday"
        )
    
    def test_get_day_of_week_stats(self):
        """Test getting both day name and weekday number"""
        # January 1, 2024 00:00 UTC was a Monday (weekday 0)
        monday_timestamp = 1704096000
        day_name, weekday_num = self.analyzer.get_day_of_week_stats(monday_timestamp)
        self.assertEqual(day_name, "Monday")
        self.assertEqual(weekday_num, 0)
        
        # January 5, 2024 00:00 UTC was a Friday (weekday 4)
        friday_timestamp = 1704441600
        day_name, weekday_num = self.analyzer.get_day_of_week_stats(friday_timestamp)
        self.assertEqual(day_name, "Friday")
        self.assertEqual(weekday_num, 4)
    
    def test_edge_cases(self):
        """Test edge cases for timestamp conversion"""
        # Test with 0 timestamp
        self.assertEqual(
            self.analyzer.get_day_name(0),
            "Unknown"
        )
        
        # Test with None (though type hints suggest int)
        self.assertEqual(
            self.analyzer.get_day_name(None),
            "Unknown"
        )
    
    def test_aggregation(self):
        """Test aggregation by day of week"""
        # Create test data with proper UTC timestamps
        test_stats = [
            {'w': 1704096000, 'c': 10, 'a': 100, 'd': 50},  # Monday Jan 1, 2024
            {'w': 1704182400, 'c': 15, 'a': 200, 'd': 75},  # Tuesday Jan 2, 2024
            {'w': 1704700800, 'c': 5, 'a': 50, 'd': 25},    # Monday Jan 8, 2024
        ]
        
        result = self.analyzer.aggregate_by_day_of_week(test_stats)
        
        # Check Monday has combined stats
        self.assertEqual(result['Monday']['commits'], 15)  # 10 + 5
        self.assertEqual(result['Monday']['additions'], 150)  # 100 + 50
        self.assertEqual(result['Monday']['deletions'], 75)  # 50 + 25
        
        # Check Tuesday
        self.assertEqual(result['Tuesday']['commits'], 15)
        self.assertEqual(result['Tuesday']['additions'], 200)
        self.assertEqual(result['Tuesday']['deletions'], 75)
        
        # Check that other days are zero
        self.assertEqual(result['Wednesday']['commits'], 0)
        self.assertEqual(result['Thursday']['commits'], 0)
        self.assertEqual(result['Friday']['commits'], 0)
        self.assertEqual(result['Saturday']['commits'], 0)
        self.assertEqual(result['Sunday']['commits'], 0)
    
    def test_aggregation_empty_stats(self):
        """Test aggregation with empty statistics"""
        result = self.analyzer.aggregate_by_day_of_week([])
        
        # All days should have zero stats
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            self.assertEqual(result[day]['commits'], 0)
            self.assertEqual(result[day]['additions'], 0)
            self.assertEqual(result[day]['deletions'], 0)
    
    def test_day_breakdown_generation(self):
        """Test generating day breakdown for an author"""
        author_stats = {
            'Monday': {'commits': 10, 'additions': 100, 'deletions': 50},
            'Friday': {'commits': 20, 'additions': 300, 'deletions': 100}
        }
        
        result = self.analyzer.generate_day_breakdown(author_stats)
        
        # Check that specified days have correct values
        self.assertEqual(result['Monday']['commits'], 10)
        self.assertEqual(result['Friday']['commits'], 20)
        
        # Check that unspecified days have zero values
        self.assertEqual(result['Tuesday']['commits'], 0)
        self.assertEqual(result['Wednesday']['commits'], 0)
        self.assertEqual(result['Thursday']['commits'], 0)
        self.assertEqual(result['Saturday']['commits'], 0)
        self.assertEqual(result['Sunday']['commits'], 0)


if __name__ == '__main__':
    unittest.main()