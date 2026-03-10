import streamlit as st
import pandas as pd
import requests
import json
from fpdf import FPDF
from streamlit_folium import st_folium
import folium
from streamlit_js_eval import get_geolocation

# --- CONFIGURATION ---
WEATHER_API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

# --- 1. DATA LOADERS ---
def load_schemes():
    # Load your provided schemes_db.json
    try:
        with open('schemes_db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_machinery_data():
    # Mock database of machinery owners across India
    return pd.DataFrame([
        {"Machine": "Mahindra Tractor", "Owner": "Rajesh Kumar", "Phone": "9876543210", "Lat": 25.5941, "Lon": 85.1376, "City": "Patna"},
        {"Machine": "John Deere Harvester", "Owner": "Suresh Singh", "Phone": "8877665544", "Lat": 30.9010, "Lon": 75.8573, "City": "Ludhiana"},
        {"Machine": "Power Tiller", "Owner": "Amit Mahto", "Phone": "9900887766", "Lat": 23.3441, "Lon": 85.3096, "City": "Ranchi"},
    ])

# --- 2. PDF GENERATOR ---
def generate_pdf(name, crop, state, selected_schemes, db):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ASES: Personalized Farmer Advisory", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Farmer Name: {name} | Crop: {crop}", ln=True)
    pdf.cell(0, 10, f"Region: {state}", ln=True)
    pdf.ln(5)
    pdf.line(10, 45, 200, 45)
    pdf.ln(10)
    for s in selected_schemes:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"- {db[s]['name']}", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, f"Benefit: {db[s]['desc']}\nLink: {db[s].get('link', 'N/A')}\n")
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP INTERFACE ---
st.set_page_config(page_title="ASES Group 32", layout="wide")
st.sidebar.title("🌿 ASES Ecosystem")
page = st.sidebar.selectbox("Navigation", ["🚜 Rental Hub (Live Location)", "📚 Knowledge Hub (All India)"])

# --- MODULE E: RENTAL HUB (WITH WEATHER & MAP) ---
if page == "🚜 Rental Hub (Live Location)":
    st.header("🚜 Kisan Sampark: Live Rental Hub")
    
    # Live Location Detection
    loc = get_geolocation()
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        
        # Weather Integration
        w_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        weather = requests.get(w_url).json()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📍 Your Location")
            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], popup="Your Farm", icon=folium.Icon(color='green')).add_to(m)
            st_folium(m, width=500, height=300)
        
        with col2:
            st.subheader("☁️ Weather Advisory")
            if weather.get("cod") == 200:
                temp = weather['main']['temp']
                desc = weather['weather'][0]['description']
                st.metric("Temperature", f"{temp}°C")
                st.info(f"Condition: {desc.capitalize()}")
                if "rain" in desc.lower():
                    st.warning("⚠️ Rain detected. Postpone heavy machine rentals to prevent soil compaction.")
            else:
                st.error("Weather data unavailable.")

    # Machinery List
    st.divider()
    df_rent = get_machinery_data()
    st.subheader("🛠️ Nearby Machinery Owners")
    for i, row in df_rent.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{row['Machine']}**")
            c2.write(f"📍 {row['City']} | Owner: {row['Owner']}")
            call_html = f'<a href="tel:{row["Phone"]}"><button style="background-color:#28a745;color:white;border:none;padding:10px;border-radius:5px;width:100%;">📞 Call</button></a>'
            c3.markdown(call_html, unsafe_allow_html=True)

# --- MODULE F: KNOWLEDGE HUB (TABULAR) ---
elif page == "📚 Knowledge Hub (All India)":
    st.header("📚 Knowledge Hub: Personalized Advisory")
    
    db = load_schemes()
    states = sorted(list(db.keys()))
    
    col_in, col_view = st.columns([1, 2])
    
    with col_in:
        u_name = st.text_input("Farmer Name", "Aditi Dwivedi")
        u_crop = st.text_input("Target Crop", "Wheat")
        u_state = st.selectbox("Select State/UT", states)
        u_selections = st.multiselect("Select Schemes to include in PDF", states)

    with col_view:
        st.subheader(f"📋 Scheme Details for {u_state}")
        # Table View
        current_data = db.get(u_state, {})
        df_display = pd.DataFrame([current_data])
        st.table(df_display[['name', 'desc']])
        st.link_button("🌐 Official Portal", current_data.get('link', '#'), use_container_width=True)
        
        st.divider()
        if u_selections:
            st.write(f"### Generate PDF for {u_name}")
            pdf_bytes = generate_pdf(u_name, u_crop, u_state, u_selections, db)
            st.download_button("📥 Download Personalized Guide", pdf_bytes, f"{u_name}_Report.pdf", use_container_width=True)
