import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import random
import smtplib
import os
import base64
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from choose_year import def_year_choose
from definition import def_rank_by_name_or_issn, def_list_all_subject, def_check_in_scopus_sjr_wos, def_rank_by_rank_key, def_rank_by_Q_key

# Thay đổi định dạng link  
st.markdown(
    """
    <style>
    a {
        text-decoration: none !important;
        color: #00BFFF !important; /* Mã màu xanh lam */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cấu hình giao diện
st.set_page_config(
    page_title="C-J-V2",
    page_icon="🔓",
    layout="wide",
    initial_sidebar_state="auto"
)
# End Cấu hình giao diện

# Mã hoá logo đầu
with open("fig/logo.png", "rb") as f:
    data_left = f.read()
    encoded_left = base64.b64encode(data_left).decode()

# Mã hoá logo cuối
with open("fig/ttk3.png", "rb") as f:
    data_right = f.read()
    encoded_right = base64.b64encode(data_right).decode()

# Start tiêu đè + logo
st.markdown(
    f"""
    <style>
    .center-header {{
        text-align: center;
        margin-bottom: 1em;
    }}

    .center-header .logo-row {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2em;
        margin-bottom: 0.5em;
    }}

    .center-header .logo-row img {{
        height: 2em;
    }}

    .center-header h1 {{
        font-size: 2.5em;
        margin: 0;
    }}
    </style>

    <div class="center-header">
        <div class="logo-row">
            <img src="data:image/png;base64,{encoded_left}">
            <img src="data:image/png;base64,{encoded_right}">
        </div>
        <h1>Check - Journal</h1>
    </div>
    """,
    unsafe_allow_html=True
)
# End tiêu đè + logo

# Tải biến môi trường 
load_dotenv()
sender_email = os.getenv('EMAIL')
sender_pass = os.getenv('EMAIL_PASS')

# Hàm gửi mã đăng nhập
def send_email(receiver_email, otp):
    msg = MIMEText(f"Xin chào,\nMã đăng nhập của bạn là: {otp}")
    msg['Subject'] = "Mã đăng nhập Check-Journal"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_pass)
        server.send_message(msg)

# Hàm log email đăng nhập về admin
def send_login_log(user_email):
    log_msg = MIMEText(f"Email: {user_email}")
    log_msg['Subject'] = "Check-Journal: Đăng nhập mới"
    log_msg['From'] = sender_email
    log_msg['To'] = "check.journal.fms.tdtu@gmail.com"
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_pass)
        server.send_message(log_msg)

# Đăng nhập
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'otp_sent' not in st.session_state:
    st.session_state['otp_sent'] = ''
if 'year' not in st.session_state:
    st.session_state['year'] = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y")
if 'wrong_attempts' not in st.session_state:
    st.session_state['wrong_attempts'] = 0

# Load email bị khoá từ file
if 'blocked_emails' not in st.session_state:
    try:
        with open("blocked_emails.txt") as f:
            st.session_state['blocked_emails'] = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        st.session_state['blocked_emails'] = []

# --- LUỒNG ĐĂNG NHẬP ---
if not st.session_state['authenticated']:
    st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 1</p>', unsafe_allow_html=True)
    user_email = st.text_input(
        "Nhập đầy đủ email TDTU của bạn để nhận mã đăng nhập. Sau đó bấm nút **Tạo mã đăng nhập**"
    ).strip()

    # Check ngay: Nếu bị khoá thì chặn luôn
    if user_email and user_email in st.session_state['blocked_emails']:
        st.error("🚫 Email này đã bị khoá do nhập sai mã đăng nhập nhiều lần. Liên hệ quản trị để mở khoá")
        st.stop()

    # Danh sách các email được phép nhận OTP
    allowed_emails_otp = [
        "@tdtu.edu.vn",
        "nguyenhuucan@gmail.com",
        "nhc156@gmail.com",
        "c2200193@student.tdtu.edu.vn",
        "tandatkhuu2k3@gmail.com"
                     ]
    if st.button("Tạo mã đăng nhập"):
        if any(allowed in user_email for allowed in allowed_emails_otp):
            otp = str(random.randint(100, 999))
            st.session_state['otp_sent'] = otp
            st.session_state['user_email'] = user_email  # Gán user_email vào session
            send_email(user_email, otp)
            st.success(f"Mã đăng nhập có 3 chữ số đã được gửi đến email **{user_email}**") 
        else:
            st.warning("⚠️ Bạn chỉ được nhập email có dạng @tdtu.edu.vn hoặc email được cấp quyền trước")
    st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 2</p>', unsafe_allow_html=True)
    otp_in = st.text_input("Nhập mã đăng nhập vừa nhận qua email", type="password")

    if st.button("Đăng nhập"):
        # Lấy email thực tế từ session
        this_email = st.session_state.get('user_email', '').strip()

        if otp_in == st.session_state['otp_sent']:
            st.session_state['authenticated'] = True
            st.session_state['wrong_attempts'] = 0
            st.success("Đăng nhập thành công")
            st.markdown('<p style="color: gold; font-weight: bold; margin: 0;">Bước 3</p>', unsafe_allow_html=True)
            st.info("⚠️ Bấm nút **Đăng nhập** lần nữa để vào ứng dụng")
            send_login_log(this_email)
        else:
            st.session_state['wrong_attempts'] += 1
            attempts_left = 5 - st.session_state['wrong_attempts']

            if st.session_state['wrong_attempts'] >= 5:
                if this_email not in st.session_state['blocked_emails']:
                    st.session_state['blocked_emails'].append(this_email)
                    # Ghi vào file blocked_emails.txt
                    with open("blocked_emails.txt", "w") as f:
                        for e in st.session_state['blocked_emails']:
                            f.write(e + "\n")
                st.error("🚫 Bạn đã nhập sai mã đăng nhập 5 lần. Email này đã bị tạm khoá. Liên hệ admin để gỡ khóa")
            else:
                st.error(f"❌ Mã đăng nhập không đúng! Bạn còn {attempts_left} lần thử")

    st.stop()

# Giao diện chính
if st.session_state['authenticated']:
    tabs = st.tabs([
        "Năm tra cứu",
        "Tra hạng theo tên hoặc ISSN",
        "Danh sách chuyên ngành",
        "Phân loại tạp chí",
        "Tìm tạp chí theo Từ khóa và Hạng",
        "Tìm tạp chí theo Từ khóa và Q",
        "Chức năng khác",
        "Thông tin ứng dụng"
    ])
    with tabs[0]:
        st.session_state['year'] = def_year_choose(st.session_state['year'])
    with tabs[1]:
        def_rank_by_name_or_issn(st.session_state['year'])
    with tabs[2]:
        def_list_all_subject(st.session_state['year'])
    with tabs[3]:
        def_check_in_scopus_sjr_wos(st.session_state['year'])
    with tabs[4]:
        def_rank_by_rank_key(st.session_state['year'])
    with tabs[5]:
        def_rank_by_Q_key(st.session_state['year'])

    # Quyền xem tài liệu nội bộ Khoa TTK
    allowed_see_ttk = [
        "phanthanhtoan@tdtu.edu.vn", # Phan Thanh Toàn
        "truongbuuchau@tdtu.edu.vn", # Trương Bửu Châu
        "duongthanhphong@tdtu.edu.vn", # Dương Thanh Phong
        "tranmykiman@tdtu.edu.vn", # Trần Mỹ Kim An
        "nguyenquocbao1@tdtu.edu.vn", # Nguyễn Quốc Bảo
        "nguyenhuucan@tdtu.edu.vn", # Nguyễn Hữu Cần
        "nguyenquoccuong@tdtu.edu.vn", # Nguyễn Quốc Cường
        "lethingocgiau@tdtu.edu.vn", # Lê Thị Ngọc Giàu
        "huynhvankha@tdtu.edu.vn", # Huỳnh Văn Kha
        "chuduckhanh@tdtu.edu.vn", # Chu Đức Khánh
        "phanquockhanh@tdtu.edu.vn", # Phan Quốc Khánh
        "lebakhiet@tdtu.edu.vn", # Lê Bá Khiết
        "tranvoanhkhoa@tdtu.edu.vn", # Trần Võ Anh Khoa
        "krugeralexander@tdtu.edu.vn", # Alexander Kruger
        "trantuanminh@tdtu.edu.vn", # Trần Tuấn Minh
        "tranminhphuong@tdtu.edu.vn", # Trần Minh Phương
        "truongthithanhphuong@tdtu.edu.vn", # Trương Thị Thanh Phương
        "lysel@tdtu.edu.vn", # Lý Sel
        "tranngocthach@tdtu.edu.vn", # Trần Ngọc Thạch
        "vongocthieu@tdtu.edu.vn", # Võ Ngọc Thiệu
        "nguyenductho@tdtu.edu.vn", # Nguyễn Đức Thọ
        "caoxuanphuong@tdtu.edu.vn", # Cao Xuân Phương
        "nguyenthihongloan@tdtu.edu.vn", # Nguyễn Thị Hồng Loan
        "letruongnhat@tdtu.edu.vn", # Lê Trường Nhật
        "nabendu.pal@tdtu.edu.vn", # Nabendu Pal
        "thachthanhtien@tdtu.edu.vn", # Thạch Thanh Tiền
        "buithuytrang@tdtu.edu.vn", # Bùi Thùy Trang
        "thanthihong@tdtu.edu.vn", # Thân Thị Hồng
        "phamthiyenanh@tdtu.edu.vn", # Phạm Thị Yến Anh
        "chengocha@tdtu.edu.vn", # Chế Ngọc Hà
        "tranbanhan@tdtu.edu.vn", # Trần Bá Nhẫn
        "tranthithuynuong@tdtu.edu.vn", # Trần Thị Thùy Nương
        "phamthanhtri@tdtu.edu.vn", # Phạm Thành Trí
        "letrungnghia@tdtu.edu.vn", # Lê Trung Nghĩa
        "ngothibichhoa@tdtu.edu.vn", # Ngô Thị Bích Hoa
        "phokimhung@tdtu.edu.vn", # Phó Kim Hưng
        "nguyenletoannhatlinh@tdtu.edu.vn", # Nguyễn Lê Toàn Nhật Linh
        "lysal@tdtu.edu.vn", # Lý Sal
        "tranthisonthao@tdtu.edu.vn", # Trần Thị Sơn Thảo
        "doanthianhthu@tdtu.edu.vn", # Đoàn Thị Anh Thư
        "phamthanhcong@tdtu.edu.vn", # Phạm Thành Công
        "nguyenthihuong@tdtu.edu.vn", # Nguyễn Thị Hương
    ]

    # Quyền admin
    unblocked_admins = [
        "nguyenhuucan@tdtu.edu.vn",
        "nguyenhuucan@gmail.com"
    ]

    with tabs[6]:  # Tab Chức năng khác
        user = st.session_state.get('user_email', '') 

        subtabs = st.tabs(["🔬 Thông tin NCKH", "📚 Hỗ trợ LaTeX", "⭐ Truy cập WoS", "📄 Thông tin và tài liệu nội bộ", "🔒 &nbsp; Admin"])

        # Tab con: Thông tin NCKH
        with subtabs[0]:
            st.markdown("**Tổng hợp thông tin liên quan đến hoạt động nghiên cứu khoa học**")
            st.markdown("""

            ---

            **📁 Phân loại tạp chí**
            - [Scopus - sources](https://www.scopus.com/sources.uri) — Kiểm tra tạp chí thuộc Scopus (miễn phí)
            - [SJR](https://www.scimagojr.com) — Kiểm tra tạp chí thuộc SJR (miễn phí)
            - [MJL-WoS](https://mjl.clarivate.com) — Kiểm tra tạp chí thuộc WoS (miễn phí)

            ---

            **👤 Thông tin nhà nghiên cứu**
            - [OrcID](https://orcid.org) — Thông tin cá nhân, quá trình đào tạo, hướng nghiên cứu, công bố (miễn phí)
            - [Google Scholar](https://scholar.google.com) — Thông tin hướng nghiên cứu, công bố, trích dẫn, h-index (miễn phí)
            - [ResearchGate](https://www.researchgate.net) — Hồ sơ cá nhân, công bố, bình luận, trao đổi (cần lời mời)
            - [ResearcherID - WoS](https://www.webofscience.com/wos/author/record/id) — Hồ sơ cá nhân, công bố, trích dẫn, H-index (cần tài khoản)

            ---

            **🗂️ Một số thông tin khác**
            - [Scopus - sources](https://www.scopus.com/sources.uri) — Tra cứu ISSN, Publisher, Title của tạp chí (miễn phí)
            - [Scopus - search](https://www.scopus.com/search/form.uri?display=basic#basic)  — Tra cứu tài liệu, trích dẫn, h-index, thông tin tác giả (cần tài khoản)
            - [WoS - search](https://www.webofscience.com/wos/woscc/basic-search)  — Tra cứu tài liệu, trích dẫn, mạng lưới, thống kê số lượng công bố trên WoS (cần tài khoản)
            - [Crossref](https://search.crossref.org) — Tìm tài liệu trích dẫn (miễn phí)
            - [MSC 2020](https://mathscinet.ams.org/mathscinet/msc/msc2020.html) — Mã chuyên ngành Toán học (miễn phí)
            - [MRLookup](https://mathscinet.ams.org/mrlookup) — Tìm tài liệu trích dẫn ngành Toán (miễn phí)
            - [MathSciNet](https://mathscinet.ams.org/mathscinet/publications-search) — Tìm tài liệu, thông tin tác giả ngành Toán (cần tài khoản)
            
            ---
            
            """, unsafe_allow_html=False)

            st.image("fig/kind.png", caption="Phân loại xếp hạng tạp chí theo TDTU", width=750 # use_container_width=True
                        )
        # Tab con: Hỗ trợ LaTeX
        with subtabs[1]:
            import streamlit as st
            import re
            from collections import Counter
            import difflib

            #st.set_page_config(page_title="LaTeX", layout="wide")
            st.subheader("Kiểm tra tham chiếu label &nbsp; & &nbsp; Sắp xếp TLTK theo định dạng \\bibitem")

            st.markdown("""
            **Hướng dẫn:**  
            1️⃣ Chọn file LaTeX chính: file main nội dung soạn thảo, không chứa TLTK  
            2️⃣ Chọn file LaTeX chứa TLTK có dạng:<br>
            &nbsp; &nbsp; &nbsp; &nbsp; \\begin{thebibliography}{...}<br>
            &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; \\bibitem{label 1} ...<br>
            &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; \\bibitem{label 2} ...<br>
            &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ...<br>
            &nbsp; &nbsp; &nbsp; &nbsp; \\end{thebibliography}  
            3️⃣ Chọn kiểu sắp xếp → Bấm **Sắp xếp**
            """, unsafe_allow_html=True)

            main_tex_file = st.file_uploader("📂 Up file LaTeX chính soạn thảo nội dung", type=["tex"])
            ref_tex_file = st.file_uploader("📂 Up file LaTeX chứa TLTK", type=["tex"])

            sort_option = st.radio(
                "🔄 Chọn kiểu sắp xếp TLTK",
                ["Thứ tự xuất hiện \\cite", "Tên tác giả đầu", "Năm xuất bản (mới → cũ)", "Năm xuất bản (cũ → mới)"]
            )

            if main_tex_file:
                st.session_state['main_content'] = main_tex_file.read().decode("utf-8")

            if ref_tex_file:
                st.session_state['ref_content'] = ref_tex_file.read().decode("utf-8")

            def extract_year(text):
                # Bước 1: Tìm năm 4 chữ số, loại bỏ URL và dạng 0000-0000
                years = re.findall(r'\b(?!https?://)\d{4}\b', text)
                years = [y for y in years if not re.search(r'\d{4}-\d{4}', y)]
                
                if years:
                    return int(years[0])
                
                # Bước 2: Nếu không có, tìm năm dạng 18xx, 19xx, 20xx
                alt_years = re.findall(r'\b(18|19|20)\d{2}\b', text)
                if alt_years:
                    # re.findall với nhóm (18|19|20) chỉ trả về phần nhóm => cần lấy cả match gốc
                    alt_years = re.findall(r'\b(18\d{2}|19\d{2}|20\d{2})\b', text)
                    return int(alt_years[0])
                return None

            if ('main_content' in st.session_state) and ('ref_content' in st.session_state):
                if st.button("Sắp xếp"):
                    main_content = st.session_state['main_content']
                    ref_content = st.session_state['ref_content']

                    # Split main content into lines for tracking line numbers
                    main_lines = main_content.splitlines()

                    # Find all \cite commands and their line numbers
                    all_cites = []
                    cite_lines = {}
                    for i, line in enumerate(main_lines, 1):  # Start line numbering at 1
                        cites = re.findall(r'\\cite{([^}]+)}', line)
                        for sub in cites:
                            labels = [label.strip() for label in sub.split(',')]
                            all_cites.extend(labels)
                            for label in labels:
                                if label not in cite_lines:
                                    cite_lines[label] = []
                                cite_lines[label].append(i)

                    # Find all \label commands in main file and their line numbers
                    all_labels = []
                    label_lines = {}
                    for i, line in enumerate(main_lines, 1):
                        labels = re.findall(r'\\label{([^}]+)}', line)
                        for label in labels:
                            all_labels.append(label)
                            if label not in label_lines:
                                label_lines[label] = []
                            label_lines[label].append(i)

                    # Find duplicate labels in main file
                    label_counts = Counter(all_labels)
                    duplicate_labels = {k: {'count': c, 'lines': label_lines[k]} for k, c in label_counts.items() if c > 1}

                    # Find table and figure labels
                    table_labels = []
                    figure_labels = []
                    table_label_lines = {}
                    figure_label_lines = {}
                    in_table = False
                    in_figure = False
                    for i, line in enumerate(main_lines, 1):
                        if re.search(r'\\begin{table}', line):
                            in_table = True
                        elif re.search(r'\\end{table}', line):
                            in_table = False
                        elif re.search(r'\\begin{figure}', line):
                            in_figure = True
                        elif re.search(r'\\end{figure}', line):
                            in_figure = False
                        elif in_table:
                            labels = re.findall(r'\\label{([^}]+)}', line)
                            for label in labels:
                                table_labels.append(label)
                                if label not in table_label_lines:
                                    table_label_lines[label] = []
                                table_label_lines[label].append(i)
                        elif in_figure:
                            labels = re.findall(r'\\label{([^}]+)}', line)
                            for label in labels:
                                figure_labels.append(label)
                                if label not in figure_label_lines:
                                    figure_label_lines[label] = []
                                figure_label_lines[label].append(i)

                    # Find duplicate table and figure labels
                    table_label_counts = Counter(table_labels)
                    duplicate_table_labels = {k: {'count': c, 'lines': table_label_lines[k]} for k, c in table_label_counts.items() if c > 1}
                    figure_label_counts = Counter(figure_labels)
                    duplicate_figure_labels = {k: {'count': c, 'lines': figure_label_lines[k]} for k, c in figure_label_counts.items() if c > 1}

                    # Find equation labels
                    equation_labels = []
                    equation_label_lines = {}
                    math_envs = ['equation', 'align', 'eqnarray', 'multline', 'gather']
                    in_math = None
                    for i, line in enumerate(main_lines, 1):
                        for env in math_envs:
                            if re.search(rf'\\begin{{{env}}}', line):
                                in_math = env
                            elif re.search(rf'\\end{{{env}}}', line) and in_math == env:
                                in_math = None
                        if in_math:
                            labels = re.findall(r'\\label{([^}]+)}', line)
                            for label in labels:
                                equation_labels.append(label)
                                if label not in equation_label_lines:
                                    equation_label_lines[label] = []
                                equation_label_lines[label].append(i)

                    # Find all \ref and \eqref commands
                    all_refs = []
                    for line in main_lines:
                        refs = re.findall(r'\\(?:ref|eqref){([^}]+)}', line)
                        all_refs.extend(refs)

                    # Find unreferenced table, figure, and equation labels
                    unreferenced_table_labels = {l: table_label_lines[l] for l in table_labels if l not in all_refs}
                    unreferenced_figure_labels = {l: figure_label_lines[l] for l in figure_labels if l not in all_refs}
                    unreferenced_equation_labels = {l: equation_label_lines[l] for l in equation_labels if l not in all_refs}

                    preamble_match = re.search(r'\\begin{thebibliography}{.*?}', ref_content)
                    if not preamble_match:
                        st.error("Không tìm thấy \\begin{thebibliography} trong file TLTK.")
                        st.stop()
                    preamble = preamble_match.group()

                    bib_items = re.findall(
                        r'(\\bibitem{([^}]+)}.*?)(?=\\bibitem{|\\end{thebibliography})',
                        ref_content, re.DOTALL
                    )
                    labels = [b[1] for b in bib_items]
                    label_counts = Counter(labels)
                    dup = {k: c for k, c in label_counts.items() if c > 1}

                    refs = []
                    for full, label in bib_items:
                        cleaned = re.sub(r'\s+', ' ', full).strip()
                        refs.append((label, cleaned))

                    if sort_option == "Thứ tự xuất hiện \\cite":
                        seen = set()
                        sorted_refs = []
                        for label in all_cites:
                            for lbl, bib in refs:
                                if lbl == label and lbl not in seen:
                                    sorted_refs.append(bib)
                                    seen.add(lbl)
                        for lbl, bib in refs:
                            if lbl not in seen:
                                sorted_refs.append(bib)
                    elif sort_option == "Tên tác giả đầu":
                        sorted_refs = sorted(
                            [b[1] for b in refs],
                            key=lambda x: re.findall(r'\\bibitem{[^}]+}([^,]+)', x)[0].strip()
                            if re.findall(r'\\bibitem{[^}]+}([^,]+)', x) else ''
                        )
                    elif sort_option == "Năm xuất bản (mới → cũ)":
                        sorted_refs = sorted(
                            [b[1] for b in refs],
                            key=lambda x: extract_year(x) if extract_year(x) else -9999,
                            reverse=True
                        )
                    else:  # "Năm xuất bản (cũ → mới)"
                        sorted_refs = sorted(
                            [b[1] for b in refs],
                            key=lambda x: extract_year(x) if extract_year(x) else 9999
                        )

                    tex_out = preamble + "\n\n" + "\n\n".join(sorted_refs) + "\n\n\\end{thebibliography}"

                    uncited = [l for l in labels if l not in all_cites]
                    multiply_cited = {l: {'count': all_cites.count(l), 'lines': cite_lines.get(l, [])} 
                                    for l in labels if all_cites.count(l) > 1}
                    missing = {l: cite_lines.get(l, []) for l in all_cites if l not in labels}

                    contents = []
                    for full, label in bib_items:
                        content = re.sub(r'\\bibitem{[^}]+}', '', full)
                        content = re.sub(r'\s+', ' ', content).strip().lower()
                        contents.append((label, content))

                    similar_pairs = []
                    for i in range(len(contents)):
                        for j in range(i + 1, len(contents)):
                            label_i, content_i = contents[i]
                            label_j, content_j = contents[j]
                            ratio = difflib.SequenceMatcher(None, content_i, content_j).ratio()
                            if ratio > 0.7:
                                similar_pairs.append((label_i, label_j, round(ratio * 100, 1)))

                    results = []
                    results.append(f"### Kết quả kiểm tra")

                    results.append(f"#### A - File main")

                    results.append(f"##### A1. Kiểm tra tất cả các label") 

                    if unreferenced_equation_labels:
                        equation_list = "\n".join([f"  - `{k}` (dòng {', '.join(map(str, v))})" for k, v in unreferenced_equation_labels.items()])
                        results.append(f"- Các label công thức không được \\ref hoặc \\eqref: \n{equation_list}")
                    else:
                        results.append(f"- Tất cả các label công thức đều được \\ref hoặc \\eqref")

                    if duplicate_labels:
                        dup_label_list = "\n".join([f"  - `{k}`: {v['count']} lần (dòng {', '.join(map(str, v['lines']))})" 
                                                for k, v in duplicate_labels.items()])
                        results.append(f"- Các label bị trùng: \n{dup_label_list}")
                    else:
                        results.append(f"- Không có label nào bị trùng")

                    results.append(f"##### A2. Label bảng")

                    if duplicate_table_labels:
                        dup_table_list = "\n".join([f"  - `{k}`: {v['count']} lần (dòng {', '.join(map(str, v['lines']))})" 
                                                for k, v in duplicate_table_labels.items()])
                        results.append(f"- Các label của bảng bị trùng: \n{dup_table_list}")
                    else:
                        results.append(f"- Không có label của bảng nào bị trùng")

                    if unreferenced_table_labels:
                        table_list = "\n".join([f"  - `{k}` (dòng {', '.join(map(str, v))})" for k, v in unreferenced_table_labels.items()])
                        results.append(f"- Các label của bảng không được \\ref hoặc \\eqref: \n{table_list}")
                    else:
                        results.append(f"- Tất cả các label của bảng đều được \\ref hoặc \\eqref")

                    results.append(f"##### A3. Label hình")

                    if duplicate_figure_labels:
                        dup_figure_list = "\n".join([f"  - `{k}`: {v['count']} lần (dòng {', '.join(map(str, v['lines']))})" 
                                                    for k, v in duplicate_figure_labels.items()])
                        results.append(f"- Các label của hình bị trùng: \n{dup_figure_list}")
                    else:
                        results.append(f"- Không có label của hình nào bị trùng")

                    if unreferenced_figure_labels:
                        figure_list = "\n".join([f"  - `{k}` (dòng {', '.join(map(str, v))})" for k, v in unreferenced_figure_labels.items()])
                        results.append(f"- Các label của hình không được \\ref hoặc \\eqref: \n{figure_list}")
                    else:
                        results.append(f"- Tất cả các label của hình đều được \\ref hoặc \\eqref")

                    results.append(f"##### A4. Citation")

                    results.append(f"- Tổng số lệnh \\cite: {len(all_cites)}")
                
                    if multiply_cited:
                        mult_list = "\n".join([f"  - `{k}`: {v['count']} lần (dòng {', '.join(map(str, v['lines']))})" 
                                            for k, v in multiply_cited.items()])
                        results.append(f"- Các label \\cite nhiều lần: \n{mult_list}")
                    else:
                        results.append(f"- Không có TLTK nào được \\cite nhiều hơn 1 lần")

                    if missing:
                        missing_list = "\n".join([f"  - `{k}` (dòng {', '.join(map(str, v))})" for k, v in missing.items()])
                        results.append(f"- Các label được \\cite nhưng không có trong file TLTK: \n{missing_list}")
                    else:
                        results.append(f"- Tất cả các label được \\cite đều có trong file TLTK")

                    results.append(f"#### B - File TLTK")

                    results.append(f"- Tổng số lệnh \\bibitem: {len(bib_items)}")

                    if uncited:
                        uncited_list = ", ".join(uncited)
                        results.append(f"- Các label không được \\cite: `{uncited_list}`")
                    else:
                        results.append(f"- Tất cả các label đều được \\cite")

                    if dup:
                        dup_list = "\n".join([f"  - `{k}`: {v} lần" for k, v in dup.items()])
                        results.append(f"- Các label bị trùng: \n{dup_list}")
                    else:
                        results.append(f"- Không có label nào bị trùng")

                    if similar_pairs:
                        sim_text = "\n".join([f"  - `{a}` ↔ `{b}` ➡️ {r}%" for a, b, r in similar_pairs])
                        results.append(f"- Các label có nội dung \\bibitem gần giống nhau trong file TLTK (>70%)\n{sim_text}")
                    else:
                        results.append(f"- Không phát hiện label nào có nội dung \\bibitem gần giống nhau trong file TLTK")

                    st.session_state['results'] = results
                    st.session_state['tex_out'] = tex_out

                    # === Tạo tên file theo quy tắc ===
                    if sort_option == "Thứ tự xuất hiện \\cite":
                        filename = "sorted_order.tex"
                    elif sort_option == "Tên tác giả đầu":
                        filename = "sorted_first_author.tex"
                    elif sort_option == "Năm xuất bản (mới → cũ)":
                        filename = "sorted_year_new_old.tex"
                    elif sort_option == "Năm xuất bản (cũ → mới)":
                        filename = "sorted_year_old_new.tex"
                    else:
                        filename = "sorted_output.tex"

                    st.session_state['filename'] = filename

            if 'results' in st.session_state:
                st.markdown("\n".join(st.session_state['results']))
                st.download_button(
                    "💾 Tải TLTK đã sắp xếp",
                    st.session_state['tex_out'].encode("utf-8"),
                    st.session_state['filename']
                )

        # Tab con: Truy cập Web of Science
        with subtabs[2]:
            
            st.subheader("Truy cập Web of Science - Bản quyền TDTU - Mọi lúc - Mọi nơi")

            username = "check.journal.fms.tdtu@gmail.com"
            password = "TDTu*88888888"

            st.markdown("""
            **📌 Thông tin đăng nhập:** <br> User: check.journal.fms.tdtu@gmail.com <br> Pass: TDTu*88888888
            """, unsafe_allow_html=True)

            # Link mở tab mới
            wos_url = "https://www.webofscience.com"
            st.markdown(
                f"""
                <a href="{wos_url}" target="_blank">🚀 Mở Web of Science và đăng nhập bằng tài khoản ở trên </a>
                """,
                unsafe_allow_html=True)

        # Tab con: Tài liệu nội bộ
        with subtabs[3]:
            if user in allowed_see_ttk:
                #st.subheader("📄 Tài liệu và thông tin nội bộ")
                st.info("Bạn đang xem nội dung chỉ dành cho nội bộ Khoa Toán - Thống kê")

                st.write("📌 Quy định về phân loại tạp chí để xếp hạng theo quy định TDTU")
                st.image("fig/kind.png", width=750)
                #st.image("fig/rank.png", caption="Cách tính phần trăm xếp hạng theo quy định TDTU", width=750)
                data = {
                    "STT": [1, 2, 3, 4, 5, 6, 7],
                    "Tổng số tạp chí theo CN hẹp": ["≥2000", "1500-1999", "1000-1499", "500-999", "200-499", "50-199", "<50"],
                    "Ngoại hạng CN (Q1)": ["<0.5%", "<0.5%", "<0.5%", "<0.5%", "<0.9%", "<2.5%", "<3.5%"],
                    "Hạng 1  (Q1)"  : ["<1%",  "<2%",  "<3%",  "<4%",  "<5%",  "<6%",  "<7%"],
                    "Hạng 2  (Q1-2)": ["<5%",  "<6%",  "<7%",  "<8%",  "<10%", "<11%", "<15%"],
                    "Hạng 3  (Q1-2)": ["<10%", "<11%", "<12%", "<13%", "<15%", "<16%", "<20%"],
                    "Hạng 4  (Q1-2)": ["<18%", "<19%", "<20%", "<21%", "<23%", "<24%", "<28%"],
                    "Hạng 5  (Q1-3)": ["<30%", "<31%", "<32%", "<33%", "<35%", "<36%", "<40%"],
                    "Hạng 6  (Q1-3)": ["<43%", "<44%", "<45%", "<46%", "<48%", "<49%", "<53%"],
                    "Hạng 7  (Q1-3)": ["<56%", "<57%", "<58%", "<59%", "<61%", "<62%", "<66%"],
                    "Hạng 8  (Q1-3)": ["<69%", "<70%", "<71%", "<72%", "<74%", "<75%", "<79%"],
                    "Hạng 9  (Q1-4)": ["<82%", "<83%", "<84%", "<85%", "<87%", "<88%", "<92%"],
                    "Hạng 10 (Q1-4)": ["≥82%", "≥83%", "≥84%", "≥85%", "≥87%", "≥88%", "≥92%"]
                }
                df = pd.DataFrame(data)
                st.write("📌 Cách tính phần trăm xếp hạng theo quy định TDTU")
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("""📌 Quy định về tiêu chí ký hợp đồng NCV cộng tác  

                1️⃣ Có học vị tiến sĩ                  
                2️⃣ Có kế hoạch nghiên cứu phù hợp với định hướng đào tạo  
                3️⃣ Là tác giả đứng đầu/gửi bài:  
                  * 04 công bố WoS (KHTN-KT)  
                  * Hoặc 02 công bố WoS hoặc 04 Scopus (KHXH)                  
                4️⃣ Có kế hoạch hợp tác công bố khoa học với nhân sự cơ hữu                  
                5️⃣ Đến Trường làm việc ít nhất 1 lần nếu chưa từng đến                  
                6️⃣ Không có dấu hiệu vi phạm liêm chính học thuật                  
                7️⃣ Có thể làm các hoạt động khác theo phê duyệt của Trường  
                🔔 Ghi chú:  
                  * Trường không trả thù lao riêng cho những hoạt động này  
                  * Phải đăng ký ít nhất 2 hoạt động/năm trong danh sách 17 hoạt động  
                  * Các hoạt động phải đủ định mức theo quy định  
                  Chi tiết 17 hoạt động:
                """)
                data = [
                (1, "Giảng dạy lý thuyết/thực hành", "1 môn/năm"),
                (2, "Hướng dẫn nghiên cứu sinh (NCS)", "1 NCS (tính trong 3 năm)"),
                (3, "Hướng dẫn luận văn thạc sĩ", "1 học viên/năm"),
                (4, "Hướng dẫn khóa luận tốt nghiệp / đồ án / đề tài sinh viên", "2 SV/năm"),
                (5, "Hướng dẫn đề tài NCKH sinh viên", "1 đề tài/năm"),
                (6, "Phản biện đề tài NCKH", "4 đề/năm"),
                (7, "Chấm luận văn thạc sĩ", "2 luận văn/năm"),
                (8, "Đánh giá luận án tiến sĩ", "1 hội đồng/năm"),
                (9, "Báo cáo Journal Club", "2 báo cáo/năm"),
                (10, "Hướng dẫn nghiên cứu sau tiến sĩ (postdoc)", "1 postdoc/năm"),
                (11, "Báo cáo chuyên đề nghiên cứu khoa học", "4 chuyên đề/năm"),
                (12, "Giới thiệu chuyên gia hợp tác với trường", "2 chuyên gia/năm"),
                (13, "Giới thiệu NCV/giảng viên về trường", "1 người/năm"),
                (14, "Tham gia trình bày tại hội thảo khoa học", "2 báo cáo/năm"),
                (15, "Là tác giả chính bài báo không được tài trợ", "2 bài/năm"),
                (16, "Tham gia hội thảo quốc tế với vai trò session chair", "1 hội thảo/năm"),
                (17, "Tham gia biên tập/bình duyệt cho tạp chí", "1 issue/năm"),
                        ]
                df = pd.DataFrame(data, columns=["STT", "Hoạt động", "Định mức yêu cầu"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.write("📌 Biểu mẫu: đang cập nhật")
            else:
                st.warning("🚫 Bạn chưa được phân quyền để xem tài liệu nội bộ Khoa Toán - Thống kê")

        # Tab con: Admin
        with subtabs[4]:
            if user in unblocked_admins:
                #st.subheader("🔒 Admin: Gỡ khóa email bị chặn")

                blocked = st.session_state.get('blocked_emails', [])
                st.write(f"📌 Danh sách email bị khoá ({len(blocked)}):")
                if blocked:
                    for e in blocked:
                        st.write(f"🔒 {e}")
                else:
                    st.info("✅ Không có email nào đang bị khoá")

                if blocked:
                    emails_to_unblock = st.multiselect(
                        "📬 Chọn một hoặc nhiều email cần gỡ khoá",
                        blocked
                    )

                    if st.button("🔓 Gỡ khoá các email đã chọn"):
                        if emails_to_unblock:
                            for email in emails_to_unblock:
                                if email in blocked:
                                    blocked.remove(email)

                                    # Gửi mail thông báo
                                    msg = MIMEText(
                                        f"Xin chào,\n\nTài khoản email [{email}] đã được gỡ khoá thành công.\n"
                                        "Bạn có thể đăng nhập lại vào ứng dụng Check-Journal (TDTU).\n\n"
                                        "Trân trọng!"
                                    )
                                    msg['Subject'] = "Thông báo: Tài khoản của bạn đã được gỡ khoá"
                                    msg['From'] = sender_email
                                    msg['To'] = email

                                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                                        server.login(sender_email, sender_pass)
                                        server.send_message(msg)

                            # Ghi file mới
                            with open("blocked_emails.txt", "w") as f:
                                for e in blocked:
                                    f.write(e + "\n")

                            st.success(f"✅ Đã gỡ khoá {len(emails_to_unblock)} email và gửi thông báo xong")
                        else:
                            st.warning("⚠️ Bạn chưa chọn email nào để gỡ khoá")
                else:
                    st.info("✅ Danh sách khoá trống, không cần gỡ")

            else:
                st.warning("🔒 Chức năng này chỉ dành cho Admin")

    with tabs[7]:
        st.info("Thông tin ứng dụng")
        st.markdown("""
        **Tên ứng dụng:** Ứng dụng Check-Journal 
        
        **Ngày khởi tạo:** 24/09/2024

        **Tác giả:** Nguyễn Hữu Cần (Khoa Toán - Thống kê, TDTU)  

        **Thông tin tác giả:** https://fms.tdtu.edu.vn/nhan-su/thac-si-nguyen-huu-can
        
        **Nguồn dữ liệu:** https://www.scimagojr.com , https://www.scopus.com/sources.uri , https://mjl.clarivate.com

        **Email hỗ trợ:** nguyenhuucan@tdtu.edu.vn

        """)
        
        st.info("Mọi góp ý vui lòng liên hệ qua email để được phản hồi")
