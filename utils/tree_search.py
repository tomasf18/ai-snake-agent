import time
import logging

logging.basicConfig(
    filename='project.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

from abc import ABC, abstractmethod


# Dominios de pesquisa
# Permitem calcular
# as accoes possiveis em cada estado, etc
class SearchDomain(ABC):
    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # lista de accoes possiveis num estado
    @abstractmethod
    def actions(self, state):
        pass

    # resultado de uma accao num estado, ou seja, o estado seguinte
    @abstractmethod
    def result(self, state, action):
        pass

    # custo de uma accao num estado
    @abstractmethod
    def cost(self, state, action):
        pass

    # custo estimado de chegar de um estado a outro
    @abstractmethod
    def heuristic(self, state, goal):
        pass

    # test if the given "goal" is satisfied in "state"
    @abstractmethod
    def satisfies(self, state, goal):
        pass


# Problemas concretos a resolver
# dentro de um determinado dominio
class SearchProblem:
    def __init__(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal

    def goal_test(self, state):
        return self.domain.satisfies(state, self.goal)


# Nos de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent, cost, heuristic, action=None):
        self.state = state
        self.parent = parent
        self.depth = (parent.depth + 1) if parent is not None else 0
        self.cost = cost
        self.heuristic = heuristic
        self.action = action

    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + "," + str(self.depth) + str(self.cost) + str(self.heuristic) + ")"

    def __repr__(self):
        return str(self)

    def in_parent(self, newstate):
        if self.parent is None:
            return False
        if self.parent.state == newstate:
            return True
        return self.parent.in_parent(newstate)


# Arvores de pesquisa
class SearchTree:
    # construtor
    def __init__(self, problem, strategy="breadth"):
        self.problem = problem
        root = SearchNode(
            problem.initial,
            None,
            0,
            self.problem.domain.heuristic(self.problem.initial, self.problem.goal),
        )
        self.open_nodes = [root]
        self.strategy = strategy
        self.solution: SearchNode | None = None
        self.non_terminals = 0
        self.highest_cost_nodes = [root]
        self.sum_depths = 0

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self, node):
        if node.parent is None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return path

    def path(self):
        return self.get_path(self.solution)
    
    def plan(self):
        return self.get_plan(self.solution)

    def get_plan(self, node):
        if node.parent is None:
            return []
        plan = self.get_plan(node.parent)
        plan += [node.action]
        return plan
    
    @property
    def average_depth(self):
        return self.sum_depths / (self.terminals + self.non_terminals - 1)

    @property
    def length(self):
        return self.solution.depth if self.solution else 0

    @property
    def terminals(self):
        return len(self.open_nodes) + 1

    @property
    def avg_branching(self):
        return (self.non_terminals + self.terminals - 1) / self.non_terminals

    @property
    def cost(self):
        return self.solution.cost if self.solution else None

    # procurar a solucao
    def search(self, limit=None, timeout=None):
        logging.info("Searching Method (Tree search)")
        logging.info("\tStarting search with snake_body: " + str(self.problem.initial["snake_body"]) + " and goal: " + str(self.problem.goal))
        
        start_time = time.time()
        
        while self.open_nodes != []:
            
            # logging.info(f"\tTIMEOUT TIME: {(time.time() - start_time) * 1000} ms")
            if timeout and (time.time() - start_time) > timeout:
                logging.info("Timeout reached")
                return None
            
            node = self.open_nodes.pop(0)
            self.non_terminals += 1
            if self.problem.goal_test(node.state):
                self.non_terminals -= 1
                self.solution = node
                return self.get_path(node)

            if limit is not None and node.depth >= limit:
                continue

            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state, a)
                if node.in_parent(newstate):
                    continue

                cost = node.cost + self.problem.domain.cost(node.state, a)
                newnode = SearchNode(
                    newstate,
                    node,
                    cost,
                    self.problem.domain.heuristic(newstate, self.problem.goal),
                    a
                )
                lnewnodes.append(newnode)

                self.sum_depths += newnode.depth

                if newnode.cost > self.highest_cost_nodes[0].cost:
                    self.highest_cost_nodes = [newnode]
                elif newnode.cost == self.highest_cost_nodes[0].cost:
                    self.highest_cost_nodes.append(newnode)

            self.add_to_open(lnewnodes)
        return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self, lnewnodes):
        if self.strategy == "breadth":
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == "depth":
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == "uniform":
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost)
        elif self.strategy == "greedy":
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.heuristic)
        elif self.strategy == "a*":
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.heuristic + node.cost)