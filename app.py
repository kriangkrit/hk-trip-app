import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"], .stMarkdown { 
        font-family: 'Anuphan', 'Montserrat', sans-serif !important; 
        font-weight: 300 !important;
        color: #444;
    }

    /* ซ่อน UI ส่วนเกิน */
    summary > span > div > div { font-size: 0 !important; visibility: hidden !important; }
    summary > span > div > div > p { font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }
    svg[data-testid="stExpanderIcon"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }

    /* --- Styles สำหรับหน้า PLAN (Flat Timeline) --- */
    .day-header {
        font-size: 16px;
        font-weight: 400;
        color: #222;
        margin: 30px 0 15px 0;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        letter-spacing: 1px;
    }
    .plan-card {
        background-color: transparent; /* เอาพื้นหลังขาวออก */
        border-left: 1px solid #ddd;   /* เส้น Timeline บางลง */
        padding: 0 0 25px 20px;
        margin-left: 5px;
        position: relative;
    }
    .plan-card::before {
        content: '';
        position: absolute;
        left: -4px;
        top: 4px;
        width: 7px;
        height: 7px;
        background-color: #bbb; /* จุดสีเทาอ่อนดูละมุนกว่า */
        border-radius: 50%;
    }
    .time-text {
        font-size: 11px;
        font-weight: 400;
        color: #aaa;
        margin-bottom: 2px;
    }
    .location-text {
        font-size: 14px;
        color: #444;
        line-height: 1.5;
    }

    /* --- Styles สำหรับหน้า SUMMARY --- */
    .mobile-flex-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        width: 100%;
        margin-top: 15px;
    }
    .flex-item-box {
        flex: 1;
        text-align: center;
    }
    .member-label { 
        font-size: 11px; 
        color: #222; 
        border-bottom: 0.5px solid #eee; 
        display: inline-block; 
        padding-bottom: 2px;
        margin-bottom: 5px;
    }
    .item-text-centered { font-size: 10px; color: #999; line-height: 1.4; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK TRIP 2026")
tab1, tab2, tab3 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
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
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0.0, value=None, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note (Optional)")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount is not None:
                    now_full = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now_full, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": note, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    if not df.empty:
        st.write("")
        display_df = df.copy()
        display_df['Date'] = display_df['Timestamp'].str.split().str[0]
        final_df = display_df.sort_index(ascending=False)[['Date', 'Item', 'Amount_HKD', 'Payer', 'Category', 'Note']]
        st.dataframe(final_df, use_container_width=True, hide_index=True)

# --- TAB 2: PLAN (Ultra Minimal Design) ---
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0)
        df_plan = df_plan.dropna(subset=['Day', 'Location'], how='all')
        
        if df_plan.empty:
            st.info("No plan data found.")
        else:
            # แปลงเลข Day ให้เป็นจำนวนเต็ม (ป้องกันการเกิด 1.0)
            df_plan['Day'] = pd.to_numeric(df_plan['Day'], errors='coerce').fillna(0).astype(int)
            
            for day in sorted(df_plan['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {day}</div>", unsafe_allow_html=True)
                
                day_data = df_plan[df_plan['Day'] == day]
                for _, r in day_data.iterrows():
                    time_val = r['Time'] if pd.notna(r['Time']) else ""
                    loc_val = r['Location'] if pd.notna(r['Location']) else ""
                    
                    st.markdown(f"""
                        <div class="plan-card">
                            <div class="time-text">{time_val}</div>
                            <div class="location-text">{loc_val}</div>
                        </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Anuphan", size=12))
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
        
        # คำนวณ Net Balance
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = str(r['Participants']).split(", ")
            share = float(r['Amount_HKD']) / len(p_list)
            for p in p_list: 
                if p in bal: bal[p] -= share

        diff = bal["KK"]
        c1, c2 = st.columns(2)
        c1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
        c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
        if diff > 0.01: st.info("Charlie → KK")
        elif diff < -0.01: st.info("KK → Charlie")
        
        # สรุปรายการรายคนแบบ Flexbox
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
