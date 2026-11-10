"""BƯỚC 4 — Phân tích dữ liệu theo đề cương môn (Chương 2 → Chương 5).

    python 4_phan_tich.py

Đầu vào : data/clean/jobs_clean_<ngày mới nhất>.csv (do 2_lam_sach.py tạo)
Đầu ra  : data/phan_tich/<ngày>/
            - 01_...png → 09_...png         biểu đồ (Chương 3, 5)
            - ket_qua_phan_tich.xlsx         bảng kết quả (Chương 2, 4, 5)

Nội dung (bám theo đề cương 71DAEE10012):
  Chương 2  Thao tác dữ liệu: DataFrame / Series / NumPy array, lọc dữ liệu, xử lý dữ liệu thiếu,
            mã hóa (one-hot), chia dữ liệu train/test
  Chương 3  Trực quan hóa: bar, grouped bar, stacked bar, pie, histogram + box, scatter, line, area
  Chương 4  Thống kê mô tả; kiểm định giả thuyết: t-test, Mann-Whitney, ANOVA, Kruskal-Wallis, chi-square
  Chương 5  Học có giám sát: Linear Regression, Logistic Regression, Decision Tree, k-NN
            Học không giám sát: K-Means, PCA
"""
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")                       # vẽ ra file, không mở cửa sổ
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
                             mean_squared_error, precision_score, r2_score, recall_score, silhouette_score)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).parent
CLEAN_DIR = ROOT / "data" / "clean"
OUT_ROOT = ROOT / "data" / "phan_tich"
ALPHA = 0.05                                 # mức ý nghĩa cho kiểm định
SEED = 42                                    # cố định ngẫu nhiên -> kết quả tái lập được
LOAI_HINH = {"internship": "Thực tập", "part-time": "Part-time", "internship/part-time": "Cả hai"}
THU_TU = ["Thực tập", "Part-time", "Cả hai"]   # cố định thứ tự + màu loại hình trên mọi biểu đồ

# Biến dùng cho mô hình ML
CAT_FEATURES = ["category", "khu_vuc", "contract_type", "source"]
NUM_FEATURES = ["experience_years"]


# =====================================================================================================
# CHƯƠNG 2 — THAO TÁC DỮ LIỆU
# =====================================================================================================
def tai_du_lieu(path: Path | None = None) -> pd.DataFrame:
    """2.1 Data import: đọc file sạch mới nhất thành DataFrame, thêm vài cột dẫn xuất."""
    path = path or max(CLEAN_DIR.glob("jobs_clean_*.csv"))
    df = pd.read_csv(path)
    df.attrs["file"] = path.name
    # Gom tỉnh thành 4 khu vực để kiểm định chi-square có đủ số quan sát mỗi ô
    df["khu_vuc"] = np.select(
        [df["location"].eq("TP. Hồ Chí Minh"), df["location"].eq("Hà Nội"), df["location"].isna()],
        ["TP. Hồ Chí Minh", "Hà Nội", "Không rõ"], default="Tỉnh khác")
    df["loai_hinh"] = df["contract_type"].map(LOAI_HINH)
    df["co_luong"] = (df["salary_label"] == "Có lương").astype(int)
    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
    return df


def loc_luong_thang(df: pd.DataFrame) -> pd.DataFrame:
    """2.3a Lọc dữ liệu (filtering): chỉ tin có lương THEO THÁNG và không bất thường."""
    return df[(df["salary_unit"] == "tháng") & df["salary_mid"].notna() & ~df["salary_outlier"]].copy()


def du_lieu_thieu(df: pd.DataFrame) -> pd.DataFrame:
    """2.3b Xử lý dữ liệu thiếu: tỷ lệ thiếu mỗi cột + cách nhóm xử lý."""
    cach_xu_ly = {
        "salary_min": "Không điền — tin 'Thỏa thuận' đã có nhãn salary_label",
        "salary_max": "Không điền — tin 'Thỏa thuận' đã có nhãn salary_label",
        "salary_mid": "Không điền — chỉ phân tích lương trên tin có lương",
        "salary_unit": "Không điền — thiếu khi không có lương",
        "experience_years": "ML: điền 0 (tin không ghi thường là không yêu cầu kinh nghiệm)",
        "location": "Gán khu vực 'Không rõ'",
        "date_posted": "Bỏ qua khi vẽ biểu đồ theo thời gian",
        "deadline": "Bỏ qua (con_han = False)",
        "salary_currency": "Không điền — tin 'Thỏa thuận' không có loại tiền",
        "fx_rate": "Không điền — chỉ tin lương ngoại tệ mới có tỷ giá",
        "fx_date": "Không điền — chỉ tin lương ngoại tệ mới có ngày tỷ giá",
    }
    thieu = df.isna().sum()
    out = pd.DataFrame({"so_dong_thieu": thieu, "ty_le_thieu_%": (thieu / len(df) * 100).round(1)})
    out = out[out["so_dong_thieu"] > 0].sort_values("so_dong_thieu", ascending=False)
    out["cach_xu_ly"] = [cach_xu_ly.get(c, "") for c in out.index]
    return out.rename_axis("cot").reset_index()


def ma_hoa_one_hot(df: pd.DataFrame) -> pd.DataFrame:
    """2.3c Mã hóa dữ liệu (encoding): biến phân loại -> các cột 0/1 (one-hot)."""
    return pd.get_dummies(df[["category", "khu_vuc", "contract_type"]], dtype=int)


def gioi_thieu_numpy(df: pd.DataFrame) -> dict:
    """2.2 Series / Array: lấy cột lương thành NumPy array và tính bằng NumPy."""
    luong: np.ndarray = loc_luong_thang(df)["salary_mid"].to_numpy()
    return {"so_phan_tu": int(luong.size), "trung_binh": float(np.mean(luong)),
            "trung_vi": float(np.median(luong)), "phan_vi_25": float(np.percentile(luong, 25)),
            "phan_vi_75": float(np.percentile(luong, 75))}


# =====================================================================================================
# CHƯƠNG 3 — TRỰC QUAN HÓA
# =====================================================================================================
def ve_bieu_do(df: pd.DataFrame, out: Path) -> list[Path]:
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    teal, cam, xam = "#1C6E7D", "#E8833A", "#9AA5B1"
    files = []

    def luu(name):
        p = out / name
        plt.tight_layout()
        plt.savefig(p, dpi=150)
        plt.close()
        files.append(p)

    luong = loc_luong_thang(df)

    # 3.2 Bar chart (đơn): số tin theo nhóm ngành
    plt.figure(figsize=(9, 6))
    s = df["category"].value_counts().sort_values()
    ax = s.plot.barh(color=teal)
    ax.bar_label(ax.containers[0], padding=3)
    ax.set(title="Số tin thực tập / part-time theo nhóm ngành", xlabel="Số tin", ylabel="")
    luu("01_bar_tin_theo_nganh.png")

    # 3.2 Grouped bar: khu vực × loại hình
    plt.figure(figsize=(9, 5))
    ct = (pd.crosstab(df["khu_vuc"], df["loai_hinh"]).reindex(columns=THU_TU, fill_value=0)
          .loc[["TP. Hồ Chí Minh", "Hà Nội", "Tỉnh khác", "Không rõ"]])
    ax = ct.plot.bar(ax=plt.gca(), color=[teal, cam, xam], rot=0)
    ax.set(title="Số tin theo khu vực và loại hình", xlabel="", ylabel="Số tin")
    ax.legend(title="Loại hình")
    luu("02_grouped_bar_khu_vuc_loai_hinh.png")

    # 3.2 Stacked bar (100%): tỷ lệ có lương / thỏa thuận theo ngành
    plt.figure(figsize=(9, 6))
    tl = pd.crosstab(df["category"], df["salary_label"], normalize="index").mul(100)
    tl = tl.sort_values("Có lương")
    ax = tl[["Có lương", "Thỏa thuận"]].plot.barh(stacked=True, ax=plt.gca(), color=[teal, xam])
    ax.set(title="Tỷ lệ tin ghi lương / thỏa thuận theo ngành (%)", xlabel="%", ylabel="")
    ax.legend(loc="lower right")
    luu("03_stacked_bar_luong_theo_nganh.png")

    # 3.3 Pie chart: tỷ lệ loại hình
    plt.figure(figsize=(6, 6))
    df["loai_hinh"].value_counts().reindex(THU_TU).plot.pie(autopct="%1.1f%%", colors=[teal, cam, xam], startangle=90,
                                            ylabel="", title="Tỷ lệ tin theo loại hình")
    luu("04_pie_loai_hinh.png")

    # Histogram + Box: phân phối lương tháng
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(luong, x="salary_mid", bins=30, color=teal, ax=axes[0])
    axes[0].set(title="Phân phối lương tháng (triệu VND)", xlabel="Lương trung bình mỗi tin", ylabel="Số tin")
    sns.boxplot(luong, x="loai_hinh", y="salary_mid", hue="loai_hinh", order=THU_TU, hue_order=THU_TU,
                palette=[teal, cam, xam], ax=axes[1])
    axes[1].set(title="Lương tháng theo loại hình", xlabel="", ylabel="Triệu VND / tháng")
    luu("05_hist_box_luong.png")

    # 3.1 Scatter: lương tối thiểu vs tối đa
    plt.figure(figsize=(7, 6))
    sc = luong.dropna(subset=["salary_min", "salary_max"])
    sns.scatterplot(sc, x="salary_min", y="salary_max", hue="loai_hinh", hue_order=THU_TU,
                    palette=[teal, cam, xam], alpha=0.7)
    plt.legend(title="Loại hình")
    plt.title("Lương tối thiểu và tối đa của mỗi tin (triệu VND)")
    luu("06_scatter_luong_min_max.png")

    # 3.1 Line chart: số tin đăng theo tuần
    plt.figure(figsize=(10, 5))
    tuan = df.dropna(subset=["date_posted"]).set_index("date_posted").resample("W")["job_id"].count()
    tuan.plot(marker="o", color=teal)
    plt.title("Số tin được đăng theo tuần")
    plt.xlabel("Tuần đăng tin")
    plt.ylabel("Số tin")
    luu("07_line_tin_theo_tuan.png")

    # 3.3 Area chart: số tin cộng dồn theo loại hình
    plt.figure(figsize=(10, 5))
    cd = (df.dropna(subset=["date_posted"]).groupby([pd.Grouper(key="date_posted", freq="W"), "loai_hinh"])
          .size().unstack(fill_value=0).reindex(columns=THU_TU, fill_value=0).cumsum())
    cd.plot.area(ax=plt.gca(), color=[teal, cam, xam], alpha=0.8)
    plt.legend(title="Loại hình")
    plt.title("Số tin cộng dồn theo loại hình")
    plt.xlabel("Tuần đăng tin")
    plt.ylabel("Số tin (cộng dồn)")
    luu("08_area_tin_cong_don.png")
    return files


# =====================================================================================================
# CHƯƠNG 4 — THỐNG KÊ
# =====================================================================================================
def mo_ta_luong(df: pd.DataFrame, by: str = "loai_hinh") -> pd.DataFrame:
    """4.1 Thống kê mô tả lương tháng theo nhóm."""
    luong = loc_luong_thang(df)
    g = luong.groupby(by)["salary_mid"]
    out = g.agg(so_tin="count", trung_binh="mean", trung_vi="median", do_lech_chuan="std",
                nho_nhat="min", lon_nhat="max")
    out.insert(4, "Q1", g.quantile(0.25))
    out.insert(5, "Q3", g.quantile(0.75))
    out["do_lech_skew"] = g.skew()
    return out.round(2).sort_values("so_tin", ascending=False).reset_index()


def _ket_luan(p: float) -> str:
    return "Bác bỏ H0 → có khác biệt / có liên hệ" if p < ALPHA else "Chưa đủ bằng chứng bác bỏ H0"


def kiem_dinh(df: pd.DataFrame) -> pd.DataFrame:
    """4.2 Kiểm định giả thuyết (α = 0,05)."""
    luong = loc_luong_thang(df)
    rows = []

    # (1) Lương thực tập vs part-time
    a = luong.loc[luong["contract_type"] == "internship", "salary_mid"]
    b = luong.loc[luong["contract_type"] == "part-time", "salary_mid"]
    p_norm = stats.shapiro(a.sample(min(len(a), 500), random_state=SEED)).pvalue
    t = stats.ttest_ind(a, b, equal_var=False)
    u = stats.mannwhitneyu(a, b)
    cau_hoi = f"Lương thực tập (n={len(a)}, trung vị {a.median():.2f}) vs part-time (n={len(b)}, trung vị {b.median():.2f})"
    rows.append(["Welch t-test", cau_hoi, "Lương TB 2 nhóm bằng nhau", t.statistic, t.pvalue, _ket_luan(t.pvalue)])
    rows.append(["Mann-Whitney U", cau_hoi, "Phân phối lương 2 nhóm như nhau", u.statistic, u.pvalue,
                 _ket_luan(u.pvalue) + (" (dùng kết quả này vì lương không phân phối chuẩn, Shapiro p="
                                        f"{p_norm:.1e})" if p_norm < ALPHA else "")])

    # (1b) Cùng câu hỏi nhưng BỎ ngành Giáo dục: part-time có lương phần lớn là gia sư / giáo viên online
    #      (lương cao) -> so sánh trong các ngành còn lại để tránh kết luận bị lệch vì ngành
    khac = luong[luong["category"] != "Giáo dục - Ngôn ngữ"]
    a2 = khac.loc[khac["contract_type"] == "internship", "salary_mid"]
    b2 = khac.loc[khac["contract_type"] == "part-time", "salary_mid"]
    u2 = stats.mannwhitneyu(a2, b2)
    rows.append(["Mann-Whitney U", f"Như trên nhưng BỎ ngành Giáo dục: thực tập (n={len(a2)}, trung vị "
                 f"{a2.median():.2f}) vs part-time (n={len(b2)}, trung vị {b2.median():.2f})",
                 "Phân phối lương 2 nhóm như nhau", u2.statistic, u2.pvalue, _ket_luan(u2.pvalue)])

    # (2) Lương giữa các ngành (các ngành có ≥ 20 tin có lương)
    du = luong["category"].value_counts()
    nganh = du[du >= 20].index.tolist()
    nhom = [luong.loc[luong["category"] == n, "salary_mid"] for n in nganh]
    f = stats.f_oneway(*nhom)
    k = stats.kruskal(*nhom)
    cau_hoi = f"Lương giữa {len(nganh)} ngành có ≥ 20 tin có lương"
    rows.append(["ANOVA một yếu tố", cau_hoi, "Lương TB các ngành bằng nhau", f.statistic, f.pvalue, _ket_luan(f.pvalue)])
    rows.append(["Kruskal-Wallis", cau_hoi, "Phân phối lương các ngành như nhau", k.statistic, k.pvalue,
                 _ket_luan(k.pvalue)])

    # (3) Khu vực × loại hình (thực tập / part-time)
    ct = pd.crosstab(df["khu_vuc"], df["contract_type"])
    c = stats.chi2_contingency(ct)
    rows.append(["Chi-square độc lập", "Khu vực × loại hình", "Khu vực và loại hình độc lập",
                 c.statistic, c.pvalue, _ket_luan(c.pvalue)])

    # (4) Ngành × có ghi lương
    ct = pd.crosstab(df["category"], df["salary_label"])
    c = stats.chi2_contingency(ct)
    rows.append(["Chi-square độc lập", "Ngành × có ghi lương / thỏa thuận", "Việc ghi lương không phụ thuộc ngành",
                 c.statistic, c.pvalue, _ket_luan(c.pvalue)])

    out = pd.DataFrame(rows, columns=["kiem_dinh", "cau_hoi", "H0", "thong_ke", "p_value", "ket_luan"])
    out["thong_ke"] = out["thong_ke"].round(3)
    out["p_value"] = out["p_value"].map(lambda p: f"{p:.2e}" if p < 0.001 else f"{p:.4f}")
    return out


# =====================================================================================================
# CHƯƠNG 5 — MACHINE LEARNING
# =====================================================================================================
def _pipeline(model) -> Pipeline:
    """Tiền xử lý chung: one-hot biến phân loại, điền thiếu + chuẩn hóa biến số."""
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
        ("num", Pipeline([("dien_thieu", SimpleImputer(strategy="constant", fill_value=0)),
                          ("chuan_hoa", StandardScaler())]), NUM_FEATURES),
    ])
    return Pipeline([("tien_xu_ly", pre), ("mo_hinh", model)])


def hoi_quy_luong(df: pd.DataFrame):
    """5.2a Linear Regression: dự đoán lương tháng từ ngành, khu vực, loại hình, nguồn, kinh nghiệm."""
    luong = loc_luong_thang(df)
    X, y = luong[CAT_FEATURES + NUM_FEATURES], luong["salary_mid"]
    # 2.3d Chia dữ liệu: 80% huấn luyện, 20% kiểm tra
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
    model = _pipeline(LinearRegression()).fit(X_tr, y_tr)
    pred = model.predict(X_te)
    base = np.full(len(y_te), y_tr.median())                   # mô hình "đoán bừa" = trung vị
    ket_qua = pd.DataFrame([
        ["Linear Regression", mean_absolute_error(y_te, pred), mean_squared_error(y_te, pred) ** 0.5,
         r2_score(y_te, pred)],
        ["Mốc so sánh (luôn đoán trung vị)", mean_absolute_error(y_te, base),
         mean_squared_error(y_te, base) ** 0.5, r2_score(y_te, base)],
    ], columns=["mo_hinh", "MAE (triệu)", "RMSE (triệu)", "R2"]).round(3)
    ket_qua.attrs["n_train"], ket_qua.attrs["n_test"] = len(X_tr), len(X_te)
    return ket_qua, model


def phan_loai_co_luong(df: pd.DataFrame):
    """5.2b–d Phân loại tin 'Có lương' vs 'Thỏa thuận': Logistic Regression, Decision Tree, k-NN."""
    X, y = df[CAT_FEATURES + NUM_FEATURES], df["co_luong"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Decision Tree (độ sâu 5)": DecisionTreeClassifier(max_depth=5, random_state=SEED),
        "k-NN (k = 7)": KNeighborsClassifier(n_neighbors=7),
    }
    rows, ma_tran = [], {}
    for name, m in models.items():
        pred = _pipeline(m).fit(X_tr, y_tr).predict(X_te)
        ma_tran[name] = confusion_matrix(y_te, pred)
        rows.append([name, accuracy_score(y_te, pred), precision_score(y_te, pred), recall_score(y_te, pred),
                     f1_score(y_te, pred)])
    da_so = int(y_tr.mode()[0])
    pred = np.full(len(y_te), da_so)
    rows.append(["Mốc so sánh (luôn đoán lớp đa số)", accuracy_score(y_te, pred),
                 precision_score(y_te, pred, zero_division=0), recall_score(y_te, pred), f1_score(y_te, pred)])
    ket_qua = pd.DataFrame(rows, columns=["mo_hinh", "Accuracy", "Precision", "Recall", "F1"]).round(3)
    return ket_qua, ma_tran


def phan_cum(df: pd.DataFrame):
    """5.3 K-Means (chọn k bằng silhouette) + PCA 2 chiều để vẽ."""
    luong = loc_luong_thang(df).reset_index(drop=True)
    X = pd.concat([luong[["salary_mid"]], pd.get_dummies(luong[["contract_type", "khu_vuc"]], dtype=int)], axis=1)
    Xs = StandardScaler().fit_transform(X)
    diem = {k: silhouette_score(Xs, KMeans(k, n_init=10, random_state=SEED).fit_predict(Xs)) for k in range(2, 7)}
    k_tot = max(diem, key=diem.get)
    luong["cum"] = KMeans(k_tot, n_init=10, random_state=SEED).fit_predict(Xs)
    pca = PCA(n_components=2, random_state=SEED)
    toa_do = pca.fit_transform(Xs)
    luong["PC1"], luong["PC2"] = toa_do[:, 0], toa_do[:, 1]
    ho_so = luong.groupby("cum").agg(
        so_tin=("job_id", "count"),
        luong_trung_vi=("salary_mid", "median"),
        ty_le_part_time=("contract_type", lambda s: round((s != "internship").mean() * 100, 1)),
        khu_vuc_chinh=("khu_vuc", lambda s: s.mode()[0]),
        nganh_chinh=("category", lambda s: s.mode()[0]),
    ).reset_index()
    thong_tin = {"k_tot_nhat": k_tot, "silhouette": round(diem[k_tot], 3),
                 "pca_giai_thich_%": round(pca.explained_variance_ratio_.sum() * 100, 1)}
    return ho_so, luong[["job_id", "title", "salary_mid", "loai_hinh", "khu_vuc", "cum", "PC1", "PC2"]], thong_tin


def ve_bieu_do_ml(ma_tran: dict, diem_cum: pd.DataFrame, out: Path) -> list[Path]:
    files = []
    ten, cm = max(ma_tran.items(), key=lambda kv: np.trace(kv[1]))   # mô hình đoán đúng nhiều nhất
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Thỏa thuận", "Có lương"], yticklabels=["Thỏa thuận", "Có lương"])
    plt.title(f"Ma trận nhầm lẫn — {ten}")
    plt.xlabel("Dự đoán")
    plt.ylabel("Thực tế")
    plt.tight_layout()
    files.append(out / "09_confusion_matrix.png")
    plt.savefig(files[-1], dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.scatterplot(diem_cum, x="PC1", y="PC2", hue="cum", palette="Set2", alpha=0.8)
    plt.title("Phân cụm K-Means hiển thị trên 2 thành phần chính (PCA)")
    plt.tight_layout()
    files.append(out / "10_kmeans_pca.png")
    plt.savefig(files[-1], dpi=150)
    plt.close()
    return files


# =====================================================================================================
def main() -> None:
    df = tai_du_lieu()
    day = f"{datetime.now():%Y-%m-%d}"
    out = OUT_ROOT / day
    out.mkdir(parents=True, exist_ok=True)
    print("=" * 70 + f"\nBƯỚC 4: PHÂN TÍCH DỮ LIỆU — file {df.attrs['file']} ({len(df):,} tin)\n" + "=" * 70)

    print("\n[Chương 2] Dữ liệu thiếu:")
    thieu = du_lieu_thieu(df)
    print(thieu.to_string(index=False))
    print("NumPy — lương tháng:", {k: round(v, 2) for k, v in gioi_thieu_numpy(df).items()})
    print(f"One-hot: {ma_hoa_one_hot(df).shape[1]} cột 0/1 từ ngành, khu vực, loại hình")

    print("\n[Chương 3] Vẽ biểu đồ...")
    hinh = ve_bieu_do(df, out)

    print("\n[Chương 4] Thống kê mô tả lương tháng (triệu VND) theo loại hình:")
    mo_ta = mo_ta_luong(df)
    print(mo_ta.to_string(index=False))
    mo_ta_nganh = mo_ta_luong(df, "category")
    kd = kiem_dinh(df)
    print("\nKiểm định giả thuyết (α = 0,05):")
    for r in kd.itertuples():
        print(f"  - {r.kiem_dinh}: {r.cau_hoi} → p = {r.p_value} → {r.ket_luan}")

    print("\n[Chương 5] Machine learning:")
    hq, _ = hoi_quy_luong(df)
    print(f"  Hồi quy lương (train {hq.attrs['n_train']}, test {hq.attrs['n_test']}):")
    print(hq.to_string(index=False))
    pl, ma_tran = phan_loai_co_luong(df)
    print("  Phân loại 'Có lương' / 'Thỏa thuận':")
    print(pl.to_string(index=False))
    ho_so, diem_cum, tt = phan_cum(df)
    print(f"  K-Means: k = {tt['k_tot_nhat']} (silhouette {tt['silhouette']}); "
          f"PCA 2 chiều giữ {tt['pca_giai_thich_%']}% phương sai")
    print(ho_so.to_string(index=False))
    hinh += ve_bieu_do_ml(ma_tran, diem_cum, out)

    xlsx = out / "ket_qua_phan_tich.xlsx"
    try:
        with pd.ExcelWriter(xlsx) as xw:
            thieu.to_excel(xw, sheet_name="C2_du_lieu_thieu", index=False)
            mo_ta.to_excel(xw, sheet_name="C4_mo_ta_luong_loai_hinh", index=False)
            mo_ta_nganh.to_excel(xw, sheet_name="C4_mo_ta_luong_nganh", index=False)
            kd.to_excel(xw, sheet_name="C4_kiem_dinh", index=False)
            hq.to_excel(xw, sheet_name="C5_hoi_quy", index=False)
            pl.to_excel(xw, sheet_name="C5_phan_loai", index=False)
            ho_so.to_excel(xw, sheet_name="C5_phan_cum", index=False)
    except PermissionError:
        sys.exit(f"LỖI: {xlsx.name} đang mở trong Excel -> đóng file rồi chạy lại.")
    print(f"\nĐã lưu {len(hinh)} biểu đồ + {xlsx.name} vào {out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
