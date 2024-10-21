from tree_search import *
from Directions import DIRECTION
from snake import Snake

FREE = 0
WALL = 1
FOOD = 2

class SnakeDomain(SearchDomain):    
    def __init__(self, map: dict):
        self.dim: tuple[int, int] = tuple(map["size"])
        self.board: list[list[int]] = map["map"]

    def actions(self, state) -> list[DIRECTION]:
        """
            Podemos ir na direçao com espaços vazios
            [
                X + X 
                + H |
                X B X
            ]
        """
        snake_body = state["snake_body"]
        snake_traverse = state["snake_traverse"]

        actlist: list[DIRECTION] = []
        snake_head = snake_body[0]
        for dir in DIRECTION:
            new_position = [snake_head[0] + dir.dir[0], snake_head[1] + dir.dir[1]]
            
            # if traverse is true we can go through the map and walls
            if snake_traverse:
                new_position[0] = new_position[0] % self.dim[0]
                new_position[1] = new_position[1] % self.dim[1]
            else:
                # if the new position is out of the map, we ignore it
                if not (0 <= new_position[0] < self.dim[0] and 0 <= new_position[1] < self.dim[1]):
                    continue
            
            if new_position in snake_body:
                continue
            
            if snake_traverse or self.board[new_position[0]][new_position[1]] != WALL:
                actlist.append(dir)

        return actlist


    def result(self, state, action):
        snake_body = state["snake_body"]
        
        head = snake_body[0]
        
        # new head position
        new_head = [head[0] + action.dir[0], head[1] + action.dir[1]]
        
        if state["snake_traverse"]:
            new_head[0] = new_head[0] % self.dim[0]
            new_head[1] = new_head[1] % self.dim[1]
        
        # for now the snake_body only contains the head
        new_snake_body = [new_head]
        
        # for each body part, we push it to the next position (example, the 
        # part that is closer to the head will have the same position as the old head and so on)
        for i in range(len(snake_body) - 1):
            new_snake_body.append(snake_body[i])
        
        if self.board[new_head[0]][new_head[1]] == FOOD:
            new_snake_body.append(snake_body[-1])
        
        newstate = {
            "snake_body": new_snake_body,
            "snake_traverse": state["snake_traverse"]
        }
        return newstate

    def cost(self, state, action):
        return 1

    def heuristic(self, new_state, goal):
        snake_head = new_state["snake_body"][0]
        snake_traverse = new_state["snake_traverse"]
        
        dx = abs((snake_head[0] - goal[0]))
        dy = abs((snake_head[1] - goal[1]))
        if snake_traverse:
            dx = min(dx, self.dim[0] - dx)
            dy = min(dy, self.dim[1] - dy)
            
        return (dx + dy)

    def satisfies(self, state, goal):
        snake_head = state["snake_body"][0]
        return goal == snake_head

    def get_next_move(self, snake: Snake) -> str:
        state = {
            "snake_body": snake.snake,
            "snake_traverse" : snake.snake_traverse,
        }
        
        problem = SearchProblem(self, state, snake.food_position)
        tree = SearchTree(problem, "greedy")
        result = tree.search()
        if result is None:
            raise Exception("No solution found")
        plan = tree.plan()
        return plan