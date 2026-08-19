# Auto-Get-Face-Access-Token

Công cụ desktop (tkinter) lấy **Page Access Token dài hạn** của Facebook
Fanpage qua đúng luồng OAuth chính thức (Facebook Login for Business) —
không đăng nhập giả lập, không đụng tới mật khẩu Facebook của bạn.

Đây là **công cụ chuẩn bị** cho [Auto-Face-API](../Auto-Face-API) (bộ đăng
bài tự động) — chạy công cụ này trước để lấy Page ID + Access Token, ghi
thẳng vào file cấu hình dùng chung `fb_autopost_config.json`.

## Cách hoạt động

1. Bạn tự đăng nhập & bấm "Cho phép" trên chính trang facebook.com (mở qua
   trình duyệt mặc định của máy).
2. Facebook redirect về `http://localhost:8765/` kèm mã tạm (`code`) — script
   dựng 1 local server tạm để bắt mã này.
3. Script đổi mã đó lấy **short-lived user token** → đổi tiếp thành
   **long-lived user token** (~60 ngày) → dùng token đó lấy
   **Page Access Token** (thường không tự hết hạn) cho từng Page bạn quản
   trị.
4. Bạn chọn Page cần dùng, script tự ghi `page_id` + `access_token` vào
   `fb_autopost_config.json`.

## Chuẩn bị trước (làm 1 lần trên developers.facebook.com)

1. Tạo 1 Facebook App → lấy **App ID** + **App Secret**.
2. Thêm sản phẩm **Facebook Login** cho App đó.
3. Vào **Facebook Login → Settings → Valid OAuth Redirect URIs**, thêm:
   ```
   http://localhost:8765/
   ```
4. Bạn phải là **Admin** của Fanpage muốn đăng bài.
5. App cần các quyền (scope): `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts` — nếu App đang ở chế độ Development, tài khoản dùng
   để test phải được thêm vào danh sách Tester/Admin của App.

## Yêu cầu

- Python 3.9+ (tkinter thường có sẵn cùng Python)
- Thư viện:

```bash
pip install requests
```

## Chạy chương trình

```bash
python3 AutoTokenAPI.py
```

Các bước trong app:

1. Nhập **App ID** và **App Secret**, bấm **① Đăng nhập Facebook & lấy
   quyền** — trình duyệt sẽ mở ra để bạn đăng nhập/cấp quyền.
2. Sau khi cấp quyền xong (tự động quay lại app), chọn Page cần dùng ở danh
   sách **② Chọn Page**.
3. Bấm **③ Lưu Page đã chọn** — `page_id` và `access_token` được ghi vào
   `fb_autopost_config.json`, sẵn sàng để `AutoFixFace.py` (repo
   Auto-Face-API) dùng ngay, không cần nhập tay.

## Bảo mật

- **App Secret** và **Access Token** được lưu ở dạng plain text trong
  `fb_autopost_config.json` cùng thư mục chạy script — **không commit file
  này lên Git**, không chia sẻ cho người khác. Nên thêm vào `.gitignore`:
  ```
  fb_autopost_config.json
  ```
- Long-lived Page Token lấy từ long-lived user token thường **không tự hết
  hạn**, nhưng sẽ bị vô hiệu nếu bạn đổi mật khẩu Facebook, thu hồi quyền
  App, hoặc Facebook phát hiện hoạt động bất thường.
- Nếu Page Token vô tình bị lộ, vào **Facebook → Cài đặt → Bảo mật → Ứng
  dụng và trang web** để thu hồi quyền truy cập của App ngay lập tức.

## Lưu ý

- README bản gốc ghi lệnh chạy là `python3 fb_get_token.py` — tên file thật
  trong repo là **`AutoTokenAPI.py`**, README này đã sửa lại đúng lệnh chạy.
