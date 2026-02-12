import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

# 1. Page Setup
st.set_page_config(page_title="Fiscal Scenario Dashboard", layout="wide")
st.title("🏛️ Advanced Fiscal Scenario Dashboard")
st.markdown("### Simulation: Impact of Revenue Shortfall (2025-2027)")

# 2. Sidebar Management (Download & Upload)
st.sidebar.header("📂 Data Management")

# Check if the file exists on the server to provide a download button
try:
    with open("Master_Fiscal_Dataset.csv", "rb") as file:
        st.sidebar.download_button(
            label="📥 Download Template CSV",
            data=file,
            file_name="Master_Fiscal_Dataset.csv",
            mime="text/csv",
            help="Download the source file to edit and re-upload"
        )
except FileNotFoundError:
    st.sidebar.error("Master_Fiscal_Dataset.csv not found in repository.")

# File uploader to override the default data
uploaded_file = st.sidebar.file_uploader("Upload your 'Master_Fiscal_Dataset.csv' to override", type="csv")

# 3. Data Loading Logic
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    # Filter for year format YYYY-YY
    df = df[df['Year'].apply(lambda x: bool(re.match(r'^\d{4}-\d{2}$', str(x))))].copy()
    cols = df.columns.drop('Year')
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    
    # Calculate Base Metrics
    df['Nominal_GDP'] = (df['Gross_Fiscal_Deficit'] / df['GFD_Percent_GDP']) * 100
    df['Total_Revenue'] = df['Net_Tax_Revenue'] + df['Non_Tax_Revenue']
    return df

# Decide which file to use
if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("✅ Using your uploaded file!")
else:
    try:
        df = load_data("Master_Fiscal_Dataset.csv")
        st.info("💡 Using pre-loaded data from the repository.")
    except Exception as e:
        st.error(f"Error loading default file: {e}")
        st.stop()

# 4. Sidebar Controls for Scenario
st.sidebar.header("⚙️ Scenario Parameters")
shortfall_pct = st.sidebar.slider("Projected Revenue Shortfall (%)", 0, 15, 5)
gdp_growth = st.sidebar.slider("Adjust GDP Growth (%)", -5, 5, 0)

# 5. Projection Logic for 2026-27
latest = df.iloc[-1].copy()
proj_2027 = latest.copy()
proj_2027['Year'] = '2026-27'
growth_factor = 1.105 + (gdp_growth/100)

proj_2027['Nominal_GDP'] *= growth_factor
proj_2027['Total_Revenue'] *= growth_factor
proj_2027['Total_Expenditure'] *= 1.08 
proj_2027['Gross_Fiscal_Deficit'] = proj_2027['Total_Expenditure'] - proj_2027['Total_Revenue']
proj_2027['GFD_Percent_GDP'] = (proj_2027['Gross_Fiscal_Deficit'] / proj_2027['Nominal_GDP']) * 100

# 6. Apply the Shortfall Scenario
sim_df = pd.concat([df.tail(2), pd.DataFrame([proj_2027])]) 

sim_df['Sim_Rev'] = sim_df['Total_Revenue'] * (1 - shortfall_pct/100)
sim_df['Sim_Deficit'] = sim_df['Gross_Fiscal_Deficit'] + (sim_df['Total_Revenue'] - sim_df['Sim_Rev'])
sim_df['Sim_Deficit_Pct'] = (sim_df['Sim_Deficit'] / sim_df['Nominal_GDP']) * 100

# 7. Visualizations
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Fiscal Deficit: Baseline vs Scenario")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sim_df['Year'], y=sim_df['GFD_Percent_GDP'], 
                         name='Baseline Target', marker_color='#2ecc71'))
    fig.add_trace(go.Bar(x=sim_df['Year'], y=sim_df['Sim_Deficit_Pct'], 
                         name=f'Scenario ({shortfall_pct}% Shortfall)', marker_color='#e74c3c'))
    fig.update_layout(barmode='group', yaxis_title="% of GDP", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Key Figures")
    summary = sim_df[['Year', 'GFD_Percent_GDP', 'Sim_Deficit_Pct']].copy()
    summary.columns = ['Year', 'Baseline %', 'Scenario %']
    st.table(summary)
    
    impact = sim_df['Sim_Deficit_Pct'].iloc[-1] - sim_df['GFD_Percent_GDP'].iloc[-1]
    st.metric("Deficit Deviation (2027)", f"+{impact:.2f}%", delta_color="inverse")

st.subheader("📊 Detailed Data Table")
st.dataframe(sim_df)
