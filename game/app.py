import arcade


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


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

    def update(self, delta_time):
        """
        Movement and game logic. This is called for every frame.

        :param float delta_time: how much time passed
        """


def main():
    """ Main method """
    # noinspection PyUnusedLocal
    window = MainWindow()
    arcade.run()
