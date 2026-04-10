import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Retail Inventory Dashboard",
    layout="wide",
    page_icon="🛒"
)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    return pd.read_csv(path)

# ── Load all outputs ─────────────────────────────────────────────
cat_df    = load("category_summary.csv")
top_df    = load("top_products.csv")
region_df = load("region_sales.csv")
low_df    = load("low_stock.csv")

# ── Fix column names (strip spaces) ─────────────────────────────
cat_df.columns    = cat_df.columns.str.strip()
top_df.columns    = top_df.columns.str.strip()
region_df.columns = region_df.columns.str.strip()
low_df.columns    = low_df.columns.str.strip()

# ════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════
st.title("🛒 Retail Inventory Dashboard")
st.caption("Powered by Apache Hadoop + PySpark · Data loaded from HDFS outputs")
st.divider()

# ════════════════════════════════════════════════════════════════
#  KPI CARDS
# ════════════════════════════════════════════════════════════════
total_rev   = cat_df["Total Revenue"].sum()
total_units = cat_df["Total Units"].sum()
low_count   = len(low_df)
avg_price   = cat_df["Avg Price"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Total Revenue",    f"${total_rev/1e6:.1f}M")
k2.metric("📦 Total Units Sold", f"{total_units/1e6:.1f}M")
k3.metric("⚠️ Low Stock Items",  f"{low_count:,}")
k4.metric("🏷️ Avg Product Price", f"${avg_price:.2f}")

st.divider()

# ════════════════════════════════════════════════════════════════
#  ROW 1: Category Revenue + Top Products
# ════════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Revenue by Category")
    fig1 = px.pie(
        cat_df,
        values="Total Revenue",
        names="Category",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig1.update_traces(textposition="outside", textinfo="percent+label")
    fig1.update_layout(showlegend=True, height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🏆 Top Selling Products")
    top10 = top_df.sort_values("Total Units Sold", ascending=False).head(10)
    fig2 = px.bar(
        top10,
        x="Total Units Sold",
        y="Product ID",
        orientation="h",
        color="Category" if "Category" in top10.columns else "Total Units Sold",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        text="Total Units Sold"
    )
    fig2.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig2.update_layout(height=380, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════════════════
#  ROW 2: Region Sales + Category Units
# ════════════════════════════════════════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.subheader("🌍 Region-wise Sales")
    fig3 = px.bar(
        region_df.sort_values("Total Revenue", ascending=False),
        x="Region",
        y="Total Revenue",
        color="Region",
        text="Total Revenue",
        color_discrete_sequence=["#185FA5","#0F6E56","#BA7517","#993556"]
    )
    fig3.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside"
    )
    fig3.update_layout(height=360, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("📦 Units Sold by Category")
    fig4 = px.bar(
        cat_df.sort_values("Total Units", ascending=True),
        x="Total Units",
        y="Category",
        orientation="h",
        color="Category",
        text="Total Units",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig4.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig4.update_layout(height=360, showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════════════════════════
#  ROW 3: Avg Inventory by Region + Revenue vs Units scatter
# ════════════════════════════════════════════════════════════════
col5, col6 = st.columns(2)

with col5:
    st.subheader("🏪 Avg Inventory Level by Region")
    fig5 = px.bar(
        region_df,
        x="Region",
        y="Avg Inventory",
        color="Region",
        text="Avg Inventory",
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig5.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig5.update_layout(height=340, showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("💡 Revenue vs Units Sold (Category)")
    fig6 = px.scatter(
        cat_df,
        x="Total Units",
        y="Total Revenue",
        size="Avg Price",
        color="Category",
        text="Category",
        size_max=50,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig6.update_traces(textposition="top center")
    fig6.update_layout(height=340)
    st.plotly_chart(fig6, use_container_width=True)

# ════════════════════════════════════════════════════════════════
#  LOW STOCK ALERTS TABLE
# ════════════════════════════════════════════════════════════════
st.divider()
st.subheader("⚠️ Low Stock Alerts")

col_f1, col_f2 = st.columns(2)
with col_f1:
    if "Category" in low_df.columns:
        cats = ["All"] + sorted(low_df["Category"].unique().tolist())
        cat_filter = st.selectbox("Filter by Category", cats)
with col_f2:
    if "Region" in low_df.columns:
        regions = ["All"] + sorted(low_df["Region"].unique().tolist())
        reg_filter = st.selectbox("Filter by Region", regions)

filtered = low_df.copy()
if cat_filter != "All" and "Category" in filtered.columns:
    filtered = filtered[filtered["Category"] == cat_filter]
if reg_filter != "All" and "Region" in filtered.columns:
    filtered = filtered[filtered["Region"] == reg_filter]

st.dataframe(
    filtered.sort_values("Inventory Level").reset_index(drop=True),
    use_container_width=True,
    height=300
)

st.caption(f"Showing {len(filtered):,} low stock records (Inventory Level < 100)")

# ════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════
st.divider()
st.caption("🛒 Retail Inventory Management System · Big Data Pipeline · Hadoop + Spark + Streamlit")
