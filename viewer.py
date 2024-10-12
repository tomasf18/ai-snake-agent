import argparse
import asyncio
import json
import logging
import os
import sys

import pygame
import websockets

from mapa import Map, Tiles

logging.basicConfig(level=logging.DEBUG)
logger_websockets = logging.getLogger("websockets")
logger_websockets.setLevel(logging.WARN)

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)

STAR = (3 * 16, 7 * 16)

SNAKE = {
    "up": (3 * 40, 0),
    "left": (4 * 40, 1 * 40),
    "down": (3 * 40, 1 * 40),
    "right": (4 * 40, 0),
}
SNAKE_BODY = {
    "up_tail": (0, 0),
    "down_tail": (40, 40),
    "left_tail": (0, 40),
    "right_tail": (40, 0),
    "vertical": (2 * 40, 0),
    "horizontal": (2 * 40, 40),
    "left_up": (5 * 40, 0),
    "left_down": (5 * 40, 40),
    "right_up": (6 * 40, 0),
    "right_down": (6 * 40, 40),
}

CHAR_LENGTH = 40
CHAR_SIZE = CHAR_LENGTH, CHAR_LENGTH
SCALE = 1

COLORS = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "pink": (255, 105, 180),
    "blue": (135, 206, 235),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "grey": (120, 120, 120),
}
BACKGROUND_COLOR = (0, 0, 0)
ROCK_COLOR = (222, 204, 166)


RANKS = {
    1: "1ST",
    2: "2ND",
    3: "3RD",
    4: "4TH",
    5: "5TH",
    6: "6TH",
    7: "7TH",
    8: "8TH",
    9: "9TH",
    10: "10TH",
}

SPRITES = None


async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)


class Artifact(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = None, None  # postpone to update_sprite()
        if not hasattr(self, "sprite"):
            self.sprite = (SPRITES, (0, 0), (*STAR, *scale((1, 1))))
        self.sprite_id = kw.pop("sprite_id", None)
        x, y = kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0))))
        self.direction = "left"

        new_pos = scale((x, y))
        self.image = pygame.Surface(CHAR_SIZE)
        self.rect = pygame.Rect(new_pos + CHAR_SIZE)
        self.update_sprite((x, y))
        super().__init__()

    def update_sprite(self, pos=None):
        if not pos:
            pos = self.x, self.y
        else:
            pos = scale(pos)

        self.rect = pygame.Rect(pos + CHAR_SIZE)
        self.image.fill((0, 0, 230))
        self.image.blit(*self.sprite)
        # self.image = pygame.transform.scale(self.image, scale((1, 1)))
        self.image.set_alpha()
        self.x, self.y = pos

    def update(self, *args, **kw):
        self.update_sprite()


class Food(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*SNAKE["up"], *scale((1, 1))))
        self.name = "food"
        super().__init__(*args, **kw)
        self.image.fill((200, 0, 0))


class SuperFood(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*SNAKE["up"], *scale((1, 1))))
        self.name = "superfood"
        super().__init__(*args, **kw)
        self.image.fill((100, 0, 100))


class Snake(Artifact):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.direction = "right"
        self.idx = kw.pop("idx")

    def update(self, new_pos, sprite_id, direction):
        if self.sprite_id != sprite_id:
            return
        x, y = scale(new_pos)

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        if sprite_id.endswith("_0"):
            self.sprite = (SPRITES, (0, 0), (*SNAKE[self.direction], *scale((1, 1))))
        else:
            dir = "horizontal" if self.direction in ["left", "right"] else "vertical"
            self.sprite = (SPRITES, (0, 0), (*SNAKE_BODY[dir], *scale((1, 1))))

        self.update_sprite(tuple(new_pos))


def clear_callback(surf, rect):
    """beneath everything there is a passage."""
    pygame.draw.rect(surf, BACKGROUND_COLOR, rect)


def scale(pos):
    x, y = pos
    return int(x * CHAR_LENGTH / SCALE), int(y * CHAR_LENGTH / SCALE)


def draw_background(mapa):
    background = pygame.Surface(scale((int(mapa.size[0]), int(mapa.size[1]))))
    for x in range(int(mapa.size[0])):
        for y in range(int(mapa.size[1])):
            wx, wy = scale((x, y))
            if mapa.map[x][y] == Tiles.STONE:
                pygame.draw.rect(
                    background, ROCK_COLOR, (wx, wy, *scale((1, 1)))
                )
            else:
                pygame.draw.rect(background, BACKGROUND_COLOR, (wx, wy, *scale((1, 1))))
    return background


def draw_info(SCREEN, text, pos, color=(180, 0, 0), background=None):
    myfont = pygame.font.Font(None, int(22 / SCALE))
    textsurface = myfont.render(text, True, color, background)

    x, y = pos
    if x > SCREEN.get_width():
        pos = SCREEN.get_width() - (textsurface.get_width() + 10), y
    if y > SCREEN.get_height():
        pos = x, SCREEN.get_height() - textsurface.get_height()

    if background:
        SCREEN.blit(background, pos)
    else:
        erase = pygame.Surface(textsurface.get_size())
        erase.fill(COLORS["grey"])

    SCREEN.blit(textsurface, pos)
    return textsurface.get_width(), textsurface.get_height()


async def main_loop(q):
    while True:
        await main_game()


async def main_game():
    global SPRITES, SCREEN

    main_group = pygame.sprite.LayeredUpdates()
    food_group = pygame.sprite.OrderedUpdates()

    logging.info("Waiting for map information from server")
    state = await q.get()  # first state message includes map information
    logging.debug("Initial game status: %s", state)
    newgame_json = json.loads(state)

    GAME_SPEED = newgame_json["fps"]
    mapa = Map(size=newgame_json["size"], mapa=newgame_json["map"])
    SCREEN = pygame.display.set_mode(scale(mapa.size))
    SPRITES = pygame.image.load("data/tilemap.png").convert_alpha()

    BACKGROUND = draw_background(mapa)
    SCREEN.blit(BACKGROUND, (0, 0))

    state = {"score": 0, "player": "player1", "digdug": (1, 1)}

    while True:
        if "size" in state and "map" in state:
            # New level! lets clean everything up!
            logger.info("New level! %s", state["level"])
            mapa = Map(size=state["size"], mapa=state["map"])
            BACKGROUND = draw_background(mapa)

            SCREEN.blit(BACKGROUND, (0, 0))

            main_group.empty()
            food_group.empty()

        if "highscores" not in state:
            SCREEN.blit(BACKGROUND, (0, 0))

        def quit():
            # clean up and exit
            pygame.display.quit()
            pygame.quit()
            sys.exit(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            quit()

        if "score" in state and "player" in state:
            text = str(state["score"])
            draw_info(SCREEN, text.zfill(6), (5, 1))
            text = str(state["player"]).rjust(32)
            draw_info(SCREEN, text, (4000, 1))

        if "lives" in state and "level" in state:
            w, h = draw_info(SCREEN, "lives: ", (SCREEN.get_width() / 4, 1))
            draw_info(
                SCREEN,
                f"{state['lives']}",
                (SCREEN.get_width() / 4 + w, 1),
                color=(255, 0, 0),
            )
            w, h = draw_info(SCREEN, "level: ", (2 * SCREEN.get_width() / 4, 1))
            draw_info(
                SCREEN,
                f"{state['level']}",
                (2 * SCREEN.get_width() / 4 + w, 1),
                color=(255, 0, 0),
            )

        if "step" in state:
            w, h = draw_info(SCREEN, "steps: ", (3 * SCREEN.get_width() / 4, 1))
            draw_info(
                SCREEN,
                f"{state['step']}",
                (3 * SCREEN.get_width() / 4 + w, 1),
                color=(255, 0, 0),
            )

        if "snakes" in state:
            for snake in state["snakes"]:

                for idx, snake_body_part in enumerate(snake["body"]):
                    if f"{snake['name']}_{idx}" not in [
                        s.sprite_id for s in main_group.sprites()
                    ]:
                        main_group.add(
                            Snake(
                                pos=snake_body_part,
                                sprite_id=f"{snake['name']}_{idx}",
                                idx=idx,
                            )
                        )
                    else:
                        x, y = snake_body_part
 
                        direction = "right"

                        main_group.update(
                            snake_body_part, sprite_id=f"{snake['name']}_{idx}", direction=direction
                        )

        if "food" in state:
            for food in state["food"]:
                if food not in [f.sprite_id for f in food_group.sprites()]:
                    x, y, kind = food
                    if kind == "FOOD":
                        food_group.add(Food(pos=(x, y), sprite_id=food))
                    else:
                        food_group.add(SuperFood(pos=(x, y), sprite_id=food))
            for food in food_group.sprites():
                if food.sprite_id not in state["food"]:
                    food_group.remove(food)

        #        if "rocks" in state:
        #            for rock in state["rocks"]:
        #                enemies_group.add(Rock(pos=rock["pos"], sprite_id=rock["id"]))

        main_group.draw(SCREEN)
        food_group.draw(SCREEN)

        if "highscores" in state:
            highscores = state["highscores"]

            HIGHSCORES = pygame.Surface(scale((20, 16)))
            HIGHSCORES.fill(COLORS["grey"])

            draw_info(HIGHSCORES, "THE 10 BEST PLAYERS", scale((5, 1)), COLORS["white"])
            draw_info(HIGHSCORES, "RANK", scale((2, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "SCORE", scale((6, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "NAME", scale((11, 3)), COLORS["orange"])

            for i, highscore in enumerate(highscores):
                c = (i % 5) + 1
                draw_info(
                    HIGHSCORES,
                    RANKS[i + 1],
                    scale((2, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    str(highscore[1]),
                    scale((6, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    highscore[0],
                    scale((11, i + 5)),
                    list(COLORS.values())[c],
                )

            SCREEN.blit(
                HIGHSCORES,
                (
                    (SCREEN.get_width() - HIGHSCORES.get_width()) / 2,
                    (SCREEN.get_height() - HIGHSCORES.get_height()) / 2,
                ),
            )
            pygame.display.flip()  # Show highscores and wait for a new game
            break

        pygame.display.flip()

        try:

            state = json.loads(q.get_nowait())
            import pprint
            pprint.pprint(state)
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(1.0 / GAME_SPEED)
            continue


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
    pygame.font.init()
    q: asyncio.Queue = asyncio.Queue()

    ws_path = f"ws://{args.server}:{args.port}/viewer"

    try:
        LOOP.run_until_complete(
            asyncio.gather(messages_handler(ws_path, q), main_loop(q))
        )
    finally:
        LOOP.stop()
