import argparse
import asyncio
import json
import logging
import os
import sys
import pprint

from consts import Tiles
import pygame
import websockets

logging.basicConfig(level=logging.DEBUG)
logger_websockets = logging.getLogger("websockets")
logger_websockets.setLevel(logging.WARN)

logger = logging.getLogger("Viewer")
logger.setLevel(logging.DEBUG)

from viewer.common import Directions, Food, Snake, Stone, ScoreBoard, get_direction
from viewer.sprites import SnakeSprite, FoodSprite, StoneSprite, ScoreBoardSprite


async def main_loop(q):
    while True:
        await main()

def should_quit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.display.quit()
            pygame.quit()
            sys.exit(0)


async def main(SCALE=32):
    logging.info("Waiting for map information from server")
    while True:
        try:
            should_quit()
            state = q.get_nowait()  # first state message includes map information
            break
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(0.1)
        
    logging.debug("Initial game status: %s", state)
    newgame_json = json.loads(state)

    new_game = True
    GAME_SPEED = newgame_json["fps"]
    WIDTH, HEIGHT = newgame_json["size"]
    MAP = newgame_json["map"]

    display = pygame.display.set_mode((SCALE * WIDTH, SCALE * HEIGHT))

    all_sprites = pygame.sprite.Group()
    food_sprites = pygame.sprite.Group()
    prev_foods = None

    for x, col in enumerate(MAP):
        for y, line in enumerate(col):
            if MAP[x][y] == Tiles.STONE:
                print(f"Stone at {x}, {y}")
                all_sprites.add(StoneSprite(Stone(pos=(x, y)), WIDTH, HEIGHT, SCALE))

    while True:
        should_quit()

        try:
            state = json.loads(q.get_nowait())
            pprint.pprint(state)

            if "snakes" in state and "food" in state:
                snakes_update = state["snakes"]
                foods_update = state["food"]
                foods_update = state["food"]
            else:
                print("Show SCOREBOARD")
                return

        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(0.1 / GAME_SPEED)
            continue

        # Update Foods
        if new_game or prev_foods != foods_update:
            food_sprites.empty()

            foods = {
                f"{food}": Food(pos=(food[0], food[1]), is_super=food[2] == "SUPER")
                for food in foods_update
            }
            food_sprites.add(
                [FoodSprite(food, WIDTH, HEIGHT, SCALE) for food in foods.values()]
            )
            prev_foods = foods_update

        # Update Snakes
        if new_game:
            snakes = {
                snake["name"]: Snake(body=snake["body"], direction=Directions.RIGHT)
                for snake in snakes_update
            }

            all_sprites.add(
                [SnakeSprite(snake, WIDTH, HEIGHT, SCALE) for snake in snakes.values()]
            )
            new_game = False
        else:
            for snake in snakes_update:
                snakes[snake["name"]].body = snake["body"]
                head = snake["body"][0]
                neck = snake["body"][1]
                snakes[snake["name"]].direction = get_direction(
                    head[0], head[1], neck[0], neck[1], HEIGHT=HEIGHT, WIDTH=WIDTH
                )

        # Render Window
        display.fill("white")

        try:
            all_sprites.update()
            food_sprites.update()
        except Exception as e:
            logging.error(e)
        food_sprites.draw(display)
        all_sprites.draw(display)

        # update window
        pygame.display.flip()


async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)


if __name__ == "__main__":
    SERVER = os.environ.get("SERVER", "localhost")
    PORT = os.environ.get("PORT", "8000")

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP address of the server", default=SERVER)
    parser.add_argument(
        "--scale", help="reduce size of window by x times", type=int, default=1
    )
    parser.add_argument("--port", help="TCP port", type=int, default=PORT)
    args = parser.parse_args()
    SCALE = args.scale

    LOOP = asyncio.get_event_loop()
    pygame.init()
    pygame.font.init()
    q: asyncio.Queue = asyncio.Queue()

    ws_path = f"ws://{args.server}:{args.port}/viewer"

    try:
        LOOP.run_until_complete(
            asyncio.gather(messages_handler(ws_path, q), main_loop(q))
        )
    finally:
        LOOP.stop()
