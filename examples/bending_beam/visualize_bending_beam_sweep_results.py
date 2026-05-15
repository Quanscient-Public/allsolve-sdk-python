"""
Demonstrates SimulationOutputData pandas DataFrame export on the "Bending beam sweep" project.

Loads the project by name "Bending beam sweep".
Uses the first simulation from the project.

- Prints info about the DataFrame for sweep step 0 and the entire DataFrame.
- Saves two plots to "output" directory:
    - "plot1.png": "z_deflection" vs "Array index" for sweep step 0.
    - "plot2.png": beam-tip "z_deflection" for every sweep step, grouped by height and material.

Prerequisites:

- Run "bending_beam_sweep.py" first,
  or have project "Bending beam sweep" with a finished static simulation in the Allsolve.

Usage::

    python visualize_bending_beam_sweep_results.py
"""

from __future__ import annotations

from pathlib import Path

import allsolve
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_NAME = "Bending beam sweep"
OUTPUT_DIR_NAME = "output"


def main() -> None:
    client = allsolve.Client()

    # Try to get the project that was created by bending_beam_sweep.py
    project = client.get_current_project()

    if project is None or project.name != PROJECT_NAME:
        # Try searching for the project by name
        project = allsolve.Project.get_by_name(name=PROJECT_NAME)
    if project is None or project.name != PROJECT_NAME:
        raise ValueError(
            f"Project not found: {PROJECT_NAME!r}. Run bending_beam_sweep.py first."
        )

    print(f"Project: {project.name} (id: {project.id})")

    simulations = project.get_simulations()
    if not simulations:
        raise ValueError("No simulations on this project.")
    sim = simulations[0]
    print(f"Simulation: {sim.name} (id: {sim.id})")

    output_data = sim.get_output_data()
    n_sweeps = output_data.get_sweep_count()
    headers = output_data.get_value_headers()

    df = output_data.to_dataframe()
    s0 = output_data.sweep_step_to_dataframe(0)
    print_dataframe_info(df, s0, n_sweeps=n_sweeps, headers=headers)

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "plot1.png"
    tip_plot_path = output_dir / "plot2.png"

    plot_sweep_zero_deflection(s0, plot_path)
    plot_tip_deflection_across_sweeps(df, tip_plot_path)

    output_data.clean_cache()
    client.set_current_project(None)  # Clear the project from the cache
    print("\nOutput cache cleaned.")


def print_dataframe_info(
    df: pd.DataFrame,
    s0: pd.DataFrame,
    *,
    n_sweeps: int,
    headers: list[str],
) -> None:
    print(f"Sweep steps: {n_sweeps}, value outputs: {headers}")

    print("\n--- to_dataframe() ---")
    print(f"shape: {df.shape}")
    print(f"columns: {list(df.columns)}")
    print(df.head(5).to_string())
    print("…")
    print(f"\nRows per sweep: ~{len(df) // max(n_sweeps, 1)}")

    print("\n--- sweep_step_to_dataframe(0) ---")
    print(f"shape: {s0.shape}")
    print(s0.to_string())
    print("…")


def plot_sweep_zero_deflection(s0: pd.DataFrame, plot_path: Path) -> None:
    """``z_deflection`` vs ``Array index`` for the first sweep."""

    if plot_path.exists():
        print(f"Output file already exists: {plot_path}")
        return

    if not {"Array index", "z_deflection"}.issubset(s0.columns):
        print("Expected Array index / z_deflection columns missing; skip plot.")
        return

    sub = s0.sort_values("Array index")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        sub["Array index"],
        sub["z_deflection"],
        marker="o",
        linewidth=2,
        markersize=6,
    )
    ax.set_xlabel("Array index (along beam top)")
    ax.set_ylabel("z deflection (m)")
    ax.grid(True, alpha=0.3)
    title_bits = []
    for col in ("force", "height", "material_index"):
        if col in sub.columns and len(sub):
            title_bits.append(f"{col}={sub[col].iloc[0]}")
    fig.suptitle(
        "Bending beam demo — Sweep 0: " + (", ".join(title_bits) if title_bits else "")
    )
    fig.tight_layout()

    fig.savefig(plot_path, dpi=200)
    plt.close(fig)
    print(f"\nSaved plot: {plot_path}")


def plot_tip_deflection_across_sweeps(df: pd.DataFrame, tip_plot_path: Path) -> None:
    """Beam-tip ``z_deflection`` for every sweep step, grouped by height and material."""

    if tip_plot_path.exists():
        print(f"Output file already exists: {tip_plot_path}")
        return

    override_cols = [
        c for c in ("force", "height", "material_index") if c in df.columns
    ]
    if not {"Array index", "z_deflection"}.issubset(df.columns) or not override_cols:
        print("Expected columns missing for tip deflection plot; skipping.")
        return

    idx = df.groupby(override_cols)["Array index"].idxmax()
    tip_data = df.loc[idx].copy()
    for col in ("force", "height", "z_deflection"):
        if col in tip_data.columns:
            tip_data[col] = pd.to_numeric(tip_data[col], errors="coerce")

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    group_cols = [c for c in ("height", "material_index") if c in tip_data.columns]

    if "force" in tip_data.columns and group_cols:
        mat_labels = {"0": "Aluminium", "1": "Copper"}
        for key, grp in tip_data.groupby(group_cols):
            if not isinstance(key, tuple):
                key = (key,)
            parts = []
            for gc, val in zip(group_cols, key):
                if gc == "material_index":
                    parts.append(mat_labels.get(str(val), f"material_index={val}"))
                else:
                    parts.append(f"{gc}={val}")
            grp = grp.sort_values("force")
            ax2.plot(
                grp["force"],
                grp["z_deflection"],
                marker="o",
                linewidth=2,
                markersize=6,
                label=", ".join(parts),
            )
        ax2.set_xlabel("Force (N)")
        ax2.legend()
    else:
        ax2.bar(
            range(len(tip_data)),
            tip_data["z_deflection"].to_numpy(dtype=float),
        )
        ax2.set_xlabel("Sweep step")

    ax2.set_ylabel("z deflection at beam tip (m)")
    ax2.grid(True, alpha=0.3)
    fig2.suptitle("Bending beam — Tip deflection across sweep steps")
    fig2.tight_layout()
    fig2.savefig(tip_plot_path, dpi=200)
    plt.close(fig2)
    print(f"\nSaved tip deflection plot: {tip_plot_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        raise
