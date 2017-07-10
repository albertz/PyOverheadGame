
import arcade
from .game import Game

# SCREEN_WIDTH = 800
# SCREEN_HEIGHT = 600
# match the ratio of ROOM_WIDTH/ROOM_HEIGHT
SCREEN_WIDTH = 4 * 150
SCREEN_HEIGHT = 4 * 150

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


class MainWindow(arcade.Window):
    """ Main application class. """

    def __init__(self):
        super(MainWindow, self).__init__(
            width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="PyOverheadGame!")

    def on_draw(self):
        """
        Called every frame for drawing.
        """
        arcade.start_render()
        arcade.set_background_color([127, 127, 127])
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
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            app.game.on_key_arrow((0, -1))
        elif key == arcade.key.DOWN:
            app.game.on_key_arrow((0, 1))
        elif key == arcade.key.LEFT:
            app.game.on_key_arrow((-1, 0))
        elif key == arcade.key.RIGHT:
            app.game.on_key_arrow((1, 0))

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.DOWN:
            pass
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            pass


def main():
    """ Main method """
    App().main()
