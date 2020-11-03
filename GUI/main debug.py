from GUI import *
from draw_shapes import *


class ColorChooseWindow(Window):
    def __init__(self, sur: Surface):
        super(ColorChooseWindow, self).__init__(sur)
        width = sur.get_width()
        height = sur.get_height()
        red_style = SliderStyle(style=ShapeStyle.sharp,
                                display_value=True, drag_button_color=(255, 0, 0), value_line_color=(255, 0, 0))
        green_style = SliderStyle(style=ShapeStyle.sharp, displayed_value_place=PlaceText.right,
                                  display_value=True, drag_button_color=(0, 255, 0), value_line_color=(0, 255, 0))
        blue_style = SliderStyle(style=ShapeStyle.sharp, displayed_value_place=PlaceText.right,
                                 display_value=True, drag_button_color=(0, 0, 255), value_line_color=(0, 0, 255))
        self.color_sum_rect = Rect(0, 0, width, height//3)
        self.red_slider = Slider(0, 255, 15, Rect(width//4, height//3 + 0*((2*height)//9) - 50, width//2, (height//3)), self,
                                 red_style)
        self.green_slider = Slider(0, 255, 15, Rect(width//4, height//3 + 1*((2*height)//9) - 50, width//2, (height//3)),
                                   self, green_style)
        self.blue_slider = Slider(0, 255, 15, Rect(width//4, height//3 + 2*((2*height)//9) - 50, width//2, (height//3)),
                                  self, blue_style)

    @property
    def current_value(self):
        return self.red_slider.get_value(), self.green_slider.get_value(), self.blue_slider.get_value()

    def draw(self, surface):
        draw.rect(surface, self.current_value, self.color_sum_rect)
        super(ColorChooseWindow, self).draw(surface)

    def on_return_click(self):
        ColorChooseWindow.returned_value = self.current_value
        super(ColorChooseWindow, self).on_return_click()


class MainWindow2(MainWindow):
    def __init__(self, master):
        width = master.get_width()
        height = master.get_height()
        super(MainWindow2, self).__init__(master)
        self.chosen_color = (0, 0, 0, 0)
        self.button_shape = RoundedRect(Rect(width//2, height//2, width//5, height//5), Color('blue'))
        # text_font = pygame.font.SysFont("comicsansms", self.button_shape.rect.height // 5)
        # self.text = text_font.render('Click me :)', True, Color('white'))
        font_obj = font.SysFont(DEFAULT_FONT, self.button_shape.surface.get_height()//8)
        self.text_input = LineInput(200, 30, (200, 300), self, cursor_color=Color('white'))
        self.button = Button(self.button_shape.surface, self.button_shape.rect.topleft,
                             self.button_click, self, PlaceType.center, None,
                             'Click me :) please Im so beatifule text and wrapped horizonally',
                             Color('white'), font_obj)

    def button_click(self):
        # Window.sound_player.play_sound(Sounds.button_push)
        # print('start', self.text_input.input_string, self.text_input.cursor_position, 'end', sep='\n')
        ColorChooseWindow(self.surface)

    def draw(self, surface):
        if (ColorChooseWindow.returned_value is not None) and ColorChooseWindow.returned_value != self.button_shape.color:
            self.button_shape.color = ColorChooseWindow.returned_value
            self.button.set_image(self.button_shape.surface)

        self.surface.fill(Color('black'))
        super(MainWindow2, self).draw(surface)


def Main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    screen = DisplayMods.Windowed((1920, 1080))
    # Window(screen)

    window = MainWindow2(screen)
    clock = pygame.time.Clock()
    running = 1
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = 0
        event_handle(events)
        # print(slider.get_value())
        draw_screen(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    Main()
