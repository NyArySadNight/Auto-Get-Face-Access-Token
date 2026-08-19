# Auto-Get-Face-Access-Token

A desktop tool (tkinter) that obtains a **long-lived Page Access Token** for
a Facebook Fanpage through the official OAuth flow (Facebook Login for
Business) — no fake browser login, and it never touches your Facebook
password.

This is the **companion setup tool** for [Auto-Face-API](../Auto-Face-API)
(the auto-poster) — run this first to get your Page ID + Access Token,
written directly into the shared config file `fb_autopost_config.json`.

## How it works

1. You log in and click "Allow" yourself, on the real facebook.com (opened
   in your machine's default browser).
2. Facebook redirects to `http://localhost:8765/` with a temporary code —
   the script spins up a temporary local server just to catch this code.
3. The script exchanges that code for a **short-lived user token** → then
   exchanges that for a **long-lived user token** (~60 days) → uses that to
   fetch a **Page Access Token** (usually doesn't expire) for each Page you
   manage.
4. You pick the Page you want to use, and the script writes `page_id` +
   `access_token` into `fb_autopost_config.json`.

## Setup (one-time, on developers.facebook.com)

1. Create a Facebook App → get its **App ID** + **App Secret**.
2. Add the **Facebook Login** product to that App.
3. Go to **Facebook Login → Settings → Valid OAuth Redirect URIs**, and add:
   ```
   http://localhost:8765/
   ```
4. You must be an **Admin** of the Fanpage you want to post to.
5. The App needs these scopes: `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts` — if the App is still in Development mode, the test
   account must be added to the App's Tester/Admin list.

## Requirements

- Python 3.9+ (tkinter usually ships with Python)
- Dependency:

```bash
pip install requests
```

## Running

```bash
python3 AutoTokenAPI.py
```

Steps inside the app:

1. Enter your **App ID** and **App Secret**, click **① Log in to Facebook &
   grant access** — your browser opens for login/consent.
2. Once permission is granted (the app picks it up automatically), pick the
   Page you want under **② Select Page**.
3. Click **③ Save selected Page** — `page_id` and `access_token` get written
   to `fb_autopost_config.json`, ready for `AutoFixFace.py` (in the
   Auto-Face-API repo) to use right away, no manual entry needed.

## Security

- **App Secret** and **Access Token** are stored as plain text in
  `fb_autopost_config.json`, in the script's directory — **never commit this
  file to Git**, and don't share it. Add it to `.gitignore`:
  ```
  fb_autopost_config.json
  ```
- A long-lived Page Token derived from a long-lived user token usually
  **doesn't expire on its own**, but will be invalidated if you change your
  Facebook password, revoke the App's permission, or Facebook flags
  suspicious activity.
- If a Page Token ever leaks, revoke App access immediately at **Facebook →
  Settings → Security → Apps and Websites**.

## Notes

- The original README listed the run command as `python3 fb_get_token.py`
  — the actual filename in this repo is **`AutoTokenAPI.py`**; this README
  corrects that.
