import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================
# Helper
# ========================

def clear_format(text):
    text = re.sub(r'\W+', ' ', text)
    return ' '.join(text.lower().split())

# ========================
# Hàm rank_h_q
# ========================

def check_rank_by_h_q(total_journals, percent, sjr_quartile):
        # Xác định rank_h dựa trên total_journals và Percent
        if total_journals >= 2000:
            thresholds = [0.5, 1, 5, 10, 18, 30, 43, 56, 69, 82]
        elif 1500 <= total_journals <= 1999:
            thresholds = [0.5, 2, 6, 11, 19, 31, 44, 57, 70, 83]
        elif 1000 <= total_journals <= 1499:
            thresholds = [0.5, 3, 7, 12, 20, 32, 45, 58, 71, 84]
        elif 500 <= total_journals <= 999:
            thresholds = [0.5, 4, 8, 13, 21, 33, 46, 59, 72, 85]
        elif 200 <= total_journals <= 499:
            thresholds = [0.9, 5, 10, 15, 23, 35, 48, 61, 74, 87]
        elif 50 <= total_journals <= 199:
            thresholds = [2.5, 6, 11, 16, 24, 36, 49, 62, 75, 88]
        elif 0 < total_journals < 50:
            thresholds = [3.5, 7, 15, 20, 28, 40, 53, 66, 79, 92]
        else:
            return 'None', 'None', 'Lỗi trong thống kê số lượng tạp chí'
        rank_h = next((i for i, th in enumerate(thresholds, start=0) if percent < th), 10)
        if rank_h < len(thresholds):
            Top_Percent = '< ' + str(thresholds[rank_h])
        else:
            Top_Percent = '>= ' + str(thresholds[-1])
        if (rank_h == 0) and (sjr_quartile == 'Q1'):
            return 'Ngoại hạng chuyên ngành', Top_Percent, ''
        elif (rank_h == 1) and  (sjr_quartile == 'Q1'):
            return 'Hạng 1', Top_Percent, ''
        elif (rank_h == 2) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2'):
            return 'Hạng 2', Top_Percent, ''
        elif (rank_h == 3) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2'):
            return 'Hạng 3', Top_Percent, ''
        elif (rank_h == 4) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2'):
            return 'Hạng 4', Top_Percent, ''
        elif (rank_h == 5) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3'):
            return 'Hạng 5', Top_Percent, ''
        elif (rank_h == 6) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3'):
            return 'Hạng 6', Top_Percent, ''
        elif (rank_h == 7) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3'):
            return 'Hạng 7', Top_Percent, ''
        elif (rank_h == 8) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3'):
            return 'Hạng 8', Top_Percent, ''
        elif (rank_h == 9) and  (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3' or sjr_quartile == 'Q4'):
            return 'Hạng 9', Top_Percent, ''
        elif (rank_h == 10) and (sjr_quartile == 'Q1' or sjr_quartile == 'Q2' or sjr_quartile == 'Q3' or sjr_quartile == 'Q4'):
            return 'Hạng 10', Top_Percent, ''
        elif (0 <= rank_h <= 1) and (sjr_quartile == 'Q2'):
            return f'Hạng 2', Top_Percent, f"Rớt từ Hạng {rank_h} vì Q2"
        elif (0 <= rank_h <= 4) and (sjr_quartile == 'Q3'):
            return f'Hạng 5', Top_Percent, f"Rớt từ Hạng {rank_h} vì Q3"
        elif (0 <= rank_h <= 8) and (sjr_quartile == 'Q4'):
            return f'Hạng 9', Top_Percent, f"Rớt từ Hạng {rank_h} vì Q4"
        else:
            return 'Không xếp hạng', Top_Percent, 'Không có Q'

# ========================
# Crawler gốc
# ========================

def find_title_or_issn(name_or_issn):
    url = f"https://www.scimagojr.com/journalsearch.php?q={name_or_issn}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = []
    STT = 0
    for link in soup.find_all('a', href=True):
        if 'journalsearch.php?q=' in link['href']:
            title_journal = link.find('span', class_='jrnlname').text
            id_scopus_journal = link['href'].split('q=')[1].split('&')[0]
            detail_url = f"https://www.scimagojr.com/journalsearch.php?q={id_scopus_journal}&tip=sid&clean=0"
            detail_response = requests.get(detail_url)
            detail_soup = BeautifulSoup(detail_response.content, 'html.parser')

            issn = 'N/A'
            publisher = 'N/A'
            STT += 1

            pub_div = detail_soup.find('h2', string='Publisher')
            if pub_div:
                pub_p = pub_div.find_next('p')
                if pub_p:
                    publisher = pub_p.text.strip()

            issn_div = detail_soup.find('h2', string='ISSN')
            if issn_div:
                issn_p = issn_div.find_next('p')
                if issn_p:
                    issn = issn_p.text.strip()

            rows.append([STT, title_journal, issn, publisher, id_scopus_journal])

    return pd.DataFrame(rows, columns=['STT', 'Tên tạp chí', 'ISSN', 'Nhà xuất bản', 'ID Scopus'])

def id_scopus_to_all(id_scopus_input):
    url = f"https://www.scimagojr.com/journalsearch.php?q={id_scopus_input}&tip=sid&clean=0"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    name_journal = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
    country = soup.find('h2', string='Country').find_next('a').text.strip() if soup.find('h2', string='Country') else 'N/A'

    treecategory_dict = {}
    area = soup.find('h2', string='Subject Area and Category')
    if area:
        cats = area.find_next_sibling('p').find_all('li', recursive=True)
        for cat in cats:
            subcats = cat.find_all('li')
            if subcats:
                for sub in subcats:
                    name = sub.find('a').text.strip()
                    code = sub.find('a')['href'].split('=')[-1]
                    treecategory_dict[name] = code
            else:
                name = cat.find('a').text.strip()
                code = cat.find('a')['href'].split('=')[-1]
                treecategory_dict[name] = code

    publisher = soup.find('h2', string='Publisher').find_next('a').text.strip() if soup.find('h2', string='Publisher') else 'N/A'
    issn = soup.find('h2', string='ISSN').find_next('p').text.strip() if soup.find('h2', string='ISSN') else 'N/A'
    coverage = soup.find('h2', string='Coverage').find_next('p').text.strip() if soup.find('h2', string='Coverage') else 'N/A'
    homepage = soup.find('a', string='Homepage')['href'] if soup.find('a', string='Homepage') else 'N/A'
    howtopublish = soup.find('a', string='How to publish in this journal')['href'] if soup.find('a', string='How to publish in this journal') else 'N/A'
    email = soup.find('a', href=True, string=lambda x: x and '@' in x)
    email = email['href'].replace('mailto:', '') if email else 'N/A'

    return name_journal, country, treecategory_dict, publisher, issn, coverage, homepage, howtopublish, email

def check_rank_by_name_1_journal(search_name_journal, subject_area_category, year_check):
    rows = []
    STT = 0
    def fetch(url, category, id_cat, total, page):
        nonlocal STT
        r = requests.get(url)
        s = BeautifulSoup(r.content, 'html.parser')
        for row in s.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                name = cells[1].text.strip()
                if clear_format(name) == clear_format(search_name_journal):
                    STT += 1
                    pos = cells[0].text.strip()
                    q = cells[3].text.strip().split()[-1]
                    h = cells[4].text.strip()
                    percent = round(float(pos)/total*100, 5)
                    rank, top, note = check_rank_by_h_q(total, percent, q)
                    rows.append([STT, name, rank, q, int(h), int(pos), int(total), percent, top, category, id_cat, int(page), note])
                    break
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = []
        for cat, id_cat in subject_area_category.items():
            r = requests.get(f"https://www.scimagojr.com/journalrank.php?category={id_cat}&year={year_check}&type=j&order=h&ord=desc")
            s = BeautifulSoup(r.content, 'html.parser')
            total = int(s.find('div', class_='pagination').text.split()[-1]) if s.find('div', class_='pagination') else 0
            for page in range(1, int(total/20)+2):
                url = f"https://www.scimagojr.com/journalrank.php?category={id_cat}&year={year_check}&type=j&order=h&ord=desc&page={page}&total_size={total}"
                futures.append(ex.submit(fetch, url, cat, id_cat, total, page))
        for f in futures:
            f.result()
    return pd.DataFrame(rows, columns=['STT', 'Tên tạp chí', 'Hạng', 'Chỉ số Q', 'H-index', 'Vị trí', 'Tổng số tạp chí', 'Phần trăm', 'Top phần trăm', 'Chuyên ngành', 'ID Chuyên ngành', 'Trang', 'Ghi chú'])

# === Bạn đã có sẵn hàm issn_to_all, ta giữ nguyên ===
def issn_to_all(issn):
    url = f"https://www.scimagojr.com/journalsearch.php?q={issn}&tip=sid&clean=0"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    name_journal = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
    country_tag = soup.find('h2', string='Country')
    country = country_tag.find_next('a').text.strip() if country_tag else 'N/A'
    treecategory_dict = {}
    subject_area_div = soup.find('h2', string='Subject Area and Category')
    if subject_area_div:
        categories = subject_area_div.find_next_sibling('p').find_all('li', recursive=True)
        for category in categories:
            subcategories = category.find_all('li')
            if subcategories:
                for subcategory in subcategories:
                    subcategory_name = subcategory.find('a').text.strip()
                    subcategory_code = subcategory.find('a')['href'].split('=')[-1]
                    treecategory_dict[subcategory_name] = subcategory_code
            else:
                category_name = category.find('a').text.strip()
                category_code = category.find('a')['href'].split('=')[-1]
                treecategory_dict[category_name] = category_code
    subject_area_category = treecategory_dict
    publisher_tag = soup.find('h2', string='Publisher')
    publisher = publisher_tag.find_next('a').text.strip() if publisher_tag else 'N/A'
    h_index_tag = soup.find('h2', string='H-Index')
    h_index = h_index_tag.find_next('p', class_='hindexnumber').text.strip() if h_index_tag else 'N/A'
    issn_tag = soup.find('h2', string='ISSN')
    issn_info = issn_tag.find_next('p').text.strip() if issn_tag else 'N/A'
    coverage_tag = soup.find('h2', string='Coverage')
    coverage = coverage_tag.find_next('p').text.strip() if coverage_tag else 'N/A'
    homepage_tag = soup.find('a', string='Homepage')
    homepage_link = homepage_tag['href'] if homepage_tag else 'N/A'
    how_to_publish_tag = soup.find('a', string='How to publish in this journal')
    how_to_publish_link = how_to_publish_tag['href'] if how_to_publish_tag else 'N/A'
    email_tag = soup.find('a', href=True, string=lambda x: x and '@' in x)
    email_question_journal = email_tag['href'].replace('mailto:', '') if email_tag else 'N/A'
    return name_journal, country, subject_area_category, publisher, h_index, issn_info, coverage, homepage_link, how_to_publish_link, email_question_journal

# Check hạng 1 tạp chí    
def def_rank_by_name_or_issn(year):
    st.subheader(f"Năm đang tra cứu — {year}")
    st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 1</p>', unsafe_allow_html=True)
    keyword = st.text_input("Nhập tên hoặc ISSN của tạp chí. Sau đó bấm **Tìm kiếm**")

    if st.button("Tìm kiếm"):
        with st.spinner("Đang tìm ..."):
            df = find_title_or_issn(keyword)
            st.session_state['df_search'] = df

    df = st.session_state.get('df_search', pd.DataFrame())
    st.info(f"Đã tìm thấy {len(df)} kết quả, xem bảng bên dưới")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 2</p>', unsafe_allow_html=True)
        options = df['STT'].astype(str) + " - " + df['Tên tạp chí']
        choose = st.selectbox(
            "Chọn đúng tên tạp chí muốn tra cứu. Sau đó bấm **Xem hạng**",
            options,
            key="choose_journal"
        )

        if st.button("Xem hạng"):
            with st.spinner("Đang tra hạng ..."):
                choose_name = choose.split(' - ', 1)[1]
                selected = df[df['Tên tạp chí'] == choose_name].iloc[0]
                id_scopus = selected['ID Scopus']
                issn = selected['ISSN']

                # Crawl chi tiết và bảng rank
                name_j, country, cats, pub, issn_detail, cover, home, howpub, mail = id_scopus_to_all(id_scopus)
                df_rank = check_rank_by_name_1_journal(name_j, cats, year)

                # Lưu vào session_state
                st.session_state['df_rank'] = df_rank
                st.session_state['id_scopus'] = id_scopus
                st.session_state['issn'] = issn
                st.session_state['publ'] = pub
                st.session_state['home'] = home

    df_rank = st.session_state.get('df_rank', pd.DataFrame())
    id_scopus = st.session_state.get('id_scopus')
    issn = st.session_state.get('issn')
    homepage_link_new = st.session_state.get('home')

    if not df_rank.empty and id_scopus and issn:
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
        st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 3</p>', unsafe_allow_html=True)
        selected_line = st.selectbox(
            "Chọn chuyên ngành để xem chi tiết và mở website SJR - Scopus - WoS in minh chứng",
            df_rank['STT'].astype(str) + " - " + df_rank['Tên tạp chí'] + " - " + df_rank['Hạng'] + " - " + df_rank['Chuyên ngành'],
            key="choose_line_rank"
        )

        if selected_line:
            stt_chosen = int(selected_line.split(' - ')[0])
            row_chosen = df_rank[df_rank['STT'] == stt_chosen].iloc[0]

            open_link_sjr = f"https://www.scimagojr.com/journalrank.php?category={row_chosen['ID Chuyên ngành']}&year={year}&type=j&order=h&ord=desc&page={row_chosen['Trang']}&total_size={row_chosen['Tổng số tạp chí']}"
            open_link_scopus = f"https://www.scopus.com/sourceid/{id_scopus}"
            open_link_wos = f"https://mjl.clarivate.com:/search-results?issn={issn}&hide_exact_match_fl=true"

            now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Hh%M ngày %d/%m/%Y") 
            publ = st.session_state.get('publ')
            if publ:
                st.info(
                    f"Thông tin trên biên bản nghiệm thu:\n"
                    f"+ Tên tạp chí: {row_chosen['Tên tạp chí']}\n"
                    f"+ ISSN: {issn}\n"
                    f"+ Nhà xuất bản: {publ}\n"
                    f"+ {row_chosen['Hạng']} (WoS), SJR: {row_chosen['Chỉ số Q']}, H-Index: {row_chosen['H-index']}, thuộc top {row_chosen['Top phần trăm']}% (thứ tự {row_chosen['Vị trí']}) trong {row_chosen['Tổng số tạp chí']} tạp chí về {row_chosen['Chuyên ngành']}, truy xuất lúc {now_vn}"
                        )
            else:
                st.warning("NXB chưa có dữ liệu. Vui lòng bấm 'Xem hạng' trước.")

            #st.markdown(f"[🌐 Mở website SJR của tạp chí **{row_chosen['Tên tạp chí']}**, chuyên ngành **{row_chosen['Chuyên ngành']}**]({open_link_sjr})")
            #st.markdown(f"[🌐 Mở website Scopus của tạp chí **{row_chosen['Tên tạp chí']}**, ISSN **{issn}**]({open_link_scopus})")
            #st.markdown(f"[🌐 Mở Website MJL-WoS của tạp chí **{row_chosen['Tên tạp chí']}**, ISSN: **{issn}**](<{open_link_wos}>)")
            
            st.markdown(
                f"""
                <a href="{open_link_sjr}">
                    \n🌐 Mở Website <span style="color: gold;">SJR</span> của tạp chí
                    <span style="color: gold;">{row_chosen['Tên tạp chí']}</span> —
                    Chuyên ngành <span style="color: gold;">{row_chosen['Chuyên ngành']}</span>
                </a>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <a href="{open_link_scopus}">
                    \n🌐 Mở Website <span style="color: gold;">Scopus</span> của tạp chí
                    <span style="color: gold;">{row_chosen['Tên tạp chí']}</span> —
                    ISSN: <span style="color: gold;">{issn}</span>
                </a>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <a href="{open_link_wos}">
                    \n🌐 Mở Website <span style="color: gold;">MJL-WoS</span> của tạp chí
                    <span style="color: gold;">{row_chosen['Tên tạp chí']}</span> —
                    ISSN: <span style="color: gold;">{issn}</span>
                </a>
                """,
                unsafe_allow_html=True
            )

            if homepage_link_check and homepage_link_check != 'N/A':
                st.markdown(
                    f"""
                    <a href="{homepage_link_check}">
                        \n🌐 Mở Website <span style="color: gold;">Homepage</span> của tạp chí
                        <span style="color: gold;">{row_chosen['Tên tạp chí']}</span>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

def check_rank_by_name_1_category(id_category, year_check):
    row_add = []
    STT = 0
    url_category = f"https://www.scimagojr.com/journalrank.php?category={id_category}&type=j&order=h&ord=desc&year={year_check}"
    response = requests.get(url_category)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination_div = soup.find('div', class_='pagination')
    total_journals_text = pagination_div.text.strip() if pagination_div else '0'
    total_journal = int(total_journals_text.split()[-1]) if total_journals_text.split() else 0

    for page_number in range(1, int(total_journal / 20) + 2):
        url = f"https://www.scimagojr.com/journalrank.php?category={id_category}&year={year_check}&type=j&order=h&ord=desc&page={page_number}&total_size={total_journal}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                name_journal_web = cells[1].text.strip()
                STT += 1
                position = cells[0].text.strip()
                SJR_Q_value = cells[3].text.strip()
                if ' ' in SJR_Q_value:
                    _, Q_value = SJR_Q_value.split()
                else:
                    Q_value = 'N/A'
                h_index = cells[4].text.strip()
                percent = round((float(position) / total_journal * 100), 5) if total_journal else 0
                rank, top_percent, note = check_rank_by_h_q(total_journal, percent, Q_value)
                row_add.append([STT, name_journal_web, rank, Q_value, int(h_index), int(position), total_journal, percent, top_percent, page_number, note])

    df = pd.DataFrame(row_add, columns=[
        'STT', 'Tên tạp chí', 'Hạng', 'Chỉ số Q', 'H-index', 'Vị trí',
        'Tổng số tạp chí', 'Phần trăm', 'Top phần trăm', 'Trang', 'Ghi chú'
    ])
    return df

def def_list_all_subject(year):
    st.subheader(f"Năm đang tra cứu — {year}")

    if st.button("📥Tải danh sách tất cả các chuyên ngành"):
        with st.spinner("Đang tải danh sách..."):
            url = f"https://www.scimagojr.com/journalrank.php?year={year}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            all_subject_li = None
            for li in soup.find_all('li'):
                a_tag = li.find('a')
                if a_tag and 'All subject categories' in a_tag.get_text():
                    all_subject_li = li
                    break

            rows = []
            if all_subject_li:
                list_items = all_subject_li.find_next_siblings('li')
                for item in list_items:
                    a_tag = item.find('a')
                    if a_tag:
                        name = a_tag.get_text(strip=True)
                        code = a_tag['href'].split('=')[-1]
                        rows.append([name, code])

            if rows:
                df = pd.DataFrame(rows, columns=['Tên chuyên ngành', 'ID Chuyên ngành'])
                df.insert(0, 'STT', range(1, len(df) + 1))
                st.session_state['df_subject_list'] = df
                st.success(f"✅ Đã tải {len(df)} chuyên ngành")
            else:
                st.warning("❌ Không tìm thấy dữ liệu")

    df = st.session_state.get('df_subject_list', pd.DataFrame())

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        options = df['STT'].astype(str) + " - " + df['Tên chuyên ngành'] + " - " + df['ID Chuyên ngành']
        choose = st.selectbox(
            "Chọn chuyên ngành để xem thông tin",
            options
        )

        if 'chosen_category' not in st.session_state:
            st.session_state['chosen_category'] = {}

        if st.button("✅ Xác nhận và tạo link SJR"):
            stt, name, code = choose.split(' - ')
            st.session_state['chosen_category']['name'] = name
            st.session_state['chosen_category']['code'] = code

            link_sjr = f"https://www.scimagojr.com/journalrank.php?category={code}&year={year}&type=j&order=h&ord=desc"
            st.success(f"Đã chọn chuyên ngành: **{name}**")
            st.markdown(f"[🌐 Mở website SJR chuyên ngành **{name}**]({link_sjr})")

        if 'chosen_category' in st.session_state and st.session_state['chosen_category']:
            name = st.session_state['chosen_category']['name']
            code = st.session_state['chosen_category']['code']
            if st.button(f"🔍 Xem hạng tất cả các tạp chí thuộc chuyên ngành **{name}**"):
                with st.spinner(f"Đang xếp hạng tất cả các tạp chí thuộc chuyên ngành **{name}** ..."):
                    df_rank = check_rank_by_name_1_category(code, year)
                    if not df_rank.empty:
                        st.dataframe(df_rank, use_container_width=True, hide_index=True)

                        buffer = BytesIO()
                        df_rank.to_excel(buffer, index=False)
                        buffer.seek(0)

                        st.download_button(
                            label=f"📥 Tải file excel xếp hạng của chuyên ngành **{name}**",
                            data=buffer,
                            file_name=f"rank_{name}_{year}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("❌ Không tìm thấy dữ liệu xếp hạng")
    else:
        st.info("👉 Bấm **Tải danh sách chuyên ngành** để bắt đầu")


# === Hàm chính ===
def def_check_in_scopus_sjr_wos(year):
    st.subheader(f"Phân loại tạp chí thuộc SJR - SCOPUS - WOS")

    keyword = st.text_input("Nhập tên hoặc ISSN của tạp chí")

    search_clicked = st.button("🔍 Tìm kiếm")

    if search_clicked:
        st.session_state['keyword_journal'] = keyword.strip()
        st.session_state['search_done'] = False  # Reset flag để ép chạy lại tìm kiếm mới

    # Chỉ tìm kiếm khi bấm nút
    if 'keyword_journal' in st.session_state and not st.session_state.get('search_done', False):
        try:
            with st.spinner(f"Đang tìm tạp chí theo '{st.session_state['keyword_journal']}'..."):
                df_1 = find_title_or_issn(st.session_state['keyword_journal'])

                # Xử lý dòng ISSN lỗi
                empty_indices = df_1[df_1['ISSN'].str.len() < 4].index.tolist()
                df_1.drop(index=empty_indices, inplace=True)

                # Lưu lại
                st.session_state['df_journals'] = df_1
                st.session_state['search_done'] = True

        except Exception as e:
            st.warning(f"⚠️ Cảnh báo lỗi >>> {str(e)}")

    # Nếu đã có dữ liệu thì LUÔN hiển thị bảng + selectbox
    if st.session_state.get('search_done', False):
        df_1 = st.session_state['df_journals']

        column_show = ['STT', 'Tên tạp chí', 'ISSN', 'Nhà xuất bản', 'ID Scopus']
        st.dataframe(df_1[column_show],hide_index=True)

        options = [f"{a} - {b} - {c} - {d}"
                   for a, b, c, d in zip(df_1['STT'], df_1['Tên tạp chí'],
                                            df_1['ISSN'], df_1['Nhà xuất bản'])]

        selected_option = st.selectbox(
            f"Đã tìm thấy {len(df_1)} kết quả - Chọn tạp chí muốn tra cứu",
            options,
            key="selected_journal"
        )

        choose_stt = selected_option.split(' - ')[0]
        selected_row = df_1.iloc[int(choose_stt) - 1]
        id_scopus_choose = selected_row['ID Scopus']

        # Chỉ gọi issn_to_all khi STT thay đổi
        if 'selected_stt' not in st.session_state or st.session_state['selected_stt'] != choose_stt:
            try:
                with st.spinner("🔄 Đang cập nhật ..."):
                    (
                        name_journal_check,
                        country,
                        subject_area_category_check,
                        publisher,
                        h_index,
                        issn_check,
                        coverage,
                        homepage_link,
                        how_to_publish_link,
                        email_question_journal
                    ) = issn_to_all(id_scopus_choose)

                    st.session_state['journal_detail'] = {
                        "name_journal_check": name_journal_check,
                        "country": country,
                        "subject_area_category_check": subject_area_category_check,
                        "publisher": publisher,
                        "h_index": h_index,
                        "issn_check": issn_check,
                        "coverage": coverage,
                        "homepage_link": homepage_link,
                        "how_to_publish_link": how_to_publish_link,
                        "email_question_journal": email_question_journal
                    }
                    st.session_state['selected_stt'] = choose_stt  # Ghi nhớ lựa chọn

            except Exception as e:
                st.warning(f"⚠️ Cảnh báo lỗi >>> {str(e)}")

        # Luôn lấy thông tin đã tra
        if 'journal_detail' in st.session_state:
            detail = st.session_state['journal_detail']
            issn_check = detail["issn_check"]

            open_link_sjr = f"<https://www.scimagojr.com/journalsearch.php?q={id_scopus_choose}&tip=sid&clean=0>"
            open_link_scopus = f"<https://www.scopus.com/sourceid/{id_scopus_choose}>"
            open_link_wos = f"<https://mjl.clarivate.com/search-results?issn={issn_check}&hide_exact_match_fl=true&utm_source=mjl&utm_medium=share-by-link&utm_campaign=search-results-share-this-journal>"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"[🌐 Mở SJR]({open_link_sjr})")
            with col2:
                st.markdown(f"[🌐 Mở SCOPUS]({open_link_scopus})")
            with col3:
                st.markdown(f"[🌐 Mở MJL-WOS]({open_link_wos})")
            link_homepage = detail['homepage_link']
            st.info(
                f"✅ **{detail['name_journal_check']}**  ➖  **Quốc gia**: {detail['country']}  ➖  "
                f"**NXB**: {detail['publisher']}  ➖  **H-Index**: {detail['h_index']}  ➖  "
                f"**HomePage**: "
                f"[Xem tại đây](<{link_homepage}>)"
            )

# Tab 4 -----------------------

def def_rank_by_rank_key(year):
    st.subheader(f"Lọc tạp chí theo Từ khoá chuyên ngành và Hạng — {year}")

    # ✅ Luôn có sẵn, không bị mất khi rerun
    column_show = [
        'STT', 'Tên tạp chí', 'Hạng', 'Chỉ số Q', 'H-index',
        'Vị trí', 'Tổng số tạp chí', 'Top phần trăm',
        'Chuyên ngành', 'Ghi chú'
    ]

    # Bước 1: Chọn từ khoá + nhập thêm
    list_keywords = [
        "math", "analysis", "numerical", "optimization", "control",
        "algebra", "geometry", "statistics", "probability",
        "computer", "computation", "engineering"
    ]
    selected_keywords = st.multiselect(
        "🔑 Chọn một hoặc nhiều hoặc ghi thêm từ khoá",
        options=list_keywords
    )
    new_keyword = st.text_input("Hoặc nhập thêm các từ khoá khác (các từ khóa cách nhau dấu phẩy)")

    # Bước 2: Chọn Hạng
    rank_options = ["Ngoại hạng chuyên ngành"] + [f"Hạng {i}" for i in range(1, 11)]
    selected_ranks = st.multiselect(
        "🏷️ Chọn một hoặc nhiều Hạng để lọc",
        options=rank_options
    )

    if st.button("🔍 Lọc tạp chí"):
        try:
            # Gom từ khoá
            all_keywords = selected_keywords.copy()
            if new_keyword.strip():
                all_keywords.extend([k.strip() for k in new_keyword.split(',') if k.strip()])
            all_keywords = list(set(all_keywords))  # Xoá trùng

            #st.write(f"🔑 Từ khoá: {all_keywords}")
            #st.write(f"🏷️ Hạng: {selected_ranks}")

            if not all_keywords or not selected_ranks:
                st.warning("⚠️ Vui lòng chọn ít nhất 1 từ khoá và 1 Hạng")
                return

            # Giữ chỗ hiển thị trạng thái & bảng
            status_placeholder = st.empty()
            dataframe_placeholder = st.empty()

            result_df = pd.DataFrame()

            # Lấy danh sách ngành
            with st.spinner("Đang lọc dữ liệu ..."):
                url = "https://www.scimagojr.com/journalrank.php?type=j&order=h&ord=desc"
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')

                all_subject_categories = None
                for li in soup.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag and 'All subject categories' in a_tag.get_text():
                        all_subject_categories = li
                        break

                list_items = all_subject_categories.find_next_siblings('li')
                categories = []
                for item in list_items:
                    a_tag = item.find('a')
                    if a_tag:
                        category = item.get_text()
                        category_id = a_tag['href'].split('=')[-1]
                        categories.append((category, category_id))

            for category, category_id in categories:
                for name_key in all_keywords:
                    if clear_format(name_key) in clear_format(category):
                        status_placeholder.info(f"Đang kiểm tra chuyên ngành: **{category}**")
                        with st.spinner("Đang lọc dữ liệu ..."):
                            df_category = check_rank_by_name_1_category(category_id, year)
                            for rank in selected_ranks:
                                filtered_df = df_category[df_category['Hạng'] == rank].copy()
                                if not filtered_df.empty:
                                    filtered_df.insert(filtered_df.columns.get_loc('Top phần trăm') + 1, 'Chuyên ngành', category)
                                    filtered_df.insert(filtered_df.columns.get_loc('Chuyên ngành') + 1, 'ID Chuyên ngành', category_id)
                                    result_df = pd.concat([result_df, filtered_df], ignore_index=True)
                                    result_df['STT'] = range(1, len(result_df) + 1)
                                    dataframe_placeholder.dataframe(result_df[column_show], hide_index=True)

            # Lưu lại để nút tải không mất khi rerun
            st.session_state['result_df'] = result_df

        except Exception as e:
            st.error(f"🚫 >>> Cảnh báo lỗi >>> {str(e)}")

    # ===========================
    # Chỉ hiện nút tải, KHÔNG render bảng lần 2
    # ===========================
    if 'result_df' in st.session_state and not st.session_state['result_df'].empty:
        result_df = st.session_state['result_df']

        towrite = BytesIO()
        result_df[column_show].to_excel(towrite, index=False, engine='xlsxwriter')
        towrite.seek(0)

        st.download_button(
            label="💾 Tải file excel kết quả lọc",
            data=towrite,
            file_name=f"Result_Rank_Keyword_{year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def def_rank_by_Q_key(year):
    st.subheader(f"🔎 Lọc tạp chí theo Từ khoá chuyên ngành và Chỉ số Q — {year}")

    # ✅ LUÔN CÓ: DÙ BẤM TẢI FILE THÌ VẪN CÒN
    column_show = [
        'STT', 'Tên tạp chí', 'Hạng', 'Chỉ số Q', 'H-index',
        'Vị trí', 'Tổng số tạp chí', 'Top phần trăm',
        'Chuyên ngành', 'Ghi chú'
    ]

    # Bước 1: Từ khoá
    list_keywords = [
        "math", "analysis", "numerical", "optimization", "control",
        "algebra", "geometry", "statistics", "probability",
        "computer", "computation", "engineering"
    ]
    selected_keywords = st.multiselect(
        "🔑 Chọn từ khoá gợi ý (có thể chọn nhiều):",
        options=list_keywords
    )
    new_keyword = st.text_input("Hoặc nhập thêm các từ khoá khác (cách nhau dấu phẩy)")

    # Bước 2: Chọn chỉ số Q
    Q_options = [f"Q{i}" for i in range(1, 5)]
    selected_Qs = st.multiselect(
        "🏷️ Chọn một hoặc nhiều chỉ số Q:",
        options=Q_options
    )

    # ✅ KEY RIÊNG để tránh Duplicate ID
    if st.button("🔍 Lọc tạp chí", key="button_q_key"):
        try:
            all_keywords = selected_keywords.copy()
            if new_keyword.strip():
                all_keywords.extend([k.strip() for k in new_keyword.split(',') if k.strip()])
            all_keywords = list(set(all_keywords))

            if not all_keywords or not selected_Qs:
                st.warning("⚠️ Vui lòng chọn ít nhất 1 từ khoá và 1 chỉ số Q")
                return

            # Placeholder
            status_placeholder = st.empty()
            dataframe_placeholder = st.empty()

            result_df = pd.DataFrame()

            with st.spinner("Đang tải danh sách chuyên ngành ..."):
                url = "https://www.scimagojr.com/journalrank.php?type=j&order=h&ord=desc"
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')

                all_subject_categories = None
                for li in soup.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag and 'All subject categories' in a_tag.get_text():
                        all_subject_categories = li
                        break

                list_items = all_subject_categories.find_next_siblings('li')
                categories = []
                for item in list_items:
                    a_tag = item.find('a')
                    if a_tag:
                        category = item.get_text()
                        category_id = a_tag['href'].split('=')[-1]
                        categories.append((category, category_id))

            for category, category_id in categories:
                for name_key in all_keywords:
                    if clear_format(name_key) in clear_format(category):
                        status_placeholder.info(f"Đang kiểm tra chuyên ngành: **{category}**")
                        with st.spinner("Đang lọc dữ liệu ..."):
                            df_category = check_rank_by_name_1_category(category_id, year)
                            for q in selected_Qs:
                                filtered_df = df_category[df_category['Chỉ số Q'] == q].copy()
                                if not filtered_df.empty:
                                    filtered_df.insert(filtered_df.columns.get_loc('Top phần trăm') + 1, 'Chuyên ngành', category)
                                    filtered_df.insert(filtered_df.columns.get_loc('Chuyên ngành') + 1, 'ID Chuyên ngành', category_id)
                                    result_df = pd.concat([result_df, filtered_df], ignore_index=True)
                                    result_df['STT'] = range(1, len(result_df) + 1)
                                    dataframe_placeholder.dataframe(result_df[column_show], hide_index=True)

            # Lưu lại, không mất khi bấm Tải
            st.session_state['result_df_q'] = result_df

        except Exception as e:
            st.error(f"🚫 >>> Cảnh báo lỗi >>> {str(e)}")

    # ✅ SAU KHI CÓ KẾT QUẢ: CHỈ HIỆN NÚT TẢI, KHÔNG RENDER LẠI BẢNG
    if 'result_df_q' in st.session_state and not st.session_state['result_df_q'].empty:
        result_df = st.session_state['result_df_q']

        towrite = BytesIO()
        result_df[column_show].to_excel(towrite, index=False, engine='xlsxwriter')
        towrite.seek(0)

        st.download_button(
            label="💾 Tải file Excel kết quả lọc",
            data=towrite,
            file_name=f"Result_Q_Keyword_{year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
