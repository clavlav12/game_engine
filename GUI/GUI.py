import pygame
from GlobalUse import *
from draw_shapes import *
import dialogs
import os.path
import sys
from typing import Union
import pygame.locals as pl
from re import finditer
import pyperclip
sys.path.insert(1, os.path.dirname(os.path.os.getcwd()))
from Engine.structures import *
from Engine.Sound import Player
image_folder = 'GUI images\\'


class Window:
    previous_windows = Stack()
    returned_value = None
    sound_player = Player()

    def __init__(self, master):
        screen_rect = master.get_rect()
        self.widget_list = []
        self.surface = master
        self.dialog = None
        self.rect = master.get_rect()
        # buttons
        left = screen_rect.right + meters(20)
        y = meters(30)
        x = meters(100)

        return_butt_img = pygame.image.load(rf"{image_folder}return.png")
        return_butt_img = pygame.transform.scale(return_butt_img, (meters(50), meters(50)))
        self.return_button = Button(return_butt_img, (meters(30), y), self.on_return_click, self, PlaceType.center)

        home_button_img = pygame.image.load(rf"{image_folder}home butt brown.png")
        home_button_img = pygame.transform.scale(home_button_img, (meters(50), meters(50)))
        self.home_button = Button(home_button_img, (left - meters(100), y), self.on_home_click, self, PlaceType.center)

        exit_button_image = pygame.image.load(rf"{image_folder}x button.png")
        exit_button_image = pygame.transform.scale(exit_button_image, (meters(50), meters(50)))
        self.exit_button = Button(exit_button_image, (left - meters(50), y), self.on_exit_click, self, PlaceType.center)

        self.mute_button = MuteButton(pygame.rect.Rect(screen_rect.right - meters(130), y, meters(50), meters(50)),
                                      self, self.sound_player, PlaceType.center)
        Window.previous_windows.push(self)
        # self.dialog = dialogs.PopUpMessage(self, self.surface)

    def add_widget(self, widget):
        self.widget_list.append(widget)

    def on_return_click(self):
        Window.previous_windows.pop()

    def on_exit_click(self):
        self.dialog = dialogs.ExitPopUpMessage(self, self.surface)

    def on_home_click(self):
        Window.previous_windows = Stack(Window.previous_windows.get_items()[0])

    def on_settings_click(self):
        SettingsWindow(self.surface)

    def draw_widgets(self):
        for widget in self.widget_list:
            widget.draw()

    def draw(self, surface):
        self.draw_widgets()
        maybe(self.dialog).draw()

    @classmethod
    def get_current_window(cls):
        return cls.previous_windows.top(default=None)

    @classmethod
    def draw_current_window(cls):
        Window.get_current_window().draw()


class SettingsWindow(Window):
    pass


class MainWindow(Window):
    def __init__(self, master):
        super(MainWindow, self).__init__(master)

    def on_return_click(self):
        self.dialog = dialogs.ExitPopUpMessage(self, self.surface)


class Windw2(Window):
    def draw(self, surface):
        print(8)
        super(Windw2, self).draw(surface)


class Widget:

    def __init__(self, surface_rect, pos, pos_place, window: Union[Window, dialogs.PopUpMessage]):
        self.rect = surface_rect
        self.place_rect(pos, pos_place)
        self.window = window
        window.add_widget(self)

    def place_rect(self, pos, pos_place):
        x, y = pos
        if pos_place == PlaceType['center']:
            self.rect.center = pos

        elif pos_place == PlaceType['top_left']:
            self.rect.x, self.rect.y = pos

        elif pos_place == PlaceType['top_right']:
            self.rect.x = pos[0] - self.rect.width
            self.rect.y = pos[1]

        elif pos_place == PlaceType['bottom_left']:
            self.rect.x = pos[0]
            self.rect.y = pos[1] - self.rect.height

        elif pos_place == PlaceType['bottom_right']:
            self.rect.x = pos[0] - self.rect.width
            self.rect.y = pos[1] - self.rect.height

    def draw(self):
        """Should be overrided in all subclasses"""
        pass

    def absolute_position(self, pos):
        return sub(pos, self.window.rect.topleft)


class Button(Widget):
    last_clicked = []
    do_nothing = lambda: None

    def __init__(self, img: pygame.Surface, pos, on_click, window, pos_place=PlaceType.top_left,
                 on_release=None, text='', text_color=Color('white'), font_object=DEFAULT_FONT,
                 text_justification=Justification.horizontally_centered, mask_collide=True):
        super(Button, self).__init__(img.get_rect(), pos, pos_place, window)

        self.text = fit_text_to_rect(text, font_object, text_color, text_justification, self.rect)
        self.mask_collide = mask_collide
        self.image = img
        if self.mask_collide:
            self.mask = pygame.mask.from_surface(img)
        self.on_click = on_click
        if on_release is None:
            self.on_release = Button.do_nothing
        else:
            self.on_release = on_release

    def draw(self):
        self.window.surface.blit(self.image, (self.rect.x, self.rect.y))
        if self.text is not None:
            self.window.surface.blit(self.text, place_center(self.rect, self.text))

    def offset(self, pos):
        return pos[0] - self.rect.x - self.window.rect.x, pos[1] - self.rect.y - self.window.rect.y

    def set_image(self, img):
        self.image = img
        self.mask = pygame.mask.from_surface(img)

    @classmethod
    def check_click(cls, events):
        for event in events:
            current_window = Window.get_current_window()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == MouseButtons.left:
                    pos = pygame.mouse.get_pos()
                    for widget in (current_window.widget_list if current_window.dialog is None
                            else current_window.dialog.widget_list):
                        if isinstance(widget, cls):
                            # or isinstance(widget, dialogs.button_type):  # second condition to fix the
                            # different between <class 'GUI.Button'> and <class '__main__.Button'> (they are the same class
                            # but different imports, it will work when importing GUI from an outer file but when running
                            # GUI as main is the condition  doesn't work.
                            if (widget.rect.collidepoint(*widget.absolute_position(pos))) \
                                    and ((not widget.mask_collide) or widget.mask.get_at(widget.offset(pos))):
                                widget.on_click()
                                cls.last_clicked.append(widget)
            if event.type == pygame.MOUSEBUTTONUP:
                for button in cls.last_clicked:
                    button.on_release()
                cls.last_clicked = []

# too much bugs
class TextInput(Widget):
    """
    This class lets the user input a piece of text, e.g. a name or a message.
    This class let's the user input a short, one-lines piece of text at a blinking cursor
    that can be moved using the arrow-keys. Delete, home and end work as well.
    """
    def __init__(
            self,
            width, height,
            pos, window,
            pos_place=PlaceType.top_left,
            initial_string="",
            font_family="",
            font_size=35,
            antialias=True,
            text_color=Color('dodgerblue2'),
            cursor_color=Color('dodgerblue2'),
            repeat_keys_initial_ms=400,
            repeat_keys_interval_ms=35,
            max_string_length=-1,
            inactive_color=Color('lightskyblue3'),
            active_color=Color('dodgerblue2')):

        """
        :param initial_string: Initial text to be displayed
        :param font_family: name or list of names for font (see pygame.font.match_font for precise format)
        :param font_size:  Size of font in pixels
        :param antialias: Determines if antialias is applied to font (uses more processing power)
        :param text_color: Color of text (duh)
        :param cursor_color: Color of cursor
        :param repeat_keys_initial_ms: Time in ms before keys are repeated when held
        :param repeat_keys_interval_ms: Interval between key press repetition when held
        :param max_string_length: Allowed length of text
        """

        super(TextInput, self).__init__(Rect(0, 0, width, height), pos, pos_place, window)

        # Text related vars:
        self.antialias = antialias
        self.text_color = text_color
        self.font_size = font_size
        self.max_string_length = max_string_length
        self.input_string = initial_string  # Inputted text
        self.fixed_string = ''
        self.active = False
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.surface = Surface((width, height), SRCALPHA)
        self.button = Button(self.surface, pos, self.on_click, window, pos_place, mask_collide=False)
        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)

        self.font_object = pygame.font.Font(font_family, font_size)

        # main surface
        self.surface = Surface((width, height), SRCALPHA)

        # Text-surface will be created during the first update call:
        self.text_surface = None

        #  if can't write anymore
        self.full = False

        # Vars to make keydowns repeat after user pressed a key for some time:
        self.keyrepeat_counters = {}  # {event.key: (counter_int, event.unicode)} (look for "***")
        self.keyrepeat_intial_interval_ms = repeat_keys_initial_ms
        self.keyrepeat_interval_ms = repeat_keys_interval_ms

        # Things cursor:
        self.cursor_surface = pygame.Surface((int(self.font_size / 20 + 1), self.font_size))
        self.cursor_surface.fill(cursor_color)
        self.cursor_position = len(initial_string)  # Inside text
        self.cursor_visible = True  # Switches every self.cursor_switch_ms ms
        self.cursor_switch_ms = 500  # /|\
        self.cursor_ms_counter = 0

        self.clock = pygame.time.Clock()

    def on_click(self):
        self.active = not self.active

    def update(self, events_list):
        if not self.active and self.text_surface is not None:
            return
        for EVENT in events_list:
            if EVENT.type == MOUSEBUTTONDOWN:
                if not (self.rect.collidepoint(*self.absolute_position(pygame.mouse.get_pos()))):
                    self.active = False

            if EVENT.type == pygame.KEYDOWN:
                self.cursor_visible = True  # So the user sees where he writes

                # If none exist, create counter for that key:
                if EVENT.key not in self.keyrepeat_counters:
                    self.keyrepeat_counters[EVENT.key] = [0, EVENT.unicode]

                if EVENT.key == pl.K_BACKSPACE:
                    self.full = self.full and self.cursor_position == 0
                    self.input_string = (
                            self.input_string[:max(self.cursor_position - 1, 0)]
                            + self.input_string[self.cursor_position:]
                    )
                    # Subtract one from cursor_pos, but do not go below zero:
                    self.cursor_position = max(self.cursor_position - 1, 0)

                elif EVENT.key == pl.K_DELETE:
                    self.full = self.full and self.cursor_position == len(self.input_string)
                    self.input_string = (
                        self.input_string[:self.cursor_position]
                        + self.input_string[self.cursor_position + 1:]
                    )

                elif EVENT.key == pl.K_RETURN:
                    return True

                elif EVENT.key == pl.K_RIGHT:
                    # Add one to cursor_pos, but do not exceed len(input_string)
                    self.cursor_position = min(self.cursor_position + 1, len(self.input_string))

                elif EVENT.key == pl.K_LEFT:
                    # Subtract one from cursor_pos, but do not go below zero:
                    self.cursor_position = max(self.cursor_position - 1, 0)

                elif EVENT.key == pl.K_END:
                    self.cursor_position = len(self.input_string)

                elif EVENT.key == pl.K_HOME:
                    self.cursor_position = 0

                elif len(self.input_string) < self.max_string_length or self.max_string_length == -1:
                    # If no special key is pressed, add unicode of key to input_string+
                    if not self.full:
                        self.input_string = (
                            self.input_string[:self.cursor_position]
                            + EVENT.unicode
                            + self.input_string[self.cursor_position:]
                        )
                        self.cursor_position += len(EVENT.unicode)  # Some are empty, e.g. K_UP

            elif EVENT.type == pl.KEYUP:
                # *** Because KEYUP doesn't include event.unicode, this dict is stored in such a weird way
                if EVENT.key in self.keyrepeat_counters:
                    del self.keyrepeat_counters[EVENT.key]

        # Update key counters:
        for key in self.keyrepeat_counters:
            self.keyrepeat_counters[key][0] += self.clock.get_time()  # Update clock

            # Generate new key events if enough time has passed:
            if self.keyrepeat_counters[key][0] >= self.keyrepeat_intial_interval_ms:
                self.keyrepeat_counters[key][0] = (
                    self.keyrepeat_intial_interval_ms
                    - self.keyrepeat_interval_ms
                )

                event_key, event_unicode = key, self.keyrepeat_counters[key][1]
                pygame.event.post(pygame.event.Event(pl.KEYDOWN, {'key': event_key, 'unicode': event_unicode}))

        # Re-render text surface:
        self.surface.fill(TRANSPARENT)
        # self.text_surface = self.font_object.render(self.input_string, self.antialias, self.text_color)
        try:
            self.text_surface, self.fixed_string = fit_text_to_rect_if_possible(self.input_string, self.font_object,
                                                                           self.text_color,
                                                                           Justification.left_justified, self.rect)
        except Exception as e:
            if 'tall' in (str(e)):
                self.full = True
                self.input_string = self.input_string[:-1]
                self.cursor_position -= 1
                self.text_surface, self.fixed_string = fit_text_to_rect_if_possible(self.input_string, self.font_object,
                                                                               self.text_color,
                                                                               Justification.left_justified, self.rect)
            else:
                raise e

        # if last char is '\n' then the user pressed space at the end of the line and it has been erased

        # Update self.cursor_visible
        self.cursor_ms_counter += self.clock.get_time()
        if self.cursor_ms_counter >= self.cursor_switch_ms:
            self.cursor_ms_counter %= self.cursor_switch_ms
            self.cursor_visible = not self.cursor_visible

        if self.cursor_visible:

            total_lines = self.fixed_string.count('\n', 0, self.cursor_position)
            s1 = {m.start() for m in finditer('\n', self.fixed_string)}
            s2 = {m.start() for m in finditer(' ', self.input_string)}
            wrapped_words = s1 or s2

            num = 0
            while True:
                try:
                    a = False
                    cursor_line, pos_in_line = self.get_line_around_index(self.fixed_string, self.cursor_position - num)
                    break
                except TypeError:
                    print(num)
                    num += 1

            print(cursor_line, pos_in_line, self.cursor_position)
            print(repr(cursor_line), pos_in_line, self.cursor_position, repr(self.fixed_string), repr(self.input_string),
                  self.cursor_surface, a)
            cursor_x_pos = self.font_object.size(cursor_line[:pos_in_line])[0]
            # Without this, the cursor is invisible when self.cursor_position > 0:
            if pos_in_line > 0:
                cursor_x_pos -= self.cursor_surface.get_width()

            cursor_y_pos =\
                (self.font_object.size(' ')[1] * (1 + self.fixed_string.count('\n', 0, self.cursor_position))) - \
                self.cursor_surface.get_height()
            self.text_surface.blit(self.cursor_surface, (cursor_x_pos, cursor_y_pos))

        self.surface.blit(self.text_surface, (2, 2))

        # pygame.draw.rect(self.surface, Color('gold'), self.text_surface.get_rect(), 3)

        clr = self.active_color if self.active else self.inactive_color
        pygame.draw.rect(self.surface, clr, self.surface.get_rect(), 2)
        self.clock.tick()
        return False


    def get_surface(self):
        return self.text_surface

    def get_text(self):
        return self.input_string

    def get_cursor_position(self):
        return self.cursor_position

    def set_text_color(self, color):
        self.text_color = color

    def set_cursor_color(self, color):
        self.cursor_surface.fill(color)

    def clear_text(self):
        self.input_string = ""
        self.cursor_position = 0

    def draw(self):
        self.window.surface.blit(self.surface, self.rect.topleft)

    def get_line_around_index(self, string, index):
        s1 = {m.start() for m in finditer('\n', self.fixed_string)}
        s2 = {m.start() for m in finditer(' ', self.input_string)}
        wrapped_words = s1 or s2
        fixed_string = self.fixed_string
        for num, index in enumerate(wrapped_words):
            fixed_string = self.remove_char(fixed_string, index - num)

        current_index = 0
        for line in fixed_string.split('\n'):
            current_index += len(line)
            if current_index >= index >= current_index - len(line):
                return line,  len(line) - (current_index - index)

    @classmethod
    def update_all(cls, events):
        current_window = Window.get_current_window()
        for widget in (current_window.widget_list if current_window.dialog is None
                                        else current_window.dialog.widget_list):
            if isinstance(widget, cls):
                widget.update(events)

    @staticmethod
    def remove_char(string, index):
        return string[:index] + string[index+1:]


class MuteButton:
    def __init__(self, rect, window, sound_player: Player, pos_place=PlaceType.top_left):
        self.player = sound_player
        muted_image = pygame.image.load(rf"{image_folder}mute.png")
        unmuted_image = pygame.image.load(rf"{image_folder}unmute.png").convert_alpha()
        self.muted_image = pygame.transform.scale(muted_image, (rect.width, rect.height)).convert_alpha()
        self.unmuted_image = pygame.transform.scale(unmuted_image, (rect.width, rect.height)).convert_alpha()
        self.button = Button(self.muted_image if self.player.mute else self.unmuted_image, rect[:2], self.on_click,
                             window, pos_place, self.on_release)

    def on_click(self):
        self.player.toggle_mute()
        if self.button.image is self.muted_image:
            self.button.image = self.unmuted_image
        else:
            self.button.image = self.muted_image

    def on_release(self):
        pass


class LineInput(Widget):
    """
    This class lets the user input a piece of text, e.g. a name or a message.
    This class let's the user input a short, one-lines piece of text at a blinking cursor
    that can be moved using the arrow-keys. Delete, home and end work as well.
    """
    def __init__(
            self,
            width, height,
            pos, window,
            pos_place=PlaceType.top_left,
            initial_string="",
            font_family="",
            antialias=True,
            text_color=Color('dodgerblue2'),
            cursor_color=Color('dodgerblue2'),
            repeat_keys_initial_ms=400,
            repeat_keys_interval_ms=35,
            max_string_length=-1,
            inactive_color=Color('lightskyblue3'),
            active_color=Color('dodgerblue2')):

        """
        :param initial_string: Initial text to be displayed
        :param font_family: name or list of names for font (see pygame.font.match_font for precise format)
        :param font_size:  Size of font in pixels
        :param antialias: Determines if antialias is applied to font (uses more processing power)
        :param text_color: Color of text (duh)
        :param cursor_color: Color of cursor
        :param repeat_keys_initial_ms: Time in ms before keys are repeated when held
        :param repeat_keys_interval_ms: Interval between key press repetition when held
        :param max_string_length: Allowed length of text
        """

        super(LineInput, self).__init__(Rect(0, 0, width, height), pos, pos_place, window)

        # Text related vars:
        self.antialias = antialias
        self.text_color = text_color
        self.font_size = height
        self.max_string_length = max_string_length
        self.input_string = initial_string  # Inputted text
        self.rendered_text = initial_string
        self.active = False
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.surface = Surface((width, height), SRCALPHA)
        self.button = Button(self.surface, pos, self.on_click, window, pos_place, mask_collide=False)
        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)

        self.font_object = pygame.font.Font(font_family, self.font_size)

        # main surface
        self.surface = Surface((width, height), SRCALPHA)

        # Text-surface will be created during the first update call:
        self.text_surface = None

        # Vars to make keydowns repeat after user pressed a key for some time:
        self.keyrepeat_counters = {}  # {event.key: (counter_int, event.unicode)} (look for "***")
        self.keyrepeat_intial_interval_ms = repeat_keys_initial_ms
        self.keyrepeat_interval_ms = repeat_keys_interval_ms

        # Things cursor:
        self.cursor_surface = pygame.Surface((int(self.font_size / 20 + 1), self.font_size))
        self.cursor_surface.fill(cursor_color)
        self.cursor_position = len(initial_string)  # Inside text
        self.cursor_visible = True  # Switches every self.cursor_switch_ms ms
        self.cursor_switch_ms = 500  # /|\
        self.cursor_ms_counter = 0

        self.clock = pygame.time.Clock()

    def on_click(self):
        self.active = not self.active

    def make_inactive(self):
        self.active = False
        self.keyrepeat_counters = {}

    def update(self, events_list):
        if not self.active and self.text_surface is not None:
            return
        for EVENT in events_list:
            if EVENT.type == MOUSEBUTTONDOWN:
                if not (self.rect.collidepoint(*self.absolute_position(pygame.mouse.get_pos()))):
                    self.make_inactive()

            if EVENT.type == pygame.KEYDOWN:
                self.cursor_visible = True  # So the user sees where he writes

                # If none exist, create counter for that key:
                if EVENT.key not in self.keyrepeat_counters:
                    self.keyrepeat_counters[EVENT.key] = [0, EVENT.unicode]

                if EVENT.key == pl.K_BACKSPACE:
                    self.input_string = (
                            self.input_string[:max(self.cursor_position - 1, 0)]
                            + self.input_string[self.cursor_position:]
                    )
                    # Subtract one from cursor_pos, but do not go below zero:
                    self.cursor_position = max(self.cursor_position - 1, 0)

                elif EVENT.key == pl.K_DELETE:
                    self.input_string = (
                        self.input_string[:self.cursor_position]
                        + self.input_string[self.cursor_position + 1:]
                    )

                elif EVENT.key == pl.K_RETURN:
                    self.make_inactive()
                    return True

                elif EVENT.key == pl.K_RIGHT:
                    # Add one to cursor_pos, but do not exceed len(input_string)
                    self.cursor_position = min(self.cursor_position + 1, len(self.input_string))

                elif EVENT.key == pl.K_LEFT:
                    # Subtract one from cursor_pos, but do not go below zero:
                    self.cursor_position = max(self.cursor_position - 1, 0)

                elif EVENT.key == pl.K_END:
                    self.cursor_position = len(self.input_string)

                elif EVENT.key == pl.K_HOME:
                    self.cursor_position = 0

                elif EVENT.key == pl.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    copyed_text = pyperclip.paste()
                    self.input_string = (
                        self.input_string[:self.cursor_position]
                        + copyed_text
                        + self.input_string[self.cursor_position:]
                    )
                    self.cursor_position += len(copyed_text)  # Some are empty, e.g. K_UP

                elif EVENT.key == pl.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pyperclip.copy(self.input_string)

                elif len(self.input_string) < self.max_string_length or self.max_string_length == -1:
                    # If no special key is pressed, add unicode of key to input_string+
                    self.input_string = (
                        self.input_string[:self.cursor_position]
                        + EVENT.unicode
                        + self.input_string[self.cursor_position:]
                    )
                    self.cursor_position += len(EVENT.unicode)  # Some are empty, e.g. K_UP
            elif EVENT.type == pl.KEYUP:
                # *** Because KEYUP doesn't include event.unicode, this dict is stored in such a weird way
                if EVENT.key in self.keyrepeat_counters:
                    del self.keyrepeat_counters[EVENT.key]

        # Update key counters:
        for key in self.keyrepeat_counters:
            self.keyrepeat_counters[key][0] += self.clock.get_time()  # Update clock

            # Generate new key events if enough time has passed:
            if self.keyrepeat_counters[key][0] >= self.keyrepeat_intial_interval_ms:
                self.keyrepeat_counters[key][0] = (
                    self.keyrepeat_intial_interval_ms
                    - self.keyrepeat_interval_ms
                )

                event_key, event_unicode = key, self.keyrepeat_counters[key][1]
                pygame.event.post(pygame.event.Event(pl.KEYDOWN, {'key': event_key, 'unicode': event_unicode}))

        # Re-render text surface:
        self.surface.fill(TRANSPARENT)
        # self.text_surface = self.font_object.render(self.input_string, self.antialias, self.text_color)

        # Update self.cursor_visible
        self.cursor_ms_counter += self.clock.get_time()
        if self.cursor_ms_counter >= self.cursor_switch_ms:
            self.cursor_ms_counter %= self.cursor_switch_ms
            self.cursor_visible = not self.cursor_visible

        string = self.input_string
        index = 0  # index is the lowest number that from it to the end is able to fit in the rect
        while self.font_object.size(string[index:])[0] >= self.rect.width:
            index += 1

        cursor_rendered_pos = self.cursor_position-len(self.input_string[:index])  # non rendered part
        self.rendered_text = string[index:]
        if cursor_rendered_pos < 0:
            index += cursor_rendered_pos
            self.rendered_text = string[index: cursor_rendered_pos]
            cursor_rendered_pos = 0  # non rendered part
        self.text_surface = self.font_object.render(self.rendered_text, True, self.text_color)

        if self.cursor_visible:
            # print(self.cursor_position, cursor_rendered_pos, index, self.rendered_text)
            cursor_x_pos = self.font_object.size(self.rendered_text[:cursor_rendered_pos])[0]
            # Without this, the cursor is invisible when self.cursor_position > 0:
            if (self.cursor_position > 0 ) and (not cursor_x_pos == 0):
                cursor_x_pos -= self.cursor_surface.get_width()
            self.text_surface.blit(self.cursor_surface, (cursor_x_pos, 0))

        self.surface.blit(self.text_surface, (2, 2))

        # pygame.draw.rect(self.surface, Color('gold'), self.text_surface.get_rect(), 3)

        clr = self.active_color if self.active else self.inactive_color
        pygame.draw.rect(self.surface, clr, self.surface.get_rect(), 2)
        self.clock.tick()
        return False

    def get_surface(self):
        return self.text_surface

    def get_text(self):
        return self.input_string

    def get_cursor_position(self):
        return self.cursor_position

    def set_text_color(self, color):
        self.text_color = color

    def set_cursor_color(self, color):
        self.cursor_surface.fill(color)

    def clear_text(self):
        self.input_string = ""
        self.cursor_position = 0

    def draw(self):
        if (not self.active) and self.cursor_visible:  # need to delete the cursor
            self.surface.fill(TRANSPARENT)
            self.text_surface = self.font_object.render(self.rendered_text, True, self.text_color)
            self.surface.blit(self.text_surface, (2, 2))
            clr = self.active_color if self.active else self.inactive_color
            pygame.draw.rect(self.surface, clr, self.surface.get_rect(), 2)
            self.cursor_visible = False
        self.window.surface.blit(self.surface, self.rect.topleft)

    @classmethod
    def update_all(cls, events):
        current_window = Window.get_current_window()
        for widget in (current_window.widget_list if current_window.dialog is None
                                        else current_window.dialog.widget_list):
            if isinstance(widget, cls):
                widget.update(events)

    @staticmethod
    def remove_char(string, index):
        return string[:index] + string[index+1:]

class ShapeStyle(Enum):
    rounded = 0
    sharp = 1
    circular = 2


class Direction(Enum):
    left_to_right = 0
    right_to_left = 1


class PlaceText:
    top_left = 'top_left'
    top_right = 'top_right'
    top_middle = 'top_middle'
    bottom_left = 'bottom_left'
    bottom_right = 'bottom_right'
    bottom_middle = 'bottom_middle'
    left = 'left'
    right = 'right'
    under_cursor = 'under_cursor'
    above_cursor = 'above_cursor'


class SliderStyle:
    def __init__(self, style=ShapeStyle.circular, drag_button_color=(82, 194, 231), value_line_color=(82, 194, 231),
                 non_value_line_color=(220, 220, 220), direction=Direction.left_to_right, display_value=False,
                 displayed_value_color=pygame.Color('white'), displayed_value_place=PlaceText.right,
                 displayed_value_font=Default()):
        self.direction = direction
        self.drag_button_color = drag_button_color
        self.style = style
        self.value_line_color = value_line_color
        self.non_value_line_color = non_value_line_color
        self.display_value = display_value
        self.displayed_value_color = displayed_value_color
        self.displayed_value_place = displayed_value_place
        self.displayed_value_font = displayed_value_font


class Slider(Widget):
    default_button_color = (82, 194, 231)
    default_line_color = (220, 220, 220)

    def __init__(self, min_value: Union[int, float], max_value: Union[int, float], value_jumps: Union[int, float],
                 line_rect: Union[tuple, list, Rect], window: Window, style=SliderStyle(), pos_place=PlaceType.top_left,
                 default_value=None):
        assert ((max_value % value_jumps) == 0),\
            f'max value must be divisible by value jumps. got max_value={max_value}, value_jumps={value_jumps}'
        assert ((min_value % value_jumps) == 0),\
            f'min value must be divisible by value jumps. got min_value={min_value}, value_jumps={value_jumps}'
        assert ((maybe(default_value).or_else(0) % value_jumps) == 0), \
            f'default value must be divisible by value jumps. got default_value={default_value}, value_jumps={value_jumps}'
        self._value = 0
        super(Slider, self).__init__(line_rect, Rect(*line_rect).topleft, pos_place, window)
        self.style = style
        self.direction = style.direction
        self.max_value = max_value
        self.min_value = min_value
        self.value_jumps = value_jumps
        self.set_value(maybe(default_value).or_else(min_value))
        self.is_dragging = False
        if isinstance(style.displayed_value_font, Default):
            self.font = pygame.font.SysFont("comicsansms", self.rect.height // 5)
        elif isinstance(style.displayed_value_font, pygame.font.Font):
            self.font = style.displayed_value_font

        line_rect = Rect(self.rect.x, self.rect.y + (self.rect.height * 2) // 5, self.rect.width, self.rect.height // 5)
        start_pos = self.get_position_by_value(self.get_value())

        if style.style is ShapeStyle.rounded:
            self.drag_button_shape = RoundedRect(Rect(start_pos[0], self.rect.top + self.rect.height // 2,
                                                      self.rect.width // 10, self.rect.height // 2),
                                                 style.drag_button_color)

        elif style.style is ShapeStyle.sharp:
            self.drag_button_shape = Rectangle(Rect(start_pos[0], self.rect.top + self.rect.height // 2,
                                                    self.rect.width // 10, self.rect.height // 2),
                                               style.drag_button_color)

        elif style.style is ShapeStyle.circular:
            # self.drag_button_shape = Circle(*self.get_position_by_value(self.get_value()), int(self.rect.height / 3),
            #                                 style.drag_button_color)
            self.drag_button_shape = Circle(start_pos[0], start_pos[1] + self.rect.height // 10, int(self.rect.height / 3.5),
                                            style.drag_button_color)

        self.non_value_line = Rectangle(line_rect, style.non_value_line_color)
        self.value_line = Rectangle(line_rect, style.value_line_color)

        self.drag_button = Button(self.drag_button_shape.surface, self.drag_button_shape.rect.topleft,
                                  self.dragged_click, window, PlaceType.center, self.dragged_release)
        self.line_button = Button(self.non_value_line.surface, self.non_value_line.rect.topleft,
                                  self.dragged_click, window, PlaceType.top_left, self.dragged_release)
        self.window.add_widget(self)

    def get_value(self):
        return self._value

    def set_value(self, value):
        if value > self.max_value:
            self._value = self.max_value
        elif value < self.min_value:
            self._value = self.min_value
        else:
            self._value = closest_number_divisible(value, self.value_jumps)

    def get_position_by_value(self, value):
        if self.direction is Direction.right_to_left:
            value = self.max_value - value
        return (round(self.rect.x + self.rect.width / (self.max_value - self.min_value) * value)), \
               self.rect.y + (self.rect.height * 2) // 5
    
    def get_value_by_position(self, pos):
        value = (pos[0] - self.rect.x) * (self.max_value / self.rect.width)
        if self.direction is Direction.right_to_left:
            value = self.max_value - value

        if value > self.max_value:
            return self.max_value
        elif value < self.min_value:
            return self.min_value
        return value

    @classmethod
    def frame_call(cls):
        current_window = Window.get_current_window()
        for widget in current_window.widget_list:
            if isinstance(widget, cls):
                widget.move_button_to_value()

    def move_button_to_value(self):
        if self.is_dragging:
            self.set_value(self.get_value_by_position(pygame.mouse.get_pos()))
        self.drag_button.rect.x = self.get_position_by_value(self.get_value())[0] - (self.drag_button.rect.width // 2)

    def button_click(self):
        """Change appearance of button"""
        if self.style.style is ShapeStyle.circular:
            draw_filled_circle(
                self.drag_button_shape.surface,
                [i - j for i, j in zip(self.drag_button_shape.rect.center, self.drag_button_shape.rect.topleft)],
                int(self.rect.height / 4), self.non_value_line.color, False)
        else:
            rect = Rect(self.drag_button_shape.rect.width // 8,
                        self.drag_button.rect.height // 8, self.drag_button_shape.rect.width - self.drag_button_shape.rect.width // 4,
                        self.drag_button.rect.height - self.drag_button_shape.rect.height // 4)
            if self.style.style is ShapeStyle.rounded:
                draw_rounded_rect(self.drag_button_shape.surface, self.non_value_line.color, rect)
            elif self.style.style is ShapeStyle.sharp:
                draw.rect(self.drag_button_shape.surface, self.non_value_line.color, rect)

    def button_release(self):
        """Change appearance of button"""
        self.drag_button_shape.redraw()

    def dragged_click(self):
        self.is_dragging = True
        self.button_click()
        self.set_value(closest_number_divisible(self.get_value_by_position(pygame.mouse.get_pos()), self.value_jumps))

    def dragged_release(self):
        self.is_dragging = False
        self.button_release()

    def get_text_position(self, text: Surface):
        text_place = maybe(self.style.displayed_value_place).value.or_else(self.style.displayed_value_place)
        line_height = self.rect.height // 5
        if text_place == PlaceText.bottom_middle:
            return self.rect.x + self.rect.width // 2 - text.get_width() // 2, \
                   self.rect.bottom - self.rect.height // 2 + self.drag_button_shape.rect.height // 2
        elif text_place == PlaceText.bottom_left:
            return self.rect.x, self.rect.bottom - self.rect.height//2 + self.drag_button_shape.rect.height//2
        elif text_place == PlaceText.bottom_right:
            return self.rect.x + self.rect.width - text.get_width(), \
                   self.rect.bottom - self.rect.height // 2 + self.drag_button_shape.rect.height // 2

        elif text_place == PlaceText.top_middle:
            return self.rect.x + self.rect.width // 2 - text.get_width() // 2, \
                   self.rect.y + self.rect.height // 2 - self.drag_button_shape.rect.height // 2 - text.get_height()
        elif text_place == PlaceText.top_left:
            return self.rect.x, \
                   self.rect.y + self.rect.height//2 - self.drag_button_shape.rect.height//2 - text.get_height()

        elif text_place == PlaceText.top_right:
            return self.rect.x + self.rect.width - text.get_width(), \
                   self.rect.y + self.rect.height // 2 - self.drag_button_shape.rect.height // 2 - text.get_height()

        elif text_place == PlaceText.left:
            return self.rect.left - 2 - text.get_width() - self.drag_button_shape.rect.width // 2, \
                   self.rect.y + (2 * line_height) - ((text.get_height() - line_height)//2)
        elif text_place == PlaceText.right:
            return self.rect.right + 2 + self.drag_button_shape.rect.width // 2, \
                   self.rect.y + (2 * line_height) - ((text.get_height() - line_height)//2)

        elif text_place == PlaceText.above_cursor:
            return self.get_position_by_value(self.get_value())[0] - text.get_width()//2,\
                   self.rect.y + self.rect.height//2 - self.drag_button_shape.rect.height//2 - text.get_height()
        elif text_place == PlaceText.under_cursor:
            return self.get_position_by_value(self.get_value())[0] - text.get_width()//2, \
                   self.rect.bottom - self.rect.height//2 + self.drag_button_shape.rect.height//2

    def draw(self):
        # pygame.draw.rect(self.window.surface, pygame.Color('grey'), self.rect, 5)
        self.non_value_line.draw(self.window.surface)
        self.value_line.rect.width = self.get_position_by_value(
            (self.max_value - self.get_value()) if self.direction is Direction.right_to_left else self.get_value())[0] - self.rect.x
        if self.direction is Direction.right_to_left:
            self.value_line.rect.x = self.get_position_by_value(self.get_value())[0] #- self.rect.x
        self.value_line.redraw()
        self.value_line.draw(self.window.surface)

        if self.style.display_value:
            text = self.font.render(str(self.get_value()), True, self.style.displayed_value_color)
            self.window.surface.blit(text, self.get_text_position(text))
        # draw_filled_circle(self.window.surface, self.get_position_by_value(self.value), int(self.rect.height / 3),
        #                    self.style.drag_button_color)
        self.drag_button.draw()


def event_handle(events):
    Button.check_click(events)
    Slider.frame_call()
    TextInput.update_all(events)
    LineInput.update_all(events)

def draw_screen(surface):
    surface.fill(pygame.Color('black'))
    Window.get_current_window().draw(surface)


def Main():
    os.system('python "main debug.py"')  # running the script as main make problems


if __name__ == '__main__':
    Main()
