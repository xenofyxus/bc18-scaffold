import battlecode as bc
import random
import sys
import traceback
import time
import astar
from worker import Worker
from knight import Knight
import strategy
import math
import time

gc = bc.GameController()

directions = list(bc.Direction)
karbonite_map = []
enemy_units_map = []
my_units_map = []
unit_map = []
terrain_map = []
my_team = gc.team()
enemy_team = bc.Team.Red if my_team == bc.Team.Blue else bc.Team.Blue
#strategy = strategy.Strategy()
map_height = gc.starting_map(gc.planet()).height
map_width = gc.starting_map(gc.planet()).width
my_units = []


def update_my_units_map(units):
    """Updates the map containing information regarding friendly units."""
    for x in range(map_width):
        for y in range(map_height):
            my_units_map[x][y] = None
    strategy.Strategy.getInstance().resetCurrentUnits()
    for unit in units:
        strategy.Strategy.getInstance().addUnit(unit.unit_type)
        location = unit.location
        if location.is_on_map():
            map_location = location.map_location()
            my_units_map[map_location.x][map_location.y] = unit


def update_enemy_units_map(units):
    """Updates the map attempting to keep track of enemy units."""
    for x in range(map_width):
        for y in range(map_height):
            if enemy_units_map[x][y] and enemy_units_map[x][y].unit_type != bc.UnitType.Factory:
                enemy_units_map[x][y] = None
    for unit in units:
        location = unit.location
        if location.is_on_map():
            update_karbonite_map(location, unit.vision_range)
            nearby = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range, enemy_team)
            for enemy in nearby:
                map_location = enemy.location.map_location()
                enemy_units_map[map_location.x][map_location.y] = enemy


def update_karbonite_map(unit_location, range):
    """Updates the map containing information regarding karbonite."""
    locations = gc.all_locations_within(unit_location.map_location(), range)
    for map_location in locations:
        karbonite_map[map_location.x][map_location.y] = gc.karbonite_at(map_location)


def init_workers():
    """Initializes the worker units with behaviour trees."""
    units = gc.my_units()
    for unit in units:
        my_units.append(Worker(
            unit.id,
            gc,
            {
                "karbonite_map": karbonite_map,
                "terrain_map": terrain_map,
                "my_units_map": my_units_map,
                "enemy_units_map": enemy_units_map
            },
            my_units
        ))


def init_maps():
    """Initializes maps used by the AI."""
    map = gc.starting_map(gc.planet())
    for x in range(map_width):
        karbonite_map.append([])
        terrain_map.append([])
        enemy_units_map.append([])
        my_units_map.append([])
        for y in range(map_height):
            loc = bc.MapLocation(gc.planet(),x,y)
            karbonite_map[x].append(map.initial_karbonite_at(loc))
            terrain_map[x].append(map.is_passable_terrain_at(loc))
            enemy_units_map[x].append(None)
            my_units_map[x].append(None)


def remove_unreachable_karbonite():
    units = gc.my_units()
    map = gc.starting_map(gc.planet())
    map_reachable = [[False]*map_height for i in range(map_width)]
    directions = [dir for dir in bc.Direction if dir is not bc.Direction.Center]
    for unit in units:
        unit_location = unit.location.map_location()
        neighbours = []
        if not map_reachable[unit_location.x][unit_location.y]:
            neighbours.append(unit_location)
        while neighbours:
            location = neighbours.pop(0)
            if map_reachable[location.x][location.y]:
                continue
            map_reachable[location.x][location.y] = True

            for dir in directions:
                adjacent_location = location.add(dir)
                # check if out of bound
                if adjacent_location.x < 0 or adjacent_location.x >= len(map_reachable) or adjacent_location.y < 0 or adjacent_location.y >= len(map_reachable[0]):
                    continue
                if terrain_map[adjacent_location.x][adjacent_location.y] and not map_reachable[adjacent_location.x][adjacent_location.y]:
                    neighbours.append(adjacent_location)
    for x in range(len(map_reachable)):
        for y in range(len(map_reachable[0])):
            if not map_reachable[x][y]:
                karbonite_map[x][y] = 0
                terrain_map[x][y] = False


def is_narrow_point(location):
    upFree = 3
    for i in range(1,4):
        upLocation = location.translate(0,i)
        if not location_in_bounds(upLocation, terrain_map) or not terrain_map[upLocation.x][upLocation.y]:
            upFree = i - 1
            break

    downFree = 3
    for i in range(1,4):
        downLocation = location.translate(0,-i)
        if not location_in_bounds(downLocation, terrain_map) or not terrain_map[downLocation.x][downLocation.y]:
            downFree = i - 1
            break

    leftFree = 3
    for i in range(1,4):
        leftLocation = location.translate(-i,0)
        if not location_in_bounds(leftLocation, terrain_map) or not terrain_map[leftLocation.x][leftLocation.y]:
            leftFree = i - 1
            break

    rightFree = 3
    for i in range(1,4):
        rightLocation = location.translate(i,0)
        if not location_in_bounds(rightLocation, terrain_map) or not terrain_map[rightLocation.x][rightLocation.y]:
            rightFree = i - 1
            break

    return (upFree + downFree) < 2 or (leftFree + rightFree) < 2


def location_in_bounds(location, map):
    return location.x >= 0 and location.x < len(map) and location.y >= 0 and location.y < len(map[0])


def find_choke_points():
    width = len(terrain_map)
    height = len(terrain_map[0])
    map = gc.starting_map(gc.planet())
    my_start_workers = gc.my_units()
    enemy_start_workers = [worker for worker in map.initial_units if worker not in my_start_workers]

    paths = []
    for worker in my_start_workers:
        for enemy_worker in enemy_start_workers:
            my_worker_location = worker.location.map_location()
            enemy_worker_location = enemy_worker.location.map_location()
            astar_path = astar.astar(terrain_map, my_units_map, my_worker_location, enemy_worker_location)
            if len(astar_path) > 0:
                paths.append(astar_path)

    choke_points = []
    paths_length = 0
    for path in paths:
        paths_length += len(path)
        for location in path:
            if is_narrow_point(location) and location not in choke_points:
                choke_points.append(location)

    average_path_length = 0
    if len(paths) > 0:
        average_path_length = paths_length / len(paths)

    return choke_points,  average_path_length

def update_strategy():
    min_amount_for_offense = strategy.Strategy.getInstance().min_nr_units_for_offense
    current_amount = strategy.Strategy.getInstance().getNumberCurrentUnits()

    if min_amount_for_offense and current_amount >= min_amount_for_offense:
        strategy.Strategy.getInstance().setBattleStrategy(strategy.BattleStrategy.Offensive)

def init_strategy():
    width = len(terrain_map)
    height = len(terrain_map[0])
    choke_points, average_path_length = find_choke_points()
    map_area =  width*height

    nr_impassable = 0
    for x in range(width):
        for y in range(height):
            if not terrain_map[x][y]:
                nr_impassable += 1

    impassable_per = 100 *nr_impassable / map_area


    if len(choke_points) > 5:
        # A lot of choke points, we need more rangers
        if map_area >= 800 and impassable_per > 20:
            # play Deffensive
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Deffensive
            strategy.Strategy.getInstance().setMaxUnit(
                {
                    'worker': 3,
                    'factory': 5,
                    'healer': 5,
                    'knight': 5,
                    'mage': 5,
                    'ranger': 50
                }
            )
        else:
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Offensive
            # play aggresive
            strategy.Strategy.getInstance().setMaxUnit(
                {
                    'worker': 3,
                    'factory': 5,
                    'healer': 5,
                    'knight': 5,
                    'mage': 20,
                    'ranger': 30
                }
            )
    elif len(choke_points) > 1:
        # There are some choke points, we need some more  rangers
        if map_area >= 800 and average_path_length > 50:
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Deffensive
            strategy.Strategy.getInstance().setMinUnitsOffense(20)
            # Wait with aggresion unit we make some units
        else:
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Offensive
            # play aggresive from start
    else:
        if map_area >= 800:
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Deffensive
            strategy.Strategy.getInstance().setMinUnitsOffense(20)
            strategy.Strategy.getInstance().setMaxUnit(
                {
                    'worker': 3,
                    'factory': 5,
                    'healer': 5,
                    'knight': 10,
                    'mage': 10,
                    'ranger': 30
                }
            )
            # Wait with aggresion unit we make some units and make some more rangers
        else:
            strategy.Strategy.getInstance().battle_strategy = strategy.BattleStrategy.Offensive
            # play aggresive from start with regular unnits


def remove_dead_units():
    my_units[:] = [unit for unit in my_units if unit.unit()]


if gc.planet() == bc.Planet.Earth:
    init_maps()
    init_workers()
    remove_unreachable_karbonite()
    init_strategy()
    for research in strategy.Strategy.research_strategy:
        gc.queue_research(research)
while True:
    if gc.planet() == bc.Planet.Mars:
        gc.next_turn()
    else:
        try:
            units = gc.my_units()
            remove_dead_units()
            update_enemy_units_map(units)
            update_my_units_map(units)
            update_strategy()
            for unit in my_units:
                if unit.unit():
                    unit.run()
        except Exception as e:
            print('Error:', e)
            # use this to show where the error was
            traceback.print_exc()
        gc.next_turn()
        sys.stdout.flush()
        sys.stderr.flush()
