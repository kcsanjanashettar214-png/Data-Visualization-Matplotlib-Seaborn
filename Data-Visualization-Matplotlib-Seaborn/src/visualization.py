"""Explore and visualize Seaborn's Tips dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


DAY_ORDER = ["Thur", "Fri", "Sat", "Sun"]
TIME_ORDER = ["Lunch", "Dinner"]
PALETTE = sns.color_palette("colorblind", n_colors=4)
TIME_PALETTE = {"Lunch": "#0072B2", "Dinner": "#D55E00"}
NUMERIC_COLUMNS = ["total_bill", "tip", "size"]
USD_TO_INR_RATE = 100.0
CURRENCY_AXIS_LABEL = "INR (₹)"


def load_and_clean_tips() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load, clean, and convert the Tips dataset's monetary values from USD to INR."""
    data = sns.load_dataset("tips").copy()
    initial_rows = len(data)
    missing_before = int(data.isna().sum().sum())
    duplicates_before = int(data.duplicated().sum())

    for column in data.select_dtypes(include=np.number).columns:
        if data[column].isna().any():
            median = data[column].median()
            if pd.isna(median):
                raise ValueError(f"Cannot impute '{column}': it has no non-missing values.")
            data[column] = data[column].fillna(median)

    for column in data.select_dtypes(include=["object", "category", "string"]).columns:
        if data[column].isna().any():
            modes = data[column].mode(dropna=True)
            if modes.empty:
                raise ValueError(f"Cannot impute '{column}': it has no non-missing values.")
            data[column] = data[column].fillna(modes.iloc[0])

    data = data.drop_duplicates().copy()
    data[["total_bill", "tip"]] = data[["total_bill", "tip"]] * USD_TO_INR_RATE
    report = {
        "initial_rows": initial_rows,
        "missing_values_before": missing_before,
        "missing_values_after": int(data.isna().sum().sum()),
        "duplicates_removed": duplicates_before,
        "final_rows": len(data),
        "currency_conversion": f"1 USD = INR {USD_TO_INR_RATE:.2f}",
    }
    return data, report


def summarize_data(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate the values used in the written interpretation of the charts."""
    daily_mean_tip = data.groupby("day", observed=False)["tip"].mean().reindex(DAY_ORDER).dropna()
    correlations = data[NUMERIC_COLUMNS].corr()
    correlation_pairs = correlations.where(
        np.triu(np.ones(correlations.shape), k=1).astype(bool)
    ).stack()
    strongest_pair = correlation_pairs.abs().idxmax()
    return {
        "rows": len(data),
        "columns": len(data.columns),
        "mean_total_bill": float(data["total_bill"].mean()),
        "median_total_bill": float(data["total_bill"].median()),
        "max_bill": float(data["total_bill"].max()),
        "highest_average_tip_day": str(daily_mean_tip.idxmax()),
        "highest_average_tip": float(daily_mean_tip.max()),
        "daily_mean_tip": daily_mean_tip,
        "bill_tip_correlation": float(data["total_bill"].corr(data["tip"])),
        "strongest_correlation_pair": strongest_pair,
        "strongest_correlation": float(correlation_pairs.loc[strongest_pair]),
        "correlations": correlations,
    }


def _finish_figure(fig: plt.Figure, takeaway: str, output_path: Path | None) -> None:
    fig.text(
        0.5,
        0.042,
        f"Currency conversion: 1 USD = INR {USD_TO_INR_RATE:.2f}",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#59635e",
    )
    fig.text(0.5, 0.015, takeaway, ha="center", va="bottom", fontsize=9, wrap=True)
    fig.tight_layout(rect=(0.04, 0.10, 0.98, 0.96))
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")


def plot_histogram(data: pd.DataFrame, output_path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(data=data, x="total_bill", bins=20, color=PALETTE[0], edgecolor="white", ax=ax)
    ax.set(title="Total Bill Distribution", xlabel=f"Total bill ({CURRENCY_AXIS_LABEL})", ylabel="Number of tables")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.grid(axis="y", alpha=0.22)
    _finish_figure(
        fig,
        "Takeaway: Most tables have lower bills, with fewer high-bill observations forming a right tail.",
        output_path,
    )
    return fig


def plot_average_tips(data: pd.DataFrame, output_path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(
        data=data,
        x="day",
        y="tip",
        order=DAY_ORDER,
        estimator="mean",
        errorbar=("ci", 95),
        color=PALETTE[1],
        ax=ax,
    )
    ax.set(title="Average Tip by Day", xlabel="Dining day", ylabel=f"Average tip ({CURRENCY_AXIS_LABEL})")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.grid(axis="y", alpha=0.22)
    _finish_figure(
        fig,
        "Takeaway: Sunday has the highest average tip in this sample; bars show 95% confidence intervals.",
        output_path,
    )
    return fig


def plot_tip_boxplot(data: pd.DataFrame, output_path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=data, x="day", y="tip", order=DAY_ORDER, palette=PALETTE, hue="day", legend=False, ax=ax)
    ax.set(title="Tip Distribution by Day", xlabel="Dining day", ylabel=f"Tip ({CURRENCY_AXIS_LABEL})")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.grid(axis="y", alpha=0.22)
    _finish_figure(
        fig,
        "Takeaway: The median and spread of tips vary by day, while individual points beyond the whiskers are potential outliers.",
        output_path,
    )
    return fig


def plot_bill_tip_scatter(data: pd.DataFrame, output_path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=data,
        x="total_bill",
        y="tip",
        hue="time",
        hue_order=TIME_ORDER,
        palette=TIME_PALETTE,
        alpha=0.82,
        s=55,
        ax=ax,
    )
    ax.set(
        title="Total Bill vs Tip",
        xlabel=f"Total bill ({CURRENCY_AXIS_LABEL})",
        ylabel=f"Tip ({CURRENCY_AXIS_LABEL})",
    )
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.legend(title="Meal")
    ax.grid(alpha=0.2)
    _finish_figure(
        fig,
        "Takeaway: Tips generally rise with total bills; colors distinguish Lunch from Dinner.",
        output_path,
    )
    return fig


def plot_correlation_heatmap(
    data: pd.DataFrame, output_path: Path | None = None
) -> plt.Figure:
    correlations = data[NUMERIC_COLUMNS].corr()
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        correlations,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Pearson correlation"},
        ax=ax,
    )
    ax.set(title="Relationships Between Numerical Variables", xlabel="Numerical variable", ylabel="Numerical variable")
    _finish_figure(
        fig,
        "Takeaway: Bill and tip have the strongest positive linear association among these numerical variables.",
        output_path,
    )
    return fig


def create_dashboard(data: pd.DataFrame, output_path: Path | None = None) -> plt.Figure:
    """Create the requested 2-by-2 dashboard and optionally save it at 150 DPI."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        f"Restaurant Tips | Rupee Overview (₹{USD_TO_INR_RATE:.0f} per USD)",
        fontsize=18,
        fontweight="bold",
        y=0.99,
    )

    sns.histplot(data=data, x="total_bill", bins=20, color=PALETTE[0], edgecolor="white", ax=axes[0, 0])
    axes[0, 0].set(title="Total Bill Distribution", xlabel=f"Total bill ({CURRENCY_AXIS_LABEL})", ylabel="Number of tables")
    axes[0, 0].xaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))

    sns.boxplot(
        data=data,
        x="day",
        y="tip",
        order=DAY_ORDER,
        palette=PALETTE,
        hue="day",
        legend=False,
        ax=axes[0, 1],
    )
    axes[0, 1].set(title="Tip Distribution by Day", xlabel="Dining day", ylabel=f"Tip ({CURRENCY_AXIS_LABEL})")
    axes[0, 1].yaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))

    sns.scatterplot(
        data=data,
        x="total_bill",
        y="tip",
        hue="time",
        hue_order=TIME_ORDER,
        palette=TIME_PALETTE,
        alpha=0.82,
        s=42,
        ax=axes[1, 0],
    )
    axes[1, 0].set(
        title="Total Bill vs Tip",
        xlabel=f"Total bill ({CURRENCY_AXIS_LABEL})",
        ylabel=f"Tip ({CURRENCY_AXIS_LABEL})",
    )
    axes[1, 0].xaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    axes[1, 0].yaxis.set_major_formatter(mticker.StrMethodFormatter("₹{x:,.0f}"))
    axes[1, 0].legend(title="Meal")

    sns.heatmap(
        data[NUMERIC_COLUMNS].corr(),
        annot=True,
        fmt=".2f",
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Pearson correlation"},
        ax=axes[1, 1],
    )
    axes[1, 1].set(title="Numerical Correlations", xlabel="Numerical variable", ylabel="Numerical variable")

    captions = [
        "Most bills are lower, with a right-skewed tail.",
        "Tip medians and spreads vary across dining days.",
        "Tips generally rise with bills; color marks meal.",
        "Bill and tip have the strongest positive correlation.",
    ]
    for ax, caption in zip(axes.flat, captions):
        ax.grid(axis="y", alpha=0.16)
        ax.text(
            0.5,
            -0.24,
            caption,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=9,
            wrap=True,
        )

    fig.text(
        0.5,
        0.018,
        f"All monetary amounts converted at 1 USD = INR {USD_TO_INR_RATE:.2f}. "
        "Correlation describes association, not causation.",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.03, 0.045, 0.98, 0.96), h_pad=3.0, w_pad=2.2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig


def generate_all_visualizations(
    data: pd.DataFrame, output_dir: Path
) -> dict[str, plt.Figure]:
    """Write all five standalone charts and the final dashboard."""
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "histogram": plot_histogram(data, output_dir / "histogram.png"),
        "bar_chart": plot_average_tips(data, output_dir / "bar_chart.png"),
        "box_plot": plot_tip_boxplot(data, output_dir / "box_plot.png"),
        "scatter_plot": plot_bill_tip_scatter(data, output_dir / "scatter_plot.png"),
        "correlation_heatmap": plot_correlation_heatmap(data, output_dir / "correlation_heatmap.png"),
        "dashboard": create_dashboard(data, output_dir / "tips_overview.png"),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "outputs"
    data, cleaning = load_and_clean_tips()
    summary = summarize_data(data)

    print("Cleaning report:", cleaning)
    print(f"\nMonetary values converted using 1 USD = INR {USD_TO_INR_RATE:.2f}.")
    print("\nFirst five rows:\n", data.head().to_string(index=False))
    print("\nDataset information:")
    data.info()
    print("\nStatistical summary:\n", data.describe().to_string())
    print("\nMissing values by column:\n", data.isna().sum().to_string())
    print("\nNumerical correlation matrix:\n", summary["correlations"].round(3).to_string())
    print(
        f"\nHighest average tip: {summary['highest_average_tip_day']} "
        f"(INR {summary['highest_average_tip']:,.2f})"
    )
    print(f"Bill-tip correlation: {summary['bill_tip_correlation']:.3f}")
    print(
        "Strongest numerical correlation: "
        f"{summary['strongest_correlation_pair'][0]} and "
        f"{summary['strongest_correlation_pair'][1]} "
        f"({summary['strongest_correlation']:.3f})"
    )

    figures = generate_all_visualizations(data, output_dir)
    for figure in figures.values():
        plt.close(figure)
    print(f"\nSaved six chart files in: {output_dir}")


if __name__ == "__main__":
    main()
