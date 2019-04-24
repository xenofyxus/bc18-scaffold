import battlecode as bc
import random
import sys
import traceback
import time
import os

def FactoryTree(unit):
    global knightCount
    global mageCount
    global rangerCount
    global workerCount
    global knightTargetPercent
    global mageTargetPercent
    global rangerTargetPercent

    try:
        unitTotal = workerCount + knightCount + mageCount + rangerCount
        knightPercent = knightCount/unitTotal
        magePercent = mageCount/unitTotal
        rangerPercent = rangerCount/unitTotal

        if len(unit.structure_garrison()) > 0:
            for dir in directions:
                if(gc.can_unload(unit.id, dir)):
                    gc.unload(unit.id, dir)

                    break

        if (workerCount < 1):
            if gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                gc.produce_robot(unit.id, bc.UnitType.Worker)

        elif(knightPercent < knightTargetPercent):
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
    global factoryCount
    global workerTargetPercent
    global karbLocations
    global unitCarbs
    global globEnemy
    building = False
    try:
        unitTotal = workerCount + knightCount + mageCount + rangerCount
        workerpercentage = workerCount/unitTotal

        enemy = ClosestEnemy(unit)
        if enemy is not None:
            AddToGlobalEnemies(enemy)

        if factoryCount < 1:
            d = FactoryPlacementDirection(unit.location.map_location())
            if d is not None and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
                gc.blueprint(unit.id, bc.UnitType.Factory, d)
                building = True

        if workerpercentage < workerTargetPercent or workerCount < 5:
            dir = FindUnoccupiedDirection()
            if dir is not None and gc.can_replicate(unit.id, dir):
                print("replicating")
                gc.replicate(unit.id, dir)
                workerCount += 1

        nearbyBuildings = gc.sense_nearby_units_by_type(unit.location.map_location(), 2, bc.UnitType.Factory)
        closestKarb = unitCarbs.get(unit.id, None)
        if(closestKarb is None):
            closestKarb = ClosestCarbLocation(unit.location.map_location())
        dir = FindGreedyPath(unit, closestKarb[0])

        for object in nearbyBuildings:
            # If we find a strucure to build on, we dont want to move.
            if gc.can_build(unit.id, object.id) and not object.structure_is_built():
                gc.build(unit.id, object.id)
                building = True
                break

        if unit.location.map_location().is_adjacent_to(closestKarb[0]):
            harvestDir = unit.location.map_location().direction_to(closestKarb[0])
            if(gc.can_harvest(unit.id, harvestDir)):
                gc.harvest(unit.id, harvestDir)
                if(gc.karbonite_at(closestKarb[0]) < 1):
                    karbLocations.remove(closestKarb)
                    unitCarbs.pop(unit.id)
                building = True

        if dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir) and not building:
            Move(unit, dir)
             
        d = FactoryPlacementDirection(unit.location.map_location())
        if d is not None and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
            gc.blueprint(unit.id, bc.UnitType.Factory, d)

    except Exception as e:
        print('Worker Error:', e)
        traceback.print_exc()


def KnightTree(unit):
    global globEnemy
    global globEnemies

    try:
        if unit.location.is_in_garrison():
            #print("Ready to load but not loaded")
            return

        enemy = ClosestEnemy(unit)

        if enemy is not None:
            AddToGlobalEnemies(enemy)
            Attack(unit, enemy)
        
        if enemy is not None and not gc.can_attack(unit.id, enemy.id):
            dir = FindGreedyPath(unit, enemy.location.map_location())
            if dir is not None:
                if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                    Move(unit, dir)
                    Attack(unit, enemy)

        elif len(globEnemies) > 0:
            gEnemy = ClosestGlobalEnemy(unit)
            dir = FindGreedyPath(unit, gEnemy.location.map_location())
            if dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                Move(unit, dir)
            
        else:
            baseLoc = ClosestBase(unit)
            dir = FindGreedyPath(unit, baseLoc)
            if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                length = baseLoc.distance_squared_to(unit.location.map_location())
                if length > 30:
                    Move(unit, dir)
                else:
                    for i in range(4):
                        dir = random.choice(directions)
                        if gc.can_move(unit.id, dir):
                            Move(unit, dir)
                            break

    except Exception as e:
        print('Knight Error:', e)
        # use this to show where the error was
        traceback.print_exc()


def MageTree(unit):
    global globEnemy
    global globEnemies
    dir = FindUnoccupiedDirection()
    attacked = False

    try:
        if unit.location.is_in_garrison():
            #print("Ready to load but not loaded")
            return

        enemy = ClosestEnemy(unit)
        if enemy is not None:
            Attack(unit, enemy)
            AddToGlobalEnemies(enemy)
            attacked = True
            if(gc.is_move_ready(unit.id) and dir is not None):
                gc.move_robot(unit.id, dir)
                enemy = ClosestEnemy(unit)
                Attack(unit, enemy)

        if len(globEnemies) > 0 and not attacked:
            gEnemy = ClosestGlobalEnemy(unit)
            dir = FindGreedyPath(unit, gEnemy.location.map_location())
            if dir is not None and gc.is_move_ready(unit.id):
                Move(unit, dir)
                enemy = ClosestEnemy(unit)
                if enemy is not None:
                    Attack(unit, enemy)
        elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)

        
    except Exception as e:
        print('Mage Error:', e)
        # use this to show where the error was
        traceback.print_exc()

def RangerTree(unit):
    global globEnemy
    global globEnemies
    attacked = False

    try:
        if unit.location.is_in_garrison():
            #print("Ready to load but not loaded")
            return

        baseLoc = ClosestBase(unit)
        dir = FindGreedyPath(unit, baseLoc)
        enemy = ClosestEnemy(unit)
        if enemy is not None:
            Attack(unit, enemy)
            AddToGlobalEnemies(enemy)
            attacked = True
            if(gc.is_move_ready(unit.id) and dir is not None):
                gc.move_robot(unit.id, dir)
                enemy = ClosestEnemy(unit)
                if enemy is not None:
                    Attack(unit, enemy)

        #if globEnemy is not None and gc.can_begin_snipe(unit.id, globEnemy.location.map_location()) and gc.is_begin_snipe_ready(unit.id):
            #print("Sniping")
            #gc.begin_snipe(unit.id, globEnemy.location.map_location())

        if len(globEnemies) > 0 and not attacked:
            gEnemy = ClosestGlobalEnemy(unit)
            dir = FindGreedyPath(unit, gEnemy.location.map_location())
            if dir is not None and gc.is_move_ready(unit.id):
                Move(unit, dir)
                enemy = ClosestEnemy(unit)
                if enemy is not None:
                    Attack(unit, enemy)

        elif dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
            length = baseLoc.distance_squared_to(unit.location.map_location())
            if length > 60:
                gc.move_robot(unit.id, dir)
            else:
                for i in range(4):
                    dir = random.choice(directions)
                    if gc.can_move(unit.id, dir):
                        Move(unit, dir)
                        break
                

        
    except Exception as e:
        print('Ranger Error:', e)
        # use this to show where the error was
        traceback.print_exc()

def FactoryPlacementDirection(currentLoc):
    dirCanidates = []
    for d in directions:
        if gc.can_move(unit.id, d):
            dirCanidates.append([d, 0])

    for d in dirCanidates:
        tempLocation = currentLoc.add(d[0])
        if(map.on_map(tempLocation) is False):
            continue
        for newD in directions:
            tempLocation.add(newD)
            if(map.on_map(tempLocation) is False):
                continue
            if(gc.is_occupiable(tempLocation)):
                d[1] += 1
    maxScore = 0
    finalDir = None
    for idx, scoredDir in enumerate(dirCanidates):
        if scoredDir[1] > maxScore:
            maxScore = scoredDir[1]
            finalDir = scoredDir[0]

    return finalDir

def FindUnoccupiedDirection():

    for d in directions:
        if gc.can_move(unit.id, d):
            return d
    return None       

def Attack(unit, enemy):

    dir = FindGreedyPath(unit, enemy.location.map_location())
    if(enemy is not None and gc.can_attack(unit.id, enemy.id) and gc.is_attack_ready(unit.id)):
        gc.attack(unit.id, enemy.id)

    if(gc.can_attack(unit.id, enemy.id) and not gc.is_attack_ready(unit.id) and unit.unit_type != bc.UnitType.Knight and enemy.unit_type != bc.UnitType.Factory and enemy.unit_type != bc.UnitType.Worker):

        dir = FleePath(unit, enemy.location.map_location())
        if(gc.is_move_ready(unit.id)):
            Move(unit, dir)

def Move(unit, dir):
    global unitTrails
    global recheck
    global notMovedUnits
    if dir is not None and gc.can_move(unit.id, dir):
        gc.move_robot(unit.id, dir)
        trail = unitTrails.get(unit.id, [])
        unitTrails[unit.id] = StinkyTrail(trail, unit.location.map_location())
    elif recheck is False:
        print("Want to move again ", dir)
        notMovedUnits.append(unit)

def AddToGlobalEnemies(enemy):
    global globEnemies

    if globEnemies.count(enemy) == 0:
        globEnemies.append(enemy)
    
    if len(globEnemies) > 2:
        del globEnemies[0]

def ClosestGlobalEnemy(unit):
    global globEnemies

    unitLocation = unit.location.map_location()
    target = None
    colosestDist = 100000

    for enemy in globEnemies:
        if enemy is not None:
            distance = unitLocation.distance_squared_to(enemy.location.map_location())
            if distance < colosestDist:
                colosestDist = distance
                target = enemy
        else:
            globEnemies.remove(enemy)

    return target

def ClosestCarbLocation(position):
    global karbLocations
    global unitCarbs
    if(len(karbLocations) == 0):
        #print("No closest location found, locations list is empty. ")
        return None
    minDist = 10000000
    targetidx = None
    #print("Carblocations is ", len(karbLocations), "long")
    for idx, location in enumerate(karbLocations):
        if(location[1] > 3):
            print("Enough workers on this karbonite deposit ", location[1])
            continue
        currentDist = position.distance_squared_to(location[0])
        if(currentDist < minDist):
            minDist = currentDist
            targetidx = idx

    karbLocations[targetidx][1] += 1
    unitCarbs[unit.id] = karbLocations[targetidx]

    return karbLocations[targetidx]

# returns the unit in the list units closest to the position specified
def ClosestEnemy(unit):

    position = unit.location.map_location()
    nearby = gc.sense_nearby_units(position, unit.vision_range)
    enemies = []
    for other in nearby:
        if(other.team != gc.team()):
            enemies.append(other)

    if(len(enemies) == 0):
        return None

    minDist = 10000000
    target = None
    for enemy in enemies:
        currentDist = position.distance_squared_to(enemy.location.map_location())
        if(currentDist < minDist):
            minDist = currentDist
            target = enemy

    return target

def ClosestBase(unit):
    global enemyBases

    position = unit.location.map_location()
    minDist = 10000000
    target = None
    for base in enemyBases:
        currentDist = position.distance_squared_to(base)
        if(currentDist < minDist):
            minDist = currentDist
            target = base

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
            target = location

    return target



def GetCarbs(map):    
    karbLocs = []
    for i in range(map.width):
        for j in range(map.height):
            location = [bc.MapLocation(bc.Planet.Earth, i, j), 0]
            if map.initial_karbonite_at(location[0]):
                karbLocs.append(location)
    return karbLocs

def FleePath(unit, goalLocation):
    unitLocation = unit.location.map_location()

    bestDir = goalLocation.direction_to(unitLocation)
    temp = unitLocation.add(bestDir)
    if gc.can_sense_location(temp) and gc.is_occupiable(temp):
        return bestDir
    
    else:
        length = len(directions)
        directionIteration = 0
        for i in range(length):
            if directions[i] == bestDir:
                directionIteration = i
        count = 0
        iter = 1
        while(count < (length + 1) / 2):
            count += 1
            temp = unitLocation.add(directions[(directionIteration + iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp):
                return directions[(directionIteration + iter) % length]
            temp = unitLocation.add(directions[(directionIteration - iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp):
                return directions[(directionIteration - iter) % length]
            iter += 1

def FindGreedyPath(unit, goalLocation):    
    global unitTrails
    unitLocation = unit.location.map_location()
    trail = unitTrails.get(unit.id, [])

    bestDir = unitLocation.direction_to(goalLocation)
    temp = unitLocation.add(bestDir)
    if gc.can_sense_location(temp) and gc.is_occupiable(temp) and trail.count(temp) == 0:
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
        while(count < (length + 2) / 2):
            count = count + 1
            temp = unitLocation.add(directions[(directionIteration + iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp) and trail.count(temp) == 0:
                return directions[(directionIteration + iter) % length]
            temp = unitLocation.add(directions[(directionIteration - iter) % length])
            if gc.can_sense_location(temp) and gc.is_occupiable(temp) and trail.count(temp) == 0:
                return directions[(directionIteration - iter) % length]
            iter = iter + 1
            
    unitTrails[unit.id] = []

def StinkyTrail(trail, location):
    round = gc.round()
    trail.append(location)
    if round < 300:
        if len(trail) > 4:
            del trail[0]

    else:
        if len(trail) > 8:
            del trail[0]
    
    return trail

def StartingPositions(map):
    enemyBase = []
    ourBase = []
    for unit in map.initial_units:
        if unit.team is not my_team:
            enemyBase.append(unit.location.map_location())
        else:
            ourBase.append(unit.location.map_location())

    return ourBase, enemyBase


print(os.getcwd())

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)


# It's a good idea to try to keep your bots deterministic, 
# to make debugging easier.
# determinism isn't required, but it means that the same things will happen 
# in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
#random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.


my_team = gc.team()
map = gc.starting_map(gc.planet())
karbLocations = []
globEnemy = None
enemyBases = []
recheck = False
notMovedUnits = []
ourBases = []
workerCount = 0
knightCount = 0
factoryCount = 0
mageCount = 0
rangerCount = 0
startRange = 10000
if(gc.planet() == bc.Planet.Earth):
    ourBases, enemyBases = StartingPositions(map)
    karbLocations = GetCarbs(map)
    startRange = enemyBases[0].distance_squared_to(ourBases[0])
    
mapSize = map.height * map.width
print(enemyBases)

if mapSize < 500 and startRange < 100:
    gc.queue_research(bc.UnitType.Knight)
    gc.queue_research(bc.UnitType.Knight)
    gc.queue_research(bc.UnitType.Knight)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    workerTargetPercent = 0.15
    knightTargetPercent = 0.85
    mageTargetPercent = 0.0
    rangerTargetPercent = 0.0
elif(startRange < 250 and mapSize < 1250):
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Knight)
    gc.queue_research(bc.UnitType.Knight)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    workerTargetPercent = 0.15
    knightTargetPercent = 0.5
    mageTargetPercent = 0.0
    rangerTargetPercent = 0.35
else:
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Ranger)
    knightTargetPercent = 0.0
    mageTargetPercent = 0.0
    rangerTargetPercent = 0.8
    workerTargetPercent = 0.2

unitTrails = {}
globEnemies = []
unitCarbs = {}

while True:
    # We only support Python 3, which means brackets around print()
    #print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
    factorylist = []
    workerList = []
    knightList = []
    mageList = []
    rangerList = []
    healerList = []
    recheck = False
    notMovedUnits = []

    # frequent try/catches are a good idea

        #First we count our units
    for unit in gc.my_units():
        if unit.unit_type == bc.UnitType.Factory:
            factoryCount += 1
            factorylist.append(unit)
        elif unit.unit_type == bc.UnitType.Worker:
            workerCount += 1
            workerList.append(unit)
        elif unit.unit_type == bc.UnitType.Knight:
            knightCount += 1
            knightList.append(unit)
        elif unit.unit_type == bc.UnitType.Mage:
            mageCount += 1
            mageList.append(unit)
        elif unit.unit_type == bc.UnitType.Ranger:
            rangerCount += 1
            rangerList.append(unit)

    try:

        for unit in workerList:
            WorkerTree(unit)

        for unit in factorylist:
            FactoryTree(unit)

        for unit in knightList:
            KnightTree(unit)

        for unit in mageList:
            MageTree(unit)

        for unit in rangerList:
            RangerTree(unit)
        
        recheck = True
        for unit in notMovedUnits:
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
                
        workerCount = 0
        knightCount = 0
        factoryCount = 0
        mageCount = 0
        rangerCount = 0

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
