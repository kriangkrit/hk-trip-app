import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="HK Trip 2026 🇭🇰",
    page_icon="🇭🇰",
    layout="centered"
)

# --- การเชื่อมต่อ Google Sheets ---
# มั่นใจว่าได้ตั้งค่า Secrets ใน Streamlit Cloud แล้ว
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ฟังก์ชันดึงข้อมูล ---
def get_data(worksheet_name):
    # ดึงข้อมูลจาก Tab ที่ระบุ (ชื่อ Sheet ใน Google Sheets)
    return conn.read(worksheet=worksheet_name, ttl=0)

# --- เมนู Sidebar ---
st.sidebar.title("📌 Menu")
menu = st.sidebar.radio("ไปที่หน้า:", ["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

# ---------------------------------------------------------
# หน้า: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
if menu == "💰 บันทึกค่าใช้จ่าย":
    st.title("💰 Expense Tracker")
    st.markdown("บันทึกค่าใช้จ่ายทริปฮ่องกง 2026")

    # ดึงข้อมูลปัจจุบันจาก Sheet ชื่อ "Sheet1" (หรือชื่อที่คุณตั้งไว้)
    existing_data = get_data("Sheet1")

    with st.form("expense_form", clear_on_submit=True):
        st.subheader("➕ เพิ่มรายการใหม่")
        col1, col2 = st.columns(2)
        
        with col1:
            item = st.text_input("รายการ", placeholder="เช่น ติ่มซำมื้อเช้า")
            amount = st.number_input("ราคา (HKD)", min_value=0.0, step=0.5)
        
        with col2:
            payer = st.selectbox("ใครจ่าย?", ["คุณ", "เพื่อน A", "เพื่อน B"])
            category = st.selectbox("หมวดหมู่", ["อาหาร", "เดินทาง", "ช้อปปิ้ง", "ที่พัก", "ทำบุญ/จิปาถะ"])
        
        participants = st.multiselect("หารกับใครบ้าง?", ["คุณ", "เพื่อน A", "เพื่อน B"], default=["คุณ", "เพื่อน A", "เพื่อน B"])
        
        submitted = st.form_submit_button("💾 บันทึกข้อมูล")

        if submitted:
            if item == "" or amount == 0:
                st.error("กรุณากรอกชื่อรายการและจำนวนเงิน")
            else:
                # เตรียมข้อมูลใหม่
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Item": item,
                    "Amount_HKD": amount,
                    "Payer": payer,
                    "Participants": ", ".join(participants),
                    "Category": category
                }])
                
                # อัปเดตข้อมูล
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"บันทึก '{item}' เรียบร้อยแล้ว!")
                st.rerun()

    st.divider()
    st.subheader("📝 รายการทั้งหมด")
    if not existing_data.empty:
        # แสดงตารางแบบย้อนหลัง (รายการล่าสุดอยู่บน)
        st.dataframe(existing_data.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลบันทึกไว้")

# ---------------------------------------------------------
# หน้า: แผนการเดินทาง
# ---------------------------------------------------------
elif menu == "📍 แผนการเดินทาง":
    st.title("📍 Travel Plan")
    st.markdown("ตารางเที่ยวฮ่องกง 5 วัดดัง และที่กินต่างๆ")
    
    try:
        # ดึงข้อมูลจากหน้า "Itinerary"
        df_plan = get_data("Itinerary")
        
        if not df_plan.empty:
            for day in df_plan['Day'].unique():
                with st.expander(f"📅 วันที่ {day}", expanded=True):
                    daily_items = df_plan[df_plan['Day'] == day]
                    for _, row in daily_items.iterrows():
                        st.write(f"⏰ **{row['Time']}** : {row['Location']}")
                        if 'Note' in row and pd.notna(row['Note']):
                            st.caption(f"ℹ️ {row['Note']}")
        else:
            st.warning("ไม่พบข้อมูลในหน้า Itinerary")
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลแผนการเดินทางได้: {e}")
        st.info("ตรวจสอบให้แน่ใจว่าชื่อ Sheet คือ 'Itinerary' และมีหัวตารางครบ")

# ---------------------------------------------------------
# หน้า: สรุปยอดรวม (Settlement)
# ---------------------------------------------------------
elif menu == "📊 สรุปยอดรวม":
    st.title("📊 Settlement Summary")
    
    df_exp = get_data("Sheet1")
    
    if not df_exp.empty:
        total_spent = df_exp['Amount_HKD'].sum()
        st.metric("ยอดรวมค่าใช้จ่ายทั้งหมด", f"{total_spent:,.2 False} HKD")
        
        # สรุปรายคน (เบื้องต้น)
        st.subheader("💰 สรุปการจ่ายเงิน")
        summary = df_exp.groupby('Payer')['Amount_HKD'].sum()
        st.bar_chart(summary)
        st.dataframe(summary)
    else:
        st.info("ยังไม่มีข้อมูลเพื่อคำนวณสรุปผล")
