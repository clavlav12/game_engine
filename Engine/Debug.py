import pygame as pg
import math
from Engine import pygame_structures


def draw_arrow(start, vec, lcolor=pg.Color('red'), tricolor=pg.Color('green'), trirad=3, thickness=2, scale=1):
    end = tuple(start + vec * scale)
    start = tuple(start)
    rad = math.pi / 180
    pg.draw.line(pygame_structures.Camera.screen, lcolor, start, end, thickness)
    rotation = (math.atan2(start[1] - end[1], end[0] - start[0])) + math.pi / 2
    pg.draw.polygon(pygame_structures.Camera.screen, tricolor, ((end[0] + trirad * math.sin(rotation),
                                                                 end[1] + trirad * math.cos(rotation)),
                                                                (end[0] + trirad * math.sin(rotation - 120 * rad),
                                                                 end[1] + trirad * math.cos(rotation - 120 * rad)),
                                                                (end[0] + trirad * math.sin(rotation + 120 * rad),
                                                                 end[1] + trirad * math.cos(rotation + 120 * rad))))


def draw_circle(p, r=2, w=0, color=pg.Color('red')):
    if isinstance(color, str):
        color = pg.Color(color)
    pg.draw.circle(pygame_structures.Camera.screen, color, tuple(p) - pygame_structures.Camera.scroller, r, w)


def get_circle(r=2, w=0, color=pg.Color('red')):
    image = pg.Surface((r*2, r*2))
    if isinstance(color, str):
        color = pg.Color(color)
    pg.draw.circle(image, color, (r, r), r, w)
    return image

def draw_rect(r: pg.Rect, clr=pg.Color('red')):
    r.topleft = r.topleft - pygame_structures.Camera.scroller
    pg.draw.rect(pygame_structures.Camera.screen, clr, r, 1)
