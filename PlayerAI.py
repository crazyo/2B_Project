import math

from PythonClientAPI.libs.Game import PointUtils as PU
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.World import *


# just need a number that is small enough
SMALLEST_NUMBER = -100000
OUR_TEAM = None

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
        # TODO:
        #   should I skip control points I already own?
        if cp.controlling_team == OUR_TEAM:
            continue
        distance = world.get_path_length(tile_pos, cp.position)
        _get = _get_mainframe_utility if cp.is_mainframe else _get_control_point_utility
        if distance:
            utility += (_get(world) / distance) ** 2
        # TODO:
        #   should consider taking the tile that control point is on if
        #   there are enemies around so as to occupy more spots
        #   which is considering distance == 0
    return utility

def _get_to_pickup_utility(world, tile_pos):
    utility = 0
    for pickup in world.pickups:
        distance = world.get_path_length(tile_pos, pickup.position)
        _get = _get_repair_kit_utility if pickup.pickup_type == PickupType.REPAIR_KIT else \
            _get_shield_utility if pickup.pickup_type == PickupType.SHIELD else \
            _get_weapon_utility
        if distance:
            utility += (_get(world) / distance) ** 2
        else:
            utility += _get(world) ** 2 * 2
    return utility


def _get_enemy_utility(world, tile_pos, enemy_units):
    utility =  0
    for enemy in enemy_units:
        distance = world.get_path_length(tile_pos, enemy.position)
        enemy_power = PlayerAI.get_indivadule_power_value(world, enemy, tile_pos)
        if distance:
            utility += (enemy_power/distance) ** 2
        else:
            utility += enemy_power ** 2 * 2
    print("_get_enemy_utility:" + str(utility))
    return -1 * utility

# TODO:
#   consider multiple enemies and multiple allies?
def _can_beat(unit, enemy):
    if unit.check_shot_against_enemy(enemy) == ShotResult.CAN_HIT_ENEMY:
        if enemy.current_weapon_type.get_range() < PU.chebyshev_distance(unit.position, enemy.position):
            return True
        num_unit_round = math.ceil(enemy.health / unit.current_weapon_type.get_damage())
        num_enemy_round = math.ceil(unit.health / enemy.current_weapon_type.get_damage())
        if num_unit_round <= num_enemy_round:
            return True
    return False


class PlayerAI:

    def __init__(self):
        pass

    def do_move(self, world, enemy_units, friendly_units):
        # initialization work
        global OUR_TEAM
        OUR_TEAM = friendly_units[0].team

        # list of maps where each map has 3 attributes:
        #     "position": the tile position of this neighbour;
        #     "utility": the utility of this tile;
        #     "unit_index": which unit does this neighbour belong to
        all_moving_units = []
        neighbour_maps_for_all_moving_units = []
        for i in range(len(friendly_units)):
            unit = friendly_units[i]
            # pick up any pickup if unit is on the tile
            if unit.check_pickup_result() == PickupResult.PICK_UP_VALID:
                unit.pickup_item_at_position()
                continue

            # shoot any enemy that is in range
            # TODO:
            #   need to calculate utility as well actually
            shot = False
            for enemy in enemy_units:
                if unit.check_shot_against_enemy(enemy) == ShotResult.CAN_HIT_ENEMY:
                    unit.shoot_at(enemy)
                    shot = True
                    break
            if shot:
                continue

            # moving...
            all_moving_units.append(i)
            neighbours = [(unit.position[0] - 1, unit.position[1] - 1),
                          (unit.position[0] - 1, unit.position[1]),
                          (unit.position[0] - 1, unit.position[1] + 1),
                          (unit.position[0], unit.position[1] - 1),
                          (unit.position[0], unit.position[1] + 1),
                          (unit.position[0] + 1, unit.position[1] - 1),
                          (unit.position[0] + 1, unit.position[1]),
                          (unit.position[0] + 1, unit.position[1] + 1)]
            neighbour_maps_for_current_unit = [
                {
                    "unit_index": i,
                    "position": neighbour,
                    "utility": _get_to_control_point_utility(world, neighbour) +
                    _get_to_pickup_utility(world, neighbour)
                } for neighbour in neighbours if unit.check_move_in_direction(
                    Direction.from_to(unit.position, neighbour)
                ) == MoveResult.MOVE_VALID
            ]
            neighbour_maps_for_all_moving_units.extend(neighbour_maps_for_current_unit)

        # assign move for each unit considering corporation
        visited_tiles = []
        neighbour_maps_for_all_moving_units.sort(key=lambda x: x["utility"], reverse=True)
        for neighbour in neighbour_maps_for_all_moving_units:
            if (neighbour["unit_index"] not in all_moving_units or
                neighbour["position"] in visited_tiles):
                continue
            unit = friendly_units[neighbour["unit_index"]]
            direction = Direction.from_to(unit.position, neighbour["position"])
            unit.move(direction)
            visited_tiles.append(neighbour["position"])
            all_moving_units.remove(neighbour["unit_index"])

        # remaining units that did not move anywhere
        for unit_index in all_moving_units:
            unit = friendly_units[unit_index]
            # got nothing better to do, might as well fire!
            shot = False
            for enemy in enemy_units:
                # TODO:
                #   pick the weakest enemy!
                if unit.check_shot_against_enemy(enemy) == ShotResult.CAN_HIT_ENEMY:
                    unit.shoot_at(enemy)
                    shot = True
                    break
            # really got nothing to do :-(
            if not shot:
                unit.standby()


    @staticmethod
    def find_weakest_unit(units):
        '''
        Given a list of unites
        Returns: the weakest unit and its corresponding HP, based on the HP, Shields.
        Returns: None if all the unites have Shelds.
        '''
        weakest_unit = units[0]
        lowest_hp = 50
        is_all_sheilds = True;
        for i in range(len(units)):
            if (units[i].shielded_turns_remaining <= 0):
                is_all_sheilds = False
                if (lowest_hp > units[i].health):
                    lowest_hp = units[i].health
                    weakest_unit = units[i]
        if not is_all_sheilds:
            return (weakest_unit, lowest_hp)

    @staticmethod
    def find_unit_with_least_Shields_Turns(units):
        '''
        Given a list of unites
        Returns: the unit that has the least Shields, and its corresponding number of Shields Turns remaining.
        '''
        weakest_unit = units[0]
        least_shielded_turns_remaining = 10

        for i in range(len(units)):
            if (least_shielded_turns_remaining > units[i].shielded_turns_remaining):
                least_shielded_turns_remaining = units[i].shielded_turns_remaining
                weakest_unit = units[i]
        return (weakest_unit, least_shielded_turns_remaining)

    @staticmethod
    def find_closest_unit(world, target_unit, units):
        '''
        Returns: the the closest unit of unites to the target unit, and its corresponding distance.
        '''
        closest_unit = units[0]
        least_distance = 10
        for i in range(len(units)):
            distance = world.get_path_length(target_unit.position, units[i].position)
            if (least_distance > distance):
                least_distance = distance
                closest_unit = units[i]
        return (closest_unit, least_distance)

    @staticmethod
    def find_enemy_density(world, target_location, units, radius):
        '''
        Args:
            world:
            target_location:
            units:
            radius:

        Returns:
        '''
        density = 0
        for i in range(len(units)):
            distance = world.get_path_length(target_location, units[i].position)
            if distance <= radius:
                density += 1
        return density


    BASE_UTILITY_SHIELD_POWER_PER_TURN = 10
    @staticmethod
    def get_indivadule_power_value(world, enemy_unit,position):
        '''
        Returns: the unit's power value based on HP, Sailed and Weapon
        '''

        weapon_point = PlayerAI._get_damage_by_weapon(enemy_unit.current_weapon_type)
        # if the enemy unit can hit the friendly unit
        if ProjectileWeapon.check_shot_against_point(enemy_unit, position, world, enemy_unit.current_weapon_type):
            weapon_point = weapon_point * 10
        sheild_turn_point = enemy_unit.shielded_turns_remaining * PlayerAI.BASE_UTILITY_SHIELD_POWER_PER_TURN
        sheild_number_point = enemy_unit.num_shields *  sheild_turn_point * 5
        HP_point = enemy_unit.health
        total_point = weapon_point + sheild_turn_point + sheild_number_point + HP_point

        return total_point

    @staticmethod
    def _get_damage_by_weapon(weapon_type):
        return weapon_type.value[1]

    '''
    Attacking functions
    '''

    @staticmethod
    def _attack(friendly_unit, enemy_unit):
        check_shot = friendly_unit.check_shot_against_enemy(enemy_unit)
        if check_shot == ShotResult.TARGET_OUT_OF_RANGE or check_shot == ShotResult.BLOCKED_BY_WORLD :
            friendly_unit.move_to_destination(enemy_unit.position)
        elif check_shot == ShotResult.CAN_HIT_ENEMY:
            friendly_unit.shoot_at(enemy_unit)
        else:
            return check_shot




''' TODO List:
0. enemy utility
1. shield activation
2. team strategy - move strongest to enemy's weakest
3. weapon choice
4. hide behind shielded ally
'''
