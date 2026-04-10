# --- TAB 1: EXPENSE ---
with tab1:
    # --- ADD NEW (Minimalist Style) ---
    st.markdown("<div style='margin-top: 1rem; margin-bottom: 1rem; font-size: 14px; letter-spacing: 1px; color: #888;'>NEW ENTRY</div>", unsafe_allow_html=True)
    
    with st.form("add_form", clear_on_submit=True):
        # แถวแรก: ชื่อรายการ
        item = st.text_input("What did you buy?", placeholder="e.g. Dim Sum")
        
        # แถวที่สอง: ราคา และ ใครจ่าย (หารครึ่งคอลัมน์)
        c1, c2 = st.columns(2)
        with c1: 
            amount = st.number_input("Price (HKD)", min_value=0.0, step=1.0, format="%.0f")
        with c2: 
            payer = st.selectbox("Payer", members)
            
        # แถวที่สาม: หมวดหมู่ และ ใครหารบ้าง
        c3, c4 = st.columns(2)
        with c3:
            cat = st.selectbox("Category", categories)
        with c4:
            parts = st.multiselect("Split", members, default=members)
            
        # แถวสุดท้าย: Note เล็กๆ และ Checkbox แบบประหยัดพื้นที่
        note = st.text_input("Note", placeholder="Optional details...")
        settled = st.checkbox("Pre-paid (Settled)")
        
        # ปุ่มกดที่ดูสะอาด
        submit = st.form_submit_button("SAVE")
        
        if submit:
            if item and amount >= 0:
                now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                new_data = pd.DataFrame([{"Timestamp": now, "Item": str(item), "Amount_HKD": float(amount), "Payer": str(payer), "Participants": ", ".join(parts), "Category": str(cat), "Is_Settled": bool(settled), "Note": str(note)}])
                df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                st.rerun()

    # --- EDIT / DELETE (Minimalist Expander) ---
    if not df.empty:
        with st.expander("MANAGE"):
            # ... (โค้ดส่วน Edit/Delete เดิมของคุณ) ...
