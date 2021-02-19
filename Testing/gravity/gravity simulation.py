import os
import pygame
import math
from Engine.structures import VectorType, Vector2, Direction, DegTrigo
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
import random

W = 1000
H = 700
# screen = DisplayMods.Windowed((1680, 1080))
print("mod")
screen = pygame_structures.DisplayMods.Windowed((W, H))
W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

pygame_structures.Camera.init(screen, "dynamic", None)


# pygame_structures.Camera.init(screen, "static", None)


class Planet(base_sprites.BaseSprite):
    # GravitationalConstant = .1e-2
    GravitationalConstant = 100
    # CoulombConstant = .1e-2
    fnt = pygame.font.SysFont('comicsansms', 12)

    def __init__(self, x, y, mass, color, radius):
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.image.convert_alpha()
        super(Planet, self).__init__(pygame.Rect(x - radius, y - radius, radius * 2, radius * 2),
                                     base_control.BaseControl(self, Direction.right), mass)
        self.color = color
        self.radius = radius

        self.mass_text = self.fnt.render(f'{self.mass:,}', True, pygame.Color('green'))
        self.mass_rect = self.mass_text.get_rect()

    # def
    def update(self, kwargs):
        # if not (10 * W > self.rect.x > - 10 * W):
        #     MySprites.BaseSprite.sprites_list.remove(self)
        # if not (10 * H > self.rect.y > - 10 * H):
        #     MySprites.BaseSprite.sprites_list.remove(self)

        for sprite in kwargs['sprites']:
            if sprite is not self:
                try:
                    sprite.add_force(Vector2.Polar(self.GravitationalConstant * self.mass * sprite.mass /
                                                   self.distance(self.rect.center, sprite.rect.center) ** 2,
                                                   DegTrigo.atan2(self.rect.center[0] - sprite.rect.center[0],
                                                                  self.rect.center[1] - sprite.rect.center[1])),
                                     mul_dtime=False)
                except ZeroDivisionError:
                    pass

    def collision(self, other):
        radius = int(math.sqrt(self.radius**2 + other.radius**2))
        self.set_mass(self.mass + other.mass)
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA, 32)
        if self.mass > 1_000_000:
            color = (0, 0, 0)
        else:
            color = [
                self.ceil(0, 255, (self.color[i] + other.color[i]) // 2) for i in range(3)
            ]
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.image.convert_alpha()
        self.color = color
        self.radius = radius

        self.velocity = (self.mass * self.velocity + other.mass * other.velocity) / (self.mass + other.mass)
        other.velocity = Vector2.Zero()
        self.force = Vector2.Zero()
        other.force = Vector2.Zero()

        other.kill()

        return True

    def set_mass(self, value):
        self.mass = value
        self.mass_text = self.fnt.render(f'{self.mass:,}' , True, pygame.Color('green'))
        self.mass_rect = self.mass_text.get_rect()

    @staticmethod
    def distance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    @staticmethod
    def ceil(min_, max_, num):
        return min(max(num, min_), max_)

    def draw(self):
        self.rect.x -= self.radius + self.rect.width // 2
        self.rect.y -= self.radius + self.rect.height // 2
        super(Planet, self).draw()
        self.rect.x += self.radius - self.rect.width // 2
        self.rect.y += self.radius - self.rect.height // 2
        self.mass_rect.center = self.rect.center
        self.mass_rect.bottom = self.rect.top
        r = pygame.Rect(self.mass_rect)
        r.topleft = r.topleft - pygame_structures.Camera.scroller
        pygame_structures.Camera.blit(self.mass_text, r)
        # self.draw_rect()


def random_position():
    return random.randint(0, W), random.randint(0, H)


def random_color():
    color = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    while color[0] < 155 and color[2] < 155:
        color = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    return color


def random_planet(x, y):
    return Planet(x, y, random.randint(1, 100000), random_color(), random.randint(1, 10))


current = None


def next_sprite():
    global current
    try:
        if current is None:
            for i in base_sprites.BaseSprite.sprites_list:
                break
            current = i
            return i
        else:
            now = False
            for i in base_sprites.BaseSprite.sprites_list:
                if now:
                    current = i
                    return i
                if i is current:
                    now = True
            for i in base_sprites.BaseSprite.sprites_list:
                break
            current = i
            return i
    except:
        return W // 2, H // 2


def add_positions(pos1, pos2):
    return pos1[0] + pos2[0], pos1[1] + pos2[1]


def sub_positions(pos1, pos2):
    return pos1[0] - pos2[0], pos1[1] - pos2[1]


def mul_position(pos1, n):
    return pos1[0] * n, pos1[1] * n


def Main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    # man = Man(600, 200, K_SPACE, K_RIGHT, K_LEFT, K_RETURN, ((0, 255, 0), (255, 0, 0)), 'M')
    # man.rect.bottom = 400
    # man.position.values = man.rect.topleft
    # r = 5
    # planet1 = Planet(*random_position(), 10000, pygame.Color('blue'), r)
    # planet2 = Planet(*random_position(), 10000, pygame.Color('red'), r)
    # planet3 = Planet(*random_position(), 10000, pygame.Color('green'), r)
    # pygame_structures.Camera.set_scroller_position(lambda: (W // 2, H // 2), smooth_move=False)
    pygame_structures.Map([], [], [], [], 50)
    running = 1
    fps = 1000
    elapsed = 1 / fps
    # fnt = pygame.font.SysFont('comicsansms', 12)
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.KEYDOWN:
                pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    random_planet(*add_positions(add_positions(pygame.mouse.get_pos(),
                                                               pygame_structures.Camera.scroller.position()),
                                                 (-W // 2, -H // 2)))
                elif event.button == 3:
                    pygame_structures.Camera.set_scroller_position(next_sprite(), smooth_move=True)
        # first = fnt.render(f'Hit Points: {tank1.hit_points}', True, get_color(tank1.hit_points))
        # second = fnt.render(f'Hit Points: {tank2.hit_points}', True, get_color(tank2.hit_points))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()
        base_sprites.tick(elapsed, keys)
        # Camera.blit(first, (W - 150, 50))
        # Camera.blit(second, (5, 50))
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pygame.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    Main()
