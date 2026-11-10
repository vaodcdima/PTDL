# Tổng quan dự án: Thị trường thực tập & part-time tại Việt Nam

| Thông tin | Nội dung |
|---|---|
| Môn học | Phân tích dữ liệu cho Môi trường doanh nghiệp (71DAEE10012), HK1/2026-2027 |
| Giảng viên | PGS. TS. Đặng Trần Khánh |
| Nhóm 3 | Nguyễn Duy Tuấn: xử lý dữ liệu, trực quan hóa |
| | Hoàng Thị Thùy Giang: thống kê, kiểm định giả thuyết |
| | Nguyễn Nam Giang: machine learning, đánh giá mô hình |
| Số liệu tính đến | 04/11/2026 (3 ngày thu thập: 13/10, 03/11, 04/11) |

**Dự án trong một câu:** nhóm tự thu thập tin tuyển dụng thật từ 2 trang web, làm sạch, phân tích theo đúng đề cương môn, rồi đưa kết quả lên một trang web để sinh viên, nhà trường và doanh nghiệp dùng khi ra quyết định.

| Số liệu chính | Giá trị |
|---|---|
| Tin thô thu được | 3.073 tin (CareerViet 2.212, JobOKO 861) |
| Tin dùng để phân tích | 1.134 tin ghi rõ thực tập hoặc part-time |
| Tin có ghi lương | 719 tin (63,4%); 415 tin còn lại ghi “thỏa thuận” (36,6%) |
| Lương trung vị | 3,25 triệu/tháng; phần lớn tin trả 2,5–6 triệu |
| Khu vực | 80% số tin ở TP. Hồ Chí Minh và Hà Nội |
| Doanh nghiệp | 735 công ty, 46 tỉnh/thành |

# Phần A. Tổng quan dự án

## 1. Bài toán thực tế

Sinh viên năm 3, năm 4 tìm thực tập chủ yếu dựa vào tin đồn. Thông tin nằm rải rác trên nhiều trang, và 37% tin không ghi lương, nên sinh viên không biết ngành nào đang cần người và mức lương nào là hợp lý.

Vì đây là môn phân tích dữ liệu cho doanh nghiệp, nhóm bắt đầu từ câu hỏi: dữ liệu này giúp ai ra quyết định gì?

| Người dùng | Cần biết | Để quyết định |
|---|---|---|
| Sinh viên | Ngành nào nhiều cơ hội? Lương bao nhiêu là hợp lý? | Nộp hồ sơ ở đâu, thương lượng mức lương nào |
| Nhà trường | Ngành nào đang cần thực tập sinh nhiều nhất? | Tư vấn sinh viên, chọn doanh nghiệp để kết nối |
| Doanh nghiệp | Lương của mình so với thị trường thế nào? | Đặt lương cạnh tranh, có nên công khai lương |

## 2. Câu hỏi phân tích và kỹ thuật

| # | Câu hỏi | Kỹ thuật | Chương |
|---|---|---|---|
| 1 | Ngành nào, ở đâu có nhiều tin nhất? | Thống kê mô tả; bar, pie, line, area | 3, 4 |
| 2 | Lương giữa các nhóm có khác nhau không? | t-test, Mann-Whitney, ANOVA, Kruskal-Wallis, chi-square | 4 |
| 3 | Dự đoán được lương từ thông tin tin đăng không? | Linear Regression, Logistic, Decision Tree, k-NN | 5 |
| 4 | Tin tuyển dụng tự chia thành những nhóm nào? | K-Means, PCA | 5 |

Chương 2 là nền cho cả bốn câu: đọc dữ liệu, DataFrame, NumPy, lọc, xử lý dữ liệu thiếu, mã hóa, chia train/test. Nhóm không dùng RNN, CNN vì dữ liệu ở dạng bảng, không phải chuỗi thời gian hay hình ảnh.

## 3. Kiến trúc hệ thống

Dữ liệu đi một chiều qua 4 file. Mỗi file chỉ làm một việc và ghi kết quả ra thư mục riêng.

```
careerviet.vn, vn.joboko.com
   |  1_crawl.py      thu thập tin mới, kiểm tra robots.txt
   v
data/raw/             dữ liệu thô theo ngày
   |  2_lam_sach.py   làm sạch 7 bước, lấy tỷ giá Vietcombank
   v
data/clean/           dữ liệu sạch (CSV + Excel)
   |  4_phan_tich.py  biểu đồ, kiểm định, machine learning
   v
data/phan_tich/       biểu đồ PNG, bảng kết quả Excel
   |  web/app.py      xem, lọc, tra cứu
   v
Người dùng
```

Chạy cả quy trình bằng một lệnh `python chay.py`, hoặc bấm nút “Lấy dữ liệu hôm nay” trên web. Sai ở đâu thì sửa và chạy lại từ đó. Dữ liệu thô không bị sửa nên kết quả luôn tái lập được.

## 4. Nguồn dữ liệu và pháp lý

| Nguồn | Cách lấy |
|---|---|
| CareerViet (careerviet.vn) | Tìm theo 5 từ khóa: `thuc-tap`, `thuc-tap-sinh`, `intern`, `part-time`, `ban-thoi-gian`; 50 tin mỗi trang |
| JobOKO (vn.joboko.com) | 4 trang danh sách: tìm “thực tập”, tổng hợp thực tập/part-time, 2 ngành làm thêm; 10 tin mỗi trang |

Các trang đã cân nhắc nhưng không dùng: Vieclam24h (robots.txt cấm đường dẫn tìm kiếm); TopCV, JobsGO, CareerLink (chặn bot, nhóm không vượt rào).

Năm nguyên tắc thu thập, đều viết thẳng vào code trong `1_crawl.py`:

| Nguyên tắc | Cách làm |
|---|---|
| Tôn trọng robots.txt | Kiểm tra trước từng đường dẫn; đường dẫn bị cấm thì bỏ qua |
| Không gây tải máy chủ | Nghỉ 1,5–2 giây giữa 2 lượt truy cập, tải lần lượt, không song song |
| Minh bạch danh tính | User-Agent ghi rõ dự án học thuật của Đại học Văn Lang, không giả trình duyệt |
| Không vượt rào | Không đăng nhập, không giải CAPTCHA, không né chặn bot |
| Chỉ dữ liệu công khai | Chỉ lấy tin tuyển dụng, không lấy thông tin cá nhân; mỗi dòng giữ link gốc |

## 5. Bước 1: Thu thập (`1_crawl.py`)

1. Đọc robots.txt của trang.
2. Đọc trang danh sách, lấy link từng tin.
3. So với các file đã lưu, bỏ qua tin đã có ở các ngày trước.
4. Mở trang chi tiết của tin mới, đọc JSON-LD và các ô thông tin.
5. Ghi từng tin vào file của ngày hôm đó. Dừng giữa chừng thì phần đã tải vẫn còn.

**JSON-LD** là đoạn dữ liệu có cấu trúc theo chuẩn schema.org/JobPosting mà chính trang web nhúng sẵn để Google đọc. Cả 2 trang dùng chung chuẩn này nên chính xác hơn bóc chữ trên giao diện, và ít hỏng khi trang đổi giao diện.

**Kiểm chứng** bằng `3_kiem_chung.py`: mở lại tin ngẫu nhiên trên trang gốc rồi so tên việc, tên công ty. File mặc định kiểm 15 tin. Lần kiểm ngày 04/11 với 30 tin: 25/25 tin còn mở khớp hoàn toàn, 5 tin đã bị gỡ do hết hạn.

**Thời gian chạy:** ngày 13/10 có 1.282 tin mới, mất khoảng 40 phút; ngày 04/11 có 388 tin mới, mất khoảng 13 phút. Lâu là do cố ý nghỉ giữa các lượt truy cập, nhóm không rút ngắn.

## 6. Dữ liệu được lưu ở đâu

Tất cả nằm trong thư mục `data/` của dự án. Mỗi ngày một file, tên file có ghi ngày, không gộp đè lên nhau.

| Đường dẫn | Nội dung | Ai dùng |
|---|---|---|
| `data/raw/careerviet_<ngày>.csv`, `joboko_<ngày>.csv` | Dữ liệu thô: tin mới của ngày đó, 16 cột, không sửa tay. Hiện có 6 file | `2_lam_sach.py` |
| `data/clean/jobs_clean_<ngày>.csv` | Dữ liệu sạch: gộp mọi ngày, 27 cột | Code phân tích, web |
| `data/clean/jobs_clean_<ngày>.xlsx` | Bản Excel: có bộ lọc, thêm sheet `bao_cao_7_buoc` | Người xem |
| `data/phan_tich/<ngày>/` | 10 biểu đồ PNG và `ket_qua_phan_tich.xlsx` | Báo cáo, web |
| `data/cap_nhat.log` | Nhật ký mỗi lần bấm nút cập nhật trên web | Khi cần xem lỗi |

**Vì sao không dùng cơ sở dữ liệu?** Với vài nghìn tin thì CSV là đủ, mở bằng Excel kiểm tra được ngay, và biết rõ tin nào lấy ngày nào. Khi dữ liệu lớn hơn nhiều thì mới cần chuyển.

**Vì sao vừa có CSV vừa có Excel?** CSV để code đọc. Excel để người xem, có định dạng và bộ lọc.

Toàn bộ file code nằm ở thư mục gốc:

```
PTDL/
  chay.py            chạy 1 -> 2 -> 4
  1_crawl.py         thu thập
  2_lam_sach.py      làm sạch 7 bước
  3_kiem_chung.py    đối chiếu tin với trang gốc
  4_phan_tich.py     Chương 2 đến Chương 5
  web/app.py         trang web
  web/style.css      giao diện web
  requirements.txt   thư viện cần cài
  README.md          hướng dẫn ngắn
```

## 7. Bước 2: Làm sạch 7 bước (`2_lam_sach.py`)

**Nguyên tắc:** gắn nhãn thay vì xóa khi dữ liệu thiếu; chỉ xóa khi tin trùng hoặc không đúng đối tượng.

| Bước | Việc làm | Kết quả ngày 04/11 |
|---|---|---|
| 1 | Gộp mọi file theo ngày của 2 nguồn | 3.073 tin từ 6 file |
| 2 | Khử trùng lặp theo tên việc + công ty đã bỏ dấu, kể cả tin chỉ khác đuôi “làm việc tại ...” | 2.767 tin (loại 306) |
| 3 | Lương thành số (triệu VND); “thỏa thuận” gắn nhãn; lương tháng ngoài 0,5–100 triệu gắn cờ `salary_outlier` | 1.323 tin có lương số trên 2.767 tin; 10 tin bất thường |
| 4 | Địa điểm đưa về tên tỉnh/thành chuẩn | 72 giá trị thô thành 57 tỉnh/thành |
| 5 | Lọc `country` = Việt Nam | Không tin nào bị loại |
| 6 | Chỉ giữ tin ghi RÕ thực tập hoặc part-time | 1.134 tin (loại 1.633) |
| 7 | Gom về 12 nhóm ngành và nhóm “Khác”; mã hóa ngành, tỉnh cho ML; thêm cột `con_han` | 13 nhóm trong dữ liệu |

**Ví dụ bước 3, chuẩn hóa lương:**

| Chuỗi gốc | Min (triệu) | Max (triệu) | Nhãn |
|---|---|---|---|
| Lên đến 8 Triệu VND | – | 8 | Có lương |
| 4 - 5 triệu | 4 | 5 | Có lương |
| 800.000 - 5 Triệu VND | 0,8 | 5 | Có lương |
| 100 - 150 USD (lấy ngày 13/10) | 2,572 | 3,858 | Có lương (tỷ giá 13/10: 25.720 đ) |
| Cạnh tranh | – | – | Thỏa thuận |

**Tỷ giá: chuyển khoản Vietcombank của NGÀY THU THẬP tin đó.** Lần đầu nhóm dùng tỷ giá cố định (thầy góp ý), sau đổi sang tỷ giá lúc chạy làm sạch; buổi góp ý 10/11 thầy hỏi tiếp "tỷ giá của ngày nào", vì cách đó đổi mọi tin, kể cả tin lấy từ 13/10, theo tỷ giá hôm chạy. Nay `1_crawl.py` ghi tỷ giá của hôm thu thập vào `data/ty_gia.csv`; các ngày cũ được bổ sung bằng tỷ giá lịch sử thật của đúng ngày (Vietcombank cho tra theo ngày; 13/10: 25.720 đ, 10/11: 25.410 đ). Làm sạch đọc bảng này nên không cần mạng và chạy lại luôn ra cùng kết quả; file sạch giữ `salary_currency`, `fx_rate`, `fx_date`, `fx_estimated` để kiểm lại. Chọn ngày thu thập vì CareerViet không ghi ngày đăng. Code: `ty_gia.py`.

**Ví dụ bước 6.** Tin được giữ nếu ghi rõ ở 1 trong 3 chỗ: loại hình nhà tuyển dụng chọn, ô “Hình thức”, hoặc tiêu đề.

| Tin | Lý do | Kết quả |
|---|---|---|
| Thực tập sinh Tester | Nhà tuyển dụng chọn loại hình INTERN | Giữ |
| Nhân viên bán hàng Part-time | Tiêu đề ghi rõ part-time | Giữ |
| International Sales | Chỉ khớp nhầm từ khóa “intern”, là việc chính thức | Loại |

Nếu giữ các tin như International Sales, lương nhân viên chính thức sẽ làm lương thực tập bị đẩy lên sai lệch.

## 8. Công nghệ sử dụng

Toàn bộ viết bằng Python (nhóm đang chạy Python 3.14), code trên VS Code.

| Công đoạn | Công nghệ | Vì sao chọn |
|---|---|---|
| Thu thập | requests, BeautifulSoup4 | HTML có sẵn dữ liệu, không cần Selenium; nhẹ và ít làm phiền máy chủ |
| Đọc tin | JSON-LD (schema.org) | Chuẩn chung, ít hỏng khi trang đổi giao diện |
| Làm sạch | pandas, re, unicodedata | Chương 2; xử lý tiếng Việt có dấu |
| Tỷ giá | Bảng tỷ giá XML của Vietcombank | Nguồn chính thức, lấy mới mỗi lần chạy |
| Lưu trữ | CSV, Excel (openpyxl) | Mở được ngay, dễ kiểm tra |
| Biểu đồ | matplotlib, seaborn, Altair | Chương 3; Altair vẽ biểu đồ trên web |
| Thống kê, ML | NumPy, SciPy, scikit-learn | Chương 4 và Chương 5 |
| Web | Streamlit | Làm web bằng Python, không cần máy chủ riêng |

## 9. Bám đề cương môn (`4_phan_tich.py`)

| Chương | Nội dung trong code |
|---|---|
| 2. Thao tác dữ liệu | Đọc CSV thành DataFrame; Series sang NumPy array; lọc tin lương tháng; bảng dữ liệu thiếu và cách xử lý; one-hot; chia 80/20 |
| 3. Trực quan hóa | 10 biểu đồ: bar, grouped bar, stacked bar, pie, histogram + box, scatter, line, area, ma trận nhầm lẫn, K-Means + PCA |
| 4. Thống kê | Trung bình, trung vị, Q1, Q3, độ lệch; Shapiro; Welch t-test, Mann-Whitney, ANOVA, Kruskal-Wallis, chi-square (α = 0,05) |
| 5. Machine learning | Linear Regression; Logistic Regression, Decision Tree, k-NN; K-Means, PCA; mỗi mô hình có giám sát đều so với mốc “đoán bừa” |

Xử lý dữ liệu thiếu:

| Cột | Tỷ lệ thiếu | Cách xử lý |
|---|---|---|
| `experience_years` | 65,5% | Khi chạy ML: điền 0, vì tin không ghi thường là không yêu cầu kinh nghiệm |
| `salary_mid` | 36,6% | Không điền; tin “thỏa thuận” đã có nhãn, chỉ phân tích lương trên tin có lương |
| `location` | 4,8% | Gán khu vực “Không rõ” |
| `date_posted`, `deadline` | 0,3% | Bỏ qua khi vẽ theo thời gian; `con_han` = False |

## 10. Kết quả phân tích

### 10.1. Ngành và khu vực

Marketing - Truyền thông dẫn đầu với 334 tin (29%). Ba ngành đầu là Marketing, Giáo dục, Nhân sự chiếm 57%. Về loại hình có 833 tin thực tập, 251 tin part-time, 50 tin tuyển cả hai.

| Ngành | Số tin | Khu vực | Số tin |
|---|---|---|---|
| Marketing - Truyền thông | 334 | TP. Hồ Chí Minh | 565 |
| Giáo dục - Ngôn ngữ | 170 | Hà Nội | 340 |
| Nhân sự - Hành chính | 141 | Tỉnh khác | 175 |
| Kinh doanh - Bán hàng | 106 | Không ghi rõ | 54 |
| Kế toán - Tài chính - Ngân hàng | 105 | | |
| Kỹ thuật - Sản xuất | 94 | | |

Các ngành còn lại: CNTT 48, Nhà hàng - Khách sạn 36, Khác 30, Chăm sóc khách hàng 23, Thiết kế 23, Logistics 20, Y tế 4.

![Số tin theo ngành](data/phan_tich/2026-11-04/01_bar_tin_theo_nganh.png)

### 10.2. Lương

Thống kê trên 712 tin có lương tháng hợp lệ. Nhóm dùng trung vị vì lương lệch phải, vài tin rất cao kéo trung bình lên.

| Nhóm | Số tin | Trung vị (triệu) | Q1 – Q3 (triệu) | Trung bình (triệu) |
|---|---|---|---|---|
| Thực tập | 519 | 3 | 2 – 4 | 3,53 |
| Part-time | 155 | 9,5 | 6 – 11,5 | 9,35 |
| Tuyển cả hai | 38 | 3,22 | 2,5 – 5,56 | 4,28 |

**Điểm cần chú ý:** phần lớn tin part-time có lương là gia sư, giáo viên online, nhóm này trả cao (trung vị ngành Giáo dục 11,5 triệu). Nếu so ngay sẽ kết luận sai là part-time gấp 3 lần thực tập. Khi bỏ ngành Giáo dục, thực tập còn 511 tin với trung vị 3 triệu, part-time còn 60 tin với trung vị 6 triệu, tức khoảng gấp đôi. Đây là con số nhóm dùng để kết luận.

![Phân bố lương](data/phan_tich/2026-11-04/05_hist_box_luong.png)

### 10.3. Kiểm định giả thuyết (α = 0,05)

Lương không phân phối chuẩn (Shapiro p < 0,001) nên nhóm ưu tiên kiểm định phi tham số. t-test và ANOVA cho cùng kết luận.

| Kiểm định | Câu hỏi | p | Kết luận |
|---|---|---|---|
| Welch t-test | Lương thực tập và part-time | < 0,001 | Khác biệt |
| Mann-Whitney U | Lương thực tập và part-time | < 0,001 | Khác biệt |
| Mann-Whitney U | Như trên, bỏ ngành Giáo dục | < 0,001 | Khác biệt |
| ANOVA | Lương giữa 8 ngành có từ 20 tin có lương | < 0,001 | Khác biệt |
| Kruskal-Wallis | Lương giữa 8 ngành có từ 20 tin có lương | < 0,001 | Khác biệt |
| Chi-square | Khu vực và loại hình | < 0,001 | Có liên hệ |
| Chi-square | Ngành và việc công khai lương | 0,056 | Chưa đủ bằng chứng |

Kiểm định cuối đáng chú ý: lần phân tích trước với ít dữ liệu hơn cho p < 0,05, nhưng thêm dữ liệu thì p = 0,056. Vì vậy nhóm chưa kết luận việc công khai lương phụ thuộc vào ngành.

### 10.4. Machine learning (chia 80% huấn luyện, 20% kiểm tra)

Đầu vào của hai bài toán dự đoán: ngành, khu vực, loại hình, nguồn, số năm kinh nghiệm.

**Dự đoán lương (train 569 tin, test 143 tin):**

| Mô hình | MAE (triệu) | RMSE (triệu) | R² |
|---|---|---|---|
| Linear Regression | 1,926 | 5,062 | 0,322 |
| Mốc so sánh: luôn đoán trung vị | 3,292 | 6,645 | -0,168 |

Mô hình sai ít hơn hẳn so với đoán bừa, đủ để ước tính tham khảo cho tin “thỏa thuận”, nên nhóm đưa vào web.

**Phân loại tin có ghi lương hay không:**

| Mô hình | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic Regression | 64,8% | 64,7% | 97,9% | 77,9% |
| Decision Tree (độ sâu 5) | 63,9% | 65,7% | 90,3% | 76,0% |
| k-NN (k = 7) | 65,6% | 67,7% | 87,5% | 76,4% |
| Mốc so sánh: luôn đoán lớp đa số | 63,4% | 63,4% | 100% | 77,6% |

Cả ba mô hình gần như không hơn mốc đoán bừa: ngành, nơi làm, loại hình chưa đủ để đoán việc công khai lương. Nhóm trình bày thẳng kết quả này.

**Phân cụm K-Means** trên 712 tin có lương, dùng lương, loại hình, khu vực: thử k từ 2 đến 6, silhouette chọn k = 6 (điểm 0,706). PCA 2 chiều giữ 53,4% phương sai.

| Cụm | Số tin | Lương trung vị (triệu) | Tỷ lệ part-time | Khu vực chính | Ngành chính |
|---|---|---|---|---|---|
| 0 | 131 | 8,5 | 99,2% | Hà Nội | Giáo dục - Ngôn ngữ |
| 1 | 282 | 3 | 0% | TP. Hồ Chí Minh | Marketing - Truyền thông |
| 2 | 167 | 3,25 | 0% | Hà Nội | Marketing - Truyền thông |
| 3 | 38 | 3,22 | 100% | Hà Nội | Marketing - Truyền thông |
| 4 | 58 | 3,5 | 0% | Tỉnh khác | Marketing - Truyền thông |
| 5 | 36 | 10,5 | 69,4% | Không rõ | Giáo dục - Ngôn ngữ |

Các cụm chủ yếu chia theo loại hình và khu vực, vì các cột này chiếm phần lớn đầu vào, nên không nên hiểu là phát hiện bất ngờ.

**Muốn mô hình tốt hơn cần thêm dữ liệu:** kỹ năng trong mô tả công việc, quy mô công ty.

## 11. Khuyến nghị

| Nhóm | Khuyến nghị |
|---|---|
| Sinh viên | Ưu tiên Marketing, Giáo dục, Nhân sự vì chiếm 57% số tin. Thực tập phần lớn trả 2–4 triệu, dưới 2 triệu là thấp, nên thương lượng. Cần thu nhập cao hơn thì xem part-time, nhất là gia sư, dạy online |
| Nhà trường | Ưu tiên tìm đối tác thực tập ở 3 ngành nhiều tin nhất. Y tế (4 tin), Logistics (20 tin) ít tin trên 2 trang này nên cần hỗ trợ sinh viên thêm kênh khác. Dùng web khi tư vấn để sinh viên thấy số liệu thật |
| Doanh nghiệp | Mốc lương thực tập: trung vị 3 triệu, phần lớn 2–4 triệu. 37% tin chưa công khai lương, nên ghi rõ lương là cách để khác biệt. Ngoài TP. Hồ Chí Minh, Hà Nội chỉ có 15% số tin nên ít tin cạnh tranh hơn, nhưng chưa biết số ứng viên ở từng nơi |

Đây là gợi ý suy ra từ dữ liệu 2 trang, chưa phải kết luận cho toàn thị trường.

## 12. Trang web (`web/app.py`)

Viết bằng Streamlit, để người không biết code cũng xem và tra cứu được.

**Hàng chọn trên cùng:** Ngày thu thập (từng ngày trong 5 ngày gần nhất, hoặc tất cả), Loại hình, Ngành, Tỉnh/thành. Mọi con số và biểu đồ đổi theo lựa chọn.

| Tab | Nội dung |
|---|---|
| Tổng quan | Số liệu chính, khuyến nghị cho 3 nhóm, biểu đồ ngành, tỉnh, loại hình, số tin mới theo ngày |
| Lương & thương lượng | Khoảng lương phổ biến, so sánh thực tập với part-time cùng ngành, ô ước tính lương |
| Tra cứu tin | Tìm theo từ khóa, lọc tin còn hạn hoặc có lương, mở tin gốc, tải danh sách ra CSV |
| Phân tích thống kê | Kiểm định, thống kê mô tả, kết quả mô hình, bộ biểu đồ đầy đủ |
| Dữ liệu & hướng dẫn | Nguồn, phương pháp, cách sử dụng |

**Hai điểm đáng chú ý:** nút “Lấy dữ liệu hôm nay” ở thanh bên trái chạy cả quy trình ở nền, có hiện tiến độ, không cần terminal; xong bấm “Hiển thị dữ liệu mới”. Và tin ghi “thỏa thuận” có kèm lương ước tính từ mô hình.

<!-- ANH_WEB -->

## 13. Cách chạy

| Muốn làm gì | Làm thế nào |
|---|---|
| Cài thư viện (1 lần) | `pip install -r requirements.txt` |
| Mở web | Mở `web/app.py` trong VS Code bấm Run, hoặc gõ `python web/app.py`. Trình duyệt tự mở http://localhost:8501; tắt bằng Ctrl+C trong terminal |
| Lấy dữ liệu mới mỗi ngày | Bấm nút “Lấy dữ liệu hôm nay” trên web, hoặc gõ `python chay.py`. Mất khoảng 15–45 phút tùy số tin mới |
| Chạy riêng từng bước | `python 1_crawl.py`, `python 2_lam_sach.py`, `python 4_phan_tich.py` |
| Kiểm chứng 15 tin ngẫu nhiên | `python 3_kiem_chung.py` |

| Hiện tượng | Cách xử lý |
|---|---|
| Báo file đang mở trong Excel | Đóng file trong Excel rồi chạy lại |
| Không lấy được tỷ giá Vietcombank | Kiểm tra mạng rồi chạy `python 2_lam_sach.py`; dữ liệu thô không mất |
| `ModuleNotFoundError` | Chạy `pip install -r requirements.txt` |
| Dừng giữa chừng bằng Ctrl+C | Dữ liệu đã tải vẫn còn; lần sau chạy tiếp phần còn thiếu |

## 14. Các yêu cầu đã thực hiện

| Yêu cầu | Đã làm | Ở đâu |
|---|---|---|
| Crawl trực tiếp 2 trang, cập nhật được mỗi ngày | Chỉ tải tin mới, không trùng các ngày trước | `1_crawl.py` |
| Chạy Python đơn giản, không cần phức tạp | Một lệnh chạy hết | `chay.py` |
| Làm sạch đúng theo slide của nhóm | Đủ 7 bước | `2_lam_sach.py` |
| Mỗi ngày một file, có ghi ngày, không gộp | Tên file có ngày tháng năm | `data/raw/`, `data/clean/` |
| Chỉ giữ Excel ở thư mục clean, bỏ báo cáo .txt | Báo cáo nằm trong sheet `bao_cao_7_buoc` | `data/clean/` |
| Quy đổi ngoại tệ không dùng số cứng; tỷ giá của đúng ngày (góp ý 10/11) | Tỷ giá Vietcombank của ngày thu thập, giữ số gốc | `ty_gia.py`, `data/ty_gia.csv` |
| Hệ thống phải nhận ra tin bị sửa / gỡ (góp ý 10/11) | Ảnh chụp danh sách mỗi ngày, so theo nguồn + mã tin | `data/snapshot/`, `1_crawl.py` |
| Schema có thể đổi (góp ý 10/11) | Kiểm đủ cột trước khi làm sạch; không ghi file rỗng | `2_lam_sach.py`, `1_crawl.py` |
| Code chuẩn đề cương môn | Chương 2 đến Chương 5 | `4_phan_tich.py` |
| Giải quyết bài toán thực tế, nghĩ như doanh nghiệp | Khuyến nghị cho 3 nhóm người dùng | Mục 11, tab Tổng quan |
| Web để demo, dễ dùng | 5 tab, tra cứu, ước tính lương | `web/app.py` |
| Giao diện để riêng | Tách file CSS | `web/style.css` |
| Bấm trên web thay cho terminal | Nút “Lấy dữ liệu hôm nay” | Thanh bên trái của web |
| Xem dữ liệu theo từng ngày | Ô chọn 5 ngày gần nhất hoặc tất cả | Hàng chọn trên cùng của web |
| Chạy từ VS Code | Bấm Run hoặc `python web/app.py` | `web/app.py` |

## 15. Hạn chế

| Hạn chế | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| Chỉ 2 trang tuyển dụng | Chưa đại diện toàn thị trường | Nêu rõ trong báo cáo; kết luận chỉ cho 2 kênh này |
| Mới 3 ngày thu thập, chưa liên tục | Chưa phân tích được xu hướng theo thời gian | Chạy đều mỗi ngày |
| 65% tin không ghi kinh nghiệm | Chưa trả lời được lương theo kinh nghiệm | Giữ nguyên, ghi rõ cách xử lý |
| Thiếu biến kỹ năng, quy mô công ty | Mô hình chưa mạnh, R² = 0,32 | Thêm biến từ mô tả công việc |
| Tin đăng nhiều tỉnh chỉ tính tỉnh đầu | Số liệu theo tỉnh có thể lệch nhẹ | Ghi chú trong báo cáo |

## 16. Kế hoạch

| Thời gian | Việc |
|---|---|
| Từ nay | Chạy thu thập đều mỗi ngày |
| 11/11 (Session 10) | GL2, 15%: thiết kế hệ thống, công nghệ |
| 18/11 – 02/12 (Session 11–13) | Thêm biến kỹ năng, cải thiện mô hình |
| 09/12 (Session 14) | GL3, 15%: kiểm tra tiến độ |
| 16/12 (Session 15) | Cuối kỳ, 50%: thuyết trình, báo cáo kỹ thuật, video |

## 17. Từ điển dữ liệu

**Dữ liệu thô** (16 cột): `data/raw/<nguồn>_<ngày>.csv`

| Cột | Ý nghĩa | Ví dụ |
|---|---|---|
| `source` | Nguồn | careerviet |
| `job_id` | Mã tin trên trang nguồn | 35C8704D |
| `title` | Tên việc | Thực tập sinh Tester |
| `company` | Công ty | Techcombank |
| `salary_text` | Lương nguyên văn | Lên đến 8 Triệu VND |
| `location_text` | Địa điểm nguyên văn | Hà Nội, Hồ Chí Minh |
| `country` | Mã quốc gia | VN |
| `employment_type` | Loại hình nhà tuyển dụng chọn | FULL_TIME, INTERN |
| `hinh_thuc` | Ô “Hình thức” trên trang | Thực tập |
| `industry` | Ngành nghề nguyên văn | CNTT - Phần mềm |
| `experience` | Kinh nghiệm nguyên văn | Không yêu cầu kinh nghiệm |
| `date_posted` | Ngày đăng | 2026-09-14 |
| `deadline` | Hạn nộp | 2026-10-14 |
| `query` | Từ khóa hoặc trang tìm ra tin | thuc-tap |
| `url` | Link tin gốc | https://careerviet.vn/... |
| `crawled_at` | Thời điểm thu thập | 2026-10-12 23:01 |

**Dữ liệu sạch** (27 cột): `data/clean/jobs_clean_<ngày>.csv`

| Nhóm | Cột | Ý nghĩa |
|---|---|---|
| Tin | `source`, `job_id`, `title`, `company` | Nguồn, mã tin, tên việc, công ty |
| Phân loại | `category` | Nhóm ngành |
| | `contract_type` | `internship`, `part-time` hoặc `internship/part-time` |
| | `location`, `country` | Tỉnh/thành (trống là tin không ghi), quốc gia |
| Lương | `salary_min`, `salary_max`, `salary_mid` | Triệu VND; `salary_mid` là trung bình min và max |
| | `salary_unit` | `tháng` hoặc `giờ` |
| | `salary_label` | `Có lương` hoặc `Thỏa thuận` |
| | `salary_outlier` | Cờ lương tháng ngoài 0,5–100 triệu |
| | `salary_text` | Chuỗi lương gốc để đối chiếu |
| | `salary_currency`, `fx_rate`, `fx_date`, `fx_estimated` | Loại tiền gốc; tỷ giá, ngày tỷ giá đã dùng (chỉ tin ngoại tệ); True nếu phải dùng ngày gần nhất |
| Kinh nghiệm | `experience_years` | Số năm yêu cầu; 0 là không yêu cầu, trống là không ghi |
| Thời gian | `date_posted`, `deadline`, `con_han` | Ngày đăng, hạn nộp, còn hạn hay không |
| Mã hóa | `category_code`, `location_code` | Số nguyên cho mô hình |
| Truy vết | `url`, `crawl_date` | Link gốc, ngày thu thập |

# Phần B. Câu hỏi thầy có thể hỏi

**1. Crawl như vậy có đúng quy định không?**
Nhóm chỉ lấy tin công khai, không cần đăng nhập; kiểm tra robots.txt trước từng đường dẫn; nghỉ 1,5–2 giây giữa các lượt; tự giới thiệu là dự án học thuật; không lấy thông tin cá nhân. Trang nào cấm hoặc chặn bot thì nhóm bỏ, không vượt rào.

**2. Vì sao chỉ có 2 trang?**
Hai trang này cho phép và có dữ liệu chuẩn JSON-LD. Vieclam24h cấm trong robots.txt; TopCV, JobsGO, CareerLink chặn bot. Đây là hạn chế, nên kết luận chỉ áp dụng cho tin đăng ở 2 kênh này.

**3. Làm sao biết dữ liệu là thật?**
Mỗi dòng giữ link gốc. File `3_kiem_chung.py` mở lại tin ngẫu nhiên và so với trang gốc: lần chạy ngày 04/11 có 25/25 tin còn mở khớp, 5 tin đã bị gỡ do hết hạn. Có thể bấm “Xem tin gốc” trên web ngay trong buổi thuyết trình.

**4. Vì sao từ 3.073 tin chỉ còn 1.134 tin?**
306 tin trùng. 1.633 tin không ghi rõ là thực tập hoặc part-time, chủ yếu là việc chính thức bị khớp từ khóa tìm kiếm, ví dụ “intern” khớp “International”. Giữ lại sẽ làm lương thực tập bị đẩy lên sai lệch.

**5. Chạy mỗi ngày có bị trùng không?**
Không. `1_crawl.py` đọc các file đã lưu và bỏ qua tin đã có. Bước 2 làm sạch còn khử trùng thêm theo tên việc và công ty, để bắt tin đăng lại với mã mới hoặc đăng ở cả 2 trang.

**6. Tỷ giá lấy thế nào?**
Mỗi lần chạy, chương trình đọc bảng tỷ giá XML của Vietcombank và dùng tỷ giá chuyển khoản, không có số cố định trong code. Không lấy được thì dừng và báo lỗi, không dùng số cũ.

**7. Vì sao dùng trung vị mà không dùng trung bình?**
Lương lệch phải: thực tập có hệ số lệch 5,71, có tin tới 38 triệu. Vài tin rất cao kéo trung bình lên, còn trung vị phản ánh đúng mức phổ biến hơn.

**8. Đã biết lương không phân phối chuẩn, sao vẫn chạy t-test và ANOVA?**
Để đối chiếu với kiểm định phi tham số, vì đề cương có cả hai. Nhóm dựa vào Mann-Whitney và Kruskal-Wallis để kết luận; t-test và ANOVA cho cùng kết luận nên kết quả chắc chắn hơn.

**9. p = 0,056 nghĩa là gì?**
Lớn hơn mức 0,05 nên chưa đủ bằng chứng bác bỏ giả thuyết “việc ghi lương không phụ thuộc ngành”. Điều này không có nghĩa là chắc chắn không phụ thuộc. Con số gần ngưỡng và đã đổi khi thêm dữ liệu, nên cần thu thập thêm.

**10. R² = 0,32 có thấp không, sao vẫn dùng?**
Thấp, mô hình mới giải thích khoảng một phần ba biến động của lương. Nhưng sai số trung bình 1,93 triệu so với 3,29 triệu nếu đoán bừa, nên vẫn có ích để tham khảo. Trên web luôn ghi kèm sai số và ghi rõ là ước tính. Muốn tốt hơn cần thêm biến kỹ năng, quy mô công ty.

**11. Mô hình phân loại chỉ ngang đoán bừa, vậy có thất bại không?**
Về dự đoán thì chưa tốt, và nhóm nói thẳng điều đó. Đây cũng là một phát hiện: các thông tin hiện có chưa đoán được doanh nghiệp có công khai lương hay không. Logistic có Recall gần 98% tức là gần như luôn đoán “có lương”, nên không được chỉ nhìn Accuracy.

**12. Silhouette 0,71 khá cao, vậy phân cụm có tốt không?**
Các cụm tách rõ, nhưng chủ yếu theo loại hình và khu vực, là những cột chiếm phần lớn đầu vào sau one-hot. Nên điểm cao không có nghĩa là phát hiện được nhóm mới. Kết quả chỉ để mô tả dữ liệu.

**13. 65% tin không ghi kinh nghiệm, xử lý thế nào?**
Khi chạy ML, nhóm điền 0 vì tin không ghi thường là không yêu cầu; đây là một giả định và đã ghi trong bảng dữ liệu thiếu. Nhóm không kết luận về lương theo kinh nghiệm vì thiếu quá nhiều.

**14. Vì sao không dùng cơ sở dữ liệu?**
Vài nghìn tin thì CSV là đủ, dễ kiểm tra bằng Excel và biết rõ tin nào lấy ngày nào. Khi dữ liệu lớn hơn nhiều thì mới cần chuyển.

**15. Vì sao không dùng Selenium?**
Hai trang trả về HTML có sẵn dữ liệu, nên `requests` đủ dùng, nhanh hơn, nhẹ hơn và ít làm phiền máy chủ hơn.

**16. Vì sao không dùng RNN, CNN?**
Dữ liệu ở dạng bảng, không phải chuỗi thời gian hay hình ảnh. Dùng mô hình phức tạp khi không phù hợp sẽ không giúp ích.

**17. Tin ngày 04/11 sao chỉ có 56 tin sau làm sạch?**
Ngày 04/11 chỉ cách lần trước 1 ngày nên có 388 tin thô mới, và chỉ tính tin mới xuất hiện trong ngày; sau lọc còn 56 tin. Con số này không có nghĩa là thị trường giảm.

**18. Sao chạy lâu vậy?**
Do cố ý nghỉ giữa các lượt truy cập để không làm nặng máy chủ, không phải do code chậm. Nhóm không rút ngắn vì đó là nguyên tắc thu thập có trách nhiệm.
