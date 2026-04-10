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
        font-weight: 300 !important; color: #444;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }
    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; width: 100%; }
    .small-header { font-size: 16px; font-weight: 400; color: #444; margin: 25px 0 10px 0; letter-spacing: 1px; border-left: 3px solid #eee; padding-left: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        for col in ['Item', 'Payer', 'Participants', 'Category', 'Note', 'Timestamp']:
            if col in df.columns: df[col] = df[col].astype(str).replace(['nan', 'None'], '')
    else:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])
except Exception:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

st.title("HK TRIP 2026")
tab1, tab2, tab3, tab4 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY", "🗺️ MAP"])

# --- TAB 1: EXPENSE (เหมือนเดิม) ---
with tab1:
    st.markdown('<div class="small-header">ADD ITEM</div>', unsafe_allow_html=True)
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("What did you buy?", placeholder="e.g. Dim Sum")
        c1, c2 = st.columns(2)
        with c1: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0, format="%.0f")
        with c2: payer = st.selectbox("Payer", members)
        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("Category", categories)
        with c4: parts = st.multiselect("Split with", members, default=members)
        note = st.text_input("Note", placeholder="Optional...")
        settled = st.checkbox("Pre-paid (Already Settled)")
        if st.form_submit_button("SAVE"):
            if item and amount >= 0:
                now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                new_row = pd.DataFrame([{"Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), "Payer": str(payer), "Participants": ", ".join(parts), "Category": str(cat), "Is_Settled": bool(settled), "Note": str(note)}])
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.rerun()
    if not df.empty:
        st.divider()
        st.dataframe(df.iloc[::-1][['Timestamp', 'Item', 'Amount_HKD', 'Payer']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
with tab2:
    st.info("Itinerary details will show here from 'Itinerary' sheet.")

# --- TAB 3: SUMMARY (ปรับปรุงใหม่ตามโจทย์) ---
with tab3:
    if not df.empty:
        # 1. กราฟสรุปภาพรวม
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # 2. คำนวณ Net Balance เพื่อโอนเงิน
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5)
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: bal[p] -= share

        st.divider()
        c1, c2 = st.columns(2)
        transfer_hkd = abs(bal['KK'])
        c1.metric("MUST TRANSFER (HKD)", f"{transfer_hkd:,.2f}")
        c2.metric("APPROX (THB)", f"{transfer_hkd * rate:,.0f}")
        
        if bal['KK'] > 0: st.info("💡 **Charlie ต้องโอนให้ KK**")
        elif bal['KK'] < 0: st.info("💡 **KK ต้องโอนให้ Charlie**")

        # 3. ส่วนสำคัญ: เจาะลึกว่าแต่ละคน "รับผิดชอบค่าอะไรไปบ้าง" (Personal Breakdown)
        st.markdown('<div class="small-header">YOUR PERSONAL BILLS</div>', unsafe_allow_html=True)
        st.caption("รายการข้างล่างนี้คือยอดที่คุณต้องจ่ายจริง (หารแล้ว)")

        for m in members:
            with st.expander(f"Detailed Bill for {m}"):
                # สร้างตารางใหม่เพื่อเก็บรายการที่คนๆ นี้มีส่วนหาร
                personal_shares = []
                for _, r in df.iterrows():
                    p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
                    if m in p_list:
                        share_amount = float(r['Amount_HKD']) / len(p_list)
                        personal_shares.append({
                            "Item": r['Item'],
                            "Category": r['Category'],
                            "Full Price": r['Amount_HKD'],
                            "Your Share": share_amount,
                            "Status": "Settled" if r['Is_Settled'] else "Pending"
                        })
                
                if personal_shares:
                    p_df = pd.DataFrame(personal_shares)
                    st.dataframe(p_df, use_container_width=True, hide_index=True)
                    
                    # สรุปยอดรวมที่คนนี้ต้องรับผิดชอบทั้งทริป
                    total_own_share = p_df['Your Share'].sum()
                    st.write(f"**Total you owe for this trip:** `{total_own_share:,.2f} HKD`")
                else:
                    st.caption("No records found.")

        # 4. สรุปยอดเงินกองกลาง (Who actually paid)
        st.markdown('<div class="small-header">ACTUAL PAYMENTS</div>', unsafe_allow_html=True)
        for m in members:
            actual_paid = df[df['Payer'] == m]['Amount_HKD'].sum()
            st.write(f"{m} ควักจ่ายไปทั้งหมด: `{actual_paid:,.2f} HKD`")

    else:
        st.info("No data found.")

# --- TAB 4: MAP ---
with tab4:
    st.write("Google Maps Integration")
