"""Visualization generator for AQPQC Selector empirical benchmarks."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from aqpqc.evaluator import evaluate_strategies
from aqpqc.selector import AQPQCSelector

def plot_benchmark_comparison(summary: dict, output_path: Path):
    """Render grouped bar chart comparing performance across the 3 strategies."""
    strategies = ["static_max", "static_min", "aqpqc"]
    labels = ["Static-Max (Level 5)", "Static-Min (Level 1)", "AQPQC Selector (Ours)"]

    sec_sat = [summary[s]["security_satisfaction_pct"] for s in strategies]
    frag_rate = [summary[s]["severe_fragmentation_pct"] for s in strategies]
    avg_pkts = [summary[s]["mean_packets"] for s in strategies]

    x = np.arange(len(strategies))
    width = 0.25

    # Aesthetic styling: clean neutral slate + restrained accent
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.edgecolor": "#71717a",
        "axes.linewidth": 0.8,
        "grid.color": "#e4e4e7",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
    })

    fig, ax1 = plt.subplots(figsize=(9, 5.5), dpi=300)

    # Bars on left axis (Percentages)
    rects1 = ax1.bar(x - width/2, sec_sat, width, label="Security Satisfaction (%)", color="#2563eb", alpha=0.9)
    rects2 = ax1.bar(x + width/2, frag_rate, width, label="Severe Packet Frag (%)", color="#dc2626", alpha=0.85)

    ax1.set_ylabel("Percentage (%)", fontsize=11, fontweight="semibold", color="#18181b")
    ax1.set_ylim(0, 115)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10, fontweight="semibold", color="#18181b")
    ax1.grid(axis="y")

    # Direct value labels on bars
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    ax1.legend(loc="upper right", frameon=True, facecolor="#ffffff", edgecolor="#e4e4e7")
    ax1.set_title("AQPQC Selector vs Static Baselines Across 1,000 Heterogeneous Scenarios",
                  fontsize=12, fontweight="bold", pad=15, color="#09090b")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Generated comparison figure: {output_path}")


def plot_feature_importance(selector: AQPQCSelector, output_path: Path):
    """Render horizontal bar chart of XGBoost decision feature weights."""
    if not selector.feature_importances_:
        return

    features = sorted(selector.feature_importances_.items(), key=lambda x: x[1])
    names = [f[0].replace("_", " ").title() for f in features]
    scores = [f[1] * 100.0 for f in features]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, scores, color="#0f766e", alpha=0.9, height=0.6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, color="#18181b")
    ax.set_xlabel("Relative Decision Weight / Importance (%)", fontsize=10, fontweight="semibold", color="#18181b")
    ax.set_title("AQPQC Selector: Decision Feature Importance (XGBoost)", fontsize=12, fontweight="bold", pad=12, color="#09090b")
    ax.grid(axis="x")

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.1f}%", xy=(w, bar.get_y() + bar.get_height()/2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=9)

    ax.set_xlim(0, max(scores) * 1.15)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Generated feature importance figure: {output_path}")


def main():
    root_dir = Path(__file__).resolve().parent.parent
    figures_dir = root_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("Running evaluation for figures...")
    summary = evaluate_strategies(n_contexts=500, random_state=42)
    plot_benchmark_comparison(summary, figures_dir / "static_vs_aqpqc_comparison.png")

    selector = AQPQCSelector()
    selector.train(n_samples=500, random_state=42)
    plot_feature_importance(selector, figures_dir / "feature_importance.png")


if __name__ == "__main__":
    main()
