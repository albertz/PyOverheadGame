
import arcade
from . import game
from .game import Game


app = None  # type: App


class App:
    def __init__(self):
        global app
        assert not app
        app = self
        self.window = MainWindow()
        self.game = Game()
        self.game.load("robot.sce")

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

    def __init__(self):
        self.room_pixel_size = 30
        width = self.room_pixel_size * (game.ROOM_WIDTH + 1 + game.KNAPSACK_WIDTH)
        height = self.room_pixel_size * (game.ROOM_HEIGHT + 1)
        super(MainWindow, self).__init__(
            width=width, height=height, title="PyOverheadGame!")

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
        elif key == arcade.key.TAB:
            app.game.on_key_tab()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.DOWN:
            pass
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            pass


def main():
    """ Main method """
    App().main()
