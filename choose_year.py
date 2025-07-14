# choose_year.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

def def_year_choose(year):
    if st.button("📥Cập nhật danh sách năm tra cứu"):
        with st.spinner("Đang cập nhật danh sách năm ..."):
            url_take_year_check = 'https://www.scimagojr.com/journalrank.php'
            response_take_year = requests.get(url_take_year_check)
            soup = BeautifulSoup(response_take_year.content, 'html.parser')
            elements = soup.find_all('a', class_='dropdown-element')
            list_years = [element.text.strip() for element in elements if element.text.strip().isdigit()]
            years = sorted(list_years, reverse=True)[:5]
            if years:
                st.session_state['years'] = years
                #st.success(f"Đã tải được danh sách năm mới nhất gồm: {', '.join(years)}")
            else:
                st.warning("❌ Lỗi mạng, không tải được danh sách các năm, vui lòng tải lại trang")
                st.session_state['years'] = [str(year)]

    if 'years' in st.session_state and st.session_state['years']:
        years = st.session_state['years']

        selected_year = st.selectbox(
            "Chọn năm tra cứu, sau đó bấm nút **Xác nhận**",
            years,
            index=0
        )

        if st.button("Xác nhận"):
            st.session_state['year'] = int(selected_year)
            st.success(f"📌 Đã chọn năm {selected_year}")

        # Nếu chưa có key thì báo chưa chọn
        if 'year' in st.session_state:
            return st.session_state['year']
        else:
            st.warning("⚠️ Bạn chưa chọn năm tra cứu")
            return None

    else:
        #st.info("👉 Bấm nút **Tải danh sách 5 năm gần nhất** để lấy danh sách các năm")
        return "⚠️ Bạn chưa chọn năm tra cứu"
