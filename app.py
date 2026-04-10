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
    
    /* Timeline */
    .day-header { font-size: 16px; font-weight: 400; color: #222; margin: 30px 0 15px 0; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .plan-card { border-left: 1px solid #ddd; padding: 0 0 25px 20px; margin-left: 5px; position: relative; }
    .plan-card::before { content: ''; position: absolute; left: -4px; top: 4px; width: 7px; height: 7px; background-color: #bbb; border-radius: 50%; }
    .time-text { font-size: 11px; color: #aaa; }
    .location-text { font-size: 14px; color: #444; }

    /* Summary Flexbox */
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
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
        df['Is_Settled'] = df['Is_Settled'].map({True: True, False: False, 'TRUE': True, 'FALSE': False}).fillna(False)
        if 'Note' not in df.columns: df['Note'] = ""
        if 'Participants' not in df.columns: df['Participants'] = ", ".join(members)
    else:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Note", "Is_Settled"])
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Note", "Is_Settled"])

# --- TAB 1: EXPENSE ---
with tab1:
    # --- ADD NEW ---
    with st.expander("➕ ADD NEW", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note (Optional)")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount > 0:
                    now_full = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now_full, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": note, "Is_Settled": settled}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()

    # --- EDIT / DELETE ---
    if not df.empty:
        with st.expander("✏️ EDIT / 🗑️ DELETE"):
            df_manage = df.copy().reset_index() # ใช้ index จริงป้องกัน error
            df_manage['Label'] = df_manage['index'].astype(str) + ": " + df_manage['Item'].astype(str)
            selected_option = st.selectbox("Select entry:", df_manage['Label'].tolist())
            
            if selected_option:
                idx = int(selected_option.split(":")[0])
                row = df.iloc[idx]
                
                col_edit, col_del = st.columns(2)
                with col_del:
                    if st.button("🗑️ DELETE", use_container_width=True):
                        df = df.drop(idx).reset_index(drop=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()
                
                with col_edit:
                    do_edit = st.toggle("✏️ EDIT")

                if do_edit:
                    with st.form("edit_form"):
                        e_item = st.text_input("Item", value=str(row['Item']))
                        e_amt = st.number_input("Price", value=float(row['Amount_HKD']))
                        # ตรวจสอบว่า payer เดิมอยู่ใน list หรือไม่
                        p_idx = members.index(row['Payer']) if row['Payer'] in members else 0
                        e_payer = st.selectbox("Payer", members, index=p_idx)
                        
                        c_idx = categories.index(row['Category']) if row['Category'] in categories else 0
                        e_cat = st.selectbox("Category", categories, index=c_idx)
                        
                        # แยกรายชื่อ Participants
                        raw_parts = str(row['Participants']).split(", ")
                        e_parts = st.multiselect("Split with", members, default=[p for p in raw_parts if p in members])
                        
                        e_note = st.text_input("Note", value=str(row['Note']) if pd.notna(row['Note']) else "")
                        e_settled = st.checkbox("Settled", value=bool(row['Is_Settled']))
                        
                        if st.form_submit_button("UPDATE"):
                            df.at[idx, 'Item'] = e_item
                            df.at[idx, 'Amount_HKD'] = e_amt
                            df.at[idx, 'Payer'] = e_payer
                            df.at[idx, 'Category'] = e_cat
                            df.at[idx, 'Participants'] = ", ".join(e_parts)
                            df.at[idx, 'Note'] = e_note
                            df.at[idx, 'Is_Settled'] = e_settled
                            conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                            st.rerun()

        st.write("---")
        display_df = df.copy()
        display_df['Date'] = display_df['Timestamp'].astype(str).str.split().str[0]
        st.dataframe(display_df.sort_index(ascending=False)[['Date', 'Item', 'Amount_HKD', 'Payer', 'Category']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
@st.dialog("VISUAL DIARY")
def show_diary(url): st.image(url, use_container_width=True)

with tab2:
    if st.button("VIEW VISUAL DIARY", use_container_width=True):
        show_diary("https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png")

    try:
        df_p = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Location'])
        if not df_p.empty:
            df_p['Day'] = pd.to_numeric(df_p['Day'], errors='coerce').fillna(0).astype(int)
            for d in sorted(df_p['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {d}</div>", unsafe_allow_html=True)
                for _, r in df_p[df_p['Day'] == d].iterrows():
                    st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except: st.info("No itinerary found.")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5)
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: bal[p] -= share
        
        diff = bal["KK"]
        c1, c2 = st.columns(2)
        c1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
        c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
        st.info("Charlie → KK" if diff > 0 else "KK → Charlie" if diff < 0 else "Balanced")

        # Item List
        u_items = {m: [] for m in members}
        for _, r in df.iterrows():
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: u_items[p].append(f"{r['Item']} ({share:,.0f})")

        st.markdown(f"""
            <div class="mobile-flex-container">
                <div class="flex-item-box"><div class="member-label">KK</div><div class="item-text-centered">{'<br>'.join(u_items['KK']) if u_items['KK'] else '-'}</div></div>
                <div class="flex-item-box"><div class="member-label">Charlie</div><div class="item-text-centered">{'<br>'.join(u_items['Charlie']) if u_items['Charlie'] else '-'}</div></div>
            </div>
        """, unsafe_allow_html=True)
    else: st.info("No data.")
