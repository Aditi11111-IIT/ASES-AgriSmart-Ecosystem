import streamlit as st
import pandas as pd
import numpy as np
import requests
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SHARED DATA REPOSITORIES ---

# Machinery Data (Generating All India)
def get_machinery_data():
    regions = {"Punjab": "Ludhiana", "Bihar": "Patna", "Maharashtra": "Pune", "UP": "Lucknow", "Tamil Nadu": "Chennai", "Haryana": "Karnal"}
    machines = ["Tractor", "Harvester", "Rotavator", "Seed Drill"]
    data = []
    for state, city in regions.items():
        for _ in range(5):
            data.append([state, f"{random.choice(['Raj', 'Amit', 'Suman'])} Singh", random.choice(machines), city, f"+91{random.randint(7000000000, 9999999999)}"])
    return pd.DataFrame(data, columns=["State", "Owner", "Machine", "Location", "Phone"])

# Schemes Data
SCHEMES = [
    {"Name": "PM-Kisan", "Limit": "All", "Benefit": "₹6,000/year", "Link": "https://pmkisan.gov.in/"},
    {"Name": "KCC", "Limit": "Small", "Benefit": "Low-interest Credit", "Link": "https://pib.gov.in/"},
    {"Name": "PKVY", "Limit": "Organic", "Benefit": "₹50,000/Ha Subsidy", "Link": "https://dmsouthwest.delhi.gov.in/"}
]

# Knowledge Hub Data
df_seeds = pd.DataFrame({
    "Crop": ["Wheat", "Rice", "Maize"],
    "Variety": ["Kalyan Sona", "IR64", "HQPM-1"],
    "Yield (q/ha)": ["45", "55", "65"]
})

# --- 3. PDF GENERATOR ---
def create_pdf(title, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for i, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row.to_dict()}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN NAVIGATION ---

st.sidebar.title("🚜 Agri-Smart v1.0")
menu = st.sidebar.radio("Navigate Ecosystem", 
    ["Dashboard", "Machinery Rental", "Govt Schemes", "Knowledge Hub", "Agri Khata"])

# --- MODULE: DASHBOARD (Weather & Quick Stats) ---
if menu == "Dashboard":
    st.title("🌾 Farmer Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Temp", "32°C", "Sunny")
    col2.metric("Soil Moisture", "45%", "-2%")
    col3.metric("Market Price (Wheat)", "₹2,125/q", "+₹15")
    
    st.subheader("Seasonal Tasks")
    st.info("🕒 It is time for Urea top-dressing in Wheat crops. Ensure soil is moist.")

# --- MODULE: MACHINERY RENTAL ---
elif menu == "Machinery Rental":
    st.title("🚜 Smart Rental Hub")
    df_m = get_machinery_data()
    state = st.selectbox("Select State", df_m['State'].unique())
    machine = st.selectbox("Select Machine", df_m['Machine'].unique())
    
    filtered = df_m[(df_m['State'] == state) & (df_m['Machine'] == machine)]
    
    for _, row in filtered.iterrows():
        with st.container():
            c1, c2 = st.columns([2, 1])
            c1.write(f"**Owner:** {row['Owner']} | **Location:** {row['Location']}")
            
            # One-Tap Call
            c2.markdown(f'<a href="tel:{row["Phone"]}" style="text-decoration:none; display:block; background:#1b5e20; color:white; text-align:center; padding:5px; border-radius:5px;">📞 Call</a>', unsafe_allow_html=True)
            
            # WhatsApp
            msg = urllib.parse.quote(f"Hi {row['Owner']}, interested in renting your {row['Machine']}.")
            wa_link = f"https://wa.me/{row['Phone'].replace('+', '')}?text={msg}"
            c2.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none; display:block; background:#25D366; color:white; text-align:center; padding:5px; border-radius:5px; margin-top:5px;">💬 WhatsApp</a>', unsafe_allow_html=True)
            st.divider()

# --- MODULE: GOVT SCHEMES & SUBSIDY ---
elif menu == "Govt Schemes":
    st.title("🏛️ Govt. Support Center")
    land = st.number_input("Enter Land Size (Hectares)", 0.1, 50.0, 1.0)
    
    st.subheader("Eligible Schemes")
    for s in SCHEMES:
        with st.expander(f"✨ {s['Name']}"):
            st.write(f"**Benefit:** {s['Benefit']}")
            st.markdown(f"[Apply Here]({s['Link']})")
    
    st.divider()
    st.subheader("Subsidy Estimator")
    st.write(f"Potential Credit (KCC): **₹{land * 75000:,.0f}**")
    st.write(f"Direct Income Support: **₹6,000/year**")

# --- MODULE: KNOWLEDGE HUB ---
elif menu == "Knowledge Hub":
    st.title("📚 Knowledge Hub")
    tab1, tab2 = st.tabs(["Seed Varieties", "Fertilizer Charts"])
    
    with tab1:
        st.table(df_seeds)
        if st.button("Download Seed PDF"):
            pdf_bytes = create_pdf("Seed Varieties", df_seeds)
            st.download_button("Click to Download", pdf_bytes, "seeds.pdf")

    with tab2:
        df_fert = pd.DataFrame({"Crop": ["Wheat", "Rice"], "N": [120, 100], "P": [60, 60], "K": [40, 40]})
        st.bar_chart(df_fert.set_index("Crop"))
        if st.button("Download Fertilizer PDF"):
            pdf_bytes = create_pdf("Fertilizer Dosage", df_fert)
            st.download_button("Click to Download", pdf_bytes, "fertilizer.pdf")

# --- MODULE: AGRI KHATA ---
elif menu == "Agri Khata":
    st.title("📒 Agri Khata (Expense Tracker)")
    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame([{"Cat": "Seed", "Amt": 500}])
    
    with st.form("Add Expense"):
        cat = st.selectbox("Category", ["Seed", "Fuel", "Labour", "Water"])
        amt = st.number_input("Amount", 0)
        if st.form_submit_button("Log Expense"):
            st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([{"Cat": cat, "Amt": amt}])])
    
    fig = px.pie(st.session_state.expenses, values='Amt', names='Cat', title="Spending Distribution")
    st.plotly_chart(fig)
