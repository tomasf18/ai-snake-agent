"""Network Game Server."""
from __future__ import annotations
import argparse
import asyncio
from datetime import datetime
import json
import logging
import os.path
import random
from collections import namedtuple
from typing import Any, Dict, Set

import requests
import websockets
from requests import RequestException
from websockets.legacy.protocol import WebSocketCommonProtocol

from game import Game

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.WARN)

logger = logging.getLogger("Server")
logger.setLevel(logging.INFO)

Player = namedtuple("Player", ["name", "ws"])

HIGHSCORE_FILE = "highscores.json"
MAX_HIGHSCORES = 10


class GameServer:
    """Network Game Server."""

    def __init__(
        self,
        level: int,
        timeout: int,
        seed: int = 0,
        players=1,
        grading: str = None,
        dbg: bool = False,
    ):
        """Initialize Gameserver."""
        self.dbg = dbg
        self.seed = seed
        self.game = Game()
        self.players: asyncio.Queue[Player] = asyncio.Queue()
        self.viewers: Set[WebSocketCommonProtocol] = set()
        self.grading = grading
        self._level = level  # game level
        self._timeout = timeout  # timeout for game
        self.game_player = {}  # websocket to player mapping
        self.number_of_players = players

        self._highscores = []
        if os.path.isfile(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as infile:
                self._highscores = json.load(infile)

    def save_highscores(self):
        """Update highscores, storing to file."""

        logger.debug("Save highscores")
        for player in self.game_player.values():
            logger.info(
                "Saving: %s <%s>",
                player,
                self.game.snakes[player].score,
            )

            self._highscores.append((player, self.game.snakes[player].score))
            self._highscores = sorted(
                self._highscores, key=lambda s: s[1], reverse=True
            )[:MAX_HIGHSCORES]

        with open(HIGHSCORE_FILE, "w") as outfile:
            json.dump(self._highscores, outfile)

    async def send_info(self, highscores: bool = False):
        """Send game info to viewer and player."""
        game_info = self.game.info()

        if highscores:
            game_info["highscores"] = self._highscores

        for viewer in self.viewers:
            try:
                await viewer.send(json.dumps(game_info))
            except Exception:
                self.viewers.remove(viewer)
                viewer.close()

        for ws, player in self.game_player.items():
            try:
                await ws.send(json.dumps(game_info))
            except Exception:
                self.game_player.pop(ws)
                await ws.close()

    async def incomming_handler(self, websocket: WebSocketCommonProtocol, path: str):
        """Process new clients arriving at the server."""
        try:
            async for message in websocket:
                data = json.loads(message)
                if "cmd" not in data:
                    continue
                if data["cmd"] == "join":
                    if path == "/player":
                        if data["name"] in self.game_player.values():
                            logger.error("Player <%s> already exists", data["name"])
                            await websocket.close()
                            continue
                        logger.info("<%s> has joined", data["name"])
                        await self.players.put(Player(data["name"], websocket))
                        self.game_player[websocket] = data["name"]

                    if path == "/viewer":
                        logger.info("Viewer connected")
                        self.viewers.add(websocket)
                        if self.game.running:
                            game_info = self.game.info()
                            await websocket.send(json.dumps(game_info))

                if data["cmd"] == "key":
                    logger.debug((self.game_player[websocket], data))
                    if len(data["key"]) > 0:
                        self.game.keypress(self.game_player[websocket], data["key"][0])
                    else:
                        self.game.keypress(self.game_player[websocket], "")

        except websockets.exceptions.ConnectionClosed as closed_reason:
            logger.info("Client disconnected: %s", closed_reason)
            if websocket in self.viewers:
                self.viewers.remove(websocket)

    async def mainloop(self):
        """Run the game."""
        while True:
            game_players = []
            logger.info("Waiting for players")
            while len(game_players) < self.number_of_players:
                game_players.append(await self.players.get())

                if game_players[-1].ws.closed:
                    logger.error("<%s> disconnect while waiting", game_players[-1].name)
                    continue

            try:
                logger.info("Starting game")
                if self.seed > 0:
                    random.seed(self.seed)

                self.game = Game()
                self.game.start([p.name for p in game_players])

                while self.game.running:
                    if self.game._step == 0:  # Starting a level ? Let's send the info
                        await self.send_info()

                    if state := await self.game.next_frame():
                        for viewer in self.viewers:
                            try:
                                await viewer.send(json.dumps(state))
                            except Exception as err:
                                logger.error(err)
                                self.viewers.remove(viewer)
                                break

                        snakes = state["snakes"]
                        del state[
                            "snakes"
                        ]  # remove snakes from state as we only send our snake sight

                        for player in game_players:
                            state["ts"] = datetime.now().isoformat()
                            for player_snake in snakes:
                                if player_snake["name"] == player.name:
                                    state = {**state, **player_snake}

                            await player.ws.send(json.dumps(state))

                self.save_highscores()

                await self.send_info(highscores=True)
                for ws, player in self.game_player.items():
                    await ws.close()
                self.game_player = {}

            except websockets.exceptions.ConnectionClosed as ws_closed:
                if ws_closed in self.game_player:
                    self.game_player.pop(ws_closed)
                logger.error("Player disconnected: %s", ws_closed)
            finally:
                try:
                    if self.grading:
                        for player in game_players:
                            game_record = {
                                "player": player.name,
                                "score": self.game.snakes[player.name].score,
                            }
                            requests.post(self.grading, json=game_record, timeout=2)
                except RequestException as err:
                    logger.error(err)
                    logger.warning("Could not save score to server")

                for ws, player in self.game_player.items():
                    logger.info("Disconnecting <%s>", player)
                    await ws.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="")
    parser.add_argument("--port", help="TCP port", type=int, default=8000)
    parser.add_argument("--seed", help="Seed number", type=int, default=0)
    parser.add_argument(
        "--debug", help="Open Bitmap with map on gameover", action="store_true"
    )
    parser.add_argument("--players", help="Number of players", type=int, default=1)
    parser.add_argument(
        "--grading-server",
        help="url of grading server",
        default=None,  # TODO "http://tetriscores.av.it.pt/game",
    )
    args = parser.parse_args()

    async def main():
        """Start server tasks."""
        g = GameServer(0, -1, args.seed, args.players, args.grading_server, args.debug)

        game_loop_task = asyncio.ensure_future(g.mainloop())

        logger.info("Listenning @ %s:%s", args.bind, args.port)
        websocket_server = websockets.serve(g.incomming_handler, args.bind, args.port)

        await asyncio.gather(websocket_server, game_loop_task)

    asyncio.run(main())
