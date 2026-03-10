import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# CONFIGURATION
WEATHER_API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"

st.set_page_config(page_title="ASES - Kisan Sampark", layout="wide")

# Sidebar for Navigation (Pre-setting for teammates)
st.sidebar.title("🌾 ASES Ecosystem")
page = st.sidebar.radio("Navigation", ["Kisan Sampark (Rentals)", "Knowledge Hub", "Others (Pending)"])

if page == "Kisan Sampark (Rentals)":
    st.title("🚜 Kisan Sampark: Smart Rental Hub")
    user_city = st.text_input("Enter your nearest city:", "Patna")
    
    if user_city:
        # 1. Weather Logic
        w_url = f"http://api.openweathermap.org/data/2.5/weather?q={user_city}&appid={WEATHER_API_KEY}&units=metric"
        weather = requests.get(w_url).json()
        
        if weather.get("cod") == 200:
            st.info(f"Current Weather in {user_city}: {weather['main']['temp']}°C, {weather['weather'][0]['description']}")
            if "rain" in weather['weather'][0]['description'].lower():
                st.warning("⚠️ High chance of rain. Renting machinery for harvesting is not advised today.")

        # 2. Rental Logic
        df = pd.read_csv("machinery.csv")
        st.subheader("Available Rentals Near You")
        
        for index, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['Machinery']}** (Owner: {row['Owner']})")
                
                # Member 4 Special: Click-to-Call
                phone_link = f'<a href="tel:{row["Phone"]}"><button style="background-color:#4CAF50;color:white;border:none;padding:8px 15px;border-radius:5px;">📞 Call Owner</button></a>'
                col2.markdown(phone_link, unsafe_allow_html=True)
                st.divider()

elif page == "Knowledge Hub":
    st.title("📚 Knowledge Hub")
    st.write("✅ PM-Kisan Samman Nidhi - [Check Eligibility]")
    st.write("✅ Soil Health Card - [Download Guide]")

else:
    st.warning("This section is under development by other team members.")
