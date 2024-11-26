from collections import deque

# ================ Objectives Explanation ================

# the objectives queue is a list of objectives like this:
# [X, Y, Z]
# we pass this queue to the search method saying that we want to achieve Z
# and the path from snake_head to Z must contain X and Y
# when we achieve X, we remove it from the queue and add a new objective like:
# [Y, Z, W]
# now the objective is to achieve W and the path from snake_head to W must contain Y and Z
# and so on...

# when a food or super_food apears in the map, we add it to the objectives queue
# now the queue is like this:
# [FOOD, NewObjective1, NewObjective2]

class MultiObjectiveSearch:
    def __init__(self, objectives = list()):
        self.objectives = deque(objectives)

    def remove_next_goal(self):
        """"Removes the next goal from the list of objectives"""
        self.objectives.popleft() 

    def get_next_goal(self):
        """Returns the first goal in the list of objectives"""
        return self.objectives[0]

    def get_list_of_objectives(self):
        """Returns the list of objectives"""
        return list(self.objectives)

    def add_goal(self, goal):
        """Adds a new goal to the list of objectives"""
        self.objectives.append(goal)
        
    def clear_goals(self):
        self.objectives.clear()

    def is_empty(self):
        """Returns True if there are no more objectives to be achieved"""
        return not self.objectives