import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

# --- 🛠️ Theme Selector (ย้ายไปไว้ข้างๆ แบบไม่เกะกะ) ---
with st.sidebar:
    st.markdown("### ⚙️ SETTINGS")
    theme_mode = st.selectbox("Appearance", ["Light", "Dark"], index=0)
    st.info("โหมดสีจะปรับตามที่คุณเลือกที่นี่")

# กำหนดค่าสีตามโหมดที่เลือก
if theme_mode == "Dark":
    bg_color, text_color, header_color = "#0e1117", "#e0e0e0", "#ffffff"
    border_color, timeline_dot, card_border = "#333333", "#555555", "#444444"
    input_bg = "#1e1e1e"
else:
    bg_color, text_color, header_color = "#ffffff", "#444444", "#222222"
    border_color, timeline_dot, card_border = "#eeeeee", "#bbbbbb", "#dddddd"
    input_bg = "#ffffff"

# --- Inject CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    .stApp {{ background-color: {bg_color}; }}
    
    html, body, [class*="css"], .stMarkdown, p, div {{ 
        font-family: 'Anuphan', sans-serif !important; 
        font-weight: 300 !important;
        color: {text_color} !important;
    }}

    /* ซ่อน UI ที่ทำให้ดูรก */
    svg[data-testid="stExpanderIcon"] {{ display: none !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .stButton>button {{ 
        border-radius: 12px; border: 0.5px solid {border_color}; 
        background-color: {input_bg}; color: {text_color};
    }}

    /* Timeline Styles */
    .day-header {{
        font-size: 16px; font-weight: 400; color: {header_color};
        margin: 30px 0 15px 0; border-bottom: 1px solid {border_color};
        padding-bottom: 5px; letter-spacing: 1px;
    }}
    .plan-card {{
        border-left: 1px solid {card_border};
        padding: 0 0 25px 20px; margin-left: 5px; position: relative;
    }}
    .plan-card::before {{
        content: ''; position: absolute; left: -4px; top: 4px;
        width: 7px; height: 7px; background-color: {timeline_dot}; border-radius: 50%;
    }}
    .time-text {{ font-size: 11px; color: #888; }}
    .location-text {{ font-size: 14px; color: {text_color}; line-height: 1.5; }}
    </style>
""", unsafe_allow_html=True)

# --- ชื่อทริปแบบคลีนๆ ---
st.markdown(f"<h3 style='text-align: center; margin-top: 10px; color: {header_color};'>HK TRIP 2026</h3>", unsafe_allow_html=True)

# --- Connection & Tabs ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

tab1, tab2, tab3 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY"])
members = ["KK", "Charlie"]

# (ส่วน Data Loading และ Tab ต่างๆ เหมือนเดิมที่คุณใช้)
# --- TAB 2: PLAN ---
@st.dialog("VISUAL DIARY", width="large")
def show_diary_modal(img_url):
    st.image(img_url, use_container_width=True)

with tab2:
    img_url = "https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png"
    if st.button("🖼️ VIEW VISUAL DIARY", use_container_width=True):
        show_diary_modal(img_url)

    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            df_plan['Day'] = pd.to_numeric(df_plan['Day'], errors='coerce').fillna(0).astype(int)
            for day in sorted(df_plan['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {day}</div>", unsafe_allow_html=True)
                day_data = df_plan[df_plan['Day'] == day]
                for _, r in day_data.iterrows():
                    time_val = r['Time'] if pd.notna(r['Time']) else ""
                    st.markdown(f'<div class="plan-card"><div class="time-text">{time_val}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")
