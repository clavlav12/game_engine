def one():
    import sys
    import pygame as pg


    pg.init()
    screen = pg.display.set_mode((500,500))
    screen_rect = screen.get_rect()


    rect = pg.Rect(0,0, 300, 100)
    o = 5
    rect.center = screen_rect.center
    rect2 = pg.Rect(rect.x-o, rect.y-o, rect.width+2*o, rect.height+2*o)
    pg.draw.rect(screen, pg.Color("tomato"), rect2)
    pg.draw.rect(screen, pg.Color("light blue"), rect)
    pg.display.flip()


    while pg.event.poll().type != pg.QUIT:
        pass
    pg.quit()
    sys.exit()

def two():
    import pygame
    import pygame.gfxdraw
    import sys
    pygame.init()
    screen = pygame.display.set_mode((500,500))
    screen_rect = screen.get_rect()

    def draw_rect_outline(surface, rect, color, width=1):
        x, y, w, h = rect
        x -= width
        y -= width
        h += 2*width
        w += 2*width
        width = max(width, 1)  # Draw at least one rect.
        width = min(min(width, w//2), h//2)  # Don't overdraw.

        # This draws several smaller outlines inside the first outline. Invert
        # the direction if it should grow outwards.
        for i in range(width):
            pygame.gfxdraw.rectangle(screen, (x+i, y+i, w-i*2, h-i*2), color)

    rect = (250, 50, 162, 100)
    draw_rect_outline(screen, rect, pygame.Color("light blue"), 8)
    pygame.draw.rect(screen, pygame.Color("tomato"), rect)
    pygame.display.flip()
    while pygame.event.poll().type != pygame.QUIT:
        pass
    pygame.quit()
    sys.exit()

two()
