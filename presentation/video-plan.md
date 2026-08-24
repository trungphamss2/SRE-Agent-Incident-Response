# Kế hoạch quay Video Demo — 3 phút

Viết lại ngày 24/08 theo **khung BTC yêu cầu**, thay bản 21/08 *(vẫn xem được trong
git history — ý "thử ép thi hành, bị chặn" của Long được giữ, xem cảnh 8)*.

```
0:00 ── 0:40   VẤN ĐỀ + CHÂN DUNG AGENT        40 giây
0:40 ── 2:30   DEMO VẬN HÀNH                  110 giây
2:30 ── 3:00   GIÁ TRỊ + KẾT QUẢ               30 giây
```

Nhịp đọc **150 chữ/phút = 2,5 chữ/giây**. Mỗi cảnh đã đếm chữ — **đừng thêm chữ**,
thêm là tràn giờ và phải cắt hình.

Tổng lời thoại: **~430 chữ**. Ngân sách tối đa 450.

---

## Vì sao chọn UC-4 chứ không phải UC-1

Ba phút chỉ đủ một kịch bản. UC-4 *(deploy thiếu migration)* là kịch bản duy nhất
có đủ bốn thứ giám khảo sẽ tìm:

| | UC-1 pool cạn | **UC-4 thiếu migration** |
|---|---|---|
Số đo có nói ra vấn đề? | có — p95 vọt lên | **KHÔNG — p95 còn nhanh hơn thường** |
Có buộc phải đọc log? | không | **có, đây là nguồn duy nhất** |
Có sửa được **thật**? | chưa | **có — lỗi 100% → 0%** |
Có cổng người duyệt? | có | có |

Dòng thứ hai là lý do. UC-4 là chỗ **số đo nói ngược sự thật** — và đó là toàn bộ
lý do sản phẩm này tồn tại.

---

# A. Chuẩn bị trước khi bấm ghi

Sáu bẫy dưới đây **đều đã làm hỏng một buổi tập rồi**. Đọc hết trước khi quay.

## A1. Bật hệ thống — thứ tự này quan trọng

```bash
cd /Users/duc/VIN_AI/P-035

# 1) demo stack
DEMO_POSTGRES_PORT=55432 docker compose -f docker-compose.demo.yml up -d
docker ps --format '{{.Names}}' | grep p035-demo      # phải ra 4 dòng

# 2) backend — CỜ REMEDIATION_REAL PHẢI Ở ĐÂY
pkill -f "uvicorn src.main"
REMEDIATION_REAL=1 python -m uvicorn src.main:app --port 8000 &
sleep 8
curl -s localhost:8000/health                          # {"status":"ok",...}

# 3) UI — điểm khởi động là status_page.py, KHÔNG phải war room
API_URL=http://localhost:8000 \
JIRA_BASE_URL=https://jibinarybro.atlassian.net \
PROM_URL=http://localhost:9090 \
  streamlit run ui/status_page.py &
curl -s -o /dev/null -w "%{http_code}\n" localhost:8501/war_room   # 200
```

> 🪤 **Bẫy 1 — `REMEDIATION_REAL=1` phải đặt trên backend, không phải trên `duyet.py`.**
> `duyet.py` chỉ gửi HTTP; phần thi hành chạy trong tiến trình backend. Đặt sai chỗ
> thì kết quả trả `simulated=true` mà **không báo lỗi gì** — mất 15 phút mới nhận ra
> (17/08). Quay xong cả video rồi mới thấy chữ `simulated` là **quay lại từ đầu**.

> 🪤 **Bẫy 2 — lệnh bật UI đã đổi ngày 22/08.** `ui/war_room.py` chuyển sang
> `ui/pages/war_room.py` (Streamlit multi-page: một tiến trình, hai trang).
>
>     localhost:8501            → trang trạng thái (cảnh 2)
>     localhost:8501/war_room   → WAR ROOM (cảnh 7)
>
> Và **phải đủ ba biến**. Thiếu `JIRA_BASE_URL` thì cảnh 7 mất nút *"Mở phiếu Jira"*;
> thiếu `PROM_URL` thì mất nút *"kiểm chứng PromQL"* — mà cảnh 7 lấy đúng hai thứ đó
> làm điểm nhấn. Đã vấp thật 21/08: chỉ truyền `API_URL`.

## A2. Hai điều kiện phải kiểm — 20 giây

```bash
# ① KHÔNG service nào còn phiếu đang mở
python -c "
from dotenv import load_dotenv; load_dotenv('.env')
from src.config import get_settings
from src.services.jira.real import RealJiraClient
s=get_settings(); c=RealJiraClient(s.jira_base_url,s.jira_email,s.jira_api_token,s.jira_project_key)
for sv in ('service-thanh-toan','service-dat-hang'):
    print(sv, '→', c.find_open_incident(sv))"
# phải ra None cả hai
```

> 🪤 **Bẫy 3 — phiếu đang mở làm CẢNH 6 mất hết nội dung.**
> `open_war_room()` thấy service đã có phiếu mở thì chỉ **comment cập nhật**, không
> chẩn đoán lại và **không đề xuất lại**. Nên ở cảnh 6 — phần chính, 32 giây, dài
> nhất video — Agent chỉ in `"đã có incident đang mở"`. Không có `rollback` để duyệt,
> nên **cảnh 6, 7, 8, 9 mất hết nội dung**.
>
> Hành vi này **có chủ ý** (chống mở phiếu trùng), không phải lỗi. Đã vấp hai lần
> trong hai ngày.

> 🪤 **Bẫy 4 — người khác chạy Agent giữa lúc mình quay.**
> Bản deploy `035.emmetech.id.vn` và Render đều dùng `JIRA_PROJECT_KEY=KAN` — **cùng
> một bảng** với máy quay. Board đi từ KAN-61 lên KAN-85 trong hai ngày mà không phải
> mình làm.
>
> Nhắn nhóm trước khi bấm ghi: *"t đang quay, đừng ai chạy `run_agent.py`"*.

## A3. Seed — trong vòng 15 phút trước cảnh 4

```bash
python demo/seed.py
```

> 🪤 **Bẫy 5 — seed quá sớm thì Agent đề xuất SAI hành động.**
> `seed.py` đặt `v1.4.3` ở mốc *"3 phút trước"*, còn `rules.DEPLOY_WINDOW_MINUTES = 15`.
> Quá hạn thì `correlate_deploy()` trả `None`, Agent tụt về nhánh mặc định và đề xuất
> **`scale_up`** thay vì **`rollback`**. Mà `executors._CHO_PHEP` chỉ cho thi hành thật
> `rollback` → cảnh 9 ra `(mô phỏng)`.
>
> Đo lúc vấp: deploy cách sự cố **58,7 phút**. Mọi mắt khác vẫn đúng — log vẫn tìm ra
> `idempotency_key`, tin cậy vẫn tăng — **chỉ hành động là sai, và không có dòng lỗi nào.**

## A4. Tài khoản Jira — bẫy chết người

> 🪤 **Bẫy 6 — Agent không tự duyệt được, kể cả khi mình muốn.**
> Cổng HITL đọc changelog Jira: ai chuyển trạng thái mà **trùng account của Agent**
> thì `ApprovalError`, không thi hành. Nên phải kéo phiếu bằng **tài khoản người**
> (`thaiduc200427`), không phải tài khoản Agent (`thaiduc0201`).
>
> Đây cũng chính là thứ cảnh 9 đem ra làm bằng chứng — **hai cái tên khác nhau trong
> lịch sử phiếu**.

## A5. Ba cửa sổ, sắp sẵn trước khi ghi

| Cửa sổ | Địa chỉ | Dùng ở cảnh |
|---|---|---|
Terminal *(phóng chữ ≥ 16pt)* | — | 4, 5, 6, 8, 10 |
Trang trạng thái | http://localhost:8501 | 2 |
War room | http://localhost:8501/war_room | 7 |
Jira | board KAN | 9 |

## A6. Dọn màn hình

- Tắt hết thông báo *(Do Not Disturb)*
- Đóng tab không liên quan — thanh bookmark càng gọn càng tốt
- Terminal: chữ to, nền tối, **không** hiện tên máy/đường dẫn dài
- Ẩn thanh Dock

---

# B. Timeline — 11 cảnh

---

## PHẦN 1 · VẤN ĐỀ + CHÂN DUNG AGENT · 0:00–0:40

### Cảnh 1 · 0:00–0:14 · Vấn đề

**Màn hình:** B-roll shot A *(xem mục C)* — phòng tối, điện thoại úp im, đèn xanh mờ
ngoài nét phía sau.

> "Hai giờ sáng, hệ thống thanh toán có sự cố. Người trực bị gọi dậy. Họ không thiếu
> kỹ năng sửa — họ thiếu **bối cảnh**: chuyện gì đang xảy ra, vì sao, và nên làm gì
> trước."

*(35 chữ · 14 giây)*

---

### Cảnh 2 · 0:14–0:26 · Vì sao monitor không đủ

**Màn hình:** trang trạng thái thật, `localhost:8501` — hai thẻ xanh, *"Hoạt động
bình thường"*. Không rê chuột.

> "Công cụ theo dõi trả lời được *có gì đó sai*. Nó không trả lời được **sai cái gì**,
> và **nên làm gì**. Khoảng trống đó, hiện tại là con người lấp bằng kinh nghiệm — lúc
> hai giờ sáng."

*(36 chữ · 12 giây)*

---

### Cảnh 3 · 0:26–0:40 · Chân dung Agent

**Màn hình:** sơ đồ 4 khối, dựng đơn giản — `PHÁT HIỆN → CHẨN ĐOÁN → ĐỀ XUẤT → CHỜ
DUYỆT`. Khối cuối tô khác màu.

> "Agent này làm bốn việc: **phát hiện** sự cố từ số đo, **chẩn đoán** nguyên nhân —
> kể cả khi phải đọc log, **đề xuất** cách khắc phục kèm rủi ro, rồi **tự đo lại** sau
> khi sửa.
>
> Việc duy nhất nó **không** làm là tự bấm nút. Mọi hành động lên hệ thống thật đều
> phải có người duyệt. Đó là thiết kế, không phải giới hạn."

*(58 chữ · 14 giây — đọc nhanh, đây là nhịp dày nhất)*

> **Vì sao câu cuối phải nằm ở đây, không để tới cảnh 8:** giám khảo nghe *"AI vận hành
> production"* là nghĩ ngay *"nguy hiểm"*. Trả lời trước thì 100 giây sau đó họ xem với
> tâm thế khác.

---

## PHẦN 2 · DEMO VẬN HÀNH · 0:40–2:30

### Cảnh 4 · 0:40–0:56 · Gây sự cố thật

**Màn hình:** Terminal.

```bash
SIMULATE_MISSING_MIGRATION=1 DEMO_POSTGRES_PORT=55432 \
  docker compose -f docker-compose.demo.yml up -d --force-recreate service-thanh-toan

python eval/run_measurements.py payment-load --seconds 80 --concurrency 3 --pause 0.05
```

**Tua nhanh ×6** đoạn chờ 80 giây. Kết thúc phải hiện dòng thống kê `{"500": …, "502": …}`.

> "Đây là sự cố thật, không phải mô phỏng. Bản `v1.4.3` thêm tính năng chống trùng giao
> dịch, nhưng **quên chạy migration** — cột trong database chưa tồn tại. Giờ không ai
> thanh toán được."

*(40 chữ · 16 giây)*

**Hậu kỳ:** khoanh đỏ dòng thống kê, giữ 2 giây. Overlay chữ **`0 request thành công`**.

---

### Cảnh 5 · 0:56–1:18 · SỐ ĐO MÙ — **đây là lý do sản phẩm tồn tại**

**Màn hình:** Terminal.

```bash
curl -s -G localhost:9090/api/v1/query --data-urlencode \
 'query=histogram_quantile(0.95, sum by (service,le) (rate(http_request_duration_seconds_bucket{handler!="/metrics",service="service-thanh-toan"}[1m])))'
```

Kết quả: **p95 ≈ 0,048 giây**.

> "Và đây là chỗ công cụ monitor bó tay. Lỗi gần một trăm phần trăm — nhưng thời gian
> phản hồi chỉ **bốn mươi tám mili giây**, nhanh hơn cả lúc bình thường. Vì request chết
> ngay ở câu lệnh đầu, chưa kịp chậm. Pool thì rảnh. Nhìn ba con số này mà đoán ra nguyên
> nhân là **không thể**."

*(55 chữ · 22 giây)*

**Hậu kỳ:** overlay ba ô cạnh nhau —
`Lỗi 99%` *(đỏ)* · `p95 0,048s` *(xanh)* · `Pool 0%` *(xanh)*

> ⏱ **Giữ overlay thêm 3 giây SAU khi hết lời thoại — im lặng, không nhạc.**
>
> Nếu người xem không *thấm* nghịch lý này thì cảnh 6 chỉ còn là *"AI đọc log"* — nghe
> giống trăm dự án khác, và mọi thứ sau đó mất trọng lượng. **Ba giây im lặng làm con số
> nặng hơn ba câu giải thích.**
>
> Cảnh này **không được cắt** dù có tràn giờ. Cắt chỗ khác.

---

### Cảnh 6 · 1:18–1:50 · Agent vào cuộc — phần chính

**Màn hình:** Terminal.

```bash
python scripts/run_agent.py --once
```

Dừng và khoanh **hai dòng log**:

| Dòng | Hậu kỳ |
|---|---|
`giả thuyết (tin cậy 30%) — Chưa đủ bằng chứng để nêu nguyên nhân gốc. Trùng thời gian: deploy v1.4.3 diễn ra 5 phút trước — chưa xác minh nhân quả…` | khoanh đỏ **cả câu**, giữ 4 giây |
`log đổi kết luận, post lại lên war room (tin cậy 30% → 70%) — thiếu cột idempotency_key trong bảng payments` | khoanh đỏ, giữ 4 giây |

> "Agent quét, phát hiện, mở phiếu. Rồi nó nói một câu đáng chú ý: *chưa đủ bằng chứng
> để nêu nguyên nhân gốc*. Nó thấy có một lần deploy trùng thời gian — và nói thẳng
> **trùng thời gian chưa phải nhân quả**.
>
> Sau đó nó đọc log của service. Và tìm ra: **thiếu một cột trong database**. Độ tin cậy
> từ ba mươi lên bảy mươi phần trăm. **Không con số nào chứa được thông tin đó** — chỉ
> log có."

*(80 chữ · 32 giây)*

> **Đọc chậm bốn chữ *"chưa xác minh nhân quả"*.** Đó là chỗ chứng minh hệ thống biết
> ranh giới hiểu biết của nó — và gần như không dự án nào dám in câu đó ra màn hình.

---

### Cảnh 7 · 1:50–2:06 · War room — bằng chứng truy vết được

**Màn hình:** F5 `localhost:8501/war_room` → mở phiếu vừa tạo. Chỉ **hai** thao tác,
đừng cuộn lung tung:

1. Chỉ vào mục bằng chứng — có tên metric gốc và con số
2. Bấm **"kiểm chứng PromQL"** → mở tab Prometheus, ra **cùng một con số**

> "Mọi con số trên trang này đều kèm câu truy vấn gốc. Bấm vào là mở thẳng Prometheus —
> ra đúng con số đó. Người trực **không phải tin Agent**, họ kiểm lại được."

*(38 chữ · 16 giây)*

---

### Cảnh 8 · 2:06–2:16 · Cổng chặn — thử ép thi hành

**Màn hình:** Terminal.

```bash
python scripts/duyet.py KAN-xx
```

Kết quả: **bị từ chối**.

> "Em thử ép hệ thống thi hành luôn, không qua ai. **Bị chặn.** Phiếu vẫn đang ở cột
> *chờ phê duyệt* — chưa ai bấm thì không có đường nào đi tiếp."

*(30 chữ · 10 giây)*

> *(Ý này của Long trong bản 21/08 — giữ lại vì nó là cách mạnh nhất để chứng minh cổng
> HITL: cho thấy nó **từ chối** trước khi cho thấy nó cho qua.)*

---

### Cảnh 9 · 2:16–2:30 · Người duyệt — hệ thống sửa thật

**Màn hình:** Jira. Kéo phiếu sang **`Remediating`** bằng tài khoản người. Chờ comment
tự hiện. Rồi mở **History** của phiếu.

> "Giờ một người thật kéo phiếu sang *Remediating*. Cùng một lệnh với lúc nãy — lúc nãy
> bị chặn, giờ qua. Em không sửa dòng code nào giữa hai lần; khác duy nhất là **có người
> bấm nút hay không**.
>
> Mở lịch sử phiếu: **hai cái tên khác nhau**. Agent không sửa được lịch sử này."

*(58 chữ · 14 giây — đọc nhanh)*

> ⚠️ Trên màn hình **không được** xuất hiện chữ `simulated`. Thấy là quên
> `REMEDIATION_REAL=1` trên backend — dừng, sửa, quay lại cảnh này.

---

## PHẦN 3 · GIÁ TRỊ + KẾT QUẢ · 2:30–3:00

### Cảnh 10 · 2:30–2:44 · Agent tự xác nhận đã khỏi

**Màn hình:** Terminal.

```bash
python eval/run_measurements.py payment-load --seconds 45 --concurrency 2 --pause 0.05
python scripts/run_agent.py --once
```

Dòng cần khoanh: `verify service-thanh-toan: không còn tín hiệu sự cố — đã hồi phục`

> "Agent tự đo lại, bằng **đúng những truy vấn đã phát hiện ra sự cố** — nên *đã hồi
> phục* cùng một định nghĩa với *phát hiện*. Trước: không một request nào thành công.
> Sau: tất cả. Tỷ lệ lỗi từ một trăm phần trăm về **không**."

*(48 chữ · 14 giây)*

**Hậu kỳ:** overlay `100% → 0%` thật to, giữ tới hết cảnh.

---

### Cảnh 11 · 2:44–3:00 · Con số đo được

**Màn hình:** bảng, dựng sạch — **không** quay code:

```
Bỏ lọt sự cố          4 / 25          recall 84%
Báo nhầm              5 / 25
Xếp mức độ đúng      17 / 21
Cổng người duyệt     100% không bị vượt qua
Chi phí hạ tầng       0 đồng
```

> "Bọn em đo trên năm mươi tình huống dựng lại từ số đo thật. Bắt được hai mươi mốt trên
> hai mươi lăm — và bọn em **kể tên bốn cái bỏ lọt** trong tài liệu, gồm cả loại mà số đo
> không thể thấy được. Cổng người duyệt: chưa lần nào bị vượt qua. Chạy hết trên hạ tầng
> miễn phí."

*(52 chữ · 16 giây)*

> **Câu *"kể tên bốn cái bỏ lọt"* là câu đáng giá nhất cả video.** Không nhóm nào tự nói
> ra chỗ mình mù. Nó biến một con số bình thường (84%) thành bằng chứng về **phương pháp**
> — và đó là thứ khó bắt chước hơn một con số đẹp.
>
> Số liệu lấy từ [`eval/RESULTS-2026-08-21.md`](../eval/RESULTS-2026-08-21.md) §1. **Kiểm
> lại trước khi quay** — nếu đã đo lại thì con số có thể đổi.

---

# C. Hai shot B-roll — chạy dưới cảnh 1

B-roll **không ăn thêm giây nào**: nó thay phần hình tĩnh của cảnh 1, lời thoại giữ
nguyên.

## Nguyên tắc: **không có màu đỏ nào**

Cảnh 1 là lúc **chưa có sự cố**, và luận điểm của dự án là *"hệ thống cháy mà số đo vẫn
nói ổn"*. Cho màn đỏ vào là kể sai — và minh hoạ đúng câu chuyện *"monitor bắt được sự
cố"* mà cảnh 5 nói thẳng là **không đủ**.

Hai màu lấy từ `ui/theme.py`: xanh `#52B788` (`--ok`), đỏ `#E5484D` (`--p1`). Dùng đúng
token của sản phẩm để cắt sang màn hình thật không bị lệch màu.

## Shot A · 0:00–0:14 · sự bình yên

```
[STYLE]
Extreme close-up, macro, shallow depth of field. A pitch-black bedroom at
night. On a dark wooden bedside table: a smartphone lying face-down, screen
off, completely still. Behind it and far out of focus, a laptop screen glows
faint green, showing only a single perfectly flat horizontal line — no text,
no numbers, unreadable at this distance. Nothing moves. A half-empty glass
of water catches a thin cold rim of moonlight. The room is asleep.

Camera: locked-off macro, almost imperceptible push-in over 14 seconds.
Focus stays on the dark phone in the foreground; the green line stays soft
and out of focus in the background.
Lighting: single soft green wash #52B788 from the out-of-focus laptop, very
low intensity. One thin cold blue moonlight rim from a window behind. Near
black everywhere else.

[AUDIO]
Quiet room tone. A faint air-conditioner hum. A distant single car passing
outside. No phone sound. No music. No alert tone.

[NEGATIVE]
red light, red colour anywhere, alert icons, warning symbols, flashing,
blinking, spiking or falling line graphs, readable text, numbers, letters,
dashboards with labels, sirens, dramatic music, tension score, people, hands,
movement, camera shake
```

## Shot B · 4 giây, đặt ở ĐẦU CẢNH 4 · nghịch lý

```
[STYLE]
Same bedside table, same darkness, identical framing to the previous shot.
The phone screen lights up and the phone buzzes hard against the wood,
rattling once, twice. Behind it, still out of focus, the laptop's green line
stays perfectly flat and perfectly green — completely unchanged. The
contradiction is the point: the phone is screaming, the screen says fine.
Hold on the unchanged green line for the final second, not on the phone.

Camera: locked-off, identical to previous shot. In the last second, focus
racks from the buzzing phone to the flat green line behind it.
Lighting: unchanged soft green #52B788 wash. The phone's own screen light
is cold white and blown out, illegible.

[AUDIO]
One second of silence. Then an aggressive phone vibration rattling against
wood, twice. Then silence again. No music, no alert sting, no sub-bass.

[NEGATIVE]
red light, red colour anywhere, red alerts, alert icons, warning symbols,
spiking graphs, falling line charts, readable text, numbers, sirens,
dramatic music, sub-bass swell, people, faces, hands
```

## Ba lưu ý khi gen

**① `readable text, numbers, letters` là dòng quan trọng nhất trong `[NEGATIVE]`.**
Mọi mô hình gen video đều dựng chữ thành ký tự méo. Video này cắt sang màn hình **thật**
ngay sau đó — chữ méo cạnh chữ thật là lộ ngay.

**② Không để mặt người.** Bỏ người thì mất luôn hai rủi ro: nhân vật khác nhau giữa hai
shot, và tay/mắt bị dựng méo.

**③ Giữ nguyên khung giữa hai shot** (`identical framing`), để cắt liền được. Gen 3–4
lần rồi chọn cặp khớp nhất.

---

# D. Nếu có sự cố lúc quay

| Hiện tượng | Nguyên nhân | Xử |
|---|---|---|
Agent in `"đã có incident đang mở"` | còn phiếu mở — **bẫy 3** | đóng phiếu đó, chạy lại cảnh 6 |
Đề xuất ra `scale_up` thay `rollback` | seed quá 15 phút — **bẫy 5** | `python demo/seed.py`, làm lại từ cảnh 4 |
Màn hình hiện chữ `simulated` | cờ đặt sai chỗ — **bẫy 1** | bật lại backend, làm lại cảnh 9 |
`duyet.py` báo 403 | kéo phiếu bằng account Agent — **bẫy 6** | kéo lại bằng tài khoản người |
PromQL trả `nan` | tải đã tắt quá 1–2 phút | chạy lại tải, quay lại cảnh 5 |
`verify` báo **CHƯA ĐỠ** / **TỆ HƠN** | **không phải hỏng** | đọc to ra — xem dưới |

## Nếu `verify` báo CHƯA ĐỠ hoặc TỆ HƠN

Đó là hai nhánh **có thật** trong code, không phải lỗi:

| Agent nói | Nghĩa |
|---|---|
⚠️ **CHƯA ĐỠ** | *"chẩn đoán ban đầu có thể sai, đừng thi hành lại cùng hành động"* |
🔴 **TỆ HƠN** | mức nặng hơn lúc mở phiếu → *"cần người vào ngay, đừng thi hành thêm"* |

Gặp thì cứ giữ nguyên và đọc to. **Một hệ thống dám nói "tôi có thể đã sai" đáng tin hơn
một hệ thống lúc nào cũng báo thành công** — và câu đó nói ra trong video còn mạnh hơn
một lần chạy suôn sẻ.

---

# E. Ngân sách thời gian — kiểm lại sau khi dựng

| Phần | Cảnh | Giây | BTC yêu cầu |
|---|---|---:|---|
Vấn đề + chân dung | 1, 2, 3 | **40** | 30–45 ✅ |
Demo vận hành | 4–9 | **110** | phần giữa ✅ |
Giá trị + kết quả | 10, 11 | **30** | 30 ✅ |
| | **Tổng** | **180** | ≤ 180 ✅ |

Nếu tràn giờ, cắt theo thứ tự này:

1. cảnh 7 *(war room)* — 16 → 12 giây, bỏ thao tác thứ nhất
2. cảnh 4 *(gây sự cố)* — tua nhanh mạnh hơn
3. cảnh 9 *(người duyệt)* — bỏ phần mở History, chỉ nói

**Không bao giờ cắt:** cảnh 5 *(số đo mù)*, cảnh 8 *(bị chặn)*, cảnh 11 *(con số)*. Ba
cảnh đó là ba luận điểm — mất cái nào là mất một chân.
