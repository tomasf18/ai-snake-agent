from tree_search import *
from Directions import DIRECTION
from snake import Snake
import consts
import random

# 'sight': {'45': {'2': 0}, 
            # '46': {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0}, 
            # '47': {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0}, 
            # '0': {'23': 0, '0': 0, '1': 0, '2': 4, '3': 0, '4': 0, '5': 0}, 
            # '1': {'0': 0, '1': 0, '2': 4, '3': 0, '4': 0}, 
            # '2': {'0': 0, '1': 0, '2': 4, '3': 0, '4': 0}, 
            # '3': {'2': 4}}
            



# {'food': [[20, 9, 'SUPER'], [41, 7, 'FOOD'], [10, 1, 'FOOD']], 
# 'players': ['danilo'], 
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
        self.board: list[list[int]] = map["map"]
        self.plan = []
        self.following_plan_to_food = False
        self.foods_in_map = set()

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
        
        goal = None
        food_in_sight = snake.check_food_in_sight()
        
        # for food in food_in_sight:
        #     self.foods_in_map.add(food)
        
        if food_in_sight is not None and not self.following_plan_to_food:
            goal = food_in_sight
            self.create_problem(state, goal)
            self.following_plan_to_food = True
        elif not self.plan:
            goal = self.random_goal_in_map()
            self.create_problem(state, goal)
        
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
    
    def random_goal_in_map(self):
        x = random.randint(0, self.dim[0] - 1)
        y = random.randint(0, self.dim[1] - 1)
        while self.board[x][y] != consts.Tiles.PASSAGE:
            x = random.randint(0, self.dim[0] - 1)
            y = random.randint(0, self.dim[1] - 1)
        return [x, y]