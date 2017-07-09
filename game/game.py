
import arcade
import re
import contextlib
import numpy
from typing import Set, List
from .data import DATA_DIR, GFX_DIR


GAME_DATA_DIR = DATA_DIR + "/game"

PICTURE_SIZE = 30
BACKGROUND_PIC = 'hinter'
PLAYER_PIC = "figur"
PLAYER_PICS = ['figur', 'konig'] + ['robot%i' % i for i in range(1, 10)]
ERROR_PIC = 'error'  # used for error-displaying

# room count
WORLD_WIDTH = 5
WORLD_HEIGHT = 4
# entity/place count in a room
ROOM_WIDTH = 20
ROOM_HEIGHT = 20
# entity/item/place count in the knapsack
KNAPSACK_WIDTH = 10
KNAPSACK_HEIGHT = 5
KNAPSACK_MAX = 27  # compatibility with Robot1 (9*3)

COMPUTER_CONTROL_INTERVAL = 750  # timer-interval for computer player control


class Game:
    def __init__(self):
        self.world = World()
        self.cur_room_idx = 0
        self.human_player = None  # type: Entity

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

    def on_screen_resize(self):
        for room in self.world.rooms:
            room.on_screen_resize()

    def on_key_arrow(self, relative):
        """
        :param (int,int) relative: (x,y)
        """
        relative = numpy.array(relative)
        self.human_player.move(relative)

    def update(self, delta_time):
        """
        Movement and game logic. This is called for every frame.

        :param float delta_time: how much time passed
        """


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
                    world=self,
                    world_coord=World.idx_to_coord(cur_room_idx),
                    room_coord=Room.idx_to_coord(cur_place_idx),
                    name=name)
            else:
                entity = None
            if name in PLAYER_PICS:
                self.rooms[cur_room_idx].players.append(entity)
            with self.rooms[cur_room_idx].update_place(cur_place_idx) as place:
                place.set_entity(entity)
            cur_place_idx += 1
            if cur_place_idx == ROOM_WIDTH * ROOM_HEIGHT:
                cur_room_idx = None
                cur_place_idx = 0
        assert cur_room_idx is None, "last room incomplete"
        assert len(loaded_rooms_idxs) == WORLD_WIDTH * WORLD_HEIGHT, "some room is missing"


class Room:
    def __init__(self, world, idx):
        """
        :param World world:
        :param int idx:
        """
        self.world = world
        self.idx = idx
        self.places = [Place(room=self, idx=i) for i in range(ROOM_WIDTH * ROOM_HEIGHT)]
        self.players = []  # type: List[Entity]
        self._entities_sprite_list = arcade.SpriteList()

    @staticmethod
    def valid_coord(coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: bool
        """
        x, y = coord
        return 0 <= x < ROOM_WIDTH and 0 <= y < ROOM_HEIGHT

    @staticmethod
    def coord_to_idx(coord):
        """
        :param (int,int)|numpy.ndarray coord:
        :rtype: int
        """
        assert Room.valid_coord(coord)
        x, y = coord
        return y * ROOM_WIDTH + x

    @staticmethod
    def idx_to_coord(idx):
        """
        :param int idx:
        :return: (x,y) coord
        :rtype: numpy.ndarray
        """
        x = idx % ROOM_WIDTH
        y = idx // ROOM_WIDTH
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
        with self.update_place(self.coord_to_idx(coord)) as place:
            place.reset_entities()

    @contextlib.contextmanager
    def update_place(self, idx):
        place = self.places[idx]
        if place.sprite and place.sprite in self._entities_sprite_list:
            self._entities_sprite_list.remove(place.sprite)
        yield place
        if place.sprite:
            self._entities_sprite_list.append(place.sprite)

    def draw(self):
        self._entities_sprite_list.draw()

    def on_screen_resize(self):
        for place in self.places:
            with self.update_place(place.idx):
                place.on_screen_resize()


class Place:
    def __init__(self, room, idx):
        """
        :param Room room:
        :param int idx:
        """
        self.room = room
        self.idx = idx
        self.entities = []  # type: List[Entity]
        self.sprite = None  # type: arcade.Sprite
        self._reset_sprite()

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

    def _reset_sprite(self):
        from .app import app
        screen_width, screen_height = app.window.get_size()
        sprite_width = screen_width // ROOM_WIDTH
        sprite_height = screen_height // ROOM_HEIGHT
        texture = arcade.load_texture(file_name="%s/%s.png" % (GFX_DIR, self.top_entity_name))
        scale = min(sprite_width / texture.width, sprite_height / texture.height)
        self.sprite = arcade.Sprite(scale=scale)
        self.sprite.append_texture(texture)
        self.sprite.set_texture(0)
        self.sprite.left = self.sprite.width * self.x
        self.sprite.top = screen_height - self.sprite.height * self.y

    def on_screen_resize(self):
        self._reset_sprite()

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

    def reset_entities(self):
        del self.entities[:]
        self._reset_sprite()

    def set_entity(self, entity):
        """
        :param Entity entity:
        """
        del self.entities[:]
        if entity:
            self.entities.append(entity)
        self._reset_sprite()

    def add_entity(self, entity):
        """
        :param Entity entity:
        """
        self.entities.append(entity)
        self._reset_sprite()

    def remove_entity(self, entity):
        """
        :param Entity entity:
        """
        self.entities.remove(entity)
        self._reset_sprite()

    def is_free(self):
        return not self.entities


class Entity:
    def __init__(self, world, world_coord, room_coord, name):
        """
        :param World world:
        :param numpy.ndarray world_coord:
        :param numpy.ndarray room_coord:
        :param str name: e.g. "figur"
        """
        self.world = world
        self.cur_world_coord = world_coord
        self.cur_room_coord = room_coord
        self.name = name

    @property
    def cur_room(self):
        return self.world.rooms[World.coord_to_idx(self.cur_world_coord)]

    @property
    def cur_place(self):
        return self.cur_room.get_place(self.cur_room_coord)

    def move(self, relative):
        """
        :param numpy.ndarray relative: (x,y)
        """
        new_coord = self.cur_room_coord + relative
        if not Room.valid_coord(new_coord):
            return
        cur_room = self.cur_room
        if not cur_room.get_place(new_coord).is_free():
            return
        with cur_room.update_place(self.cur_place.idx) as place:
            place.remove_entity(self)
        with cur_room.update_place(Room.coord_to_idx(new_coord)) as place:
            place.add_entity(self)
        self.cur_room_coord = new_coord
