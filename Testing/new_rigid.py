from Engine import pygame_structures
from Engine import base_sprites
from Engine import base_control
from typing import Optional, Tuple
from Engine import structures
from typing import Union
import pygame as pg
import math
import os


class RotationMatrix:
    def __init__(self, angle):
        self.tl = structures.DegTrigo.cos(angle)
        self.tr = -structures.DegTrigo.sin(angle)
        self.bl = -self.tr
        self.br = self.tl

    def __mul__(self, other):
        if isinstance(other, structures.Vector2):
            return structures.Vector2.Cartesian(
                self.tl * other.x + self.tr * other.y,
                self.bl * other.x + self.br * other.y
            )
        return NotImplemented

    def __rmul__(self, other):
        return self * other


class RigidBall(base_sprites.ImagedRigidBody):
    def __init__(self, radius, x, y, control=False):
        """
        :param radius:
        :param x: center x position
        :param y: center y position
        """
        image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        pg.draw.circle(image, pg.Color("red"), (radius, radius), radius)
        rect = pg.Rect(x - radius, y - radius, radius * 2, radius * 2)

        density = 1
        if not control:
            super(RigidBall, self).__init__(image, rect, radius ** 2 * math.pi * density, math.pi * radius ** 4 / 4, 0)
        else:
            super(RigidBall, self).__init__(image, rect, radius ** 2 * math.pi * density, math.pi * radius ** 4 / 4, 0,
                                            control=base_control.AllDirectionMovement(self))

        self.generate_collision_manifold = False
        self.collision_manifold_generator = self.ball2ball
        self.radius = radius

        self.restitution = 0.5

    def operate_gravity(self):
        pass

    def collision(self, other, collision):
        if not isinstance(other, RigidBall):
            return False

        self.resolve_collision(other, collision)
        return True

    def resolve_collision(self, other, manifold):
        is_collision = self.resolve_penetration(other, manifold)
        if not is_collision:
            return
        normal = (self.com_position - other.com_position).normalized()
        relative_velocity = self.velocity - other.velocity
        separating_velocity = relative_velocity * normal

        new_separating_velocity = - separating_velocity * min(self.elasticity, other.elasticity)

        vel_sep_diff = new_separating_velocity - separating_velocity
        impulse = vel_sep_diff / (self.inv_mass + other.inv_mass)
        impulse_vector = normal * impulse

        self.velocity += impulse_vector * self.inv_mass
        other.velocity += impulse_vector * -other.inv_mass

    def resolve_penetration(self, other, manifold):
        distance = self.com_position - other.com_position
        pen = self.radius + other.radius - abs(distance)
        if pen < 0:
            return False
        pen_res = distance.normalized() * pen / (self.inv_mass + other.inv_mass)

        self.add_to_position(pen_res * self.inv_mass)
        other.add_to_position(-pen_res * other.inv_mass)
        return True

    def ball2ball(self, other: Union[base_sprites.Tile,
                                     base_sprites.BaseSprite,
                                     pg.sprite.Sprite]):
        pass


class WallControl(base_control.BaseControl):
    def __init__(self, sprite: base_sprites.BaseRigidBody):
        super(WallControl, self).__init__(sprite, structures.Direction.right)

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        keys = kwargs['keys']
        if keys[pg.K_RIGHT]:
            # self.sprite.start += structures.Vector2.Cartesian(-1, 0)
            self.sprite.angular_velocity = 150
            self.sprite.update_attributes()
        if keys[pg.K_LEFT]:
            # self.sprite.start += structures.Vector2.Cartesian(1, 0)
            self.sprite.angular_velocity = - 150
            self.sprite.update_attributes()


class Capsule(base_sprites.BaseRigidBody):
    def __init__(self, p1, p2, radius):
        self.p1 = structures.Vector2.Point(p1)
        self.p2 = structures.Vector2.Point(p2)
        rect =

    def get_rect(self):
        left = min(self.p1.x, self.p2.x)
        top = min(self.p1.y, self.p2.y)
        width = max(abs(self.p1.x - self.p2.x), 1)
        height = max(abs(self.p1.y - self.p2.y), 1)
        return pg.Rect(left, top, width, height)

class Wall(base_sprites.BaseRigidBody):
    def __init__(self, start: Union[structures.Vector2, tuple, list], end: Union[structures.Vector2, tuple, list]):
        self.start = structures.Vector2.Point(start)
        self.end = structures.Vector2.Point(end)

        self.ref_start = self.start.copy()
        self.ref_end = self.end.copy()
        self.ref_unit = (self.end - self.start).normalized()
        self.ref_center = (self.start + self.end) / 2

        self.orientation = 0
        # super(Wall, self).__init__(self.get_rect(), base_control.NoMoveControl(), 500)
        # super(Wall, self).__init__(self.get_rect(), WallControl(self), 500)
        super(Wall, self).__init__(self.get_rect(), 500, 1, 0, base_control.NoMoveControl())

        self.update_attributes()

        self.collide_check_by_rect = True

    def update(self, control_dict):
        rot_mat = RotationMatrix(self.orientation)
        new_dir = rot_mat * self.ref_unit

        self.start = self.ref_center + (new_dir * (-self.length / 2))
        self.end = self.ref_center + (new_dir * (self.length / 2))

        print(self.angular_velocity)
        self.angular_velocity -= min(200 * control_dict['dtime'] * structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=lambda x: abs(x))
        # self.angular_velocity *= 0.01 ** control_dict['dtime']

        self.update_attributes()

    @property
    def length(self):
        return (self.end - self.start).magnitude()

    def update_attributes(self):
        self.rect = self.get_rect()
        self.set_position(*self.rect.topleft)

        image = pg.Surface(self.rect.size, pg.SRCALPHA)

        pg.draw.line(
            image,
            pg.Color("black"),
            tuple(self.start - self.rect.topleft),
            tuple(self.end - self.rect.topleft),
            3
        )

        self.image = image.convert_alpha()
        self.mask = pg.mask.from_surface(self.image)

    def get_rect(self):
        left = min(self.start.x, self.end.x)
        top = min(self.start.y, self.end.y)
        width = max(abs(self.start.x - self.end.x), 1)
        height = max(abs(self.start.y - self.end.y), 1)
        return pg.Rect(left, top, width, height)

    def unit(self):
        return (self.end - self.start).normalized()

    def closest_point(self, sprite: base_sprites.BaseSprite):
        ball_to_start = self.start - sprite.com_position
        if self.unit() * ball_to_start > 0:
            return self.start

        ball_to_end = sprite.com_position - self.end
        if self.unit() * ball_to_end > 0:
            return self.end

        closest_distance = self.unit() * ball_to_start
        closest_vector = self.unit() * closest_distance
        return self.start - closest_vector
    
    def collision(self, other, collision):
        if not isinstance(other, RigidBall):
            return False
        if not self.collide_with(other):
            return False

        pen_vec = other.com_position - self.closest_point(other)
        other.add_to_position(pen_vec.normalized() * (other.radius - pen_vec.magnitude()))

        normal = (other.com_position - self.closest_point(other)).normalized()
        separating_velocity = other.velocity * normal
        new_separating_velocity = - separating_velocity * other.elasticity
        vel_sep_diff = separating_velocity - new_separating_velocity

        other.velocity += normal * -vel_sep_diff

    def collide_with(self, other: RigidBall):
        ball_to_closest = self.closest_point(other) - other.com_position
        return ball_to_closest.magnitude() <= other.radius
    
    # def draw(self, draw_health=False):
    #     self.draw_rect()
    #     super(Wall, self).draw()


def draw_circle(p):
    pg.draw.circle(pygame_structures.Camera.screen, pg.Color('red'), tuple(p), 2)


def Main():
    W = 1000
    H = 700

    screen = pygame_structures.DisplayMods.Windowed((W, H))
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

    pygame_structures.Camera.init(screen, "dynamic", None)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame_structures.Map([], [], [], [], 50)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    RigidBall(50, 500, 500, False)
    RigidBall(20, 200, 450, True)

    p1, p2 = (250, 400), (600, 400)
    # wall = Wall(p1, p2)
    # Wall((0, 0), (600, 1))
    Wall((0, 0), (W, 0))
    Wall((0, 0), (0, H))
    Wall((0, H), (W, H))
    Wall((W, 0), (W, H))

    while running:
        events = pg.event.get()
        for event in events:
            if event.type == pg.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pg.QUIT:
                running = 0
            elif event.type == pg.KEYDOWN:
                pass
            elif event.type == pg.MOUSEBUTTONDOWN:
                pass
                # if event.button == 1:
                #     random_planet(*add_positions(add_positions(pygame.mouse.get_pos(),
                #                                                pygame_structures.Camera.scroller.position()),
                #                                  (-W // 2, -H // 2)))
                # elif event.button == 3:
                #     pygame_structures.Camera.set_scroller_position(next_sprite(), smooth_move=True)

        keys = pg.key.get_pressed()
        if keys[pg.K_LCTRL] and keys[pg.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()
        base_sprites.tick(elapsed, keys)

        # vec = wall.closest_point(ball) - ball.com_position
        # pg.draw.line(pygame_structures.Camera.screen,
        #              pg.Color('red'),
        #              tuple(ball.com_position),
        #              tuple(ball.com_position + vec),
        #              2)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    Main()
    # mat = RotationMatrix(30)
    # vec = structures.Vector2.Cartesian(20, 65)
    #
    # vec2 = vec.copy()
    # vec2.theta += 30
    # print(mat * vec, vec2)
