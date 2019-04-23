import battlecode as bc
import random
import sys
import traceback
import time

import os
print(os.getcwd())

print("pystarting")

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
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Worker)

my_team = gc.team()
enemy_team = bc.Team.Red
if my_team == bc.Team.Red:
	enemy_team = bc.Team.Blue

visible_enemy_units = []

neg_offset = [0,-1, 1,-2, -3, 2, 3]
pos_offset = [0, 1,-1, 2, 3, -2, -3]

offset = [0,-1,1,-2,2,-3,3]

previous_positions = {
}


if gc.planet() == bc.Planet.Earth:
	my_Starting_Quadrants = []
	enemy_Starting_Quadrants = []
	temp_enemy_starting = []
	map = gc.starting_map(gc.planet())
	midPoint = (map.width/2, map.height/2)
	upperRight = (map.width, map.height)
	upperLeft = (0, map.height)
	lowerRight = (map.width, 0)
	lowerLeft = (0, 0)

	upperRight = (round((upperRight[0]+midPoint[0]) / 2), round((upperRight[1]+midPoint[1]) / 2))
	upperLeft = (round((upperLeft[0]+midPoint[0]) / 2), round((upperLeft[1]+midPoint[1]) / 2))
	lowerRight = (round((lowerRight[0]+midPoint[0]) / 2), round((lowerRight[1]+midPoint[1]) / 2)) 
	lowerLeft = (round((lowerLeft[0]+midPoint[0]) / 2), round((lowerLeft[1]+midPoint[1]) / 2)) 

	guard_positions = []

	enemies_Close = False
	for unit in gc.my_units():
		if len(gc.sense_nearby_units_by_team(unit.location.map_location(), unit.vision_range, enemy_team)) > 0:
			enemies_Close = True
		
		if unit.location.map_location().x == map.width/2-0.5 or unit.location.map_location().y == map.height/2-0.5:
			continue

		if unit.location.map_location().x >= map.width/2:
			if unit.location.map_location().y >= map.height/2:
				# forth quadrant
				if upperRight in my_Starting_Quadrants:
					continue
				my_Starting_Quadrants.append(upperRight)
				temp_enemy_starting.append(lowerLeft)
			elif unit.location.map_location().y < map.height/2:
				# third quadrant
				if upperLeft in my_Starting_Quadrants:
					continue
				my_Starting_Quadrants.append(upperLeft)
				temp_enemy_starting.append(lowerRight)
		elif unit.location.map_location().y >= map.height/2:
			# second quadrant
			if lowerRight in my_Starting_Quadrants:
				continue
			my_Starting_Quadrants.append(lowerRight)
			temp_enemy_starting.append(upperLeft)
		elif unit.location.map_location().y < map.height/2:
			# first quadrant
			if lowerLeft in my_Starting_Quadrants:
				continue
			my_Starting_Quadrants.append(lowerLeft)
			temp_enemy_starting.append(upperRight)

	enemy_Starting_Quadrants = list(set([lowerLeft,lowerRight,upperLeft,upperRight]) - set(my_Starting_Quadrants))
	if len(my_Starting_Quadrants) < 2 and not enemies_Close:
		enemy_Starting_Quadrants = temp_enemy_starting
	elif enemies_Close:
		enemy_Starting_Quadrants = my_Starting_Quadrants
		guard_positions = enemy_Starting_Quadrants
	
	if not enemies_Close:
		for my_Quad in my_Starting_Quadrants:
			for their_Quad in enemy_Starting_Quadrants:
				posTuple = (round((my_Quad[0]+their_Quad[0]) / 2), round((my_Quad[1]+their_Quad[1]) / 2))
				if not posTuple in guard_positions:
					guard_positions.append(posTuple)

	print('my starting position ', my_Starting_Quadrants)
	print('enemy starting position ', enemy_Starting_Quadrants)

	print('guardpositions = ', guard_positions)

	karbLocations = []
	for i in range(map.width):
		for j in range(map.height):
			location = bc.MapLocation(bc.Planet.Earth, i, j)
			if map.initial_karbonite_at(location):
				karbLocations.append(location)

class Help_Functions(object):

	def Spread_Out(unit):
		moves = []
		shuffled = random.sample(directions, len(directions))
		for dir in shuffled:
			if gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
				new_location = (unit.location.map_location()).add(dir)
				nearby_Team_Members = gc.sense_nearby_units_by_team(new_location, 2, my_team)
				if len(nearby_Team_Members) == 1:
					gc.move_robot(unit.id, dir)
					moves = []
					break
				moves.append((-1*len(nearby_Team_Members), dir))
		if moves != []:
			moves.sort()
			gc.move_robot(unit.id, moves[0][1])
		else:
			d = random.choice(directions)
			if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
				gc.move_robot(unit.id, d)

	def Move_Towards(unit, target_location):
		global offset
		temp_location_X = unit.location.map_location().x
		temp_location_Y = unit.location.map_location().y

		oldPositions = previous_positions.get(unit.id)
		dir = unit.location.map_location().direction_to(target_location)

		true_offset = offset
		for off in true_offset:
			offset_direction = directions[(directions.index(dir)+off)%8]
			pos = (unit.location.map_location()).add(offset_direction)
			old = (pos.x, pos.y)
			if gc.is_move_ready(unit.id) and gc.can_move(unit.id, offset_direction) and (oldPositions == None or not old in oldPositions):
				if off > 0:
					offset = pos_offset
				elif off < 0:
					offset = neg_offset
				else:
					offset = [0,-1,1,-2,2,-3,3]

				if oldPositions == None:
					new_dict_list = ((temp_location_X, temp_location_Y))
				elif len(oldPositions) < 2:
					new_dict_list = ((temp_location_X, temp_location_Y), oldPositions[0])
				elif len(oldPositions) < 3:
					new_dict_list = ((temp_location_X, temp_location_Y), oldPositions[0], oldPositions[1])
				elif len(oldPositions) < 4:
					new_dict_list = ((temp_location_X, temp_location_Y), oldPositions[0], oldPositions[1], oldPositions[2])
				else:
					new_dict_list = ((temp_location_X, temp_location_Y), oldPositions[0], oldPositions[1], oldPositions[2], oldPositions[3])
				previous_positions[unit.id] = new_dict_list
				gc.move_robot(unit.id, offset_direction)
				return pos

	def Attack_Nearby_Unit(unit):
		pass

	#Returns the best target within range, if there is none, return itself
	def Get_Target_Within_Range(unit,radius, newPos = None):
		if newPos is None:
			nearby = gc.sense_nearby_units(unit.location.map_location(), radius)
		else:
			nearby = gc.sense_nearby_units(newPos, radius)
		bestTarget = unit
		for other in nearby:
			if other.team != my_team:
				if bestTarget == unit:
					bestTarget = other
				if other.unit_type == bc.UnitType.Mage:
					bestTarget = other
				elif other.unit_type == bc.UnitType.Healer:
					if (bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Healer):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Ranger:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Knight:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Knight and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Worker:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Worker and bestTarget.unit_type != bc.UnitType.Knight and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
		return bestTarget

	def Get_Snipe_Target(unit, visibleTargets):
		bestTarget = unit
		for other in visibleTargets:
			if other.team != my_team:
				if bestTarget == unit:
					bestTarget = other
				if other.unit_type == bc.UnitType.Mage:
					bestTarget = other
				elif other.unit_type == bc.UnitType.Healer:
					if (bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Healer):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Ranger:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Knight:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Knight and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
				elif other.unit_type == bc.UnitType.Worker:
					if(bestTarget.unit_type != bc.UnitType.Mage and bestTarget.unit_type != bc.UnitType.Worker and bestTarget.unit_type != bc.UnitType.Knight and bestTarget.unit_type != bc.UnitType.Healer and bestTarget.unit_type != bc.UnitType.Ranger):
						bestTarget = other
		return bestTarget

#helperFunctions for specific units,
class FactoryClass(object):
	def Unload_unit(unit):
		garrison = unit.structure_garrison()
		if len(garrison) > 0:
			for dir in directions:
				if gc.can_unload(unit.id, dir):
					#print('unloaded a knight!')
					gc.unload(unit.id, dir)
					break

	def Produce_unit(unit, production_type):
		if gc.can_produce_robot(unit.id, production_type):
			gc.produce_robot(unit.id, production_type)
			#print('produced a unit!')

already_harvesting = []

class WorkerClass(object):
	def Harvest(unit):
		for dir in directions:
			if gc.can_harvest(unit.id, dir):
				gc.harvest(unit.id, dir)
				if not unit.location.map_location() in already_harvesting:
					already_harvesting.append(unit.location.map_location())
				return True

	def Create_Blueprint(unit):
		#might want to do this in random directions instead by using random.sample
		for dir in directions:
			if gc.can_blueprint(unit.id, bc.UnitType.Factory, dir):
				gc.blueprint(unit.id, bc.UnitType.Factory, dir)
				return True

	def Build(unit):
		nearby_blueprints = gc.sense_nearby_units_by_type(unit.location.map_location(), 2, bc.UnitType.Factory)
		for building in nearby_blueprints:
			if gc.can_build(unit.id, building.id) and not building.structure_is_built():
				gc.build(unit.id, building.id)
				#print('building on a structure')
				return True

	def Repair(unit):
		nearby_buildings = gc.sense_nearby_units_by_type(unit.location.map_location(), 2, bc.UnitType.Factory)
		for building in nearby_buildings:
			if gc.can_repair(unit.id, building.id):
				gc.repair(unit.id, building.id)
				return

	def Replicate(unit):
		#might want to do this in random directions instead by using random.sample
		for dir in directions:
			if gc.can_replicate(unit.id, dir):
				gc.replicate(unit.id, dir)
				return

	def Scout_Area(unit):
		nearby_enemies = gc.sense_nearby_units_by_team(unit.location.map_location(), 10, enemy_team)
		if len(nearby_enemies) > 0:
			return nearby_enemies[0].location

	def Find_Scout_Points(unit):
		max_X = map.width
		max_Y = map.height

		lower_left_location = bc.MapLocation(bc.Planet.Earth, max_X, max_Y)
		lower_right_location = bc.MapLocation(bc.Planet.Earth, 0, max_Y)
		upper_left_location = bc.MapLocation(bc.Planet.Earth, max_X, 0)
		upper_right_location =  bc.MapLocation(bc.Planet.Earth, 0, 0)
		temp_locations = [lower_left_location, lower_right_location, upper_left_location, upper_right_location]

		for i in range(1,len(temp_locations)):
			current = temp_locations[i]
			while i > 0 and unit.location.map_location().distance_squared_to(temp_locations[i-1]) < unit.location.map_location().distance_squared_to(current):
				temp_locations[i] = temp_locations[i-1]
				i = i-1
				temp_locations[i] = current
		return temp_locations

	def Get_Closest_Karbonite(unit):
		maxDist = 100000
		closest_karbonite = unit.location.map_location()
		for loc in karbLocations:
			if not loc in already_harvesting:
				currDist = unit.location.map_location().distance_squared_to(loc)
				if currDist < maxDist:
					maxDist = currDist
					closest_karbonite = loc

		return closest_karbonite

class KnightClass(object):
	def Javelin_attack(unit):
		if not gc.is_javelin_ready(unit.id):
			return

		nearby_targets = sense_nearby_units_by_team(unit.location.map_location(), unit.ability_range(), enemy_team)

		for enemy in nearby_targets:
			if unit.can_javelin(unit.id, enemy.id):
				gc.javelin(unit.id, enemy.id)
				return

	def Javelin_attack_target(unit,target):
		if not gc.is_javelin_ready(unit.id):
			return
		if gc.can_javelin(unit.id, target.id):
			gc.javelin(unit.id, target.id)
			return
class RangerClass(object):
	def Snipe_attack(unit, target):
		if unit.ranger_is_sniping():
			return

		if not gc.is_begin_snipe_ready(unit.id):
			return
    
		if gc.can_begin_snipe(unit.id, target.location.map_location()):
			gc.begin_snipe(unit.id, target.location.map_location())
			return

#keeping count of how many units of each type we have (is there a better way? units.knights?)
amount_of_factories = 0
amount_of_workers = 0
amount_of_knights = 0
amount_of_rangers = 0

scout_id = -1
scout_available = False
scout_target = 0
scout_targets = []

harvesters = 0

while True:
	# We only support Python 3, which means brackets around print()
	#temporary amounts
	temp_factories = 0
	temp_workers = 0
	temp_knights = 0
	temp_rangers = 0
	worker_units = []
	temp_visible_enemy_units = []
	# frequent try/catches are a good idea
	try:
		# walk through our units:
		for unit in gc.my_units():
			# decide what to do with factory
			if unit.unit_type == bc.UnitType.Factory:
				temp_factories += 1
				if unit.is_factory_producing():
					if unit.factory_unit_type() == bc.UnitType.Worker:
						temp_workers += 1
					elif unit.factory_unit_type() == bc.UnitType.Knight:
						temp_knights += 1
					elif unit.factory_unit_type() == bc.UnitType.Ranger:
						temp_rangers += 1
					continue
				FactoryClass.Unload_unit(unit)
				if gc.karbonite() > 40:
					#This 4 is higly temporary, need to figure out a good number
					if amount_of_workers < 2:
						if gc.can_produce_robot(unit.id, bc.UnitType.Worker):
							FactoryClass.Produce_unit(unit, bc.UnitType.Worker)
						else:
							continue
					elif gc.round() < 100 or (amount_of_rangers+amount_of_knights > 0 and amount_of_knights/(amount_of_rangers+amount_of_knights) < 0.4):
						if gc.can_produce_robot(unit.id, bc.UnitType.Knight):
							amount_of_knights += 1
							temp_knights += 1
							FactoryClass.Produce_unit(unit, bc.UnitType.Knight)
					else:
						if gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
							amount_of_rangers += 1
							temp_rangers += 1
							FactoryClass.Produce_unit(unit, bc.UnitType.Ranger)	
				else:
					continue

			if unit.unit_type == bc.UnitType.Worker:
				temp_workers += 1
				#if the unit is produced but in garrison we cannot use it until it has been released
				if unit.location.is_in_garrison():
					continue
				# decide what to do with Worker
				if gc.karbonite() > 150 and amount_of_workers < 10 and amount_of_factories > 3:
					WorkerClass.Replicate(unit)
				worker_units.append(unit)
				#replicate??

				#if factories * 50 + 200
				#WorkerClass.Replicate(unit)
				#WorkerClass.Build(unit)
				#WorkerClass.Create_Blueprint(unit)

			if unit.unit_type == bc.UnitType.Knight:
				temp_knights += 1
				#if the unit is produced but in garrison we cannot use it until it has been released
				if unit.location.is_in_garrison():
					continue

				#Check melee range
				melee = False
				bestTarget = Help_Functions.Get_Target_Within_Range(unit, unit.attack_range())
				if bestTarget != unit:
					if(temp_visible_enemy_units.count(bestTarget) == 0):
						temp_visible_enemy_units.append(bestTarget)
					#print(unit.id, 'We are in melee range, we should fight!')
					melee = True
					#We check if our attack is ready, if not we should stick around to attack next loop
					if gc.is_attack_ready(unit.id):
						gc.attack(unit.id, bestTarget.id)

				#Check ability range
				bestTarget = Help_Functions.Get_Target_Within_Range(unit, unit.ability_range())
				if bestTarget != unit and gc.is_javelin_ready(unit.id) and not melee:
					if(temp_visible_enemy_units.count(bestTarget) == 0):
						temp_visible_enemy_units.append(bestTarget)
					melee = True
					KnightClass.Javelin_attack_target(unit,bestTarget)

				#Check vision range
				bestTarget = Help_Functions.Get_Target_Within_Range(unit, unit.vision_range)
				if bestTarget != unit and not melee:
					if(temp_visible_enemy_units.count(bestTarget) == 0):
						temp_visible_enemy_units.append(bestTarget)
					#if len(gc.sense_nearby_units_by_team(unit.location.map_location(), unit.vision_range, my_team)) > 0:
					newPos = Help_Functions.Move_Towards(unit, bestTarget.location.map_location())
					#Maybe we can attack that dude after we have moved, lets check!
					meleeTarget = Help_Functions.Get_Target_Within_Range(unit, unit.attack_range(), newPos)
					if meleeTarget != unit:
						if gc.is_attack_ready(unit.id):
							gc.attack(unit.id, meleeTarget.id)

				#Check if we have location of any enemies
				elif len(visible_enemy_units) > 0 and not melee:
					closestTarget = unit
					distanceToClosest = 9000
					for target in visible_enemy_units:
						if unit.location.map_location().distance_squared_to(target.location.map_location()) < distanceToClosest:
							closestTarget = target
					Help_Functions.Move_Towards(unit, closestTarget.location.map_location())
					
				#Move to a good location to chill - Random so far
				elif not melee:
					closest_Guard1 = 9000
					closest_Guard2 = 9000
					bestGuard = bc.MapLocation(bc.Planet.Earth, enemy_Starting_Quadrants[0][0], enemy_Starting_Quadrants[0][1])
					bestguards = (bestGuard, bestGuard)
					for guards in guard_positions:
						guard_map_pos = bc.MapLocation(bc.Planet.Earth, guards[0], guards[1])
						distance_To_Guard = unit.location.map_location().distance_squared_to(guard_map_pos)
					
						if distance_To_Guard < closest_Guard1:
							closest_Guard2 = closest_Guard1
							bestguards = (guard_map_pos, bestguards[0])
							closest_Guard1 = distance_To_Guard
						elif distance_To_Guard < closest_Guard2 and not distance_To_Guard == closest_Guard1:
							closest_Guard2 = distance_To_Guard
							bestguards = (bestguards[0], guard_map_pos)
					
					Help_Functions.Move_Towards(unit, random.choice(bestguards))

			if unit.unit_type == bc.UnitType.Ranger:
				temp_rangers += 1
				#if the unit is produced but in garrison we cannot use it until it has been released
				if unit.location.is_in_garrison():
					continue
				#Check melee range
				melee = False
				bestTarget = Help_Functions.Get_Target_Within_Range(unit, unit.attack_range())
				if bestTarget != unit:
					if(temp_visible_enemy_units.count(bestTarget) == 0):
						temp_visible_enemy_units.append(bestTarget)
					#print(unit.id, 'We are in melee range, we should fight!')
					melee = True
					#We check if our attack is ready, if not we should stick around to attack next loop
					if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, bestTarget.id):
						gc.attack(unit.id, bestTarget.id)

				#Check ability range
				bestTarget = Help_Functions.Get_Snipe_Target(unit, visible_enemy_units)
				if bestTarget != unit and not melee:
					RangerClass.Snipe_attack(unit, bestTarget)

				#Check vision range
				bestTarget = Help_Functions.Get_Target_Within_Range(unit, unit.vision_range)
				if bestTarget != unit and not melee:
					if(temp_visible_enemy_units.count(bestTarget) == 0):
						temp_visible_enemy_units.append(bestTarget)
					newPos = Help_Functions.Move_Towards(unit, bestTarget.location.map_location())
					#Maybe we can attack that dude after we have moved, lets check!
					meleeTarget = Help_Functions.Get_Target_Within_Range(unit, unit.attack_range(), newPos)
					if meleeTarget != unit:
						if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, bestTarget.id):
							gc.attack(unit.id, meleeTarget.id)

				#Check if we have location of any enemies
				elif len(visible_enemy_units) > 0 and not melee:
					closestTarget = unit
					distanceToClosest = 9000
					for target in visible_enemy_units:
						if unit.location.map_location().distance_squared_to(target.location.map_location()) < distanceToClosest:
							closestTarget = target
					Help_Functions.Move_Towards(unit, closestTarget.location.map_location())
					
				#Move to a good location to chill - Random so far
				elif not melee: 
					Help_Functions.Spread_Out(unit)

		for workers in worker_units:
			if workers.location.is_in_garrison():
				continue
			bestTarget = Help_Functions.Get_Target_Within_Range(workers, workers.vision_range)
			if bestTarget != workers:
				if(temp_visible_enemy_units.count(bestTarget) == 0):
					temp_visible_enemy_units.append(bestTarget)
			if not scout_available and gc.round() > 100:
				scout_available = True
				scout_id = workers.id

			if scout_id == workers.id:
				if scout_targets == []:
					scout_targets = WorkerClass.Find_Scout_Points(workers)
				if workers.location.map_location().distance_squared_to(scout_targets[scout_target]) < 10 and scout_target < 4:
					scout_target += 1
				if scout_target == 4:
					scout_target = 0
				Help_Functions.Move_Towards(workers, scout_targets[scout_target])
			else:
				if not WorkerClass.Build(workers):
					if amount_of_factories < 6 and gc.karbonite() > 200:
						if WorkerClass.Create_Blueprint(workers):
							continue
						else:
							Help_Functions.Spread_Out(workers)

					nearby_factories = gc.sense_nearby_units_by_type(workers.location.map_location(), 2, bc.UnitType.Factory)
					if len(nearby_factories) > 0:
						Help_Functions.Spread_Out(workers)

					karbonite_at = WorkerClass.Get_Closest_Karbonite(workers)
					if WorkerClass.Harvest(workers):
						continue
					elif not workers.location.map_location().distance_squared_to(karbonite_at) < 2:
						Help_Functions.Move_Towards(workers, karbonite_at)
						continue


	except Exception as e:
		print('Error:', e)
		# use this to show where the error was
		traceback.print_exc()

	#saving the amount of units for next turn
	amount_of_factories = temp_factories
	amount_of_workers = temp_workers
	amount_of_knights = temp_knights
	amount_of_rangers = temp_rangers
	visible_enemy_units = temp_visible_enemy_units
	# send the actions we've performed, and wait for our next turn.
	gc.next_turn()

	# these lines are not strictly necessary, but it helps make the logs make more sense.
	# it forces everything we've written this turn to be written to the manager.
	sys.stdout.flush()
	sys.stderr.flush()