import battlecode as bc
import behaviour_tree as bt
import random
import units
import math
import astar
import strategy


class Mage(units.Unit):
    """The container for the mage unit."""
    def __init__(self, unit, gc, maps):
        super().__init__(unit, gc)
        self._targeted_enemy = None
        self._maps = maps

    def generate_tree(self):
        """Generates the tree for the mage."""
        tree = bt.FallBack()

        enemy_visible_sequence = bt.Sequence()
        enemy_visible_sequence.add_child(self.EnemyVisible(self))
        attack_sequence = bt.Sequence()
        attack_sequence.add_child(self.FindBestTarget(self))
        attack_sequence.add_child(self.Attack(self))
        enemy_visible_sequence.add_child(attack_sequence)

        enemies_not_visible_sequence = bt.Sequence()

        move_fallback = bt.FallBack()
        move_sequence = bt.Sequence()
        move_sequence.add_child(self.OffensiveStrategy(self))
        move_sequence.add_child(self.FindClosestEnemy(self))
        move_sequence.add_child(self.CreatePath(self))
        move_sequence.add_child(self.MoveOnPath(self))
        move_fallback.add_child(move_sequence)
        move_fallback.add_child(self.MoveRandomly(self))

        enemies_not_visible_sequence.add_child(move_fallback)
        enemies_not_visible_sequence.add_child(enemy_visible_sequence)

        tree.add_child(enemy_visible_sequence)
        tree.add_child(enemies_not_visible_sequence)

        return tree

    ##################
    # ENEMY HANDLING #
    ##################

    class EnemyVisible(bt.Condition):
        """Check if there is an enemy in range of the mage."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            mage = self.__outer.unit()
            range = mage.vision_range
            location = mage.location.map_location()
            my_team = mage.team
            enemy_team = bc.Team.Red if my_team == bc.Team.Blue else bc.Team.Blue

            nearby_enemy_units = self.__outer._gc.sense_nearby_units_by_team(location, range, enemy_team)

            return len(nearby_enemy_units) > 0

    class FindBestTarget(bt.Action):
        """Find the best target in range of the mage."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            mage = self.__outer.unit()
            range = mage.vision_range
            location = mage.location.map_location()
            my_team = mage.team
            enemy_team = bc.Team.Red if my_team == bc.Team.Blue else bc.Team.Blue
            my_units_map = self.__outer._maps['my_units_map']

            best_target_id = None
            best_target_hp = math.inf
            best_target_nr_enemies = 0
            nearby_enemy_units = self.__outer._gc.sense_nearby_units_by_team(location, range, enemy_team)
            for enemy in nearby_enemy_units:
                current_target_nr_enemies = 0
                current_target_hp = 0
                enemy_location = enemy.location.map_location()

                # Get the amount of enemies adjacent to this one.
                for dir in list(bc.Direction):
                    adjacent_location = enemy_location.add(dir)
                    if adjacent_location.x < 0 or adjacent_location.x >= len(my_units_map) or adjacent_location.y < 0 or adjacent_location.y >= len(my_units_map[0]):
                        continue
                    if self.__outer._gc.has_unit_at_location(adjacent_location) and not my_units_map[adjacent_location.x][adjacent_location.y]:
                        current_target_nr_enemies += 1
                        current_target_hp += self.__outer._gc.sense_unit_at_location(adjacent_location).health
                    elif self.__outer._gc.has_unit_at_location(adjacent_location) and my_units_map[adjacent_location.x][adjacent_location.y]:
                        current_target_nr_enemies -= 1
                        current_target_hp += 2*self.__outer._gc.sense_unit_at_location(adjacent_location).health

                # Update best target if more enemies were found.
                if current_target_nr_enemies > best_target_nr_enemies:
                    best_target_nr_enemies = current_target_nr_enemies
                    best_target_hp = current_target_hp
                    best_target_id = enemy.id
                elif current_target_nr_enemies == best_target_nr_enemies and current_target_hp < best_target_hp:
                    # If the current enemy has the same number of adjacent enemies as the best, pick the group
                    # with the lowest total HP.
                    best_target_nr_enemies = current_target_nr_enemies
                    best_target_hp = current_target_hp
                    best_target_id = enemy.id

            if best_target_id:
                self.__outer._targeted_enemy = best_target_id
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL



    class Attack(bt.Action):
        """Attacks the enemy targeted by the mage."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)
            mage = self.__outer.unit()
            enemies_map = self.__outer._maps['enemy_units_map']

            if not enemy:
                self._status = bt.Status.FAIL
            else:
                if self.__outer._gc.is_attack_ready(mage.id) and self.__outer._gc.can_attack(mage.id, enemy.id):
                    self.__outer._gc.attack(mage.id, enemy.id)
                    self._status = bt.Status.SUCCESS

                     # Remove enemy from enemy_units_map if it died
                    enemy_location = enemy.location.map_location()
                    for dir in list(bc.Direction):
                        adjacent_location = enemy_location.add(dir)
                        if adjacent_location.x < 0 or adjacent_location.x >= len(enemies_map) or adjacent_location.y < 0 or adjacent_location.y >= len(enemies_map[0]):
                            continue
                        if not self.__outer._gc.has_unit_at_location(adjacent_location) or self.__outer._gc.sense_unit_at_location(adjacent_location).team == mage.team:
                            enemies_map[adjacent_location.x][adjacent_location.y] = None

                else:
                    self._status = bt.Status.RUNNING



    class OffensiveStrategy(bt.Condition):
        """Moves towards the enemy."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return strategy.Strategy.battle_strategy == strategy.BattleStrategy.Offensive



    class FindClosestEnemy(bt.Action):
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            mage = self.__outer.unit()
            mage_location = mage.location.map_location()
            enemies_map = self.__outer._maps['enemy_units_map']

            min_distance = math.inf
            closest_unit_location = None
            for x in range(len(enemies_map)):
                for y in range(len(enemies_map[0])):
                    enemy = enemies_map[x][y]
                    if enemy:
                        current_distance = mage_location.distance_squared_to(enemy.location.map_location())

                        # check just in case enemy desingregated its unit or we failed to attack for any reason
                        if current_distance < mage.vision_range:
                            continue
                        if current_distance < min_distance:
                            min_distance = current_distance
                            closest_unit_location = enemy.location.map_location()

            if closest_unit_location:
                self.__outer._targeted_location = closest_unit_location
                self._status = bt.Status.SUCCESS
            else:
                self.__outer._targeted_location = None
                self._status = bt.Status.FAIL

    class CreatePath(bt.Action):
        """Create the path to the closest injured friend."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            location = self.__outer._targeted_location
            mage = self.__outer.unit()
            terrain_map = self.__outer._maps['terrain_map']
            my_units_map = self.__outer._maps['my_units_map']
            path = astar.astar(terrain_map, my_units_map, mage.location.map_location(), location, max_path_length=5)

            if len(path) > 0:
                path.pop(0) # Remove the point the unit is already on.
                self.__outer._path_to_follow = path
                self._status = bt.Status.SUCCESS
            else:
                self.__outer._path_to_follow = None
                self._status = bt.Status.FAIL

    class MoveOnPath(bt.Action):
        """Move towards the closest known enemy position."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            next_point = self.__outer._path_to_follow[0]
            mage = self.__outer.unit()
            unit_map_location = mage.location.map_location()
            move_direction = unit_map_location.direction_to(next_point)
            if self.__outer._gc.can_move(mage.id, move_direction):
                self._status = bt.Status.RUNNING
                if self.__outer._gc.is_move_ready(mage.id):
                    self.__outer._gc.move_robot(mage.id, move_direction)
                    self.__outer._path_to_follow.pop(0)
                    if len(self.__outer._path_to_follow) == 1:
                        self.__outer._path_to_follow = None
                        self._status = bt.Status.SUCCESS
            else:
                self.__outer._path_to_follow = None
                self._status = bt.Status.FAIL

    #################
    # MOVE RANDOMLY #
    #################

    class MoveRandomly(bt.Action):
        """Move in some random direction."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            random_dir = random.choice(list(bc.Direction))
            mage = self.__outer.unit()
            if self.__outer._gc.is_move_ready(mage.id) and self.__outer._gc.can_move(mage.id, random_dir):
                self.__outer._gc.move_robot(mage.id, random_dir)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL
