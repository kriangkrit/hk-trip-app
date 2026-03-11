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
    
    try:
        existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        existing_data = existing_data.dropna(how='all')
    except Exception as e:
        existing_data = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category"])

    # ฟอร์มบันทึกข้อมูล
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("➕ เพิ่มรายการใหม่")
        col1, col2 = st.columns(2)
        with col1:
            item = st.text_input("รายการ")
            amount = st.number_input("ราคา (HKD)", min_value=0.0, step=0.5)
        with col2:
            payer = st.selectbox("ใครจ่าย?", ["คุณ", "เพื่อน A", "เพื่อน B"])
            category = st.selectbox("หมวดหมู่", ["อาหาร", "เดินทาง", "ช้อปปิ้ง", "ที่พัก", "ทำบุญ/จิปาถะ"])
        
        participants = st.multiselect("หารกับใครบ้าง?", ["คุณ", "เพื่อน A", "เพื่อน B"], default=["คุณ", "เพื่อน A", "เพื่อน B"])
        
        if st.form_submit_button("💾 บันทึกข้อมูล"):
            if item and amount > 0:
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Item": item,
                    "Amount_HKD": amount,
                    "Payer": payer,
                    "Participants": ", ".join(participants),
                    "Category": category
                }])
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                st.success(f"บันทึก {item} เรียบร้อย!")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลให้ครบ")

    st.divider()
    
    # --- ส่วนการแสดงผลและ "เลือกลบ" ---
    st.subheader("📝 รายการทั้งหมด")
    if not existing_data.empty:
        # แสดงตารางพร้อมเลข Index เพื่อให้เลือกง่าย
        st.dataframe(existing_data, use_container_width=True)
        
        st.subheader("🗑️ ลบรายการที่ระบุ")
        # สร้าง List ของรายการให้เพื่อนเลือก (เอา Index มาบวกกับชื่อรายการ)
        list_to_delete = [f"{i}: {row['Item']} ({row['Amount_HKD']} HKD)" for i, row in existing_data.iterrows()]
        
        selected_item = st.selectbox("เลือกรายการที่จะลบ:", ["-- เลือกรายการ --"] + list_to_delete)
        
        if selected_item != "-- เลือกรายการ --":
            # ดึงเลข Index กลับมา
            index_to_delete = int(selected_item.split(":")[0])
            
            if st.button("❌ ยืนยันการลบรายการนี้"):
                # ลบแถวที่เลือก
                updated_df = existing_data.drop(index_to_delete).reset_index(drop=True)
                # อัปเดตกลับไปที่ Sheet
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                st.warning(f"ลบรายการ '{selected_item}' เรียบร้อยแล้ว")
                st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลบันทึกไว้")

# (ส่วนหน้าอื่นๆ เหมือนเดิม...)
elif menu == "📍 แผนการเดินทาง":
    st.title("📍 Travel Plan")
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0)
        if not df_plan.empty:
            for day in df_plan['Day'].unique():
                with st.expander(f"📅 วันที่ {day}", expanded=True):
                    items = df_plan[df_plan['Day'] == day]
                    for _, row in items.iterrows():
                        st.write(f"⏰ **{row['Time']}** : {row['Location']}")
    except: st.error("ไม่พบหน้า Itinerary")

elif menu == "📊 สรุปยอดรวม":
    st.title("📊 Settlement Summary")
    try:
        df_exp = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        if not df_exp.empty:
            st.metric("ยอดรวม", f"{df_exp['Amount_HKD'].sum():,.2f} HKD")
            st.bar_chart(df_exp.groupby('Payer')['Amount_HKD'].sum())
    except: st.info("ยังไม่มีข้อมูล")
