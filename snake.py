from SnakeDomain import SnakeDomain

class Snake:
    def __init__(self):
        pass

    def update(self, state: dict) -> None:
        # extract information from the state
        self.level = state["level"]  # get the level (provavelmente não é necessário -----------)
        self.step = state["step"]  # get the step (provavelmente não é necessário -----------)
        self.timeout = state["timeout"]  # get the timeout (provavelmente não é necessário -----------)

        self.food_position = state["food"][0][0:2]  # get the food position
        self.food_type = state["food"][0][2]  # get the food type

        self.timestamp = state["ts"]  # get the timestamp (provavelmente não é necessário -----------)
        self.name = state["name"]  # get the snake name (provavelmente não é necessário -----------)

        self.snake = state["body"]  # get the snake body positions
        self.snake_head = self.snake[0]  # get the snake head position
        self.snake_body = self.snake[1:]  # get the snake body positions
        self.snake_sight = state["sight"]  # get the snake sight
        self.score = state["score"]  # get the score
        self.snake_range = state["range"]  # get the snake range
        self.snake_traverse = state["traverse"]  # get the snake traverse


        # simple logic to move the snake to the food
        # if self.snake_head[0] < self.food_position[0]:
        #     return "d" # move right
        # elif self.snake_head[0] > self.food_position[0]:
        #     return "a" # move left
        # elif self.snake_head[1] < self.food_position[1]:
        #     return "s" # move down
        # elif self.snake_head[1] > self.food_position[1]:
        #     return "w" # move up