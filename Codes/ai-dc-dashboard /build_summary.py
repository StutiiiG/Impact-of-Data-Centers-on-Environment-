from pathlib import Path
import pandas as pd

# Directory where this script lives, e.g. .../US-AI-Server-Analysis/Codes/ai-dc-dashboard
SCRIPT_DIR = Path(__file__).resolve().parent

# Repo root: go two levels up from ai-dc-dashboard → Codes → repo root
REPO_ROOT = SCRIPT_DIR.parents[1]

# Scenario outputs are in the repo-level Outputs/ folder
OUTPUTS_DIR = REPO_ROOT / "Outputs"

# Dashboard-specific data folder (next to this script)
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

print("DEBUG:")
print("  SCRIPT_DIR:", SCRIPT_DIR)
print("  REPO_ROOT:", REPO_ROOT)
print("  OUTPUTS_DIR:", OUTPUTS_DIR)

scenario_files = {
    "Best carbon":  "best_carbon_totals.csv",
    "Best water":   "best_water_totals.csv",
    "Worst carbon": "worst_carbon_totals.csv",
    "Worst water":  "worst_water_totals.csv",
}

frames = []

for scenario, fname in scenario_files.items():
    path = OUTPUTS_DIR / fname
    if not path.exists():
        print(f"WARNING: {path} not found, skipping this scenario")
        continue

    df = pd.read_csv(path)

    # Keep only 2025–2030 (your project horizon)
    df = df[(df["year"] >= 2025) & (df["year"] <= 2030)].copy()

    df["scenario"] = scenario
    frames.append(df)

if not frames:
    raise RuntimeError("No scenario CSVs found. Check filenames in Outputs/.")

summary = pd.concat(frames, ignore_index=True)
summary = summary.sort_values(["year", "scenario"])

out_path = DATA_DIR / "dc_impact_summary.csv"
summary.to_csv(out_path, index=False)

print(f"Saved combined summary to {out_path}")
print(summary)
