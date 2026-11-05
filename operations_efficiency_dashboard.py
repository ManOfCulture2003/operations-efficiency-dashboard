"""Reproducible, local-first operations KPI reporting for synthetic or owned CSV data."""
from __future__ import annotations

import argparse
from datetime import date
from html import escape
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED = ("Date", "Machine", "Operations", "DelayedOperations", "DelayMinutes")
NUMERIC = ("Operations", "DelayedOperations", "DelayMinutes")
MACHINE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
MAX_ROWS = 100_000


def generate_data(*, seed: int = 0, days: int = 90) -> pd.DataFrame:
    """Generate labeled synthetic daily totals, never represented as observed data."""
    if not 1 <= days <= 3650:
        raise ValueError("days must be between 1 and 3650")
    rng = np.random.default_rng(seed)
    rows = []
    for day in pd.date_range("2026-01-01", periods=days, freq="D"):
        for machine, chance in (("Machine_A", 0.04), ("Machine_B", 0.11), ("Machine_C", 0.07)):
            operations = int(rng.integers(80, 121))
            delayed = int(rng.binomial(operations, chance))
            delay_minutes = int(rng.integers(1, 11, size=delayed).sum())
            rows.append((day.strftime("%Y-%m-%d"), machine, operations, delayed, delay_minutes))
    return pd.DataFrame(rows, columns=REQUIRED)


def validate_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate schema, data integrity and spreadsheet-safe machine identifiers."""
    missing = [name for name in REQUIRED if name not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("Input contains no records")
    if len(frame) > MAX_ROWS:
        raise ValueError(f"Input exceeds {MAX_ROWS:,} records")
    result = frame.loc[:, list(REQUIRED)].copy()
    machines = result["Machine"]
    if machines.isna().any() or not machines.map(lambda value: isinstance(value, str) and bool(MACHINE_PATTERN.fullmatch(value))).all():
        raise ValueError("Machine must contain 1-40 letters, digits, underscores or hyphens and start with a letter or digit")
    try:
        # Explicit ISO format avoids ambiguous month/day interpretation.
        if result["Date"].isna().any() or not result["Date"].map(lambda x: isinstance(x, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", x))).all():
            raise ValueError("Dates must use YYYY-MM-DD")
        result["Date"] = pd.to_datetime(result["Date"], format="%Y-%m-%d", errors="raise")
    except (TypeError, ValueError) as exc:
        raise ValueError("Dates must be valid YYYY-MM-DD calendar dates") from exc
    for name in NUMERIC:
        if result[name].map(lambda value: isinstance(value, (bool, np.bool_))).any():
            raise ValueError(f"{name} must contain whole-number counts, not booleans")
        try:
            values = pd.to_numeric(result[name], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must contain nonnegative whole numbers") from exc
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all() or (values < 0).any() or (values % 1 != 0).any():
            raise ValueError(f"{name} must contain nonnegative whole numbers")
        if (values > 100_000_000).any():
            raise ValueError(f"{name} contains an implausibly large value")
        result[name] = values.astype("int64")
    if (result["Operations"] == 0).any():
        raise ValueError("Operations must be greater than zero for each record")
    if (result["DelayedOperations"] > result["Operations"]).any():
        raise ValueError("DelayedOperations cannot exceed Operations")
    if ((result["DelayedOperations"] == 0) & (result["DelayMinutes"] != 0)).any():
        raise ValueError("DelayMinutes must be zero when DelayedOperations is zero")
    if result.duplicated(subset=["Date", "Machine"]).any():
        raise ValueError("Duplicate Date/Machine records are not allowed")
    return result.sort_values(["Date", "Machine"]).reset_index(drop=True)


def filter_dates(frame: pd.DataFrame, *, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    def parse(value: str | None) -> pd.Timestamp | None:
        if value is None:
            return None
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Date filters must use YYYY-MM-DD")
        try:
            return pd.to_datetime(value, format="%Y-%m-%d", errors="raise")
        except ValueError as exc:
            raise ValueError("Date filters must be valid calendar dates") from exc
    lower, upper = parse(start), parse(end)
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("start date cannot be later than end date")
    selected = frame
    if lower is not None:
        selected = selected.loc[selected["Date"] >= lower]
    if upper is not None:
        selected = selected.loc[selected["Date"] <= upper]
    if selected.empty:
        raise ValueError("No records match the requested date range")
    return selected.copy()


def summarize(frame: pd.DataFrame, group_by: str = "Machine") -> pd.DataFrame:
    """Weighted KPIs: rates must use summed numerators and denominators."""
    if group_by not in ("Machine", "Date"):
        raise ValueError("group_by must be Machine or Date")
    summary = frame.groupby(group_by, as_index=False, sort=True)[list(NUMERIC)].sum()
    summary["DelayIncidencePct"] = (100 * summary["DelayedOperations"] / summary["Operations"]).round(2)
    summary["DelayMinutesPerOperation"] = (summary["DelayMinutes"] / summary["Operations"]).round(3)
    summary["MinutesPerDelayedOperation"] = (
        summary["DelayMinutes"] / summary["DelayedOperations"].replace(0, np.nan)
    ).round(2)
    return summary


def save_chart(summary: pd.DataFrame, path: Path, metric: str, label: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(summary["Machine"], summary[metric])
    ax.set_ylabel(label)
    ax.set_xlabel("Machine")
    ax.set_title(label + " by machine")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def make_html(summary: pd.DataFrame, *, synthetic: bool, start: str, end: str) -> str:
    rows = "\n".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>"
        for row in summary[["Machine", "Operations", "DelayedOperations", "DelayMinutes", "DelayIncidencePct", "DelayMinutesPerOperation"]].itertuples(index=False, name=None)
    )
    source = "SYNTHETIC DEMONSTRATION DATA — NOT REAL BUSINESS PERFORMANCE" if synthetic else "USER-SUPPLIED LOCAL DATA — VERIFY BEFORE SHARING"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operations Efficiency Report</title><style>
body{{font:16px system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#172334;background:#f8fafc}}header{{background:#172334;color:white;padding:1.5rem;border-radius:12px}}.note{{font-weight:700;color:#8b3d0a;background:#fff3db;padding:1rem;border-radius:8px;margin:1rem 0}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:.7rem;text-align:left;border-bottom:1px solid #dbe2e8}}th{{background:#e8eef5}}.scroll{{overflow-x:auto}}img{{max-width:100%;height:auto;background:white;border-radius:8px;margin:1rem 0}}footer{{margin:2rem 0;color:#475569}}@media print{{body{{background:white}}}}
</style></head><body><header><h1>Operations Efficiency Report</h1><p>{escape(start)} through {escape(end)} · Inclusive</p></header><p class="note">{escape(source)}</p><h2>Machine KPIs</h2><div class="scroll"><table><thead><tr><th>Machine</th><th>Operations</th><th>Delayed operations</th><th>Delay minutes</th><th>Delayed (%)</th><th>Minutes / operation</th></tr></thead><tbody>{rows}</tbody></table></div><h2>Delay incidence</h2><img src="delay_incidence.png" alt="Bar chart of percent of operations delayed by machine"><h2>Delay duration</h2><img src="delay_minutes_per_operation.png" alt="Bar chart of delay minutes per operation by machine"><footer>Delayed (%) = 100 × delayed operations / total operations. Minutes / operation = total delay minutes / total operations. These are different KPIs; neither is a causal explanation.</footer></body></html>"""


def build_report(*, input_path: Path | None, output_dir: Path, seed: int = 0, days: int = 90, start: str | None = None, end: str | None = None) -> dict[str, Path]:
    synthetic = input_path is None
    if synthetic:
        raw = generate_data(seed=seed, days=days)
    else:
        # Limit memory exposure from unexpectedly large CSVs.
        raw = pd.read_csv(input_path, nrows=MAX_ROWS + 1, dtype={"Date": str, "Machine": str})
    frame = filter_dates(validate_data(raw), start=start, end=end)
    by_machine = summarize(frame)
    by_day = summarize(frame, group_by="Date")
    paths = {name: output_dir / name for name in (
        "records.csv", "machine_kpis.csv", "daily_kpis.csv", "delay_incidence.png",
        "delay_minutes_per_operation.png", "report.html")}
    if input_path is not None:
        source = input_path.resolve()
        if any(path.resolve() == source or (path.exists() and path.samefile(input_path))
               for path in paths.values()):
            raise ValueError("Report would overwrite the input file; choose a different output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.assign(Date=frame["Date"].dt.strftime("%Y-%m-%d")).to_csv(paths["records.csv"], index=False)
    by_machine.to_csv(paths["machine_kpis.csv"], index=False)
    by_day.assign(Date=by_day["Date"].dt.strftime("%Y-%m-%d")).to_csv(paths["daily_kpis.csv"], index=False)
    save_chart(by_machine, paths["delay_incidence.png"], "DelayIncidencePct", "Delayed operations (%)")
    save_chart(by_machine, paths["delay_minutes_per_operation.png"], "DelayMinutesPerOperation", "Delay minutes per operation")
    paths["report.html"].write_text(make_html(by_machine, synthetic=synthetic, start=frame["Date"].min().strftime("%Y-%m-%d"), end=frame["Date"].max().strftime("%Y-%m-%d")), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an offline operations KPI report from synthetic or owned data")
    parser.add_argument("--input", type=Path, help="Optional CSV input; omit for explicitly synthetic demo data")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--start", help="Inclusive YYYY-MM-DD date filter")
    parser.add_argument("--end", help="Inclusive YYYY-MM-DD date filter")
    args = parser.parse_args()
    try:
        files = build_report(input_path=args.input, output_dir=args.output_dir, seed=args.seed, days=args.days, start=args.start, end=args.end)
    except (ValueError, OSError, pd.errors.ParserError) as exc:
        parser.error(str(exc))
    print("Created local report:", files["report.html"])
    print("CSV files and charts:", files["report.html"].parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
