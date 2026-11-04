"""Bảng phân tích thị trường thực tập & part-time — Nhóm 3 (PTDL 71DAEE10012).

Chạy: mở file này trong VS Code bấm ▶ Run, hoặc  python web/app.py  /  python -m streamlit run web/app.py
→ trình duyệt tự mở http://localhost:8501 (dừng: Ctrl+C trong terminal)

Đọc file sạch mới nhất data/clean/jobs_clean_<ngày>.csv; phân tích dùng chung hàm trong 4_phan_tich.py.
Nút "Lấy dữ liệu hôm nay" chạy chay.py (thu thập → làm sạch → phân tích) ở nền, thay cho gõ lệnh trong terminal.
Giao diện (màu, khung) nằm riêng ở web/style.css.
"""
import html
import importlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from streamlit import runtime
from streamlit.web import cli

ROOT = Path(__file__).resolve().parent.parent
if not runtime.exists():          # chạy bằng "python web/app.py" (nút ▶ VS Code) -> tự bật web Streamlit
    os.chdir(ROOT)                # để Streamlit đọc .streamlit/config.toml ở thư mục gốc
    sys.argv = ["streamlit", "run", __file__]
    sys.exit(cli.main())

sys.path.insert(0, str(ROOT))
pt = importlib.import_module("4_phan_tich")
lam_sach = importlib.import_module("2_lam_sach")

LOG = ROOT / "data" / "cap_nhat.log"
XANH, XANH_LA, CAM, CHU = "#0D9488", "#0284C7", "#D97706", "#134E4A"
TAT_CA = "Tất cả"
HIEN_PHAN_TICH = False          # đặt True để hiện lại tab "Phân tích thống kê"

st.set_page_config(page_title="Thị trường thực tập & part-time — Nhóm 3", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)


# ============================================================================================ dữ liệu
@st.cache_data
def tai(path: str, sua_luc: float) -> pd.DataFrame:      # sua_luc: file ghi lại trong ngày thì đọc lại
    return pt.tai_du_lieu(Path(path))


@st.cache_resource
def mo_hinh(path: str, sua_luc: float):
    df = tai(path, sua_luc)
    return pt.hoi_quy_luong(df), pt.phan_loai_co_luong(df)[0], pt.kiem_dinh(df)


@st.cache_resource
def tien_trinh() -> dict:
    """Tiến trình chay.py đang chạy nền — dùng chung cho mọi tab trình duyệt."""
    # shortcut: khởi động lại web khi đang cập nhật thì web không còn theo dõi tiến trình cũ, nó vẫn chạy tiếp
    return {"p": None, "bat_dau": None}


def so(x: float) -> str:
    """3.0 -> '3' ; 3.25 -> '3,25'"""
    return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def ngay_vn(d) -> str:
    return pd.to_datetime(d).strftime("%d/%m/%Y")


def loc(d: pd.DataFrame, ngay: str, loai: str, nganh: str, noi: str) -> pd.DataFrame:
    if ngay != TAT_CA:
        d = d[d["crawl_date"] == ngay]
    if loai != TAT_CA:
        d = d[d["loai_hinh"].isin([loai, "Cả hai"])]
    if nganh != TAT_CA:
        d = d[d["category"] == nganh]
    if noi != TAT_CA:
        d = d[d["location"] == noi]
    return d


def cot(s: pd.Series, ten: str, mau: str = XANH, to_dam: str | None = None, dinh_dang: str = "d"):
    """Biểu đồ cột ngang: nhãn bên trái, số liệu cuối cột, mỗi dòng cao bằng nhau."""
    d = s.rename_axis("nhan").reset_index(name="gia_tri")
    mau_cot = alt.condition(alt.datum.nhan == to_dam, alt.value(CAM), alt.value(mau)) if to_dam else alt.value(mau)
    # Chừa sẵn chỗ cho nhãn 2 bên: Vega đo chữ trước khi font web tải xong nên tự đo sẽ bị cắt nhãn
    cho_nhan = int(d["nhan"].str.len().max() * 7.6) + 16
    goc = alt.Chart(d).encode(
        y=alt.Y("nhan:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=280, labelFontSize=13, labelColor=CHU, labelPadding=8, ticks=False,
                              domain=False, minExtent=cho_nhan, maxExtent=cho_nhan)),
        x=alt.X("gia_tri:Q", axis=None, scale=alt.Scale(domainMin=0, domainMax=float(d["gia_tri"].max()) * 1.15)))
    bar = goc.mark_bar(cornerRadiusEnd=3, height={"band": 0.7}).encode(
        color=mau_cot, tooltip=[alt.Tooltip("nhan", title=" "), alt.Tooltip("gia_tri", title=ten, format=dinh_dang)])
    nhan_so = goc.mark_text(align="left", dx=5, baseline="middle", color=CHU, fontSize=12).encode(
        text=alt.Text("gia_tri:Q", format=dinh_dang))
    return (bar + nhan_so).properties(height=max(90, 32 * len(d))).configure_view(strokeWidth=0)


def the_kpi(nhan: str, gia_tri: str, phu: str = "") -> str:
    return f'<div class="kpi"><div class="kpi-nhan">{nhan}</div><div class="kpi-so">{gia_tri}</div>' \
           f'<div class="kpi-phu">{phu}&nbsp;</div></div>'


def the_ds(tieu_de: str, dong: list[str]) -> str:
    return f'<div class="card"><h4>{tieu_de}</h4><ul>' + "".join(f"<li>{x}</li>" for x in dong) + "</ul></div>"


def nhan_dinh(df: pd.DataFrame, luong: pd.DataFrame) -> dict[str, list[str]]:
    """Nhận định + khuyến nghị cho 3 nhóm người dùng, tính từ dữ liệu đang lọc."""
    n = len(df)
    nganh, tinh, cty = df["category"].value_counts(), df["location"].value_counts(), df["company"].value_counts()
    sv = [f"Nhiều tin nhất: <b>{nganh.index[0]}</b> ({nganh.iloc[0] / n:.0%} số tin)"
          + (f", tiếp theo là <b>{nganh.index[1]}</b> ({nganh.iloc[1] / n:.0%})." if len(nganh) > 1 else ".")]
    if len(tinh):
        sv.append(f"<b>{tinh.index[0]}</b> chiếm {tinh.iloc[0] / n:.0%} số tin — nơi có nhiều lựa chọn nhất.")
    if len(luong) >= 5:
        q1, tv, q3 = luong["salary_mid"].quantile([.25, .5, .75])
        sv.append(f"Phần lớn tin trả <b>{so(q1)}–{so(q3)} triệu/tháng</b>; khi thương lượng nên đề xuất quanh "
                  f"mức phổ biến {so(tv)} triệu.")
    con_ngay = (pd.to_datetime(df["deadline"], errors="coerce") - pd.Timestamp.today().normalize()).dt.days
    sv.append(f"{int(con_ngay.between(0, 7).sum())} tin hết hạn nộp trong 7 ngày tới — nên ưu tiên nộp sớm.")

    truong = [f"Ngành cần thực tập sinh nhiều nhất: <b>{', '.join(nganh.head(3).index)}</b> — ưu tiên tìm doanh "
              "nghiệp đối tác thực tập ở các ngành này.",
              f"Doanh nghiệp đăng nhiều tin nhất: <b>{html.escape(cty.index[0])}</b> ({cty.iloc[0]} tin)."]
    nganh_that = nganh.drop("Khác", errors="ignore")                 # "Khác" không phải một ngành cụ thể
    if len(nganh_that) > 3:
        truong.append(f"Ngành ít tin: <b>{nganh_that.index[-1]}</b> ({nganh_that.iloc[-1]} tin) — sinh viên ngành "
                      "này cần chủ động tìm thêm kênh khác.")

    dn = [f"<b>{1 - df['co_luong'].mean():.0%}</b> tin không ghi rõ lương (chỉ ghi 'thỏa thuận')."]
    giau = (df[df["category"] != "Khác"].groupby("category")["co_luong"].agg(["mean", "size"])
            .query("size >= 20"))
    if not giau.empty:
        x = giau["mean"].idxmin()
        dn.append(f"Ngành ít ghi lương nhất: <b>{x}</b> ({1 - giau.loc[x, 'mean']:.0%} tin không ghi) — ghi rõ lương "
                  "giúp tin nổi bật hơn trong nhóm này.")
    if len(luong) >= 5:
        dn.append(f"Mức lương phổ biến trên thị trường là <b>{so(luong['salary_mid'].median())} triệu/tháng</b> — dùng làm "
                  "mốc khi đặt lương thực tập / part-time.")
    return {"Sinh viên": sv, "Nhà trường": truong, "Doanh nghiệp tuyển dụng": dn}


def luong_the(r) -> str:
    if r.co_luong == 0:
        return f'<span class="chip chip-an">Thỏa thuận · ước tính {so(r.uoc_tinh)} tr</span>'
    if r.salary_unit != "tháng" or r.salary_outlier:
        return f'<span class="chip chip-tien">{html.escape(str(r.salary_text))}</span>'
    lo, hi = r.salary_min, r.salary_max
    if pd.notna(lo) and pd.notna(hi) and lo != hi:
        txt = f"{so(lo)} – {so(hi)} tr/tháng"
    elif pd.isna(lo):
        txt = f"Đến {so(hi)} tr/tháng"
    elif pd.isna(hi):
        txt = f"Từ {so(lo)} tr/tháng"
    else:
        txt = f"{so(lo)} tr/tháng"
    return f'<span class="chip chip-tien">{txt}</span>'


# ============================================================================================ cập nhật dữ liệu
def bat_dau_cap_nhat() -> None:
    LOG.parent.mkdir(exist_ok=True)   # máy mới tải code về chưa có thư mục data
    with open(LOG, "wb") as f:
        p = subprocess.Popen([sys.executable, "-u", "chay.py"], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    tien_trinh().update(p=p, bat_dau=datetime.now())


def cuoi_log(n: int = 8) -> str:
    return "\n".join(LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]) if LOG.exists() else ""


@st.fragment(run_every=5)
def khung_cap_nhat(ngay_moi: str) -> None:
    tt = tien_trinh()
    p = tt["p"]
    if p is not None and p.poll() is None:
        phut = (datetime.now() - tt["bat_dau"]).seconds // 60
        st.info(f"Đang lấy dữ liệu, đã chạy {phut} phút (thường 15–45 phút).")
        st.code(cuoi_log(2), language=None)
        return
    if p is not None:
        if p.returncode == 0:
            st.success("Đã cập nhật xong.")
        else:
            st.error(f"Cập nhật bị lỗi (mã {p.returncode}). Xem dòng cuối nhật ký bên dưới.")
        st.code(cuoi_log(), language=None)
        if st.button("Hiển thị dữ liệu mới", use_container_width=True):
            tt["p"] = None
            st.rerun()
        return
    if st.button("Lấy dữ liệu hôm nay", type="primary", use_container_width=True):
        bat_dau_cap_nhat()
        st.rerun(scope="fragment")
    st.caption(f"Dữ liệu đến {ngay_moi}. Cần mạng và đóng các file Excel trong thư mục data.")


def xoa_bo_loc() -> None:
    for k in ("ngay", "loai", "nganh", "noi"):
        st.session_state[k] = TAT_CA


# ============================================================================================ trang
files = sorted(pt.CLEAN_DIR.glob("jobs_clean_*.csv"))
dau, nut = st.columns([3, 1], vertical_alignment="top")
dau.markdown("""<div class="dau-trang"><h1>Thị trường thực tập & part-time tại Việt Nam</h1>
<p>Bảng phân tích cho sinh viên, nhà trường và doanh nghiệp · Nguồn: CareerViet, JobOKO</p></div>""",
             unsafe_allow_html=True)
with nut:
    khung_cap_nhat(ngay_vn(files[-1].stem[-10:]) if files else "—")
if not files:
    st.warning("Chưa có dữ liệu. Bấm **Lấy dữ liệu hôm nay** ở góc trên bên phải.")
    st.stop()

file = files[-1]
df_all = tai(str(file), file.stat().st_mtime).copy()
(hq, model), bang_phan_loai, bang_kiem_dinh = mo_hinh(str(file), file.stat().st_mtime)
df_all["uoc_tinh"] = model.predict(df_all[pt.CAT_FEATURES + pt.NUM_FEATURES]).clip(min=0.5).round(1)
so_tin_ngay = df_all["crawl_date"].value_counts().sort_index(ascending=False)

with st.container(border=True):
    c0, c1, c2, c3, c4 = st.columns([1.3, 1, 1.3, 1, .7], vertical_alignment="bottom")
    ngay = c0.selectbox("Ngày lấy tin", [TAT_CA] + so_tin_ngay.index[:5].tolist(), key="ngay",
                        format_func=lambda d: f"Tất cả ({len(df_all):,} tin)".replace(",", ".") if d == TAT_CA
                        else f"{ngay_vn(d)} ({so_tin_ngay[d]} tin mới)")
    loai = c1.selectbox("Loại hình", [TAT_CA, "Thực tập", "Part-time"], key="loai")
    nganh = c2.selectbox("Ngành", [TAT_CA] + df_all["category"].value_counts().index.tolist(), key="nganh")
    noi = c3.selectbox("Tỉnh / thành", [TAT_CA] + df_all["location"].value_counts().index.tolist(), key="noi")
    c4.button("Xóa bộ lọc", on_click=xoa_bo_loc, use_container_width=True,
              disabled=(ngay, loai, nganh, noi) == (TAT_CA,) * 4)

df = loc(df_all, ngay, loai, nganh, noi)
luong = pt.loc_luong_thang(df)
if df.empty:
    st.info("Không có tin nào khớp lựa chọn này. Thử chọn rộng hơn (ví dụ 'Tất cả').")
    st.stop()

st.markdown('<div class="luoi-kpi">' + "".join([
    the_kpi("Tin tuyển dụng", f"{len(df):,}".replace(",", "."),
            "toàn bộ dữ liệu" if ngay == TAT_CA else f"mới ngày {ngay_vn(ngay)}"),
    the_kpi("Còn hạn nộp", f"{int(df['con_han'].sum()):,}".replace(",", "."), f"{df['con_han'].mean():.0%} số tin"),
    the_kpi("Mức lương phổ biến", f"{so(luong['salary_mid'].median())} tr" if len(luong) else "–",
            "một nửa số tin trả thấp hơn"),
    the_kpi("Có ghi lương", f"{df['co_luong'].mean():.0%}", "còn lại ghi 'thỏa thuận'"),
    the_kpi("Doanh nghiệp", f"{df['company'].nunique():,}".replace(",", "."), "đang tuyển"),
]) + "</div>", unsafe_allow_html=True)

tabs = st.tabs(["Tổng quan", "Lương & thương lượng", "Tra cứu tin"]
               + ["Phân tích thống kê"] * HIEN_PHAN_TICH + ["Dữ liệu & hướng dẫn"])
tab1, tab2, tab3, tab5 = tabs[0], tabs[1], tabs[2], tabs[-1]

# ============================================================================================ 1. tổng quan
with tab1:
    st.markdown("#### Gợi ý cho từng nhóm")
    st.markdown('<div class="luoi-the">' + "".join(the_ds(ai, dong) for ai, dong in nhan_dinh(df, luong).items())
                + "</div>", unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        st.markdown("#### Số tin theo ngành")
        st.altair_chart(cot(df["category"].value_counts(), "Số tin"), use_container_width=True)
        st.markdown("#### Theo loại hình")
        st.altair_chart(cot(df["loai_hinh"].value_counts(), "Số tin", XANH_LA), use_container_width=True)
    with b:
        st.markdown("#### 10 tỉnh / thành nhiều tin nhất")
        st.altair_chart(cot(df["location"].value_counts().head(10), "Số tin", XANH_LA), use_container_width=True)
        st.markdown("#### Tin mới theo ngày lấy tin (5 ngày gần nhất)")
        theo_ngay = loc(df_all, TAT_CA, loai, nganh, noi)["crawl_date"].value_counts().sort_index(ascending=False)[:5]
        st.altair_chart(cot(theo_ngay.rename(index=ngay_vn), "Tin mới"), use_container_width=True)

# ============================================================================================ 2. lương
with tab2:
    a, b = st.columns([3, 2])
    with a:
        chon = " · ".join([ngay_vn(ngay) if ngay != TAT_CA else "tất cả các ngày",
                           loai if loai != TAT_CA else "thực tập + part-time",
                           nganh if nganh != TAT_CA else "mọi ngành", noi if noi != TAT_CA else "toàn quốc"])
        if len(luong) >= 5:
            q1, tv, q3 = luong["salary_mid"].quantile([.25, .5, .75])
            st.markdown(f"""<div class="card"><h4>Mức lương theo lựa chọn: {html.escape(chon)}</h4>
<div class="lon">Phần lớn tin trả {so(q1)} – {so(q3)} triệu/tháng</div>
<div class="nho">Mức phổ biến {so(tv)} triệu (một nửa số tin trả thấp hơn) · dựa trên {len(luong)} tin có ghi lương
theo tháng · {1 - df['co_luong'].mean():.0%} tin cùng loại không ghi rõ lương</div>
<div class="goi-y"><b>Gợi ý thương lượng:</b> dưới {so(q1)} triệu là thấp hơn 3/4 số tin cùng loại;
từ {so(q3)} triệu trở lên là mức tốt.</div></div>""", unsafe_allow_html=True)
        else:
            st.info(f"Chỉ có {len(luong)} tin ghi lương với lựa chọn này — chưa đủ để kết luận. Thử chọn rộng hơn.")

        cung = pt.loc_luong_thang(loc(df_all, ngay, TAT_CA, nganh, noi))       # cùng ngày + ngành + nơi
        x1, x2 = st.columns(2)
        for col, ma, ten in [(x1, "internship", "Thực tập"), (x2, "part-time", "Part-time")]:
            s = cung.loc[cung["contract_type"] == ma, "salary_mid"]
            col.markdown(the_kpi(f"{ten}: mức phổ biến", f"{so(s.median())} tr" if len(s) >= 5 else "–",
                                 f"{len(s)} tin có lương"), unsafe_allow_html=True)
        st.caption("So sánh trong cùng ngày, ngành và nơi đã chọn — tránh so lệch vì khác ngành.")

        st.markdown("#### Mức lương phổ biến theo ngành (triệu/tháng)")
        d = (pt.loc_luong_thang(loc(df_all, ngay, loai, TAT_CA, noi)).groupby("category")["salary_mid"]
             .agg(["median", "count"]).query("count >= 5")["median"])
        if d.empty:
            st.caption("Chưa đủ dữ liệu (cần ngành có ít nhất 5 tin ghi lương).")
        else:
            st.altair_chart(cot(d, "Mức phổ biến (triệu)", to_dam=nganh, dinh_dang=".1f"), use_container_width=True)
            st.caption("Chỉ tính ngành có ít nhất 5 tin ghi lương theo tháng. Ngành đang chọn tô màu cam.")

    with b:
        st.markdown('<div class="card"><h4>Ước tính mức lương</h4><div class="nho">Máy học từ các tin có ghi lương '
                    'để ước tính mức lương cho tin chỉ ghi "thỏa thuận".</div></div>', unsafe_allow_html=True)
        with st.form("du_doan"):
            ds_nganh = df_all["category"].value_counts().index.tolist()
            f_nganh = st.selectbox("Ngành", ds_nganh, index=ds_nganh.index(nganh) if nganh in ds_nganh else 0)
            f_noi = st.selectbox("Khu vực", ["TP. Hồ Chí Minh", "Hà Nội", "Tỉnh khác"])
            f_loai = st.selectbox("Loại hình", list(pt.LOAI_HINH), format_func=pt.LOAI_HINH.get)
            f_kn = st.number_input("Số năm kinh nghiệm yêu cầu", 0.0, 5.0, 0.0, 0.5)
            ok = st.form_submit_button("Ước tính", type="primary", use_container_width=True)
        if ok:
            x = pd.DataFrame([{"category": f_nganh, "khu_vuc": f_noi, "contract_type": f_loai, "source": s,
                               "experience_years": f_kn} for s in ("careerviet", "joboko")])
            st.markdown(f'<div class="card"><h4>Kết quả ước tính</h4><div class="lon">Khoảng {so(round(max(model.predict(x).mean(), .5), 1))}'
                        f' triệu/tháng</div><div class="nho">Thường lệch khoảng {so(hq.iloc[0]["MAE (triệu)"])} triệu '
                        'so với lương thật. Chỉ dùng để tham khảo.</div></div>', unsafe_allow_html=True)

# ============================================================================================ 3. tra cứu
with tab3:
    a, b, c, e = st.columns([3, 1, 1, 1.4], vertical_alignment="bottom")
    q = a.text_input("Tìm theo tên việc hoặc công ty", placeholder="vd: marketing, kế toán, gia sư, tester")
    con_han = b.checkbox("Còn hạn nộp", value=True)
    co_luong = c.checkbox("Có ghi lương")
    sap_xep = e.selectbox("Sắp xếp", ["Mới đăng nhất", "Lương cao nhất", "Sắp hết hạn"])
    d = df
    if q:
        tu = lam_sach.bo_dau(q)
        d = d[(d["title"].map(lam_sach.bo_dau) + " " + d["company"].map(lam_sach.bo_dau)).str.contains(tu, regex=False)]
    if con_han:
        d = d[d["con_han"]]
    if co_luong:
        d = d[d["co_luong"] == 1]
    d = {"Mới đăng nhất": lambda x: x.sort_values("date_posted", ascending=False),
         "Lương cao nhất": lambda x: x.sort_values("salary_mid", ascending=False),
         "Sắp hết hạn": lambda x: x.sort_values("deadline")}[sap_xep](d)
    bang = d.assign(luong=d["salary_text"].where(d["co_luong"] == 1,
                                                 "Thỏa thuận (ước tính " + d["uoc_tinh"].map(so) + " tr)"))
    bang = bang[["title", "company", "category", "loai_hinh", "location", "luong", "deadline", "url"]]

    x1, x2 = st.columns([3, 1])
    x1.markdown(f"**{len(d):,} tin**".replace(",", ".") + (" · hiển thị 30 tin đầu" if len(d) > 30 else ""))
    x2.download_button("Tải danh sách (CSV)", bang.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"tin_tuyen_dung_{datetime.now():%Y-%m-%d}.csv", mime="text/csv",
                       use_container_width=True)
    if d.empty:
        st.info("Không có tin nào. Thử từ khóa khác hoặc bỏ bớt điều kiện.")
    the_tin = []
    for r in d.head(30).itertuples():
        han = pd.to_datetime(r.deadline, errors="coerce")
        the_tin.append(f"""<div class="job">
<div class="job-title">{html.escape(str(r.title))}</div>
<div class="job-co">{html.escape(str(r.company))}</div>
<div class="job-chip"><span class="chip">{html.escape(str(r.location)) if pd.notna(r.location) else "Không rõ nơi làm"}</span>
<span class="chip">{r.loai_hinh}</span>{luong_the(r)}
<span class="chip">Hạn {han.strftime("%d/%m/%Y") if pd.notna(han) else "—"}</span></div>
<a href="{html.escape(str(r.url), quote=True)}" target="_blank" rel="noopener">Xem tin gốc ↗</a></div>""")
    st.markdown('<div class="luoi-tin">' + "".join(the_tin) + "</div>", unsafe_allow_html=True)
    if len(d) > 30:
        with st.expander(f"Xem tất cả {len(d)} tin dạng bảng"):
            st.dataframe(bang, hide_index=True, use_container_width=True,
                         column_config={"title": "Tên việc", "company": "Công ty", "category": "Ngành",
                                        "loai_hinh": "Loại hình", "location": "Tỉnh", "luong": "Lương",
                                        "deadline": "Hạn nộp",
                                        "url": st.column_config.LinkColumn("Link", display_text="Mở tin")})

# ============================================================================================ 4. phân tích
def tab_phan_tich() -> None:
    st.caption("Tính trên toàn bộ dữ liệu (không theo bộ lọc phía trên) — theo đề cương Chương 2–5.")
    with st.expander("Kiểm định giả thuyết (α = 0,05)", expanded=True):
        st.dataframe(bang_kiem_dinh.rename(columns={
            "kiem_dinh": "Kiểm định", "cau_hoi": "Câu hỏi", "H0": "Giả thuyết H0", "thong_ke": "Thống kê",
            "p_value": "p-value", "ket_luan": "Kết luận"}), hide_index=True, use_container_width=True)
        st.caption("Lương lệch phải, không phân phối chuẩn → ưu tiên Mann-Whitney và Kruskal-Wallis. Dòng 'BỎ ngành "
                   "Giáo dục' kiểm tra lại kết luận khi loại ảnh hưởng của ngành.")
    with st.expander("Thống kê mô tả lương tháng"):
        st.dataframe(pt.mo_ta_luong(df_all), hide_index=True, use_container_width=True)
        st.dataframe(pt.mo_ta_luong(df_all, "category"), hide_index=True, use_container_width=True)
    with st.expander("Mô hình học máy"):
        st.markdown(f"**Hồi quy tuyến tính — dự đoán lương** (huấn luyện {hq.attrs['n_train']} tin, "
                    f"kiểm tra {hq.attrs['n_test']} tin)")
        st.dataframe(hq, hide_index=True, use_container_width=True)
        st.markdown("**Phân loại tin công khai lương / thỏa thuận**")
        st.dataframe(bang_phan_loai, hide_index=True, use_container_width=True)
        st.caption("Mô hình phân loại chỉ nhỉnh hơn mốc 'đoán bừa' → ngành, nơi làm, loại hình không đủ để biết "
                   "doanh nghiệp có công khai lương hay không; cần thêm thông tin như quy mô công ty.")
    thu_muc = sorted(p for p in pt.OUT_ROOT.glob("*") if p.is_dir()) if pt.OUT_ROOT.exists() else []
    if thu_muc:
        with st.expander(f"Bộ biểu đồ đầy đủ (từ 4_phan_tich.py, ngày {ngay_vn(thu_muc[-1].name)})"):
            hinh = st.columns(2)
            for i, p in enumerate(sorted(thu_muc[-1].glob("*.png"))):
                hinh[i % 2].image(str(p), caption=p.stem, use_container_width=True)


if HIEN_PHAN_TICH:
    with tabs[3]:
        tab_phan_tich()

# ============================================================================================ 5. dữ liệu & hướng dẫn
with tab5:
    a, b = st.columns(2)
    with a:
        st.markdown("""#### Hướng dẫn sử dụng
1. **Chọn phạm vi** ở hàng trên cùng: *Ngày lấy tin* (từng ngày trong 5 ngày gần nhất, hoặc tất cả),
   *Loại hình*, *Ngành*, *Tỉnh / thành*. Mọi con số và biểu đồ đổi theo lựa chọn.
2. **Tổng quan:** gợi ý cho sinh viên, nhà trường, doanh nghiệp; biểu đồ ngành, tỉnh, loại hình.
3. **Lương & thương lượng:** khoảng lương phổ biến, so sánh thực tập với part-time, ước tính mức lương.
4. **Tra cứu tin:** tìm theo từ khóa, lọc tin còn hạn / có lương, bấm *Xem tin gốc* để mở tin trên trang tuyển
   dụng, bấm *Tải danh sách (CSV)* để lấy dữ liệu ra Excel.

#### Cập nhật dữ liệu mỗi ngày
Bấm **Lấy dữ liệu hôm nay** ở góc trên bên phải (tương đương lệnh `python chay.py`). Quá trình chạy nền 15–45 phút,
ngay dưới nút hiện tiến độ. Xong thì bấm **Hiển thị dữ liệu mới**.

#### Cách mở web
Trong VS Code mở `web/app.py` bấm ▶ Run, hoặc gõ `python web/app.py`. Trình duyệt tự mở http://localhost:8501.
Tắt web: `Ctrl+C` trong terminal.
""")
    with b:
        st.markdown("""#### Trang web này giúp gì?
Thông tin thực tập / part-time nằm rải rác, nhiều tin không ghi lương. Trang này giúp **sinh viên** chọn nơi ứng
tuyển và thương lượng lương, **nhà trường** biết ngành nào cần thực tập sinh để kết nối doanh nghiệp,
**doanh nghiệp** so mức lương với thị trường.

#### Dữ liệu lấy từ đâu?
Từ careerviet.vn và vn.joboko.com: chỉ lấy tin công khai, đúng quy định của từng trang (robots.txt), nghỉ 1,5 giây
giữa các lượt; làm sạch 7 bước; lương ngoại tệ đổi theo tỷ giá Vietcombank lúc chạy. Mỗi tin giữ link gốc.

**Mức lương phổ biến** là mức ở giữa: một nửa số tin trả thấp hơn, một nửa trả cao hơn. Vài tin lương rất cao
không làm lệch con số này.

#### Cần lưu ý
Chỉ có 2 trang tuyển dụng; nhiều tin không ghi kinh nghiệm; lương ước tính chỉ để tham khảo.
""")
        raw = pd.concat([pd.read_csv(f, usecols=["source", "crawled_at"], encoding="utf-8-sig")
                         for f in sorted(lam_sach.RAW_DIR.glob("*_????-??-??.csv"))], ignore_index=True)
        raw["Ngày lấy tin"] = raw["crawled_at"].str[:10].map(ngay_vn)
        st.markdown("#### Số tin lấy được theo ngày và trang (chưa làm sạch)")
        st.dataframe(pd.crosstab(raw["Ngày lấy tin"], raw["source"].map({"careerviet": "CareerViet",
                                                                          "joboko": "JobOKO"}),
                                 margins=True, margins_name="Tổng"), use_container_width=True)
    st.caption(f"Nhóm 3 · Phân tích dữ liệu cho Môi trường doanh nghiệp (71DAEE10012) · file {file.name}")
