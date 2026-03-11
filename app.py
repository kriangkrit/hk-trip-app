import streamlit as st
import pandas as pd

# ใส่ ID ของ Google Sheets ของคุณตรงนี้
SHEET_ID = '1-X_your_google_sheet_id_here' 
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

st.title("🇭🇰 HK Trip Expense")

# ฟอร์มกรอกข้อมูล
with st.form("my_form"):
    item = st.text_input("รายการ")
    price = st.number_input("ราคา (HKD)")
    payer = st.selectbox("ใครจ่าย?", ["คุณ", "เพื่อน A", "เพื่อน B"])
    submitted = st.form_submit_button("บันทึก")
    
    if submitted:
        st.write(f"บันทึก {item} เรียบร้อย (รอเชื่อมต่อระบบเขียนข้อมูล)")

# แสดงตาราง
st.subheader("รายการที่บันทึกแล้ว")
try:
    df = pd.read_csv(SHEET_URL)
    st.dataframe(df)
except:
    st.warning("ยังไม่ได้ใส่ Sheet ID หรือไฟล์ไม่ได้เปิด Public ไว้")
