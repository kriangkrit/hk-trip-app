import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Config & Theme ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

# Custom CSS for Minimalism
st.markdown("""
    <style>
    .main { background-color: #fafafa; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; background-color: transparent !important; }
    .stButton>button { border-radius: 20px; border: 1px solid #ddd; background-color: white; color: #333; }
    .stButton>button:hover { border-color: #000; color: #000; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 300; }
    h1, h2, h3 { font-weight: 300 !important; letter-spacing: -0.5px; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK Trip 2026")

tab1, tab2, tab3 = st.tabs(["Expense", "Plan", "Summary"])
members = ["KK", "Charlie"]

# --- Load Data ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
with tab1:
    with st.expander("✨ Add New", expanded=False):
        with st.form("expense_form", clear_on_submit=True):
            item = st.text_input("What?", placeholder="Item name")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Amount (HKD)", min_value=0.0, step=1.0)
            with c2: payer = st.selectbox("Who paid?", members)
            
            cat = st.selectbox("Category", ["อาหาร", "เดินทาง", "ที่พัก", "ช้อปปิ้ง", "อื่น ๆ"])
            parts = st.multiselect("Split with", members, default=members)
            settled = st.checkbox("Settled (Pre-paid)")
            
            if st.form_submit_button("Add Item"):
                if item and amount > 0:
                    new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%y-%m-%d %H:%M"), "Item": item, "Amount_HKD": amount, "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    # Data Display (Minimal Table)
    if not df.empty:
        st.write("---")
        display_df = df.sort_index(ascending=False)[['Item', 'Amount_HKD', 'Payer', 'Category']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Edit/Delete in one minimal line
        with st.expander("Edit / Delete"):
            choice = st.selectbox("Select Item", df.index, format_func=lambda x: f"{df.iloc[x]['Item']} ({df.iloc[x]['Amount_HKD']})")
            c_edit, c_del = st.columns(2)
            if c_del.button("Delete Forever", use_container_width=True):
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(choice).reset_index(drop=True))
                st.rerun()
            st.caption("To edit, please use the Google Sheet directly or delete & re-add for now.")

# ---------------------------------------------------------
# TAB 2: Plan
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            st.markdown(f"**Day {day}**")
            for _, r in df_plan[df_plan['Day'] == day].iterrows():
                st.markdown(f"<small>{r['Time']} — {r['Location']}</small>", unsafe_allow_html=True)
            st.write("")
    except: st.info("No plan data found.")

# ---------------------------------------------------------
# TAB 3: Summary
# ---------------------------------------------------------
with tab3:
    rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
    
    if not df.empty:
        # Chart
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

        # Settlement
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        df_unsettled = df[df['Is_Settled'] == False]
        
        bal = {m: 0.0 for m in members}
        for _, r in df_unsettled.iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = r['Participants'].split(", ")
            for p in p_list: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

        diff = bal["KK"] # If positive, Charlie owes KK
        st.write("---")
        c1, c2 = st.columns(2)
        c1.metric("Transfer (HKD)", f"{abs(diff):,.2f}")
        c2.metric("Transfer (THB)", f"{abs(diff)*rate:,.2f}")
        
        if diff > 0.01: st.text(f"Charlie → KK")
        elif diff < -0.01: st.text(f"KK → Charlie")
        else: st.text("All settled!")

        # Net Usage
        st.write("")
        st.markdown("**Net Spend per Person**")
        usage = {m: 0.0 for m in members}
        for _, r in df.iterrows():
            p_list = r['Participants'].split(", ")
            for p in p_list: usage[p] += (float(r['Amount_HKD']) / len(p_list))
        
        for m in members:
            st.write(f"<small>{m}: {usage[m]:,.0f} HKD ({usage[m]*rate:,.0f} THB)</small>", unsafe_allow_html=True)
