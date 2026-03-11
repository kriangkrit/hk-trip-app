import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    /* เลือกฟอนต์ Montserrat สำหรับความ Minimal ที่ดูพรีเมียม */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Montserrat', sans-serif; 
        color: #444;
    }

    /* ปรับหัวข้อให้บางและกว้างขึ้น */
    h1, h2, h3 { 
        font-weight: 200 !important; 
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ปรับแต่งปุ่มให้มนและโปร่งแสง */
    .stButton>button {
        border-radius: 8px;
        border: 0.5px solid #eee;
        background-color: #ffffff;
        font-weight: 300;
        letter-spacing: 1px;
        transition: all 0.4s ease;
    }
    .stButton>button:hover { 
        border-color: #000; 
        background-color: #000; 
        color: #fff;
    }

    /* ซ่อนปุ่ม +/- และปรับแต่งช่อง Input ให้เรียบที่สุด */
    button.step-up, button.step-down { display: none; }
    div[data-baseweb="input"] {
        border-radius: 0px;
        border-bottom: 1px solid #eee;
        background-color: transparent !important;
    }
    
    /* ปรับแต่ง Metric (ตัวเลขสรุปเงิน) */
    [data-testid="stMetricValue"] { 
        font-weight: 200 !important; 
        font-size: 2.5rem !important;
        color: #222;
    }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK Trip 2026")

tab1, tab2, tab3 = st.tabs(["💰 Expense", "📍 Plan", "📊 Summary"])
members = ["KK", "Charlie"]
# Categories in English
categories = ["Food", "Drinks", "Transport", "Shopping", "Accommodation", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# ---------------------------------------------------------
# TAB 1: Expense Tracking
# ---------------------------------------------------------
with tab1:
    # 1. Add New Expense
    with st.expander("➕ Add Expense", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g., Dim Sum")
            c1, c2 = st.columns(2)
            with c1: 
                amount = st.number_input("Amount (HKD)", min_value=1, value=None, step=1, placeholder="0")
            with c2: 
                payer = st.selectbox("Who paid?", members)
            
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            settled = st.checkbox("Pre-paid (Exclude from Transfer)")
            
            if st.form_submit_button("Save Item"):
                if item and amount and parts:
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "Item": item, 
                        "Amount_HKD": float(amount), 
                        "Payer": payer, 
                        "Participants": ", ".join(parts), 
                        "Category": cat, 
                        "Is_Settled": settled
                    }])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.success("Saved!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")

    # 2. Edit Expense
    if not df.empty:
        with st.expander("✏️ Edit"):
            list_edit = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_edit = st.selectbox("Select item to edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Item Name", value=r['Item'])
                    e_amount = st.number_input("Amount", value=float(r['Amount_HKD']), step=1.0)
                    e_payer = st.selectbox("Payer", members, index=members.index(r['Payer']))
                    
                    current_cat = r['Category'] if r['Category'] in categories else "Others"
                    e_cat = st.selectbox("Category", categories, index=categories.index(current_cat))
                    
                    current_parts = r['Participants'].split(", ")
                    e_parts = st.multiselect("Split with", members, default=[m for m in current_parts if m in members])
                    e_settled = st.checkbox("Pre-paid", value=bool(r['Is_Settled']))
                    
                    if st.form_submit_button("Update"):
                        df.at[idx, 'Item'] = e_item
                        df.at[idx, 'Amount_HKD'] = e_amount
                        df.at[idx, 'Payer'] = e_payer
                        df.at[idx, 'Category'] = e_cat
                        df.at[idx, 'Participants'] = ", ".join(e_parts)
                        df.at[idx, 'Is_Settled'] = e_settled
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.success("Updated!")
                        st.rerun()

    # 3. Delete Expense
    if not df.empty:
        with st.expander("🗑️ Delete"):
            sel_del = st.selectbox("Select item to delete", ["-- Select --"] + [f"{i}: {r['Item']}" for i, r in df.iterrows()])
            if sel_del != "-- Select --" and st.button("Confirm Delete"):
                idx = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx).reset_index(drop=True))
                st.rerun()

    st.write("")
    # Display recent items on top
    st.dataframe(df.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: Plan (Itinerary)
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        if not df_plan.empty:
            for day in df_plan['Day'].unique():
                st.markdown(f"**Day {day}**")
                day_items = df_plan[df_plan['Day'] == day]
                for _, r in day_items.iterrows():
                    st.markdown(f"<p style='font-size:14px; color:#666;'>{r['Time']} — {r['Location']}</p>", unsafe_allow_html=True)
        else:
            st.info("No plan data found in Google Sheets.")
    except: st.info("Check Google Sheets 'Itinerary' tab.")

# ---------------------------------------------------------
# TAB 3: Summary & Settlement
# ---------------------------------------------------------
with tab3:
    st.subheader("Financial Overview")
    rate = st.number_input("Exchange Rate (1 HKD = ? THB)", value=4.5, step=0.01)
    
    if not df.empty:
        # Chart
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

        # Category Table
        st.markdown("**Category Breakdown**")
        cat_table = cat_sum.copy()
        cat_table['THB'] = cat_table['Amount_HKD'] * rate
        cat_table.columns = ['Category', 'HKD', 'THB']
        st.table(cat_table.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))

        # Transfer Calculation
        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        df_unsettled = df[df['Is_Settled'] == False]
        bal = {m: 0.0 for m in members}
        for _, r in df_unsettled.iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = r['Participants'].split(", ")
            for p in p_list: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

        st.divider()
        st.write("### 💸 Transfer")
        diff = bal["KK"] # Positive: Charlie pays KK
        
        c1, c2 = st.columns(2)
        c1.metric("HKD", f"{abs(diff):,.2f}")
        c2.metric("THB", f"{abs(diff)*rate:,.0f}")
        
        if diff > 0.01: 
            st.info(f"Charlie → KK")
        elif diff < -0.01: 
            st.info(f"KK → Charlie")
        else:
            st.success("All settled!")

        # Net Spend Summary
        st.write("")
        st.markdown("**Net Spend per Person (Everything Included)**")
        usage = {m: 0.0 for m in members}
        for _, r in df.iterrows():
            p_list = r['Participants'].split(", ")
            for p in p_list: usage[p] += (float(r['Amount_HKD']) / len(p_list))
        
        usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
        st.table(usage_df.style.format({'HKD': '{:,.2f}', 'THB': '{:,.2f}'}))
    else:
        st.info("No expense data recorded yet.")
