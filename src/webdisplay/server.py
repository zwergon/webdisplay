import argparse
import pathlib
import time
import asyncio
import logging
import threading
import websockets
import webbrowser

from websockets.asyncio.server import ServerConnection


logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("relay")

# Ensemble des clients navigateur connectés
browsers: set[ServerConnection] = set()


async def _handler(ws: ServerConnection):
    path = ws.request.path if hasattr(
        ws, "request") else getattr(ws, "path", "/")

    if path == "/send":
        # Connexion depuis Python distant
        log.info("Producteur connecté depuis %s", ws.remote_address)
        try:
            async for message in ws:
                if browsers:
                    # Diffuse à tous les navigateurs connectés
                    await asyncio.gather(
                        *[b.send(message) for b in browsers],
                        return_exceptions=True,
                    )
                    log.info(
                        "Image diffusée à %d navigateur(s) (%d octets)",
                        len(browsers),
                        len(message) if isinstance(
                            message, (bytes, str)) else 0,
                    )
                else:
                    log.warning("Aucun navigateur connecté, image ignorée")
        except websockets.exceptions.ConnectionClosed:
            pass
        log.info("Producteur déconnecté")

    else:
        # Connexion depuis le navigateur
        browsers.add(ws)
        log.info("Navigateur connecté (%d au total)", len(browsers))
        try:
            await ws.wait_closed()
        finally:
            browsers.discard(ws)
            log.info("Navigateur déconnecté (%d restants)", len(browsers))


async def _relay(port: int):
    async with websockets.serve(_handler, "0.0.0.0", port):
        log.info("Relay démarré sur ws://localhost:%d", port)
        await asyncio.Future()


HERE = pathlib.Path(__file__).parent.resolve()
HTML_FILE = HERE / "static" / "index.html"


def _open_browser(host: str, port: int, delay: float = 0.8):
    """Ouvre index.html après un court délai (le temps que le relay démarre)."""
    time.sleep(delay)

    html_uri = HTML_FILE.as_uri()

    # On injecte l'URL WebSocket correcte dans la query-string si besoin,
    # mais index.html lit déjà ws://localhost:8765/view par défaut.
    # Si le port est différent, on passe par un fichier HTML temporaire
    # avec l'URL pré-remplie.
    if host != 'localhost' or port != 8765:
        import tempfile
        import shutil
        content = HTML_FILE.read_text(encoding="utf-8")
        content = content.replace(
            "ws://localhost:8765/view",
            f"ws://{host}:{port}/view",
        )
        tmp = pathlib.Path(tempfile.mktemp(suffix=".html"))
        tmp.write_text(content, encoding="utf-8")
        html_uri = tmp.as_uri()

    log.info("Ouverture du navigateur : %s", html_uri)
    webbrowser.open(html_uri)


def start(host: str = 'localhost', port: int = 8765, open_browser: bool = True):
    """Lance le relay et bloque jusqu'à Ctrl+C."""
    if open_browser:
        t = threading.Thread(target=_open_browser,
                             args=(host, port,), daemon=True)
        t.start()

    try:
        asyncio.run(_relay(port))
    except KeyboardInterrupt:
        log.info("Arrêt.")


def run():
    parser = argparse.ArgumentParser(
        description="Lance le relay WebDisplay et ouvre le navigateur.")
    parser.add_argument("--host", type=str, default='localhost',
                        help="Host WebSocket (défaut : localhost)")
    parser.add_argument("--port", type=int, default=8765,
                        help="Port WebSocket (défaut : 8765)")
    parser.add_argument("--no-browser", action="store_true",
                        help="Ne pas ouvrir le navigateur")
    args = parser.parse_args()

    start(host=args.host, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    run()
