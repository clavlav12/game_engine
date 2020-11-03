import pygame
from GlobalUse import *
from sys import exit as close_program


class PopUpMessage:
    returned_value = None

    def __init__(self, window, screen, color, text, font_object=DEFAULT_FONT, text_color=Color('white'),
                 text_justification=Justification.horizontally_centered):

        self.window = window
        self.screen = screen
        self.widget_list = []
        self.rect = pygame.Rect(0, 0, meters(400), meters(200))
        self.rect.center = screen.get_rect().center
        self.text = fit_text_to_rect(text, font_object, text_color, text_justification, self.rect)
        self.surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.main_rounded_rect = GUI.Rectangle(pygame.Rect(0, 0, meters(400), meters(200)), color)
        self.main_rounded_rect.surface.blit(self.text,
                                            (self.main_rounded_rect.rect.width//2-self.text.get_width()//2,
                                             self.main_rounded_rect.rect.height//2-self.text.get_height()//2))

    def draw(self):
        self.main_rounded_rect.draw(self.surface)
        self.draw_widgets()
        self.screen.set_alpha(122)
        self.screen.blit(self.surface, (self.rect.x, self.rect.y))  # top left at mid of the screen

    def add_widget(self, butt):
        self.widget_list.append(butt)

    def draw_widgets(self):
        for widget in self.widget_list:
            widget.draw()


class YesNoMessage(PopUpMessage):
    def __init__(self, window, screen, color, text, font_object=DEFAULT_FONT, text_color=Color('white'),
                 text_justification=Justification.horizontally_centered):
        super(YesNoMessage, self).__init__(window, screen, color, text, font_object, text_color, text_justification)

        self.yes_button_shape = GUI.RoundedRect(pygame.Rect(*meters_multi(30, 150, 110, 35)), pygame.Color('green'))
        size = int((self.yes_button_shape.rect.height)/1.5)
        yes_text = fit_text_to_rect('yes', font.SysFont(DEFAULT_FONT, size, bold=True),
                                    Color('white'), Justification.horizontally_centered, self.yes_button_shape.rect)
        self.yes_button_shape.surface.blit(yes_text,
                                           sub(place_center(self.yes_button_shape.surface.get_rect(), yes_text),2))

        self.no_button_shape = GUI.RoundedRect(pygame.Rect(*meters_multi(400-30-110, 150, 110, 35)), Color('red'))
        no_text = fit_text_to_rect('no', font.SysFont(DEFAULT_FONT, size, bold=True),
                                   Color('white'), Justification.horizontally_centered, self.no_button_shape.rect)
        self.no_button_shape.surface.blit(no_text,
                                          sub(place_center(self.no_button_shape.surface.get_rect(), no_text), 2))

        self.yes_button = GUI.Button(self.yes_button_shape.surface, self.yes_button_shape.rect.topleft, self.yes, self)
        self.no_button = GUI.Button(self.no_button_shape.surface, self.no_button_shape.rect.topleft, self.no, self)

    def yes(self):
        pass

    def no(self):
        pass


class ExitPopUpMessage(YesNoMessage):
    def __init__(self, window, screen):
        font_object = font.SysFont('comicsansms', meters(40), italic=True, bold=True)
        super(ExitPopUpMessage, self).__init__(window, screen, Color('grey'), 'Are you sure you want to exit?\n ',
                                               font_object, Color('black'))

    def yes(self):
        pygame.quit()
        close_program()

    def no(self):
        self.window.dialog = None


import GUI
