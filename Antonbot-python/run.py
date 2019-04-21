import battlecode as bc
import random
import sys
import traceback
import time
import os


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
    dir = random.choice(directions)

    try:
        if(unit.location.is_in_garrison() is True):
            print("Im a mage in a garrison and i need to unload before starting my mission.")
            return
        # Very wierd way of checking teams. didnt find an smarter atm.
        nearby = gc.sense_nearby_units(unit.location.map_location(), 3)
        enemies = None

        for other in nearby:
            if(other.team != gc.team()):
                enemies.append(other)
        if(enemies is not None):
            enemy = ClosestUnit(enemies)
            if(gc.can_attack(unit.id, enemy) and gc.is_attack_ready(unit.id)):
                gc.attack(unit.id, enemy)
                print("Im a mage and i just attacked unit: ", enemy)
            
            if(gc.can_attack(unit.id, enemy) and not gc.is_attack_ready(unit.id)):
                print("Im a mage and i need to rest to attack again, getting out of here. ")
                # TODO: Run to closest factory.
                if(gc.is_move_ready(unit.id)):
                    gc.move_robot(unit.id, dir)
                else:
                    print("Im a mage but im too tired to move or attack.")
        else:
            
            if(gc.is_move_ready(unit.id)):
                gc.move_robot(unit.id, dir)
                print("Im a mage on a mission to find enemies.")
            else:
                print("I need to rest to continue my mission.")

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


# returns the unit in the list units closest to the position specified
def ClosestUnit(position, units):

    if(len(units) == 0):
        print("No closest unit found, units list is empty. ")
        return None

    minDist = 10000000
    target = None
    for unit in units:
        currentDist = position.distance_squared_to(unit)
        if(currentDist < minDist):
            minDist = currentDist
            target = unit

    return target


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
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)

my_team = gc.team()

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

