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
    
    /* 1. บังคับพื้นหลังของแอปและ Container ทั้งหมดให้เป็นสีขาว */
    .stApp, .main, .block-container, [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #333 !important;
    }

    /* 2. บังคับ Input ทุกประเภท (Text, Number, Select) ให้พื้นหลังขาว ขอบจาง */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="popover"],
    .stMultiSelect div[role="listbox"],
    div[role="combobox"] {
        background-color: #ffffff !important;
        color: #333 !important;
        border: 1px solid #eeeeee !important;
    }

    /* 3. แก้ไขสีตัวอักษรใน Input และ Placeholder ให้มองเห็นบนพื้นขาว */
    input, p, span, label, div {
        color: #333 !important;
        font-family: 'Anuphan', sans-serif !important;
    }

    /* 4. ปรับแต่งปุ่ม Multi-select tags (KK, Charlie) ให้ดูคลีน */
    span[data-baseweb="tag"] {
        background-color: #f5f5f5 !important;
        color: #333 !important;
        border: 0.5px solid #eee !important;
    }
    
    /* 5. ปรับแต่งปุ่ม SAVE ให้เป็นสีขาวขอบเทา */
    .stButton>button {
        background-color: #ffffff !important;
        color: #333 !important;
        border: 1px solid #eeeeee !important;
        border-radius: 8px;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #f9f9f9 !important;
        border-color: #ccc !important;
    }

    /* 6. ซ่อนขีดแดงใต้ Tab และปรับแต่ง Tab ให้ขาวล้วน */
    .stTabs [data-baseweb="tab-highlight-view"] { background-color: #333 !important; }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; }

    /* 7. ปรับสีพื้นหลังของ Number Input (ปุ่ม + และ -) */
    div[data-testid="stNumberInputStepDown"], 
    div[data-testid="stNumberInputStepUp"] {
        background-color: #ffffff !important;
        border-left: 1px solid #eee !important;
    }

    /* ซ่อน UI ที่ไม่จำเป็น */
    #MainMenu, footer, header { visibility: hidden; }
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
        # ทำความสะอาดข้อมูลเบื้องต้น
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
                new_row = pd.DataFrame([{
                    "Timestamp": now, 
                    "Item": str(item), 
                    "Amount_HKD": float(amount), 
                    "Payer": str(payer), 
                    "Participants": ", ".join(parts), 
                    "Category": str(cat), 
                    "Is_Settled": bool(settled), 
                    "Note": str(note)
                }])
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
                    # แปลงค่า Is_Settled ให้เป็น bool เพื่อใช้ใน checkbox
                    current_settled = str(row['Is_Settled']).upper() == 'TRUE' or row['Is_Settled'] == True
                    u_settled = st.checkbox("Settled", value=current_settled)
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

# --- TAB 3: SUMMARY (UPDATED) ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        cat_sum = cat_sum[cat_sum['Amount_HKD'] > 0]
        
        if not cat_sum.empty:
            # 1. Pie Chart
            fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=10, r=10), font=dict(family="Anuphan", size=14))
            st.plotly_chart(fig, use_container_width=True)
            
            # 2. Table Breakdown
            st.markdown("<p style='font-weight:300;'>CATEGORY BREAKDOWN</p>", unsafe_allow_html=True)
            st.table(cat_sum.style.format({'Amount_HKD': '{:,.0f}'}))
            st.divider()

            # 3. Settlement Calculation
            rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
            
            # Ensure Is_Settled is boolean for calculation
            df['Is_Settled_Bool'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
            
            bal = {m: 0.0 for m in members}
            for _, r in df[df['Is_Settled_Bool'] == False].iterrows():
                bal[r['Payer']] += float(r['Amount_HKD'])
                p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip()]
                if p_list:
                    share = float(r['Amount_HKD']) / len(p_list)
                    for p in p_list:
                        if p in bal: bal[p] -= share

            diff = bal["KK"]
            c1, c2 = st.columns(2)
            c1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
            c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
            
            if diff > 0.01: st.info("Charlie → KK")
            elif diff < -0.01: st.info("KK → Charlie")
            else: st.success("Balanced")

            st.markdown("<hr style='border: 0.5px solid #eee; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:300;'>NET SPEND PER PERSON</p>", unsafe_allow_html=True)
            
            # 4. Usage Statistics
            usage = {m: 0.0 for m in members}
            user_items = {m: [] for m in members}
            for _, r in df.iterrows():
                p_list = [p.strip() for p in str(r['Participants']).split(",") if p.strip()]
                if p_list:
                    share = float(r['Amount_HKD']) / len(p_list)
                    for p in p_list: 
                        if p in usage: 
                            usage[p] += share
                            user_items[p].append(f"{r['Item']} ({share:,.0f})")
            
            usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
            st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
            
            # 5. Mobile-Friendly Item Lists
            kk_items = ' • ' + ' <br> • '.join(user_items["KK"]) if user_items["KK"] else 'No items'
            charlie_items = ' • ' + ' <br> • '.join(user_items["Charlie"]) if user_items["Charlie"] else 'No items'

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

# --- TAB 4: MAP ---
with tab4:
    st.markdown('<div class="small-header">GOOGLE MAPS</div>', unsafe_allow_html=True)
    maps_src = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3691.802773295842!2d114.1672918!3d22.285493!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x340400631669463f%3A0x6ec040520623604f!2sHong%20Kong!5e0!3m2!1sen!2sth!4v1712745582345!5m2!1sen!2sth"

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
    st.link_button("OPEN IN GOOGLE MAPS APP", "https://maps.app.goo.gl/kXvA6WfK3N5mYh9u8", use_container_width=True)
