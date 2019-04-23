import battlecode as bc
from abc import ABC, abstractmethod
import behaviour_tree as bt
import random
import strategy
import astar

class Unit(ABC):
    """An abstract class container for units. Contains the tree for the unit
    and the battlecode unit reference. Subclasses must implement a tree
    generation function.
    """
    def __init__(self, unit, gc):
        self._unit = unit
        self._gc = gc
        self._tree = self.generate_tree()

    @abstractmethod
    def generate_tree(self):
        pass

    def get_enemy_unit(self, unit_id):
        try:
            return self._gc.unit(unit_id)
        except:
            # Unit not in visible range.
            return None

    def get_friendly_unit(self, unit_id):
        units = self._gc.my_units()
        for unit in units:
            if unit.id == unit_id:
                return unit
        return None

    def unit(self):
        return self.get_friendly_unit(self._unit)

    def run(self):
        """Runs the unit's behaviour tree and returns the result."""
        return self._tree.run()
