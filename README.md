# PTDL Nhóm 3 — Tin tuyển dụng thực tập & part-time tại Việt Nam

## Cài 1 lần
```
pip install -r requirements.txt
```

## Chạy
```
python chay.py
```
Tự động: **crawl** tin mới từ CareerViet + JobOKO → **làm sạch 7 bước** → **phân tích** (Chương 2–5 của môn).
Chạy lại mỗi ngày để tăng mẫu (chỉ tải tin mới, không trùng). Crawl mất khoảng 15–45 phút (tùy số tin mới) vì cố ý nghỉ 1,5 giây
giữa các lượt truy cập; `Ctrl+C` giữa chừng vẫn giữ dữ liệu đã tải.

Thư mục `data/` không đưa lên GitHub. Máy mới tải code về chạy lệnh trên một lần để tạo dữ liệu.

## Trang web
**Mở web:** mở `web/app.py` trong VS Code rồi **bấm ▶ Run**, hoặc gõ:
```
python web/app.py
```
Trình duyệt tự mở http://localhost:8501. Tắt web: `Ctrl+C` trong terminal của VS Code.

**Sử dụng:**
1. **Hàng chọn trên cùng:** *Ngày lấy tin* (từng ngày trong 5 ngày gần nhất, hoặc tất cả), *Loại hình*,
   *Ngành*, *Tỉnh / thành*. Mọi con số, biểu đồ đổi theo lựa chọn.
2. **Tổng quan:** nhận định & khuyến nghị cho sinh viên / nhà trường / doanh nghiệp, biểu đồ ngành, tỉnh, loại hình,
   số tin mới theo ngày.
3. **Lương & thương lượng:** khoảng lương phổ biến, so sánh thực tập với part-time cùng ngành, ước tính lương.
4. **Tra cứu tin:** tìm theo từ khóa, lọc tin còn hạn / có lương, mở tin gốc, **tải danh sách ra CSV**.
5. **Cập nhật dữ liệu không cần terminal:** bấm **Lấy dữ liệu hôm nay** ở góc trên bên phải (tương đương
   `python chay.py`). Chạy nền 15–45 phút, ngay dưới nút hiện tiến độ; xong bấm **Hiển thị dữ liệu mới**.
   Nhật ký lưu ở `data/cap_nhat.log`.

Tab **Phân tích thống kê** đang ẩn; đặt `HIEN_PHAN_TICH = True` trong `web/app.py` để hiện lại.
Giao diện web (màu, khung) nằm riêng trong `web/style.css`.

Chạy riêng từng bước: `python 1_crawl.py` · `python 2_lam_sach.py` · `python 3_kiem_chung.py` (kiểm chứng 15 tin)
· `python 4_phan_tich.py`.

## Các file
| File | Việc |
|---|---|
| `1_crawl.py` | Crawl CareerViet (careerviet.vn) + JobOKO (vn.joboko.com). Kiểm tra robots.txt, nghỉ 1,5s giữa các lượt |
| `2_lam_sach.py` | 7 bước làm sạch (bên dưới) |
| `3_kiem_chung.py` | Kiểm chứng 15 tin ngẫu nhiên với link gốc |
| `4_phan_tich.py` | Phân tích theo đề cương: Chương 2 (dữ liệu thiếu, mã hóa, chia train/test), Chương 3 (8 loại biểu đồ), Chương 4 (thống kê mô tả, kiểm định), Chương 5 (Regression, Logistic, Decision Tree, k-NN, K-Means, PCA) |
| `web/app.py` | Trang web (Streamlit): bộ lọc theo ngày/loại hình/ngành/tỉnh, nhận định, lương, tra cứu, nút cập nhật dữ liệu |
| `web/style.css` | Giao diện web (màu, khung) |
| `ty_gia.py` | Tỷ giá Vietcombank theo ngày, dùng chung cho bước 1 và 2 |
| `chay.py` | Chạy 1 → 2 → 4 |
| `data/ty_gia.csv` | Tỷ giá chuyển khoản từng ngày thu thập (ngay, ma, ty_gia, lay_luc) |
| `data/snapshot/` | Ảnh chụp trang danh sách mỗi ngày + file `thay_doi_*` (tin mới / đã sửa / không còn) |
| `data/raw/<nguồn>_<ngày>.csv` | Dữ liệu thô, tin **mới** của ngày đó; mỗi dòng có `url` tin gốc |
| `data/clean/jobs_clean_<ngày>.csv` | Dữ liệu sạch (gộp mọi ngày) để phân tích; lương tính bằng **triệu VND** |
| `data/clean/jobs_clean_<ngày>.xlsx` | Bản Excel để xem + sheet báo cáo 7 bước |
| `data/phan_tich/<ngày>/` | 10 biểu đồ PNG + `ket_qua_phan_tich.xlsx` (bảng kết quả Chương 2, 4, 5) |

Tổng hợp chi tiết toàn bộ dự án: [TONG_HOP_DU_AN.md](TONG_HOP_DU_AN.md)

## 7 bước làm sạch (`2_lam_sach.py`)
1. Gộp dữ liệu 2 nguồn
2. Khử trùng lặp theo (tên việc + công ty) đã bỏ dấu
3. Chuẩn hóa lương → `salary_min`, `salary_max` (triệu VND); rỗng/0 → `salary_label = "Thỏa thuận"`, không xóa;
   lương tháng ngoài 0,5–100 triệu → gắn cờ `salary_outlier`. Ngoại tệ: xem mục **Tỷ giá** bên dưới.
4. Chuẩn hóa địa điểm → `location` (tỉnh/thành)
5. Lọc `country = Việt Nam`
6. Lọc `contract_type` ghi RÕ internship / part-time (loại tin chỉ suy từ từ khóa tìm kiếm)
7. Gom ngành → `category`; encoding `category_code`, `location_code`; thêm `con_han` (còn hạn nộp)

Đầu bước làm sạch có **kiểm cấu trúc**: file thô nào thiếu cột (so với `COLUMNS` trong `1_crawl.py`) thì dừng
và báo rõ tên file, tên cột, không chạy tiếp ra dữ liệu rỗng. Dữ liệu thô không bao giờ bị sửa nên luôn làm sạch lại được.

## Tỷ giá (`ty_gia.py`, `data/ty_gia.csv`)
- **Tỷ giá nào:** tỷ giá **chuyển khoản** của Vietcombank.
- **Ngày nào:** **ngày thu thập** tin đó (`crawl_date`), không phải ngày chạy làm sạch. Chọn ngày thu thập vì
  CareerViet không ghi ngày đăng, chỉ có ngày "cập nhật". Nhờ vậy chạy lại bao nhiêu lần cũng ra cùng kết quả.
- `1_crawl.py` ghi tỷ giá của hôm thu thập vào `data/ty_gia.csv` (mỗi ngày 1 lần). Các ngày cũ (13/10–09/11) được
  bổ sung bằng **tỷ giá lịch sử thật** của đúng ngày đó (Vietcombank cho tra theo ngày), không phải ước lượng.
- Làm sạch đọc bảng này, không cần mạng. Ngày nào còn thiếu thì thử tải; không tải được thì dùng ngày gần nhất
  và đánh `fx_estimated = True`. Chỉ dừng khi có tin ngoại tệ mà chưa có tỷ giá nào của loại tiền đó.
- File sạch giữ số gốc: `salary_text` (chữ gốc), `salary_currency` (VND, USD…), `fx_rate` (tỷ giá đã dùng),
  `fx_date` (ngày của tỷ giá), `fx_estimated`.
- Bổ sung tỷ giá cho mọi ngày đã thu thập: `python ty_gia.py`.

## Phát hiện tin bị sửa / không còn (`data/snapshot/`)
Mỗi lần thu thập, ngoài tải chi tiết tin **mới**, chương trình lưu ảnh chụp **toàn bộ trang danh sách** (cả tin đã
thấy) vào `data/snapshot/<nguồn>_<ngày>.csv`, rồi so với ảnh chụp ngày gần nhất trước đó theo khóa **nguồn + mã tin**
→ `data/snapshot/thay_doi_<nguồn>_<ngày>.csv`:
- **mới**: chỉ có hôm nay; **đã sửa**: có cả 2 ngày nhưng tên việc / công ty / lương / nơi làm khác (ghi từng cột,
  giá trị cũ → mới); **không còn trong kết quả**: chỉ có ngày trước (chưa kết luận là đã xóa, vì trang chỉ hiện tin
  còn hạn và có thể đẩy tin xuống trang sau).
- Trước khi so: bỏ nhãn "(Mới)", khoảng trắng thừa; một ngày có, một ngày rỗng thì không tính là sửa.
- Giới hạn: chỉ so các cột có trên trang danh sách (hạn nộp không có ở đó nên chưa so); tin đăng lại có mã mới
  thì coi là tin mới; chỉ bắt đầu so được từ ngày thứ hai có ảnh chụp (bắt đầu từ 10/11/2026).
- Lúc thu thập, nếu trang danh sách không đọc ra tin nào (trang đổi cấu trúc / lỗi) thì **cảnh báo, không ghi file**;
  nếu các cột thường luôn có (tên, công ty, lương, loại hình, ngày đăng, hạn nộp) rỗng quá nửa thì cảnh báo to.

## Phân tích (`4_phan_tich.py`) — bám đề cương 71DAEE10012
| Chương | Nội dung trong code |
|---|---|
| 2. Thao tác dữ liệu | Đọc CSV → DataFrame; Series → NumPy array; lọc tin lương tháng; bảng dữ liệu thiếu + cách xử lý; one-hot; chia 80/20 |
| 3. Trực quan hóa | Bar, grouped bar, stacked bar, pie, histogram + box, scatter, line, area |
| 4. Thống kê | Thống kê mô tả (trung bình, trung vị, Q1, Q3, độ lệch); Welch t-test, Mann-Whitney U, ANOVA, Kruskal-Wallis, chi-square (α = 0,05) |
| 5. Machine learning | Linear Regression (dự đoán lương: MAE, RMSE, R²); Logistic Regression, Decision Tree, k-NN (phân loại có lương / thỏa thuận: Accuracy, Precision, Recall, F1); K-Means (chọn k bằng silhouette) + PCA |

Mỗi mô hình đều so với **mốc "đoán bừa"** (luôn đoán trung vị / lớp đa số) để biết mô hình có thực sự tốt hơn không.
