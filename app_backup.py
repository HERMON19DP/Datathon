import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

st.set_page_config(page_title="Where Should We Fix First?", page_icon="🧭", layout="wide")

DATA = Path(__file__).parent
@st.cache_data
def load_data():
    locations = pd.read_csv(DATA / "locations.csv")
    incidents = pd.read_csv(DATA / "incidents.csv", parse_dates=["timestamp"])
    complaints = pd.read_csv(DATA / "public_complaints.csv", parse_dates=["created_at"])
    # Keep the location table as the anchor; aggregate event-level records before joining.
    sev = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    inc = incidents.copy()
    inc["severity_value"] = inc["severity"].map(sev).fillna(1)
    inc["high_critical"] = inc["severity"].isin(["High", "Critical"]).astype(int)
    inc["month"] = inc["timestamp"].dt.to_period("M").astype(str)
    ia = inc.groupby("location_id").agg(
        incident_count=("incident_id","count"),
        severity_mean=("severity_value","mean"),
        severity_sum=("severity_value","sum"),
        high_critical_count=("high_critical","sum"),
        injuries=("injuries","sum"),
        unresolved_incidents=("resolved",lambda x:(x==0).sum()),
        avg_resolution_hours=("resolution_hours","mean"),
    ).reset_index()
    # Category-level evidence for recommendations
    itypes = inc.pivot_table(index="location_id", columns="incident_type", values="incident_id",
                             aggfunc="count", fill_value=0).reset_index()
    ca = complaints.copy()
    ca["open_like"] = ca["status"].isin(["Open","In progress","Assigned"]).astype(int)
    ca["month"] = ca["created_at"].dt.to_period("M").astype(str)
    comp = ca.groupby("location_id").agg(
        complaint_count=("complaint_id","count"),
        open_complaints=("open_like","sum"),
        avg_days_to_resolution=("days_to_resolution","mean"),
    ).reset_index()
    cats = ca.pivot_table(index="location_id", columns="category", values="complaint_id",
                          aggfunc="count", fill_value=0).reset_index()
    df = locations.merge(ia,on="location_id",how="left").merge(itypes,on="location_id",how="left").merge(comp,on="location_id",how="left").merge(cats,on="location_id",how="left")
    numeric = df.select_dtypes(include="number").columns
    df[numeric] = df[numeric].fillna(0)
    # Transparent, reproducible heuristic baseline. Min-max scaling makes components comparable.
    def norm(s):
        lo, hi = s.min(), s.max()
        return (s-lo)/(hi-lo) if hi > lo else s*0
    df["severity_component"] = norm(df["severity_sum"])
    df["frequency_component"] = norm(df["incident_count"])
    df["complaint_component"] = norm(df["complaint_count"])
    cond = {"Good":0, "Fair":1, "Poor":2, "Critical":3}
    df["condition_component"] = norm(df["road_condition"].map(cond).fillna(0))
    exposure = (
        norm(df["population_density_per_km2"]) * 0.4 +
        df["near_school"].astype(float) * 0.25 +
        df["near_hospital"].astype(float) * 0.2 +
        df["pedestrian_activity"].map({"Low":0,"Medium":0.5,"High":1}).fillna(0) * 0.15
    )
    df["context_component"] = norm(exposure)
    df["priority_score"] = 100 * (
        0.30*df["severity_component"] +
        0.25*df["frequency_component"] +
        0.20*df["complaint_component"] +
        0.15*df["condition_component"] +
        0.10*df["context_component"]
    )
    df["priority_band"] = pd.cut(df["priority_score"],[-0.01,33,66,100.01],labels=["Monitor","Review","High priority"])
    return locations, incidents, complaints, df.sort_values("priority_score",ascending=False), inc, ca

@st.cache_resource
def train_resolution_model():
    """Train and evaluate a complaint resolution-time model on completed complaints only."""
    loc = pd.read_csv(DATA / "locations.csv")
    complaints_data = pd.read_csv(DATA / "public_complaints.csv")

    # Only complaints with a completed lifecycle and a valid observed duration are targets.
    completed = complaints_data[
        complaints_data["status"].isin(["Resolved", "Closed"])
        & complaints_data["days_to_resolution"].notna()
        & (complaints_data["days_to_resolution"] >= 0)
    ].copy()
    completed = completed.merge(loc, on="location_id", how="left", validate="many_to_one")

    categorical_features = [
        "category", "priority_reported", "zone", "road_type",
        "road_condition", "pedestrian_activity"
    ]
    numeric_features = [
        "population_density_per_km2", "near_school", "near_hospital"
    ]
    features = categorical_features + numeric_features
    target = "days_to_resolution"

    # Coerce booleans/numeric fields safely for the sklearn pipeline.
    for col in numeric_features:
        completed[col] = pd.to_numeric(completed[col], errors="coerce")
    X = completed[features]
    y = completed[target].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), categorical_features),
            ("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy="median"))
            ]), numeric_features),
        ]
    )
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=250, min_samples_leaf=3, random_state=42, n_jobs=-1
        )),
    ])
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    baseline_value = float(y_train.median())
    model_mae = float(mean_absolute_error(y_test, predictions))
    baseline_mae = float(mean_absolute_error(y_test, np.full(len(y_test), baseline_value)))

    test_results = pd.DataFrame({
        "Actual days": y_test.to_numpy(),
        "Predicted days": predictions,
    })
    return {
        "model": model,
        "features": features,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "model_mae": model_mae,
        "baseline_mae": baseline_mae,
        "baseline_value": baseline_value,
        "train_count": len(X_train),
        "test_count": len(X_test),
        "completed_count": len(completed),
        "test_results": test_results,
        "locations": loc,
        "completed": completed,
    }


locations, incidents, complaints, ranked, inc, ca = load_data()
st.title("🧭 Where Should We Fix First?")
st.caption("City Priority Intelligence")

with st.sidebar:
    st.header("Explore priorities")
    zones = ["All zones"] + sorted(ranked["zone"].dropna().unique().tolist())
    zone = st.selectbox("Zone", zones)
    issue_types = ["All incident types"] + sorted(inc["incident_type"].dropna().unique().tolist())
    issue = st.selectbox("Incident type", issue_types)
    min_score = st.slider("Minimum priority score", 0, 100, 0)
    st.divider()
    st.markdown("**Baseline score weights**")
    st.caption("Severity 30% · Frequency 25% · Complaints 20% · Road condition 15% · Context 10%")

view = ranked.copy()
if zone != "All zones":
    view = view[view["zone"] == zone]
if issue != "All incident types":
    if issue in view.columns:
        view = view[view[issue] > 0]
    else:
        view = view.iloc[0:0]
view = view[view["priority_score"] >= min_score]
top = view.head(10)

m1,m2,m3,m4 = st.columns(4)
m1.metric("Locations in view", f"{len(view):,}")
m2.metric("Incidents", f"{int(view['incident_count'].sum()):,}")
m3.metric("Public complaints", f"{int(view['complaint_count'].sum()):,}")
m4.metric("Poor / critical roads", f"{int(view['road_condition'].isin(['Poor','Critical']).sum()):,}")
st.divider()

left,right = st.columns([1.35,1])
with left:
    st.subheader("Priority map")
    if len(view):
        fig = px.scatter(
            view, x="longitude", y="latitude", color="priority_score", size="incident_count",
            hover_name="location_id",
            hover_data={"zone":True,"road_condition":True,"incident_count":True,"complaint_count":True,"priority_score":":.1f","longitude":False,"latitude":False},
            color_continuous_scale="YlOrRd", size_max=20,
            labels={"longitude":"Synthetic longitude","latitude":"Synthetic latitude","priority_score":"Priority score"},
            title="Simulated coordinates — not a real city map"
        )
        fig.update_layout(height=440, margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No locations match the selected filters.")
with right:
    st.subheader("Ranked locations")
    show_cols = ["location_id","zone","priority_score","priority_band","incident_count","complaint_count","road_condition"]
    table = top[show_cols].copy()
    table["priority_score"] = table["priority_score"].round(1)
    st.dataframe(table,hide_index=True,use_container_width=True,height=440)
    st.caption("Ranks are relative to the current filtered view.")

st.divider()
st.subheader("Inspect the evidence")
if len(view):
    selected_id = st.selectbox("Select a location", view["location_id"].tolist(), index=0)
    row = ranked.loc[ranked["location_id"] == selected_id].iloc[0]
    a,b,c,d = st.columns(4)
    a.metric("Priority score", f"{row['priority_score']:.1f}/100")
    b.metric("Incidents", int(row["incident_count"]))
    c.metric("Complaints", int(row["complaint_count"]))
    d.metric("Reported injuries", int(row["injuries"]))
    x,y = st.columns([1,1])
    with x:
        st.markdown("**Why it ranks here**")
        components = pd.DataFrame({
            "Evidence factor":["Severity burden","Incident frequency","Complaint volume","Road condition","Local context"],
            "Normalized factor":[row["severity_component"],row["frequency_component"],row["complaint_component"],row["condition_component"],row["context_component"]],
            "Weight":[0.30,0.25,0.20,0.15,0.10],
        })
        components["Weighted contribution"] = 100*components["Normalized factor"]*components["Weight"]
        components["Normalized factor"] = components["Normalized factor"].round(2)
        components["Weighted contribution"] = components["Weighted contribution"].round(1)
        st.dataframe(components,hide_index=True,use_container_width=True)
        st.write(f"Road condition: **{row['road_condition']}** · Zone: **{row['zone']}** · Road type: **{row['road_type']}**")
        st.write(f"Near school: **{'Yes' if row['near_school'] else 'No'}** · Near hospital: **{'Yes' if row['near_hospital'] else 'No'}** · Pedestrian activity: **{row['pedestrian_activity']}**")
    with y:
        st.markdown("**Issue history and intervention ideas**")
        loc_inc = incidents[incidents["location_id"] == selected_id]
        loc_com = complaints[complaints["location_id"] == selected_id]
        if len(loc_inc):
            monthly_i = loc_inc.assign(month=loc_inc["timestamp"].dt.to_period("M").astype(str)).groupby("month").size().rename("Incidents").reset_index()
        else:
            monthly_i = pd.DataFrame({"month":[],"Incidents":[]})
        if len(loc_com):
            monthly_c = loc_com.assign(month=loc_com["created_at"].dt.to_period("M").astype(str)).groupby("month").size().rename("Complaints").reset_index()
        else:
            monthly_c = pd.DataFrame({"month":[],"Complaints":[]})
        trend = pd.merge(monthly_i,monthly_c,on="month",how="outer").fillna(0).sort_values("month")
        if len(trend):
            st.line_chart(trend.set_index("month")[["Incidents","Complaints"]])
        types = loc_inc["incident_type"].value_counts()
        cats = loc_com["category"].value_counts()
        evidence_terms = []
        for name,count in types.items():
            if name in ["Pothole"] and (row["road_condition"] in ["Poor","Critical"] or count>=2):
                evidence_terms.append(("Road inspection / pothole repair",f"{count} pothole incident(s); road condition {row['road_condition']}"))
            if name in ["Flooding","Blocked drain"] and count>=2:
                evidence_terms.append(("Drainage inspection",f"{count} flooding/blocked-drain incident(s)"))
            if name in ["Signal failure","Collision"] and count>=2:
                evidence_terms.append(("Traffic-signal / road-safety inspection",f"{count} signal-failure/collision incident(s)"))
            if name in ["Streetlight outage"] and count>=2:
                evidence_terms.append(("Streetlight audit",f"{count} streetlight outage(s)"))
        if "Pedestrian safety" in cats.index and cats["Pedestrian safety"]>=2:
            evidence_terms.append(("Pedestrian-safety review",f"{int(cats['Pedestrian safety'])} pedestrian-safety complaint(s)"))
        if not evidence_terms:
            evidence_terms.append(("Field verification", "Evidence is limited; verify conditions before committing resources"))
        for name,reason in evidence_terms[:4]:
            st.markdown(f"- **{name}** — {reason}")
else:
    st.info("Adjust filters to inspect a location.")


st.divider()
st.subheader("Predict complaint resolution time")
st.write("Estimate the number of days to resolve a complaint using historical completed complaints and location characteristics.")

try:
    resolution = train_resolution_model()
    model = resolution["model"]
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Training complaints", f"{resolution['train_count']:,}")
    metric2.metric("Test complaints", f"{resolution['test_count']:,}")
    metric3.metric("Random Forest MAE", f"{resolution['model_mae']:.2f} days")
    metric4.metric("Median baseline MAE", f"{resolution['baseline_mae']:.2f} days")

    if resolution["model_mae"] < resolution["baseline_mae"]:
        st.info(f"Random Forest MAE is {resolution['baseline_mae'] - resolution['model_mae']:.2f} days lower than the median baseline.")
    else:
        st.info(f"Median baseline currently performs better by {resolution['model_mae'] - resolution['baseline_mae']:.2f} days MAE.")

    pred_tab, eval_tab, history_tab = st.tabs(["Make a prediction", "Model evaluation", "Historical patterns"])
    with pred_tab:
        st.markdown("**Estimate a new complaint's resolution time**")
        p1, p2, p3 = st.columns(3)
        categories = sorted(complaints["category"].dropna().unique().tolist())
        priorities = sorted(complaints["priority_reported"].dropna().unique().tolist())
        location_options = ranked["location_id"].astype(str).tolist()
        with p1:
            selected_category = st.selectbox("Complaint category", categories, key="resolution_category")
        with p2:
            selected_priority = st.selectbox("Reported priority", priorities, key="resolution_priority")
        with p3:
            selected_location = st.selectbox("Location", location_options, key="resolution_location")

        selected_location_row = resolution["locations"].loc[
            resolution["locations"]["location_id"].astype(str) == str(selected_location)
        ].iloc[0]
        prediction_input = pd.DataFrame([{
            "category": selected_category,
            "priority_reported": selected_priority,
            "zone": selected_location_row.get("zone"),
            "road_type": selected_location_row.get("road_type"),
            "road_condition": selected_location_row.get("road_condition"),
            "pedestrian_activity": selected_location_row.get("pedestrian_activity"),
            "population_density_per_km2": selected_location_row.get("population_density_per_km2"),
            "near_school": selected_location_row.get("near_school"),
            "near_hospital": selected_location_row.get("near_hospital"),
        }], columns=resolution["features"])
        predicted_days = max(0.0, float(model.predict(prediction_input)[0]))
        similar = resolution["completed"].loc[
            resolution["completed"]["category"] == selected_category, "days_to_resolution"
        ]
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated resolution time", f"{predicted_days:.1f} days")
        c2.metric("Historical category median", f"{similar.median():.1f} days" if len(similar) else "Not available")
        c3.metric("Completed examples in category", f"{len(similar):,}")

    with eval_tab:
        st.markdown("**Held-out test set: actual vs predicted**")
        test_results = resolution["test_results"]
        eval_fig = px.scatter(
            test_results, x="Actual days", y="Predicted days",
            opacity=0.55, labels={"Actual days": "Actual resolution time (days)", "Predicted days": "Predicted resolution time (days)"},
            title="Prediction quality on unseen test complaints"
        )
        upper = float(max(test_results["Actual days"].max(), test_results["Predicted days"].max()))
        eval_fig.add_shape(type="line", x0=0, y0=0, x1=upper, y1=upper, line=dict(dash="dash"))
        eval_fig.update_layout(height=380, margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(eval_fig, use_container_width=True)
        st.write("MAE is the average absolute difference between predicted and actual days. Lower is better.")
        st.dataframe(pd.DataFrame([
            {"Model": "Random Forest Regressor", "MAE (days)": round(resolution["model_mae"], 3)},
            {"Model": "Training-set median baseline", "MAE (days)": round(resolution["baseline_mae"], 3)},
        ]), hide_index=True, use_container_width=True)

    with history_tab:
        hist = resolution["completed"].groupby("category").agg(
            complaints=("complaint_id", "count"),
            median_days=("days_to_resolution", "median"),
            mean_days=("days_to_resolution", "mean"),
        ).reset_index().sort_values("median_days", ascending=False)
        hist["median_days"] = hist["median_days"].round(1)
        hist["mean_days"] = hist["mean_days"].round(1)
        hist_fig = px.bar(hist, x="category", y="median_days", hover_data=["complaints", "mean_days"],
                          labels={"category": "Complaint category", "median_days": "Median resolution time (days)"},
                          title="Historical median resolution time by category")
        hist_fig.update_layout(height=360, margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(hist_fig, use_container_width=True)
        st.dataframe(hist.rename(columns={"category":"Category", "complaints":"Completed complaints", "median_days":"Median days", "mean_days":"Mean days"}), hide_index=True, use_container_width=True)
except Exception as exc:
    st.error("The resolution-time model could not be trained. Check that scikit-learn is installed and the complaint/location CSV schemas are unchanged.")
    st.exception(exc)

st.divider()
st.subheader("Compare interventions")
options = {
    "Targeted inspection": {"effort":1,"urgency":2,"evidence":"Useful when evidence is incomplete"},
    "Focused repair / maintenance": {"effort":3,"urgency":3,"evidence":"Suitable when repeated issue and infrastructure evidence align"},
    "Engineering assessment": {"effort":4,"urgency":3,"evidence":"Suitable for severe or complex patterns"},
    "Monitor and collect more data": {"effort":1,"urgency":1,"evidence":"Suitable when signals are weak or inconsistent"},
}
ci1,ci2,ci3 = st.columns(3)
with ci1:
    action_a = st.selectbox("Option A", list(options.keys()), index=1)
with ci2:
    action_b = st.selectbox("Option B", list(options.keys()), index=0)
with ci3:
    available_effort = st.slider("Available effort units",1,8,4)
comp_rows=[]
for action in dict.fromkeys([action_a,action_b]):
    d=options[action]
    comp_rows.append({"Intervention":action,"Illustrative effort units":d["effort"],"Urgency (1–3)":d["urgency"],"Fits effort budget": "Yes" if d["effort"]<=available_effort else "No","When to consider":d["evidence"]})
st.dataframe(pd.DataFrame(comp_rows),hide_index=True,use_container_width=True)

with st.expander("Data and method notes"):
    st.markdown("""
    - Priority scores use the existing weighted heuristic: severity burden 30%, incident frequency 25%, complaint volume 20%, road condition 15%, and local context 10%.
    - The resolution-time model uses complaint category, reported priority, and location characteristics. Complaint status is not used as a feature.
    - Only complaints marked `Resolved` or `Closed` with a valid duration are used as training targets.
    - Evaluation uses a held-out test split and compares Random Forest MAE with a training-set median baseline.
    """)

st.divider()
st.caption("This dashboard uses simulated data for demonstration purposes.")
