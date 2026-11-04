"""BƯỚC 2 — Làm sạch dữ liệu: 7 bước (slide 7 + Giai đoạn 1 slide 8).

    1. Gộp dữ liệu 2 nguồn
    2. Khử trùng lặp theo (tên việc + công ty) đã bỏ dấu
    3. Chuẩn hóa lương: salary_min / salary_max (VND); rỗng hoặc 0 -> gắn nhãn "Thỏa thuận", KHÔNG xóa
    4. Chuẩn hóa địa điểm: giá trị thô -> tỉnh/thành
    5. Lọc country = Việt Nam
    6. Phân loại contract_type, chỉ giữ tin ghi RÕ internship / part-time
       (loại tin chỉ suy ra từ từ khóa tìm kiếm)
    7. Gom ngành (category) + Encoding category, location cho thống kê / ML

Đầu vào : data/raw/<nguồn>_<YYYY-MM-DD>.csv — tất cả các ngày (do 1_crawl.py tạo, không bị sửa)
Đầu ra  : data/clean/jobs_clean_<YYYY-MM-DD>.csv + .xlsx (sheet "bao_cao_7_buoc" = số tin vào/ra từng bước)
          -> mỗi ngày chạy ra 1 bộ file riêng mang ngày hôm đó, file ngày cũ giữ nguyên
"""
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path(__file__).parent / "data" / "raw"
CLEAN_DIR = Path(__file__).parent / "data" / "clean"
TY_GIA_URL = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"   # tối đa 1 lần / 5 phút
SALARY_MIN_OK, SALARY_MAX_OK = 0.5, 100     # khoảng lương tháng hợp lý (triệu VND)


def bo_dau(text) -> str:
    """'Thực tập sinh Đà Nẵng' -> 'thuc tap sinh da nang' (chỉ giữ chữ + số)."""
    s = unicodedata.normalize("NFD", str(text or "")).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ============================================================ lương
def lay_ty_gia() -> tuple[dict, str]:
    """Tỷ giá CHUYỂN KHOẢN hiện tại của Vietcombank -> ({'USD': 26xxx.0, 'EUR': ...}, thời điểm cập nhật)."""
    r = requests.get(TY_GIA_URL, timeout=30)
    r.raise_for_status()
    goc = ET.fromstring(r.content)
    ty_gia = {e.get("CurrencyCode"): float(e.get("Transfer").replace(",", ""))
              for e in goc.iter("Exrate") if re.fullmatch(r"[\d,.]+", e.get("Transfer") or "")}
    return ty_gia, goc.findtext("DateTime", "")


def parse_salary(text, ty_gia: dict):
    """'Lên đến 8 Triệu' -> (None, 8e6, 'MONTH'); '4 - 5 triệu' -> (4e6, 5e6, 'MONTH');
    '25.000đ/giờ' -> (25000, 25000, 'HOUR'); 'Thỏa thuận' -> (None, None, None).
    Ngoại tệ (USD, EUR, JPY... hoặc $) quy đổi theo ty_gia = {mã: VND} lấy lúc chạy."""
    raw = str(text or "").lower()
    key = bo_dau(text)
    if not re.search(r"\d", raw):
        return None, None, None
    unit = "HOUR" if re.search(r"/\s*(giờ|h)\b|theo giờ|\bgiờ\b", raw) else "MONTH"
    nums = []
    for num, word in re.findall(r"(\d+(?:[.,]\d+)*)(?![.,]?\d)\s*(?:(triệu|tr|m|k|nghìn|ngàn)(?![a-zà-ỹ]))?", raw)[:2]:
        if (word or num[0] == "0") and re.fullmatch(r"\d+[.,]\d+", num):   # 7,5 triệu / 0.082 triệu
            val = float(num.replace(",", "."))
        else:                                                    # 1,000 / 10.000.000
            val = float(re.sub(r"[.,](?=\d{3}\b)", "", num).replace(",", "."))
        nums.append([val, {"triệu": 1e6, "tr": 1e6, "m": 1e6, "k": 1e3, "nghìn": 1e3, "ngàn": 1e3}.get(word)])
    ma = next((m.upper() for m in re.findall(r"\b[a-z]{3}\b", raw) if m.upper() in ty_gia),
              "USD" if "$" in raw else None)
    for i, (val, mult) in enumerate(nums):
        if mult:
            continue
        if val >= 1000:                    # "800.000 - 5 triệu": số đầu đã tính bằng đồng
            nums[i][1] = 1
            continue
        other = nums[1 - i][1] if len(nums) == 2 else None   # "4 - 5 triệu": mượn đơn vị số sau
        nums[i][1] = other or (1e6 if unit == "MONTH" and not ma else 1)
    rate = ty_gia[ma] if ma else 1
    vals = [v * m * rate for v, m in nums]
    if len(vals) == 2:
        return min(vals), max(vals), unit
    if re.search(r"len den|toi da|up ?to|duoi", key) or "<" in raw:
        return None, vals[0], unit
    if re.search(r"\btren\b|\btu\b|toi thieu", key) or ">" in raw:
        return vals[0], None, unit
    return vals[0], vals[0], unit


# Tự kiểm tra nhanh hàm đọc lương với tỷ giá giả (chạy mỗi lần import)
_TG = {"USD": 25_000.0, "EUR": 30_000.0}
assert parse_salary("500 - 1,000 USD", _TG)[:2] == (12.5e6, 25e6)
assert parse_salary("$800", _TG)[:2] == (20e6, 20e6)
assert parse_salary("1.000 EUR", _TG)[:2] == (30e6, 30e6)
assert parse_salary("800.000 - 5 Triệu VND", _TG)[:2] == (8e5, 5e6)
assert parse_salary("Thỏa thuận", _TG) == (None, None, None)


# ============================================================ địa điểm
TINH_THANH = [
    "Hà Nội", "TP. Hồ Chí Minh", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "An Giang", "Bà Rịa - Vũng Tàu",
    "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cao Bằng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang", "Hòa Bình", "Hưng Yên",
    "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An",
    "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam",
    "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình",
    "Thái Nguyên", "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang", "Vĩnh Long",
    "Vĩnh Phúc", "Yên Bái",
]
TINH = {bo_dau(t): t for t in TINH_THANH}
TINH.update({"ho chi minh": "TP. Hồ Chí Minh", "hcm": "TP. Hồ Chí Minh", "tphcm": "TP. Hồ Chí Minh",
             "sai gon": "TP. Hồ Chí Minh", "hue": "Thừa Thiên Huế", "vung tau": "Bà Rịa - Vũng Tàu",
             "ba ria vung tau": "Bà Rịa - Vũng Tàu", "dak lak": "Đắk Lắk", "dak nong": "Đắk Nông"})
NUOC_NGOAI = {"nuoc ngoai", "nhat ban", "japan", "han quoc", "korea", "dai loan", "singapore", "duc", "uc", "my"}


def to_province(location_text):
    """'Hà Nội, Hồ Chí Minh' -> 'Hà Nội' (tỉnh đầu tiên nhận ra được); không nhận ra -> None."""
    for part in re.split(r"[,|;/]", str(location_text or "")):
        k = re.sub(r"^(tinh|thanh pho|tp)\s+", "", bo_dau(part))
        if k in TINH:
            return TINH[k]
    return None


def to_country(row) -> str:
    parts = {re.sub(r"^(tinh|thanh pho|tp)\s+", "", bo_dau(p)) for p in re.split(r"[,|;/]", str(row.location_text))}
    if row.location is None and parts & NUOC_NGOAI:
        return "Nước ngoài"
    if row.location is not None or bo_dau(row.country) in ("vn", "viet nam", "vietnam", ""):
        return "Việt Nam"
    return "Nước ngoài"


# ============================================================ loại hình
INTERN = re.compile(r"\b(thuc tap|tts|intern|internship)\b")
PART = re.compile(r"\b(part time|parttime|ban thoi gian|lam them)\b")


def to_contract_type(row) -> str:
    """Chỉ tính là thực tập / part-time khi GHI RÕ ở: loại hình nhà tuyển dụng chọn (JSON-LD),
    ô 'Hình thức', hoặc tiêu đề tin. Ví dụ 'International Sales' (khớp từ khóa 'intern') -> 'khác'."""
    et, text = str(row.employment_type).upper(), bo_dau(row.hinh_thuc) + " | " + bo_dau(row.title)
    intern = "INTERN" in et or bool(INTERN.search(text))
    part = "PART_TIME" in et or bool(PART.search(text))
    return "internship/part-time" if intern and part else "internship" if intern else "part-time" if part else "khác"


# ============================================================ ngành
NHOM_NGANH = {   # nhóm -> các cụm từ khóa (đã bỏ dấu), cách nhau dấu phẩy
    "CNTT - Phần mềm": "cntt, it, phan mem, phan cung, lap trinh, cong nghe thong tin, software, developer, "
                       "data, du lieu, tester, game",
    "Kế toán - Tài chính - Ngân hàng": "ke toan, kiem toan, tai chinh, ngan hang, chung khoan, dau tu, thue, bao hiem",
    "Marketing - Truyền thông": "marketing, truyen thong, quang cao, pr, tiep thi, content, seo, su kien, bao chi, "
                                "bien tap, digital",
    "Kinh doanh - Bán hàng": "kinh doanh, ban hang, sales, ban le, thuong mai dien tu, bat dong san",
    "Nhân sự - Hành chính": "nhan su, hanh chinh, van phong, thu ky, tro ly, le tan, phap ly, phap luat, tuyen dung",
    "Chăm sóc khách hàng": "cham soc khach hang, cskh, tu van, telesales, call center",
    "Thiết kế - Sáng tạo": "thiet ke, do hoa, my thuat, thoi trang, video, kien truc",
    "Logistics - Xuất nhập khẩu": "logistics, xuat nhap khau, giao nhan, van chuyen, kho, mua hang, chuoi cung ung",
    "Kỹ thuật - Sản xuất": "ky thuat, co khi, dien, dien tu, tu dong hoa, xay dung, san xuat, bao tri, qa, qc, "
                           "hoa hoc, moi truong",
    "Giáo dục - Ngôn ngữ": "giao duc, dao tao, giang day, giao vien, gia su, tro giang, phien dich, bien dich, ngoai ngu",
    "Nhà hàng - Khách sạn - Du lịch": "nha hang, khach san, du lich, phuc vu, pha che, barista, nau an, spa, lam dep",
    "Y tế - Dược": "y te, duoc, dieu duong, benh vien, nha khoa",
}
NHOM_NGANH = {g: [f" {w.strip()} " for w in ws.split(",")] for g, ws in NHOM_NGANH.items()}
NHAN_CHUNG = {"moi tot nghiep thuc tap", "thuc tap", "moi tot nghiep", "lam ban thoi gian", "sinh vien lam them",
              "nganh nghe khac", "khac", "thong ke", "freelance"}


def _nhom(text: str):
    t = f" {bo_dau(text)} "
    for g, words in NHOM_NGANH.items():
        if any(w in t for w in words):
            return g
    return None


def to_category(row) -> str:
    """Nhãn ngành 2 trang khác nhau -> gom về 12 nhóm chung. Ưu tiên nhóm khớp tiêu đề tin."""
    labels = [l for l in str(row.industry).split(",") if bo_dau(l) and bo_dau(l) not in NHAN_CHUNG]
    groups = [g for g in map(_nhom, labels) if g]
    by_title = _nhom(row.title)
    if by_title and (by_title in groups or not groups):
        return by_title
    return groups[0] if groups else "Khác"


def to_years(text):
    """'Chưa có kinh nghiệm' -> 0 ; '1 - 2 Năm' -> 1 ; '6 tháng' -> 0.5"""
    t = bo_dau(text)
    if re.search(r"khong (yeu cau|yc)|chua co|duoi 1 nam", t):
        return 0.0
    m = re.search(r"(\d+)\s*(?:\d+\s*)?(nam|thang)", t)
    return (int(m.group(1)) / (12 if m.group(2) == "thang" else 1)) if m else None


# ============================================================ chạy 7 bước
def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    log = []

    def step(msg):
        print(msg)
        log.append(msg)

    today = datetime.now()
    step("=" * 60 + f"\nBƯỚC 2: LÀM SẠCH DỮ LIỆU (7 bước) — ngày {today:%d/%m/%Y}\n" + "=" * 60)

    # 1. Gộp tất cả file theo ngày: careerviet_2026-10-13.csv, joboko_2026-10-13.csv, ...
    files = sorted(RAW_DIR.glob("*_????-??-??.csv"))
    if not files:
        sys.exit("Chưa có dữ liệu trong data/raw — hãy chạy 1_crawl.py trước.")
    df = pd.concat([pd.read_csv(f, dtype=str, encoding="utf-8-sig") for f in files], ignore_index=True).fillna("")
    df["crawl_date"] = df["crawled_at"].str[:10]
    step(f"[1] Gộp 2 nguồn: {len(df):,} tin thô từ {len(files)} file  {df['source'].value_counts().to_dict()}")
    step(f"    Số tin theo ngày thu thập: {df['crawl_date'].value_counts().sort_index().to_dict()}")

    # 2. Khử trùng lặp
    n = len(df)
    df = df.drop_duplicates(["source", "job_id"], keep="last")
    # Bỏ đuôi "... làm việc tại <tỉnh>" để nhận ra tin đăng lặp cho nhiều tỉnh (vd gia sư online)
    ten_viec = df["title"].str.replace(r"\s*(làm việc\s+)?tại\s+[^,\-\]\)]+$", "", regex=True, case=False)
    df["_key"] = ten_viec.map(bo_dau) + "|" + df["company"].map(bo_dau)
    df = df.drop_duplicates("_key").drop(columns="_key").reset_index(drop=True)
    step(f"[2] Khử trùng lặp (tên việc + công ty, đã bỏ dấu): {n:,} -> {len(df):,} tin (loại {n - len(df):,})")

    # 3. Lương — ngoại tệ quy đổi theo tỷ giá Vietcombank lúc chạy (không dùng tỷ giá cố định)
    try:
        ty_gia, cap_nhat = lay_ty_gia()
    except (requests.RequestException, ET.ParseError) as e:
        sys.exit(f"\nLỖI: không lấy được tỷ giá Vietcombank ({e}). Kiểm tra mạng rồi chạy lại "
                 "`python 2_lam_sach.py` — dữ liệu thô đã lưu, không mất gì.")
    step(f"    Tỷ giá Vietcombank (chuyển khoản, cập nhật {cap_nhat}): 1 USD = {ty_gia['USD']:,.0f} đ")
    parsed = df["salary_text"].map(lambda t: parse_salary(t, ty_gia))
    # Đơn vị: TRIỆU VND (vd 4.5 = 4.500.000đ) cho gọn, dễ đọc, dễ vẽ biểu đồ
    df["salary_min"] = [round(p[0] / 1e6, 3) if p[0] else None for p in parsed]
    df["salary_max"] = [round(p[1] / 1e6, 3) if p[1] else None for p in parsed]
    df["salary_unit"] = [{"MONTH": "tháng", "HOUR": "giờ"}.get(p[2], "") for p in parsed]
    df["salary_mid"] = df[["salary_min", "salary_max"]].mean(axis=1).round(3)
    no_salary = df["salary_min"].fillna(0).eq(0) & df["salary_max"].fillna(0).eq(0)
    df["salary_label"] = no_salary.map({True: "Thỏa thuận", False: "Có lương"})
    # Lương tháng ngoài khoảng 0,5–100 triệu là bất thường (vd gia sư tính theo buổi, nhập sai) -> gắn cờ, KHÔNG xóa
    df["salary_outlier"] = (df["salary_unit"] == "tháng") & ~df["salary_mid"].between(SALARY_MIN_OK, SALARY_MAX_OK)
    step(f"[3] Chuẩn hóa lương: {(~no_salary).sum():,} tin có lương số ({(~no_salary).mean():.1%}), "
         f"{no_salary.sum():,} tin 'Thỏa thuận' ({no_salary.mean():.1%}) -> gắn nhãn, KHÔNG xóa; "
         f"{df['salary_outlier'].sum():,} tin lương bất thường -> gắn cờ salary_outlier")

    # 4. Địa điểm
    raw_values = {p.strip() for t in df["location_text"] for p in re.split(r"[,|;/]", t) if p.strip()}
    df["location"] = df["location_text"].map(to_province)
    step(f"[4] Chuẩn hóa địa điểm: {len(raw_values):,} giá trị thô -> {df['location'].nunique():,} tỉnh/thành "
         f"({df['location'].isna().sum():,} tin không ghi/không nhận ra tỉnh)")

    # 5. country = Việt Nam
    n = len(df)
    df["country"] = df.apply(to_country, axis=1)
    df = df[df["country"] == "Việt Nam"].copy()
    step(f"[5] Lọc country = Việt Nam: {n:,} -> {len(df):,} tin (loại {n - len(df):,} tin nước ngoài)")

    # 6. contract_type
    n = len(df)
    df["contract_type"] = df.apply(to_contract_type, axis=1)
    df = df[df["contract_type"] != "khác"].copy()
    step(f"[6] Lọc contract_type ghi RÕ internship/part-time: {n:,} -> {len(df):,} tin "
         f"(loại {n - len(df):,} tin chỉ suy từ từ khóa tìm kiếm)  {df['contract_type'].value_counts().to_dict()}")

    # 7. Ngành + kinh nghiệm + encoding
    df["category"] = df.apply(to_category, axis=1)
    df["experience_years"] = df["experience"].map(to_years)
    df["con_han"] = pd.to_datetime(df["deadline"], errors="coerce") >= pd.Timestamp(today.date())
    df["category_code"] = df["category"].astype("category").cat.codes
    df["location_code"] = df["location"].fillna("Không rõ").astype("category").cat.codes
    step(f"[7] Gom {df['category'].nunique()} nhóm ngành + encoding category_code, location_code")

    # Sắp cột theo nhóm, sắp dòng theo ngành -> tỉnh -> tên việc cho dễ đọc
    df = df[CLEAN_COLUMNS].sort_values(["category", "location", "title"]).reset_index(drop=True)
    # Mỗi ngày chạy ra 1 bộ file riêng mang ngày hôm đó; file các ngày trước giữ nguyên
    day = f"{today:%Y-%m-%d}"
    out = CLEAN_DIR / f"jobs_clean_{day}.csv"
    try:
        df.to_csv(out, index=False, encoding="utf-8-sig", float_format="%g")
    except PermissionError:
        sys.exit(f"\nLỖI: {out.name} đang mở trong Excel -> đóng file rồi chạy lại.")
    step(f"\nKẾT QUẢ: {len(df):,} tin -> {out}")
    step(f"Dữ liệu thu thập từ ngày {df['crawl_date'].min()} đến ngày {df['crawl_date'].max()}")

    # Bản Excel để XEM dữ liệu sạch (có định dạng); code phân tích vẫn đọc file .csv
    save_excel({"du_lieu_sach": df, "bao_cao_7_buoc": pd.DataFrame({"Báo cáo làm sạch": log})},
               CLEAN_DIR / f"jobs_clean_{day}.xlsx")


CLEAN_COLUMNS = [
    "source", "job_id", "title", "company",                                   # tin
    "category", "contract_type", "location", "country",                       # phân loại
    "salary_min", "salary_max", "salary_mid", "salary_unit", "salary_label",  # lương (triệu VND)
    "salary_outlier", "salary_text", "experience_years",
    "date_posted", "deadline", "con_han",                                     # thời gian (con_han = còn hạn nộp)
    "category_code", "location_code",                                         # mã hóa cho ML
    "url", "crawl_date",                                                      # truy vết: link gốc, ngày thu thập
]


def save_excel(sheets: dict, path: Path) -> None:
    """Xuất Excel dễ xem: tiêu đề đậm có nền, cố định dòng đầu, bộ lọc, độ rộng cột vừa nội dung."""
    from openpyxl.styles import Alignment, Font, PatternFill
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as xw:
            for name, data in sheets.items():
                data.to_excel(xw, sheet_name=name, index=False)
                ws = xw.sheets[name]
                ws.freeze_panes = "A2"
                ws.auto_filter.ref = ws.dimensions
                for cell in ws[1]:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill("solid", fgColor="2F5597")
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                for col in ws.columns:
                    width = max(len(str(c.value or "")) for c in list(col)[:200])
                    ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 8), 50)
        print(f"  Đã xuất bản xem bằng Excel: {path}")
    except PermissionError:
        print(f"  (Bỏ qua {path.name}: file đang mở trong Excel — đóng file rồi chạy lại)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
