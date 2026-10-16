# CivicPulse — Where Should We Fix First?

CivicPulse is a smart-city decision-support prototype developed for DATATHON 2026. It helps civic operations teams identify locations that may require attention by combining incident records, public complaints, and location characteristics.

The application ranks locations using a transparent weighted priority score, explains the evidence behind each ranking, compares potential interventions, and includes a machine-learning experiment for estimating complaint resolution time.

> **Important:** This project uses synthetic educational data. Coordinates and timestamps are simulated and must not be interpreted as real civic reports. The application is a prototype, not a validated system for real-world public safety or municipal decisions.

## Features

- **Location prioritization:** Rank locations using incident severity, incident frequency, complaint volume, road condition, and local context.
- **Interactive priority map:** Explore simulated coordinates and filter locations by zone, incident type, and minimum priority score.
- **Evidence-based inspection:** Examine incident counts, complaints, reported injuries, location characteristics, score contributions, and historical trends.
- **Intervention comparison:** Compare predefined intervention options using illustrative effort units, urgency ratings, and budget-fit checks.
- **Resolution-time prediction:** Use a Random Forest regression model to estimate complaint resolution duration.
- **Model evaluation:** Compare model performance against a median baseline using Mean Absolute Error (MAE).
- **Historical analysis:** Explore resolution-time patterns across complaint categories.

## Technology Stack

- **Language:** Python
- **Dashboard:** Streamlit
- **Data processing:** Pandas, NumPy
- **Visualization:** Plotly
- **Machine learning:** scikit-learn

## Project Structure

The project root directory is `smart-city/`.

```text
smart-city/
├── app.py
├── app_backup.py
├── incidents.csv
├── locations.csv
├── public_complaints.csv
├── requirements.txt
├── README.md
└── .gitignore
```

A local `.venv/` directory may also exist. It should not be committed to Git.

## Dataset Description

The application uses three synthetic datasets.

| File | Description |
|---|---|
| `locations.csv` | Location attributes, including zone, road type, road condition, population density, proximity to schools and hospitals, pedestrian activity, and simulated coordinates. |
| `incidents.csv` | Incident records, including incident type, severity, injuries, reporting source, resolution status, timestamps, and resolution duration. |
| `public_complaints.csv` | Public complaint records, including category, reported priority, status, creation timestamp, and resolution duration. |

All three datasets share the `location_id` field.

The application aggregates incident and complaint records by location before joining them with location attributes. Missing numeric values in the combined location-level dataset are filled with zero for the current prototype.

## Prerequisites

- Python 3.10 or newer
- Git
- A terminal such as Git Bash, PowerShell, or Command Prompt

Verify the installations:

```bash
python --version
git --version
```

On Windows, if `python` is unavailable, try:

```powershell
py --version
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/HERMON19DP/Datathon.git
cd Datathon
```

If you have already cloned the repository into a local directory named `smart-city`, navigate to that directory instead.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Git Bash:**

```bash
source .venv/Scripts/activate
```

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux or macOS:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ensure `requirements.txt` includes every runtime dependency, including `scikit-learn`, which is imported by `app.py`.

### 5. Run the application

Run the following command from the project root, where `app.py` and the CSV files are located:

```bash
streamlit run app.py
```

The application will normally be available at:

<http://localhost:8501>

Stop the application using `Ctrl+C`.

If port 8501 is already occupied, use:

```bash
streamlit run app.py --server.port 8502
```

## How Location Prioritization Works

The application uses a weighted heuristic to calculate a priority score between 0 and 100.

| Component | Weight |
|---|---:|
| Severity burden | 30% |
| Incident frequency | 25% |
| Complaint volume | 20% |
| Road condition | 15% |
| Local context | 10% |

The components are normalized before being combined into the final score.

Local context incorporates population density, proximity to schools and hospitals, and pedestrian activity.

The resulting score supports relative prioritization within the available dataset. It is not a calibrated probability of future incidents or a validated real-world risk score.

### Understanding the Dashboard

1. Use the sidebar filters to select a zone, incident type, or minimum score.
2. Explore the priority map and ranked locations.
3. Select a location to inspect its score components and supporting evidence.
4. Review incident and complaint trends and the intervention suggestions.
5. Compare alternative interventions against the illustrative effort budget.

## Complaint Resolution-Time Prediction

The application includes a supervised-learning experiment that estimates the number of days required to resolve a complaint.

### Model

- **Algorithm:** `RandomForestRegressor`
- **Target:** `days_to_resolution`
- **Training records:** Complaints marked `Resolved` or `Closed` with valid, non-negative resolution durations
- **Features:** Complaint category, reported priority, zone, road type, road condition, pedestrian activity, population density, and proximity to schools and hospitals
- **Data split:** 80% training and 20% testing, using `random_state=42`
- **Evaluation metric:** Mean Absolute Error (MAE), measured in days
- **Baseline:** Median resolution duration calculated from the training set

The preprocessing pipeline imputes missing values and one-hot encodes categorical features.

### Interpreting the Results

The dashboard compares Random Forest MAE with the median baseline MAE. Lower MAE indicates smaller average absolute prediction errors.

A previously recorded evaluation showed:

- Random Forest MAE: 3.48 days
- Median baseline MAE: 3.22 days

In that evaluation, the Random Forest did not outperform the baseline. These values are historical reference results, not guaranteed results for every run. Use the current dashboard evaluation when reporting model performance.

The prediction is experimental and should not be interpreted as a guaranteed resolution date.

## Intervention Comparison

The dashboard offers predefined intervention options, including:

- Targeted inspection
- Focused repair or maintenance
- Engineering assessment
- Monitoring and additional data collection

Effort units and urgency ratings are illustrative planning assumptions. They are not actual financial costs, measured resource requirements, or proven impact estimates.

The application does not establish that a particular intervention will reduce incidents. Recommendations should be treated as suggestions for further investigation.

## Limitations

- The datasets are synthetic and do not represent verified municipal records.
- The priority-score weights are assumptions and have not been validated against real-world outcomes.
- The resolution-time model is an experimental predictive model and may not outperform a simple baseline.
- The intervention options use illustrative effort and urgency values.
- The prototype does not establish causal relationships between interventions and incident reduction.
- Real-world deployment would require validated data, domain review, appropriate safeguards, and evaluation against actual operational outcomes.

## Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and install the dependencies:

```bash
pip install -r requirements.txt
```

If scikit-learn is missing, verify that it is listed in `requirements.txt` and install it:

```bash
pip install scikit-learn
```

### CSV file not found

Ensure that `locations.csv`, `incidents.csv`, and `public_complaints.csv` are in the same directory as `app.py`, and run Streamlit from the project root.

### Port already in use

```bash
streamlit run app.py --server.port 8502
```

## Development Guidelines

- Keep the three dataset filenames unchanged unless the corresponding paths in `app.py` are updated.
- Add every runtime dependency to `requirements.txt`.
- Keep `.venv/`, cache files, temporary files, and secrets out of Git.
- Re-run the application and evaluate the model after changing code or data.
- Document score assumptions and model limitations when presenting results.
- Do not use the current synthetic dataset for actual public-safety or municipal decisions.

## License

No license has been specified. Add a `LICENSE` file if the project is to be distributed under an open-source license.

---

**CivicPulse — Where Should We Fix First?**

*A synthetic-data smart-city decision-support prototype for DATATHON 2026.*
