import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
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

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; transition: 0.3s; }
    button.step-up, button.step-down { display: none !important; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }

    [data-testid="stMetricValue"] { font-weight: 200 !important; font-size: 2.2rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; }
    
    div[data-testid="stExpander"] { border: 1px solid #f9f9f9 !important; border-radius: 12px !important; margin-bottom: 10px; }
    
    /* Centered Item List Styling */
    .centered-container { text-align: center; margin-bottom: 25px; }
    .member-name { font-size: 14px; font-weight: 400; color: #222; margin-bottom: 8px; border-bottom: 0.5px solid #eee; display: inline-block; padding: 0 15px 3px 15px; }
    .item-list-centered { font-size: 12px; color: #888; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# --- Connection & Setup (Same as before) ---
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
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# --- TAB 1 & 2 (Keep as is) ---
with tab1:
    with st.expander("ADD NEW", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g. Dim Sum")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0, value=None, step=1)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount is not None:
                    new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%y-%m-%d %H:%M"), "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()
    if not df.empty:
        with st.expander("EDIT"):
            list_edit = [f"{i}: {row['Item']}" for i, row in df.iterrows()]
            sel_edit = st.selectbox("Select Item", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Name", value=r['Item'])
                    e_amount = st.number_input("Price", value=float(r['Amount_HKD']))
                    e_cat = st.selectbox("Category", categories, index=categories.index(r['Category']) if r['Category'] in categories else 0)
                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Category'] = e_item, e_amount, e_cat
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df); st.rerun()
        with st.expander("DELETE"):
            sel_del = st.selectbox("Choose item", ["-- Select --"] + [f"{i}: {r['Item']}" for i, r in df.iterrows()])
            if sel_del != "-- Select --" and st.button("CONFIRM DELETE", use_container_width=True):
                idx_to_del = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx_to_del).reset_index(drop=True))
                st.rerun()
    st.dataframe(df.sort_index(ascending=False)[['Item', 'Amount_HKD', 'Payer', 'Category']], use_container_width=True, hide_index=True)

with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            st.markdown(f"**DAY {day}**")
            for _, r in df_plan[df_plan['Day'] == day].iterrows():
                st.markdown(f"<p style='font-size:14px; color:#888; margin-bottom:2px;'>{r['Time']} — {r['Location']}</p>", unsafe_allow_html=True)
    except: st.info("Check Sheets.")

# --- TAB 3: SUMMARY (Centered Items) ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        # 1. Chart & Breakdown Table
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        cat_sum = cat_sum[cat_sum['Amount_HKD'] > 0]
        if not cat_sum.empty:
            fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=10, r=10), font=dict(family="Anuphan", size=14))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<p style='font-weight:300; text-align:center;'>CATEGORY BREAKDOWN</p>", unsafe_allow_html=True)
            st.table(cat_sum.style.format({'Amount_HKD': '{:,.0f}'}))
            
            st.divider()

            # 2. Rate & Settlement
            rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
            df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
            bal = {m: 0.0 for m in members}
            for _, r in df[df['Is_Settled'] == False].iterrows():
                bal[r['Payer']] += float(r['Amount_HKD'])
                p_list = str(r['Participants']).split(", ")
                for p in p_list: 
                    if p in bal: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

            diff = bal["KK"]
            c1, c2 = st.columns(2)
            c1.metric("TRANSFER (HKD)", f"{abs(diff):,.2f}")
            c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
            if diff > 0.01: st.info("Charlie → KK")
            elif diff < -0.01: st.info("KK → Charlie")

            # 3. Centered Net Spend & Itemized Lists
            st.markdown("<hr style='border: 0.5px solid #eee; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:300; text-align:center; letter-spacing: 1px;'>NET SPEND PER PERSON</p>", unsafe_allow_html=True)
            
            usage = {m: 0.0 for m in members}
            user_items = {m: [] for m in members}
            for _, r in df.iterrows():
                p_list = str(r['Participants']).split(", ")
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: 
                    if p in usage: 
                        usage[p] += share
                        user_items[p].append(f"{r['Item']} ({share:,.0f})")
            
            # ตารางสรุปยอด (Center ในตัวตาราง)
            usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
            st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
            
            st.write("")
            
            # FIXED: จัดวาง Items แบบอยู่ตรงกลางรายบุคคล
            for m in members:
                st.markdown(f"""
                    <div class="centered-container">
                        <div class="member-name">{m}'s Items</div>
                        <div class="item-list-centered">
                            {' • ' + ' <br> • '.join(user_items[m]) if user_items[m] else 'No items'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
    else:
        st.info("No data.")
