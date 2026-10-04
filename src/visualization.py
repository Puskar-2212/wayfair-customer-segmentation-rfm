"""
Data Visualization Module
Generates production-grade charts for customer segmentation, revenue share,
RFM heatmaps, and cohort analysis. Designed for both headless CLI and notebook rendering.
"""

from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from src.config import OUTPUTS_DIR


# Consistent styling theme
STYLE_THEME = "whitegrid"
PALETTE_NAME = "viridis"


def set_plotting_style():
    """Sets standard visualization styling."""
    sns.set_theme(style=STYLE_THEME)
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 16
    })


def plot_segment_distribution(summary_df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots horizontal bar chart of customer count per segment."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    
    sorted_df = summary_df.sort_values(by='num_customers', ascending=True)
    sns.barplot(
        x='num_customers',
        y='segment',
        data=sorted_df,
        hue='segment',
        palette=PALETTE_NAME,
        legend=False,
        ax=ax
    )
    
    ax.set_title("Customer Count by Segment", fontweight='bold', pad=15)
    ax.set_xlabel("Number of Customers")
    ax.set_ylabel("")

    # Annotate bar totals
    for p in ax.patches:
        width = p.get_width()
        ax.annotate(
            f"{int(width):,}",
            (width, p.get_y() + p.get_height() / 2.),
            ha='left',
            va='center',
            xytext=(6, 0),
            textcoords='offset points',
            fontweight='semibold'
        )

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def plot_revenue_share(summary_df: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots a donut chart displaying total revenue contribution by segment."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(9, 8), dpi=150)

    colors = sns.color_palette(PALETTE_NAME, len(summary_df))
    wedges, texts, autotexts = ax.pie(
        summary_df['total_revenue'],
        labels=summary_df['segment'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        pctdistance=0.75,
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)
    )

    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')

    ax.set_title("Revenue Share by Segment", fontweight='bold', pad=20)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def plot_rfm_heatmap(segmented_rfm: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots heatmap showing average customer monetary value across R and F scores."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

    heatmap_data = segmented_rfm.pivot_table(
        index='f_score',
        columns='r_score',
        values='monetary',
        aggfunc='mean'
    ).sort_index(ascending=False)

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=",.0f",
        cmap="YlGnBu",
        cbar_kws={'label': 'Average Monetary Spend ($)'},
        ax=ax
    )

    ax.set_title("Average Spend by Recency & Frequency Score", fontweight='bold', pad=15)
    ax.set_xlabel("Recency Score (5 = Most Recent)", labelpad=10)
    ax.set_ylabel("Frequency Score (5 = Most Frequent)", labelpad=10)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def plot_recency_vs_frequency(segmented_rfm: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots scatter plot of Recency vs Frequency colored by segment."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(11, 6), dpi=150)

    sns.scatterplot(
        x='recency',
        y='frequency',
        hue='segment',
        data=segmented_rfm,
        alpha=0.75,
        palette='tab10',
        ax=ax,
        s=40
    )

    ax.set_title("Recency vs. Frequency by Customer Segment", fontweight='bold', pad=15)
    ax.set_xlabel("Recency (Days since last qualifying order)")
    ax.set_ylabel("Frequency (Total qualifying orders)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def plot_segment_by_channel(pct_channel_ct: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots stacked bar chart showing segment composition across acquisition channels."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    pct_channel_ct.plot(
        kind='bar',
        stacked=True,
        colormap='Set2',
        ax=ax
    )

    ax.set_title("Segment Composition by Acquisition Channel (%)", fontweight='bold', pad=15)
    ax.set_xlabel("Segment")
    ax.set_ylabel("Percentage (%)")
    ax.legend(title='Channel', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.xticks(rotation=40, ha='right')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def plot_segment_by_cohort(pct_cohort_ct: pd.DataFrame, save_path: Optional[Path] = None) -> plt.Figure:
    """Plots stacked bar chart showing segment distribution across signup cohort years."""
    set_plotting_style()
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    pct_cohort_ct.plot(
        kind='bar',
        stacked=True,
        colormap='Paired',
        ax=ax
    )

    ax.set_title("Segment Composition by Signup Year (%)", fontweight='bold', pad=15)
    ax.set_xlabel("Segment")
    ax.set_ylabel("Percentage (%)")
    ax.legend(title='Signup Year', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.xticks(rotation=40, ha='right')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    return fig


def generate_all_visualizations(
    segmented_rfm: pd.DataFrame,
    summary_df: pd.DataFrame,
    customers: pd.DataFrame,
    output_dir: Path = OUTPUTS_DIR
):
    """Generates and persists all six publication figures to the outputs folder."""
    from src.analysis import analyze_channel_attribution, analyze_signup_cohorts
    
    # 1. Distribution
    plot_segment_distribution(summary_df, save_path=output_dir / "segment_distribution.png")
    plt.close()

    # 2. Revenue Share
    plot_revenue_share(summary_df, save_path=output_dir / "revenue_share.png")
    plt.close()

    # 3. RFM Heatmap
    plot_rfm_heatmap(segmented_rfm, save_path=output_dir / "rfm_heatmap.png")
    plt.close()

    # 4. Scatter Plot
    plot_recency_vs_frequency(segmented_rfm, save_path=output_dir / "recency_frequency_scatter.png")
    plt.close()

    # 5. Channel attribution
    _, pct_channel, _, _ = analyze_channel_attribution(segmented_rfm, customers)
    plot_segment_by_channel(pct_channel, save_path=output_dir / "segment_by_channel.png")
    plt.close()

    # 6. Signup cohorts
    _, pct_cohort = analyze_signup_cohorts(segmented_rfm, customers)
    plot_segment_by_cohort(pct_cohort, save_path=output_dir / "segment_by_signup_year.png")
    plt.close()
