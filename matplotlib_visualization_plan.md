# Matplotlib Visualization Enhancement Plan

## Overview
This document outlines the implementation plan for enhancing the GitHub statistics visualizer using matplotlib to support toggling between different metrics (commits, additions, deletions) with interactive controls.

## Goals
1. Enable metric toggling without re-running the script
2. Support multiple contributors with selection controls
3. Provide comparison views across all three metrics
4. Add export functionality for generated charts
5. Maintain simplicity and command-line compatibility

## Implementation Timeline
**Estimated Duration**: 2-3 days (16-24 development hours)

---

## Phase 1: Core Interactive Visualizer (Day 1)

### 1.1 Create InteractiveVisualizer Class

```python
# visualizer.py
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, CheckButtons, Slider
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal

class InteractiveVisualizer:
    """Interactive matplotlib visualizer for GitHub statistics"""
    
    def __init__(self, stats_data: Dict, weekly_aggregates: Dict = None):
        """
        Initialize visualizer with contributor and weekly data
        
        Args:
            stats_data: Dictionary of contributor statistics
            weekly_aggregates: Optional weekly aggregated data
        """
        self.stats_data = stats_data
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
        from matplotlib.widgets import Button
        ax_button = plt.axes([0.025, 0.05, 0.15, 0.04])
        self.btn_export = Button(ax_button, 'Export Chart')
        self.btn_export.on_clicked(self.export_chart)
```

### 1.2 Implement Update Methods

```python
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
                            markersize=6)
        
        # Formatting
        self.ax_main.set_xlabel('Week', fontsize=12)
        self.ax_main.set_ylabel(self.current_metric.capitalize(), fontsize=12)
        self.ax_main.set_title(f'{self.current_metric.capitalize()} Over Time', fontsize=14)
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend(loc='best', fontsize=10)
        
        # Rotate x-axis labels for better readability
        plt.setp(self.ax_main.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.fig.canvas.draw_idle()
```

---

## Phase 2: Multi-Metric Comparison View (Day 1-2)

### 2.1 Comparison Dashboard

```python
class ComparisonDashboard:
    """Dashboard showing all three metrics simultaneously"""
    
    def __init__(self, stats_data: Dict, weekly_aggregates: Dict = None):
        self.stats_data = stats_data
        self.weekly_aggregates = weekly_aggregates
        self.contributors_to_show = 5
        
    def create_dashboard(self):
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
            self._plot_metric_panel(ax, metric, top_contributors, colors_map[metric])
        
        # Add shared x-label
        axes[-1].set_xlabel('Week', fontsize=12)
        
        # Add legend to top panel only
        axes[0].legend(loc='upper left', fontsize=9, ncol=2)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        plt.show()
    
    def _plot_metric_panel(self, ax, metric, contributors, base_color):
        """Plot a single metric panel"""
        # Plot data for each contributor
        for i, contributor in enumerate(contributors):
            data = self._get_contributor_metric_data(contributor, metric)
            
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
        
        # Add metric totals as text
        total = sum(self._get_metric_total(c, metric) for c in contributors)
        ax.text(0.98, 0.95, f'Total: {total:,}',
               transform=ax.transAxes,
               fontsize=10,
               ha='right',
               va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
```

### 2.2 Heatmap Visualization

```python
    def create_activity_heatmap(self):
        """Create a heatmap showing activity patterns"""
        import matplotlib.colors as mcolors
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data matrix
        contributors = list(self.stats_data.keys())[:15]  # Top 15
        weeks = self._get_all_weeks()
        
        # Create matrix for heatmap
        matrix = np.zeros((len(contributors), len(weeks)))
        
        for i, contributor in enumerate(contributors):
            for j, week in enumerate(weeks):
                matrix[i, j] = self._get_week_value(contributor, week, self.current_metric)
        
        # Create heatmap
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(weeks)))
        ax.set_yticks(np.arange(len(contributors)))
        ax.set_xticklabels(weeks, rotation=45, ha='right')
        ax.set_yticklabels(contributors)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(self.current_metric.capitalize(), rotation=270, labelpad=20)
        
        # Add title
        ax.set_title(f'Activity Heatmap - {self.current_metric.capitalize()}', fontsize=14)
        
        plt.tight_layout()
        plt.show()
```

---

## Phase 3: Export and Utility Functions (Day 2)

### 3.1 Export Functionality

```python
class ExportManager:
    """Handle export of visualizations in various formats"""
    
    @staticmethod
    def export_current_figure(format: Literal['png', 'svg', 'pdf', 'eps'] = 'png',
                            dpi: int = 300,
                            filename: Optional[str] = None):
        """Export the current matplotlib figure"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'github_stats_{timestamp}.{format}'
        
        plt.savefig(filename, format=format, dpi=dpi, bbox_inches='tight')
        print(f"Chart exported to: {filename}")
        return filename
    
    @staticmethod
    def export_data_report(stats_data: Dict, 
                          metric: str,
                          format: Literal['html', 'markdown'] = 'html'):
        """Generate a formatted report with charts and statistics"""
        from io import BytesIO
        import base64
        
        # Generate charts
        charts = []
        for chart_type in ['line', 'bar', 'heatmap']:
            buf = BytesIO()
            # Generate and save chart to buffer
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            charts.append(img_base64)
        
        # Create report template
        if format == 'html':
            return ExportManager._generate_html_report(stats_data, metric, charts)
        else:
            return ExportManager._generate_markdown_report(stats_data, metric, charts)
```

### 3.2 Console Fallback

```python
def generate_console_chart(stats_data: Dict, 
                          metric: str = 'commits',
                          weeks: int = 8,
                          width: int = 60):
    """Generate ASCII chart for console output"""
    print(f"\n{metric.upper()} - Last {weeks} weeks")
    print("=" * width)
    
    # Get data for all contributors
    all_weeks = set()
    contributor_data = {}
    
    for contributor, weeks_data in stats_data.items():
        contributor_data[contributor] = {}
        for week_info in weeks_data[-weeks:]:
            week = week_info['week']
            all_weeks.add(week)
            contributor_data[contributor][week] = week_info.get(metric, 0)
    
    # Sort weeks
    sorted_weeks = sorted(all_weeks)
    
    # Create bar chart
    for contributor in list(contributor_data.keys())[:5]:  # Top 5
        print(f"\n{contributor}:")
        for week in sorted_weeks:
            value = contributor_data[contributor].get(week, 0)
            bar_length = int((value / max_value) * (width - 20)) if max_value > 0 else 0
            bar = '█' * bar_length
            print(f"  {week}: {bar} {value}")
```

---

## File Structure

```
commit-bot/
├── visualizer.py              # Main visualization module
│   ├── InteractiveVisualizer  # Interactive plotting class
│   ├── ComparisonDashboard    # Multi-metric dashboard
│   └── ExportManager          # Export functionality
├── visualizer_utils.py        # Helper functions
│   ├── data_processing        # Data preparation functions
│   ├── color_schemes          # Color palette management
│   └── formatting             # Axis and label formatting
├── console_viz.py             # ASCII/console visualization
└── examples/
    ├── example_interactive.py # Example usage scripts
    └── example_dashboard.py
```

---

## Integration with Main Application

### Update main.py

```python
# main.py additions
def main():
    # ... existing code ...
    
    parser.add_argument('--visualize', action='store_true',
                       help='Launch interactive visualizer')
    parser.add_argument('--viz-mode', choices=['interactive', 'dashboard', 'heatmap'],
                       default='interactive',
                       help='Visualization mode')
    parser.add_argument('--viz-metric', choices=['commits', 'additions', 'deletions'],
                       default='commits',
                       help='Initial metric to display')
    
    args = parser.parse_args()
    
    # ... existing code ...
    
    if args.visualize:
        from visualizer import InteractiveVisualizer, ComparisonDashboard
        
        if args.viz_mode == 'interactive':
            viz = InteractiveVisualizer(weekly_stats, weekly_aggregates)
            viz.current_metric = args.viz_metric
            viz.create_interactive_plot()
        elif args.viz_mode == 'dashboard':
            dashboard = ComparisonDashboard(weekly_stats, weekly_aggregates)
            dashboard.create_dashboard()
        elif args.viz_mode == 'heatmap':
            viz = InteractiveVisualizer(weekly_stats, weekly_aggregates)
            viz.current_metric = args.viz_metric
            viz.create_activity_heatmap()
```

---

## Usage Examples

### Basic Interactive Mode
```bash
# Launch interactive visualizer with default settings
python main.py --visualize

# Start with additions metric selected
python main.py --visualize --viz-metric additions

# Launch comparison dashboard
python main.py --visualize --viz-mode dashboard
```

### Programmatic Usage
```python
from visualizer import InteractiveVisualizer
from github_stats import fetch_contributor_stats, process_statistics

# Fetch data
contributors = fetch_contributor_stats(owner, repo, token)
weekly_stats = process_statistics(contributors, weeks=26)

# Create interactive plot
viz = InteractiveVisualizer(weekly_stats)
viz.create_interactive_plot()

# Export current view
viz.export_chart('png')
```

---

## Testing Plan

### Unit Tests
```python
# test_visualizer.py
import unittest
from visualizer import InteractiveVisualizer

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            'user1': [
                {'week': '2024-01-01', 'commits': 5, 'additions': 100, 'deletions': 50},
                {'week': '2024-01-08', 'commits': 3, 'additions': 75, 'deletions': 25}
            ]
        }
        
    def test_metric_switching(self):
        viz = InteractiveVisualizer(self.test_data)
        viz.update_metric('Additions')
        self.assertEqual(viz.current_metric, 'additions')
        
    def test_contributor_selection(self):
        viz = InteractiveVisualizer(self.test_data)
        viz.toggle_contributor('user1')
        self.assertIn('user1', viz.selected_contributors)
```

### Manual Testing Checklist
- [ ] Metric radio buttons switch correctly
- [ ] Contributor checkboxes toggle visibility
- [ ] Week slider adjusts time range
- [ ] Export generates files correctly
- [ ] Charts render without errors
- [ ] Performance acceptable with 50+ contributors

---

## Performance Considerations

### Optimization Strategies
1. **Data Caching**: Cache processed data to avoid recalculation
2. **Lazy Loading**: Only process visible contributors
3. **Decimation**: Reduce data points for large time ranges
4. **Blitting**: Use matplotlib blitting for smoother updates

```python
class OptimizedVisualizer(InteractiveVisualizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.use_blitting = True
        
    def _prepare_plot_data(self):
        cache_key = (self.current_metric, tuple(self.selected_contributors), self.weeks_to_show)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Process data
        data = super()._prepare_plot_data()
        self.cache[cache_key] = data
        return data
```

---

## Known Limitations

1. **GUI Requirements**: Requires display server (won't work in pure SSH)
2. **Responsiveness**: May lag with 100+ contributors
3. **Memory Usage**: Large datasets may consume significant RAM
4. **Platform Differences**: Widget appearance varies by OS

### Workarounds
- Use `matplotlib.use('Agg')` for headless operation
- Implement data pagination for large datasets
- Add data sampling options for performance
- Provide console fallback for SSH environments

---

## Future Enhancements

1. **Animation**: Animate transitions between metrics
2. **Annotations**: Click points to show detailed information
3. **Trend Lines**: Add regression/moving averages
4. **Predictive Analytics**: Forecast future activity
5. **Team Grouping**: Group contributors by team
6. **Milestone Markers**: Show release dates on timeline
7. **Comparative Mode**: Compare multiple repositories

---

## Dependencies

### Required
```txt
matplotlib>=3.5.0
numpy>=1.21.0
```

### Optional
```txt
seaborn>=0.11.0    # Enhanced styling
pandas>=1.3.0      # Better data manipulation
```

---

## Estimated Timeline

| Task | Hours | Status |
|------|-------|--------|
| Core InteractiveVisualizer | 6-8 | Phase 1 |
| Update methods and callbacks | 4-5 | Phase 1 |
| Comparison Dashboard | 3-4 | Phase 2 |
| Heatmap visualization | 2-3 | Phase 2 |
| Export functionality | 2-3 | Phase 3 |
| Integration with main.py | 1-2 | Phase 3 |
| Testing and debugging | 3-4 | Phase 3 |
| Documentation | 2-3 | Phase 3 |
| **Total** | **23-32** | |

---

## Conclusion

This matplotlib enhancement provides a cost-effective solution for interactive metric visualization with minimal dependencies. It maintains compatibility with the existing command-line workflow while adding professional visualization capabilities suitable for technical users and data analysis.