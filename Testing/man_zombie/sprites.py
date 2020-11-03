class Man(AdvancedSprite):
    """Main player sprites"""
    # just taking random image to get height and width after trans scale to be able to crop later (see lines 23/36)
    scale = 1 / 2.5
    idle_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Firing" + '\\*', scale)
    dying_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Dying" + '\\*', scale)
    dying_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), dying_right_images))
    move_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Run Firing" + '\\*', scale,
                                        sort_key=lambda x: int(x.split('\\\\')[-1].split(' ')[-1].split('.')[0]))
    move_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), move_right_images))

    idle_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), idle_right_images))
    direction = {'right': 1, 'left': 0, 'idle': 2}
    CAPACITY = 4

    # hitbox = (x+55, y+35, self.width-125, self.height-45) # nothing special on those num, just Trial and error

    def __init__(self, x, y, jump_key, right_key, left_key, shoot_key, health_bar_colors, name):
        # hit boxes & moving
        self.moving_speed = 350

        self.walk_left_animation = Animation.by_images_list(Man.move_left_images, 30)  # Random number. should play with
        # it for best results
        self.walk_right_animation = Animation.by_images_list(Man.move_right_images, 30)
        self.dying_right_animation = Animation.by_images_list(Man.dying_right_images, 10, False)
        self.dying_left_animation = Animation.by_images_list(Man.dying_left_images, 10, False)
        self.idle_right_animation = Animation.by_images_list(Man.idle_right_images, 10)
        self.idle_left_animation = Animation.by_images_list(Man.idle_left_images, 10)

        rect = Man.idle_right_images[0].get_rect()  # just random. it will set again every time image changes
        rect.topleft = x, y
        super(Man, self).__init__(rect, controls.ManControl(left_key, right_key, jump_key, shoot_key, self,
                                                            Direction.idle_right, 0.5), 1, 10, health_bar_colors, 2)
        # super(Man, self).__init__(rect, controls.SimpleZombieControl(self, Direction.right), 1, health_bar_colors, 10,
        #                           resistance_length=2)

        # visuals
        self.name = name

        # jumping & physics
        # self.last_rect = self.rect
        self.hit_timer = Timer(1)

    def final_dead(self):
        pass

    def draw(self):
        dead = False
        if not self.is_dead:
            if self.control.direction in (Direction.right, Direction.jumping_right):  # moving right
                self.image = self.walk_right_animation.get_image()
            elif self.control.direction in (Direction.left, Direction.jumping_left):
                self.image = self.walk_left_animation.get_image()
            elif self.control.direction == Direction.idle_left:
                self.image = self.idle_left_animation.get_image()
            elif self.control.direction == Direction.idle_right:
                self.image = self.idle_right_animation.get_image()

        elif self.visible:  # if man died but still visible:
            if self.control.direction in Direction.lefts:
                self.image = self.dying_left_animation.get_image()
            elif self.control.direction in Direction.rights:
                self.image = self.dying_right_animation.get_image()
            x, y = self.rect.topleft
            self.rect = self.image.get_rect()
            self.rect.topleft = (x, y)
            dead = True
            # self.draw_rect()
        else:
            self.final_dead()  # if man is completely dead
        super(Man, self).draw(not dead)


class Zombie(AdvancedSprite):
    scale = 1 / 2.5
    moving_right_images = get_images_list(r"animation\zombie\PNG\Tiny "
                                          r"Zombie 01\PNG Sequences\Walking" + '\\*', scale)
    moving_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), moving_right_images))

    dying_right_images = get_images_list(r'animation\zombie\PNG\Tiny Zombie 01\PNG Sequences\Dying' + '\\*', scale)
    dying_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), dying_right_images))

    idle_right_images = get_images_list(r'animation\zombie\PNG\Tiny Zombie 01\PNG Sequences\idle' + '\\*', scale)
    idle_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), idle_right_images))

    def __init__(self, x, y):
        rect = Zombie.moving_right_images[0].get_rect()
        rect.topleft = x, y

        self.walk_right_animation = Animation.by_images_list(Zombie.moving_right_images, 3)
        self.walk_left_animation = Animation.by_images_list(Zombie.moving_left_images, 3)

        self.dying_right_animation = Animation.by_images_list(Zombie.dying_right_images, 3, False)
        self.dying_left_animation = Animation.by_images_list(Zombie.dying_left_images, 3, False)

        self.idle_right_animation = Animation.by_images_list(Zombie.idle_right_images, 3)
        self.idle_left_animation = Animation.by_images_list(Zombie.idle_left_images, 3)
        self.moving_speed = 150
        self.damage = 3

        self.hit_strength = 1000
        self.idle_hit_angle = 40

        super(Zombie, self).__init__(rect, controls.SimpleZombieControl(self, 1), 1, 10, ((4, 3, 137), (66, 165, 245)),
                                     1)
        # super(Zombie, self).__init__(rect, controls.ManControl(K_LEFT, K_RIGHT, K_SPACE, K_RETURN, self,
        #                                                        Direction.idle_right, Timer(2)), 1, ((4, 3, 137), (66, 165, 245)), 10)

    def draw(self):
        if not self.is_dead:
            if self.control.direction == Direction.right:  # moving right
                self.image = self.walk_right_animation.get_image()
            elif self.control.direction == Direction.left:
                self.image = self.walk_left_animation.get_image()
            elif self.control.direction == Direction.idle_left:
                self.image = self.idle_left_animation.get_image()
            elif self.control.direction == Direction.idle_right:
                self.image = self.idle_right_animation.get_image()

        elif self.visible:  # if man died but still visible:
            if self.control.direction in Direction.lefts:
                self.image = self.dying_left_animation.get_image()
            elif self.control.direction in Direction.rights:
                self.image = self.dying_right_animation.get_image()
        else:
            self.final_dead()  # if man is completely dead

        super(Zombie, self).draw()

    def collision(self, other: AdvancedSprite):
        if self.is_dead:
            return

        if isinstance(other, Vehicle):
            if self.control.direction == Direction.right and other.rect.right > self.rect.right:
                self.control.direction = Direction.left
            elif self.control.direction == Direction.left and other.rect.left < self.rect.left:
                self.control.direction = Direction.right

        elif isinstance(other, AdvancedSprite) and other.resistance_timer.finished():
            other.hit_points -= self.damage
            if round(other.velocity.x, 2) == 0:
                if self.control.direction in Direction.lefts:
                    other.add_force(Vector2.Polar(self.hit_strength, 180 + self.idle_hit_angle), 'push')
                elif self.control.direction in Direction.rights:
                    other.add_force(Vector2.Polar(self.hit_strength, 360 - self.idle_hit_angle), 'push')
            else:
                if self.rect.center[0] > other.rect.center[0]:  # The zombie is to the right of other
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 180 + self.idle_hit_angle), 'push')
                elif self.rect.center[0] < other.rect.center[0]:  # The zombie is to the left of other
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 360 - self.idle_hit_angle), 'push')
                else:
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 270), 'push')

            other.resistance_timer.activate()
            t = Timer(3, True)
            # other.control.in_control = UntilCondition(lambda: other.on_platform or t)
            other.control.in_control = UntilCondition(lambda: other.platform_collide or
                                                              (other.sprite_collide and not
                                                              isinstance(other.sprite_collide, Zombie)) or t)


