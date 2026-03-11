import streamlit as st
import pandas as pd

# ข้อมูลการเชื่อมต่อ
SHEET_ID = '1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc'
# gid 0 คือหน้าแรก (มักจะเป็นค่าใช้จ่าย)
EXPENSE_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0'
# gid ที่คุณส่งมาคือหน้า Itinerary
PLAN_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=1784624804'

st.set_page_config(page_title="HK Trip 2026", page_icon="🇭🇰")

# แถบเมนูด้านข้าง
menu = st.sidebar.radio("เลือกรายการ", ["📍 แผนการเดินทาง", "💰 บันทึกค่าใช้จ่าย"])

if menu == "📍 แผนการเดินทาง":
    st.title("📍 Travel Plan")
    try:
        df_plan = pd.read_csv(PLAN_URL)
        # แสดงแผนแบ่งตามวัน
        for day in df_plan['Day'].unique():
            with st.expander(f"📅 วันที่ {day}", expanded=True):
                items = df_plan[df_plan['Day'] == day]
                for _, row in items.iterrows():
                    st.write(f"**{row['Time']}** : {row['Location']}")
                    if pd.notna(row['Note']):
                        st.caption(f"💬 {row['Note']}")
    except:
        st.info("จัดเตรียมข้อมูลในหน้า Itinerary (Day, Time, Location, Note) เพื่อแสดงผล")

elif menu == "💰 บันทึกค่าใช้จ่าย":
    st.title("💰 Expense Tracker")
    # ส่วนฟอร์มกรอกข้อมูล
    with st.form("add_expense"):
        item = st.text_input("รายการ")
        amount = st.number_input("ราคา (HKD)", min_value=0.0)
        payer = st.selectbox("ใครจ่าย?", ["คุณ", "เพื่อน A", "เพื่อน B"])
        if st.form_submit_button("บันทึก"):
            st.success(f"บันทึก {item} เรียบร้อย!")
    
    st.divider()
    # แสดงรายการจากหน้าแรกของ Sheet
    try:
        df_exp = pd.read_csv(EXPENSE_URL)
        st.subheader("รายการทั้งหมด")
        st.dataframe(df_exp, use_container_width=True)
    except:
        st.warning("ยังไม่มีข้อมูลค่าใช้จ่าย")
