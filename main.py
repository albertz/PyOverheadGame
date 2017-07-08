#!/usr/bin/env python3

try:
    import arcade
    import better_exchook
except ImportError:
    print("See requirements.txt or README.md about what you need to install.")
    print("Usually: pip3 install --user -r requirements.txt")
    print()
    raise


from game.app import main


if __name__ == "__main__":
    better_exchook.install()
    main()
