from tree_search import *
from Directions import DIRECTION
from snake import Snake
import consts
import random

import logging

logging.basicConfig(
    filename='project.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# {'players': ['danilo'], 
# 'step': 274, 
# 'timeout': 3000, 
# 'ts': '2024-10-22T14:13:33.345679', 
# 'name': 'danilo', 
# 'body': [[21, 12], [22, 12], [22, 11], [22, 10], [22, 9], [23, 9], [24, 9], [25, 9], [26, 9], [27, 9], [28, 9], [29, 9], [30, 9], [31, 9], [32, 9]], 
# 'sight': {'18': {'12': 0}, '19': {'10': 0, '11': 0, '12': 0, '13': 0, '14': 0}, '20': {'10': 0, '11': 0, '12': 0, '13': 0, '14': 0}, '21': {'9': 1, '10': 1, '11': 1, '12': 4, '13': 0, '14': 0, '15': 0}, '22': {'10': 4, '11': 4, '12': 4, '13': 0, '14': 0}, '23': {'10': 0, '11': 0, '12': 0, '13': 0, '14': 0}, '24': {'12': 0}}, 
# 'score': 13, 
# 'range': 3, 
# 'traverse': False}

class SnakeDomain(SearchDomain):    
    def __init__(self, map: dict):
        self.dim: tuple[int, int] = tuple(map["size"])
        self.time_per_frame: float = 1 / int(map["fps"])
        self.board: list[list[int]] = map["map"]
        self.board_copy: list[list[int]] = map["map"]
        self.map_positions: set = set()
        self.map_positions_copy: set = set()
        self.plan = []
        self.following_plan_to_food = False
        self.foods_in_map: set = set()
        self.super_foods_in_map: set = set()
        self.goal = None


    async def startupMap(self):
        for x in range(self.dim[0]):
            for y in range(self.dim[1]):
                if self.board[x][y] != consts.Tiles.STONE:
                    self.map_positions.add((x, y))
                    self.map_positions_copy.add((x, y))
                if self.board[x][y] == consts.Tiles.FOOD:
                    self.foods_in_map.add((x, y))
        

    def actions(self, state) -> list[DIRECTION]:
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
            
            if new_position in snake_body or tuple(new_position) in self.super_foods_in_map:
                continue

            if snake_traverse or self.board[new_position[0]][new_position[1]] != consts.Tiles.STONE:
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
        
        if self.board[new_head[0]][new_head[1]] == consts.Tiles.FOOD:
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
        
        snake_sight = snake.snake_sight
        for row, cols in snake_sight.items():
            for col, value in cols.items():
                self.map_positions_copy.discard((int(row), int(col)))
        
        foods_in_sight, super_foods_in_sight = snake.check_food_in_sight()
        
        for food in foods_in_sight:
            if list(food) != self.goal:
                self.foods_in_map.add(food)
        
        for super_food in super_foods_in_sight:
            self.super_foods_in_map.add(super_food)
            self.map_positions.discard(super_food)
        
        logging.info(f"Foods in map: {self.foods_in_map}")
        logging.info(f"Board copy: {self.board_copy}")
        
    
        if len(self.foods_in_map) > 0 and not self.following_plan_to_food:
            self.goal = list(self.foods_in_map.pop()) 
            logging.info(f"Goal: {self.goal}")
            self.create_problem(state, self.goal)
            self.following_plan_to_food = True
        elif not self.plan:
            self.goal = list(self.random_goal_in_map())
            self.create_problem(state, self.goal)
        
        move = self.plan.pop(0)
        if (move not in self.actions(state)):
            self.create_problem(state, self.goal)
            move = self.plan.pop(0)
        if not self.plan:
            self.following_plan_to_food = False
        key = move.key

        return key
    
    def create_problem(self, state, goal):
        problem = SearchProblem(self, state, goal)
        tree = SearchTree(problem, "greedy")
        result = tree.search()
        if result is None:
            raise Exception("No solution found")
        self.plan = tree.plan()
        logging.info(f"Plan: {self.plan}")
    
    def random_goal_in_map(self):
        if len(self.map_positions_copy) == 0:
            self.map_positions_copy = self.map_positions.copy()
        return self.map_positions_copy.pop()