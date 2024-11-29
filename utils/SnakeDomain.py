import math
import pprint
from utils.multi_objective_search import MultiObjectiveSearch
from utils.tree_search import *
from utils.Directions import DIRECTION
from utils.snake import Snake
import time
import datetime
import consts
import random

import logging

logging.basicConfig(
    filename='project.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
EATING_SUPERFOOD = True

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
        self.multi_objectives = MultiObjectiveSearch([])

        # Debugging
        self.maxDist = 0


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
            
            if new_position in snake_body :#or tuple(new_position) in self.super_foods_in_map:
                continue

            sight = state["snake_sight"]
            for row, cols in sight.items():
                for col, value in cols.items():
                    if value == consts.Tiles.SNAKE:
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
            "snake_traverse": state["snake_traverse"],
            "snake_sight": state["snake_sight"],
            "objectives": [] if not state["objectives"] else state["objectives"] if new_head != state["objectives"][0] else state["objectives"][1:]
        }
        logging.info(f"New state in result function: {newstate}")
        return newstate

    def cost(self, state, action):
        return 1

    def heuristic(self, new_state, goal):
        snake_head = new_state["snake_body"][0]
        snake_traverse = new_state["snake_traverse"]
        objectives = new_state["objectives"]
        
        
        if objectives:
            logging.info(f"Objectives in heuristic function: {objectives}")
            return self.calculateDistance(snake_head, objectives[0], snake_traverse)
        else:
            logging.info(f"There are no ojectives, returning distance to goal: {goal}")
            return self.calculateDistance(snake_head, goal, snake_traverse)

    def calculateDistance(self, start, end, snake_traverse):
        dx = abs((end[0] - start[0]))
        dy = abs((end[1] - start[1]))
        if snake_traverse:
            dx = min(dx, self.dim[0] - dx)
            dy = min(dy, self.dim[1] - dy)

        return (dx + dy)

    def satisfies(self, state, goal):
        snake_head = state["snake_body"][0]
        logging.info(f"VERIFYING IF snake_head == goal: snake_head: {snake_head}, goal: {goal}")
        return goal == snake_head

    def get_next_move(self, snake: Snake) -> str:
        """Returns the next move to be taken by the snake"""
        
        logging.info("\tgetNextMove: Started computing...")
        ti: float = time.time()
        
        state = {
            "snake_body": snake.snake,
            "snake_traverse" : snake.snake_traverse,
            "snake_sight" : snake.snake_sight,
            "objectives" : self.multi_objectives.get_list_of_objectives()
        }
        
        # 1. Update the map removing the snake sight
        self.updateMapCopy(state["snake_sight"])
        
        # 2. Add new known foods
        foods_in_sight, super_foods_in_sight = snake.check_food_in_sight()
        
        for food in foods_in_sight:
            if list(food) not in self.multi_objectives.objectives:
                self.foods_in_map.add(food)
        
        for super_food in super_foods_in_sight:
            if list(super_food) not in self.multi_objectives.objectives:
                self.super_foods_in_map.add(super_food)
                
        
        logging.info(f"Foods in map: {self.foods_in_map}")
        logging.info(f"Board copy: {self.board_copy}")
        
        head = state["snake_body"][0]

        # If there are foods in the map
        if ((normal_food := len(self.foods_in_map) > 0) or (EATING_SUPERFOOD and len(self.super_foods_in_map) > 0)) and not self.following_plan_to_food:
            ## Meter para ignorar superfood de alguma maneira
            # first objective (food)
            goal = list(min(
                self.foods_in_map if normal_food else self.super_foods_in_map, 
                key=lambda pos: self.calculateDistance(head, pos, snake_traverse=state["snake_traverse"])
            ))
            
            # clear the list of objectives
            self.multi_objectives.clear_goals()
            
            for point in self.create_list_objectives(state, goal):
                self.multi_objectives.add_goal(point)

            logging.info(f"Food Position: {goal}")
            self.create_problem(state)
            self.following_plan_to_food = True

        # If there are no objectives
        elif self.multi_objectives.is_empty():
            random_point = self.closest_unknown_position(state)
            for point in self.create_list_objectives(state, random_point):
                self.multi_objectives.add_goal(point)
            
            self.create_problem(state)

        # if the snake has reached the goal
        elif head == self.multi_objectives.get_next_goal():

            # If following plan to food, update the map_positions_copy
            if self.following_plan_to_food:
                self.foods_in_map.discard(tuple(head))
                self.super_foods_in_map.discard(tuple(head))

                self.map_positions_copy = self.map_positions.copy()
                self.following_plan_to_food = False
                
            # Remove the goal from the list of objectives
            self.multi_objectives.remove_next_goal()
            
            # Create a new objective
            goal_list = self.multi_objectives.get_list_of_objectives()
            new_goal = self.create_list_objectives(state, goal_list[0], goal_list[1])[-1]
            self.multi_objectives.add_goal(new_goal)

            # Create a new problem
            self.create_problem(state)
        
        move = self.plan.pop(0)
        
        ## Panic move
        if (move not in (valid_moves:=self.actions(state))):
            move = random.choice(valid_moves)
            self.plan = []

        # ======================== DEBUG ========================
        print(f"\n\n{self.map_positions_copy}")
        tf: float = time.time()
        dt: float = tf - ti 
        diff_to_server = tf - datetime.datetime.fromisoformat(snake.timestamp).timestamp()
        if (diff_to_server > self.maxDist):
            self.maxDist = diff_to_server
        logging.error(
            "\tgetNextMove time to compute %.2fms (diff to server %.2fms (max diff %.2fms))",
                dt*1000,
                diff_to_server*1000,
                self.maxDist*1000
        )
        # ======================== DEBUG ========================

        return move.key
    
    def create_problem(self, state, goal = None):
        objectives = self.multi_objectives.get_list_of_objectives()
        state["objectives"] = objectives[:-1]
        goal = list(objectives[-1])
        problem = SearchProblem(self, state, goal)
        tree = SearchTree(problem, "greedy")
        result = tree.search(timeout=0.01)
        if result is None:
            logging.error(f"No solution found, goal: {goal}, state: {state}")
            valid_moves = self.actions(state)
            if valid_moves:
                self.plan = [random.choice(valid_moves)]
            else:
                raise Exception("No valid moves")
        else:
            self.plan = tree.plan()
        logging.info(f"Plan: {self.plan}")
    
    def closest_unknown_position(self, state):
        head = state["snake_body"][0]
        traverse = state["snake_traverse"]
        sight = state["snake_sight"]

        if len(self.map_positions_copy) == 0:
            self.updateMapCopy(sight, refresh=True)

        minPos = min(
            self.map_positions_copy, 
            key=lambda pos: self.calculateDistance(head, pos, traverse)
        )

        return minPos


    def updateMapCopy(self, sight, refresh = False):
        if refresh:
            self.map_positions_copy = self.map_positions.copy()

        for row, cols in sight.items():
            for col, value in cols.items():
                self.map_positions_copy.discard((int(row), int(col)))

    def create_list_objectives(self, state, goal: tuple[int, int], intermediary: tuple[int, int] = None) -> list[tuple[int, int]]:  
        """"Returns a list of objectives to be achieved"""    
        half_snake_size = max(3, len(state["snake_body"])/2)
        width = self.dim[0]
        height = self.dim[1]

        x_1, y_1 = intermediary if intermediary is not None else (None, None)

        if intermediary is None:
            # Random number between 0º and 360º 
            theta1 = random.random() * 2 * math.pi
            x_1 = ( goal[0] + int( half_snake_size * math.cos(theta1)) ) % width
            y_1 = ( goal[1] + int( half_snake_size * math.sin(theta1)) ) % height
        else:
            theta1 = math.atan2(y_1 - goal[1], x_1 - goal[0])

        # Random number between 45º and 315º 
        theta2 = math.pi/4 + random.random() * ( 2 * math.pi - math.pi / 2)
        x_2 = ( x_1 + int( half_snake_size * math.cos(theta2)) ) % width 
        y_2 = ( y_1 + int( half_snake_size * math.sin(theta2)) ) % height

        logging.info(f"Objectives: {goal}, {x_1, y_1}, {x_2, y_2}")

        return [goal, [x_1, y_1], [x_2, y_2]]
