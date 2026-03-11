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
# ใช้ URL ของคุณ
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_lDyCMogHXKLfSetDj8QzejELtAIB4CQ6xk1LrBSZGc/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- เมนู Sidebar ---
st.sidebar.title("📌 Menu")
menu = st.sidebar.radio("ไปที่หน้า:", ["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

# ---------------------------------------------------------
# หน้า: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
if menu == "💰 บันทึกค่าใช้จ่าย":
    st.title("💰 Expense Tracker")
    
    # 1. ดึงข้อมูลจาก Google Sheets (หน้าแรก Index 0)
    try:
        existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        # กรองแถวที่ว่างทิ้ง
        existing_data = existing_data.dropna(how='all')
    except Exception as e:
        existing_data = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category"])

    # 2. ฟอร์มสำหรับกรอกข้อมูลใหม่
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
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Item": item,
                    "Amount_HKD": amount,
                    "Payer": payer,
                    "Participants": ", ".join(participants),
                    "Category": category
                }])
                
                # รวมข้อมูลเก่าและใหม่
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                
                # บันทึกลง Google Sheets
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                
                st.success(f"บันทึก '{item}' เรียบร้อยแล้ว!")
                st.rerun()

    st.divider()
    
    # 3. ส่วนการแสดงผลตารางและการลบข้อมูล
    st.subheader("📝 รายการทั้งหมด")
    if not existing_data.empty:
        st.dataframe(existing_data.sort_index(ascending=False), use_container_width=True)
        
        # ปุ่มสำหรับลบข้อมูล
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("🗑️ ลบรายการล่าสุด"):
                updated_df = existing_data.drop(existing_data.index[-1])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                st.warning("ลบรายการล่าสุดเรียบร้อย!")
                st.rerun()
        
        with col_del2:
            # เพิ่มปุ่ม Reset เผื่ออยากลบทั้งหมด (ต้องกดยืนยัน)
            if st.checkbox("ยืนยันเพื่อล้างข้อมูลทั้งหมด"):
                if st.button("🔥 ล้างข้อมูลทั้งหมด"):
                    empty_df = pd.DataFrame(columns=existing_data.columns)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=empty_df)
                    st.error("ล้างข้อมูลทั้งหมดเรียบร้อย!")
                    st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลบันทึกไว้")

# ---------------------------------------------------------
# หน้า: แผนการเดินทาง
# ---------------------------------------------------------
elif menu == "📍 แผนการเดินทาง":
    st.title("📍 Travel Plan")
    
    try:
        # ดึงข้อมูลจากหน้า Itinerary (gid=1784624804)
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0)
        
        if not df_plan.empty:
            df_plan = df_plan.dropna(subset=['Day', 'Location'], how='all')
            for day in df_plan['Day'].unique():
                with st.expander(f"📅 วันที่ {day}", expanded=True):
                    daily_items = df_plan[df_plan['Day'] == day]
                    for _, row in daily_items.iterrows():
                        st.write(f"⏰ **{row['Time']}** : {row['Location']}")
                        if 'Note' in row and pd.notna(row['Note']):
                            st.caption(f"ℹ️ {row['Note']}")
        else:
            st.warning("ยังไม่มีข้อมูลในหน้า Itinerary")
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")

# ---------------------------------------------------------
# หน้า: สรุปยอดรวม
# ---------------------------------------------------------
elif menu == "📊 สรุปยอดรวม":
    st.title("📊 Settlement Summary")
    
    try:
        df_exp = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        df_exp = df_exp.dropna(subset=['Amount_HKD'])
        
        if not df_exp.empty:
            total_spent = df_exp['Amount_HKD'].sum()
            st.metric("ยอดรวมค่าใช้จ่ายทั้งหมด", f"{total_spent:,.2f} HKD")
            
            # กราฟแท่งสรุปรายคน
            st.subheader("💰 สรุปการจ่ายเงินแยกรายคน")
            summary = df_exp.groupby('Payer')['Amount_HKD'].sum()
            st.bar_chart(summary)
            
            # ตารางสรุป
            st.dataframe(summary)
            
            st.info("💡 ทริค: คุณสามารถเปิด Google Sheets เพื่อคำนวณการหารเงินที่ละเอียดกว่านี้ได้")
        else:
            st.info("ยังไม่มีข้อมูลค่าใช้จ่ายเพื่อคำนวณ")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
