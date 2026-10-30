# Operations Efficiency Dashboard

**Educational portfolio project — default data is synthetic, not real employer, airline, or machinery data.**

Aggregates validated daily machine logs into total operations, delay minutes, and delay minutes per 100 operations. Generates a CSV summary and bar chart.

## Setup (Python 3.11+)

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python operations_efficiency_dashboard.py
python -m unittest discover -v
```

The program writes generated artifacts under `outputs/` (ignored by Git). To analyze a local CSV instead, pass `--input your_file.csv`.

CSV fields: `Date,Machine,Operations,DelayMinutes`. Read the input validation code before substituting your data. No company or customer information should be uploaded without permission.

Required values cannot be missing, machine names cannot be blank, and dates must be valid. Operations must be positive and delay minutes nonnegative; both metrics must be finite numbers. Invalid rows cause an error before exports are written, instead of being silently omitted from totals.

## Technical approach

Aggregates validated daily machine logs into total operations, delay minutes, and delay minutes per 100 operations. Generates a CSV summary and bar chart.

The automated tests cover reproducibility and core validation/metrics. GitHub Actions runs the tests on pushes and pull requests.

## Limits

The generated figures and model scores demonstrate code behavior **only**. They are not real-world business improvements, production deployments, or evidence of predictive accuracy on actual organizations. More real-world validation, data quality checks, and monitoring are needed before deployment.

## Portfolio talking points

This project demonstrates Python data processing, an automated test suite, reproducible dependencies, and technical documentation. Be ready to walk through the source code yourself.
