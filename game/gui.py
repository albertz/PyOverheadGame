
import arcade
from typing import List


class MenuStack:
    def __init__(self):
        self.stack = []  # type: List[Menu]

    def is_visible(self):
        return len(self.stack) > 0

    def draw(self):
        for menu in self.stack:
            menu.draw()


class Menu:
    def __init__(self, menu_stack, actions, title=None, initial_selected_action_index=0):
        """
        :param MenuStack menu_stack:
        :param list[(str,()->None)] actions:
        :param str title:
        :param int initial_selected_action_index:
        """
        self.menu_stack = menu_stack
        self.selected_action_index = initial_selected_action_index
        self.actions = actions
        self.title = title
        self.title_label = None
        if title:
            self.title_label = arcade.create_text(
                title, color=arcade.color.BLACK, anchor_y="center", font_size=20)
        self.border_size = 20
        self.title_step_size = self.border_size
        self.labels = [
            arcade.create_text(
                act[0], color=arcade.color.BLACK, anchor_y="center", font_size=20)
            for act in actions]
        self.label_width = max([label.content_width for label in self.labels]) + 30
        self.label_height = max([label.content_height for label in self.labels]) + 10
        self.label_step_size = 5

    def close(self):
        self.menu_stack.stack.remove(self)

    def draw(self):
        from .app import app
        center_x = app.window.width // 2
        height = self.label_height * len(self.labels)
        height += self.label_step_size * (len(self.labels) - 1)
        if self.title_label:
            height += self.title_step_size + self.title_label.content_height
        height += self.border_size * 2
        width = self.label_width
        if self.title_label:
            width = max(width, self.title_label.content_width)
        width += self.border_size * 2
        background_size_args = dict(
            center_x=center_x, center_y=app.window.height // 2,
            width=width, height=height)
        arcade.draw_rectangle_filled(color=arcade.color.WHITE, **background_size_args)
        arcade.draw_rectangle_outline(color=arcade.color.BLUE, **background_size_args)
        y = (app.window.height - height) // 2
        y += self.border_size
        if self.title_label:
            arcade.render_text(
                self.title_label,
                start_x=center_x - self.title_label.content_width // 2,
                start_y=app.window.height - y - self.title_label.content_height // 2)
            y += self.title_label.content_height + self.title_step_size
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
    def __init__(self, menu_stack, choices, title, initial_choice_idx=0):
        """
        :param MenuStack menu_stack:
        :param list[(str, ()->None)] choices:
        :param str title:
        :param int initial_choice_idx:
        """
        def make_choice_callback(callback):
            def choice_callback():
                self.close()
                callback()
            return choice_callback
        super(ChoiceMenu, self).__init__(
            menu_stack=menu_stack, title=title, initial_selected_action_index=initial_choice_idx,
            actions=[
                (choice, make_choice_callback(callback))
                for (choice, callback) in choices])
