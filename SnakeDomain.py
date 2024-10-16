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
            
            if new_position in snake_body:
                continue
            
            if snake_traverse or self.board[new_position[0]][new_position[1]] == WALL:
                actlist.append(dir)

        return actlist


    def result(self, state, action):
        snake_body = state["snake_body"]
        
        head = snake_body[0]
           
        snake_body[0:0] = [action + head]
        if self.board[head[0]][head[1]] != FOOD:
            snake_body.pop()
        
        return { 
            "snake_body": snake_body, 
            "snake_traverse": state["snake_traverse"]
        }

    def cost(self, state, action):
        return 1

    def heuristic(self, new_state, goal):
        snake_head = new_state["snake_body"][0]
        return abs((snake_head[0] - goal[0])) + \
               abs((snake_head[1] - goal[1]))

    def satisfies(self, state, goal):
        snake_head = state["snake_body"][0]
        return goal == snake_head

    def get_next_move(self, snake: Snake) -> str:
        state = {
            "snake_body": snake.snake,
            "snake_traverse" : snake.snake_traverse,
        }
        
        print("DEBUG: ", state)
        
        problem = SearchProblem(self, state, snake.food_position)
        print("DEBUG: ", problem.initial, problem.goal)
        tree = SearchTree(problem, "a*")
        result = tree.search()
        if result is None:
            raise Exception("No solution found")
        return tree.plan()[0]