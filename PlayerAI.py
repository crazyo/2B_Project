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
