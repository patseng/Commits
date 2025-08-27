#!/usr/bin/env python3
"""
Interactive visualization module for GitHub statistics
Supports toggling between commits, additions, and deletions metrics
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal
import numpy as np
import warnings

# Handle matplotlib import gracefully
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.widgets import RadioButtons, CheckButtons, Slider, Button
    from matplotlib.table import Table
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available. Console visualization only.")

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Default excluded authors (bots)
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


class InteractiveVisualizer:
    """Interactive matplotlib visualizer for GitHub statistics"""
    
    def __init__(self, stats_data: Dict, weekly_aggregates: Dict = None):
        """
        Initialize visualizer with contributor and weekly data
        
        Args:
            stats_data: Dictionary of contributor statistics
            weekly_aggregates: Optional weekly aggregated data
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for interactive visualization")
            
        self.stats_data = filter_authors(stats_data)
        self.weekly_aggregates = weekly_aggregates
        self.current_metric = 'commits'
        self.selected_contributors = []
        self.weeks_to_show = 12
        
        # Setup figure and axes references
        self.fig = None
        self.ax_main = None
        self.line_objects = {}
        
        # Color palette for contributors
        self.colors = plt.cm.tab20(np.linspace(0, 1, 20))
        self.contributor_colors = {}
        
    def create_interactive_plot(self):
        """Create main plot window with interactive controls"""
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.suptitle('GitHub Repository Statistics Visualizer', fontsize=16)
        
        # Main plot area (adjusting for control panels)
        self.ax_main = plt.axes([0.25, 0.2, 0.65, 0.65])
        
        # Create control panels
        self._create_metric_selector()
        self._create_contributor_selector()
        self._create_week_slider()
        self._create_export_button()
        
        # Initial plot
        self.update_plot()
        
        plt.show()
    
    def _create_metric_selector(self):
        """Create radio buttons for metric selection"""
        rax = plt.axes([0.025, 0.6, 0.15, 0.15], facecolor='lightgray')
        self.radio = RadioButtons(rax, ('Commits', 'Additions', 'Deletions'))
        self.radio.on_clicked(self.update_metric)
        
    def _create_contributor_selector(self):
        """Create checkboxes for contributor selection"""
        cax = plt.axes([0.025, 0.25, 0.15, 0.3], facecolor='lightgray')
        
        # Get top 10 contributors by total commits
        contributors = self._get_top_contributors(10)
        self.selected_contributors = contributors[:5]  # Select top 5 by default
        
        # Assign colors to contributors
        for i, contrib in enumerate(contributors):
            self.contributor_colors[contrib] = self.colors[i % len(self.colors)]
        
        visibility = [c in self.selected_contributors for c in contributors]
        self.check = CheckButtons(cax, contributors, visibility)
        self.check.on_clicked(self.toggle_contributor)
        
    def _create_week_slider(self):
        """Create slider for adjusting time range"""
        ax_slider = plt.axes([0.25, 0.05, 0.65, 0.03])
        self.slider = Slider(
            ax_slider, 'Weeks to Display', 
            4, 52, valinit=self.weeks_to_show, valstep=1
        )
        self.slider.on_changed(self.update_weeks)
        
    def _create_export_button(self):
        """Create export button"""
        ax_button = plt.axes([0.025, 0.05, 0.15, 0.04])
        self.btn_export = Button(ax_button, 'Export Chart')
        self.btn_export.on_clicked(self.export_chart)
    
    def _get_top_contributors(self, n: int) -> List[str]:
        """Get top N contributors by total commits"""
        contributor_totals = {}
        for contributor, weeks in self.stats_data.items():
            total = sum(w.get('commits', 0) for w in weeks)
            contributor_totals[contributor] = total
        
        sorted_contributors = sorted(contributor_totals.items(), 
                                   key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_contributors[:n]]
    
    def update_metric(self, label):
        """Update displayed metric based on radio button selection"""
        self.current_metric = label.lower()
        self.update_plot()
        
    def toggle_contributor(self, label):
        """Toggle contributor visibility"""
        if label in self.selected_contributors:
            self.selected_contributors.remove(label)
        else:
            self.selected_contributors.append(label)
        self.update_plot()
        
    def update_weeks(self, val):
        """Update number of weeks displayed"""
        self.weeks_to_show = int(val)
        self.update_plot()
        
    def update_plot(self):
        """Redraw the plot with current settings"""
        self.ax_main.clear()
        
        # Get data for selected contributors and metric
        plot_data = self._prepare_plot_data()
        
        # Plot lines for each contributor
        for contributor, data in plot_data.items():
            weeks = data['weeks']
            values = data['values']
            color = data['color']
            
            self.ax_main.plot(weeks, values, 
                            label=contributor, 
                            color=color, 
                            marker='o', 
                            linewidth=2,
                            markersize=6,
                            alpha=0.8)
        
        # Formatting
        self.ax_main.set_xlabel('Week', fontsize=12)
        self.ax_main.set_ylabel(self.current_metric.capitalize(), fontsize=12)
        self.ax_main.set_title(f'{self.current_metric.capitalize()} Over Time', fontsize=14)
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend(loc='best', fontsize=10)
        
        # Rotate x-axis labels for better readability
        plt.setp(self.ax_main.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add summary statistics
        self._add_summary_text()
        
        self.fig.canvas.draw_idle()
    
    def _prepare_plot_data(self) -> Dict[str, Dict]:
        """Prepare data for plotting"""
        plot_data = {}
        
        for contributor in self.selected_contributors:
            if contributor not in self.stats_data:
                continue
                
            weeks_data = self.stats_data[contributor][-self.weeks_to_show:]
            
            weeks = []
            values = []
            
            for week_info in weeks_data:
                weeks.append(week_info['week'])
                values.append(week_info.get(self.current_metric, 0))
            
            plot_data[contributor] = {
                'weeks': weeks,
                'values': values,
                'color': self.contributor_colors.get(contributor, 'blue')
            }
        
        return plot_data
    
    def _add_summary_text(self):
        """Add summary statistics to the plot"""
        if not self.selected_contributors:
            return
            
        total = 0
        for contributor in self.selected_contributors:
            if contributor in self.stats_data:
                weeks_data = self.stats_data[contributor][-self.weeks_to_show:]
                total += sum(w.get(self.current_metric, 0) for w in weeks_data)
        
        text = f'Total {self.current_metric}: {total:,}'
        self.ax_main.text(0.98, 0.95, text,
                         transform=self.ax_main.transAxes,
                         fontsize=10,
                         ha='right',
                         va='top',
                         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def export_chart(self, event=None):
        """Export the current chart"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'github_stats_{self.current_metric}_{timestamp}.png'
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart exported to: {filename}")


class ComparisonDashboard:
    """Dashboard showing all three metrics simultaneously"""
    
    def __init__(self, stats_data: Dict, weekly_aggregates: Dict = None):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for comparison dashboard")
            
        self.stats_data = filter_authors(stats_data)
        self.weekly_aggregates = weekly_aggregates
        self.contributors_to_show = 5
        
    def create_dashboard(self, weeks: int = 12):
        """Create a 3-panel dashboard"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        fig.suptitle('GitHub Statistics Comparison Dashboard', fontsize=16, y=0.98)
        
        metrics = ['commits', 'additions', 'deletions']
        colors_map = {
            'commits': '#2E86AB',
            'additions': '#A23B72', 
            'deletions': '#F18F01'
        }
        
        # Get top contributors
        top_contributors = self._get_top_contributors(self.contributors_to_show)
        
        for ax, metric in zip(axes, metrics):
            self._plot_metric_panel(ax, metric, top_contributors, colors_map[metric], weeks)
        
        # Add shared x-label
        axes[-1].set_xlabel('Week', fontsize=12)
        
        # Add legend to top panel only
        axes[0].legend(loc='upper left', fontsize=9, ncol=2)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        
        # Add export button
        ax_button = plt.axes([0.85, 0.01, 0.1, 0.025])
        btn = Button(ax_button, 'Export')
        btn.on_clicked(lambda x: self._export_dashboard())
        
        plt.show()
    
    def _get_top_contributors(self, n: int) -> List[str]:
        """Get top N contributors by total commits"""
        contributor_totals = {}
        for contributor, weeks in self.stats_data.items():
            total = sum(w.get('commits', 0) for w in weeks)
            contributor_totals[contributor] = total
        
        sorted_contributors = sorted(contributor_totals.items(), 
                                   key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_contributors[:n]]
    
    def _plot_metric_panel(self, ax, metric, contributors, base_color, weeks):
        """Plot a single metric panel"""
        # Plot data for each contributor
        for i, contributor in enumerate(contributors):
            data = self._get_contributor_metric_data(contributor, metric, weeks)
            
            # Use color variations for different contributors
            alpha = 0.3 + (0.7 * (i / len(contributors)))
            
            ax.plot(data['weeks'], data['values'],
                   label=contributor if metric == 'commits' else None,
                   alpha=alpha,
                   linewidth=1.5,
                   color=base_color)
        
        # Panel formatting
        ax.set_ylabel(metric.capitalize(), fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add metric totals as text
        total = self._calculate_panel_total(contributors, metric, weeks)
        ax.text(0.98, 0.95, f'Total: {total:,}',
               transform=ax.transAxes,
               fontsize=10,
               ha='right',
               va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _get_contributor_metric_data(self, contributor, metric, weeks):
        """Get metric data for a contributor"""
        if contributor not in self.stats_data:
            return {'weeks': [], 'values': []}
            
        weeks_data = self.stats_data[contributor][-weeks:]
        
        week_labels = []
        values = []
        
        for week_info in weeks_data:
            week_labels.append(week_info['week'])
            values.append(week_info.get(metric, 0))
        
        return {'weeks': week_labels, 'values': values}
    
    def _calculate_panel_total(self, contributors, metric, weeks):
        """Calculate total for a metric across contributors"""
        total = 0
        for contributor in contributors:
            if contributor in self.stats_data:
                weeks_data = self.stats_data[contributor][-weeks:]
                total += sum(w.get(metric, 0) for w in weeks_data)
        return total
    
    def _export_dashboard(self):
        """Export the dashboard"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'github_dashboard_{timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Dashboard exported to: {filename}")


class ActivityHeatmap:
    """Heatmap visualization for activity patterns"""
    
    def __init__(self, stats_data: Dict):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for heatmap visualization")
            
        self.stats_data = filter_authors(stats_data)
        
    def create_heatmap(self, metric: str = 'commits', max_contributors: int = 15):
        """Create activity heatmap"""
        import matplotlib.colors as mcolors
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get contributors and weeks
        contributors = self._get_top_contributors(max_contributors)
        all_weeks = self._get_all_weeks()
        
        # Create matrix for heatmap
        matrix = np.zeros((len(contributors), len(all_weeks)))
        
        for i, contributor in enumerate(contributors):
            if contributor in self.stats_data:
                for week_data in self.stats_data[contributor]:
                    week = week_data['week']
                    if week in all_weeks:
                        j = all_weeks.index(week)
                        matrix[i, j] = week_data.get(metric, 0)
        
        # Create heatmap
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(all_weeks)))
        ax.set_yticks(np.arange(len(contributors)))
        
        # Show every Nth week label to avoid crowding
        n = max(1, len(all_weeks) // 12)
        ax.set_xticklabels([w if i % n == 0 else '' for i, w in enumerate(all_weeks)], 
                           rotation=45, ha='right')
        ax.set_yticklabels(contributors)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(metric.capitalize(), rotation=270, labelpad=20)
        
        # Add title
        ax.set_title(f'Activity Heatmap - {metric.capitalize()}', fontsize=14)
        
        plt.tight_layout()
        
        # Add export button
        ax_button = plt.axes([0.85, 0.01, 0.1, 0.04])
        btn = Button(ax_button, 'Export')
        btn.on_clicked(lambda x: self._export_heatmap(metric))
        
        plt.show()
    
    def _get_top_contributors(self, n: int) -> List[str]:
        """Get top N contributors by total commits"""
        contributor_totals = {}
        for contributor, weeks in self.stats_data.items():
            total = sum(w.get('commits', 0) for w in weeks)
            contributor_totals[contributor] = total
        
        sorted_contributors = sorted(contributor_totals.items(), 
                                   key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_contributors[:n]]
    
    def _get_all_weeks(self) -> List[str]:
        """Get all unique weeks across all contributors"""
        all_weeks = set()
        for weeks_data in self.stats_data.values():
            for week_info in weeks_data:
                all_weeks.add(week_info['week'])
        return sorted(all_weeks)
    
    def _export_heatmap(self, metric):
        """Export the heatmap"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'github_heatmap_{metric}_{timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Heatmap exported to: {filename}")


def generate_console_table(stats: Dict[str, List[Dict]], 
                          weeks: int = 6,
                          exclude_authors: List[str] = None) -> None:
    """Generate a console-friendly table of commit data"""
    
    if exclude_authors is None:
        exclude_authors = EXCLUDED_AUTHORS
    
    filtered_stats = filter_authors(stats, exclude_authors)
    
    # Get all unique weeks from the last N weeks
    all_weeks = set()
    for author_data in filtered_stats.values():
        for week_data in author_data[-weeks:]:
            all_weeks.add(week_data['week'])
    
    if not all_weeks:
        print("No data available for the specified period")
        return
    
    sorted_weeks = sorted(list(all_weeks))[-weeks:]
    week_labels = [datetime.strptime(w, '%Y-%m-%d').strftime('%m/%d') 
                  for w in sorted_weeks]
    
    # Calculate column widths
    col_width = 8
    author_width = 15
    
    print("\nLast {} Weeks Commit Activity (Human Contributors)".format(weeks))
    print("=" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    # Print header
    header = "Author".ljust(author_width) + " | "
    for week in week_labels:
        header += week.center(col_width) + " | "
    header += "Total".center(col_width)
    print(header)
    print("-" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    # Track weekly totals
    weekly_totals = [0] * len(sorted_weeks)
    
    # Get top contributors by total commits
    contributor_totals = {}
    for author, weeks_data in filtered_stats.items():
        week_commits = {w['week']: w['commits'] for w in weeks_data}
        total = sum(week_commits.get(w, 0) for w in sorted_weeks)
        if total > 0:
            contributor_totals[author] = total
    
    # Sort contributors by total commits
    sorted_contributors = sorted(contributor_totals.items(), 
                               key=lambda x: x[1], reverse=True)
    
    # Print data for each contributor
    for author, _ in sorted_contributors[:10]:  # Show top 10
        weeks_data = filtered_stats[author]
        week_commits = {w['week']: w['commits'] for w in weeks_data}
        
        row = author[:author_width].ljust(author_width) + " | "
        author_total = 0
        for i, week in enumerate(sorted_weeks):
            commits = week_commits.get(week, 0)
            row += str(commits).center(col_width) + " | "
            weekly_totals[i] += commits
            author_total += commits
        row += str(author_total).center(col_width)
        print(row)
    
    # Print footer with totals
    print("-" * (author_width + (col_width + 3) * (len(week_labels) + 1)))
    
    totals_row = "Weekly Total".ljust(author_width) + " | "
    for total in weekly_totals:
        totals_row += str(total).center(col_width) + " | "
    totals_row += str(sum(weekly_totals)).center(col_width)
    print(totals_row)
    print()


def generate_commit_line_chart(stats: Dict[str, List[Dict]], 
                              weeks: int = 6,
                              exclude_authors: List[str] = None,
                              output_file: str = None) -> str:
    """Generate line chart with commits per week per author"""
    
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib not installed. Install with: pip install matplotlib")
        print("Showing console table instead.")
        generate_console_table(stats, weeks, exclude_authors)
        return None
    
    if exclude_authors is None:
        exclude_authors = EXCLUDED_AUTHORS
    
    filtered_stats = filter_authors(stats, exclude_authors)
    
    # Prepare chart data
    all_weeks = set()
    for author_data in filtered_stats.values():
        for week_data in author_data:
            all_weeks.add(week_data['week'])
    
    sorted_weeks = sorted(list(all_weeks))
    if len(sorted_weeks) > weeks:
        sorted_weeks = sorted_weeks[-weeks:]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Get top contributors
    contributor_totals = {}
    for author, weeks_data in filtered_stats.items():
        total = sum(w.get('commits', 0) for w in weeks_data)
        contributor_totals[author] = total
    
    sorted_contributors = sorted(contributor_totals.items(), 
                               key=lambda x: x[1], reverse=True)
    top_contributors = [c[0] for c in sorted_contributors[:10]]
    
    # Plot lines
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    
    for idx, author in enumerate(top_contributors):
        weeks_data = filtered_stats[author]
        week_commits = {w['week']: w['commits'] for w in weeks_data}
        
        x_data = []
        y_data = []
        for week in sorted_weeks:
            x_data.append(week)
            y_data.append(week_commits.get(week, 0))
        
        ax.plot(x_data, y_data, 
               marker='o', 
               label=author, 
               color=colors[idx],
               linewidth=2,
               markersize=6,
               alpha=0.8)
    
    # Formatting
    ax.set_xlabel('Week', fontsize=12)
    ax.set_ylabel('Number of Commits', fontsize=12)
    ax.set_title(f'Last {weeks} Weeks Commit Activity', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=9)
    
    # Rotate x-axis labels
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save file
    if output_file is None:
        output_file = f"commit_chart_{weeks}weeks.png"
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {output_file}")
    
    plt.show()
    
    return output_file


# Legacy function for backward compatibility
def prepare_chart_data(stats: Dict[str, List[Dict]], 
                      weeks: int = 6,
                      exclude_authors: List[str] = None) -> Dict[str, Any]:
    """
    Prepare data for chart generation (legacy support)
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


if __name__ == "__main__":
    # Load statistics
    stats = load_stats_from_file()
    
    # Show console table
    generate_console_table(stats, weeks=6)
    
    # Try to show interactive visualizer
    if MATPLOTLIB_AVAILABLE:
        print("\nLaunching interactive visualizer...")
        print("Use radio buttons to switch between Commits, Additions, and Deletions")
        print("Use checkboxes to toggle contributors")
        print("Use slider to adjust time range")
        
        viz = InteractiveVisualizer(stats)
        viz.create_interactive_plot()
    else:
        print("\nInstall matplotlib for interactive charts: pip install matplotlib")