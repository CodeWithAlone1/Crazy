from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, os, httpx, hashlib, secrets
from datetime import datetime, date
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AppsFlyer Bypass Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Data Directory (Render ke liye /tmp) ─────────────────────────────────────
DATA_DIR      = Path("/tmp/af_data")
CONFIG_FILE   = DATA_DIR / "games.json"
LOGS_FILE     = DATA_DIR / "logs.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_json(path, default):
    if not Path(path).exists():
        save_json(path, default)
        return default
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def load_config():
    return load_json(CONFIG_FILE, {"games": []})

def load_logs():
    return load_json(LOGS_FILE, {"events": []})

def load_settings():
    return load_json(SETTINGS_FILE, {
        "admin_password": hashlib.sha256(b"admin123").hexdigest(),
        "app_name": "AF Bypass Tool",
        "maintenance": False,
        "rate_limit": 10,
        "postback_url": "",
        "allow_registration": True
    })

def add_log(game_name, task_label, user_id, gaid, status, response_text=""):
    logs = load_logs()
    logs["events"].insert(0, {
        "id":        secrets.token_hex(4),
        "timestamp": datetime.now().isoformat(),
        "date":      date.today().isoformat(),
        "game":      game_name,
        "task":      task_label,
        "user_id":   user_id,
        "gaid":      (gaid[:8] + "****") if gaid else "",
        "status":    status,
        "response":  response_text[:200]
    })
    logs["events"] = logs["events"][:500]
    save_json(LOGS_FILE, logs)

def check_rate_limit(gaid: str):
    settings = load_settings()
    limit  = settings.get("rate_limit", 10)
    logs   = load_logs()
    today  = date.today().isoformat()
    count  = sum(
        1 for e in logs["events"]
        if e.get("date") == today
        and e.get("gaid", "").startswith(gaid[:8])
        and e.get("status") == "success"
    )
    return count < limit

# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    password: str

class GameModel(BaseModel):
    name:     str
    app_id:   str
    dev_key:  str
    platform: str  = "android"
    icon:     str  = "🎮"
    enabled:  bool = True

class TaskModel(BaseModel):
    label:       str
    event_name:  str
    event_value: dict = {}
    reward:      int  = 0
    daily_limit: int  = 5
    enabled:     bool = True

class BypassRequest(BaseModel):
    game_id: str
    task_id: str
    gaid:    str
    af_id:   str
    user_id: Optional[str] = ""
    ip:      Optional[str] = ""

class SettingsUpdate(BaseModel):
    app_name:          Optional[str]  = None
    maintenance:       Optional[bool] = None
    rate_limit:        Optional[int]  = None
    postback_url:      Optional[str]  = None
    allow_registration:Optional[bool] = None
    new_password:      Optional[str]  = None
    current_password:  Optional[str]  = None

# ── Sessions ──────────────────────────────────────────────────────────────────
sessions: set = set()

def verify_admin(request: Request):
    token = request.headers.get("X-Admin-Token", "")
    if token not in sessions:
        raise HTTPException(401, "Unauthorized — pehle login karo")
    return True

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/admin/login")
async def admin_login(req: LoginRequest):
    settings = load_settings()
    hashed   = hashlib.sha256(req.password.encode()).hexdigest()
    if hashed != settings["admin_password"]:
        raise HTTPException(401, "Password galat hai")
    token = secrets.token_hex(32)
    sessions.add(token)
    return {"token": token, "app_name": settings.get("app_name", "AF Bypass Tool")}

@app.post("/api/admin/logout")
async def admin_logout(request: Request):
    token = request.headers.get("X-Admin-Token", "")
    sessions.discard(token)
    return {"ok": True}

# ── Games (Admin) ─────────────────────────────────────────────────────────────
@app.get("/api/admin/games")
async def get_games(auth=Depends(verify_admin)):
    return load_config()

@app.post("/api/admin/games")
async def add_game(game: GameModel, auth=Depends(verify_admin)):
    cfg    = load_config()
    new_id = secrets.token_hex(4)
    cfg["games"].append({"id": new_id, **game.dict(), "tasks": []})
    save_json(CONFIG_FILE, cfg)
    return {"ok": True, "id": new_id}

@app.put("/api/admin/games/{game_id}")
async def update_game(game_id: str, game: GameModel, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            saved_tasks = g.get("tasks", [])
            g.update(game.dict())
            g["tasks"] = saved_tasks
            save_json(CONFIG_FILE, cfg)
            return {"ok": True}
    raise HTTPException(404, "Game nahi mila")

@app.delete("/api/admin/games/{game_id}")
async def delete_game(game_id: str, auth=Depends(verify_admin)):
    cfg = load_config()
    cfg["games"] = [g for g in cfg["games"] if g["id"] != game_id]
    save_json(CONFIG_FILE, cfg)
    return {"ok": True}

@app.patch("/api/admin/games/{game_id}/toggle")
async def toggle_game(game_id: str, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            g["enabled"] = not g.get("enabled", True)
            save_json(CONFIG_FILE, cfg)
            return {"ok": True, "enabled": g["enabled"]}
    raise HTTPException(404, "Game nahi mila")

# ── Tasks (Admin) ─────────────────────────────────────────────────────────────
@app.post("/api/admin/games/{game_id}/tasks")
async def add_task(game_id: str, task: TaskModel, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            tid = secrets.token_hex(4)
            g.setdefault("tasks", []).append({"id": tid, **task.dict()})
            save_json(CONFIG_FILE, cfg)
            return {"ok": True, "id": tid}
    raise HTTPException(404, "Game nahi mila")

@app.put("/api/admin/games/{game_id}/tasks/{task_id}")
async def update_task(game_id: str, task_id: str, task: TaskModel, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            for t in g.get("tasks", []):
                if t["id"] == task_id:
                    t.update(task.dict())
                    t["id"] = task_id
                    save_json(CONFIG_FILE, cfg)
                    return {"ok": True}
    raise HTTPException(404, "Task nahi mila")

@app.delete("/api/admin/games/{game_id}/tasks/{task_id}")
async def delete_task(game_id: str, task_id: str, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            g["tasks"] = [t for t in g.get("tasks", []) if t["id"] != task_id]
            save_json(CONFIG_FILE, cfg)
            return {"ok": True}
    raise HTTPException(404, "Game nahi mila")

@app.patch("/api/admin/games/{game_id}/tasks/{task_id}/toggle")
async def toggle_task(game_id: str, task_id: str, auth=Depends(verify_admin)):
    cfg = load_config()
    for g in cfg["games"]:
        if g["id"] == game_id:
            for t in g.get("tasks", []):
                if t["id"] == task_id:
                    t["enabled"] = not t.get("enabled", True)
                    save_json(CONFIG_FILE, cfg)
                    return {"ok": True, "enabled": t["enabled"]}
    raise HTTPException(404, "Task nahi mila")

# ── Analytics (Admin) ─────────────────────────────────────────────────────────
@app.get("/api/admin/analytics")
async def get_analytics(auth=Depends(verify_admin)):
    logs         = load_logs()
    events       = logs["events"]
    today        = date.today().isoformat()
    today_events = [e for e in events if e.get("date") == today]
    success_all  = [e for e in events if e.get("status") == "success"]
    fail_all     = [e for e in events if e.get("status") == "failed"]
    game_counts  = {}
    for e in success_all:
        g = e.get("game", "Unknown")
        game_counts[g] = game_counts.get(g, 0) + 1
    return {
        "total_events":  len(events),
        "today_events":  len(today_events),
        "total_success": len(success_all),
        "total_failed":  len(fail_all),
        "top_games":     sorted(game_counts.items(), key=lambda x: -x[1])[:5],
        "recent_logs":   events[:50]
    }

@app.delete("/api/admin/logs")
async def clear_logs(auth=Depends(verify_admin)):
    save_json(LOGS_FILE, {"events": []})
    return {"ok": True}

# ── Settings (Admin) ──────────────────────────────────────────────────────────
@app.get("/api/admin/settings")
async def get_settings(auth=Depends(verify_admin)):
    s = load_settings()
    s.pop("admin_password", None)
    return s

@app.put("/api/admin/settings")
async def update_settings(upd: SettingsUpdate, auth=Depends(verify_admin)):
    s = load_settings()
    if upd.app_name           is not None: s["app_name"]           = upd.app_name
    if upd.maintenance        is not None: s["maintenance"]        = upd.maintenance
    if upd.rate_limit         is not None: s["rate_limit"]         = upd.rate_limit
    if upd.postback_url       is not None: s["postback_url"]       = upd.postback_url
    if upd.allow_registration is not None: s["allow_registration"] = upd.allow_registration
    if upd.new_password:
        curr_hash = hashlib.sha256((upd.current_password or "").encode()).hexdigest()
        if curr_hash != s["admin_password"]:
            raise HTTPException(400, "Current password galat hai")
        s["admin_password"] = hashlib.sha256(upd.new_password.encode()).hexdigest()
    save_json(SETTINGS_FILE, s)
    return {"ok": True}

# ── Public API (User Panel) ───────────────────────────────────────────────────
@app.get("/api/games")
async def public_games():
    settings = load_settings()
    if settings.get("maintenance"):
        raise HTTPException(503, "Maintenance mode ON — baad mein aao")
    cfg    = load_config()
    result = []
    for g in cfg["games"]:
        if not g.get("enabled", True):
            continue
        tasks = [
            {"id": t["id"], "label": t["label"],
             "reward": t.get("reward", 0)}
            for t in g.get("tasks", []) if t.get("enabled", True)
        ]
        result.append({
            "id":       g["id"],
            "name":     g["name"],
            "icon":     g.get("icon", "🎮"),
            "platform": g.get("platform", "android"),
            "tasks":    tasks
        })
    return {"games": result}

@app.post("/api/bypass")
async def bypass_event(req: BypassRequest):
    settings = load_settings()
    if settings.get("maintenance"):
        raise HTTPException(503, "Maintenance mode ON")
    if not req.gaid or not req.af_id:
        raise HTTPException(400, "GAID aur AppsFlyer ID dono chahiye")

    cfg  = load_config()
    game = next((g for g in cfg["games"] if g["id"] == req.game_id), None)
    if not game:
        raise HTTPException(404, "Game nahi mila")
    if not game.get("enabled", True):
        raise HTTPException(400, "Yeh game disabled hai")

    task = next((t for t in game.get("tasks", []) if t["id"] == req.task_id), None)
    if not task:
        raise HTTPException(404, "Task nahi mila")
    if not task.get("enabled", True):
        raise HTTPException(400, "Yeh task disabled hai")

    if not check_rate_limit(req.gaid):
        limit = settings.get("rate_limit", 10)
        raise HTTPException(429, f"Rate limit exceed — aaj ke liye limit {limit} hai")

    if not game.get("dev_key"):
        raise HTTPException(400, "Dev Key set nahi hai — admin se contact karo")

    now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
    payload = {
        "appsflyer_id":   req.af_id,
        "advertising_id": req.gaid,
        "eventName":      task["event_name"],
        "eventValue":     json.dumps(task.get("event_value", {})),
        "eventTime":      now,
    }
    if req.ip:      payload["ip"]                 = req.ip
    if req.user_id: payload["customer_user_id"]   = req.user_id

    url     = f"https://api2.appsflyer.com/inappevent/{game['app_id']}"
    headers = {"authentication": game["dev_key"], "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
        status = "success" if resp.status_code == 200 else "failed"
        add_log(game["name"], task["label"], req.user_id, req.gaid, status, resp.text)

        if resp.status_code == 200:
            return {
                "ok":      True,
                "message": f"Event fire ho gaya! Reward: {task.get('reward', 0)} coins",
                "reward":  task.get("reward", 0),
                "event":   task["event_name"]
            }
        else:
            return JSONResponse(status_code=400, content={
                "ok":      False,
                "message": f"AppsFlyer ne reject kiya ({resp.status_code})",
                "detail":  resp.text
            })
    except Exception as e:
        add_log(game["name"], task["label"], req.user_id, req.gaid, "failed", str(e))
        raise HTTPException(500, f"Network error: {str(e)}")

# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

# ── Serve HTML Pages (GET + HEAD fixed for Render) ───────────────────────────
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def user_page(request: Request):
    if request.method == "HEAD":
        return HTMLResponse(content="", status_code=200)
    with open("templates/user.html") as f:
        return HTMLResponse(content=f.read())

@app.api_route("/admin", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def admin_page(request: Request):
    if request.method == "HEAD":
        return HTMLResponse(content="", status_code=200)
    with open("templates/admin.html") as f:
        return HTMLResponse(content=f.read())

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
