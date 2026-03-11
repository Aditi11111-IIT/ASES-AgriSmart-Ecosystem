import streamlit as st
import pandas as pd
import random
import urllib.parse
import plotly.express as px
import requests

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Agri-Smart Ecosystem", layout="wide", page_icon="🌾")

# 🔑 OpenWeatherMap API Key
API_KEY = "886705b4c1182ebf6969f51d03f973f9"

# --- 2. SESSION STATE ---
if 'temp' not in st.session_state: st.session_state.temp = 25
if 'hum' not in st.session_state: st.session_state.hum = 50
if 'ledger' not in st.session_state: 
    st.session_state.ledger = pd.DataFrame([{"Item": "Seeds (बीज)", "Cost": 1200}])

# --- 3. CUSTOM STYLING ---
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
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA ENGINE (RENTAL) ---
@st.cache_data
def get_rental_data(district):
    data = []
    items = ["Mahindra Tractor (ट्रैक्टर)", "Harvester (हार्वेस्टर)", "Rotavator (रोटावेटर)", "Drone (ड्रोन)"]
    names = ["Sandeep Singh", "Rajesh Kumar", "Anjali Reddy", "Gurnam Patil", "Amit Verma"]
    for i in range(8):
        data.append({
            "Item": random.choice(items), "Owner": random.choice(names),
            "District": district, "Phone": f"+91{random.randint(7000000000, 9999999999)}",
            "Price": f"₹{random.randint(500, 3000)}/hr"
        })
    return pd.DataFrame(data)

# --- 5. SIDEBAR & LOCATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/5/52/Indian_Institute_of_Technology_Patna_Logo.png", width=120)
    st.title("ASES NAVIGATION")
    lang = st.radio("भाषा चुनें / Select Language", ["Hindi", "English"], horizontal=True)
    
    # Translation Dictionary
    t = {
        "menu": ["🏠 डैशबोर्ड", "🚜 रेंटल हब", "📚 ज्ञान केंद्र", "📈 मूल्य पूर्वानुमान", "📒 एग्री खाता"] if lang == "Hindi" else ["🏠 Dashboard", "🚜 Rental Hub", "📚 Knowledge Hub", "📈 Price Prediction", "📒 Agri Khata"],
        "state": "अपना राज्य चुनें" if lang == "Hindi" else "Select State",
        "dist": "अपना जिला चुनें" if lang == "Hindi" else "Select District",
        "update": "मौसम अपडेट करें" if lang == "Hindi" else "Update Weather",
        "call": "📞 कॉल करें" if lang == "Hindi" else "📞 Call Owner",
        "wa": "💬 व्हाट्सएप" if lang == "Hindi" else "💬 WhatsApp",
        "expense": "खर्च का विवरण" if lang == "Hindi" else "Expense Item",
        "cost": "लागत (₹)" if lang == "Hindi" else "Cost (₹)",
        "add": "एंट्री जोड़ें" if lang == "Hindi" else "Add Entry"
    }

    menu = st.radio("सेवा चुनें", t["menu"])
    st.markdown("---")
    
    india_map = {
        "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Meerut"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"]
    } # Adding truncated map for brevity, you can keep your full map here
    
    st_loc = st.selectbox(t["state"], list(india_map.keys()))
    dt_loc = st.selectbox(t["dist"], india_map[st_loc])
    
    if st.button(t["update"]):
        try:
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={dt_loc},IN&appid={API_KEY}&units=metric"
            res = requests.get(w_url).json()
            st.session_state.temp, st.session_state.hum = res['main']['temp'], res['main']['humidity']
            st.success("सफलतापूर्वक अपडेट किया गया!" if lang == "Hindi" else "Weather Synced!")
        except: st.error("API Error")

# --- 6. MODULES ---

if menu in ["🏠 डैशबोर्ड", "🏠 Dashboard"]:
    st.title(f"👨‍🌾 कमांड सेंटर: {dt_loc}")
    col1, col2, col3 = st.columns(3)
    col1.metric("तापमान (Temperature)", f"{st.session_state.temp}°C")
    col2.metric("नमी (Humidity)", f"{st.session_state.hum}%")
    col3.metric("मिट्टी की स्थिति", "बेहतर (Optimal)")
    st.info("💡 **सलाह:** वर्तमान मौसम रबी फसलों की बुवाई के लिए अनुकूल है।" if lang == "Hindi" else "💡 **Pro-Tip:** Current weather is ideal for Rabi sowing.")

elif menu in ["🚜 रेंटल हब", "🚜 Rental Hub"]:
    st.title("🚜 कृषि मशीनरी रेंटल")
    df = get_rental_data(dt_loc)
    for _, row in df.iterrows():
        with st.container():
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"### {row['Item']}\n👤 मालिक: {row['Owner']} | 💰 किराया: {row['Price']}\n📍 जिला: {row['District']}")
            c2.markdown(f'<a href="tel:{row["Phone"]}" class="call-btn">{t["call"]}</a>', unsafe_allow_html=True)
            wa_msg = urllib.parse.quote(f"नमस्ते {row['Owner']}, मुझे आपके {row['Item']} की आवश्यकता है।")
            c2.markdown(f'<a href="https://wa.me/{row["Phone"].replace("+","")}?text={wa_msg}" class="wa-btn">{t["wa"]}</a>', unsafe_allow_html=True)
            st.divider()

elif menu in ["📚 ज्ञान केंद्र", "📚 Knowledge Hub"]:
    st.title("📚 फसल जानकारी केंद्र")
    
    crops_en = [
        {"Crop": "Wheat", "Type": "Cereal", "Season": "Rabi", "Soil": "Loamy", "Water": "Moderate", "Pest": "Aphids", "Fertilizer": "NPK 120:60:40", "Pro-Tip": "Provide irrigation at CRI stage."},
        {"Crop": "Rice", "Type": "Cereal", "Season": "Kharif", "Soil": "Clayey", "Water": "High", "Pest": "Stem Borer", "Fertilizer": "NPK 100:60:40", "Pro-Tip": "Keep standing water during tillering."},
        {"Crop": "Mustard", "Type": "Oilseed", "Season": "Rabi", "Soil": "Sandy Loam", "Water": "Low", "Pest": "Aphids", "Fertilizer": "NPK + Sulphur", "Pro-Tip": "Sow before Oct 15 to avoid pests."},
        {"Crop": "Sugarcane", "Type": "Cash", "Season": "Annual", "Soil": "Alluvial", "Water": "High", "Pest": "Pyrilla", "Fertilizer": "Nitrogen High", "Pro-Tip": "Earthing up prevents lodging."}
    ]
    
    crops_hi = [
        {"फसल": "गेहूं", "प्रकार": "अनाज", "सीजन": "रबी", "मिट्टी": "दोमट", "पानी": "मध्यम", "कीट": "माहू", "उर्वरक": "NPK 120:60:40", "प्रो-टिप": "CRI अवस्था पर सिंचाई जरूर करें।"},
        {"फसल": "धान", "प्रकार": "अनाज", "सीजन": "खरीफ", "मिट्टी": "चिकनी", "पानी": "अधिक", "कीट": "तना छेदक", "उर्वरक": "NPK 100:60:40", "प्रो-टिप": "कल्ले फूटते समय खेत में पानी रखें।"},
        {"फसल": "सरसों", "प्रकार": "तिलहन", "सीजन": "रबी", "मिट्टी": "बलुई दोमट", "पानी": "कम", "कीट": "चेपा/माहू", "उर्वरक": "NPK + सल्फर", "प्रो-टिप": "कीटों से बचने के लिए 15 अक्टूबर से पहले बोएं।"},
        {"फसल": "गन्ना", "प्रकार": "नकदी", "सीजन": "वार्षिक", "मिट्टी": "जलोढ़", "पानी": "अधिक", "कीट": "पायरीला", "उर्वरक": "नाइट्रोजन अधिक", "प्रो-टिप": "मिट्टी चढ़ाने से फसल गिरती नहीं है।"}
    ]
    
    st.table(pd.DataFrame(crops_hi if lang == "Hindi" else crops_en))
    
    st.subheader("पोषक तत्वों की पहचान (Nutrient Identification)")
    

elif menu in ["📈 मूल्य पूर्वानुमान", "📈 Price Prediction"]:
    st.title("📈 बाजार भाव पूर्वानुमान (2026)")
    df_p = pd.DataFrame({"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "Price": [random.randint(2200, 2700) for _ in range(6)]})
    st.plotly_chart(px.line(df_p, x="Month", y="Price", title="अनुमानित मूल्य रुझान (Predicted Price Trend)"))

elif menu in ["📒 एग्री खाता", "📒 Agri Khata"]:
    st.title("📒 डिजिटल एग्री खाता")
    with st.form("ledger_form", clear_on_submit=True):
        item = st.text_input(t["expense"])
        cost = st.number_input(t["cost"], 0)
        if st.form_submit_button(t["add"]):
            new_row = pd.DataFrame([{"Item": item, "Cost": cost}])
            st.session_state.ledger = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
            st.rerun()
    st.plotly_chart(px.pie(st.session_state.ledger, values='Cost', names='Item', title="खर्चों का विश्लेषण (Expense Analysis)"))
