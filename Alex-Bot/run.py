import battlecode as bc
import random
import sys
import traceback
import time
import os
print(os.getcwd())


# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)

my_team = gc.team()


def FactoryTree(unit):

    try:

        if len(unit.structure_garrison()) > 0:
            dir = random.choice(directions)
            if(gc.can_unload(unit.id, dir)):
                gc.unload(unit.id, dir)

        elif gc.can_produce_robot(unit.id, bc.UnitType.Mage):
            gc.produce_robot(unit.id, bc.UnitType.Mage)

    except Exception as e:
        print('Factory Error:', e)
        # use this to show where the error was
        traceback.print_exc()

def WorkerTree(unit):

    try:

        nearbyObjects = gc.sense_nearby_units(unit.location.map_location(), 2)
        dir = random.choice(directions)

        for object in nearbyObjects:
            if gc.can_build(unit.id, object.id):
                gc.build(unit.id, object.id)
                continue
        
        if gc.can_blueprint(unit.id, bc.UnitType.Factory, dir):
            gc.blueprint(unit.id, bc.UnitType.Factory, dir)

        elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
            gc.move_robot(unit.id, dir)

    except Exception as e:
        print('Worker Error:', e)
        # use this to show where the error was
        traceback.print_exc()


def KnightTree(unit):

    try:

        print("I am a Knight")

    except Exception as e:
        print('Knight Error:', e)
        # use this to show where the error was
        traceback.print_exc()


def MageTree(unit):

    try:

        print("I am a Mage")

    except Exception as e:
        print('Mage Error:', e)
        # use this to show where the error was
        traceback.print_exc()


def RangerTree(unit):

    try:

        print("I am a Ranger")

    except Exception as e:
        print('Ranger Error:', e)
        # use this to show where the error was
        traceback.print_exc()


print("pystarting")


def FindPath(start, goal):

    closed = []
    open = []
    startNode = Node(start)
    nodes = [startNode]
    open.append(start)

    while len(open) > 0:
        currentNode = open[0]

    for i in open: #Fixa detta med loc/nodes
        if i.cost() < currentNode.cost() or (i.cost() == currentNode.cost() and i.gethCost() < currentNode.gethCost()):
            currentNode = i

    open.remove(currentNode.getLocation())
    closed.append(currentNode.getLocation())

    if currentNode.getLocation() == goal:
        return Path(startNode, currentNode)
    
    for loc in GetNeighbours(currentNode.getLocation()):
        if (not gc.can_move(loc)) or closed.count(loc) > 0:
            continue
        
        cost = currentNode.getgCost() + GetDistance(currentNode.getLocation(), loc)

        if open.count(loc) == 0:
            new = Node(loc)
            nodes.append(new)
            currentNode.setChild(new)
            new.setParent(currentNode)
            new.setgCost = cost
            new.sethCost = GetDistance(loc, goal)
            open.append(loc)

        elif cost < GetNode(loc, nodes).getgCost:
            node = GetNode(loc, nodes)
            currentNode.setChild(node)
            node.setParent(currentNode)
            node.setgCost = cost
            node.sethCost = GetDistance(loc, goal)

    
def GetNeighbours(location):
    
    neighbours = [] 
    for dir in directions:
        temp = location.add(dir)
        if gc.can_move(temp):
            neighbours.append(temp)
    
    return neighbours
            
def GetDistance(current, goal):
    return current.distance_squared_to(goal)

def GetNode(location, nodes):
    for node in nodes:
        if node.getLocation() == location:
            return node

def Path (start, goal):

    return start


while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')

    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():

            # first, factory logic
            if unit.unit_type == bc.UnitType.Factory:
                FactoryTree(unit)

            elif unit.unit_type == bc.UnitType.Worker:
                WorkerTree(unit)

            elif unit.unit_type == bc.UnitType.Knight:
                KnightTree(unit)

            elif unit.unit_type == bc.UnitType.Mage:
                MageTree(unit)

            elif unit.unit_type == bc.UnitType.Ranger:
                RangerTree(unit)    
                

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()


class Node(object):
    def __init__ (self, location):
        self.location = location

    def getLocation(self):
        return self.location

    def setChild(self, child):
        self.child = child

    def getChild(self):
        return self.child
    
    def setParent(self, parent):
        self.parent = parent
    
    def getParent(self, parent):
        return self.parent

    def sethCost(self, h):
        self.h = h

    def gethCost(self):
        return self.h

    def setgCost(self, g):
        self.g = g

    def getgCost(self):
        return self.g

    def cost(self):
        return g + h

