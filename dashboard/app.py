import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE SETUP & ADVANCED STYLING ---
st.set_page_config(page_title="Supply Chain Command Center", page_icon="🌐", layout="wide")

# Premium UI CSS (Hover effects, soft borders, hidden UI clutter)
st.markdown("""
<style>
    /* Premium Metric Cards with Hover Animation */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.15);
    }
    
    /* Clean up top padding to make it look like a real app */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Make Tabs look like modern buttons */
    button[data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    button[data-baseweb="tab"] div { 
        font-weight: 600; 
        font-size: 16px; 
        letter-spacing: 0.5px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Main Header Area
c1, c2 = st.columns([1, 4])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830305.png", width=80) # Placeholder logo
with c2:
    st.title("Global Supply Chain Command Center")
    st.markdown("Monitor delivery health, identify high-risk suppliers, and simulate global disruptions in real-time.")

st.divider()

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv('data/DataCoSupplyChainDataset.csv', encoding='iso-8859-1')
    df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'])
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df['Shipping_Gap'] = df['Days for shipping (real)'] - df['Days for shipment (scheduled)']
    return df

df = load_data()

# --- 3. PREMIUM SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### 🎛️ Navigation & Filters")
    with st.container(border=True):
        selected_region = st.selectbox("🌍 Target Region", sorted(df['Order Region'].unique()))
        risk_threshold = st.slider("⚠️ Risk Watchlist Threshold (%)", 0, 100, 50)
    
    st.markdown("### ⚡ Stress Test Engine")
    with st.container(border=True):
        st.caption("Simulate a sudden logistics delay in the selected region to view potential impact.")
        sim_delay = st.number_input("Days Delayed", min_value=0, max_value=30, value=0)

# --- 4. FILTER DATA & APPLY SIMULATION ---
filtered_df = df[df['Order Region'] == selected_region].copy()

if sim_delay > 0:
    filtered_df['Days for shipping (real)'] += sim_delay
    filtered_df['Shipping_Gap'] = filtered_df['Days for shipping (real)'] - filtered_df['Days for shipment (scheduled)']
    filtered_df['Late_delivery_risk'] = (filtered_df['Shipping_Gap'] > 0).astype(int)
    # Trigger a subtle pop-up notification
    st.toast(f"Simulation Active: {sim_delay} Day Delay applied to {selected_region}!", icon="⚠️")

# --- 5. EXECUTIVE KPI ROW ---
col1, col2, col3 = st.columns(3)

with col1:
    avg_delay = filtered_df['Shipping_Gap'].mean()
    global_avg = df['Shipping_Gap'].mean()
    st.metric("⏱️ Avg Shipping Delay", f"{avg_delay:.2f} Days", delta=f"{avg_delay - global_avg:.2f} vs Global Avg", delta_color="inverse")

with col2:
    late_rate = (filtered_df['Late_delivery_risk'] == 1).mean() * 100
    st.metric("🚨 Late Delivery Risk", f"{late_rate:.1f}%")

with col3:
    total_sales = filtered_df['Sales'].sum()
    st.metric("💰 Total Regional Sales", f"${total_sales:,.0f}")

st.write("") # Add a little breathing room

# --- 6. DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Performance Analytics", "🌍 Geographic Risk Map", "🏢 Supplier Watchlist"])

# Configuration to hide the distracting Plotly modebar
plotly_config = {'displayModeBar': False}

# TAB 1: PERFORMANCE
with tab1:
    st.write("") # Padding
    c1, c2 = st.columns(2, gap="large")
    
    with c1:
        st.markdown("#### Profit Margin vs. Delivery Delay")
        fig_scatter = px.scatter(
            filtered_df, x="Shipping_Gap", y="Order Profit Per Order", 
            color="Delivery Status", hover_name="Product Name",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        # UI Upgrade: Remove gridlines for a cleaner look
        fig_scatter.update_layout(xaxis_showgrid=False, yaxis_showgrid=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_scatter, use_container_width=True, theme="streamlit", config=plotly_config)
        
    with c2:
        st.markdown("#### Top Products by Sales Volume")
        top_prods = filtered_df.groupby('Product Name')['Sales'].sum().nlargest(8).reset_index()
        fig_bar = px.bar(
            top_prods, x='Sales', y='Product Name', orientation='h',
            color='Sales', color_continuous_scale="Teal"
        )
        # UI Upgrade: Remove gridlines and clean up margins
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_showgrid=False, yaxis_showgrid=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit", config=plotly_config)

    if sim_delay > 0:
        st.error(f"**Disaster Simulation Active:** The metrics and charts above reflect a sudden **{sim_delay}-day** logistics failure in {selected_region}.")

# TAB 2: GEOGRAPHIC MAP
with tab2:
    st.write("")
    st.markdown(f"#### Order Distribution & Risk Heatmap: {selected_region}")
    fig_map = px.scatter_geo(
        filtered_df, lat='Latitude', lon='Longitude',
        color='Late_delivery_risk', size='Sales', hover_name='Order City',
        color_continuous_scale='Reds', opacity=0.8
    )
    fig_map.update_geos(fitbounds="locations", showcountries=True, countrycolor="rgba(128,128,128,0.2)")
    fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_map, use_container_width=True, theme="streamlit", config=plotly_config)

# TAB 3: SUPPLIER WATCHLIST
with tab3:
    st.write("")
    st.markdown(f"#### ⚠️ Critical Watchlist: {selected_region}")
    st.caption(f"Displaying product categories with a failure rate exceeding your **{risk_threshold}%** threshold limit.")
    
    supplier_risk = filtered_df.groupby('Category Name').agg(
        Avg_Late_Risk=('Late_delivery_risk', 'mean'),
        Total_Profit=('Order Profit Per Order', 'sum'),
        Total_Orders=('Order Id', 'count')
    ).reset_index()
    
    supplier_risk['Avg_Late_Risk'] = (supplier_risk['Avg_Late_Risk'] * 100).round(1)
    high_risk = supplier_risk[supplier_risk['Avg_Late_Risk'] > risk_threshold]
    
    if not high_risk.empty:
        st.dataframe(
            high_risk.sort_values(by='Avg_Late_Risk', ascending=False),
            column_config={
                "Avg_Late_Risk": st.column_config.ProgressColumn("Failure Risk %", min_value=0, max_value=100, format="%f%%"),
                "Total_Profit": st.column_config.NumberColumn("Profit Exposure", format="$%d"),
                "Total_Orders": st.column_config.NumberColumn("Orders Impacted")
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.success(f"✅ Operations Nominal: No categories exceed the {risk_threshold}% risk threshold.")