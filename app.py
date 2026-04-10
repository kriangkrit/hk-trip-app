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

    /* ซ่อน UI ส่วนเกินของ Streamlit */
    summary > span > div > div { font-size: 0 !important; visibility: hidden !important; }
    summary > span > div > div > p { font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }
    svg[data-testid="stExpanderIcon"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }

    /* หัวข้อหลัก */
    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    
    /* สไตล์ปุ่มและ Input */
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; transition: 0.3s; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }
    [data-testid="stMetricValue"] { font-weight: 200 !important; font-size: 1.8rem !important; }
    
    /* --- Styles สำหรับหน้า PLAN (Timeline) --- */
    .day-header {
        background-color: #333;
        color: white;
        padding: 5px 15px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 400;
        display: inline-block;
        margin: 25px 0 15px 0;
        letter-spacing: 1px;
    }
    .plan-card {
        background-color: #ffffff;
        border-left: 2px solid #eee;
        padding: 0 0 20px 20px;
        margin-left: 10px;
        position: relative;
    }
    .plan-card::before {
        content: '';
        position: absolute;
        left: -5px;
        top: 0;
        width: 8px;
        height: 8px;
        background-color: #333;
        border-radius: 50%;
    }
    .time-text {
        font-size: 11px;
        font-weight: 600;
        color: #999;
        margin-bottom: 2px;
        text-transform: uppercase;
    }
    .location-text {
        font-size: 15px;
        color: #222;
        line-height: 1.4;
    }

    /* --- Styles สำหรับหน้า SUMMARY (Mobile Flex) --- */
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
        min-width: 0;
    }
    .member-label { 
        font-size: 11px; 
        font-weight: 400; 
        color: #222; 
        margin-bottom: 5px; 
        border-bottom: 0.5px solid #eee; 
        display: inline-block; 
        padding: 0 5px 1px 5px; 
        white-space: nowrap;
    }
    .item-text-centered { 
        font-size: 10px; 
        color: #999; 
        line-height: 1.4; 
        overflow-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK TRIP 2026")
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
            item = st.text_input("Item", placeholder="e.g. Dim Sum")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0.0, value=None, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note (Optional)", placeholder="เพิ่มเติม...")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount is not None:
                    now_full = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now_full, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": note, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    if not df.empty:
        with st.expander("EDIT"):
            list_edit = [f"{i}: {r['Item']}" for i, r in df.iterrows()]
            sel_edit = st.selectbox("Select Item to Edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Name", value=r['Item'])
                    e_amount = st.number_input("Price", value=float(r['Amount_HKD']))
                    e_cat = st.selectbox("Category", categories, index=categories.index(r['Category']) if r['Category'] in categories else 0)
                    e_note = st.text_input("Note", value=r['Note'] if pd.notna(r['Note']) else "")
                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Category'], df.at[idx, 'Note'] = e_item, e_amount, e_cat, e_note
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df); st.rerun()

        with st.expander("DELETE"):
            list_del = [f"{i}: {r_del['Item']}" for i, r_del in df.iterrows()]
            sel_del = st.selectbox("Choose item to remove", ["-- Select --"] + list_del)
            if sel_del != "-- Select --" and st.button("CONFIRM DELETE", use_container_width=True):
                idx_to_del = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx_to_del).reset_index(drop=True))
                st.rerun()

        st.write("")
        display_df = df.copy()
        display_df['Date'] = display_df['Timestamp'].str.split().str[0]
        final_df = display_df.sort_index(ascending=False)[['Date', 'Item', 'Amount_HKD', 'Payer', 'Category', 'Note']]
        st.dataframe(final_df, use_container_width=True, hide_index=True)

# --- TAB 2: PLAN (New Design: Timeline Cards) ---
with tab2:
    try:
        # ดึงข้อมูลจากแผ่นงาน Itinerary
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="Itinerary", ttl=0)
        df_plan = df_plan.dropna(subset=['Day', 'Location'], how='all')
        
        if df_plan.empty:
            st.info("No plan data found.")
        else:
            for day in df_plan['Day'].unique():
                # แสดงหัวข้อวันแบบ Badge
                st.markdown(f"<div class='day-header'>DAY {day}</div>", unsafe_allow_html=True)
                
                day_data = df_plan[df_plan['Day'] == day]
                for _, r in day_data.iterrows():
                    time_val = r['Time'] if pd.notna(r['Time']) else ""
                    loc_val = r['Location'] if pd.notna(r['Location']) else ""
                    
                    # แสดงกิจกรรมแบบ Timeline Card
                    st.markdown(f"""
                        <div class="plan-card">
                            <div class="time-text">{time_val}</div>
                            <div class="location-text">{loc_val}</div>
                        </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading Itinerary: {e}")

# --- TAB 3: SUMMARY ---
with tab3:
    if not df.empty and df['Amount_HKD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        cat_sum = cat_sum[cat_sum['Amount_HKD'] > 0]
        if not cat_sum.empty:
            fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=10, r=10), font=dict(family="Anuphan", size=14))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<p style='font-weight:300;'>CATEGORY</p>", unsafe_allow_html=True)
            st.table(cat_sum.style.format({'Amount_HKD': '{:,.0f}'}))
            st.divider()

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

            st.markdown("<hr style='border: 0.5px solid #eee; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:300;'>NET SPEND PER PERSON</p>", unsafe_allow_html=True)
            
            usage = {m: 0.0 for m in members}
            user_items = {m: [] for m in members}
            for _, r in df.iterrows():
                p_list = str(r['Participants']).split(", ")
                share = float(r['Amount_HKD']) / len(p_list)
                for p in p_list: 
                    if p in usage: 
                        usage[p] += share
                        user_items[p].append(f"{r['Item']} ({share:,.0f})")
            
            usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
            st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
            
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
