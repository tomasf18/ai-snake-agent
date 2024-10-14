from tree_search import *
from snake import Snake
DIRECTIONS = [ (1, 0), (-1, 0), (0, 1), (0, -1) ] # right, left, up, down

class SnakeDomain(SearchDomain):    
    def __init__(self, map: dict):
        self.dim: tuple[int, int] = tuple(map["size"])
        self.board: list[list[int]] = map["map"]

    def actions(self, current_position):
        """
            Podemos ir na direçao com espaços vazios
            [
                X + X 
                + H |
                X B X
            ]
        """
        actlist = []
        for dir in DIRECTIONS:
            checkbox = [current_position[0] + dir[0], current_position[1] + dir[1]]
            if checkbox in self.snake.body:
                continue

            if self.snake.transverse or \
                self.board[checkbox[0]][checkbox[1]] == 0:
                actlist.append(checkbox)

        return actlist


    def result(self, current_position, action):
        return action
    
    # def result(self, state, action):
    #     if all(pc in state for pc in action.pc):
    #         newstate = [s for s in state if s not in action.neg]
    #         # Do estado atual, nao quero as que nao ajudam a ir na direçao
    #         # E quero as que ajudam
    #         newstate.extend(action.pos)
    #         return set(newstate)

    def cost(self, square, action):
        return 1

    def heuristic(self, current_position, food_position):
        return abs((current_position[0] - food_position[0])) + abs((current_position[1] - food_position[1]))

    def satisfies(self, current_position, food_position):
        return food_position == current_position

    def get_next_move(self) -> str:
        p = SearchProblem(self, self.snake.head, self.snake.food_position)
        t = SearchTree(p, "a*")
        t.search()
        return t.get_path()[0]