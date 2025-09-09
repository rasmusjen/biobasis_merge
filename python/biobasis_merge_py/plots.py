"""Plot generation using Plotly for interactive HTML visualizations."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def determine_plot_columns(df: pd.DataFrame, exclude_columns: Optional[List[str]] = None) -> List[str]:
    """Determine which columns to plot, excluding specified columns."""
    if exclude_columns is None:
        exclude_columns = ['TIMESTAMP', 'RECORD', 'timestamp', 'record']
    
    plot_columns = []
    for col in df.columns:
        if col not in exclude_columns:
            # Check if column is numeric or can be converted to numeric
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                plot_columns.append(col)
            elif df[col].dtype == 'object':
                # Try to convert object columns to numeric to see if they contain numbers
                try:
                    numeric_values = pd.to_numeric(df[col], errors='coerce')
                    # Include if at least 10% of values are numeric
                    if numeric_values.notna().sum() / len(df) >= 0.1:
                        plot_columns.append(col)
                except:
                    continue
    
    logger.debug(f"Selected {len(plot_columns)} columns for plotting: {plot_columns}")
    return plot_columns


def calculate_subplot_layout(num_plots: int, max_cols: int = 2) -> tuple:
    """Calculate optimal subplot layout."""
    if num_plots == 0:
        return 1, 1
    
    cols = min(num_plots, max_cols)
    rows = math.ceil(num_plots / cols)
    
    return rows, cols


def downsample_data(df: pd.DataFrame, max_points: int = 200000) -> pd.DataFrame:
    """Downsample data if it has too many points."""
    if len(df) <= max_points:
        return df
    
    # Calculate stride for downsampling
    stride = math.ceil(len(df) / max_points)
    downsampled = df.iloc[::stride].copy()
    
    logger.info(f"Downsampled data from {len(df)} to {len(downsampled)} points (stride={stride})")
    return downsampled


def create_time_series_plots(df: pd.DataFrame, timestamp_col: str, output_path: str) -> None:
    """
    Create interactive Plotly time series plots and save to HTML.
    
    Features:
    - Excludes TIMESTAMP and RECORD columns
    - Combines BGTemp_C_Avg and AirTC_Avg in same subplot with different colors
    - Auto grid layout with max 2 columns  
    - Downsamples if > 200k rows
    - Saves as interactive HTML
    """
    try:
        # Determine columns to plot
        all_plot_columns = determine_plot_columns(df)
        
        if not all_plot_columns:
            logger.warning("No numeric columns found for plotting")
            # Create empty plot
            fig = go.Figure()
            fig.add_annotation(
                text="No numeric data columns available for plotting",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title="Biobasis Meteorological Data - No Data")
            fig.write_html(output_path)
            return
        
        # Downsample if necessary
        plot_df = downsample_data(df)
        
        # Special handling for temperature plots
        temp_columns = ['BGTemp_C_Avg', 'AirTC_Avg']
        has_temp_data = any(col in all_plot_columns for col in temp_columns)
        
        # Create plot structure
        plot_columns = []
        subplot_titles = []
        
        if has_temp_data:
            # Add combined temperature plot
            plot_columns.append('Temperature')
            subplot_titles.append('Temperature (°C)')
            
            # Add other columns (excluding temperature columns)
            other_columns = [col for col in all_plot_columns if col not in temp_columns]
            plot_columns.extend(other_columns)
            subplot_titles.extend(other_columns)
        else:
            plot_columns = all_plot_columns
            subplot_titles = all_plot_columns
        
        # Calculate subplot layout
        rows, cols = calculate_subplot_layout(len(plot_columns))
        
        # Create subplots
        fig = make_subplots(
            rows=rows, 
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Add traces for each column/group
        for i, column in enumerate(plot_columns):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            if column == 'Temperature' and has_temp_data:
                # Special handling for combined temperature plot
                colors = ['red', 'blue']
                for j, temp_col in enumerate(temp_columns):
                    if temp_col in plot_df.columns and not plot_df[temp_col].isnull().all():
                        # Convert to numeric if needed for plotting
                        y_data = plot_df[temp_col]
                        if y_data.dtype == 'object':
                            y_data = pd.to_numeric(y_data, errors='coerce')
                        
                        fig.add_trace(
                            go.Scatter(
                                x=plot_df[timestamp_col],
                                y=y_data,
                                mode='lines',
                                name=temp_col,
                                showlegend=True,
                                line=dict(width=1, color=colors[j])
                            ),
                            row=row, col=col
                        )
            else:
                # Regular single column plot
                if column in plot_df.columns:
                    # Convert to numeric if needed for plotting
                    y_data = plot_df[column]
                    if y_data.dtype == 'object':
                        y_data = pd.to_numeric(y_data, errors='coerce')
                    
                    # Skip columns with all NaN values
                    if y_data.isnull().all():
                        logger.debug(f"Skipping column {column} - all NaN values")
                        continue
                    
                    fig.add_trace(
                        go.Scatter(
                            x=plot_df[timestamp_col],
                            y=y_data,
                            mode='lines',
                            name=column,
                            showlegend=False,
                            line=dict(width=1)
                        ),
                        row=row, col=col
                    )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Biobasis Meteorological Data Time Series",
                x=0.5,
                font=dict(size=16)
            ),
            height=300 * rows,
            showlegend=has_temp_data  # Only show legend for temperature plot
        )
        
        # Update x-axis labels
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(title_text="Time (UTC)", row=i, col=j)
        
        # Save to HTML
        fig.write_html(
            output_path,
            include_plotlyjs='cdn',
            config={'displayModeBar': True, 'displaylogo': False}
        )
        
        effective_plots = len(all_plot_columns) if not has_temp_data else len(all_plot_columns) - 1
        logger.info(f"Created interactive plots with {effective_plots} variables, saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to create plots: {e}")
        raise


def create_summary_plot(merge_summary: dict, output_path: str) -> None:
    """Create a summary plot showing data coverage and missing timestamps."""
    try:
        # Create a simple bar chart showing data coverage
        fig = go.Figure()
        
        coverage = merge_summary.get('data_coverage', 0)
        missing_pct = 100 - coverage
        
        fig.add_trace(go.Bar(
            x=['Data Coverage', 'Missing Data'],
            y=[coverage, missing_pct],
            marker_color=['green', 'red'],
            text=[f'{coverage:.1f}%', f'{missing_pct:.1f}%'],
            textposition='auto'
        ))
        
        fig.update_layout(
            title=f"Data Coverage Summary<br>{merge_summary.get('date_range', '')}",
            yaxis_title="Percentage",
            showlegend=False
        )
        
        # Add text annotations with summary stats
        fig.add_annotation(
            text=f"Total rows: {merge_summary.get('total_rows', 0)}<br>"
                 f"Expected rows: {merge_summary.get('expected_rows', 0)}<br>"
                 f"Missing timestamps: {merge_summary.get('missing_timestamps', 0)}",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            align="left",
            bgcolor="lightgray",
            bordercolor="black",
            borderwidth=1
        )
        
        # Save summary plot separately
        summary_path = output_path.replace('.html', '_summary.html')
        fig.write_html(summary_path)
        
        logger.info(f"Created summary plot: {summary_path}")
        
    except Exception as e:
        logger.warning(f"Failed to create summary plot: {e}")


def validate_plot_output(output_path: str) -> bool:
    """Validate that plot file was created successfully."""
    plot_file = Path(output_path)
    
    if not plot_file.exists():
        return False
    
    # Check file size (should be > 0)
    if plot_file.stat().st_size == 0:
        return False
    
    # Basic content check (should contain plotly)
    try:
        with open(plot_file, 'r') as f:
            content = f.read(1000)  # Read first 1000 chars
            if 'plotly' not in content.lower():
                return False
    except Exception:
        return False
    
    return True
