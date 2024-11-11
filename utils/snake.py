import consts

class Snake:
    def __init__(self):
        pass

    def update(self, data: dict) -> None:
        
        # extract information from the data
        self.players = data["players"]
        self.step = data["step"]
        self.timeout = data["timeout"]
        self.timestamp = data["ts"]
        self.name = data["name"]
        self.snake = data["body"]
        self.snake_head = self.snake[0]
        self.snake_body = self.snake[1:]
        self.snake_sight = data["sight"]
        self.score = data["score"]
        self.snake_range = data["range"]
        self.snake_traverse = data["traverse"]
    
    def check_food_in_sight(self) -> list[tuple[int, int]]:
        foods_in_sight = []
        super_foods_in_sight = []
        for row, cols in self.snake_sight.items():
            for col, value in cols.items():
                if value == consts.Tiles.FOOD:
                    foods_in_sight.append( (int(row), int(col)) )
                if value == consts.Tiles.SUPER:
                    super_foods_in_sight.append( (int(row), int(col)) )
        return foods_in_sight, super_foods_in_sight