import pygame

from spritesheet import SpriteSheet
from common import Directions, Snake, Food, ScoreBoard, get_direction

CELL_SIZE = 64


class ScoreBoardSprite(pygame.sprite.Sprite):
    def __init__(self, scoreboard, WIDTH, HEIGHT, SCALE):
        self.font = pygame.font.Font(None, 32)
        super().__init__()

        self.scoreboard = scoreboard
        self.image = pygame.Surface([WIDTH * SCALE, len(scoreboard.scores) * SCALE])
        self.rect = self.image.get_rect()
        self.SCALE = SCALE

    def update(self):
        self.image.fill("white")
        for i, (player, score) in enumerate(self.scoreboard.scores.items()):
            self.image.blit(
                self.font.render(f"{player}: {score}", True, "green", "white"),
                (0, i * self.SCALE),
            )


class FoodSprite(pygame.sprite.Sprite):
    def __init__(self, food: Food, WIDTH, HEIGHT, SCALE):
        super().__init__()

        SNAKE_SPRITESHEET = SpriteSheet("snake-graphics.png")

        self.food = food
        self.SCALE = SCALE

        food_image_rect = (0, 3 * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        self.food_image = SNAKE_SPRITESHEET.image_at(food_image_rect, -1)
        self.food_image = pygame.transform.scale(self.food_image, (SCALE, SCALE))

        self.image = pygame.Surface([WIDTH * SCALE, HEIGHT * SCALE])
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        self.image.fill("white")
        self.image.set_colorkey("white")

        # Render Food
        self.image.blit(
            self.food_image,
            (self.SCALE * self.food.pos[0], self.SCALE * self.food.pos[1]),
        )


class SnakeSprite(pygame.sprite.Sprite):
    def __init__(self, snake: Snake, WIDTH, HEIGHT, SCALE):
        super().__init__()

        SNAKE_SPRITESHEET = SpriteSheet("snake-graphics.png")

        self.snake = snake
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH
        self.SCALE = SCALE

        snake_map = {
            ("head", Directions.UP): (3, 0),
            ("head", Directions.RIGHT): (4, 0),
            ("head", Directions.LEFT): (3, 1),
            ("head", Directions.DOWN): (4, 1),
            (Directions.UP, Directions.RIGHT): (0, 0),
            (Directions.LEFT, Directions.DOWN): (0, 0),
            (Directions.DOWN, Directions.RIGHT): (0, 1),
            (Directions.LEFT, Directions.UP): (0, 1),
            (Directions.LEFT, Directions.LEFT): (1, 0),
            (Directions.RIGHT, Directions.RIGHT): (1, 0),
            (Directions.RIGHT, Directions.DOWN): (2, 0),
            (Directions.UP, Directions.LEFT): (2, 0),
            (Directions.UP, Directions.UP): (2, 1),
            (Directions.DOWN, Directions.DOWN): (2, 1),
            (Directions.RIGHT, Directions.UP): (2, 2),
            (Directions.DOWN, Directions.LEFT): (2, 2),
            ("tail", Directions.UP): (4, 3),
            ("tail", Directions.DOWN): (3, 2),
            ("tail", Directions.RIGHT): (3, 3),
            ("tail", Directions.LEFT): (4, 2),
        }

        # Load and resize images to SCALE
        self.snake_images = {
            name: pygame.transform.scale(
                SNAKE_SPRITESHEET.image_at(
                    (a * CELL_SIZE, b * CELL_SIZE, CELL_SIZE, CELL_SIZE), -1
                ),
                (SCALE, SCALE),
            )
            for (name, (a, b)) in snake_map.items()
        }

        self.image = pygame.Surface([WIDTH * SCALE, HEIGHT * SCALE])
        self.update()
        self.rect = self.image.get_rect()

    def update(self):
        self.image.fill("white")
        self.image.set_colorkey("white")

        # Get Head
        prev_x, prev_y = self.snake.body[0]
        prev_dir = None

        # Walk from 1st body position towards tail
        for x, y in self.snake.body[1:]:
            dir = get_direction(x, y, prev_x, prev_y, self.HEIGHT, self.WIDTH)
            if prev_dir is None:
                image = ("head", self.snake.direction)
            else:
                image = (prev_dir, dir)

            # blit previous body part now that we now directions taken
            if image in self.snake_images:  # TODO remove this check
                self.image.blit(
                    self.snake_images[image], (self.SCALE * prev_x, self.SCALE * prev_y)
                )

            prev_x, prev_y = x, y
            prev_dir = dir

        # Finally blit tail
        self.image.blit(
            self.snake_images[("tail", prev_dir)],
            (self.SCALE * prev_x, self.SCALE * prev_y),
        )
