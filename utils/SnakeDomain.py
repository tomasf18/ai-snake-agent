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
        
        # TODO: Delete this line
        self.goal = None

        # TODO: Delete this line
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
            # TODO alterar state -> adicionar objetivos
        }
        return newstate

    def cost(self, state, action):
        return 1

    def heuristic(self, new_state, goal):
        # TODO verificar pelos objetivos
        snake_head = new_state["snake_body"][0]
        snake_traverse = new_state["snake_traverse"]
        
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
        return goal == snake_head

    def get_next_move(self, snake: Snake) -> str:
        """Returns the next move to be taken by the snake"""
        
        logging.info("\tgetNextMove: Started computing...")
        ti: float = time.time()
        
        state = {
            "snake_body": snake.snake,
            "snake_traverse" : snake.snake_traverse,
            "snake_sight" : snake.snake_sight,
            "objectives" : None, # Alterar para ter objetivos
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

            if not EATING_SUPERFOOD:
                self.map_positions.discard(super_food)
                
        
        logging.info(f"Foods in map: {self.foods_in_map}")
        logging.info(f"Board copy: {self.board_copy}")
        
        head = state["snake_body"][0]

        # Se existe foods conhecidas
        if len(self.foods_in_map) > 0 and not self.following_plan_to_food:
            self.goal = list(min(
                self.foods_in_map, 
                key=lambda pos: self.calculateDistance(head, pos, snake_traverse=state["snake_traverse"])
            ))
            self.foods_in_map.discard(tuple(self.goal))

            logging.info(f"Goal: {self.goal}")
            # TODO: 
            # self.multi_objectives.

            self.create_problem(state, self.goal)
            self.following_plan_to_food = True

        # Se existe superfoods conhecidas
        elif (self.super_foods_in_map) > 0:
            self.goal = list(min(
                self.super_foods_in_map, 
                key=lambda pos: self.calculateDistance(head, pos, snake_traverse=state["snake_traverse"])
            ))
            self.super_foods_in_map.discard(tuple(self.goal))

            logging.info(f"Goal: {self.goal}")
            self.create_problem(state, self.goal)

        # Se nao há objetivos
        elif self.multi_objectives.is_empty():
            random_point = self.random_goal_in_map(state)
            for point in self.create_list_objectives(state, random_point):
                self.multi_objectives.add_goal(point)
            
            # TODO: Create problem

        # Se chegou ao objetivo
        elif head == self.multi_objectives.get_next_goal():
            # Eliminar o objetivo atual
            self.multi_objectives.remove_next_goal()
            
            # Criar um novo objetivo a visitar TODO: fazer do genero do que fi<emos la em baixo
            new_goal = self.random_goal_in_map(state)
            self.multi_objectives.add_goal(new_goal)

            # Criar um problema com o proximo objetivo
            self.create_problem(state)
        
        move = self.plan.pop(0)
        ## Panic move
        if (move not in (valid_moves:=self.actions(state))):
            move = random.choice(valid_moves)
            self.plan = []

        if self.following_plan_to_food and not self.plan:
            self.map_positions_copy = self.map_positions.copy()
            self.following_plan_to_food = False
        key = move.key

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

        return key
    
    def create_problem(self, state, goal = None):
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
    
    def random_goal_in_map(self, state):
        head = state["snake_body"][0]
        traverse = state["snake_traverse"]
        sight = state["snake_sight"]

        if len(self.map_positions_copy) == 0:
            self.updateMapCopy(sight, refresh=True)

        minPos = min(
            self.map_positions_copy, 
            key=lambda pos: self.calculateDistance(head, pos, traverse)
        )

        self.map_positions_copy.discard(minPos)
        return tuple(minPos)


    def updateMapCopy(self, sight, refresh = False):
        if refresh:
            self.map_positions_copy = self.map_positions.copy()

        for row, cols in sight.items():
            for col, value in cols.items():
                self.map_positions_copy.discard((int(row), int(col)))

    def create_list_objectives(self, state, goal):
        """"Returns a list of objectives to be achieved"""    
        half_snake_size = len(state["snake_body"])/2
        width = self.dim[0]
        height = self.dim[1]

        # Random number between 0º and 360º 
        theta1 = random.random() * 2 * math.pi
        x_1 = ( goal[0] + int( half_snake_size * math.cos(theta1)) ) % width
        y_1 = ( goal[1] + int( half_snake_size * math.sin(theta1)) ) % height

        # Random number between 45º and 315º 
        theta2 = math.pi/4 + random.random() * ( 2 * math.pi - math.pi / 2)
        x_2 = ( x_1[0] + int( half_snake_size * math.cos(theta2)) ) % width 
        y_2 = ( y_1[1] + int( half_snake_size * math.sin(theta2)) ) % height

        return [goal, (x_1, y_1), (x_2, y_2)]
