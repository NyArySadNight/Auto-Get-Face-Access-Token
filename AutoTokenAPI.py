#!/usr/bin/env python3
"""
FB Get Token - Công cụ lấy Page Access Token (dài hạn) qua đúng luồng OAuth
chính thức của Facebook (Facebook Login for Business).

KHÔNG đăng nhập giả lập, KHÔNG lưu mật khẩu Facebook của bạn ở đâu cả.
Script chỉ mở trình duyệt để BẠN tự đăng nhập & bấm "Cho phép" trên chính
trang facebook.com, sau đó Facebook trả về 1 mã (code) tới máy bạn qua
localhost, script dùng mã đó đổi lấy access token qua Graph API.

Chuẩn bị trước (làm 1 lần trên developers.facebook.com):
    1. Tạo 1 Facebook App -> lấy App ID + App Secret.
    2. Thêm sản phẩm "Facebook Login" cho App đó.
    3. Vào Facebook Login > Settings > "Valid OAuth Redirect URIs", thêm:
           http://localhost:8765/
    4. Bạn phải là Admin của Fanpage muốn đăng bài.

Cài đặt (1 lần):
    pip install requests

Chạy:
    python3 fb_get_token.py

Kết quả: chọn Page trong danh sách -> script tự ghi page_id + access_token
(Page Token dài hạn, thường không tự hết hạn) vào file
fb_autopost_config.json để AutoDangBaiFace.py dùng luôn, không cần nhập tay.
"""

import http.server
import json
import os
import threading
import urllib.parse
import webbrowser

import requests
import tkinter as tk
from tkinter import messagebox, ttk

GRAPH_API_VERSION = "v19.0"
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"
# Quyền tối thiểu để lấy danh sách Page + đăng bài (text/ảnh/video):
SCOPES = "pages_show_list,pages_read_engagement,pages_manage_posts"

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_autopost_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data):
    current = load_config()
    current.update(data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)


class _OAuthCaptureHandler(http.server.BaseHTTPRequestHandler):
    """Handler tạm để bắt tham số ?code=... mà Facebook redirect về."""

    captured_code = None
    captured_error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if "code" in qs:
            _OAuthCaptureHandler.captured_code = qs["code"][0]
            body = "<h2>Đã nhận quyền thành công.</h2><p>Bạn có thể đóng tab này và quay lại ứng dụng.</p>"
        elif "error" in qs:
            _OAuthCaptureHandler.captured_error = qs.get("error_description", qs.get("error"))[0]
            body = f"<h2>Đã huỷ hoặc lỗi cấp quyền.</h2><p>{_OAuthCaptureHandler.captured_error}</p>"
        else:
            body = "<h2>Đang chờ...</h2>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # im lặng, không in log HTTP ra console


class FBGetTokenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FB Get Token - Lấy Page Access Token")
        self.root.geometry("560x520")

        self.config_data = load_config()
        self.pages = []  # list các dict {id, name, access_token}

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}

        frm = ttk.Frame(self.root)
        frm.pack(fill="x", **pad)

        ttk.Label(frm, text="App ID:").grid(row=0, column=0, sticky="w")
        self.app_id_var = tk.StringVar(value=self.config_data.get("fb_app_id", ""))
        ttk.Entry(frm, textvariable=self.app_id_var, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="App Secret:").grid(row=1, column=0, sticky="w")
        self.app_secret_var = tk.StringVar(value=self.config_data.get("fb_app_secret", ""))
        ttk.Entry(frm, textvariable=self.app_secret_var, width=40, show="*").grid(row=1, column=1, sticky="w")

        ttk.Label(
            frm,
            text=f"Redirect URI cần khai báo trong App:\n{REDIRECT_URI}",
            foreground="gray",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Button(self.root, text="① Đăng nhập Facebook & lấy quyền", command=self.start_oauth).pack(
            pady=10
        )

        ttk.Label(self.root, text="② Chọn Page muốn dùng để đăng bài:").pack(anchor="w", padx=10)
        self.pages_listbox = tk.Listbox(self.root, height=8)
        self.pages_listbox.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Button(
            self.root, text="③ Lưu Page đã chọn vào fb_autopost_config.json", command=self.save_selected_page
        ).pack(pady=5)

        ttk.Label(self.root, text="Nhật ký:").pack(anchor="w", padx=10)
        self.log_box = tk.Text(self.root, height=10, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ---------- Bước 1: OAuth ----------

    def start_oauth(self):
        app_id = self.app_id_var.get().strip()
        app_secret = self.app_secret_var.get().strip()
        if not app_id or not app_secret:
            messagebox.showerror("Lỗi", "Nhập App ID và App Secret trước.")
            return

        save_config({"fb_app_id": app_id, "fb_app_secret": app_secret})

        _OAuthCaptureHandler.captured_code = None
        _OAuthCaptureHandler.captured_error = None

        params = {
            "client_id": app_id,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "response_type": "code",
        }
        auth_url = "https://www.facebook.com/" + GRAPH_API_VERSION + "/dialog/oauth?" + urllib.parse.urlencode(
            params
        )

        self.log("Đang mở trình duyệt để bạn đăng nhập & cấp quyền...")
        webbrowser.open(auth_url)

        threading.Thread(target=self._run_local_server, args=(app_id, app_secret), daemon=True).start()

    def _run_local_server(self, app_id, app_secret):
        server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _OAuthCaptureHandler)
        server.timeout = 120  # chờ tối đa 2 phút cho 1 request
        # handle_request() xử lý từng request 1, chờ tới khi có code hoặc error hoặc hết hạn
        while _OAuthCaptureHandler.captured_code is None and _OAuthCaptureHandler.captured_error is None:
            server.handle_request()
            if _OAuthCaptureHandler.captured_code is None and _OAuthCaptureHandler.captured_error is None:
                # handle_request() có thể trả về do timeout mà chưa có gì -> dừng luôn để tránh treo vô hạn
                break
        server.server_close()

        if _OAuthCaptureHandler.captured_error:
            self.root.after(0, lambda: self.log(f"❌ Facebook trả lỗi: {_OAuthCaptureHandler.captured_error}"))
            return
        if not _OAuthCaptureHandler.captured_code:
            self.root.after(0, lambda: self.log("⚠️ Hết thời gian chờ, chưa nhận được quyền. Thử lại bước ①."))
            return

        self.root.after(0, lambda: self.log("✅ Đã nhận quyền, đang đổi lấy token..."))
        self._exchange_and_load_pages(app_id, app_secret, _OAuthCaptureHandler.captured_code)

    def _exchange_and_load_pages(self, app_id, app_secret, code):
        try:
            # Bước A: code -> short-lived user access token
            r1 = requests.get(
                f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token",
                params={
                    "client_id": app_id,
                    "redirect_uri": REDIRECT_URI,
                    "client_secret": app_secret,
                    "code": code,
                },
                timeout=30,
            )
            r1_data = r1.json()
            if "access_token" not in r1_data:
                self.root.after(0, lambda: self.log(f"❌ Lỗi lấy token: {r1_data}"))
                return
            short_token = r1_data["access_token"]

            # Bước B: short-lived -> long-lived user access token (~60 ngày)
            r2 = requests.get(
                f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "fb_exchange_token": short_token,
                },
                timeout=30,
            )
            r2_data = r2.json()
            long_user_token = r2_data.get("access_token", short_token)

            # Bước C: lấy danh sách Page + Page Access Token (từ long-lived user token
            # thường KHÔNG tự hết hạn)
            r3 = requests.get(
                f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts",
                params={"access_token": long_user_token},
                timeout=30,
            )
            r3_data = r3.json()
            pages = r3_data.get("data", [])
            if not pages:
                self.root.after(
                    0,
                    lambda: self.log(
                        "⚠️ Không tìm thấy Page nào. Kiểm tra bạn có phải Admin của Page, "
                        "và đã chấp nhận đủ quyền pages_show_list."
                    ),
                )
                return

            self.pages = pages
            self.root.after(0, self._fill_pages_listbox)
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Lỗi kết nối: {e}"))

    def _fill_pages_listbox(self):
        self.pages_listbox.delete(0, "end")
        for p in self.pages:
            self.pages_listbox.insert("end", f"{p.get('name')}  (ID: {p.get('id')})")
        self.log(f"✅ Tìm thấy {len(self.pages)} Page. Chọn 1 Page rồi bấm bước ③.")

    # ---------- Bước 3: lưu ----------

    def save_selected_page(self):
        sel = self.pages_listbox.curselection()
        if not sel or not self.pages:
            messagebox.showerror("Lỗi", "Chọn 1 Page trong danh sách trước.")
            return
        page = self.pages[sel[0]]
        save_config({"page_id": page.get("id"), "access_token": page.get("access_token")})
        self.log(f"💾 Đã lưu Page \"{page.get('name')}\" vào {os.path.basename(CONFIG_PATH)}.")
        self.log("Giờ bạn có thể mở AutoDangBaiFace.py, Page ID và Access Token sẽ tự điền sẵn.")


def main():
    root = tk.Tk()
    app = FBGetTokenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
