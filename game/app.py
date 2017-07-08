import arcade


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class MainWindow(arcade.Window):
    """ Main application class. """


def main():
    """ Main method """
    window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT)
    arcade.run()
    
