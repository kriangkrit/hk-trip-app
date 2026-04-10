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
    
    .day-header { font-size: 16px; font-weight: 400; color: #222; margin: 30px 0 15px 0; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .plan-card { border-left: 1px solid #ddd; padding: 0 0 25px 20px; margin-left: 5px; position: relative; }
    .plan-card::before { content: ''; position: absolute; left: -4px; top: 4px; width: 7px; height: 7px; background-color: #bbb; border-radius: 50%; }
    .time-text { font-size: 11px; color: #aaa; }
    .location-text { font-size: 14px; color: #444; }

    .mobile-flex-container { display: flex; justify-content: space-between; gap: 8px; width: 100%; margin-top: 15px; }
    .flex-item-box { flex: 1; text-align: center; }
    .member-label { font-size: 11px; color: #222; border-bottom: 0.5px solid #eee; margin-bottom: 5px; display: inline-block; }
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
    # อ่านข้อมูลและลบแถวที่ว่างเปล่าออกทั้งหมด
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    
    # ตรวจสอบและสร้างคอลัมน์ที่จำเป็นหากหายไป (ป้องกัน Error)
    required_cols = ["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    if not df.empty:
        # ทำความสะอาดข้อมูล
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
        # แปลง Is_Settled ให้เป็น Boolean ที่ถูกต้อง
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        df['Payer'] = df['Payer'].fillna(members[0])
        df['Participants'] = df['Participants'].fillna(", ".join(members))
except Exception as e:
    st.error(f"Connection Error: {e}")
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

# --- TAB 1: EXPENSE ---
with tab1:
    with st.expander("➕ ADD NEW"):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount > 0:
                    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_data = pd.DataFrame([{"Timestamp": now, "Item": item, "Amount_HKD": amount, "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": settled, "Note": note}])
                    df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()

    if not df.empty:
        with st.expander("✏️ EDIT / 🗑️ DELETE"):
            # สร้างตัวเลือก Index + Item Name
            options = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            selected = st.selectbox("Select entry:", options)
            idx = int(selected.split(":")[0])
            row = df.iloc[idx]

            col_e, col_d = st.columns(2)
            with col_d:
                if st.button("🗑️ DELETE", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()
            with col_e:
                edit_mode = st.toggle("✏️ EDIT")

            if edit_mode:
                with st.form("edit_form"):
                    u_item = st.text_input("Item", value=str(row['Item']))
                    u_amt = st.number_input("Price", value=float(row['Amount_HKD']))
                    u_payer = st.selectbox("Payer", members, index=members.index(row['Payer']) if row['Payer'] in members else 0)
                    u_cat = st.selectbox("Category", categories, index=categories.index(row['Category']) if row['Category'] in categories else 0)
                    # Participants handling
                    p_current = [p.strip() for p in str(row['Participants']).split(",") if p.strip() in members]
                    u_parts = st.multiselect("Split with", members, default=p_current)
                    u_note = st.text_input("Note", value=str(row['Note']) if pd.notna(row['Note']) else "")
                    u_settled = st.checkbox("Settled", value=bool(row['Is_Settled']))

                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'] = u_item
                        df.at[idx, 'Amount_HKD'] = u_amt
                        df.at[idx, 'Payer'] = u_payer
                        df.at[idx, 'Category'] = u_cat
                        df.at[idx, 'Participants'] = ", ".join(u_parts)
                        df.at[idx, 'Note'] = u_note
                        df.at[idx, 'Is_Settled'] = u_settled
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()

        st.divider()
        # แสดงผลตาราง (สลับเอาล่าสุดขึ้นบน)
        view_df = df.copy()
        view_df['Date'] = view_df['Timestamp'].astype(str).str.split().str[0]
        st.dataframe(view_df.iloc[::-1][['Date', 'Item', 'Amount_HKD', 'Payer', 'Category']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
@st.dialog("VISUAL DIARY")
def show_img(url): st.image(url, use_container_width=True)

with tab2:
    if st.button("VIEW VISUAL DIARY", use_container_width=True):
        show_img("https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png")
    
    try:
        itinerary = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Location'])
        for d in sorted(pd.to_numeric(itinerary['Day']).unique()):
            st.markdown(f"<div class='day-header'>DAY {int(d)}</div>", unsafe_allow_html=True)
            for _, r in itinerary[itinerary['Day'] == d].iterrows():
                st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except: st.info("Add 'Itinerary' sheet with Day, Time, Location columns to see plan.")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5)
        
        # Balance Logic
        balances = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            balances[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: balances[p] -= share
        
        kk_bal = balances["KK"]
        c1, c2 = st.columns(2)
        c1.metric("TRANSFER (HKD)", f"{abs(kk_bal):,.2f}")
        c2.metric("TRANSFER (THB)", f"{abs(kk_bal)*rate:,.0f}")
        st.info("Charlie → KK" if kk_bal > 0 else "KK → Charlie" if kk_bal < 0 else "All Settled")

        # รายการของแต่ละคน
        u_list = {m: [] for m in members}
        for _, r in df.iterrows():
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: u_list[p].append(f"{r['Item']} ({share:,.0f})")

        st.markdown(f"""
            <div class="mobile-flex-container">
                <div class="flex-item-box"><div class="member-label">KK</div><div class="item-text-centered">{'<br>'.join(u_list['KK']) if u_list['KK'] else '-'}</div></div>
                <div class="flex-item-box"><div class="member-label">Charlie</div><div class="item-text-centered">{'<br>'.join(u_list['Charlie']) if u_list['Charlie'] else '-'}</div></div>
            </div>
        """, unsafe_allow_html=True)
    else: st.info("No data yet.")
