import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stButton>button {
        border-radius: 12px;
        border: 1px solid #f0f0f0;
        background-color: white;
        transition: all 0.3s;
    }
    .stButton>button:hover { border-color: #000; background-color: #fafafa; }
    
    button.step-up {display: none;}
    button.step-down {display: none;}
    div[data-baseweb="input"] > div > div {padding-right: 0;}
    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
    
    [data-testid="stMetricValue"] { font-weight: 300; letter-spacing: -1px; }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK Trip 2026")

tab1, tab2, tab3 = st.tabs(["💰 Expense", "📍 Plan", "📊 Summary"])
members = ["KK", "Charlie"]
# แยกหมวดหมู่ อาหาร และ เครื่องดื่ม ตามคำขอ
categories = ["อาหาร", "เครื่องดื่ม", "การเดินทาง", "ช้อปปิ้ง", "ที่พัก", "ตั๋วเครื่องบิน", "อื่น ๆ"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Is_Settled"])

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
with tab1:
    # 1. เพิ่มรายการใหม่
    with st.expander("➕ Add Expense", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("รายการ", placeholder="เช่น Dim Sum")
            c1, c2 = st.columns(2)
            with c1: 
                amount = st.number_input("ราคา (HKD)", min_value=1, value=None, step=1, placeholder="0")
            with c2: 
                payer = st.selectbox("ใครจ่าย?", members)
            
            cat = st.selectbox("หมวดหมู่", categories)
            parts = st.multiselect("หารกับใคร?", members, default=members)
            settled = st.checkbox("จ่ายจบไปแล้ว (Pre-paid)")
            
            if st.form_submit_button("Save Item"):
                if item and amount and parts:
                    new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    # 2. แก้ไขรายการ (เพิ่มหมวดหมู่ และปรับปรุงตามคำขอ)
    if not df.empty:
        with st.expander("✏️ Edit"):
            list_edit = [f"{i}: {row['Item']} ({row['Amount_HKD']})" for i, row in df.iterrows()]
            sel_edit = st.selectbox("เลือกรายการที่จะแก้", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("ชื่อรายการ", value=r['Item'])
                    e_amount = st.number_input("ราคา", value=float(r['Amount_HKD']), step=1.0)
                    e_payer = st.selectbox("คนจ่าย", members, index=members.index(r['Payer']))
                    
                    # เพิ่มส่วนแก้ไขหมวดหมู่ในหน้า Edit
                    current_cat = r['Category'] if r['Category'] in categories else "อื่น ๆ"
                    e_cat = st.selectbox("หมวดหมู่", categories, index=categories.index(current_cat))
                    
                    current_parts = r['Participants'].split(", ")
                    e_parts = st.multiselect("คนหาร", members, default=[m for m in current_parts if m in members])
                    e_settled = st.checkbox("จ่ายจบแล้ว", value=bool(r['Is_Settled']))
                    
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

    # 3. ลบรายการ
    if not df.empty:
        with st.expander("🗑️ Delete"):
            sel_del = st.selectbox("เลือกรายการที่จะลบ", ["-- Select --"] + [f"{i}: {r['Item']}" for i, r in df.iterrows()])
            if sel_del != "-- Select --" and st.button("Confirm Delete"):
                idx = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx).reset_index(drop=True))
                st.rerun()

    st.write("")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: Plan
# ---------------------------------------------------------
with tab2:
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0).dropna(subset=['Day', 'Location'], how='all')
        for day in df_plan['Day'].unique():
            st.markdown(f"**Day {day}**")
            for _, r in df_plan[df_plan['Day'] == day].iterrows():
                st.markdown(f"<p style='font-size:14px; color:#666;'>{r['Time']} — {r['Location']}</p>", unsafe_allow_html=True)
    except: st.info("Check Google Sheets 'Itinerary' tab.")

# ---------------------------------------------------------
# TAB 3: Summary
# ---------------------------------------------------------
with tab3:
    rate = st.number_input("Rate (1 HKD = ? THB)", value=4.5, step=0.01)
    
    if not df.empty:
        cat_sum = df.groupby('Category')['Amount_HKD'].sum().reset_index()
        fig = px.pie(cat_sum, values='Amount_HKD', names='Category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Category Breakdown**")
        cat_table = cat_sum.copy()
        cat_table['THB'] = cat_table['Amount_HKD'] * rate
        st.table(cat_table.style.format({'Amount_HKD': '{:,.0f}', 'THB': '{:,.0f}'}))

        df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
        df_unsettled = df[df['Is_Settled'] == False]
        bal = {m: 0.0 for m in members}
        for _, r in df_unsettled.iterrows():
            bal[r['Payer']] += float(r['Amount_HKD'])
            p_list = r['Participants'].split(", ")
            for p in p_list: bal[p] -= (float(r['Amount_HKD']) / len(p_list))

        st.write("---")
        c1, c2 = st.columns(2)
        diff = bal["KK"]
        c1.metric("Transfer (HKD)", f"{abs(diff):,.2f}")
        c2.metric("Transfer (THB)", f"{abs(diff)*rate:,.0f}")
        
        if diff > 0.01: st.info(f"Charlie → KK")
        elif diff < -0.01: st.info(f"KK → Charlie")

        st.write("")
        st.markdown("**Net Spend per Person (Total)**")
        usage = {m: 0.0 for m in members}
        for _, r in df.iterrows():
            p_list = r['Participants'].split(", ")
            for p in p_list: usage[p] += (float(r['Amount_HKD']) / len(p_list))
        
        usage_df = pd.DataFrame([{"Name": m, "HKD": usage[m], "THB": usage[m]*rate} for m in members])
        st.table(usage_df.style.format({'HKD': '{:,.0f}', 'THB': '{:,.0f}'}))
