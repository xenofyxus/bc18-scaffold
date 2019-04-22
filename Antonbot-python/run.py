import battlecode as bc
import random
import sys
import traceback
import time
import os


def FactoryTree(unit):
    global workerCount
    global knightCount
    global mageCount
    global rangerCount
    try:
        unitTotal = workerCount + knightCount + mageCount + rangerCount
        workerPercent = workerCount/unitTotal
        knightPercent = knightCount/unitTotal
        magePercent = mageCount/unitTotal
        rangerPercent = rangerCount/unitTotal

        workerTargetPercent = 0.05
        knightTargetPercent = 0.45
        mageTargetPercent = 0.50
        rangerTargetPercent = 0

        if len(unit.structure_garrison()) > 0:
            for dir in directions:
                if(gc.can_unload(unit.id, dir)):
                    gc.unload(unit.id, dir)
                    break
        if(knightPercent < knightTargetPercent):
            if gc.can_produce_robot(unit.id, bc.UnitType.Knight):
                gc.produce_robot(unit.id, bc.UnitType.Knight)
        
        elif(magePercent < mageTargetPercent):
            if gc.can_produce_robot(unit.id, bc.UnitType.Mage):
                gc.produce_robot(unit.id, bc.UnitType.Mage)
        
        elif(rangerPercent < rangerTargetPercent):
            if gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                gc.produce_robot(unit.id, bc.UnitType.Ranger)

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
                    break

            if dir is not None and gc.can_replicate(unit.id, dir):
                gc.replicate(unit.id, dir)
                workerCount = workerCount + 1

        nearbyBuildings = gc.sense_nearby_units_by_type(unit.location.map_location(), 2, bc.UnitType.Factory)
        closestKarb = ClosestLocation(unit.location.map_location(), karbLocations)
        dir = FindGreedyPathToLoc(unit, closestKarb)

        for object in nearbyBuildings:
            # If we find a strucure to build on, we dont want to move.
            if gc.can_build(unit.id, object.id) and not object.structure_is_built():
                gc.build(unit.id, object.id)
                break

        if unit.location.map_location().is_adjacent_to(closestKarb.location.map_location):
            for tempDir in directions:
                if(gc.can_harvest(unit.id, tempDir)):
                    gc.harvest(unit.id, tempDir)
                    break

        if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
            gc.move_robot(unit.id, dir)
             
        if gc.can_blueprint(unit.id, bc.UnitType.Factory, dir):
            gc.blueprint(unit.id, bc.UnitType.Factory, dir)

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
                            print("Im a Knight boii and cannot move or attack, too tired :(")
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
    dir = random.choice(directions)

    try:
        if(unit.location.is_in_garrison() is True):
            print("Im a mage in a garrison and i need to unload before starting my mission.")
            return

        FindAndAttack(unit)
        
        if(gc.is_move_ready(unit.id)):
            gc.move_robot(unit.id, dir)
            print("Im a mage on a mission to find enemies.")
            FindAndAttack(unit)
        else:
            print("I need to rest to continue my mission.")
        
    except Exception as e:
        print('Mage Error:', e)
        # use this to show where the error was
        traceback.print_exc()


def FindAndAttack(unit):
    global globEnemy
    nearby = gc.sense_nearby_units(unit.location.map_location(), unit.vision_range)
    enemies = []

    # Very wierd way of checking teams. didnt find an smarter atm.
    for other in nearby:
        if(other.team != gc.team()):
            enemies.append(other)
    if(len(enemies) > 0):
        enemy = ClosestUnit(unit.location.map_location(), enemies)
        dir = FindGreedyPath(unit, enemy)
        if(gc.can_attack(unit.id, enemy.id) and gc.is_attack_ready(unit.id)):
            gc.attack(unit.id, enemy.id)
            print("Im a mage and i just attacked unit: ", enemy)
        if(gc.can_attack(unit.id, enemy.id) and not gc.is_attack_ready(unit.id)):
            print("Im a mage and i need to rest to attack again, getting out of here. ")
            # TODO: Run to closest factory.
            if(gc.is_move_ready(unit.id)):
                gc.move_robot(unit.id, dir)
            else:
                print("Im a mage but im too tired to move or attack.")
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

def RangerTree(unit):

    try:
        print("I am a Ranger")

    except Exception as e:
        print('Ranger Error:', e)
        # use this to show where the error was
        traceback.print_exc()


# returns the unit in the list units closest to the position specified
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


def ClosestLocation(position, locations):

    if(len(locations) == 0):
        print("No closest location found, locations list is empty. ")
        return None

    minDist = 10000000
    target = None
    for location in locations:
        currentDist = position.distance_squared_to(location)
        if(currentDist < minDist):
            minDist = currentDist
            target = unit

    return target


def GetCarbs():    
    global karbLocations
    for i in range(map.width):
        for j in range(map.height):
            location = bc.MapLocation(bc.Planet.Earth, i, j)
            if map.initial_karbonite_at(location):
                karbLocations.append(location)


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


def FindGreedyPathToLoc(unit, location):
    
    unitLocation = unit.location.map_location()
    bestDir = unitLocation.direction_to(location)
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

print(os.getcwd())

print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)

print("pystarted")

# It's a good idea to try to keep your bots deterministic, 
# to make debugging easier.
# determinism isn't required, but it means that the same things will happen 
# in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Mage)

my_team = gc.team()
map = gc.starting_map(gc.planet())
karbLocations = []
globEnemy = None
workerCount = 0
knightCount = 0
factoryCount = 0
mageCount = 0
rangerCount = 0
if(gc.planet() == bc.Planet.Earth):
    GetCarbs()

while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')

    # frequent try/catches are a good idea

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
            rangerCount += 1

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

