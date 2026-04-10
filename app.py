import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

# --- Minimal Theme Toggle Logic ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'Light'

# สร้างส่วนหัวและปุ่ม Toggle ในบรรทัดเดียวกัน
head_col, btn_col = st.columns([3, 1])
with head_col:
    st.markdown("<h3 style='margin:0;'>HK TRIP 2026</h3>", unsafe_allow_html=True)
with btn_col:
    # ปุ่มเปลี่ยนโหมดแบบ Icon-only (ประหยัดที่ที่สุด)
    label = "☀️ Light" if st.session_state.theme == 'Dark' else "🌑 Dark"
    if st.button(label):
        st.session_state.theme = 'Dark' if st.session_state.theme == 'Light' else 'Light'
        st.rerun()

# กำหนดสี
if st.session_state.theme == "Dark":
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
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&display=swap');
    
    .stApp {{ background-color: {bg_color}; }}
    
    html, body, [class*="css"], .stMarkdown, p, div {{ 
        font-family: 'Anuphan', sans-serif !important; 
        font-weight: 300 !important;
        color: {text_color} !important;
    }}

    /* ซ่อนส่วนที่ไม่จำเป็น */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: transparent; }}
    
    /* ปุ่ม Theme (เฉพาะปุ่มบนขวา) */
    div.stButton > button:first-child {{
        border-radius: 20px;
        padding: 2px 15px;
        font-size: 12px;
        border: 1px solid {border_color};
        background-color: {input_bg};
        float: right;
    }}

    /* Timeline & Plan Styles */
    .day-header {{
        font-size: 16px; font-weight: 400; color: {header_color};
        margin: 25px 0 10px 0; border-bottom: 1px solid {border_color};
        padding-bottom: 5px;
    }}
    .plan-card {{
        border-left: 1px solid {card_border};
        padding: 0 0 20px 20px; margin-left: 5px; position: relative;
    }}
    .plan-card::before {{
        content: ''; position: absolute; left: -4.5px; top: 5px;
        width: 8px; height: 8px; background-color: {timeline_dot}; border-radius: 50%;
    }}
    .time-text {{ font-size: 11px; color: #888; }}
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

tab1, tab2, tab3 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY"])

# (เนื้อหาแต่ละ Tab เหมือนในโค้ดที่คุณให้มาล่าสุด)

with tab1:
    # --- TAB 1: EXPENSE ---
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
        if not df.empty:
            df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
    except:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Note", "Is_Settled"])

    with st.expander("ADD NEW", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item")
            c_a, c_b = st.columns(2)
            with c_a: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0)
            with c_b: payer = st.selectbox("Payer", ["KK", "Charlie"])
            if st.form_submit_button("SAVE"):
                if item and amount:
                    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": "KK, Charlie", "Category": "Other", "Is_Settled": False}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()
    if not df.empty:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True, hide_index=True)

with tab2:
    # --- TAB 2: PLAN ---
    @st.dialog("VISUAL DIARY", width="large")
    def show_diary_modal(url):
        st.image(url, use_container_width=True)

    img_url = "https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png"
    if st.button("🖼️ VIEW VISUAL DIARY", use_container_width=True):
        show_diary_modal(img_url)

    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            df_plan['Day'] = pd.to_numeric(df_plan['Day'], errors='coerce').fillna(0).astype(int)
            for day in sorted(df_plan['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {day}</div>", unsafe_allow_html=True)
                for _, r in df_plan[df_plan['Day'] == day].iterrows():
                    st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

with tab3:
    # --- TAB 3: SUMMARY ---
    if not df.empty:
        fig = px.pie(df, values='Amount_HKD', names='Payer', hole=0.7)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate", value=4.5)
        st.info("Summary logic ready.")
    else:
        st.info("No data.")
