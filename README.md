# AppsFlyer Bypass Tool 🚀
## Render Pe Deploy Karne Ke Steps

---

### Step 1 — GitHub Pe Upload Karo

1. GitHub.com pe naya **free account** banao (agar nahi hai)
2. **New Repository** banao — naam: `af-bypass-tool`
3. Yeh saari files upload karo:
   ```
   server.py
   requirements.txt
   render.yaml
   templates/
     admin.html
     user.html
   ```

---

### Step 2 — Render Pe Deploy Karo

1. **render.com** pe jaao → Free account banao
2. **New +** → **Web Service** click karo
3. **Connect GitHub** → Apna `af-bypass-tool` repo select karo
4. Yeh settings dalo:
   ```
   Name:          af-bypass-tool
   Environment:   Python
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
5. **Create Web Service** click karo
6. 2-3 minute wait karo → **Live URL** mil jayegi!

   Example: `https://af-bypass-tool.onrender.com`

---

### Step 3 — Access Karo

| Page | URL |
|------|-----|
| User Panel | `https://your-app.onrender.com/` |
| Admin Panel | `https://your-app.onrender.com/admin` |

**Default Admin Password:** `admin123`
> ⚠️ Login karke turant Settings mein password change karo!

---

### Important Note — Render Free Tier

```
Free tier pe server 15 min inactivity ke baad "sleep" ho jaata hai.
Pehli request thodi slow hogi (cold start ~30 sec).
Production use ke liye Render ka $7/month plan lo.
```

---

### Files Structure

```
af-bypass-tool/
├── server.py           ← FastAPI backend
├── requirements.txt    ← Python dependencies
├── render.yaml         ← Render config
└── templates/
    ├── admin.html      ← Admin panel (dark theme)
    └── user.html       ← User panel (light theme)
```

### Data Storage

```
/tmp/af_data/
├── games.json      ← Games + Tasks
├── logs.json       ← Event logs
└── settings.json   ← App settings
```

> Note: Render free tier pe /tmp data kabhi kabhi reset ho sakta hai.
> Permanent storage ke liye PostgreSQL ya MongoDB Atlas add karo.

---

### Admin Features

- Games add/edit/delete/enable/disable
- Tasks manage karo (event, reward, daily limit)
- Dashboard — stats, top games, recent logs
- Rate limiting per GAID
- Maintenance mode
- Password change

### User Flow

1. GAID + AppsFlyer ID daalo
2. Game select karo
3. Task select karo
4. Bypass button dabao ✅
