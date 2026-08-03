# ─────────────────────────────────────────────────────────────
# Tiffin Wala 🍱
# Ghar Jaisa Khana, Rozana
# ─────────────────────────────────────────────────────────────

A mobile-first Flask web application for managing tiffin subscription bookings.

## 🚀 Quick Start (Local Development)

### 1. Create & activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
# Edit .env with your values
```

### 4. Run the app
```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## 🔐 Admin Panel

URL: http://localhost:5000/admin/login

| Field     | Default Value     |
|-----------|-------------------|
| Username  | `admin`           |
| Password  | `TiffinWala@2024` |

> ⚠️ Change credentials via environment variables before deploying to production.

---

## 📁 Project Structure

```
tiffin-wala/
├── app.py                   # Flask routes, DB, business logic
├── requirements.txt         # Python dependencies
├── Procfile                 # Render/Heroku deployment
├── .env.example             # Environment variable template
├── instance/
│   └── tiffin.db            # SQLite database (auto-created)
├── static/
│   ├── images/
│   │   ├── hero_thali.png   # Hero food photo
│   │   └── qr_code.png      # UPI QR code
│   └── uploads/             # Payment screenshots (auto-created)
└── templates/
    ├── index.html           # Landing page + multi-step wizard
    ├── admin_login.html     # Admin login
    └── admin.html           # Admin dashboard
```

---

## 🌐 Deploy to Render (Free)

1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Connect GitHub repo
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn app:app`
6. Add **Environment Variables** in Render dashboard:
   - `SECRET_KEY` → random string
   - `ADMIN_USERNAME` → your username
   - `ADMIN_PASSWORD` → strong password
7. Click **Deploy**

> 📌 For persistent file uploads on Render, configure an external storage (S3 or Cloudinary) since free tier uses ephemeral storage.

---

## 📱 WhatsApp Integration (Future)

The `send_whatsapp_confirmation()` function in `app.py` contains detailed instructions for integrating:
- **Meta WhatsApp Cloud API** (recommended)
- **Twilio WhatsApp API** (alternative)

Look for the `TODO` comments in `app.py` for the exact integration points.

---

## 🎨 Design System

| Color          | Hex       | Usage                          |
|----------------|-----------|--------------------------------|
| Dark Forest Green | `#1a4731` | Headers, buttons, accents    |
| Vibrant Orange | `#f5840a` | Highlights, CTAs, prices      |
| Light Cream    | `#fef9ef` | Page backgrounds               |

Slogans used throughout the app:
- *"Ghar jaisa swad, har roz!"*
- *"Ghar Jaisa Khana, Har Roz, Har Waqt!"*
- *"Swad bhi, Sehat bhi aur Pyaar bhi."*
- *"GHAR JAISA KHANA, ROZANA"*

---

## 💡 Pricing

| Plan      | Regular Thali | Premium Thali |
|-----------|---------------|---------------|
| Monthly   | ₹50 (trial)   | ₹120          |
| One-Time  | ₹80           | ₹150          |

---

*Made with ❤️ — Tiffin Wala, Ghar Jaisa Khana, Rozana*
