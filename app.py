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

# --- ส่วนหัวของแอป ---
st.title("🇭🇰 Hong Kong Trip 2026")
st.markdown("ศูนย์รวมข้อมูลการเดินทางและค่าใช้จ่าย")

# --- สร้าง Tabs แทน Sidebar ---
tab1, tab2, tab3 = st.tabs(["💰 บันทึกค่าใช้จ่าย", "📍 แผนการเดินทาง", "📊 สรุปยอดรวม"])

# ---------------------------------------------------------
# TAB 1: บันทึกค่าใช้จ่าย
# ---------------------------------------------------------
with tab1:
    st.subheader("💰 Expense Tracker")
    
    try:
        existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        existing_data = existing_data.dropna(how='all')
    except Exception as e:
        existing_data = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category"])

    # ฟอร์มบันทึกข้อมูล
    with st.expander("➕ เพิ่มรายการใหม่", expanded=True):
        with st.form("expense_form", clear_on_submit=True):
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
    
    # รายการทั้งหมดและระบบเลือกลบ
    st.subheader("📝 รายการทั้งหมด")
    if not existing_data.empty:
        st.dataframe(existing_data, use_container_width=True)
        
        with st.expander("🗑️ ลบรายการ"):
            list_to_delete = [f"{i}: {row['Item']} ({row['Amount_HKD']} HKD)" for i, row in existing_data.iterrows()]
            selected_item = st.selectbox("เลือกรายการที่จะลบ:", ["-- เลือกรายการ --"] + list_to_delete)
            
            if selected_item != "-- เลือกรายการ --":
                index_to_delete = int(selected_item.split(":")[0])
                if st.button("❌ ยืนยันการลบ"):
                    updated_df = existing_data.drop(index_to_delete).reset_index(drop=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=updated_df)
                    st.warning("ลบเรียบร้อย!")
                    st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลบันทึกไว้")

# ---------------------------------------------------------
# TAB 2: แผนการเดินทาง
# ---------------------------------------------------------
with tab2:
    st.subheader("📍 Itinerary")
    try:
        df_plan = conn.read(spreadsheet=SHEET_URL, worksheet="1784624804", ttl=0)
        if not df_plan.empty:
            df_plan = df_plan.dropna(subset=['Day', 'Location'], how='all')
            for day in df_plan['Day'].unique():
                with st.expander(f"📅 วันที่ {day}", expanded=True):
                    items = df_plan[df_plan['Day'] == day]
                    for _, row in items.iterrows():
                        st.write(f"⏰ **{row['Time']}** : {row['Location']}")
                        if 'Note' in row and pd.notna(row['Note']):
                            st.caption(f"ℹ️ {row['Note']}")
        else:
            st.info("จัดเตรียมข้อมูลในหน้า Itinerary")
    except:
        st.error("ไม่พบข้อมูลแผนการเดินทาง")

# ---------------------------------------------------------
# TAB 3: สรุปยอดรวม
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 Summary")
    try:
        df_exp = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0)
        if not df_exp.empty:
            df_exp = df_exp.dropna(subset=['Amount_HKD'])
            total_spent = df_exp['Amount_HKD'].sum()
            st.metric("ยอดรวมค่าใช้จ่าย", f"{total_spent:,.2f} HKD")
            
            st.write("💰 **จ่ายไปแล้วเท่าไหร่:**")
            summary = df_exp.groupby('Payer')['Amount_HKD'].sum()
            st.bar_chart(summary)
            st.table(summary)
        else:
            st.info("ไม่มีข้อมูลสรุป")
    except:
        st.error("เกิดข้อผิดพลาดในการคำนวณ")
