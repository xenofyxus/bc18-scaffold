import battlecode as bc
import behaviour_tree as bt
import random
import strategy
import astar
import units

class Worker(units.Unit):
    """The container for the worker unit."""
    def __init__(self, unit, gc, maps, my_units):
        super().__init__(unit, gc)
        self._maps = maps
        self._my_units = my_units

        self._blueprint_to_build_on = None
        self._karbonite_to_mine = None
        self._path_to_follow = None
        self._nearby_karbonite_locations = []

    def generate_tree(self):
        """Generates the tree for the worker."""
        tree = bt.FallBack()

        # Build on adjacent blueprints
        build = bt.Sequence()
        build.add_child(self.BlueprintAdjacent(self))
        build.add_child(self.BuildBlueprint(self))
        tree.add_child(build)

        # Avoid enemies
        enemies = bt.Sequence()
        enemies.add_child(self.EnemyVisible(self))
        enemies.add_child(self.MoveAwayFromEnemy(self))
        tree.add_child(enemies)

        # Move towards blueprints with no workers
        #find_blueprint = bt.Sequence()

        #tree.add_child(find_blueprint)

        # Add blueprints
        add_blueprint = bt.Sequence()
        add_blueprint.add_child(self.NeedAnotherFactory(self))
        add_blueprint.add_child(self.EnoughKarboniteToBuild(self))
        add_blueprint.add_child(self.AddBlueprint(self))
        tree.add_child(add_blueprint)

        # Mine karbonite
        karbonite = bt.FallBack()
        adjacent_karbonite_sequence = bt.Sequence()
        adjacent_karbonite_sequence.add_child(self.KarboniteInAdjacentCell(self))
        adjacent_karbonite_sequence.add_child(self.HarvestKarbonite(self))
        no_adj_karbonite_sequence = bt.Sequence()
        no_adj_karbonite_sequence.add_child(self.KarboniteExists(self))
        path_fallback = bt.FallBack()
        path_following_sequence = bt.Sequence()
        path_following_sequence.add_child(self.ExistsPath(self))
        path_following_sequence.add_child(self.MoveOnPath(self))
        create_path_fallback = bt.FallBack()
        create_path_sequence = bt.Sequence()
        create_path_sequence.add_child(self.NearbyKarboniteCells(self))
        create_path_sequence.add_child(self.CreatePath(self))
        create_path_fallback.add_child(create_path_sequence)
        create_path_fallback.add_child(self.FindNearbyKarboniteCells(self))
        path_fallback.add_child(path_following_sequence)
        path_fallback.add_child(create_path_fallback)
        no_adj_karbonite_sequence.add_child(path_fallback)

        karbonite.add_child(adjacent_karbonite_sequence)
        karbonite.add_child(no_adj_karbonite_sequence)
        karbonite.add_child(self.MoveRandomly(self))
        tree.add_child(karbonite)

        return tree

    ############
    # BUILDING #
    ############
    class BlueprintAdjacent(bt.Condition):
        """Determines if there is a blueprint in an adjacent square."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            # Already has a factory that it is building on
            blueprint = self.__outer.get_friendly_unit(self.__outer._blueprint_to_build_on)
            worker = self.__outer.unit()
            if blueprint and self.__outer._gc.can_build(worker.id, blueprint.id) :
                return True
            else:
                self.__outer._blueprint_to_build_on = None


            # Look for factories that are not built yet
            location = worker.location
            if location.is_on_map():
                nearby_factories = self.__outer._gc.sense_nearby_units_by_type(location.map_location(), 2, bc.UnitType.Factory)
                for factory in nearby_factories:
                    if self.__outer._gc.can_build(worker.id, factory.id):
                        # Found factory
                        self.__outer._blueprint_to_build_on = factory.id
                        return True
            return False

    class BuildBlueprint(bt.Action):
        """Builds on a blueprint that has been found adjacent to the worker."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            factory = self.__outer.get_friendly_unit(self.__outer._blueprint_to_build_on)
            worker = self.__outer.unit()

            # Factory does not exist even though it should
            if not factory:
                self._status = bt.Status.FAIL
            else:
                # Build the factory and check if it is finished
                self.__outer._gc.build(worker.id, factory.id)
                if self.__outer.get_friendly_unit(factory.id).structure_is_built():
                    self.__outer._blueprint_to_build_on = None

                    from factory import Factory
                    self.__outer._my_units.append(Factory(
                        factory.id,
                        self.__outer._gc,
                        self.__outer._maps,
                        self.__outer._my_units
                    ))

                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.RUNNING

    ##################
    # ENEMY HANDLING #
    ##################

    class EnemyVisible(bt.Condition):
        """Determines if there is a enemy unit in visible range."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            worker = self.__outer.unit()
            location = worker.location
            if location.is_on_map():
                # Determines if we can see some enemy units beside workers and factories.
                enemy_team = bc.Team.Red if self.__outer._gc.team() == bc.Team.Blue else bc.Team.Blue
                nearby_enemy_units = self.__outer._gc.sense_nearby_units_by_team(location.map_location(), worker.vision_range, enemy_team)
                for enemy in nearby_enemy_units:
                    if enemy.unit_type != bc.UnitType.Factory and enemy.unit_type != bc.UnitType.Worker:
                        return True
            return False

    class MoveAwayFromEnemy(bt.Action):
        """Moves away from enemy units."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            worker = self.__outer.unit()
            enemy = None
            location = worker.location
            if location.is_on_map():
                # Determines if we can see some enemy units beside workers and factories.
                enemy_team = bc.Team.Red if self.__outer._gc.team() == bc.Team.Blue else bc.Team.Blue
                nearby_enemy_units = self.__outer._gc.sense_nearby_units_by_team(location.map_location(), worker.vision_range, enemy_team)
                for nearby_enemy in nearby_enemy_units:
                    if nearby_enemy.unit_type != bc.UnitType.Factory and nearby_enemy.unit_type != bc.UnitType.Worker:
                        enemy = nearby_enemy
                        break

            if enemy:
                enemy_direction = worker.location.map_location().direction_to(enemy.location.map_location())
                opposite_direction_position = worker.location.map_location().subtract(enemy_direction)
                opposite_direction = worker.location.map_location().direction_to(opposite_direction_position)
                if self.__outer._gc.is_move_ready(worker.id) and self.__outer._gc.can_move(worker.id, opposite_direction):
                    self.__outer._gc.move_robot(worker.id, opposite_direction)
                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.FAIL

    ##################
    # ADD BLUEPRINTS #
    ##################

    class NeedAnotherFactory(bt.Condition):
        """Determines if we need another Factory."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return strategy.Strategy.getInstance().getCurrentUnit(bc.UnitType.Factory) < strategy.Strategy.getInstance().getMaxUnit(bc.UnitType.Factory)

    class EnoughKarboniteToBuild(bt.Condition):
        """Determines if we have enought karbonite to build a Factory."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return self.__outer._gc.karbonite() >= bc.UnitType.Factory.blueprint_cost()

    class AddBlueprint(bt.Action):
        """Adds one blueprint to any of the adjacent cells if possible."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            blueprint_added = False
            worker = self.__outer.unit()
            for dir in list(bc.Direction):
                if self.__outer._gc.can_blueprint(worker.id, bc.UnitType.Factory, dir):
                    proposed_placement = worker.location.map_location().add(dir)

                    # Check that we have no adjacent factories.
                    factory_too_close = False
                    for unit in self.__outer._gc.sense_nearby_units_by_team(proposed_placement, 2, self.__outer._gc.team()):
                        if unit.unit_type == bc.UnitType.Factory:
                            factory_too_close = True
                    if factory_too_close:
                        continue

                    # Check that we are not adjacent to impassable terrain
                    edge_amount = 0
                    map = self.__outer._maps['terrain_map']
                    width = len(map)
                    height = len(map[0])
                    x = proposed_placement.x
                    y = proposed_placement.y
                    if (x-1 < 0 or y-1 < 0 or not map[x-1][y-1]) and (x+1 >= width or y+1 >= height or not map[x+1][y+1]):
                        continue
                    if (y-1 < 0 or not map[x][y-1]) and (y+1 >= height or not map[x][y+1]):
                        continue
                    if (x+1 >= width or y-1 < 0 or not map[x+1][y-1]) and (x-1 < 0 or y+1 >= height or not map[x-1][y+1]):
                        continue
                    if (x-1 < 0 or not map[x-1][y]) and (x+1 >= width or not map[x+1][y]):
                        continue

                    self.__outer._gc.blueprint(worker.id, bc.UnitType.Factory, dir)
                    blueprint_added = True
                    break
            if blueprint_added:
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL

    ##############
    # HARVESTING #
    ##############

    class KarboniteInAdjacentCell(bt.Condition):
        """Check if there is karbonite in any adjacent cells."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            worker = self.__outer.unit()
            if self.__outer._karbonite_to_mine and self.__outer._gc.can_harvest(
                worker.id,
                self.__outer._karbonite_to_mine
            ):
                return True
            else:
                self.__outer.karbonite_to_mine = None

            for dir in list(bc.Direction):
                if self.__outer._gc.can_harvest(worker.id, dir):
                    self.__outer._karbonite_to_mine = dir
                    return True
            return False

    class HarvestKarbonite(bt.Action):
        """Harvest karbonite in any of the adjacent cells."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            karbonite_direction = self.__outer._karbonite_to_mine

            # Karbonite does not exist even though it should
            if not karbonite_direction:
                self._status = bt.Status.FAIL
            else:
                # Harvest the karbonite and check if deposit is empty
                worker = self.__outer.unit()
                self.__outer._gc.harvest(worker.id, karbonite_direction)
                amount = worker.worker_harvest_amount()
                karbonite_location = worker.location.map_location().add(karbonite_direction)
                self.__outer._maps['karbonite_map'][karbonite_location.x][karbonite_location.y] = max(
                    self.__outer._maps['karbonite_map'][karbonite_location.x][karbonite_location.y] - amount,
                    0
                )
                if self.__outer._maps['karbonite_map'][karbonite_location.x][karbonite_location.y] == 0:
                    self.__outer._karbonite_to_mine = None
                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.RUNNING

    class KarboniteExists(bt.Condition):
        """Check if there is any karbonite left on the map."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            for column in self.__outer._maps['karbonite_map']:
                for karbonite_in_cell in column:
                    if karbonite_in_cell > 0:
                        return True
            return False

    class ExistsPath(bt.Condition):
        """Check if we have a path to follow."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            if self.__outer._path_to_follow:
                return True
            else:
                return False

    class MoveOnPath(bt.Action):
        """Move on the current path."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            next_point = self.__outer._path_to_follow[0]
            worker = self.__outer.unit()
            unit_map_location = worker.location.map_location()
            move_direction = unit_map_location.direction_to(next_point)
            if self.__outer._gc.can_move(worker.id, move_direction):
                self._status = bt.Status.RUNNING
                if self.__outer._gc.is_move_ready(worker.id):
                    self.__outer._gc.move_robot(worker.id, move_direction)
                    self.__outer._path_to_follow.pop(0)
                    if len(self.__outer._path_to_follow) == 1:
                        self.__outer._path_to_follow = None
                        self._status = bt.Status.SUCCESS
            else:
                self.__outer._path_to_follow = None
                self._status = bt.Status.FAIL

    class NearbyKarboniteCells(bt.Condition):
        """Check if we have some karbonite cell saved to move towards."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return len(self.__outer._nearby_karbonite_locations) > 0

    class CreatePath(bt.Action):
        """Create aStar path to first point in the NearbyKarboniteCells list."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            karbonite_location = self.__outer._nearby_karbonite_locations.pop(0)
            karbonite_map = self.__outer._maps['karbonite_map']
            my_units_map = self.__outer._maps['my_units_map']

            # Make sure karbonite has not been stolen
            while karbonite_map[karbonite_location.x][karbonite_location.y] == 0 or my_units_map[karbonite_location.x][karbonite_location.y]:
                if len(self.__outer._nearby_karbonite_locations) > 0:
                    karbonite_location = self.__outer._nearby_karbonite_locations.pop(0)
                else:
                    self._status = bt.Status.FAIL
                    return

            terrain_map = self.__outer._maps['terrain_map']
            my_units_map = self.__outer._maps['my_units_map']
            worker = self.__outer.unit()
            unit_map_location = worker.location.map_location()
            path = astar.astar(terrain_map, my_units_map, unit_map_location, karbonite_location)
            if len(path) > 0:
                path.pop(0) # Remove the point the unit is already on
                self.__outer._path_to_follow = path
                self._status = bt.Status.SUCCESS
            else:
                self.__outer._path_to_follow = None
                self._status = bt.Status.FAIL

    class FindNearbyKarboniteCells(bt.Action):
        """Find nearby cells with karbonite by expanding manhattan distance"""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            karbonite_map = self.__outer._maps['karbonite_map']
            width = len(karbonite_map)
            height = len(karbonite_map[0])
            length = 2
            worker = self.__outer.unit()
            location = worker.location.map_location()
            cells_left = True

            while cells_left and len(self.__outer._nearby_karbonite_locations) <= 3:
                cells_left = False
                for x in range(-length, length + 1):
                    for y in range(-length, length + 1):
                        # Already checked these values
                        if abs(x) <= length-1 and abs(y) <= length-1:
                            continue

                        possible_location = location.translate(x, y)

                        # Check if location is outside of the map
                        if possible_location.x < 0 or possible_location.y < 0 or possible_location.x >= width or possible_location.y >= height:
                            continue

                        cells_left = True

                        # Determine if there is karbonite at the location
                        if karbonite_map[possible_location.x][possible_location.y] > 0:
                            self.__outer._nearby_karbonite_locations.append(possible_location)
                length += 1

            if (len(self.__outer._nearby_karbonite_locations) > 0):
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL

    class MoveRandomly(bt.Action):
        """Move in some random direction."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            worker = self.__outer.unit()
            random_dir = random.choice(list(bc.Direction))
            if self.__outer._gc.is_move_ready(worker.id) and self.__outer._gc.can_move(worker.id, random_dir):
                self.__outer._gc.move_robot(worker.id, random_dir)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL
