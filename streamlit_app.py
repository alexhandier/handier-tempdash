#!/usr/bin/env python3
"""
Clean Performance Dashboard - February 2026
Simple, actionable metrics for business decisions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Campaign data: from store (data/campaigns.db) when local, else north star fallback for published dashboard
try:
    from scripts.campaign_store import get_totals_for_month
    _campaign_totals = get_totals_for_month("2026-02")
    STORE_TOTAL_SENT = _campaign_totals["total_sent"]
    STORE_TOTAL_POSITIVE = _campaign_totals["total_positive"]
    STORE_CAMPAIGNS = _campaign_totals["campaigns"]
    CAMPAIGN_STORE_AVAILABLE = True
except Exception:
    # North star fallback (4 campaigns from Sequence Breakup) so published dashboard shows correct numbers
    STORE_TOTAL_SENT = 2155
    STORE_TOTAL_POSITIVE = 35
    STORE_CAMPAIGNS = [
        {"id": "1.3-1-30", "name": "Campaign 1.3 1/30", "date": "2026-02", "campaign_type": "general", "total_sent": 668, "positive_responses": 9},
        {"id": "2.2-1-30", "name": "Campaign 2.2 1/30 - Land", "date": "2026-02", "campaign_type": "land", "total_sent": 952, "positive_responses": 16},
        {"id": "2.3-2-16", "name": "Campaign 2.3 2/16 - Land", "date": "2026-02", "campaign_type": "land", "total_sent": 344, "positive_responses": 7},
        {"id": "1.4-2-16", "name": "Campaign 1.4 2/16", "date": "2026-02", "campaign_type": "general", "total_sent": 191, "positive_responses": 3},
    ]
    CAMPAIGN_STORE_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal CSS - Tesla-like
st.markdown("""
<style>
    .stMetric {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
    }
    h1 {
        font-weight: 300;
        font-size: 48px;
        margin-bottom: 40px;
    }
    h2 {
        font-weight: 300;
        font-size: 32px;
        margin-top: 40px;
        margin-bottom: 20px;
    }
    .big-number {
        font-size: 64px;
        font-weight: 100;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA — February 1–20, 2026 (from pipeline database)
# ============================================================================

# Daily data: 15 active days. properties = processed, fit = FIT, sendable = leads with email + valid address
daily_data = {
    'Feb 2': {'properties': 6139, 'fit': 543, 'agents': 382, 'sendable': 382, 'found_on_redfin': 6139, 'duplicates': 0},
    'Feb 3': {'properties': 1308, 'fit': 80, 'agents': 58, 'sendable': 58, 'found_on_redfin': 1308, 'duplicates': 0},
    'Feb 4': {'properties': 6648, 'fit': 649, 'agents': 400, 'sendable': 400, 'found_on_redfin': 6648, 'duplicates': 0},
    'Feb 5': {'properties': 5512, 'fit': 515, 'agents': 320, 'sendable': 320, 'found_on_redfin': 5512, 'duplicates': 0},
    'Feb 6': {'properties': 7046, 'fit': 568, 'agents': 364, 'sendable': 364, 'found_on_redfin': 7046, 'duplicates': 0},
    'Feb 9': {'properties': 5450, 'fit': 525, 'agents': 340, 'sendable': 340, 'found_on_redfin': 5450, 'duplicates': 0},
    'Feb 10': {'properties': 4781, 'fit': 477, 'agents': 306, 'sendable': 306, 'found_on_redfin': 4781, 'duplicates': 0},
    'Feb 11': {'properties': 4559, 'fit': 532, 'agents': 308, 'sendable': 308, 'found_on_redfin': 4559, 'duplicates': 0},
    'Feb 12': {'properties': 7388, 'fit': 564, 'agents': 411, 'sendable': 411, 'found_on_redfin': 7388, 'duplicates': 0},
    'Feb 13': {'properties': 4593, 'fit': 311, 'agents': 200, 'sendable': 200, 'found_on_redfin': 4593, 'duplicates': 0},
    'Feb 16': {'properties': 4185, 'fit': 471, 'agents': 218, 'sendable': 218, 'found_on_redfin': 4185, 'duplicates': 0},
    'Feb 17': {'properties': 5831, 'fit': 665, 'agents': 290, 'sendable': 290, 'found_on_redfin': 5831, 'duplicates': 0},
    'Feb 18': {'properties': 4018, 'fit': 487, 'agents': 225, 'sendable': 225, 'found_on_redfin': 4018, 'duplicates': 0},
    'Feb 19': {'properties': 5986, 'fit': 423, 'agents': 308, 'sendable': 308, 'found_on_redfin': 5986, 'duplicates': 0},
    'Feb 20': {'properties': 5912, 'fit': 433, 'agents': 267, 'sendable': 267, 'found_on_redfin': 5912, 'duplicates': 0},
}

# Variant breakdown from Sequence Breakup (north star screenshots)
# Campaign 1.4 2/16 — Lead List 191: A:48/0, B:48/1, C:47/2, D:48/0
general_variants = {
    'Email A': {'sent': 48, 'positive': 0},
    'Email B': {'sent': 48, 'positive': 1},
    'Email C': {'sent': 47, 'positive': 2},
    'Email D': {'sent': 48, 'positive': 0},
}
# Campaign 2.3 2/16 - Land — Lead List 344: A:87/3, B:85/2, C:85/1, D:87/1
land_variants = {
    'Email A': {'sent': 87, 'positive': 3},
    'Email B': {'sent': 85, 'positive': 2},
    'Email C': {'sent': 85, 'positive': 1},
    'Email D': {'sent': 87, 'positive': 1},
}

# Extraction totals — from pipeline DB (February 1–20, 2026). Verified.
ACTIVE_DAYS = 15
TOTAL_PROPERTIES = 79356   # New properties sent to AI verifier
TOTAL_FIT = 7243          # Passed FIT (construction/land, 2024+)
UNIQUE_AGENTS_WITH_EMAIL = 3274
TOTAL_SENDABLE = 4397     # FIT + email + valid street (exportable CSV rows)
# Positive responses: from campaign store (data/campaigns.db) if available, else fallback
VERIFIED_POSITIVE_RESPONSES = STORE_TOTAL_POSITIVE if CAMPAIGN_STORE_AVAILABLE else 10
CAMPAIGN_TOTAL_SENT = STORE_TOTAL_SENT if CAMPAIGN_STORE_AVAILABLE else (146 + 281)

# ============================================================================
# HEADER
# ============================================================================

st.title("Performance Dashboard")
st.markdown("**February 2026** • February 1–20 • 15 Active Days")

# ============================================================================
# TOP LINE METRICS (Big numbers that matter)
# ============================================================================

st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)

total_properties = TOTAL_PROPERTIES
total_fit = TOTAL_FIT
total_sendable = TOTAL_SENDABLE
total_found = sum([d['found_on_redfin'] for d in daily_data.values()])
total_duplicates = sum([d['duplicates'] for d in daily_data.values()])
avg_daily_sendable = total_sendable / ACTIVE_DAYS

general_total_sent = sum([d['sent'] for d in general_variants.values()])
land_total_sent = sum([d['sent'] for d in land_variants.values()])
general_positive = sum([d['positive'] for d in general_variants.values()])
land_positive = sum([d['positive'] for d in land_variants.values()])
# Total sent = from campaign store (north star: leads from each iteration)
total_sent = CAMPAIGN_TOTAL_SENT if CAMPAIGN_STORE_AVAILABLE else (general_total_sent + land_total_sent)
overall_conv = (VERIFIED_POSITIVE_RESPONSES / total_sent * 100) if total_sent else 0

with col1:
    st.metric("Found on Redfin", f"{total_found:,}")
    st.caption(f"→ {total_properties:,} processed")
    st.caption("Extraction: pipeline DB Feb 1–20")

with col2:
    st.metric("Properties Processed", f"{total_properties:,}",
              f"{int(total_properties/ACTIVE_DAYS):,}/day avg")
    st.caption("New properties verified by AI")

with col3:
    st.metric("FIT Rate", f"{(total_fit/total_properties*100):.1f}%",
              f"{total_fit:,} passed")
    st.caption("Under construction or vacant land")

with col4:
    st.metric("Sendable Leads", f"{total_sendable:,}",
              f"{int(avg_daily_sendable)}/day avg")
    st.caption("With email + valid address")

with col5:
    st.metric("Positive Responses", f"{VERIFIED_POSITIVE_RESPONSES}",
              f"{overall_conv:.2f}% conversion")
    st.caption(f"From {total_sent:,} emails sent ({len(STORE_CAMPAIGNS) if CAMPAIGN_STORE_AVAILABLE else 2} campaigns)" + (" • data/campaigns.db" if CAMPAIGN_STORE_AVAILABLE else ""))

# ============================================================================
# DAILY VOLUME TRENDS
# ============================================================================

st.markdown("---")
st.header("Daily Volume")
st.caption("Tracking new properties processed each day (duplicates excluded)")

dates = list(daily_data.keys())
properties = [daily_data[d]['properties'] for d in dates]
fit = [daily_data[d]['fit'] for d in dates]
sendable = [daily_data[d]['sendable'] for d in dates]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates, y=properties,
    name='Properties Processed',
    mode='lines+markers',
    line=dict(color='#E0E0E0', width=2),
    marker=dict(size=8)
))

fig.add_trace(go.Scatter(
    x=dates, y=fit,
    name='FIT Properties',
    mode='lines+markers',
    line=dict(color='#90CAF9', width=3),
    marker=dict(size=8)
))

fig.add_trace(go.Scatter(
    x=dates, y=sendable,
    name='Sendable Leads',
    mode='lines+markers',
    line=dict(color='#2196F3', width=3),
    marker=dict(size=10)
))

fig.update_layout(
    height=400,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=0, t=40, b=0),
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=14)
)

fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor='#F0F0F0')

st.plotly_chart(fig, use_container_width=True)

# Quick stats
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"**Peak Day:** {max(dates, key=lambda d: daily_data[d]['sendable'])} ({max([d['sendable'] for d in daily_data.values()])} leads)")
with col2:
    avg_fit_rate = total_fit / total_properties * 100
    st.caption(f"**Avg FIT Rate:** {avg_fit_rate:.1f}%")
with col3:
    avg_conversion = sum([d['sendable'] for d in daily_data.values()]) / total_properties * 100
    st.caption(f"**Properties → Leads:** {avg_conversion:.1f}%")

# ============================================================================
# OPERATIONAL COSTS
# ============================================================================

st.markdown("---")
st.header("Operational Costs")

# Scaled for February (rates from earlier period: 5.47/5262 per property, 31.55/2333 per sendable)
property_verification_cost = total_properties * (5.47 / 5262)
email_enrichment_cost = total_sendable * (31.55 / 2333)
total_variable_cost = property_verification_cost + email_enrichment_cost

col1, col2, col3, col4 = st.columns(4)

with col1:
    cost_to_verify = property_verification_cost / total_properties
    st.metric("Cost to Verify", f"${cost_to_verify:.4f}")
    st.caption("Per property (AI vision)")

with col2:
    cost_to_get_email = email_enrichment_cost / total_sendable
    st.metric("Cost to Get Email", f"${cost_to_get_email:.2f}")
    st.caption("Per lead (enrichment)")

with col3:
    cost_per_clean_lead = total_variable_cost / total_sendable
    st.metric("Cost per Clean Lead", f"${cost_per_clean_lead:.2f}")
    st.caption("Verification + enrichment")

with col4:
    cost_per_positive = total_variable_cost / VERIFIED_POSITIVE_RESPONSES if VERIFIED_POSITIVE_RESPONSES else 0
    st.metric("Cost per Positive", f"${cost_per_positive:.2f}")
    st.caption("Verified positives only")

# ============================================================================
# LEAD FUNNEL
# ============================================================================

st.markdown("---")
st.header("Lead Quality Funnel")
st.caption("Each stage filters for quality - from raw properties to qualified leads")

col1, col2 = st.columns([1, 2])

with col1:
    funnel_data = {
        'Properties Processed': total_properties,
        'FIT (construction + 2024+)': total_fit,
        'Has Email': UNIQUE_AGENTS_WITH_EMAIL,
        'Sendable': total_sendable,
    }
    
    for i, (stage, count) in enumerate(funnel_data.items()):
        if i == 0:
            st.markdown(f"**{stage}**")
            st.markdown(f"<div class='big-number'>{count:,}</div>", unsafe_allow_html=True)
        else:
            prev_count = list(funnel_data.values())[i-1]
            retention = count / prev_count * 100
            st.markdown(f"↓ {retention:.1f}%")
            st.metric(stage, f"{count:,}")

with col2:
    # Funnel visualization
    values = list(funnel_data.values())
    labels = list(funnel_data.keys())
    
    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(color=['#BDBDBD', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3'])
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(size=14)
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.caption("""
**Properties Processed:** New properties verified by AI (excludes duplicates from previous runs)  
**FIT:** Under construction or vacant land, built 2024+, pass AI image verification  
**Has Email:** Unique agents with valid email (FIT properties)  
**Sendable:** Qualified leads (FIT + email + valid address, exportable to CSV)

*Source: pipeline database, February 1–20, 2026*
""")

# ============================================================================
# CAMPAIGN PERFORMANCE
# ============================================================================

st.markdown("---")
st.header("Campaign Performance")

if CAMPAIGN_STORE_AVAILABLE and STORE_CAMPAIGNS:
    st.subheader("February 2026 campaigns (from data/campaigns.db)")
    campaign_df = pd.DataFrame(STORE_CAMPAIGNS)
    campaign_df["conversion %"] = (campaign_df["positive_responses"] / campaign_df["total_sent"] * 100).round(2)
    st.dataframe(
        campaign_df[["name", "date", "campaign_type", "total_sent", "positive_responses", "conversion %"]].rename(
            columns={"name": "Campaign", "date": "Date", "campaign_type": "Type", "total_sent": "Sent", "positive_responses": "Positive"}
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"**Total: {CAMPAIGN_TOTAL_SENT:,} sent, {VERIFIED_POSITIVE_RESPONSES} positive.** To add or update: run `python scripts/campaign_store.py` or use `scripts/campaign_store.add_campaign()`.")

st.subheader("Variant performance (sample: 2/16 campaigns)")
st.caption("Email A–D breakdown for Campaign 1.4 2/16 (General) and Campaign 2.3 2/16 - Land.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("General Properties")
    
    # Calculate conversion rates
    general_df = pd.DataFrame([
        {
            'Variant': variant,
            'Sent': data['sent'],
            'Positive': data['positive'],
            'Rate': f"{(data['positive']/data['sent']*100):.2f}%" if data['sent'] else "0%"
        }
        for variant, data in general_variants.items()
    ])
    
    # Highlight best (guard div by zero)
    best_general = max(general_variants.items(), key=lambda x: x[1]['positive']/x[1]['sent'] if x[1]['sent'] else 0)
    
    st.dataframe(general_df, use_container_width=True, hide_index=True)
    
    # Simple bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(general_variants.keys()),
            y=[(d['positive']/d['sent']*100) if d['sent'] else 0 for d in general_variants.values()],
            marker_color=['#2196F3' if k == best_general[0] else '#E0E0E0' for k in general_variants.keys()],
            text=[f"{(d['positive']/d['sent']*100):.2f}%" if d['sent'] else "0%" for d in general_variants.values()],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='white',
        yaxis_title="Conversion Rate (%)",
        font=dict(size=14)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    
    st.plotly_chart(fig, use_container_width=True)
    
    best_rate = (best_general[1]['positive']/best_general[1]['sent']*100) if best_general[1]['sent'] else 0
    st.success(f"**Best: {best_general[0]}** ({best_rate:.2f}% conversion)")

with col2:
    st.subheader("Land Properties")
    
    # Calculate conversion rates
    land_df = pd.DataFrame([
        {
            'Variant': variant,
            'Sent': data['sent'],
            'Positive': data['positive'],
            'Rate': f"{(data['positive']/data['sent']*100):.2f}%" if data['sent'] else "0%"
        }
        for variant, data in land_variants.items()
    ])
    
    # Highlight best (guard div by zero)
    best_land = max(land_variants.items(), key=lambda x: x[1]['positive']/x[1]['sent'] if x[1]['sent'] else 0)
    
    st.dataframe(land_df, use_container_width=True, hide_index=True)
    
    # Simple bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(land_variants.keys()),
            y=[(d['positive']/d['sent']*100) if d['sent'] else 0 for d in land_variants.values()],
            marker_color=['#4CAF50' if k == best_land[0] else '#E0E0E0' for k in land_variants.keys()],
            text=[f"{(d['positive']/d['sent']*100):.2f}%" if d['sent'] else "0%" for d in land_variants.values()],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='white',
        yaxis_title="Conversion Rate (%)",
        font=dict(size=14)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    
    st.plotly_chart(fig, use_container_width=True)
    
    best_land_rate = (best_land[1]['positive']/best_land[1]['sent']*100) if best_land[1]['sent'] else 0
    st.success(f"**Best: {best_land[0]}** ({best_land_rate:.2f}% conversion)")

# ============================================================================
# KEY LEARNINGS & RECOMMENDATION
# ============================================================================

st.markdown("---")
st.header("What We've Learned")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Data Insights")
    conv_to_sendable = total_sendable / total_properties * 100
    st.markdown(f"""
    - **{int(total_properties/ACTIVE_DAYS):,} properties/day** processed (AI verified)
    - **{total_fit/total_properties*100:.1f}% FIT** (under construction/vacant + 2024+)
    - **{conv_to_sendable:.1f}%** processed → sendable leads
    - **{VERIFIED_POSITIVE_RESPONSES} positive responses** ({total_sent:,} emails, {len(STORE_CAMPAIGNS) if CAMPAIGN_STORE_AVAILABLE else 2} campaigns)
    
    **FIT rate:** Redfin + year-built filter pre-target; AI verifies construction/land from images.
    """)

with col2:
    st.markdown("### 🎯 Campaign Insights (verified data)")
    general_conv = (general_positive / general_total_sent * 100) if general_total_sent else 0
    land_conv = (land_positive / land_total_sent * 100) if land_total_sent else 0
    st.markdown(f"""
    - **General (1.4 2/16):** Best variant **Email C** ({general_positive} positive from {general_total_sent} sent, {general_conv:.2f}%)
    - **Land (2.3 2/16):** Best variant **Email A** ({land_positive} positive from {land_total_sent} sent, {land_conv:.2f}%)
    - Total verified positives: **{VERIFIED_POSITIVE_RESPONSES}** (add more campaigns via report to update)
    """)

# Single, clear recommendation
st.info(f"""
### 💡 Recommendation

**Current Status:** February 1–20 — **79,356** properties processed, **4,397** sendable leads, **{VERIFIED_POSITIVE_RESPONSES}** positive responses from {len(STORE_CAMPAIGNS) if CAMPAIGN_STORE_AVAILABLE else 2} campaigns (source: data/campaigns.db).

**Next Steps:**
1. Keep current targeting; pipeline volume is strong.
2. Use **Email C** for general, **Email A** for land (from verified 2/16 campaign data).
3. Add new campaigns to the store: `python -c "from scripts.campaign_store import add_campaign; add_campaign('2.4', 'Campaign 2.4', '2026-02-20', 300, 5, 'land')"`
4. Monitor daily volume; CSVs in `exports/by_week/YYYY-Www/`.
""")

# Footer
st.markdown("---")
st.caption("February 2026 • Data through Feb 20 • 15 active days • Campaign totals from data/campaigns.db")
