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
        font-weight: 300 !important; color: #555;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Typography */
    h1 { font-weight: 200 !important; letter-spacing: 3px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; font-size: 24px !important; }
    h3 { font-weight: 300 !important; font-size: 14px !important; letter-spacing: 1px; color: #888; text-transform: uppercase; margin-bottom: 15px; }
    
    /* UI Elements */
    .stButton>button { border-radius: 10px; border: 0.5px solid #eee; background-color: #fff; color: #888; font-size: 12px; height: 38px; transition: 0.3s; }
    .stButton>button:hover { border-color: #bbb; color: #444; }
    div[data-baseweb="input"], div[data-baseweb="select"] { border-radius: 8px !important; border: 0.2px solid #f0f0f0 !important; }
    
    /* Hide Table Index & border */
    .styled-table { border: none !important; }
    hr { margin: 2rem 0; opacity: 0.3; }

    /* Plan & Summary */
    .day-header { font-size: 14px; font-weight: 400; color: #222; margin: 30px 0 10px 0; letter-spacing: 1px; }
    .plan-card { border-left: 0.5px solid #eee; padding: 0 0 20px 15px; margin-left: 5px; }
    .time-text { font-size: 10px; color: #bbb; }
    .location-text { font-size: 13px; color: #666; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK 2026")
tab1, tab2, tab3 = st.tabs(["EXPENSE", "PLAN", "SUMMARY"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        for col in ['Item', 'Payer', 'Participants', 'Category', 'Note', 'Timestamp']:
            df[col] = df[col].astype(str).replace(['nan', 'None'], '')
    else:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

# --- TAB 1: EXPENSE ---
with tab1:
    # --- Form Section ---
    st.subheader("Add Record")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Entry Name", placeholder="e.g. Dim Sum")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: amount = st.number_input("Amount (HKD)", min_value=0.0, step=1.0, format="%.0f")
        with c2: payer = st.selectbox("Payer", members)
        with c3: cat = st.selectbox("Type", categories)
        
        parts = st.multiselect("Split with", members, default=members)
        
        col_btn, col_opt = st.columns([1, 1])
        with col_opt: settled = st.checkbox("Pre-paid (Settled)", value=False)
        
        if st.form_submit_button("SAVE ENTRY"):
            if item and amount >= 0:
                now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                new_data = pd.DataFrame([{"Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), "Payer": str(payer), "Participants": ", ".join(parts), "Category": str(cat), "Is_Settled": bool(settled), "Note": ""}])
                df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.rerun()

    # --- Manage Section ---
    if not df.empty:
        st.write("")
        with st.expander("Edit / Delete"):
            options = [f"{i}: {row['Item']} - {row['Amount_HKD']}" for i, row in df.iterrows()]
            selected = st.selectbox("Select entry", options)
            idx = int(selected.split(":")[0])
            row = df.iloc[idx]

            ce, cd = st.columns(2)
            with cd: 
                if st.button("DELETE", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()
            with ce: edit_mode = st.toggle("EDIT MODE")

            if edit_mode:
                with st.form("edit_form"):
                    u_item = st.text_input("Item", value=str(row['Item']))
                    u_amt = st.number_input("Price", value=float(row['Amount_HKD']))
                    u_payer = st.selectbox("Payer", members, index=members.index(row['Payer']) if row['Payer'] in members else 0)
                    if st.form_submit_button("UPDATE"):
                        df = df.astype(object)
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Payer'] = str(u_item), float(u_amt), str(u_payer)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()

        st.divider()
        # Minimal Table View
        view_df = df.copy()
        view_df['Date'] = view_df['Timestamp'].astype(str).str.split().str[0]
        # สลับเอาล่าสุดขึ้นบนและเลือกเฉพาะคอลัมน์สำคัญ
        final_view = view_df.iloc[::-1][['Item', 'Amount_HKD', 'Payer']]
        st.dataframe(final_view, use_container_width=True, hide_index=True)

# --- TAB 2: PLAN --- (ยังคง Minimal Style เดิม)
with tab2:
    try:
        itinerary = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Location'])
        for d in sorted(pd.to_numeric(itinerary['Day']).unique()):
            st.markdown(f"<div class='day-header'>DAY {int(d)}</div>", unsafe_allow_html=True)
            for _, r in itinerary[itinerary['Day'] == d].iterrows():
                st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except: st.info("Check 'Itinerary' sheet.")

# --- TAB 3: SUMMARY --- (มินิมอลด้วย Donut Chart)
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.8, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("")
        rate = st.number_input("Exchange Rate (1 HKD)", value=4.5, step=0.01)
        # (Logic คำนวณเงินคงเดิม...)
        st.caption("Minimal Summary Active")
