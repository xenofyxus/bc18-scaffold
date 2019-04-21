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
globEnemy = None
workerCount = 0
knightCount = 0
factoryCount = 0
mageCount = 0
rangerCount = 0

class Node(object):

    g = 0
    h = 0
    location = None
    child = None
    parent = None

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
    
    def getParent(self):
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
        return self.g + self.h

def FactoryTree(unit):

    try:

        if len(unit.structure_garrison()) > 0:
            dir = random.choice(directions)
            if(gc.can_unload(unit.id, dir)):
                gc.unload(unit.id, dir)

        elif gc.can_produce_robot(unit.id, bc.UnitType.Knight):
            gc.produce_robot(unit.id, bc.UnitType.Knight)
        
        elif gc.can_produce_robot(unit.id, bc.UnitType.Mage):
            gc.produce_robot(unit.id, bc.UnitType.Mage)

    except Exception as e:
        print('Factory Error:', e)
        traceback.print_exc()

def WorkerTree(unit):
    global workerCount
    try:

        if workerCount < 5:
            dir = None
            for d in directions:
                if gc.can_move(unit.id, d):
                    dir = d
                    continue

            if dir is not None and gc.can_replicate(unit.id, dir):
                gc.replicate(unit.id, dir)
                workerCount = workerCount + 1
        
        else:
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
        traceback.print_exc()


def KnightTree(unit):
    global globEnemy
    try:
        if unit.location.is_in_garrison():
            #print("Im a Knight in a garrison and i need to unload before starting my mission.")
            return
                
        units = gc.sense_nearby_units(unit.location.map_location(), unit.vision_range)
        enemies = []
        for object in units:
            if object.team != my_team:
                enemies.append(object)

        if len(enemies) > 0:
            enemy = ClosestUnit(unit.location.map_location(), enemies)
            globEnemy = enemy
            if gc.can_attack(unit.id, enemy.id) and gc.is_attack_ready(unit.id):
                gc.attack(unit.id, enemy.id)
            
            else:
                if not unit.location.map_location().is_adjacent_to(enemy.location.map_location()):
                    #dir = FindPath(unit.location.map_location(), enemy.location.map_location())
                    dir = FindGreedyPath(unit, enemy)
                    if dir is not None:
                        if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                            
                            location = unit.location.map_location().direction_to(enemy.location.map_location())
                            print("Moving towards ", dir, "we enemy is ", location)
                            gc.move_robot(unit.id, dir)
                        else:
                            print ("Im a Knight boii and cannot move or attack, too tired :(")
                    else:
                        dir = random.choice(directions)
                        if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                            gc.move_robot(unit.id, dir)

        elif globEnemy is not None:
            #if globEnemy.is_on_map():
            #dir = FindPath(unit.location.map_location(), globEnemy.location.map_location())
            dir = FindGreedyPath(unit, globEnemy)
            if dir is not None:
                if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                    gc.move_robot(unit.id, dir)
            else:
                dir = random.choice(directions)
                if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                    gc.move_robot(unit.id, dir)
            
        else:
            dir = random.choice(directions)
            if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)


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
def ClosestUnit(position, units):

    if(len(units) == 0):
        print("No closest unit found, units list is empty. ")
        return None

    minDist = 10000000
    target = None
    for unit in units:
        currentDist = position.distance_squared_to(unit.location.map_location())
        if(currentDist < minDist):
            minDist = currentDist
            target = unit

    return target

def FindGreedyPath(unit, enemy):
    
    unitLocation = unit.location.map_location()
    enemyLocation = enemy.location.map_location()
    bestDir = unitLocation.direction_to(enemyLocation)
    temp = unitLocation.add(bestDir)
    if gc.can_sense_location(temp) and gc.is_occupiable(temp):
        return bestDir

    # If we cant go straight towards our target then we look for 
    # the best possible direction which leads towards the target
    else:
        length = len(directions)
        directionIteration = 0
        for i in range(length):
            if directions[i] == bestDir:
                directionIteration = i
        count = 0
        iter = 1
        while(count < length / 2):
            count = count + 1
            temp = unitLocation.add(directions[(directionIteration + iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp):
                return directions[(directionIteration + iter) % length]
            temp = unitLocation.add(directions[(directionIteration - iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp):
                return directions[(directionIteration - iter) % length]
            iter = iter + 1

def FindPath(start, goal):

    closed = []
    open = []
    startNode = Node(start)
    nodes = [startNode]
    open.append(start)
    count = 0

    while len(open) > 0:
        count += 1
        currentNode = GetNode(open[0], nodes)

        for i in nodes: 
            if i.cost() < currentNode.cost() or (i.cost() == currentNode.cost() and i.gethCost() < currentNode.gethCost()):
                currentNode = i

        open.remove(currentNode.getLocation())
        closed.append(currentNode.getLocation())

        if currentNode.getLocation().is_adjacent_to(goal):
            loc = startNode.getLocation()
            #print("Path found after ", count, " iterations")
            return loc.direction_to(startNode.getChild().getLocation())

        for loc in GetNeighbours(currentNode.getLocation()):
            if closed.count(loc) > 0:
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

            elif cost < GetNode(loc, nodes).getgCost():
                node = GetNode(loc, nodes)
                currentNode.setChild(node)
                node.setParent(currentNode)
                node.setgCost = cost
                node.sethCost = GetDistance(loc, goal)
    
    #print("No path could be found after ", count, " iterations")

    
def GetNeighbours(location):
    
    neighbours = [] 
    for dir in directions:
        temp = location.add(dir)
        if gc.can_sense_location(temp):
            if gc.is_occupiable(temp):
                neighbours.append(temp)
    
    return neighbours
            
def GetDistance(current, goal):
    distance = current.distance_squared_to(goal)
    return distance

def GetNode(location, nodes):
    for node in nodes:
        if node.getLocation() == location:
            return node

def Path (start, goal):

    currentNode = goal
    newPath = []
    while(currentNode.getLocation() != start.getLocation() or currentNode == None):
        print("calculating path")
        newPath.append(currentNode)
        currentNode = currentNode.getParent()
    
    newPath = newPath.reverse()
    return newPath[0].getLocation()


while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')

    # frequent try/catches are a good idea
    try:
        #First we count our units
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Factory:
                factoryCount += 1
            elif unit.unit_type == bc.UnitType.Worker:
                workerCount += 1
            elif unit.unit_type == bc.UnitType.Knight:
                knightCount += 1
            elif unit.unit_type == bc.UnitType.Mage:
                mageCount += 1
            elif unit.unit_type == bc.UnitType.Ranger:
                rangeCount += 1

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


