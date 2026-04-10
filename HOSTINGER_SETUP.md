# Hostinger Deployment Fix — FORM.AI Newsletter

## Files to upload/replace

| File | Where | What it does |
|------|-------|-------------|
| `app.py` | project root | 50MB limit, error handlers |
| `passenger_wsgi.py` | project root | Hostinger WSGI entry point |
| `.htaccess` | project root | Increase upload limit |
| `routes/newsletter.py` | routes/ folder | Strips base64 before save |
| `templates/newsletter/edit.html` | templates/newsletter/ | Better save error messages |

---

## Step 1 — Fix passenger_wsgi.py virtualenv path

Open `passenger_wsgi.py` and check the virtualenv name matches YOUR Hostinger folder.

In Hostinger File Manager, go to:
```
/home/u123456789/virtualenv/
```
You'll see a folder — **copy that exact name** and update line in passenger_wsgi.py:

```python
os.path.join(_HOME, 'virtualenv', 'YOUR_FOLDER_NAME', '3.11', 'bin', 'python'),
```

Your folder is probably named the same as your domain or project (e.g. `fc2`, `formcraft`, etc.)

---

## Step 2 — Rename htaccess

The file must be named exactly `.htaccess` (with the dot at the start).

In Hostinger File Manager it may show as `htaccess` — rename it to `.htaccess`.

---

## Step 3 — Set HTTPS cookie in .env

Add this to your `.env` file on Hostinger:
```
HTTPS=true
```

---

## Step 4 — Why "Save failed" happens

**Root cause:** You uploaded images from your computer.
Uploaded images become base64 strings (2–20MB each).
Hostinger Nginx has a **1MB request limit** → HTTP 413 → "Save failed".

**Fix (already in newsletter.py):** Base64 images are now stripped before saving.

**For images in newsletters:** Use external URLs instead of uploading:
- Go to [unsplash.com](https://unsplash.com) → right-click any image → "Copy image address"
- Paste that URL into the Image block in the newsletter editor
- External URLs work perfectly in both the editor and email sends ✅

---

## Step 5 — Restart after uploading

In Hostinger hPanel:
1. Go to **Websites** → your site → **Python**
2. Click **Restart** to reload the application

OR create/touch the restart file:
```
touch /home/u123456789/YOUR_DOMAIN/tmp/restart.txt
```

---

## Troubleshooting

### Still seeing "Save failed"?
Check Hostinger error logs: hPanel → Websites → Logs → Error log

### App not loading at all?
- Verify `passenger_wsgi.py` virtualenv path is correct
- Check all packages installed: `pip install -r requirements.txt`

### Session/login issues?
Make sure `SECRET_KEY` in `.env` is a long random string and consistent.
