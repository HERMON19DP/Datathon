# CivicPulse — Feature Guide & Demo Walkthrough

> **Purpose:** Explain the features that are currently implemented in `app.py`, how to use them, and what their outputs mean.
>
> **Data warning:** CivicPulse uses synthetic educational data. Coordinates and timestamps are simulated. This is a Datathon prototype, not a validated system for real municipal or public-safety decisions.

## 1. Application overview

CivicPulse is a Streamlit dashboard titled **“Where Should We Fix First?”**. It loads three CSV files from the same directory as `app.py`:

- `locations.csv` — location attributes and simulated coordinates.
- `incidents.csv` — incident type, severity, injuries, resolution status, timestamp, and duration.
- `public_complaints.csv` — complaint category, reported priority, status, creation timestamp, and resolution duration.

The app aggregates incident and complaint records by `location_id`, combines them with location attributes, calculates a weighted location-priority score, and presents maps, rankings, supporting evidence, resolution-time modelling, and intervention comparisons.

The dashboard has five main user-facing areas:

1. **Explore priorities** — sidebar filters used to control the map, metrics, and ranked table.
2. **Priority map** — a scatter plot of filtered locations using simulated longitude and latitude.
3. **Ranked locations** — the top 10 locations in the current filtered view.
4. **Inspect the evidence** — details and evidence for a selected location.
5. **Predict complaint resolution time** and **Compare interventions** — separate tools for experimental prediction and illustrative planning comparisons.

---

## 2. Explore priorities: filters

The **Explore priorities** controls are in the sidebar. They filter the location records shown in the map, summary metrics, and ranked table.

### Zone

- **What it does:** Restricts the current view to locations in the selected zone.
- **How to use it:** Choose **All zones** to include every zone, or choose a specific zone to focus on that area.
- **What changes:** The number of locations in view, the aggregate incident/complaint/road metrics, the map points, and the ranked table.

### Incident type

- **What it does:** Keeps locations that have at least one record of the selected incident type.
- **How to use it:** Choose **All incident types** for the full location set, or choose a type such as one of the incident types present in the CSV.
- **What changes:** The displayed locations, metrics, map, and ranking table.
- **Important detail:** This filter selects locations where the chosen incident type has a positive count. It does **not** recalculate the priority score using only that incident type; the score remains based on the overall aggregated location signals.

### Minimum priority score

- **What it does:** Hides locations whose calculated `priority_score` is below the chosen threshold.
- **How to use it:** Move the slider from 0 to 100. A higher threshold narrows the displayed set.
- **What changes:** The map, summary metrics, and ranked table.
- **Important detail:** This is a display filter, not a way to change the score or its weights.

### Score weights shown in the sidebar

The sidebar displays the current baseline weights:

| Component | Weight |
|---|---:|
| Severity burden | 30% |
| Incident frequency | 25% |
| Complaint volume | 20% |
| Road condition | 15% |
| Local context | 10% |

These weights are explanatory text in the current UI; there are no controls to adjust them interactively.

---

## 3. Summary metrics

Four metric cards appear above the map and ranked table. They are calculated from the **currently filtered locations**:

- **Locations in view:** Number of locations remaining after the selected filters.
- **Incidents:** Sum of incident counts across the locations in view.
- **Public complaints:** Sum of complaint counts across the locations in view.
- **Poor / critical roads:** Number of locations in view whose road condition is `Poor` or `Critical`.

These values change when the sidebar filters change. They are not city-wide totals unless all locations are included.

---

## 4. Priority map

The map is a Plotly scatter plot using `longitude` on the horizontal axis and `latitude` on the vertical axis.

### How to read it

- **Each point** represents a location in the current filtered view.
- **Point colour** represents the calculated priority score; the colour scale moves through yellow to red.
- **Point size** represents the incident count. Larger points have more incident records.
- **Hover details** include location ID, zone, road condition, incident count, complaint count, and priority score.

### Important limitations

The plot title explicitly says **“Simulated coordinates — not a real city map.”** These coordinates are synthetic and should not be used to navigate to or identify real incident sites. The chart is a spatial overview of the supplied demonstration data, not a map of a verified city.

If no locations match the filters, the app displays a message saying no locations match the selected filters.

---

## 5. Ranked locations

The table beside the map shows the **top 10 locations** in the current filtered view. The app sorts locations by `priority_score` in descending order before applying the filters.

The table shows:

- `location_id`
- `zone`
- `priority_score` (rounded to one decimal place)
- `priority_band`
- `incident_count`
- `complaint_count`
- `road_condition`

The UI caption says that ranks are relative to the current filtered view.

### How to use the ranking

1. Apply filters to focus on a zone or incident type, if needed.
2. Review the highest-scoring locations in the table.
3. Select a location in **Inspect the evidence** to understand the data behind its score.
4. Do not use the score alone as a decision to allocate resources; inspect the supporting evidence and account for the synthetic-data limitation.

### Priority score bands

The app creates these bands from the calculated score:

- **Monitor:** score from approximately 0 through 33.
- **Review:** above 33 through 66.
- **High priority:** above 66 through 100.

The final score is a weighted heuristic, not a trained model's prediction and not a calibrated probability of future incidents.

---

## 6. How the priority score is calculated

The score is calculated during data loading. The contributing factors are min-max normalized so their values can be combined on a comparable scale.

### Severity burden — 30%

The app maps incident severity to numeric values (`Low` = 1, `Medium` = 2, `High` = 3, `Critical` = 4), sums those values by location, then normalizes the sum across locations.

### Incident frequency — 25%

The app counts incident records for each location and normalizes those counts.

### Complaint volume — 20%

The app counts public complaint records for each location and normalizes those counts.

### Road condition — 15%

Road conditions are mapped to an ordered numeric scale (`Good` = 0, `Fair` = 1, `Poor` = 2, `Critical` = 3), then normalized.

### Local context — 10%

The app builds an exposure value from:
- normalized population density, weighted 40% within this context component;
- `near_school`, weighted 25%;
- `near_hospital`, weighted 20%;
- pedestrian activity (`Low` = 0, `Medium` = 0.5, `High` = 1), weighted 15%.

That exposure value is normalized across locations. It then contributes 10% to the final score.

### Final score

The app calculates:

`priority_score = 100 × (0.30 × severity + 0.25 × frequency + 0.20 × complaints + 0.15 × road condition + 0.10 × local context)`

Here, each named component is its normalized value. If a component has no variation across locations, its normalized value is set to zero.

**Interpretation:** A high score means a location scores highly under the project's chosen weighting assumptions. It does not prove causation, predict future incidents, or establish an objectively correct order for real-world action.

---

## 7. Inspect the evidence

The **Inspect the evidence** section lets the user choose a location from the current filtered view. It then displays the selected location's score and related evidence.

### Location selector

The selector contains the location IDs in the current filtered view. If filters exclude every location, the app instead asks the user to adjust filters.

### Four headline metrics

For the selected location, the app displays:

- **Priority score:** Score out of 100, formatted to one decimal place.
- **Incidents:** Aggregated number of incident records.
- **Complaints:** Aggregated number of public complaints.
- **Reported injuries:** Sum of the incident injury field for that location.

### “Why it ranks here” table

This table displays five factors:

- Severity burden
- Incident frequency
- Complaint volume
- Road condition
- Local context

For each factor, it shows:
- the normalized factor value;
- the factor's fixed weight;
- the weighted contribution to the final 0–100 score.

The weighted contribution is calculated as `100 × normalized factor × weight` and rounded to one decimal place. The normalized factor is rounded to two decimals in the displayed table.

The section also shows the selected location's road condition, zone, road type, whether it is near a school or hospital, and its pedestrian-activity level.

### “Issue history and intervention ideas”

This panel shows:
- a monthly line chart of incident counts and complaint counts for the selected location;
- evidence-triggered intervention ideas based on incident types, complaint categories, counts, and road condition.

The current code can display suggestions such as:

- **Road inspection / pothole repair** when pothole incidents are present and the road is `Poor`/`Critical`, or there are at least two pothole incidents.
- **Drainage inspection** when there are at least two flooding or blocked-drain incidents.
- **Traffic-signal / road-safety inspection** when there are at least two signal-failure or collision incidents.
- **Streetlight audit** when there are at least two streetlight outages.
- **Pedestrian-safety review** when there are at least two complaints in the `Pedestrian safety` category.
- **Field verification** when none of the above rules produces a suggestion.

The panel displays up to four suggestions. These are rule-based prompts for further inspection, not ML-generated recommendations and not proof that the suggested intervention will work.

### How to inspect a location effectively

1. Choose a location from the selector.
2. Read the score and headline counts.
3. Use the weighted-contribution table to see which factors contribute most to the score.
4. Review location characteristics and monthly incident/complaint patterns.
5. Read the intervention ideas and check which observed records triggered them.
6. Describe the evidence as an association or observed pattern; do not claim that the data proves a cause.

---

## 8. Predict complaint resolution time

This is a separate machine-learning section. It estimates how many days a complaint may take to resolve, based on complaint attributes and location characteristics.

### How the model is trained

The code trains a scikit-learn `RandomForestRegressor` inside `train_resolution_model()`.

- **Target:** `days_to_resolution`
- **Training candidates:** Complaints with status `Resolved` or `Closed`, a non-missing duration, and a duration greater than or equal to zero.
- **Categorical features:** complaint `category`, `priority_reported`, location `zone`, `road_type`, `road_condition`, and `pedestrian_activity`.
- **Numeric features:** `population_density_per_km2`, `near_school`, and `near_hospital`.
- **Split:** 80% training and 20% testing, with `random_state=42`.
- **Model:** Random Forest with 250 trees, `min_samples_leaf=3`, `random_state=42`, and all available CPU cores (`n_jobs=-1`).
- **Preprocessing:** Missing categorical values are filled with the most frequent value and one-hot encoded; missing numeric values are filled with the median.
- **Evaluation:** Mean Absolute Error (MAE) on the held-out test data.
- **Baseline:** A constant prediction equal to the median resolution duration in the training set.

Only completed complaints are used as target examples. The complaint status itself is not one of the prediction features.

### The four model metrics

The model section reports:

- **Training complaints:** Number of examples in the training split.
- **Test complaints:** Number of examples in the held-out test split.
- **Random Forest MAE:** Average absolute error of the Random Forest predictions, in days.
- **Median baseline MAE:** Average absolute error from always predicting the training-set median, in days.

Lower MAE is better. The app explicitly reports whether the Random Forest MAE is lower than the baseline or whether the median baseline performs better.

### “Make a prediction” tab

Use these controls:

1. **Complaint category:** Choose a category from the values present in `public_complaints.csv`.
2. **Reported priority:** Choose a reported priority present in the complaint data.
3. **Location:** Choose a location ID.

The app retrieves that location's zone, road type, road condition, pedestrian activity, population density, and school/hospital proximity flags from `locations.csv`. It combines these values with the chosen complaint category and priority, then passes the row to the trained model.

The output shows:

- **Estimated resolution time:** The model's predicted duration in days, clipped so it cannot be below zero.
- **Historical category median:** Median observed duration among completed complaints in the selected category.
- **Completed examples in category:** Number of completed complaints available for that category.

The prediction is an estimate, not a promised service deadline. It depends on patterns in synthetic historical data and may be inaccurate for individual complaints.

### “Model evaluation” tab

This tab plots actual resolution days against predicted resolution days for held-out test complaints. A dashed diagonal line indicates where predictions would exactly equal actual values. Points closer to that line indicate smaller errors for those examples.

It also displays a table comparing Random Forest MAE with the median baseline MAE.

### “Historical patterns” tab

This tab groups completed complaints by category and displays:
- number of completed complaints;
- median resolution duration;
- mean resolution duration.

It includes a bar chart of median resolution time by category. This is a descriptive summary of the completed records, not a prediction for a specific new complaint.

### How to explain this model honestly

The model is an implemented ML experiment, but it should only be described as outperforming the baseline if the current displayed MAE is lower than the median baseline MAE. The app computes these values at runtime; use the current dashboard metrics in a presentation rather than assuming old evaluation figures remain the same.

---

## 9. Compare interventions

This section compares two predefined response options and checks their illustrative effort requirements against an effort budget.

### Available options

| Option | Illustrative effort units | Urgency (1–3) | Current guidance text |
|---|---:|---:|---|
| Targeted inspection | 1 | 2 | Useful when evidence is incomplete |
| Focused repair / maintenance | 3 | 3 | Suitable when repeated issue and infrastructure evidence align |
| Engineering assessment | 4 | 3 | Suitable for severe or complex patterns |
| Monitor and collect more data | 1 | 1 | Suitable when signals are weak or inconsistent |

These values are hard-coded in `app.py`. They are not calculated from a trained model and are not actual money, staff-hours, or validated impact estimates.

### How to use it

1. Choose an intervention under **Option A**.
2. Choose another intervention under **Option B**.
3. Set **Available effort units** using the slider (1–8; default 4).
4. Compare the resulting table.

The table shows:
- **Intervention:** Selected option.
- **Illustrative effort units:** Fixed effort value assigned to that option in code.
- **Urgency (1–3):** Fixed ordinal rating assigned to the option.
- **Fits effort budget:** `Yes` if its effort units are less than or equal to the slider value; otherwise `No`.
- **When to consider:** The option's predefined guidance text.

If the same intervention is selected in both controls, the app removes the duplicate and displays it once.

### What the comparison does and does not mean

- **Effort units** are relative, illustrative values, not real resource estimates.
- **Urgency** is a predefined rating, not a model prediction of harm or benefit.
- **Fits effort budget** is a simple comparison against the slider value; it is not an approved budget calculation.
- **When to consider** is static guidance written into the app.
- The comparison does not currently use the selected location's evidence to calculate an optimal intervention, nor does it estimate intervention outcomes or cost-effectiveness.

Use this section to discuss trade-offs in a prototype demonstration, not as an automated recommendation for real municipal spending.

---

## 10. Data and method notes

The expandable **Data and method notes** panel reiterates:
- the five weighted components used for priority scoring;
- the resolution-time model features;
- that only resolved/closed complaints with valid durations are training targets;
- that evaluation uses a held-out test split and a training-set median baseline.

The app also displays a footer noting that the dashboard uses simulated data for demonstration purposes.

### Data-handling details in the current code

- The location table is the anchor table; incidents and complaints are aggregated by `location_id` before being joined to locations.
- Numeric missing values in the combined location-level table are filled with zero.
- Incident severities are mapped to numeric values for the severity calculations.
- Complaint statuses `Open`, `In progress`, and `Assigned` are treated as open-like when the app aggregates complaint data.
- Monthly trend charts are based on incident timestamps and complaint creation timestamps.

---

## 11. Suggested demo sequence

A short demo can follow this order:

1. **Start with Explore priorities.** Explain that the zone, incident-type, and minimum-score controls filter the current view.
2. **Change a filter.** Point out that the map, metrics, and ranked table update together.
3. **Read the Priority map.** Explain point colour and size, and explicitly note that the coordinates are simulated.
4. **Review Ranked locations.** Show that the table lists the top 10 locations in the filtered view.
5. **Inspect the evidence.** Select a location, explain its weighted score components, and show the monthly history and rule-triggered ideas.
6. **Predict complaint resolution time.** Choose a category, reported priority, and location; show the estimate, category median, and number of completed examples.
7. **Open Model evaluation.** Compare Random Forest MAE with baseline MAE; state which is lower in the current run.
8. **Compare interventions.** Select two options, change the effort budget, and explain that the values are illustrative rather than real cost or impact estimates.

---

## 12. Known limitations and responsible use

- All supplied data are synthetic; locations, timestamps, and records are not verified real-world reports.
- The priority score is a transparent weighted heuristic, not a trained ML model or a calibrated risk probability.
- The score weights are assumptions and have not been validated against real outcomes.
- The incident-type filter changes which locations are shown; it does not recompute the score for only that incident type.
- The Random Forest is experimental and may not beat the simple median baseline.
- Intervention effort and urgency values are hard-coded illustrative assumptions.
- Rule-triggered ideas are prompts for further inspection, not causal conclusions or guaranteed effective interventions.
- The app should not be used to make actual public-safety, infrastructure, or municipal resource-allocation decisions.

---

## Repository references

- Main application: [`app.py`](app.py)
- Dataset descriptions and setup instructions: [`README.md`](README.md)
- Dependencies: [`requirements.txt`](requirements.txt)

**CivicPulse — Where Should We Fix First?**  
*A synthetic-data smart-city decision-support prototype for DATATHON 2026.*
