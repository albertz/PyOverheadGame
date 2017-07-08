
import arcade
import re
import contextlib
from typing import Set
from .data import DATA_DIR, GFX_DIR


GAME_DATA_DIR = DATA_DIR + "/game"

PICTURE_SIZE = 30
BACKGROUND_PIC = 'hinter.png'
PLAYER_PICS = ('figur.png', 'robot*.png', 'konig.png')
ERROR_PIC = 'error.png'  # used for error-displaying

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

    def draw(self):
        self.world.rooms[self.cur_room_idx].draw()

    def on_screen_resize(self):
        for room in self.world.rooms:
            room.on_screen_resize()

    def update(self, delta_time):
        """
        Movement and game logic. This is called for every frame.

        :param float delta_time: how much time passed
        """


class World:
    def __init__(self):
        self.rooms = [Room(i) for i in range(WORLD_WIDTH * WORLD_HEIGHT)]

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
                loaded_rooms_idxs.add(cur_room_idx)
                continue
            with self.rooms[cur_room_idx].update_place(cur_place_idx) as place:
                place.set_entity_by_name(l)
            cur_place_idx += 1
            if cur_place_idx == ROOM_WIDTH * ROOM_HEIGHT:
                cur_room_idx = None
                cur_place_idx = 0
        assert cur_room_idx is None, "last room incomplete"
        assert len(loaded_rooms_idxs) == WORLD_WIDTH * WORLD_HEIGHT, "some room is missing"


class Room:
    def __init__(self, idx):
        self.idx = idx
        self.places = [Place(i) for i in range(ROOM_WIDTH * ROOM_HEIGHT)]
        self._entities_sprite_list = arcade.SpriteList()

    @contextlib.contextmanager
    def update_place(self, idx):
        place = self.places[idx]
        if place.sprite:
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
    def __init__(self, idx):
        self.idx = idx
        self.entity = None  # type: Entity
        self.sprite = None  # type: arcade.Sprite

    @property
    def place_x(self):
        return self.idx % ROOM_WIDTH

    @property
    def place_y(self):
        return self.idx // ROOM_WIDTH

    def _reset_sprite(self):
        from .app import app
        screen_width, screen_height = app.window.get_size()
        sprite_width = screen_width // ROOM_WIDTH
        sprite_height = screen_height // ROOM_HEIGHT
        texture = arcade.load_texture(file_name="%s/%s.png" % (GFX_DIR, self.entity.name))
        scale = min(sprite_width / texture.width, sprite_height / texture.height)
        self.sprite = arcade.Sprite(scale=scale)
        self.sprite.append_texture(texture)
        self.sprite.set_texture(0)
        self.sprite.left = self.sprite.width * self.place_x
        self.sprite.top = screen_height - self.sprite.height * self.place_y

    def on_screen_resize(self):
        self._reset_sprite()

    def set_entity_by_name(self, name):
        """
        :param str name: e.g. "wand1.bmp" or "wand1.png" or "wand1"
        """
        if name.endswith(".bmp") or name.endswith(".png"):
            name = name[:-4]
        self.entity = Entity(name=name)
        self._reset_sprite()


class Entity:
    def __init__(self, name):
        self.name = name
