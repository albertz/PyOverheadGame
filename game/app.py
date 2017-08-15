
import arcade
import pyglet.image
from . import game
from .game import Game
from .data import GFX_DIR


app = None  # type: App


class App:
    def __init__(self):
        global app
        assert not app
        app = self
        self.window = MainWindow()
        self.game = Game()
        self.game.init()

    # noinspection PyMethodMayBeStatic
    def main(self):
        arcade.run()

    def get_screen_pos_args(self, pos):
        """
        :param (numpy.ndarray, numpy.ndarray) pos: ((x1,y1), (x2,y2))
        :return: center_x, center_y, width, height
        :rtype: dict[str,int]
        """
        p1, p2 = pos
        center = (p1 + p2) // 2
        size = p2 - p1
        return {
            "center_x": center[0],
            "center_y": self.window.height - center[1],
            "width": size[0],
            "height": size[1]}


class MainWindow(arcade.Window):
    """ Main application class. """

    KeyRepeatDelayTime = 0.2
    KeyRepeatTime = 0.05
    KeyRepeatIgnoreKeys = (arcade.key.RETURN,)  # can lead to unexpected behavior

    def __init__(self):
        self.entity_pixel_size = 30
        width = self.entity_pixel_size * (game.ROOM_WIDTH + 1 + game.KNAPSACK_WIDTH)
        height = self.entity_pixel_size * (game.ROOM_HEIGHT + 1)
        super(MainWindow, self).__init__(
            width=width, height=height, title="PyOverheadGame!")
        self.key_downs = {}  # key int idx -> delta time
        self.set_icon(pyglet.image.load("%s/robot.png" % GFX_DIR))

    def on_draw(self):
        """
        Called every frame for drawing.
        """
        arcade.start_render()
        arcade.set_background_color(arcade.color.BABY_BLUE)
        app.game.draw()

    # Does not work?
    # def on_resize(self, width, height):
    #    #app.game.on_screen_resize()
    #    pass

    def update(self, delta_time):
        """
        Movement and game logic. This is called for every frame.

        :param float delta_time: how much time passed
        """
        app.game.update(delta_time=delta_time)
        for key, t in sorted(self.key_downs.items()):
            t += delta_time
            while t > self.KeyRepeatDelayTime:
                t -= self.KeyRepeatTime
                self.on_key_press(key=key, modifiers=0)
            self.key_downs[key] = t

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """
        if key == arcade.key.UP:
            app.game.on_key_arrow((0, -1))
        elif key == arcade.key.DOWN:
            app.game.on_key_arrow((0, 1))
        elif key == arcade.key.LEFT:
            app.game.on_key_arrow((-1, 0))
        elif key == arcade.key.RIGHT:
            app.game.on_key_arrow((1, 0))
        elif key in (arcade.key.TAB, arcade.key.SPACE):
            app.game.on_key_tab()
        elif key == arcade.key.RETURN:
            app.game.on_key_return()
        elif key == arcade.key.ESCAPE:
            app.game.on_key_escape()
        if key not in self.KeyRepeatIgnoreKeys:
            self.key_downs.setdefault(key, 0.0)

    def on_key_release(self, key, modifiers):
        """
        Called when the user releases a key.
        """
        self.key_downs.pop(key, None)

    def on_text(self, text):
        app.game.on_text(text)

    def on_text_motion(self, motion):
        app.game.on_text_motion(motion)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        app.game.on_mouse_motion(x, self.height - y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        app.game.on_mouse_press(x, self.height - y, button)


def main():
    """ Main method """
    App().main()
