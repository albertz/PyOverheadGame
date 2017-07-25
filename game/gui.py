
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


class Window:
    def __init__(self, window_stack, title=None):
        """
        :param WindowStack window_stack:
        :param str title:
        """
        self.menu_stack = window_stack
        self.border_size = 20
        self.title = title
        self.title_label = None
        if title:
            self.title_label = arcade.create_text(
                title, color=arcade.color.BLACK, anchor_y="center", font_size=20)
        self.title_step_size = self.border_size

    def close(self):
        self.menu_stack.stack.remove(self)

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
        arcade.draw_rectangle_filled(color=arcade.color.WHITE, **background_size_args)
        arcade.draw_rectangle_outline(color=arcade.color.BLUE, **background_size_args)

    def draw_title(self):
        from .app import app
        width, height = self.get_size()
        center_x = app.window.width // 2
        y = (app.window.height - height) // 2
        y += self.border_size
        if self.title_label:
            arcade.render_text(
                self.title_label,
                start_x=center_x - self.title_label.content_width // 2,
                start_y=app.window.height - y - self.title_label.content_height // 2)
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


class Menu(Window):
    def __init__(self, actions, initial_selected_action_index=0, **kwargs):
        """
        :param list[(str,()->None)] actions:
        :param int initial_selected_action_index:
        """
        super(Menu, self).__init__(**kwargs)
        self.selected_action_index = initial_selected_action_index
        self.actions = actions
        self.labels = [
            arcade.create_text(
                act[0], color=arcade.color.BLACK, anchor_y="center", font_size=20)
            for act in actions]
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
        from .app import app
        center_x = app.window.width // 2
        y = super(Menu, self).draw()
        y += self.label_height // 2
        for i, label in enumerate(self.labels):
            focused = i == self.selected_action_index
            arcade.draw_rectangle_filled(
                color=arcade.color.BABY_BLUE if focused else arcade.color.BLUE_GRAY,
                center_x=center_x, center_y=app.window.height - y,
                width=self.label_width, height=self.label_height)
            arcade.draw_rectangle_outline(
                color=arcade.color.BLUE if focused else arcade.color.BLACK,
                center_x=center_x, center_y=app.window.height - y,
                width=self.label_width, height=self.label_height)
            arcade.render_text(
                label,
                start_x=center_x - label.content_width // 2, start_y=app.window.height - y)
            y += self.label_height + self.label_step_size

    def switch_focus(self, relative=1):
        self.selected_action_index += relative
        self.selected_action_index %= len(self.actions)

    def do_action(self):
        self.actions[self.selected_action_index][1]()


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


class Rectangle(object):
    """
    Draws a rectangle into a batch.
    """
    def __init__(self, x1, y1, x2, y2, batch):
        import pyglet
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
            ('c4B', [200, 200, 220, 255] * 4)
        )


class TextInput(Window):
    """
    See here:
    https://github.com/adamlwgriffiths/Pyglet/blob/master/examples/text_input.py
    """

    def __init__(self, callback, **kwargs):
        super(TextInput, self).__init__(**kwargs)
        self.callback = callback

        import pyglet
        from .app import app

        self.batch = pyglet.graphics.Batch()
        self.text_width = app.window.width // 3

        self.document = pyglet.text.document.UnformattedDocument("")
        self.document.set_style(0, len(self.document.text),
            dict(color=(0, 0, 0, 255), font_size=20)
        )
        font = self.document.get_font()
        self.text_height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, self.text_width, self.text_height, multiline=False, batch=self.batch)
        self.caret = pyglet.text.caret.Caret(self.layout)

        x = 0
        y = 0
        pad = 2
        self.rectangle = Rectangle(
            x - pad, y - pad,
            x + self.text_width + pad, y + self.text_height + pad, self.batch)

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
        self._draw_start_pos(x, y)
        self.batch.draw()

    def do_action(self):
        self.close()
        self.callback(self.document.text)

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
        self.caret.on_text(text)

    def on_text_motion(self, motion):
        self.caret.on_text_motion(motion)
