# Operations Efficiency Dashboard

A **free, local-first operations analytics report** that converts daily machine totals into defensible KPIs, CSV exports, charts and an offline HTML dashboard. It runs on Windows, macOS or Linux with Python. This is a portfolio demonstration, **not a record of actual employer operations**.

## What it does

- Generates reproducible **clearly labeled synthetic** daily records with `--seed` (default), or analyzes your **own authorized CSV** using `--input`.
- Validates dates, numeric values, machine identifiers, uniqueness and internal consistency before calculating anything.
- Computes machine and daily summaries using **weighted rates**, avoiding the mistake of averaging percentages with different denominators.
- Distinguishes **delay incidence** (% of operations delayed) from **delay duration** (minutes per operation). These are not interchangeable.
- Filters an inclusive date range and saves an offline `report.html`, three CSVs and two PNG charts.
- Uses local files only; it does not upload your data or require an account.

## Quick start

```bash
git clone https://github.com/ManOfCulture2003/operations-efficiency-dashboard.git
cd operations-efficiency-dashboard
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python operations_efficiency_dashboard.py --seed 42 --days 90
```

Open `reports/report.html` in your browser. The default sample begins on **2026-01-01** and uses fictional machines. Output is ignored by Git; do not commit private business data.

### Analyze your own CSV

```bash
python operations_efficiency_dashboard.py --input my_operations.csv --start 2026-02-01 --end 2026-02-28 --output-dir my_report
```

Required columns (one record per date and machine):

| Date | Machine | Operations | DelayedOperations | DelayMinutes |
|---|---|---:|---:|---:|
| 2026-02-01 | Machine_A | 100 | 8 | 35 |
| 2026-02-01 | Machine_B | 120 | 0 | 0 |

- `Date`: valid ISO `YYYY-MM-DD` calendar date; duplicate Date/Machine pairs are rejected.
- `Machine`: 1–40 ASCII letters, digits, `_` or `-`, starting with a letter or digit (also prevents spreadsheet formula injection in exports).
- `Operations`: positive whole number.
- `DelayedOperations`: whole number between 0 and `Operations`.
- `DelayMinutes`: nonnegative whole minutes; must be zero if `DelayedOperations` is zero.
- Limits: 100,000 records and 20 MiB per input CSV. Oversized files are rejected before parsing; no report is written. CSV contents are processed locally and not sent anywhere.

### KPI definitions

| KPI | Calculation | Interpretation |
|---|---|---|
| Delay incidence (%) | `100 × sum(DelayedOperations) / sum(Operations)` | Share of operations that experienced a delay |
| Delay minutes per operation | `sum(DelayMinutes) / sum(Operations)` | Average delay burden per operation, including non-delayed operations |
| Minutes per delayed operation | `sum(DelayMinutes) / sum(DelayedOperations)` | Delay duration among delayed operations; blank if none were delayed |

All summaries use **total numerators and denominators**, not the unweighted average of daily ratios. Delays are synthetic in demo mode; no causal inference, productivity improvements, or accuracy claims are made.

## Output files

`reports/report.html` (offline dashboard), `records.csv` (validated selected rows), `machine_kpis.csv`, `daily_kpis.csv`, `delay_incidence.png`, `delay_minutes_per_operation.png`. Legacy `operations_delay_rate.png` in the repository predates this update and should not be treated as the new report output.

## Test

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs tests and generates a smoke-test report on Ubuntu and Windows with Python 3.11 and 3.13. Manual testing with your own Windows environment and real authorized business CSVs is still recommended.

## Architecture and limitations

`generate_data → validate_data → filter_dates → summarize → save charts/CSV/HTML`. The report is static; rerun the CLI to refresh it. The synthetic generator models three fictional machines with fixed delay probabilities for illustration only; it is not a calibrated simulation of any actual facility. Input data quality and the meaning of 'delayed operation' must be established by whoever collects real records. Output HTML references PNGs in the same directory, so keep the report files together. No database or network service is required.

## Interview explanation

"I built a local analytics workflow that validates operations CSVs, computes weighted delay KPIs, and generates an offline dashboard. I separated the frequency of delays from their duration, tested invalid input and weighted aggregation, and automated cross-platform testing. The default dataset is explicitly synthetic."

## License

MIT. The original repository README stated an MIT license, but the repository has no `LICENSE` file yet; verify license ownership before distributing third-party contributions.
