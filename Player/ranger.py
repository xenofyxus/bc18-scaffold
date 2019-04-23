import battlecode as bc
import behaviour_tree as bt
import random
import units
import math
import astar
import strategy

class Ranger(units.Unit):
    """The container for the ranger unit."""
    def __init__(self, unit, gc, maps):
        super().__init__(unit, gc)
        self._targeted_enemy = None
        self._targeted_location = None
        self._path_to_follow = None
        self._maps = maps

    def generate_tree(self):
        """Generates the tree for the ranger."""
        tree = bt.FallBack()

        # Attack or chase/run from enemies
        enemy_handling = bt.Sequence()
        enemy_visible = self.EnemyVisible(self)
        enemy_handling.add_child(enemy_visible)

        enemy_fallback = bt.FallBack()
        enemy_in_range = bt.Sequence()
        enemy_in_attack_range = self.EnemyInAttackRange(self)
        enemy_in_range.add_child(enemy_in_attack_range)
        attack = self.Attack(self)
        enemy_in_range.add_child(attack)

        enemy_close = bt.Sequence()
        enemy_too_close = self.EnemyTooClose(self)
        enemy_close.add_child(enemy_too_close)
        move_away = self.MoveAway(self)
        enemy_close.add_child(move_away)
        enemy_close.add_child(enemy_in_range)
        enemy_fallback.add_child(enemy_close)

        enemy_far = bt.Sequence()
        enemy_too_far = self.EnemyTooFar(self)
        enemy_far.add_child(enemy_too_far)
        move_towards = self.MoveTowards(self)
        enemy_far.add_child(move_towards)
        enemy_far.add_child(enemy_in_range)
        enemy_fallback.add_child(enemy_far)

        enemy_fallback.add_child(enemy_in_range)
        enemy_handling.add_child(enemy_fallback)
        tree.add_child(enemy_handling)

        move_fallback = bt.FallBack()
        move_sequence = bt.Sequence()
        move_sequence.add_child(self.OffensiveStrategy(self))
        move_sequence.add_child(self.FindClosestEnemy(self))
        move_sequence.add_child(self.CreatePath(self))
        move_sequence.add_child(self.MoveOnPath(self))
        move_fallback.add_child(move_sequence)
        move_fallback.add_child(self.MoveRandomly(self))
        tree.add_child(move_fallback)

        return tree

    ##################
    # ENEMY HANDLING #
    ##################

    class EnemyVisible(bt.Condition):
        """Check if there is an enemy in range of the ranger."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            ranger = self.__outer.unit()
            range = ranger.vision_range
            location = ranger.location.map_location()
            team = ranger.team
            enemy_team = bc.Team.Red if team == bc.Team.Blue else bc.Team.Blue

            nearby_units = self.__outer._gc.sense_nearby_units_by_team(location, range, enemy_team)

            # No enemy visible
            if not nearby_units:
                return False

            # Look for the enemy closest to the ranger with lowest health
            best_enemy = nearby_units[0]
            best_enemy_distance = location.distance_squared_to(best_enemy.location.map_location())
            for unit in nearby_units:
                enemy_distance = location.distance_squared_to(unit.location.map_location())
                if enemy_distance < best_enemy_distance:
                    best_enemy = unit
                    best_enemy_distance = enemy_distance
                elif enemy_distance == best_enemy_distance:
                    if unit.health < best_enemy.health:
                        best_enemy = unit
                        best_enemy_distance = enemy_distance

            self.__outer._targeted_enemy = best_enemy.id
            return True

    class EnemyInAttackRange(bt.Condition):
        """Check if the enemy is in attack range of the ranger."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            ranger = self.__outer.unit()
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)

            enemy_distance = ranger.location.map_location().distance_squared_to(enemy.location.map_location())

            return enemy_distance > ranger.ranger_cannot_attack_range() and enemy_distance <= ranger.attack_range()

    class Attack(bt.Action):
        """Attacks the enemy targeted by the ranger."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)
            ranger = self.__outer.unit()
            enemies_map = self.__outer._maps['enemy_units_map']

            if not enemy:
                self._status = bt.Status.FAIL
            else:
                if self.__outer._gc.is_attack_ready(ranger.id) and self.__outer._gc.can_attack(ranger.id, enemy.id):
                    self.__outer._gc.attack(ranger.id, enemy.id)
                    self._status = bt.Status.SUCCESS
                     # Remove enemy from enemy_units_map if it died
                    location = ranger.location.map_location()
                    enemy_team = bc.Team.Red if ranger.team == bc.Team.Blue else bc.Team.Blue
                    killed_enemy = True
                    nearby_units = self.__outer._gc.sense_nearby_units_by_team(location, ranger.attack_range(), enemy_team)
                    for nearby_unit in nearby_units:
                        if nearby_unit.id == enemy.id:
                            killed_enemy = False
                            break
                    if killed_enemy:
                        enemy_location = enemy.location.map_location()
                        enemies_map[enemy_location.x][enemy_location.y] = None
                else:
                    self._status = bt.Status.RUNNING

    class EnemyTooClose(bt.Condition):
        """Check if the enemy is too close to the ranger."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            ranger = self.__outer.unit()
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)

            enemy_distance = ranger.location.map_location().distance_squared_to(enemy.location.map_location())

            return enemy_distance <= (ranger.attack_range() / 2)

    class MoveAway(bt.Action):
        """Moves away from the enemy."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)
            ranger = self.__outer.unit()

            if not enemy:
                self._status = bt.Status.FAIL
            else:
                enemy_direction = ranger.location.map_location().direction_to(enemy.location.map_location())
                opposite_direction_position = ranger.location.map_location().subtract(enemy_direction)
                opposite_direction = ranger.location.map_location().direction_to(opposite_direction_position)
                if self.__outer._gc.is_move_ready(ranger.id) and self.__outer._gc.can_move(ranger.id, opposite_direction):
                    self.__outer._gc.move_robot(ranger.id, opposite_direction)
                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.FAIL

    class EnemyTooFar(bt.Condition):
        """Check if the enemy is too far from the ranger."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            ranger = self.__outer.unit()
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)

            enemy_distance = ranger.location.map_location().distance_squared_to(enemy.location.map_location())

            return enemy_distance > ranger.attack_range()

    class MoveTowards(bt.Action):
        """Moves towards the enemy."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            enemy = self.__outer.get_enemy_unit(self.__outer._targeted_enemy)
            ranger = self.__outer.unit()

            if not enemy:
                self._status = bt.Status.FAIL
            else:
                enemy_direction = ranger.location.map_location().direction_to(enemy.location.map_location())
                if self.__outer._gc.is_move_ready(ranger.id) and self.__outer._gc.can_move(ranger.id, enemy_direction):
                    self.__outer._gc.move_robot(ranger.id, enemy_direction)
                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.FAIL

    class OffensiveStrategy(bt.Condition):
        """Moves towards the enemy."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return strategy.Strategy.getInstance().battle_strategy == strategy.BattleStrategy.Offensive

    class FindClosestEnemy(bt.Action):
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            ranger = self.__outer.unit()
            ranger_location = ranger.location.map_location()
            enemies_map = self.__outer._maps['enemy_units_map']

            min_distance = math.inf
            closest_unit_location = None
            for x in range(len(enemies_map)):
                for y in range(len(enemies_map[0])):
                    enemy = enemies_map[x][y]
                    if enemy:
                        current_distance = ranger_location.distance_squared_to(enemy.location.map_location())

                        # check just in case enemy desingregated its unit or we failed to attack for any reason
                        if current_distance < ranger.vision_range:
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
            ranger = self.__outer.unit()
            terrain_map = self.__outer._maps['terrain_map']
            my_units_map = self.__outer._maps['my_units_map']
            path = astar.astar(terrain_map, my_units_map, ranger.location.map_location(), location, max_path_length=5)

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
            ranger = self.__outer.unit()
            unit_map_location = ranger.location.map_location()
            move_direction = unit_map_location.direction_to(next_point)
            if self.__outer._gc.can_move(ranger.id, move_direction):
                self._status = bt.Status.RUNNING
                if self.__outer._gc.is_move_ready(ranger.id):
                    self.__outer._gc.move_robot(ranger.id, move_direction)
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
            ranger = self.__outer.unit()
            if self.__outer._gc.is_move_ready(ranger.id) and self.__outer._gc.can_move(ranger.id, random_dir):
                self.__outer._gc.move_robot(ranger.id, random_dir)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL
