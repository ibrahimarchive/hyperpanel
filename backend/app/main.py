"""
HyperPanel — FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json

from app.config import settings
from app.database import init_db, async_session
from app.services.auth_service import create_admin_user, decode_token
from app.services.terminal_service import terminal_manager
from app.services.system_service import (
    get_cpu_stats, get_memory_stats, get_disk_stats, get_network_stats,
)

# Import routers
from app.routers import (
    auth, dashboard, websites, databases, domains, ssl, files, firewall, users,
    docker, email, ftp, backups, cron, fail2ban, logs, php, processes, services, activity, updates, panel_settings,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hyperpanel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info(f"Starting {settings.PANEL_NAME} v{settings.PANEL_VERSION}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create admin user if not exists
    async with async_session() as session:
        admin = await create_admin_user(session)
        if admin:
            logger.info(f"Admin user '{admin.username}' created")
        await session.commit()

    yield

    logger.info("Shutting down HyperPanel")


# Create FastAPI app
app = FastAPI(
    title=settings.PANEL_NAME,
    version=settings.PANEL_VERSION,
    description="A modern server control panel",
    lifespan=lifespan,
)

# CORS
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
is_wildcard = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=not is_wildcard,  # Avoid wildcard with credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(websites.router)
app.include_router(databases.router)
app.include_router(domains.router)
app.include_router(domains.dns_router)
app.include_router(ssl.router)
app.include_router(files.router)
app.include_router(firewall.router)
app.include_router(users.router)
app.include_router(docker.router)
app.include_router(email.router)
app.include_router(ftp.router)
app.include_router(backups.router)
app.include_router(cron.router)
app.include_router(fail2ban.router)
app.include_router(logs.router)
app.include_router(php.router)
app.include_router(processes.router)
app.include_router(services.router)
app.include_router(activity.router)
app.include_router(updates.router)
app.include_router(panel_settings.router)


# ── WebSocket: Real-time Monitoring ──────────────────────────────

class ConnectionManager:
    """Manages WebSocket connections for real-time monitoring."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, data: dict):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@app.websocket("/ws/monitoring")
async def monitoring_websocket(websocket: WebSocket):
    """Real-time system monitoring via WebSocket."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Send system stats every 2 seconds
            stats = {
                "cpu": get_cpu_stats().model_dump(),
                "memory": get_memory_stats().model_dump(),
                "disk": get_disk_stats().model_dump(),
                "network": get_network_stats().model_dump(),
            }
            await websocket.send_json(stats)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """Web terminal WebSocket endpoint connecting to PTY shell."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=1008)
        return

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    session = terminal_manager.create_session(user_id)
    started = await session.start()
    if not started:
        try:
            await websocket.send_text("\r\n\x1b[31m[Error: Failed to spawn shell process]\x1b[0m\r\n")
            await websocket.close(code=1011)
        except Exception:
            pass
        terminal_manager.remove_session(session.session_id)
        return

    stop_event = asyncio.Event()

    async def pty_reader():
        try:
            while not stop_event.is_set() and session.is_alive():
                data = session.read()
                if data:
                    await websocket.send_text(data)
                await asyncio.sleep(0.02)
        except Exception:
            pass
        finally:
            stop_event.set()

    reader_task = asyncio.create_task(pty_reader())

    try:
        while not stop_event.is_set():
            try:
                message = await websocket.receive_text()
            except (WebSocketDisconnect, Exception):
                break

            try:
                msg = json.loads(message)
                msg_type = msg.get("type")
                if msg_type == "input":
                    session.write(msg.get("data", ""))
                elif msg_type == "resize":
                    cols = int(msg.get("cols", 80))
                    rows = int(msg.get("rows", 24))
                    session.resize(cols, rows)
            except json.JSONDecodeError:
                session.write(message)
    finally:
        stop_event.set()
        reader_task.cancel()
        terminal_manager.remove_session(session.session_id)


# ── Serve Frontend ──────────────────────────────────────────────

# Serve static frontend files
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")

    @app.get("/login")
    async def serve_login():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(str(frontend_dir / "dashboard.html"))

    @app.get("/panel")
    async def serve_panel():
        return FileResponse(str(frontend_dir / "dashboard.html"))


# ── Health Check ─────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
    }


# ── Run with Uvicorn ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.PANEL_HOST,
        port=settings.PANEL_INTERNAL_PORT,
        reload=settings.DEBUG,
    )
