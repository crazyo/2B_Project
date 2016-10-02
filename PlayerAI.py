from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *


class PlayerAI:
    def __init__(self):
        pass

    def do_move(self, world, enemy_units, friendly_units):
        for i in range(4):
            cp_loc = world.get_nearest_control_point(friendly_units[i].position).position
            friendly_units[i].move(world.get_next_direction_in_path(friendly_units[i].position, cp_loc))
            enemy_units[i].shielded_turns_remaining = 5

        enemy_units[3].health = 1
        enemy_units[3].shielded_turns_remaining = 1
        print(self.find_enemy_density(world, (1,1),enemy_units, 10))
        print(friendly_units[1].current_weapon_type)

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


    @staticmethod
    def get_indivadule_power_value(unit, range):
        '''
        Returns: the unit's power value based on HP, Sailed and Weapon
        '''


        weapon_point = _get_damage_by_weapon(unit.weaponType, range)
        sheild_turn_point = unit.shielded_turns_remaining ** weapon_point
        sheild_number_point = unit.num_shields *  sheild_turn_point * 5
        HP_point = unit.health
        total_point = weapon_point + sheild_turn_point + sheild_number_point + HP_point
        return total_point

    def _get_damage_by_weapon(type, range):
        if type[0] >= range:
            return type[1]
        else :
            return 0
