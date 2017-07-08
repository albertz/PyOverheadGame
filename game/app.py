
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
        self.game.world.load("robot.sce")

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


def main():
    """ Main method """
    App().main()
