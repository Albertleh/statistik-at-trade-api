"""Streamlit dashboard that visualizes trade index analytics from the API."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# Configure the Streamlit page layout and title.
st.set_page_config(page_title="AT Trade Pulse Dashboard", layout="wide")

# Friendly labels for metric keys shown in the UI.
METRICS = {
    "uidxnom": "Nominal turnover index",
    "uidxreal": "Real turnover index",
    "beschidx": "Employment index",
}

# Human-readable descriptions for common NACE trade codes.
NACE_LABELS = {
    "G": "Wholesale & retail trade; repair of motor vehicles and motorcycles",
    "45": "Sale and repair of motor vehicles and motorcycles",
    "46": "Wholesale trade, except of motor vehicles and motorcycles",
    "47": "Retail trade, except of motor vehicles and motorcycles",
    "451": "Sale of motor vehicles",
    "452": "Maintenance and repair of motor vehicles",
    "453": "Sale of motor vehicle parts and accessories",
    "454": "Sale, maintenance and repair of motorcycles and related parts",
    "461": "Wholesale on a fee or contract basis",
    "462": "Wholesale of agricultural raw materials and live animals",
    "463": "Wholesale of food, beverages and tobacco",
    "464": "Wholesale of household goods",
    "465": "Wholesale of information and communication equipment",
    "466": "Wholesale of other machinery, equipment and supplies",
    "467": "Other specialized wholesale",
    "469": "Non-specialized wholesale trade",
    "471": "Retail sale in non-specialized stores",
    "472": "Retail sale of food, beverages and tobacco in specialized stores",
    "473": "Retail sale of automotive fuel in specialized stores",
    "474": "Retail sale of information and communication equipment in specialized stores",
    "475": "Retail sale of other household equipment in specialized stores",
    "476": "Retail sale of cultural and recreation goods in specialized stores",
    "477": "Retail sale of other goods in specialized stores",
    "478": "Retail sale via stalls and markets",
    "479": "Retail trade not in stores, stalls or markets",
}


def format_nace(code: str) -> str:
    """Format NACE codes with their sector description."""
    label = NACE_LABELS.get(code)
    if label:
        return f"{code} — {label}"
    return code


@st.cache_data(ttl=60)
def fetch_nace_list(base_url: str) -> list[str]:
    """Fetch available NACE codes from the API."""
    response = requests.get(f"{base_url}/nace", timeout=5)
    response.raise_for_status()
    data = response.json()
    return [str(item) for item in data]


@st.cache_data(ttl=60)
def fetch_series(
    base_url: str,
    nace: str,
    metric: str,
    start: str | None,
    end: str | None,
    limit: int = 5000,
) -> list[dict]:
    """Fetch time-series data for a NACE code + metric."""
    params = {"nace": nace, "metric": metric, "limit": limit}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    response = requests.get(f"{base_url}/series", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60)
def fetch_latest(base_url: str, nace: str, metric: str) -> dict:
    """Fetch the latest value and delta from the API."""
    response = requests.get(
        f"{base_url}/latest", params={"nace": nace, "metric": metric}, timeout=5
    )
    response.raise_for_status()
    return response.json()


def safe_json_to_df(payload: list[dict]) -> pd.DataFrame:
    """Normalize JSON payloads into a consistent DataFrame."""
    if not payload:
        return pd.DataFrame(columns=["period_date", "value"])
    df = pd.DataFrame(payload)
    if "period_date" not in df.columns:
        for candidate in ["date", "period", "latest_date", "latest_period"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "period_date"})
                break
    if "value" not in df.columns:
        for candidate in ["value", "latest_value", "index_value"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "value"})
                break
    df["period_date"] = pd.to_datetime(df["period_date"], errors="coerce")
    df = df.dropna(subset=["period_date"])
    df = df.sort_values("period_date")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def compute_changes(df: pd.DataFrame) -> pd.DataFrame:
    """Compute MoM and YoY percent changes for charting."""
    if df.empty:
        return df
    df = df.copy()
    df["mom_pct"] = df["value"].pct_change(1) * 100
    df["yoy_pct"] = df["value"].pct_change(12) * 100
    return df


# Page title shown at the top of the dashboard.
st.title("AT Trade Pulse Dashboard")

with st.sidebar:
    st.header("Controls")
    base_url = st.text_input("API base URL", value="http://localhost:8000")

    try:
        nace_list = fetch_nace_list(base_url)
    except requests.RequestException:
        st.error("API not reachable, start it first: ./scripts/run.sh")
        st.stop()

    if not nace_list:
        st.error("No NACE codes found. Run the API ingestion first: /ingest?mode=mock")
        st.stop()

    default_nace = "47" if "47" in nace_list else nace_list[0]
    nace_code = st.selectbox(
        "NACE code",
        options=nace_list,
        index=nace_list.index(default_nace),
        format_func=format_nace,
    )
    metric_key = st.selectbox("Metric", options=list(METRICS.keys()), format_func=METRICS.get)
    compare_sectors = st.toggle("Compare sectors (45/46/47/G)")

    nace_description = NACE_LABELS.get(nace_code, "No description available for this code.")
    st.caption(f"Selected sector: {nace_description}")

# Fetch the full series to determine date bounds and defaults.
try:
    raw_series = fetch_series(base_url, nace_code, metric_key, None, None)
except requests.RequestException:
    st.error("Failed to fetch series data. Ensure the API is running and ingested.")
    st.stop()

series_df = safe_json_to_df(raw_series)
if series_df.empty:
    st.warning("No data found. Run /ingest?mode=mock in the API.")
    st.stop()

min_date = series_df["period_date"].min().date()
max_date = series_df["period_date"].max().date()

with st.sidebar:
    default_start = max(min_date, (max_date - pd.DateOffset(months=36)).date())
    date_range = st.date_input(
        "Date range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
    )

if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered_df = series_df[
    (series_df["period_date"] >= pd.to_datetime(start_date))
    & (series_df["period_date"] <= pd.to_datetime(end_date))
]
filtered_df = compute_changes(filtered_df)

try:
    latest_payload = fetch_latest(base_url, nace_code, metric_key)
except requests.RequestException:
    latest_payload = {}

latest_value = latest_payload.get("latest_value") or latest_payload.get("value")
latest_delta = latest_payload.get("delta") or latest_payload.get("delta_value")
latest_delta_pct = latest_payload.get("delta_percent")

st.subheader("Latest snapshot")
col1, col2, col3 = st.columns(3)
col1.metric("Latest value", latest_value)
col2.metric("Delta", latest_delta)
col3.metric("Delta %", latest_delta_pct)

st.divider()

line_fig = px.line(
    filtered_df,
    x="period_date",
    y="value",
    title=f"{METRICS[metric_key]} (NACE {nace_code})",
)
line_fig.update_layout(yaxis_title="Index")

mom_df = filtered_df.dropna(subset=["mom_pct"]).tail(12)
mom_fig = px.bar(
    mom_df,
    x="period_date",
    y="mom_pct",
    title="Month-over-month % change (last 12 months)",
)

if filtered_df["yoy_pct"].notna().sum() >= 1 and len(filtered_df) >= 13:
    yoy_df = filtered_df.dropna(subset=["yoy_pct"]).tail(12)
    yoy_fig = px.bar(
        yoy_df,
        x="period_date",
        y="yoy_pct",
        title="Year-over-year % change (last 12 months)",
    )
else:
    yoy_fig = None

nominal_df = safe_json_to_df(fetch_series(base_url, nace_code, "uidxnom", None, None))
real_df = safe_json_to_df(fetch_series(base_url, nace_code, "uidxreal", None, None))
merge_df = pd.merge(
    nominal_df[["period_date", "value"]].rename(columns={"value": "uidxnom"}),
    real_df[["period_date", "value"]].rename(columns={"value": "uidxreal"}),
    on="period_date",
    how="inner",
)
merge_df = merge_df[(merge_df["period_date"] >= pd.to_datetime(start_date)) & (merge_df["period_date"] <= pd.to_datetime(end_date))]
merge_df["gap"] = merge_df["uidxnom"] - merge_df["uidxreal"]

nominal_fig = go.Figure()
nominal_fig.add_trace(go.Scatter(x=merge_df["period_date"], y=merge_df["uidxnom"], name="uidxnom"))
nominal_fig.add_trace(go.Scatter(x=merge_df["period_date"], y=merge_df["uidxreal"], name="uidxreal"))
nominal_fig.add_trace(go.Scatter(x=merge_df["period_date"], y=merge_df["gap"], name="gap"))
nominal_fig.update_layout(title="Nominal vs Real with gap", yaxis_title="Index")

heat_df = filtered_df.copy()
heat_df["year"] = heat_df["period_date"].dt.year
heat_df["month"] = heat_df["period_date"].dt.month
pivot = heat_df.pivot_table(index="year", columns="month", values="value", aggfunc="mean")
heatmap_fig = px.imshow(
    pivot,
    labels=dict(x="Month", y="Year", color="Index"),
    title="Seasonality heatmap",
)

comparison_fig = None
if compare_sectors:
    sector_codes = [code for code in ["45", "46", "47", "G"] if code in nace_list]
    comparison_frames = []
    for code in sector_codes:
        sector_series = safe_json_to_df(fetch_series(base_url, code, metric_key, None, None))
        sector_series = sector_series[
            (sector_series["period_date"] >= pd.to_datetime(start_date))
            & (sector_series["period_date"] <= pd.to_datetime(end_date))
        ]
        sector_series["nace"] = code
        comparison_frames.append(sector_series)
    if comparison_frames:
        comparison_df = pd.concat(comparison_frames, ignore_index=True)
        comparison_fig = px.line(
            comparison_df,
            x="period_date",
            y="value",
            color="nace",
            title="Sector comparison",
        )

left, right = st.columns(2)
with left:
    st.plotly_chart(line_fig, use_container_width=True)
    st.plotly_chart(mom_fig, use_container_width=True)
with right:
    if yoy_fig is None:
        st.warning("YoY chart requires at least 13 months of data.")
    else:
        st.plotly_chart(yoy_fig, use_container_width=True)
    st.plotly_chart(nominal_fig, use_container_width=True)

st.plotly_chart(heatmap_fig, use_container_width=True)

if comparison_fig is not None:
    st.plotly_chart(comparison_fig, use_container_width=True)

st.subheader("Data preview")
preview_df = filtered_df.tail(20).copy()
preview_df["period_date"] = preview_df["period_date"].dt.strftime("%Y-%m-%d")
st.dataframe(preview_df, use_container_width=True)

with st.expander("NACE code reference"):
    st.markdown(
        "The dataset uses NACE Rev.2 codes for trade sectors. "
        "Use the list below to interpret the most common codes."
    )
    nace_reference = [
        {"code": code, "sector": label} for code, label in sorted(NACE_LABELS.items())
    ]
    st.dataframe(pd.DataFrame(nace_reference), use_container_width=True, hide_index=True)
