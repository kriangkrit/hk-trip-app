import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

# --- Theme Selector on Main Page ---
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("<h3 style='text-align: left; margin-top: 5px;'>HK TRIP 2026</h3>", unsafe_allow_html=True)
with c2:
    # เลือกโหมดสี (ใช้ปุ่มกดเลือกที่หน้าแรก)
    theme_mode = st.segmented_control(
        "Theme", ["Light", "Dark"], default="Light", label_visibility="collapsed"
    )

# --- Theme Logic (กำหนดตัวแปรสี) ---
if theme_mode == "Dark":
    bg_color, text_color, header_color = "#0e1117", "#eeeeee", "#ffffff"
    border_color, timeline_dot, card_border = "#333333", "#555555", "#444444"
    input_bg = "#1e1e1e"
else:
    bg_color, text_color, header_color = "#ffffff", "#444444", "#222222"
    border_color, timeline_dot, card_border = "#eeeeee", "#bbbbbb", "#dddddd"
    input_bg = "#ffffff"

# --- Inject Fixed CSS (แก้ปัญหาบั๊กสีในมือถือ) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    /* ล็อกสีพื้นหลังแอป */
    .stApp {{ 
        background-color: {bg_color} !important; 
    }}
    
    /* ล็อกสีตัวอักษรทุกประเภท */
    html, body, [class*="css"], .stMarkdown, p, div, span, label, li {{ 
        font-family: 'Anuphan', sans-serif !important; 
        font-weight: 300 !important;
        color: {text_color} !important;
    }}

    /* ซ่อน UI มาตรฐานของ Streamlit */
    summary > span > div > div {{ font-size: 0 !important; visibility: hidden !important; }}
    summary > span > div > div > p {{ font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }}
    svg[data-testid="stExpanderIcon"] {{ display: none !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* แก้ไขช่อง Input และ Selectbox ให้สีไม่เพี้ยนในมือถือ */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextInput input, .stNumberInput input, div[role="listbox"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}

    /* แก้สีปุ่มกด */
    .stButton>button {{ 
        border-radius: 12px; 
        border: 1px solid {border_color} !important; 
        background-color: {input_bg} !important; 
        color: {text_color} !important;
        width: 100%;
    }}
    
    /* ปรับแต่ง Tabs */
    button[data-baseweb="tab"] {{
        color: {text_color} !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        border-bottom-color: #ff4b4b !important;
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
    
    /* Summary Flexbox */
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
    if 'Note' not in df.columns: df['Note'] = ""
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
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
                    new_row = pd.DataFrame([{"Timestamp": now, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": "", "Is_Settled": False}])
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
                day_data = df_plan[df_plan['Day'] == day]
                for _, r in day_data.iterrows():
                    time_val = r['Time'] if pd.notna(r['Time']) else ""
                    loc_val = r['Location'] if pd.notna(r['Location']) else ""
                    st.markdown(f'<div class="plan-card"><div class="time-text">{time_val}</div><div class="location-text">{loc_val}</div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(
            showlegend=True, 
            margin=dict(t=10, b=10, l=10, r=10), 
            font=dict(family="Anuphan", size=12, color=text_color),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
        
        # Calculate Balance
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = str(r['Participants']).split(", ")
            share = float(r['Amount_HKD']) / len(p_list)
            for p in p_list: 
                if p in bal: bal[p] -= share
        
        diff = bal["KK"]
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
        c_m2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
        
        # Summary Lists
        user_items = {m: [] for m in members}
        for _, r in df.iterrows():
            p_list = str(r['Participants']).split(", ")
            share = float(r['Amount_HKD']) / len(p_list)
            for p in p_list: 
                if p in user_items: user_items[p].append(f"{r['Item']} ({share:,.0f})")

        kk_items = ' • ' + ' <br> • '.join(user_items["KK"]) if user_items["KK"] else '-'
        charlie_items = ' • ' + ' <br> • '.join(user_items["Charlie"]) if user_items["Charlie"] else '-'

        st.markdown(f"""
            <div class="mobile-flex-container">
                <div class="flex-item-box">
                    <div class="member-label">KK's Items</div>
                    <div class="item-text-centered">{kk_items}</div>
                </div>
                <div class="flex-item-box">
                    <div class="member-label">Charlie's Items</div>
                    <div class="item-text-centered">{charlie_items}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No data.")
