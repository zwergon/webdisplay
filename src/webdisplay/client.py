"""
webdisplay.py — Module côté machine distante
Copiez ce fichier à côté de vos scripts Python.

Dépendances : pip install websockets pillow
(matplotlib est optionnel, uniquement si vous utilisez show_figure)

Usage rapide :
    import webdisplay
    webdisplay.connect("ws://localhost:8765/send")   # une seule fois

    # Depuis matplotlib
    webdisplay.show_figure(fig)

    # Depuis PIL / Pillow
    webdisplay.show_image(pil_img)

    # Depuis des bytes PNG bruts
    webdisplay.show_png(png_bytes)

    # Fermer proprement en fin de script
    webdisplay.close()
"""

import asyncio
import io
import threading
import base64
import json
import websockets

# ── état interne ──────────────────────────────────────────────────────────────
_loop: asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None
_ws = None
_uri: str = "ws://localhost:8765/send"


# ── démarrage de la boucle asyncio dans un thread dédié ──────────────────────

def connect(uri: str = "ws://localhost:8765/send"):
    """Ouvre la connexion WebSocket vers le relay.  Appel optionnel :
    si vous appelez show_* sans avoir appelé connect(), la connexion
    s'établit automatiquement avec l'URI par défaut."""
    global _uri
    _uri = uri
    _ensure_started()

    future = asyncio.run_coroutine_threadsafe(_connect(), _loop)
    try:
        future.result(timeout=5)
    except Exception as e:
        raise RuntimeError(
            f"Webdisplay: impossible de se connecter à {uri}") from e


def close():
    """Ferme proprement la connexion."""
    global _ws, _loop
    if _ws and _loop:
        asyncio.run_coroutine_threadsafe(_ws.close(), _loop)


# ── API publique ──────────────────────────────────────────────────────────────

def show_figure(fig, title: str = "", dpi: int = 150, fmt: str = "png"):
    """Envoie une figure matplotlib.
    Exemple :
        fig, ax = plt.subplots()
        ax.plot([1,2,3])
        webdisplay.show_figure(fig)
    """
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    show_png(buf.read(), title=title)


def show_image(pil_img, title: str = "", fmt: str = "PNG"):
    """Envoie un objet PIL.Image.
    Exemple :
        from PIL import Image
        img = Image.open("photo.jpg")
        webdisplay.show_image(img)
    """
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    buf.seek(0)
    show_png(buf.read(), title=title)


def show_png(png_bytes: bytes, title: str = ""):
    """Envoie des bytes PNG bruts."""
    _ensure_started()
    b64 = base64.b64encode(png_bytes).decode()
    payload = json.dumps({"title": title, "data": b64})
    future = asyncio.run_coroutine_threadsafe(_send(payload), _loop)
    future.result(timeout=10)   # bloquant côté script, non bloquant côté relay


# ── internals ─────────────────────────────────────────────────────────────────

def _ensure_started():
    global _loop, _thread
    if _loop is None:
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_loop.run_forever, daemon=True)
        _thread.start()


async def _connect():
    global _ws
    try:
        _ws = await websockets.connect(_uri)
    except Exception as e:
        _ws = None
        raise ConnectionError(f"Impossible de se connecter à {_uri}") from e


async def _send(payload: str):
    global _ws
    if _ws is None:
        await _connect()
    try:
        await _ws.send(payload)
    except (websockets.exceptions.ConnectionClosed, Exception):
        # Reconnexion automatique si la connexion a été perdue
        await _connect()
        await _ws.send(payload)
