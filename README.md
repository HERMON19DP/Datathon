# CivicPulse — Where Should We Fix First?

CivicPulse is a Datathon MVP that helps civic operations teams explore simulated incident and public-complaint data, rank locations for review, inspect the evidence behind each score, compare candidate interventions, and experiment with complaint resolution-time prediction.

> **Data notice:** This project uses simulated data, including coordinates and timestamps. It is a prototype, not a validated system for real-world public-safety or municipal decisions.

## Current features

- **Priority map:** Explore location-level priority scores and filter by zone, incident type, and minimum score.
- **Ranked locations:** Sort locations by the baseline priority score.
- **Inspect the evidence:** Review score components, incident and complaint summaries, location context, and historical trends.
- **Compare interventions:** Compare predefined response options using illustrative effort units, urgency, and budget-fit checks.
- **Complaint resolution-time prediction:** A Random Forest regression experiment estimates `days_to_resolution` from complaint and location features.
- **Model evaluation:** Compare regression MAE with a median baseline and inspect historical resolution-time patterns.

## Technology

- Python
- Streamlit
- Pandas and NumPy
- Plotly
- scikit-learn

The current working application is Streamlit. A React + Vite UI migration may be developed separately; it is not required to run this app.

## Project structure

```text
Where_Should_We_Fix_First_MVP/
├── app.py
├── incidents.csv
├── locations.csv
├── public_complaints.csv
├── requirements.txt
├── README.md
└── .gitignore
```

Your local `.venv/` directory may also exist. It should not be committed.

## Prerequisites

- Python 3.10 or newer recommended
- Git
- Git Bash on Windows (commands below use Git Bash syntax)

Check Python and Git:

```bash
python --version
git --version
```

If `python` is not recognized on Windows, try `py --version` and use `py` in place of `python` in the setup commands.

## Local setup (Windows + Git Bash)

Run these commands from the project root, the directory containing `app.py`:

```bash
cd /d/Datathon/Where_Should_We_Fix_First_MVP

python -m venv .venv
source .venv/Scripts/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you need to install the ML dependency separately because it is not yet listed in `requirements.txt`:

```bash
pip install scikit-learn
```

Start the application:

```bash
streamlit run app.py
```

Streamlit normally opens the app at <http://localhost:8501>. Stop it with `Ctrl+C`.

### If virtual-environment activation fails

In Git Bash, use:

```bash
source .venv/Scripts/activate
```

In Windows PowerShell, the activation command is different:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Data files

The app expects these CSV files in the project root:

- `locations.csv` — location attributes and simulated coordinates.
- `incidents.csv` — incident records, severity, type, injuries, timestamps, and resolution fields.
- `public_complaints.csv` — complaint category, reported priority, status, and resolution duration.

The datasets share `location_id`. Incident and complaint records are aggregated by location before being combined with location attributes.

Do not rename the CSV files or move them out of the project root unless you also update the paths in `app.py`.

## How priority scoring works

Location ranking currently uses a transparent weighted heuristic rather than a trained priority classifier:

| Component | Weight |
|---|---:|
| Severity burden | 30% |
| Incident frequency | 25% |
| Complaint volume | 20% |
| Road condition | 15% |
| Local context | 10% |

The component values are normalized before being combined into a 0–100 score. These weights are prototype assumptions and should not be interpreted as validated real-world risk estimates.

## Complaint resolution-time model

The separate supervised-learning experiment predicts complaint resolution duration in days.

- Target: `days_to_resolution` for completed complaints.
- Inputs: complaint category, reported priority, and location characteristics.
- Algorithm: scikit-learn `RandomForestRegressor`.
- Metric: Mean Absolute Error (MAE), in days.
- Baseline: a median prediction calculated from training data.

A previously recorded evaluation showed Random Forest MAE of **3.48 days** versus **3.22 days** for the median baseline. In that evaluation, the Random Forest did not outperform the baseline. Re-run evaluation after changing code or data; do not treat those values as guaranteed for every run.

## Intervention comparison

Intervention options, urgency ratings, and effort units are fixed, illustrative planning assumptions. They are not measured financial costs or proven impact estimates. The app does not establish that a particular intervention will reduce incidents.

## Troubleshooting

**`ModuleNotFoundError`**
Activate `.venv` and install dependencies:

```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

**`streamlit: command not found`**

```bash
python -m streamlit run app.py
```

**CSV file not found**

Make sure the terminal is in the project root and that the three CSV files are beside `app.py`.

**Port 8501 is already in use**

```bash
streamlit run app.py --server.port 8502
```

## Development notes

- Keep `.venv/`, Python caches, local secrets, and editor-specific files out of Git.
- Add every runtime dependency to `requirements.txt` so another developer can reproduce the setup.
- Do not commit API keys, passwords, tokens, or personal credentials.
- The dataset is simulated. Validate data quality, model performance, score weights, and intervention assumptions before any real-world use.

## License

No license has been specified yet. Add a `LICENSE` file if you decide to distribute the project under an open-source license.
