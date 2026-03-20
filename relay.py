#!/usr/bin/env python3
"""
relay.py — Serveur WebSocket local
Lance ce script sur ta machine locale (là où tourne le navigateur).
Usage : python relay.py [--port 8765]
"""

import asyncio
import argparse
import logging
import websockets
from websockets.asyncio.server import ServerConnection

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("relay")

# Ensemble des clients navigateur connectés
browsers: set[ServerConnection] = set()


async def handler(ws: ServerConnection):
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


async def main(port: int):
    log.info("Relay démarré sur ws://localhost:%d", port)
    log.info("  → navigateur sur  ws://localhost:%d/view", port)
    log.info("  → producteur sur  ws://localhost:%d/send", port)
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # tourne indéfiniment


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
