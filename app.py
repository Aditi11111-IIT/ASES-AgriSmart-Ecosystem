import streamlit as st
import pandas as pd
import random
import urllib.parse
from fpdf import FPDF
import plotly.express as px
import requests

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 API Key for Weather
API_KEY = "886705b4c1182ebf6969f51d03f973f9"

# --- 2. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'ledger' not in st.session_state: 
    st.session_state.ledger = pd.DataFrame([{"Item": "Initial Seed", "Cost": 1200}])

# --- 3. STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { border-radius: 8px; background-color: #2e7d32; color: white; }
    .call-btn {
        background-color: #1b5e20; color: white; padding: 10px;
        text-align: center; border-radius: 5px; text-decoration: none;
        display: block; font-weight: bold; margin-bottom: 5px;
    }
    .wa-btn {
        background-color: #25D366; color: white; padding: 10px;
        text-align: center; border-radius: 5px; text-decoration: none;
        display: block; font-weight: bold;
    }
    th { background-color: #2e7d32 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. RENTAL HUB DATA ---
@st.cache_data
def get_rental_data():
    data = []
    items = ["Mahindra Tractor", "John Deere Harvester", "Rotavator", "Power Tiller"]
    owners = ["Sandeep Singh", "Rajesh Kumar", "Anjali Reddy", "Gurnam Patil"]
    districts = ["Patna", "Ludhiana", "Lucknow", "Pune", "Ahmedabad"]
    for i in range(15):
        data.append({
            "Item": random.choice(items), "Owner": random.choice(owners),
            "District": random.choice(districts), "Phone": f"+91{random.randint(7000000000, 9999999999)}",
            "Price": f"₹{random.randint(500, 3000)}/hr"
        })
    return pd.DataFrame(data)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES v1.0")
    menu = st.radio("MENU", ["🏠 Dashboard", "🚜 Rental Hub", "📚 Knowledge Hub", "📈 Price Prediction", "📒 Agri Khata"])
    st.markdown("---")
    loc = st.selectbox("Your District", ["Patna", "Ludhiana", "Lucknow", "Pune", "Ahmedabad"])
    if st.button("Sync Live Weather"):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            st.session_state.temp = res['main']['temp']
            st.session_state.hum = res['main']['humidity']
            st.success("Weather Updated!")
        except: st.error("Check Internet/API Key")

# --- 6. MODULES ---

if menu == "🏠 Dashboard":
    st.title(f"👨‍🌾 Command Center: {loc}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temp", f"{st.session_state.temp}°C")
    c2.metric("Humidity", f"{st.session_state.hum}%")
    c3.metric("Soil Health", "Optimal")
    st.info("💡 Pro-Tip: Current weather is ideal for sowing mustard.")

elif menu == "🚜 Rental Hub":
    st.title("🚜 Rental & Call Feature")
    df = get_rental_data()
    search = st.text_input("Search Machinery")
    filtered = df[df['Item'].str.contains(search, case=False)]
    for _, row in filtered.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(row['Item'])
                st.write(f"👤 **Owner:** {row['Owner']} | 💰 **Rate:** {row['Price']}")
                st.caption(f"📍 Location: {row['District']}")
            with col2:
                st.markdown(f'<a href="tel:{row["Phone"]}" class="call-btn">📞 Call Owner</a>', unsafe_allow_html=True)
                wa_msg = urllib.parse.quote(f"Hello {row['Owner']}, I am interested in renting your {row['Item']}.")
                st.markdown(f'<a href="https://wa.me/{row["Phone"].replace("+","")}?text={wa_msg}" class="wa-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
            st.divider()

elif menu == "📚 Knowledge Hub":
    st.title("📚 Crop Intelligence Hub")
    lang = st.radio("Select Language / भाषा चुनें", ["English", "Hindi"], horizontal=True)
    
    # 10 Crop Dataset
    crops_en = [
        {"Crop": "Wheat", "Type": "Cereal", "Season": "Rabi", "Soil": "Loamy", "Water": "Moderate", "Pest": "Aphids", "Fertilizer": "NPK 120:60:40", "Pro Tip": "Provide 4-6 irrigations at critical stages."},
        {"Crop": "Rice", "Type": "Cereal", "Season": "Kharif", "Soil": "Clayey", "Water": "High", "Pest": "Stem Borer", "Fertilizer": "NPK 100:60:40", "Pro Tip": "Keep 5cm standing water during tillering."},
        {"Crop": "Mustard", "Type": "Oilseed", "Season": "Rabi", "Soil": "Sandy Loam", "Water": "Low", "Pest": "Aphids", "Fertilizer": "Sulphur + NPK", "Pro Tip": "Early sowing helps avoid aphid attacks."},
        {"Crop": "Cotton", "Type": "Fiber", "Season": "Kharif", "Soil": "Black Soil", "Water": "Moderate", "Pest": "Bollworm", "Fertilizer": "NPK 100:50:50", "Pro Tip": "Deep plowing destroys pest pupae."},
        {"Crop": "Sugarcane", "Type": "Cash Crop", "Season": "Annual", "Soil": "Alluvial", "Water": "Very High", "Pest": "Pyrilla", "Fertilizer": "Nitrogen High", "Pro Tip": "Earthing up prevents lodging."},
        {"Crop": "Maize", "Type": "Cereal", "Season": "Kharif/Rabi", "Soil": "Well-drained Loam", "Water": "Moderate", "Pest": "Fall Armyworm", "Fertilizer": "NPK 120:60:40", "Pro Tip": "Avoid waterlogging during flowering."},
        {"Crop": "Soybean", "Type": "Pulse/Oil", "Season": "Kharif", "Soil": "Fertile Loam", "Water": "Moderate", "Pest": "Girdle Beetle", "Fertilizer": "DAP + NPK", "Pro Tip": "Inoculate seeds with Rhizobium culture."},
        {"Crop": "Gram (Chana)", "Type": "Pulse", "Season": "Rabi", "Soil": "Heavy Soil", "Water": "Low", "Pest": "Pod Borer", "Fertilizer": "Low Nitrogen", "Pro Tip": "Nipping improves branching."},
        {"Crop": "Potato", "Type": "Vegetable", "Season": "Rabi", "Soil": "Sandy Loam", "Water": "Moderate", "Pest": "Late Blight", "Fertilizer": "Potash High", "Pro Tip": "Use certified disease-free tubers."},
        {"Crop": "Tomato", "Type": "Vegetable", "Season": "Year-round", "Soil": "Well-drained", "Water": "Moderate", "Pest": "Fruit Borer", "Fertilizer": "NPK + Micronutrients", "Pro Tip": "Mulching helps preserve soil moisture."}
    ]

    crops_hi = [
        {"फसल": "गेहूं", "प्रकार": "अनाज", "सीजन": "रबी", "मिट्टी": "दोमट", "पानी": "मध्यम", "कीट": "एफिड्स", "उर्वरक": "NPK 120:60:40", "प्रो टिप": "महत्वपूर्ण चरणों में 4-6 सिंचाई करें।"},
        {"फसल": "चावल", "प्रकार": "अनाज", "सीजन": "खरीफ", "मिट्टी": "चिकनी", "पानी": "अधिक", "कीट": "तना छेदक", "उर्वरक": "NPK 100:60:40", "प्रो टिप": "कल्ले फूटते समय 5 सेमी पानी रखें।"},
        {"फसल": "सरसों", "प्रकार": "तिलहन", "सीजन": "रबी", "मिट्टी": "बलुई दोमट", "पानी": "कम", "कीट": "माहू", "उर्वरक": "सल्फर + NPK", "प्रो टिप": "जल्दी बुवाई एफिड हमलों से बचाती है।"},
        {"फसल": "कपास", "प्रकार": "रेशा", "सीजन": "खरीफ", "मिट्टी": "काली मिट्टी", "पानी": "मध्यम", "कीट": "सुंडी", "उर्वरक": "NPK 100:50:50", "प्रो टिप": "गहरी जुताई कीट के प्यूपा को नष्ट करती है।"},
        {"फसल": "गन्ना", "प्रकार": "नकदी फसल", "सीजन": "वार्षिक", "मिट्टी": "जलोढ़", "पानी": "बहुत अधिक", "कीट": "पायरीला", "उर्वरक": "नाइट्रोजन अधिक", "प्रो टिप": "मिट्टी चढ़ाना गिरने से रोकता है।"}
    ] # Add other 5 crops similarly in Hindi

    data = crops_en if lang == "English" else crops_hi
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("Nutrient Guide / पोषक तत्व मार्गदर्शिका")
    

elif menu == "📈 Price Prediction":
    st.title("📈 Market Forecast")
    df_p = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Price": [random.randint(2000, 2500) for _ in range(6)]
    })
    st.plotly_chart(px.line(df_p, x="Month", y="Price", title="Wheat Price Trend 2026"))

elif menu == "📒 Agri Khata":
    st.title("📒 Financial Ledger")
    with st.form("ledger"):
        item = st.text_input("Item")
        cost = st.number_input("Cost", 0)
        if st.form_submit_button("Add Entry"):
            new = pd.DataFrame([{"Item": item, "Cost": cost}])
            st.session_state.ledger = pd.concat([st.session_state.ledger, new], ignore_index=True)
    st.plotly_chart(px.pie(st.session_state.ledger, values='Cost', names='Item'))
