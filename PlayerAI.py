from PythonClientAPI.libs.Game import PointUtils as PU
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.World import *


# just need a number that is small enough
SMALLEST_NUMBER = -10000

###################################
# utility constants and functions #
###################################
BASE_UTILITY_MAINFRAME = 200
def _get_mainframe_utility(world):
    ''' TODO:
    mainframe utility should change in respect of:
        1. the number of mainframe we have captured
        2. the number of mainframe left for enemy to capture
        3. the total number of mainframes on the map
    '''
    return BASE_UTILITY_MAINFRAME

BASE_UTILITY_CONTROL_POINT = 100
def _get_control_point_utility(world):
    ''' TODO:
    control point utility should change in respect of:
        1. the controlling team of the control point
        2. the game phase (the ability to score points elsewhere)
    '''
    return BASE_UTILITY_CONTROL_POINT

BASE_UTILITY_REPAIR_KIT = 50
def _get_repair_kit_utility(world):
    ''' TODO:
    repair kit utility should change in respect of:
        1. how many health points this unit has left
        2. whether this repair kit could be saved for another ally
        3. whether this repair kit would be taken by an enemy
    '''
    return BASE_UTILITY_REPAIR_KIT

BASE_UTILITY_SHIELD = 30
def _get_shield_utility(world):
    ''' TODO:
    shield utility should change in respect of:
        1. how many shield this unit already has
        2. whether this shield could be saved for another ally
        3. whether this shield would be taken by an enemy
    '''
    return BASE_UTILITY_SHIELD

BASE_UTILITY_WEAPON = 20
def _get_weapon_utility(world):
    ''' TODO:
    weapon utility should change in respect of:
        1. the weapon type
        2. current weapon this unit is holding
        3. whether this weapon could be saved for another ally
        4. whether this weapon would be taken by an enemy
            - if so, what weapon is that enemy currently holding
    '''
    return BASE_UTILITY_WEAPON


def _get_to_control_point_utility(world, tile_pos):
    utility = 0
    for cp in world.control_points:
        distance = PU.chebyshev_distance(tile_pos, cp.position)
        _get = _get_mainframe_utility if cp.is_mainframe else _get_control_point_utility
        if distance:
            utility += (_get(world) / distance) ** 2
        # TODO:
        #   should consider taking the tile that control point is on if
        #   there are enemies around so as to occupy more spots
    return utility

def _get_to_pickup_utility(world, tile_pos):
    utility = 0
    for pickup in world.pickups:
        distance = PU.chebyshev_distance(tile_pos, pickup.position)
        _get = _get_repair_kit_utility if pickup.pickup_type == PickupType.REPAIR_KIT else \
            _get_shield_utility if pickup.pickup_type == PickupType.SHIELD else \
            _get_weapon_utility
        if distance:
            utility += (_get(world) / distance) ** 2
        else:
            utility += _get(world) ** 2 * 2
    return utility


class PlayerAI:

    def __init__(self):
        pass

    def do_move(self, world, enemy_units, friendly_units):
        for unit in friendly_units:
            # pick up any pickup if unit is on the tile
            if unit.check_pickup_result() == PickupResult.PICK_UP_VALID:
                unit.pickup_item_at_position()
                continue

            neighbours = [(unit.position[0] - 1, unit.position[1] - 1),
                          (unit.position[0] - 1, unit.position[1]),
                          (unit.position[0] - 1, unit.position[1] + 1),
                          (unit.position[0], unit.position[1] - 1),
                          (unit.position[0], unit.position[1] + 1),
                          (unit.position[0] + 1, unit.position[1] - 1),
                          (unit.position[0] + 1, unit.position[1]),
                          (unit.position[0] + 1, unit.position[1] + 1)]
            neighbour_direction_map = {}
            for neighbour in neighbours:
                neighbour_direction_map[neighbour] = Direction.from_to(unit.position, neighbour)

            best_neighbour_utility = SMALLEST_NUMBER
            best_neighbour_direction = None
            for neighbour, direction in neighbour_direction_map.items():
                if world.can_move_from_point_in_direction(unit.position, direction):
                    utility = _get_to_control_point_utility(world, neighbour) + \
                        _get_to_pickup_utility(world, neighbour)
                    if utility > best_neighbour_utility:
                        best_neighbour_utility = utility
                        best_neighbour_direction = direction

            if best_neighbour_direction:
                unit.move(best_neighbour_direction)
            else:
                unit.move(Direction.NOWHERE)
