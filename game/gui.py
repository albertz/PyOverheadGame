
import arcade
from typing import List


class WindowStack:
    def __init__(self):
        self.stack = []  # type: List[Window]

    def is_visible(self):
        return len(self.stack) > 0

    def draw(self):
        for window in self.stack:
            window.draw()

    def switch_focus(self, relative=1):
        self.stack[-1].switch_focus(relative=relative)

    def do_action(self):
        self.stack[-1].do_action()

    def on_key_escape(self):
        self.stack[-1].on_key_escape()

    def on_text(self, text):
        self.stack[-1].on_text(text)

    def on_text_motion(self, motion):
        self.stack[-1].on_text_motion(motion)

    def on_mouse_motion(self, x, y):
        self.stack[-1].on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button):
        self.stack[-1].on_mouse_press(x, y, button)


class Window:
    def __init__(self, window_stack, title=None):
        """
        :param WindowStack window_stack:
        :param str title:
        """
        self.window_stack = window_stack
        self.border_size = 20
        self.title = title
        self.title_label = None
        if title:
            self.title_label = create_html_text(
                title, color=arcade.color.BLACK, anchor_y="center", font_size=20)
        self.title_step_size = self.border_size

    def open(self):
        self.window_stack.stack.append(self)

    def close(self):
        self.window_stack.stack.remove(self)

    def get_size(self):
        raise NotImplementedError

    def draw(self):
        self.draw_background()
        return self.draw_title()

    def draw_background(self):
        from .app import app
        width, height = self.get_size()
        background_size_args = dict(
            center_x=app.window.width // 2, center_y=app.window.height // 2,
            width=width, height=height)
        # Arcade 3.x uses explicit rectangle helpers (no draw_rectangle_*).
        arcade.draw_lbwh_rectangle_filled(
            background_size_args["center_x"] - background_size_args["width"] // 2,
            background_size_args["center_y"] - background_size_args["height"] // 2,
            background_size_args["width"],
            background_size_args["height"],
            color=arcade.color.WHITE,
        )
        arcade.draw_lbwh_rectangle_outline(
            background_size_args["center_x"] - background_size_args["width"] // 2,
            background_size_args["center_y"] - background_size_args["height"] // 2,
            background_size_args["width"],
            background_size_args["height"],
            color=arcade.color.BLUE,
        )

    def draw_title(self):
        from .app import app
        width, height = self.get_size()
        center_x = app.window.width // 2
        y = (app.window.height - height) // 2
        y += self.border_size
        if self.title_label:
            # Position and draw the HTMLLabel directly instead of using the
            # removed arcade.render_text helper from older Arcade versions.
            self.title_label.x = center_x - self.title_label.content_width // 2
            self.title_label.y = app.window.height - y - self.title_label.content_height // 2
            self.title_label.draw()
            y += self.title_label.content_height + self.title_step_size
        return y

    def do_action(self):
        raise NotImplementedError

    def switch_focus(self, relative=1):
        pass

    def on_key_escape(self):
        self.close()

    def on_text(self, text):
        pass

    def on_text_motion(self, motion):
        pass

    def on_mouse_motion(self, x, y):
        pass

    def on_mouse_press(self, x, y, button):
        pass


class Menu(Window):
    def __init__(self, actions, initial_selected_action_index=0, **kwargs):
        """
        :param list[(str,()->None)] actions:
        :param int initial_selected_action_index:
        """
        super(Menu, self).__init__(**kwargs)
        from .app import app
        center_x = app.window.width // 2
        self.selected_action_index = initial_selected_action_index
        self.actions = actions
        self.labels = []
        y = 0
        for act in actions:
            # arcade.Text in newer Arcade expects (text, x, y, color, ...)
            label = arcade.Text(
                act[0],
                center_x,
                y,
                color=arcade.color.BLACK,
                anchor_x="center",
                anchor_y="center",
                font_size=20,
            )
            self.labels.append(label)
            y += label.content_height + 5
        self.label_location_map = {}
        self.label_width = max([label.content_width for label in self.labels]) + 30
        self.label_height = max([label.content_height for label in self.labels]) + 10
        self.label_step_size = 5

    def get_size(self):
        height = 0
        height += self.label_height * len(self.labels)
        height += self.label_step_size * (len(self.labels) - 1)
        if self.title_label:
            height += self.title_step_size + self.title_label.content_height
        height += self.border_size * 2
        width = self.label_width
        if self.title_label:
            width = max(width, self.title_label.content_width)
        width += self.border_size * 2
        return width, height

    def draw(self):
        self.label_location_map.clear()
        from .app import app
        center_x = app.window.width // 2
        y = super(Menu, self).draw()
        y += self.label_height // 2
        for i, label in enumerate(self.labels):
            focused = i == self.selected_action_index
            self.label_location_map[(center_x, y)] = i
            center_y = app.window.height - y
            lbwh_x = center_x - self.label_width // 2
            lbwh_y = center_y - self.label_height // 2
            arcade.draw_lbwh_rectangle_filled(
                lbwh_x,
                lbwh_y,
                self.label_width,
                self.label_height,
                color=arcade.color.BABY_BLUE if focused else arcade.color.BLUE_GRAY,
            )
            arcade.draw_lbwh_rectangle_outline(
                lbwh_x,
                lbwh_y,
                self.label_width,
                self.label_height,
                color=arcade.color.BLUE if focused else arcade.color.BLACK,
            )
            # Keep text centered inside each menu item rectangle.
            label.x = center_x
            label.y = center_y
            label.draw()
            y += label.content_height + self.label_step_size

    def switch_focus(self, relative=1):
        self.selected_action_index += relative
        self.selected_action_index %= len(self.actions)

    def do_action(self):
        self.actions[self.selected_action_index][1]()

    def _find_label_for_location(self, x, y):
        for (label_x, label_y), i in self.label_location_map.items():
            if abs(label_x - x) < self.label_width // 2 and abs(label_y - y) < self.label_height // 2:
                return i
        return None

    def on_mouse_motion(self, x, y):
        idx = self._find_label_for_location(x, y)
        if idx is not None:
            self.selected_action_index = idx

    def on_mouse_press(self, x, y, button):
        idx = self._find_label_for_location(x, y)
        if button == 1 and idx is not None:
            self.selected_action_index = idx
            self.do_action()


class ChoiceMenu(Menu):
    def __init__(self, choices, title, initial_choice_idx=0, cancel_choice_idx=None, **kwargs):
        """
        :param list[(str, ()->None)] choices:
        :param str title:
        :param int initial_choice_idx:
        :param int|None cancel_choice_idx:
        """
        def make_choice_callback(callback):
            def choice_callback():
                self.close()
                callback()
            return choice_callback
        super(ChoiceMenu, self).__init__(
            title=title, initial_selected_action_index=initial_choice_idx,
            actions=[
                (choice, make_choice_callback(callback))
                for (choice, callback) in choices],
            **kwargs)
        self.cancel_choice_idx = cancel_choice_idx

    def on_key_escape(self):
        if self.cancel_choice_idx is None:
            return
        self.actions[self.cancel_choice_idx][1]()


class ConfirmActionMenu(ChoiceMenu):
    def __init__(self, title, action, **kwargs):
        """
        :param str title:
        :param ()->None action:
        """
        super(ConfirmActionMenu, self).__init__(
            title=title,
            initial_choice_idx=1, cancel_choice_idx=1,
            choices=[("Yes", action), ("No", lambda: None)],
            **kwargs)


class MessageBox(ChoiceMenu):
    def __init__(self, title, action=None, **kwargs):
        """
        :param str title:
        :param (()->None)|None action:
        """
        super(MessageBox, self).__init__(
            title=title,
            initial_choice_idx=0, cancel_choice_idx=0,
            choices=[("Ok", action or (lambda: None))],
            **kwargs)


class TextInput(Window):
    """
    See here:
    https://github.com/adamlwgriffiths/Pyglet/blob/master/examples/text_input.py
    """

    def __init__(self, callback, **kwargs):
        super(TextInput, self).__init__(**kwargs)
        self.callback = callback
        # Simple text buffer for input; avoid using pyglet's text layout APIs
        # which changed significantly in newer pyglet/Arcade versions.
        from .app import app
        self.text = ""
        self.text_width = app.window.width // 3
        self.text_height = 28  # reasonable fixed height for the input line

    def _draw_start_pos(self, x, y):
        from .app import app
        import pyglet
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glTranslatef(x, app.window.height - y, 0)

    def draw(self):
        y = super(TextInput, self).draw()
        from .app import app
        width, height = self.get_size()
        x = (app.window.width - width) // 2 + self.border_size
        y += self.text_height
        # Draw the text input background
        pad = 2
        center_x = x + self.text_width // 2
        center_y = app.window.height - (y + self.text_height // 2)
        lbwh_x = center_x - (self.text_width + pad * 2) // 2
        lbwh_y = center_y - (self.text_height + pad * 2) // 2
        arcade.draw_lbwh_rectangle_filled(
            lbwh_x,
            lbwh_y,
            self.text_width + pad * 2,
            self.text_height + pad * 2,
            color=arcade.color.LIGHT_GRAY,
        )
        arcade.draw_lbwh_rectangle_outline(
            lbwh_x,
            lbwh_y,
            self.text_width + pad * 2,
            self.text_height + pad * 2,
            color=arcade.color.BLACK,
        )
        # Draw the current text
        text_label = arcade.Text(
            self.text,
            x + pad,
            app.window.height - y - self.text_height + pad,
            color=arcade.color.BLACK,
            anchor_x="left",
            anchor_y="baseline",
            font_size=20,
        )
        text_label.draw()

    def do_action(self):
        self.close()
        self.callback(self.text)

    def on_key_escape(self):
        self.close()
        self.callback(None)

    def get_size(self):
        height = 0
        if self.title_label:
            height += self.title_step_size + self.title_label.content_height
        height += self.text_height
        height += self.border_size * 2
        width = self.text_width
        if self.title_label:
            width = max(width, self.title_label.content_width)
        width += self.border_size * 2
        return width, height

    def on_text(self, text):
        if text in ("\n", "\r"):
            return
        # Basic text editing: support backspace and appending characters.
        if text in ("\b", "\x7f"):
            self.text = self.text[:-1]
        else:
            self.text += text

    def on_text_motion(self, motion):
        # No-op; we do not keep a real caret here.
        pass


class HelpMenu(MessageBox):
    def __init__(self, **kwargs):
        from . import game
        from .app import app
        s = app.window.entity_pixel_size
        super(HelpMenu, self).__init__(
            title=f"""
<font size=3>
Goal of the game: In some of the rooms, there is a king, which has to be defeated.
The king is immortal unless you collected and activated all the diamonds at the corresponding spots.<br>
<br>
<img src='{game.PLAYER_PIC}.png' width={s} height={s}>, this is you.
You can collect certain items to your knapsack, which is shown to the right.
Press <font color='blue'>TAB</font> to switch to the knapsack and select some item.
Press <font color='blue'>RETURN</font> to activate some item.
<br>
<img src='{game.ROBOT_PICS[1]}.png' width={s} height={s}> is a robot which wants to kill you.
But you are lucky that it is kind of stupid.
<img src='{game.KING_PIC}.png' width={s} height={s}>, this is the king.
<br>
Anything which runs into the electric wall <img src='{game.ELECTRIC_WALL_PIC}.png' width={s} height={s}> will die.
<br>
Collect the keys <img src='{game.KEY_PICS[2]}.png' width={s} height={s}> to be able to pass the doors
<img src='{game.DOOR_PICS[2]}.png' width={s} height={s}>.
Doors at the edge are closed when there are still robots alive in the room.
<br>
Collect the chemical <img src='{game.BURN_PIC}.png' width={s} height={s}> and activate nearby
a normal wall <img src='{game.SOFT_WALL_PIC}.png' width={s} height={s}> to burn it away.
<br>
If you get to the kill switch <img src='{game.KILL_PIC}.png' width={s} height={s}>,
all robots in the room will get killed immediately.
<br>
The elixir <img src='{game.GET_LIVE_PIC}.png' width={s} height={s}> can be used to give you an additional life.
Collect the diamonds <img src='{game.DIAMOND_PICS[0]}.png' width={s} height={s}> and activate nearby the
corresponding spot <img src='{game.CODE_PICS[0]}.png' width={s} height={s}>.
</font>
            """,
            **kwargs)


def create_html_text(
        text: str,
        color,
        width: int=None,
        anchor_x="left",
        anchor_y="baseline",
        font_size: float = 12,
        font_name=('Calibri', 'Arial'),
        bold: bool = False,
        italic: bool = False):
    """
    Create text to be rendered later. This operation takes a while, so it is
    better to hold it between frames when the text does not change.
    """
    if width is None:
        from .app import app
        width = (app.window.width * 4) // 5
    if len(color) == 3:
        color = (color[0], color[1], color[2], 255)

    from pyglet.text.formats.html import HTMLDecoder
    html_font_sizes = HTMLDecoder.font_sizes
    html_font_size = min([(abs(v - font_size), k) for (k, v) in sorted(html_font_sizes.items())])[1]

    text = "<font face='%s' size=%r color=%s>%s</font>" % (
        ",".join(font_name), html_font_size, "#%02x%02x%02x" % (color[0], color[1], color[2]), text)
    if bold:
        text = "<b>%s</b>" % text
    if italic:
        text = "<it>%s</it>" % text

    from pyglet.resource import FileLocation
    from pyglet.text import HTMLLabel
    from .data import GFX_DIR
    label = HTMLLabel(
        text,
        location=FileLocation(GFX_DIR),
        x=0, y=0,
        multiline=True,
        width=width,
        anchor_x=anchor_x,
        anchor_y=anchor_y)

    return label
