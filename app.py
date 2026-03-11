import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    /* ใช้ Anuphan (ไทย) และ Montserrat (อังกฤษ) แบบบางพิเศษ */
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Anuphan', 'Montserrat', sans-serif; 
        color: #444;
        font-weight: 300;
    }

    h1, h2, h3 { 
        font-weight: 300 !important; 
        letter-spacing: 1px;
        color: #222;
    }

    /* ปุ่มมนและเส้นบาง */
    .stButton>button {
        border-radius: 12px;
        border: 0.5px solid #eee;
        background-color: #ffffff;
        font-weight: 300;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        border-color: #000; 
        color: #000;
        background-color: #fafafa;
    }

    /* ปรับแต่ง Input ให้คลีน (ซ่อนปุ่ม +/-) */
    button.step-up, button.step-down { display: none; }
    div[data-baseweb="input"] {
        border-radius: 8px;
        border: 0.5px solid #f0f0f0;
    }

    /* Metric (ยอดเงิน) แบบบาง */
    [data-testid="stMetricValue"] { 
        font-weight: 200 !important; 
        font-size: 2.2rem !important;
        letter-spacing: -1px;
    }
    
    /* ซ่อนเลข Index ในตาราง */
    [data-testid="stTable"] { font-weight: 300; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK Trip 2026")

tab1, tab2, tab3 = st.tabs(["Expense", "Plan", "Summary"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Accommodation", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย (Expense)
# ---------------------------------------------------------
with tab1:
    # 1. Add New
    with st.expander("➕ Add New", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g. Dim Sum")
            c1, c2 = st.columns(2)
            with c1: 
                # พิมพ์ตัวเลขได้เลย ไม่มีปุ่ม +/-
                amount = st.number_input("Amount (HKD)", min_value=1, value=None, step=1, placeholder="0")
            with c2: 
                payer = st.selectbox("Payer", members)
            
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            settled = st.checkbox("Pre-paid (Settled)")
            
            if st.form_submit_button("Save"):
                if item and amount and parts:
                    new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%y-%m-%d %H:%M"), "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    # 2. Edit (ครบทุกหมวดหมู่)
    if not df.empty:
        with st.expander("✏️ Edit"):
            list_edit = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_edit = st.selectbox("Select to edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Item Name", value=r['Item'])
                    e_amount = st.number_input("Amount", value=float(r['Amount_HKD']), step=1.0)
                    e_payer = st.selectbox("Payer", members, index=members.index(r['Payer']))
                    
                    curr_cat = r['Category'] if r['Category'] in categories else "Others"
                    e_cat = st.selectbox("Category", categories, index=categories.index(curr_cat))
                    
                    curr_parts = r['Participants'].split(", ")
                    e_parts = st.multiselect("Split with", members, default=[m for m in curr_parts if m in members])
                    e_settled = st.checkbox("Pre-paid", value=bool(r['Is_Settled']))
                    
                    if st.form_submit_button("Update"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Payer'] = e_item, e_amount, e_payer
                        df.at[idx, 'Category'], df.at[idx, 'Participants'], df.at[idx, 'Is_Settled'] = e_cat, ", ".join(e_parts), e_settled
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()

    # 3. Delete
    if not df.empty:
        with st.expander("🗑️ Delete"):
            sel_del = st.selectbox("Select to delete", ["-- Select --"] + [f"{i}: {r['Item']}" for i, r in df.iterrows()])
            if sel_del != "-- Select --" and st.button("Confirm Delete"):
                idx = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx).reset_index(drop=True))
                st.rerun()

    st.write("")
    st.dataframe(df.sort_index(ascending=False)[['Item', 'Amount_HKD', 'Payer', 'Category']], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: แผนการเดินทาง (Plan)
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            st.markdown(f"<p style='font-size:18px; font-weight:300; margin-top:15px;'>Day {day}</p>", unsafe_allow_html=True)
            for _, r in df_plan[df_plan['Day'] == day].iterrows():
                st.markdown(f"<p style='font-size:14px; color:#888; margin-bottom:2px;'>{r['Time']} — {r['Location']}</p>", unsafe_allow_html=True)
    except: st.info("Check 'Itinerary' tab in Sheets.")

# ---------------------------------------------------------
# TAB 3: สรุป (Summary)
# ---------------------------------------------------------
with tab3:
    rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
    
    if not df.empty:
        # Donut Chart แบบ Minimal
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Anuphan", size=12))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<p style='font-weight:300;'>Category Breakdown</p>", unsafe_allow_html=True)
        cat_table = cat_sum.copy()
        cat_table['THB'] = cat_table['Amount_HKD'] * rate
        st.table(cat_table.style.format({'Amount_HKD': '{:,.0f}', 'THB': '{:,.0f}'}))

        # Settlement (ยอดโอน)
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        df_unsettled = df[df['Is_Settled'] == False]
        bal = {m: 0.0 for m in members}
        for _, r in df_unsettled.iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = r['Participants'].split(", ")
            for p in p_list: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

        st.divider()
        c1, c2 = st.columns(2)
        diff = bal["KK"] # Positive: Charlie owes KK
        c1.metric("Transfer (HKD)", f"{abs(diff):,.2f}")
        c2.metric("Transfer (THB)", f"{abs(diff)*rate:,.0f}")
        
        if diff > 0.01: st.info(f"Charlie → KK")
        elif diff < -0.01: st.info(f"KK → Charlie")
        else: st.success("All settled!")

        # Net Spend (ยอดใช้จริงรายคน)
        st.write("")
        st.markdown("<p style='font-weight:300;'>Net Spend per Person</p>", unsafe_allow_html=True)
        usage = {m: 0.0 for m in members}
        for _, r in df.iterrows():
            p_list = r['Participants'].split(", ")
            for p in p_list: usage[p] += (float(r['Amount_HKD']) / len(p_list))
        
        usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
        st.table(usage_df.style.format({'HKD': '{:,.0f}', 'THB': '{:,.0f}'}))
