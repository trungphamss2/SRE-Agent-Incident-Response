# Bàn giao dựng video — cho Long

Kế hoạch đầy đủ ở [`video-plan.md`](video-plan.md). File này chỉ trả lời **ba câu**:
Long dán gì vào Flow · ai quay phần nào · lắp lại thế nào.

## Chia việc

| Phần | Ai | Ghi chú |
|---|---|---|
**2 shot B-roll** *(18 giây)* | **Long** — gen bằng Flow | prompt ở §1 |
**9 cảnh màn hình** *(162 giây)* | **Đức** — quay màn hình | Đức có stack chạy được |
**Overlay + lồng tiếng + dựng** | **Long** | danh sách ở §3 |

> ⚠️ **Flow không gen được phần sản phẩm.** 162 giây kia là màn hình thật: terminal,
> war room, Jira. Đó là điểm mạnh nhất của dự án — mọi con số đều thật, kiểm lại được.
> Gen phần đó bằng AI là **tự phá** thứ duy nhất khó bắt chước.
>
> Và chữ do AI gen luôn ra ký tự méo. Cắt cạnh màn hình thật là lộ ngay.

---

# §1. Hai prompt dán vào Flow

## ⚠️ Đọc trước: giới hạn độ dài clip

Flow gen mỗi lần khoảng **8 giây**. Nên **shot A không gen một lần được** nếu muốn 14
giây. Hai cách:

- **Cách nên làm:** gen shot A **8 giây**, rồi 6 giây còn lại của cảnh 1 dùng **màn hình
  trạng thái thật** *(Đức quay)*. Vào sản phẩm thật sớm hơn — tốt hơn cho phần chấm.
- Cách hai: gen 2 clip cùng khung rồi cắt nối. Tốn công, dễ lệch màu.

Nếu Flow bản Long dùng cho phép dài hơn 8 giây thì cứ gen 14 giây một lần.

## Cài đặt Flow

```
Tỷ lệ khung   16:9
Độ dài        8 giây (shot A) · 4 giây (shot B)
Âm thanh      bật, theo khối [AUDIO]
Gen           3–4 lần mỗi shot, chọn cặp KHỚP KHUNG nhất
```

Hai màu lấy từ `ui/theme.py` — `#52B788` là `--ok`, `#E5484D` là `--p1`. Dùng đúng
token của sản phẩm để cắt sang màn hình thật không lệch màu.

---

## SHOT A · 8 giây · đặt ở 0:00 · *sự bình yên*

```
[STYLE]
Extreme close-up, macro, shallow depth of field. A pitch-black bedroom at
night. On a dark wooden bedside table: a smartphone lying face-down, screen
off, completely still. Behind it and far out of focus, a laptop screen glows
faint green, showing only a single perfectly flat horizontal line — no text,
no numbers, unreadable at this distance. Nothing moves. A half-empty glass
of water catches a thin cold rim of moonlight. The room is asleep.

Camera: locked-off macro, almost imperceptible push-in. Focus stays on the
dark phone in the foreground; the green line stays soft and out of focus in
the background.
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

---

## SHOT B · 4 giây · đặt ở **đầu cảnh 4 (0:40)** · *nghịch lý*

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
Mọi mô hình gen video dựng chữ thành ký tự méo. Video này cắt sang màn hình **thật**
ngay sau đó.

**② Không để mặt người.** Bỏ người thì mất luôn hai rủi ro: nhân vật khác nhau giữa hai
shot, và tay/mắt bị dựng méo. *(Prompt gốc có `[CHARACTER]` chưa định nghĩa — đã bỏ.)*

**③ Giữ nguyên khung giữa hai shot** — `identical framing` trong prompt B. Đây là chỗ
làm nên hiệu quả: người xem thấy **cái gì đã đổi, cái gì không đổi**. Gen tới khi được
một cặp khớp.

**④ Không có màu đỏ nào.** Cảnh 1 là lúc **chưa có sự cố**, và luận điểm của dự án là
*"hệ thống cháy mà số đo vẫn nói ổn"*. Màn đỏ minh hoạ đúng câu chuyện *"monitor bắt
được sự cố"* — mà cảnh 5 nói thẳng là **không đủ**. Có đỏ là video tự mâu thuẫn.

---

# §2. Chín cảnh Đức quay — Long nhận file gì

Đức quay theo `video-plan.md` mục B, xuất **9 file rời**, đặt tên đúng thứ tự:

```
02-trang-trang-thai.mov      6s    trang xanh, không rê chuột
03-so-do-agent.mov          14s    sơ đồ 4 khối (hoặc Long tự dựng, xem dưới)
04-gay-su-co.mov            16s    terminal, đã tua nhanh ×6
05-so-do-mu.mov             22s    terminal, PromQL ra p95 = 0,048
06-agent-vao-cuoc.mov       32s    terminal, 2 dòng log cần khoanh
07-war-room.mov             16s    war room + bấm kiểm chứng PromQL
08-bi-chan.mov              10s    terminal, duyet.py bị từ chối
09-nguoi-duyet.mov          14s    Jira: kéo phiếu + mở History
10-tu-xac-nhan.mov          14s    terminal, verify → đã hồi phục
```

**Cảnh 3 (sơ đồ 4 khối)** — Long tự dựng bằng công cụ dựng cũng được, không cần quay.
Bốn khối `PHÁT HIỆN → CHẨN ĐOÁN → ĐỀ XUẤT → CHỜ DUYỆT`, khối cuối tô khác màu. Có thể
lấy ý từ `docs/architecture_diagram.md`.

**Yêu cầu quay:**

| | |
|---|---|
Độ phân giải | 1920×1080 trở lên |
Chữ terminal | ≥ 16pt — người xem trên điện thoại phải đọc được |
Con trỏ | đứng yên khi không cần thao tác |
Thông báo | tắt hết *(Do Not Disturb)* |
Thanh Dock, bookmark | ẩn / dọn gọn |

---

# §3. Overlay Long cần làm

| Cảnh | Overlay | Giữ bao lâu |
|---|---|---|
④ | khoanh đỏ dòng `{"500": …, "502": …}` + chữ **`0 request thành công`** | 2s |
⑤ | **ba ô cạnh nhau:** `Lỗi 99%` *(đỏ)* · `p95 0,048s` *(xanh)* · `Pool 0%` *(xanh)* | tới hết cảnh |
⑤ | **giữ thêm 3 giây SAU khi hết lời thoại — IM LẶNG, không nhạc** | 3s |
⑥ | khoanh đỏ dòng `tin cậy 30% — Chưa đủ bằng chứng…` **cả câu** | 4s |
⑥ | khoanh đỏ dòng `log đổi kết luận (30% → 70%) — thiếu cột idempotency_key` | 4s |
⑨ | khoanh **hai cái tên khác nhau** trong History của phiếu Jira | 3s |
⑩ | **`100% → 0%`** chữ thật to | tới hết cảnh |
⑪ | **bảng số** — xem dưới | 16s |

## Bảng số cảnh ⑪ — dựng sạch, đừng quay code

```
Bỏ lọt sự cố          4 / 25          recall 84%
Báo nhầm              5 / 25
Xếp mức độ đúng      17 / 21
Cổng người duyệt     100% không bị vượt qua
Chi phí hạ tầng       0 đồng
```

> ⚠️ **Kiểm lại số trước khi dựng.** Nguồn: `eval/RESULTS-2026-08-21.md` §1. Nếu Đức đo
> lại thì con số có thể đổi — hỏi Đức một câu trước khi render.

## Ba giây im lặng ở cảnh ⑤ — đừng cắt

Cảnh 5 là lý do sản phẩm tồn tại. Nếu người xem không *thấm* nghịch lý *"lỗi 99% mà
p95 nhanh hơn bình thường"*, thì cảnh 6 chỉ còn là *"AI đọc log"* — nghe giống trăm dự
án khác, và mọi thứ sau đó mất trọng lượng.

**Ba giây im lặng làm con số nặng hơn ba câu giải thích.** Đừng lấp bằng nhạc.

---

# §4. Lắp lại — dòng thời gian

```
0:00 ─ 0:08   SHOT A (Flow)              ┐
0:08 ─ 0:14   02-trang-trang-thai.mov    ┘ lời thoại cảnh 1 chạy xuyên cả 14 giây
0:14 ─ 0:26   02-trang-trang-thai.mov      cảnh 2
0:26 ─ 0:40   03-so-do-agent               cảnh 3 — chân dung Agent
0:40 ─ 0:44   SHOT B (Flow)              ┐
0:44 ─ 0:56   04-gay-su-co.mov           ┘ cảnh 4
0:56 ─ 1:18   05-so-do-mu.mov              cảnh 5  ⚠️ KHÔNG CẮT
1:18 ─ 1:50   06-agent-vao-cuoc.mov        cảnh 6 — dài nhất
1:50 ─ 2:06   07-war-room.mov              cảnh 7
2:06 ─ 2:16   08-bi-chan.mov               cảnh 8  ⚠️ KHÔNG CẮT
2:16 ─ 2:30   09-nguoi-duyet.mov           cảnh 9
2:30 ─ 2:44   10-tu-xac-nhan.mov           cảnh 10
2:44 ─ 3:00   bảng số (Long dựng)          cảnh 11 ⚠️ KHÔNG CẮT
```

**Lời thoại đầy đủ 11 cảnh ở `video-plan.md` mục B** — đã đếm chữ theo nhịp 150
chữ/phút. **Đừng thêm chữ**, thêm là tràn giờ.

Tổng: **414 chữ · 180 giây · 138 chữ/phút**.

## Nếu tràn giờ, cắt theo thứ tự

1. cảnh ⑦ *(war room)* — 16 → 12 giây, bỏ thao tác thứ nhất
2. cảnh ④ *(gây sự cố)* — tua nhanh mạnh hơn
3. cảnh ⑨ — bỏ phần mở History, chỉ nói

**Không bao giờ cắt:** ⑤ *(số đo mù)* · ⑧ *(bị chặn)* · ⑪ *(con số)*. Ba cảnh đó là ba
luận điểm — mất cái nào là mất một chân.

---

# §5. Nhạc và tiếng

**Không nhạc nền xuyên video.** Ba chỗ duy nhất nên có tiếng:

| Chỗ | Tiếng |
|---|---|
Shot A | room tone + điều hoà, rất nhỏ |
Shot B | **một** tiếng rung điện thoại, rồi im |
Cảnh ⑤, 3 giây cuối | **im lặng hoàn toàn** |

Lý do: video này bán **tính đáng tin**, không bán cảm xúc. Nhạc kịch tính chồng lên số
đo thật làm người xem nghi ngờ số đo. Giọng đọc rõ + im lặng đúng chỗ mạnh hơn.

---

# §6. Trước khi render — kiểm 6 điều

- [ ] Tổng **≤ 3:00**
- [ ] Không có chữ AI-gen nào lọt vào khung *(ký tự méo)*
- [ ] Không có **màu đỏ** nào trong hai shot Flow
- [ ] Màn hình **không hiện chữ `simulated`** ở cảnh ⑨ — thấy là phải quay lại cảnh đó
- [ ] Bảng số cảnh ⑪ khớp `eval/RESULTS-2026-08-21.md`
- [ ] Ba giây im lặng ở cảnh ⑤ còn nguyên
