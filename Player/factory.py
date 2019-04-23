import battlecode as bc
import behaviour_tree as bt
import random
import strategy
import units
from worker import Worker
from knight import Knight
from healer import Healer
from ranger import Ranger
from mage import Mage


class Factory(units.Unit):
    """The container for the factory unit."""
    def __init__(self, unit, gc, maps, my_units):
        super().__init__(unit, gc)
        self._maps = maps
        self._my_units = my_units

    def generate_tree(self):
        tree = bt.Sequence()

        unload = self.Unload(self)
        tree.add_child(unload)

        build_fallback = bt.FallBack()
        workers = bt.Sequence()
        need_more_workers = self.NeedMoreWorkers(self)
        workers.add_child(need_more_workers)
        can_build_worker = self.CanBuildWorker(self)
        workers.add_child(can_build_worker)
        build_worker = self.BuildWorker(self)
        workers.add_child(build_worker)
        build_fallback.add_child(workers)

        non_workers = bt.Sequence()
        can_build = self.CanBuild(self)
        non_workers.add_child(can_build)
        non_workers_fallback = bt.FallBack()
        local_damage = bt.Sequence()
        damaged_units = self.DamagedUnits(self)
        local_damage.add_child(damaged_units)
        no_healer_nearby = self.NoHealerNearby(self)
        local_damage.add_child(no_healer_nearby)
        build_healer = self.BuildHealer(self)
        local_damage.add_child(build_healer)
        non_workers_fallback.add_child(local_damage)
        local_enemies = bt.Sequence()
        enemies_nearby = self.EnemiesNearby(self)
        local_enemies.add_child(enemies_nearby)
        build_knight = self.BuildKnight(self)
        local_enemies.add_child(build_knight)
        non_workers_fallback.add_child(local_enemies)
        build_global = self.BuildGlobal(self)
        non_workers_fallback.add_child(build_global)
        non_workers.add_child(non_workers_fallback)
        build_fallback.add_child(non_workers)
        tree.add_child(build_fallback)

        return tree

    ##########
    # UNLOAD #
    ##########

    class Unload(bt.Action):
        """Unloads a unit from the factory if it exists."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            factory = self.__outer.unit()
            garrison = factory.structure_garrison()
            if garrison:
                direction = random.choice(list(bc.Direction))
                if self.__outer._gc.can_unload(factory.id, direction):
                    self.__outer._gc.unload(factory.id, direction)

                    location = factory.location.map_location().add(direction)
                    unit = self.__outer._gc.sense_unit_at_location(location)

                    if unit: # TODO: Add other unit types' tree containers
                        strategy.Strategy.getInstance().removeInProduction(unit.unit_type)
                        strategy.Strategy.getInstance().addUnit(unit.unit_type)
                        if unit.unit_type == bc.UnitType.Worker:
                            self.__outer._my_units.append(Worker(
                                unit.id,
                                self.__outer._gc,
                                self.__outer._maps,
                                self.__outer._my_units
                            ))
                        elif unit.unit_type == bc.UnitType.Knight:
                            self.__outer._my_units.append(Knight(
                                unit.id,
                                self.__outer._gc,
                                self.__outer._maps
                            ))
                        elif unit.unit_type == bc.UnitType.Healer:
                            self.__outer._my_units.append(Healer(
                                unit.id,
                                self.__outer._gc,
                                self.__outer._maps
                            ))
                        elif unit.unit_type == bc.UnitType.Ranger:
                            self.__outer._my_units.append(Ranger(
                                unit.id,
                                self.__outer._gc,
                                self.__outer._maps
                            ))
                        elif unit.unit_type == bc.UnitType.Mage:
                            self.__outer._my_units.append(Mage(
                                unit.id,
                                self.__outer._gc,
                                self.__outer._maps
                            ))
            self._status = bt.Status.SUCCESS

    ###########
    # WORKERS #
    ###########

    class NeedMoreWorkers(bt.Condition):
        """Check if more workers are needed."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return strategy.Strategy.getInstance().getCurrentUnit(bc.UnitType.Worker) < strategy.Strategy.getInstance().getMaxUnit(bc.UnitType.Worker)

    class CanBuildWorker(bt.Condition):
        """Check if resources exist to build a worker."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return self.__outer._gc.karbonite() >= bc.UnitType.Worker.factory_cost()

    class BuildWorker(bt.Action):
        """Builds a worker."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            factory = self.__outer.unit()
            if self.__outer._gc.can_produce_robot(factory.id, bc.UnitType.Worker):
                self.__outer._gc.produce_robot(factory.id, bc.UnitType.Worker)
                strategy.Strategy.getInstance().addInProduction(bc.UnitType.Worker)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL

    ###############
    # NON WORKERS #
    ###############

    class CanBuild(bt.Condition):
        """Check if resources to build exist."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            return self.__outer._gc.karbonite() >= bc.UnitType.Knight.factory_cost()

    class DamagedUnits(bt.Condition):
        """Check if damaged units are nearby."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            factory = self.__outer.unit()
            factory_x = factory.location.map_location().x
            factory_y = factory.location.map_location().y
            for x in range(-5, 6):
                for y in range(-5, 6):
                    if factory_x + x < 0 or factory_x + x >= len(self.__outer._maps['my_units_map']):
                        continue
                    if factory_y + y < 0 or factory_y + y >= len(self.__outer._maps['my_units_map'][factory_x + x]):
                        continue
                    unit = self.__outer._maps['my_units_map'][factory_x + x][factory_y + y]
                    if unit:
                        if unit.unit_type != bc.UnitType.Factory and unit.health <= 0.5 * unit.max_health:
                            return True
            return False

    class NoHealerNearby(bt.Condition):
        """Check if a healer is already in the area."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            factory = self.__outer.unit()
            factory_x = factory.location.map_location().x
            factory_y = factory.location.map_location().y
            for x in range(-5, 6):
                for y in range(-5, 6):
                    if factory_x + x < 0 or factory_x + x >= len(self.__outer._maps['my_units_map']):
                        continue
                    if factory_y + y < 0 or factory_y + y >= len(self.__outer._maps['my_units_map'][factory_x + x]):
                        continue
                    unit = self.__outer._maps['my_units_map'][factory_x + x][factory_y + y]
                    if unit:
                        if unit.unit_type == bc.UnitType.Healer:
                            return False
            return True

    class BuildHealer(bt.Action):
        """Builds a healer."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            factory = self.__outer.unit()
            if self.__outer._gc.can_produce_robot(factory.id, bc.UnitType.Healer):
                self.__outer._gc.produce_robot(factory.id, bc.UnitType.Healer)
                strategy.Strategy.getInstance().addInProduction(bc.UnitType.Healer)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL

    class EnemiesNearby(bt.Condition):
        """Check if an enemy is in the area."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def condition(self):
            factory = self.__outer.unit()
            factory_x = factory.location.map_location().x
            factory_y = factory.location.map_location().y
            for x in range(-5, 6):
                for y in range(-5, 6):
                    if factory_x + x < 0 or factory_x + x >= len(self.__outer._maps['enemy_units_map']):
                        continue
                    if factory_y + y < 0 or factory_y + y >= len(self.__outer._maps['enemy_units_map'][factory_x + x]):
                        continue
                    unit = self.__outer._maps['enemy_units_map'][factory_x + x][factory_y + y]
                    if unit:
                        return True
            return False

    class BuildKnight(bt.Action):
        """Builds a knight."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            factory = self.__outer.unit()
            if self.__outer._gc.can_produce_robot(factory.id, bc.UnitType.Knight):
                self.__outer._gc.produce_robot(factory.id, bc.UnitType.Knight)
                strategy.Strategy.getInstance().addInProduction(bc.UnitType.Knight)
                self._status = bt.Status.SUCCESS
            else:
                self._status = bt.Status.FAIL

    class BuildGlobal(bt.Action):
        """Builds a unit depending on what is needed globally."""
        def __init__(self, outer):
            super().__init__()
            self.__outer = outer

        def action(self):
            unit_type = strategy.Strategy.getInstance().unitNeeded()
            if unit_type:
                factory = self.__outer.unit()
                if self.__outer._gc.can_produce_robot(factory.id, unit_type):
                    self.__outer._gc.produce_robot(factory.id, unit_type)
                    strategy.Strategy.getInstance().addInProduction(unit_type)
                    self._status = bt.Status.SUCCESS
                else:
                    self._status = bt.Status.FAIL
            else:
                self._status = bt.Status.FAIL
