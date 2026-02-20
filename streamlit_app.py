#!/usr/bin/env python3
"""
Performance Dashboard — February 2026
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from scripts.campaign_store import get_totals_for_month
    _campaign_totals = get_totals_for_month("2026-02")
    STORE_TOTAL_SENT = _campaign_totals["total_sent"]
    STORE_TOTAL_POSITIVE = _campaign_totals["total_positive"]
    STORE_CAMPAIGNS = _campaign_totals["campaigns"]
    CAMPAIGN_STORE_AVAILABLE = True
except Exception:
    STORE_TOTAL_SENT = 2155
    STORE_TOTAL_POSITIVE = 35
    STORE_CAMPAIGNS = [
        {"id": "1.3-1-30",  "name": "Campaign 1.3 1/30",        "date": "2026-02", "campaign_type": "general", "total_sent": 668,  "positive_responses": 9},
        {"id": "2.2-1-30",  "name": "Campaign 2.2 1/30 — Land", "date": "2026-02", "campaign_type": "land",    "total_sent": 952,  "positive_responses": 16},
        {"id": "2.3-2-16",  "name": "Campaign 2.3 2/16 — Land", "date": "2026-02", "campaign_type": "land",    "total_sent": 344,  "positive_responses": 7},
        {"id": "1.4-2-16",  "name": "Campaign 1.4 2/16",        "date": "2026-02", "campaign_type": "general", "total_sent": 191,  "positive_responses": 3},
    ]
    CAMPAIGN_STORE_AVAILABLE = False

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], main {
        background-color: #ffffff !important;
    }
    .stMetric {
        background: #f8f9fa !important;
        padding: 20px;
        border-radius: 8px;
    }
    h1 { font-weight: 300; font-size: 48px; margin-bottom: 40px; }
    h2 { font-weight: 300; font-size: 32px; margin-top: 40px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA
# ============================================================================

daily_data = {
    'Feb 2':  {'properties': 6139, 'sendable': 382,  'found_on_redfin': 6139},
    'Feb 3':  {'properties': 1308, 'sendable': 58,   'found_on_redfin': 1308},
    'Feb 4':  {'properties': 6648, 'sendable': 400,  'found_on_redfin': 6648},
    'Feb 5':  {'properties': 5512, 'sendable': 320,  'found_on_redfin': 5512},
    'Feb 6':  {'properties': 7046, 'sendable': 364,  'found_on_redfin': 7046},
    'Feb 9':  {'properties': 5450, 'sendable': 340,  'found_on_redfin': 5450},
    'Feb 10': {'properties': 4781, 'sendable': 306,  'found_on_redfin': 4781},
    'Feb 11': {'properties': 4559, 'sendable': 308,  'found_on_redfin': 4559},
    'Feb 12': {'properties': 7388, 'sendable': 411,  'found_on_redfin': 7388},
    'Feb 13': {'properties': 4593, 'sendable': 200,  'found_on_redfin': 4593},
    'Feb 16': {'properties': 4185, 'sendable': 218,  'found_on_redfin': 4185},
    'Feb 17': {'properties': 5831, 'sendable': 290,  'found_on_redfin': 5831},
    'Feb 18': {'properties': 4018, 'sendable': 225,  'found_on_redfin': 4018},
    'Feb 19': {'properties': 5986, 'sendable': 308,  'found_on_redfin': 5986},
    'Feb 20': {'properties': 5912, 'sendable': 267,  'found_on_redfin': 5912},
}

# All 4 campaigns — variant breakdown from Sequence Breakup screenshots
all_campaigns_variants = {
    "Campaign 1.3 1/30 (General)": {
        "type": "general",
        "variants": {
            "Email A": {"sent": 167, "positive": 1},
            "Email B": {"sent": 167, "positive": 3},
            "Email C": {"sent": 166, "positive": 3},
            "Email D": {"sent": 168, "positive": 2},
        },
    },
    "Campaign 2.2 1/30 — Land": {
        "type": "land",
        "variants": {
            "Email A": {"sent": 236, "positive": 5},
            "Email B": {"sent": 242, "positive": 4},
            "Email C": {"sent": 234, "positive": 4},
            "Email D": {"sent": 240, "positive": 3},
        },
    },
    "Campaign 1.4 2/16 (General)": {
        "type": "general",
        "variants": {
            "Email A": {"sent": 48, "positive": 0},
            "Email B": {"sent": 48, "positive": 1},
            "Email C": {"sent": 47, "positive": 2},
            "Email D": {"sent": 48, "positive": 0},
        },
    },
    "Campaign 2.3 2/16 — Land": {
        "type": "land",
        "variants": {
            "Email A": {"sent": 87, "positive": 3},
            "Email B": {"sent": 85, "positive": 2},
            "Email C": {"sent": 85, "positive": 1},
            "Email D": {"sent": 87, "positive": 1},
        },
    },
}

ACTIVE_DAYS = 15
TOTAL_PROPERTIES = 79356
TOTAL_SENDABLE = 4397
VERIFIED_POSITIVE_RESPONSES = STORE_TOTAL_POSITIVE if CAMPAIGN_STORE_AVAILABLE else 35
CAMPAIGN_TOTAL_SENT = STORE_TOTAL_SENT if CAMPAIGN_STORE_AVAILABLE else 2155

# ============================================================================
# HELPERS — Bayesian A/B
# ============================================================================

VARIANT_COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]

def bayesian_chart(variants: dict, title: str) -> go.Figure:
    """Overlay Beta posteriors for each variant."""
    # find the max conversion rate across variants to set a sensible x range
    max_rate = max(
        (d["positive"] / d["sent"]) if d["sent"] else 0
        for d in variants.values()
    )
    x_max = max(max_rate * 4, 0.08)  # at least 8% range
    x = np.linspace(0, x_max, 1000)

    fig = go.Figure()
    for i, (name, d) in enumerate(variants.items()):
        a = 1 + d["positive"]
        b = 1 + d["sent"] - d["positive"]
        y = stats.beta.pdf(x, a, b)
        color = VARIANT_COLORS[i % len(VARIANT_COLORS)]
        fig.add_trace(go.Scatter(
            x=x * 100,
            y=y,
            name=name,
            mode="lines",
            fill="tozeroy",
            fillcolor=color.replace("#", "rgba(").replace(")", ",0.12)") if False else f"rgba{tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + (0.12,)}",
            line=dict(color=color, width=2),
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#262730")),
        xaxis_title="Conversion Rate (%)",
        yaxis_title="Probability Density",
        height=280,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#262730"),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0")
    return fig


def prob_best(variants: dict, n_samples: int = 100_000) -> dict:
    """Monte Carlo P(variant is best) for each variant."""
    names = list(variants.keys())
    samples = np.stack([
        np.random.beta(1 + d["positive"], 1 + d["sent"] - d["positive"], n_samples)
        for d in variants.values()
    ])  # shape: (n_variants, n_samples)
    best = np.argmax(samples, axis=0)
    return {names[i]: float(np.mean(best == i) * 100) for i in range(len(names))}


# ============================================================================
# HEADER
# ============================================================================

st.title("Performance Dashboard")
st.markdown("**February 2026** · Feb 1–20 · 15 Active Days")
st.markdown("---")

# ============================================================================
# TOP LINE METRICS
# ============================================================================

total_properties = TOTAL_PROPERTIES
total_sendable = TOTAL_SENDABLE
total_sent = CAMPAIGN_TOTAL_SENT
overall_conv = (VERIFIED_POSITIVE_RESPONSES / total_sent * 100) if total_sent else 0
avg_daily_sendable = total_sendable / ACTIVE_DAYS

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Properties Verified", f"{total_properties:,}",
              f"{int(total_properties / ACTIVE_DAYS):,}/day avg")
    st.caption("Scraped from Redfin · AI-verified (no duplicates)")

with col2:
    st.metric(
        "Raw Leads", f"{total_sendable:,}",
        f"{int(avg_daily_sendable)}/day avg",
        help=(
            "Property–agent pairs that passed FIT, have a valid email, and a valid street address. "
            "4,397 rows → ~3,226 unique emails after dedup. "
            "Delivered is lower: VA removes invalid emails and may use only part of the list per campaign."
        ),
    )
    st.caption("FIT · valid email · valid address")

with col3:
    st.metric("Delivered", f"{total_sent:,}")
    n_campaigns = len(STORE_CAMPAIGNS) if CAMPAIGN_STORE_AVAILABLE else 4
    st.caption(f"Emails sent across {n_campaigns} campaigns")

with col4:
    st.metric("Positive Responses", f"{VERIFIED_POSITIVE_RESPONSES}",
              f"{overall_conv:.2f}% of delivered")
    st.caption("Positive replies across all campaigns")

# ============================================================================
# DAILY VOLUME — dual y-axis so both lines are legible
# ============================================================================

st.markdown("---")
st.header("Daily Volume")

dates = list(daily_data.keys())
properties_by_day = [daily_data[d]["properties"] for d in dates]
leads_by_day = [daily_data[d]["sendable"] for d in dates]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=dates, y=properties_by_day,
    name="Properties Verified",
    marker_color="#E3F2FD",
    yaxis="y1",
    opacity=0.8,
))

fig.add_trace(go.Scatter(
    x=dates, y=leads_by_day,
    name="Raw Leads",
    mode="lines+markers",
    line=dict(color="#2196F3", width=3),
    marker=dict(size=8),
    yaxis="y2",
))

fig.update_layout(
    height=380,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(size=13, color="#262730"),
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis=dict(
        title="Properties Verified",
        showgrid=True,
        gridcolor="#F0F0F0",
        title_font=dict(color="#BDBDBD"),
        tickfont=dict(color="#BDBDBD"),
    ),
    yaxis2=dict(
        title="Raw Leads",
        overlaying="y",
        side="right",
        showgrid=False,
        title_font=dict(color="#2196F3"),
        tickfont=dict(color="#2196F3"),
    ),
)
fig.update_xaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    peak = max(dates, key=lambda d: daily_data[d]["sendable"])
    st.caption(f"**Peak Day:** {peak} — {daily_data[peak]['sendable']} raw leads")
with col_b:
    pct = sum(leads_by_day) / total_properties * 100
    st.caption(f"**Properties → Raw Leads:** {pct:.1f}%")

# ============================================================================
# OPERATIONAL COSTS
# ============================================================================

st.markdown("---")
st.header("Operational Costs")

property_verification_cost = total_properties * (5.47 / 5262)
email_enrichment_cost = total_sendable * (31.55 / 2333)
total_variable_cost = property_verification_cost + email_enrichment_cost

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Cost to Verify", f"${property_verification_cost / total_properties:.4f}")
    st.caption("Per property · AI vision")
with col2:
    st.metric("Cost to Get Email", f"${email_enrichment_cost / total_sendable:.2f}")
    st.caption("Per lead · enrichment")
with col3:
    st.metric("Cost per Raw Lead", f"${total_variable_cost / total_sendable:.2f}")
    st.caption("Verification + enrichment")
with col4:
    cpp = total_variable_cost / VERIFIED_POSITIVE_RESPONSES if VERIFIED_POSITIVE_RESPONSES else 0
    st.metric("Cost per Positive", f"${cpp:.2f}")
    st.caption("All variable costs / positives")

# ============================================================================
# CAMPAIGN SUMMARY TABLE
# ============================================================================

st.markdown("---")
st.header("Campaign Performance")

if CAMPAIGN_STORE_AVAILABLE and STORE_CAMPAIGNS:
    campaign_df = pd.DataFrame(STORE_CAMPAIGNS)
else:
    campaign_df = pd.DataFrame([
        {"name": c, "campaign_type": v["type"],
         "total_sent": sum(x["sent"] for x in v["variants"].values()),
         "positive_responses": sum(x["positive"] for x in v["variants"].values())}
        for c, v in all_campaigns_variants.items()
    ])

campaign_df["Conversion %"] = (
    campaign_df["positive_responses"] / campaign_df["total_sent"] * 100
).round(2)

st.dataframe(
    campaign_df[["name", "campaign_type", "total_sent", "positive_responses", "Conversion %"]].rename(
        columns={"name": "Campaign", "campaign_type": "Type",
                 "total_sent": "Sent", "positive_responses": "Positive"}
    ),
    use_container_width=True,
    hide_index=True,
)
st.caption(f"**Total: {total_sent:,} sent · {VERIFIED_POSITIVE_RESPONSES} positive · {overall_conv:.2f}% conversion**")

# ============================================================================
# BAYESIAN A/B — all 4 campaigns, all variants
# ============================================================================

st.markdown("---")
st.header("Email Variant Analysis — Bayesian")
st.caption(
    "Posterior Beta distributions (Beta(1+positives, 1+failures) prior). "
    "The wider/flatter the curve, the less data we have for that variant. "
    "**P(best)** = probability this variant has the highest true conversion rate."
)

campaign_names = list(all_campaigns_variants.keys())

# Row 1
col1, col2 = st.columns(2)
for col, cname in zip([col1, col2], campaign_names[:2]):
    campaign = all_campaigns_variants[cname]
    variants = campaign["variants"]
    probs = prob_best(variants)

    with col:
        st.subheader(cname)

        # Summary table with P(best)
        rows = []
        for vname, d in variants.items():
            rate = d["positive"] / d["sent"] * 100 if d["sent"] else 0
            rows.append({
                "Variant": vname,
                "Sent": d["sent"],
                "Positive": d["positive"],
                "Rate": f"{rate:.2f}%",
                "P(best)": f"{probs[vname]:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Bayesian chart
        st.plotly_chart(bayesian_chart(variants, cname), use_container_width=True)

# Row 2
col3, col4 = st.columns(2)
for col, cname in zip([col3, col4], campaign_names[2:]):
    campaign = all_campaigns_variants[cname]
    variants = campaign["variants"]
    probs = prob_best(variants)

    with col:
        st.subheader(cname)

        rows = []
        for vname, d in variants.items():
            rate = d["positive"] / d["sent"] * 100 if d["sent"] else 0
            rows.append({
                "Variant": vname,
                "Sent": d["sent"],
                "Positive": d["positive"],
                "Rate": f"{rate:.2f}%",
                "P(best)": f"{probs[vname]:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.plotly_chart(bayesian_chart(variants, cname), use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("February 2026 · Data through Feb 20 · 15 active days · Source: pipeline DB + Sequence Breakup screenshots")
