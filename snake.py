import consts

class Snake:
    def __init__(self):
        pass

    def update(self, state: dict) -> None:
        # extract information from the state
        self.players = state["players"]
        self.step = state["step"]
        self.timeout = state["timeout"]
        self.timestamp = state["ts"]
        self.name = state["name"]
        self.snake = state["body"]
        self.snake_head = self.snake[0]
        self.snake_body = self.snake[1:]
        self.snake_sight = state["sight"]
        self.score = state["score"]
        self.snake_range = state["range"]
        self.snake_traverse = state["traverse"]
    
    def check_food_in_sight(self) -> list[int] | None:
        for row, cols in self.snake_sight.items():
            for col, value in cols.items():
                if value == consts.Tiles.FOOD:
                    return [int(row), int(col)]
        return None