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

    summary > span > div > div { font-size: 0 !important; visibility: hidden !important; }
    summary > span > div > div > p { font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }
    svg[data-testid="stExpanderIcon"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; width: 100%; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }

    /* Custom Header Style - White & Small */
    .small-header {
        font-size: 16px;
        font-weight: 400;
        color: #FFFFFF; 
        margin-bottom: 15px;
        letter-spacing: 1px;
    }

    /* Timeline Styles */
    .day-header {
        font-size: 16px;
        font-weight: 400;
        color: #222;
        margin: 30px 0 15px 0;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
    }
    .plan-card {
        border-left: 1px solid #ddd;
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
        background-color: #bbb;
        border-radius: 50%;
    }
    .time-text { font-size: 11px; color: #aaa; }
    .location-text { font-size: 14px; color: #444; }

    /* Summary Mobile Styles */
    .mobile-flex-container {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
        margin-top: 15px;
    }
    .flex-item-box { flex: 1; text-align: center; }
    .member-label { 
        font-size: 11px; color: #222; border-bottom: 0.5px solid #eee; 
        display: inline-block; padding-bottom: 2px; margin-bottom: 5px;
    }
    .item-text-centered { font-size: 10px; color: #999; line-height: 1.4; }
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
        # Force string types for text columns
        for col in ['Item', 'Payer', 'Participants', 'Category', 'Note', 'Timestamp']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None'], '')
    else:
        df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])
except Exception:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled", "Note"])

st.title("HK TRIP 2026")
tab1, tab2, tab3, tab4 = st.tabs(["💰 EXPENSE", "📍 PLAN", "📊 SUMMARY", "🗺️ MAP"])

# --- TAB 1: EXPENSE ---
with tab1:
    st.markdown('<div class="small-header">ADD ITEM</div>', unsafe_allow_html=True)
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("What did you buy?", placeholder="e.g. Dim Sum")
        c1, c2 = st.columns(2)
        with c1: amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0, format="%.0f")
        with c2: payer = st.selectbox("Payer", members)
        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("Category", categories)
        with c4: parts = st.multiselect("Split", members, default=members)
        note = st.text_input("Note", placeholder="Optional...")
        settled = st.checkbox("Pre-paid (Settled)")
        if st.form_submit_button("SAVE"):
            if item and amount >= 0:
                now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                new_row = pd.DataFrame([{"Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), "Payer": str(payer), "Participants": ", ".join(parts), "Category": str(cat), "Is_Settled": bool(settled), "Note": str(note)}])
                df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.rerun()

    if not df.empty:
        st.write("")
        with st.expander("Edit / Delete"):
            options = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            selected = st.selectbox("Select entry:", options)
            idx = int(selected.split(":")[0])
            row = df.iloc[idx]
            col_e, col_d = st.columns(2)
            with col_d:
                if st.button("DELETE", key=f"del_{idx}", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                    st.rerun()
            with col_e:
                edit_mode = st.toggle("EDIT", key=f"tog_{idx}")
            if edit_mode:
                with st.form("edit_form"):
                    u_item = st.text_input("Item", value=str(row['Item']))
                    u_amt = st.number_input("Price", value=float(row['Amount_HKD']))
                    u_payer = st.selectbox("Payer", members, index=members.index(row['Payer']) if row['Payer'] in members else 0)
                    u_cat = st.selectbox("Category", categories, index=categories.index(row['Category']) if row['Category'] in categories else 0)
                    u_parts = st.multiselect("Split with", members, default=[p.strip() for p in str(row['Participants']).split(",") if p.strip() in members])
                    u_note = st.text_input("Note", value=str(row['Note']))
                    u_settled = st.checkbox("Settled", value=bool(row['Is_Settled']))
                    if st.form_submit_button("UPDATE"):
                        df = df.astype(object)
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'] = str(u_item), float(u_amt)
                        df.at[idx, 'Payer'], df.at[idx, 'Category'] = str(u_payer), str(u_cat)
                        df.at[idx, 'Participants'], df.at[idx, 'Note'] = ", ".join(u_parts), str(u_note)
                        df.at[idx, 'Is_Settled'] = bool(u_settled)
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()
        st.divider()
        st.dataframe(df.iloc[::-1][['Timestamp', 'Item', 'Amount_HKD', 'Payer']], use_container_width=True, hide_index=True)

# --- TAB 2: PLAN ---
@st.dialog("VISUAL DIARY", width="large")
def show_diary(url): st.image(url, use_container_width=True)

with tab2:
    if st.button("VIEW VISUAL DIARY", use_container_width=True):
        show_diary("https://raw.githubusercontent.com/kriangkrit/hk-trip-app/main/unnamed.png")
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            df_plan['Day'] = pd.to_numeric(df_plan['Day'], errors='coerce').fillna(0).astype(int)
            for d in sorted(df_plan['Day'].unique()):
                st.markdown(f"<div class='day-header'>DAY {d}</div>", unsafe_allow_html=True)
                for _, r in df_plan[df_plan['Day'] == d].iterrows():
                    st.markdown(f'<div class="plan-card"><div class="time-text">{r["Time"]}</div><div class="location-text">{r["Location"]}</div></div>', unsafe_allow_html=True)
    except: st.info("Check 'Itinerary' sheet.")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and pd.to_numeric(df['Amount_HKD']).sum() > 0:
        fig = px.pie(df, values='Amount_HKD', names='Category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
        rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5)
        bal = {m: 0.0 for m in members}
        for _, r in df[df['Is_Settled'] == False].iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip() in members]
            if p_list:
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: bal[p] -= share
        c1, c2 = st.columns(2)
        c1.metric("TRANSFER (HKD)", f"{abs(bal['KK']):,.2f}")
        c2.metric("TRANSFER (THB)", f"{abs(bal['KK'])*rate:,.0f}")
        st.info("Charlie → KK" if bal['KK'] > 0 else "KK → Charlie" if bal['KK'] < 0 else "Balanced")
    else: st.info("No data.")

# --- TAB 4: MAP ---
with tab4:
    st.markdown('<div class="small-header">GOOGLE MAPS</div>', unsafe_allow_html=True)
    
    # *** ใช้ URL เฉพาะส่วน src จาก iframe ของคุณ ***
    # หาก URL ใน iframe ของคุณคือ https://www.google.com/maps9... ให้เอามาใส่ที่นี่
    maps_src = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d118147.68202022137!2d114.07328965935035!3d22.29255855079815!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3403f07478df3241%3A0xfa64079059951077!2z4Liu4Lit4LiH4LiB4LiH!5e0!3m2!1sth!2sth!4v1715615615615!5m2!1sth!2sth"

    st.markdown(f"""
        <iframe 
            src="{maps_src}" 
            width="100%" 
            height="550" 
            style="border:0; border-radius:15px; background-color: #f0f0f0;" 
            allowfullscreen="" 
            loading="lazy" 
            referrerpolicy="no-referrer-when-downgrade">
        </iframe>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.link_button("OPEN IN GOOGLE MAPS APP", "https://maps.app.goo.gl/Yp9H1Z2xNPr7XqZ88", use_container_width=True)
