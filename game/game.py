
import arcade
import re
import numpy
import random
from typing import Set, List, Dict, Optional
from .data import DATA_DIR, GFX_DIR


GAME_DATA_DIR = DATA_DIR + "/game"

PICTURE_SIZE = 30
BACKGROUND_PIC = 'hinter'
PLAYER_PIC = "figur"
ROBOT_PICS = ["konig"] + ['robot%i' % i for i in range(1, 10)]
PLAYER_PICS = [PLAYER_PIC] + ROBOT_PICS
KEY_PICS = ["schl%i" % i for i in range(1, 10)]
DOOR_PICS = ["tuer%i" % i for i in range(1, 10)]
DIAMOND_PICS = ["diamant%i" % i for i in range(1, 4)]
CODE_PICS = ["code%i" % i for i in range(1, 4)]
COLLECTABLE_PICS = ["speicher", "aetz", "leben"] + KEY_PICS + DIAMOND_PICS
SCORES_PICS = ["punkt%i" % i for i in range(1, 6)]
ERROR_PIC = 'error'  # used for error-displaying

# room count
WORLD_WIDTH = 5
WORLD_HEIGHT = 4
# entity/place count in a room
ROOM_WIDTH = 20
ROOM_HEIGHT = 20
# entity/item/place count in the knapsack
KNAPSACK_WIDTH = 3
KNAPSACK_HEIGHT = 9
KNAPSACK_MAX = 27  # compatibility with Robot1 (9*3)

COMPUTER_CONTROL_INTERVAL = 0.75  # timer-interval for computer player control


class Game:
    def __init__(self):
        self.world = World()
        self.cur_room_idx = 0
        self.human_player = None  # type: Entity
        self.dt_computer = 0.0

    @property
    def cur_room(self):
        return self.world.rooms[self.cur_room_idx]

    def load(self, filename):
        """
        :param str filename:
        """
        self.world.load(filename)
        self.human_player = self.world.find_human_player()

    def draw(self):
        self.cur_room.draw()
        self.human_player.knapsack.draw()

    def on_screen_resize(self):
        for room in self.world.rooms:
            room.on_screen_resize()

    def on_key_arrow(self, relative):
        """
        :param (int,int) relative: (x,y)
        """
        relative = numpy.array(relative)
        self.human_player.move(relative)

    def do_computer_interval(self):
        for player in self.cur_room.find_players():
            if player.name in ROBOT_PICS:
                do_robot_action(robot=player, human=self.human_player)

    def update(self, delta_time):
        """
        Movement and game logic. This is called for every frame.

        :param float delta_time: how much time passed
        """
        self.dt_computer += delta_time
        if self.dt_computer >= COMPUTER_CONTROL_INTERVAL:
            self.dt_computer -= COMPUTER_CONTROL_INTERVAL
            self.do_computer_interval()


class World:
    def __init__(self):
        self.rooms = [Room(world=self, idx=i) for i in range(WORLD_WIDTH * WORLD_HEIGHT)]

    @staticmethod
    def valid_coord(coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: bool
        """
        x, y = coord
        return 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT

    @staticmethod
    def coord_to_idx(coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: int
        """
        assert World.valid_coord(coord)
        x, y = coord
        return y * WORLD_WIDTH + x

    @staticmethod
    def idx_to_coord(idx):
        """
        :param int idx:
        :return: (x,y) coord
        :rtype: numpy.ndarray
        """
        x = idx % WORLD_WIDTH
        y = idx // WORLD_WIDTH
        return numpy.array([x, y])

    def find_human_player(self):
        """
        :rtype: Entity
        """
        for room in self.rooms:
            for player in room.players:
                if player.name == PLAYER_PIC:
                    return player

    def load(self, filename):
        """
        :param str filename:
        """
        loaded_rooms_idxs = set()  # type: Set[int]
        cur_room_idx = None
        cur_place_idx = 0
        for l in open("%s/%s" % (GAME_DATA_DIR, filename)).read().splitlines():
            if cur_room_idx is None:
                m = re.match(r":RAUM([0-9]+)", l)
                assert m, "did not expect %r" % l
                cur_room_idx = int(m.groups()[0]) - 1
                assert 0 <= cur_room_idx < WORLD_WIDTH * WORLD_HEIGHT
                assert cur_room_idx not in loaded_rooms_idxs
                del self.rooms[cur_room_idx].players[:]
                loaded_rooms_idxs.add(cur_room_idx)
                continue
            name = Place.normalize_name(l)
            if name != BACKGROUND_PIC:
                entity = Entity(
                    room=self.rooms[cur_room_idx],
                    room_coord=self.rooms[cur_room_idx].idx_to_coord(cur_place_idx),
                    name=name)
            else:
                entity = None
            if name in PLAYER_PICS:
                if name == PLAYER_PIC:
                    entity.lives = 3
                    entity.knapsack = Room(
                        world=self,
                        width=KNAPSACK_WIDTH, height=KNAPSACK_HEIGHT,
                        screen_offset=(ROOM_WIDTH + 1, 0))
                self.rooms[cur_room_idx].players.append(entity)
            self.rooms[cur_room_idx].places[cur_place_idx].set_entity(entity)
            cur_place_idx += 1
            if cur_place_idx == ROOM_WIDTH * ROOM_HEIGHT:
                cur_room_idx = None
                cur_place_idx = 0
        assert cur_room_idx is None, "last room incomplete"
        assert len(loaded_rooms_idxs) == WORLD_WIDTH * WORLD_HEIGHT, "some room is missing"


class Room:
    def __init__(self, world, idx=None, width=ROOM_WIDTH, height=ROOM_HEIGHT, screen_offset=(0, 0)):
        """
        :param World world:
        :param int|None idx: room idx in the world, such that world.rooms[idx] is self
        :param int width: number of places in width
        :param int height: number of places in height
        :param (int,int) screen_offset: place-size screen offset
        """
        self.world = world
        self.idx = idx
        self.screen_offset = screen_offset
        self.width = width
        self.height = height
        self.places = [Place(room=self, idx=i) for i in range(width * height)]
        self.players = []  # type: List[Entity]
        self.entities_sprite_list = arcade.SpriteList()

    def __repr__(self):
        return "<Room idx=%r>" % (self.idx,)

    def valid_coord(self, coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: bool
        """
        x, y = coord
        return 0 <= x < self.width and 0 <= y < self.height

    def coord_to_idx(self, coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: int
        """
        assert self.valid_coord(coord)
        x, y = coord
        return y * self.width + x

    def idx_to_coord(self, idx):
        """
        :param int idx:
        :return: (x,y) coord
        :rtype: numpy.ndarray
        """
        x = idx % self.width
        y = idx // self.width
        return numpy.array([x, y])

    def get_place(self, coord):
        """
        :param (int,int)|numpy.ndarray coord:
        """
        return self.places[self.coord_to_idx(coord)]

    def reset_place(self, coord):
        """
        :param (int,int)|numpy.ndarray coord:
        """
        self.places[self.coord_to_idx(coord)].reset_entities()

    def draw(self):
        from .app import app
        screen_width = app.window.room_pixel_size * self.width
        screen_height = app.window.room_pixel_size * self.height
        arcade.draw_rectangle_filled(
            center_x=self.screen_offset[0] * app.window.room_pixel_size + screen_width // 2,
            center_y=app.window.height - (
                self.screen_offset[1] * app.window.room_pixel_size + screen_height // 2),
            width=screen_width, height=screen_height,
            color=[127, 127, 127])
        self.entities_sprite_list.draw()

    def on_screen_resize(self):
        del self.entities_sprite_list[:]
        for place in self.places:
            for entity in place.entities:
                entity.reset_sprite()
            if place.entities:
                self.entities_sprite_list.append(place.entities[-1].sprite)

    def count_entities(self):
        """
        :return: total number of entities in this room
        :rtype: int
        """
        c = 0
        for place in self.places:
            c += len(place.entities)
        return c

    def have_entity_name(self, name):
        """
        :param str name:
        :return: whether we have an entity with this name
        :rtype: bool
        """
        for place in self.places:
            for entity in place.entities:
                if entity.name == name:
                    return True
        return False

    def find_free_place(self):
        """
        :return: a place where there is no entity, or None
        :rtype: None|Place
        """
        for place in self.places:
            if not place.entities:
                return place
        return None

    def find_players(self):
        players = []
        for place in self.places:
            for entity in place.entities:
                if entity.name in PLAYER_PICS:
                    players.append(entity)
        return players


class Place:
    def __init__(self, room, idx):
        """
        :param Room room:
        :param int idx:
        """
        self.room = room
        self.idx = idx
        self.entities = []  # type: List[Entity]

    @property
    def x(self):
        return self.idx % ROOM_WIDTH

    @property
    def y(self):
        return self.idx // ROOM_WIDTH

    @property
    def coord(self):
        return numpy.array([self.x, self.y])

    @property
    def top_entity_name(self):
        if self.entities:
            return self.entities[-1].name
        return BACKGROUND_PIC

    @staticmethod
    def normalize_name(name):
        """
        :param str name: e.g. "wand1.bmp" or "wand1.png" or "wand1"
        :return: e.g. "wand1"
        :rtype: str
        """
        if name.endswith(".bmp") or name.endswith(".png"):
            name = name[:-4]
        return name

    def _remove_top_entity_sprite(self):
        if self.entities and self.entities[-1].sprite in self.room.entities_sprite_list:
            self.room.entities_sprite_list.remove(self.entities[-1].sprite)

    def _add_top_entity_sprite(self):
        if self.entities:
            self.room.entities_sprite_list.append(self.entities[-1].sprite)

    def reset_entities(self):
        self._remove_top_entity_sprite()
        del self.entities[:]

    def set_entity(self, entity):
        """
        :param Entity entity:
        """
        self._remove_top_entity_sprite()
        del self.entities[:]
        if entity:
            self.add_entity(entity)

    def add_entity(self, entity):
        """
        :param Entity entity:
        """
        self._remove_top_entity_sprite()
        self.entities.append(entity)
        self._add_top_entity_sprite()
        self.on_add_entity()

    def remove_entity(self, entity):
        """
        :param Entity entity:
        """
        self._remove_top_entity_sprite()
        self.entities.remove(entity)
        self._add_top_entity_sprite()

    def is_free(self):
        return not self.entities

    def is_allowed_to_add_entity(self, entity):
        """
        :param Entity entity:
        :rtype: bool
        """
        return is_allowed_together(self.entities + [entity])

    def on_add_entity(self):
        on_joined_together(world=self.room.world, entities=self.entities)


class Entity:
    def __init__(self, room, room_coord, name):
        """
        :param Room room:
        :param numpy.ndarray room_coord:
        :param str name: e.g. "figur"
        """
        self.room = room
        self.room_coord = room_coord
        self.name = name
        self.knapsack = None  # type: Optional[Room]
        self.scores = 0
        self.lives = 0
        self.is_alive = True
        self.sprite = None  # type: arcade.Sprite
        self.reset_sprite()

    def __repr__(self):
        return "<Entity %r in room %r in place %r>" % (
            self.name, self.room, tuple(self.room_coord))

    def update_sprite_pos(self):
        from .app import app
        self.sprite.left = self.sprite.width * self.room_coord[0] + \
                           self.room.screen_offset[0] * app.window.room_pixel_size
        self.sprite.top = app.window.height - (
            self.sprite.height * self.room_coord[1] +
            self.room.screen_offset[1] * app.window.room_pixel_size)

    def reset_sprite(self):
        from .app import app
        texture = arcade.load_texture(file_name="%s/%s.png" % (GFX_DIR, self.name))
        scale = app.window.room_pixel_size / texture.width
        self.sprite = arcade.Sprite(scale=scale)
        self.sprite.append_texture(texture)
        self.sprite.set_texture(0)
        self.update_sprite_pos()

    @property
    def place(self):
        return self.room.get_place(self.room_coord)

    def can_move(self, relative):
        """
        :param numpy.ndarray relative: (x,y)
        """
        if not self.is_alive:
            return False
        new_coord = self.room_coord + relative
        if not self.room.valid_coord(new_coord):
            return False
        if not self.room.get_place(new_coord).is_allowed_to_add_entity(self):
            return False
        return True

    def move(self, relative):
        """
        :param numpy.ndarray relative: (x,y)
        """
        if not self.can_move(relative):
            return
        self.move_to_place(self.room.get_place(self.room_coord + relative))

    def move_to_place(self, place):
        """
        :param Place place:
        """
        self.place.remove_entity(self)
        self.room = place.room
        self.room_coord = place.coord
        place.add_entity(self)
        self.update_sprite_pos()

    def kill(self):
        if self.lives > 0:
            self.lives -= 1
            return
        self.place.remove_entity(self)
        self.is_alive = False


def is_allowed_together(entities):
    """
    :param list[Entity] entities:
    :rtype: bool
    """
    if len(entities) <= 1:
        return True
    entity_names_map = {}  # type: Dict[str,List[Entity]]
    for entity in entities:
        entity_names_map.setdefault(entity.name, [])
        entity_names_map[entity.name].append(entity)
    if any(["wand%i" % i in entity_names_map for i in range(1, 3)]):
        return False
    if any(["code%i" % i in entity_names_map for i in range(1, 4)]):
        return False
    doors = [door for door in DOOR_PICS if door in entity_names_map]
    if doors:
        if len(doors) > 1:
            return False
        door = doors[0]
        door_idx = DOOR_PICS.index(doors[0])
        door_key = KEY_PICS[door_idx]
        for entity in entities:
            if entity.name == door:
                continue
            if not entity.knapsack:
                continue
            if not entity.knapsack.have_entity_name(door_key):
                return False
        return True
    robots = [entity for entity in entities if entity.name in PLAYER_PICS and entity.name != PLAYER_PIC]
    if len(robots) > 1:
        return False
    return True


def on_joined_together(world, entities):
    """
    :param World world:
    :param list[Entity] entities:
    """
    if len(entities) <= 1:
        return
    electro_walls = [entity for entity in entities if entity.name == "wand3"]
    players = [entity for entity in entities if entity.name in PLAYER_PICS]
    while players and electro_walls:
        for player in players:
            if not electro_walls:
                break
            electro_wall = electro_walls[0]
            electro_wall.kill()
            player.kill()
            if not electro_wall.is_alive:
                electro_walls.remove(electro_wall)
            if not player.is_alive:
                players.remove(player)
    human_players = [entity for entity in players if entity.name == PLAYER_PIC]
    robots = [entity for entity in players if entity.name != PLAYER_PIC]
    while human_players and robots:
        human = human_players[0]
        robot = robots[0]
        robot.kill()
        human.kill()
        if not robot.is_alive:
            robots.remove(robot)
        if not human.is_alive:
            human_players.remove(human)
    points = [entity for entity in entities if entity.name in SCORES_PICS]
    while human_players and points:
        for human in human_players:
            if not points:
                break
            point = points[0]
            human.scores += 1000
            point.kill()
            if not point.is_alive:
                points.remove(point)
    collectable = [entity for entity in entities if entity.name in COLLECTABLE_PICS]
    while human_players and collectable:
        for human in human_players:
            if not collectable:
                break
            place = human.knapsack.find_free_place()
            if not place:
                continue
            item = collectable.pop(0)
            item.move_to_place(place)


def do_robot_action(robot, human):
    """
    :param Entity robot:
    :param Entity human:
    """
    relative = numpy.clip(human.room_coord - robot.room_coord, -1, 1)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    random.shuffle(dirs)
    dirs = [numpy.array(d) for d in dirs]
    # First try to move in any direction like the human player.
    for d in dirs:
        if not robot.can_move(d):
            continue
        for i in (0, 1):
            if relative[i] and relative[i] == d[i]:
                robot.move(d)
                return
    # Now try to move in any direction.
    for d in dirs:
        if robot.can_move(d):
            robot.move(d)
            return
    # This will fail but show some intention.
    robot.move(dirs[0])
