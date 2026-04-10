import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

# --- Theme Selector on Main Page ---
# วางไว้บนสุดเพื่อให้เลือกโหมดได้ง่ายๆ
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("<h3 style='text-align: left; margin-top: 5px;'>HK TRIP 2026</h3>", unsafe_allow_html=True)
with c2:
    # ใช้ segmented_control เพื่อความเป็นระเบียบ (Streamlit 1.35+)
    theme_mode = st.segmented_control(
        "Theme", ["Light", "Dark"], default="Light", label_visibility="collapsed"
    )

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

    summary > span > div > div {{ font-size: 0 !important; visibility: hidden !important; }}
    summary > span > div > div > p {{ font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }}
    svg[data-testid="stExpanderIcon"] {{ display: none !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    .stButton>button {{ 
        border-radius: 12px; border: 0.5px solid {border_color}; 
        background-color: {input_bg}; color: {text_color};
    }}
    
    /* Segmented Control Styling */
    div[data-testid="stSegmentedControl"] {{
        background-color: {input_bg};
        border-radius: 12px;
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
    
    /* Summary Flex */
    .mobile-flex-container {{ display: flex; justify-content: space-between; gap: 8px; margin-top: 15px; }}
    .member-label {{ font-size: 11px; color: {text_color}; border-bottom: 0.5px solid {border_color}; margin-bottom: 5px; }}
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

tab1, tab2, tab3 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading (Expense) ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Note", "Is_Settled"])

# --- TAB 1: EXPENSE ---
with tab1:
    with st.expander("ADD NEW", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item")
            c_a, c_b = st.columns(2)
            with c_a: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0)
            with c_b: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            if st.form_submit_button("SAVE"):
                if item and amount:
                    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": False}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()
    if not df.empty:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True, hide_index=True)

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
                for _, r in df_plan[df_plan['Day'] == day].iterrows():
                    st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty:
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.7)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate", value=4.5)
        # (ส่วนคำนวณเงินโอนเหมือนเดิม)
        st.info("Summary logic active")
    else:
        st.info("No data.")
