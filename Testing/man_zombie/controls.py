class ManControl(LeftRightMovement, ShootControl, JumpControl):
    JUMP_FORCE = 750
    SHOT_DELAY = 0.4
    MOVING_SPEED = 350  # p/s

    def __init__(self, left_key, right_key, jump_key, shoot_key, man, init_direction, jump_delay):
        LeftRightMovement.__init__(self, ManControl.MOVING_SPEED, man, init_direction)
        ShootControl.__init__(self, init_direction, man, shot_delay=ManControl.SHOT_DELAY)
        JumpControl.__init__(self, jump_delay, man, init_direction, ManControl.JUMP_FORCE)
        self.shoot_key = shoot_key
        self.jump_key = jump_key
        self.right_key = right_key
        self.left_key = left_key

    def reset(self):
        BaseControl.reset(self)
        JumpControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        # print(self.in_control)
        pressed_keys = kwargs['keys']

        if self.sprite.is_dead:
            if self.direction == Direction.left:
                self.sprite.add_force(Vector2.Cartesian((self.sprite.moving_speed * self.sprite.mass)
                                                        , 0), 'friction')
                self.direction = Direction.idle_left

            if self.direction == Direction.right:
                self.sprite.add_force(Vector2.Cartesian((-self.sprite.moving_speed * self.sprite.mass)
                                                        , 0), 'friction')
                self.direction = Direction.idle_right
            return

        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            if self.direction == Direction.left:
                self.sprite.walk_left_animation.reset()
            elif self.direction == Direction.idle_left:
                self.sprite.idle_left_animation.reset()
            elif self.direction == Direction.idle_right:
                self.sprite.idle_right_animation.reset()
            self.direction = Direction.right

        elif pressed_keys[self.left_key] and (not pressed_keys[self.right_key]) :  # moving left
            if self.direction == Direction.right:
                self.sprite.walk_right_animation.reset()
            elif self.direction == Direction.idle_left:
                self.sprite.idle_left_animation.reset()
            elif self.direction == Direction.idle_right:
                self.sprite.idle_right_animation.reset()
            self.direction = Direction.left

        else:  # the user is pressing both right and left buttons or he is not pressing neither right or left
            self.stop()

        LeftRightMovement.move(self, **kwargs)

        if pressed_keys[self.jump_key] and self.jump_timer.finished() and self.sprite.on_platform:
            # jumping
            self.jump()

        if pressed_keys[self.shoot_key]:
            # shooting
            if self.direction in Direction.rights:
                self.shoot(Vector2.Cartesian(MySprites.GunBullet.SPEED))
                # self.shoot(Vector2.Cartesian(ManControl.MOVING_SPEED))
            else:
                self.shoot(Vector2.Cartesian(-MySprites.GunBullet.SPEED))
                # self.shoot(Vector2.Cartesian(-ManControl.MOVING_SPEED))


class SimpleZombieControl(LeftRightMovement):
    MOVING_SPEED = 150  # p/s

    def __init__(self, zombie, starting_direction):
        LeftRightMovement.__init__(self, SimpleZombieControl.MOVING_SPEED, zombie, starting_direction)

    def move(self, **kwargs):
        if not self.in_control:
            return
        if self.sprite.is_dead:
            self.stop()
            # print(self.sprite.force, self.sprite.velocity, '\t', self.sprite.__class__.__name__)
        LeftRightMovement.move(self, **kwargs)
        """simply move the zombie as the direction above"""

    def platform_collide(self, direction, platform):
        if direction == Direction.horizontal:
            if self.direction == Direction.left:
                self.direction = Direction.right
            elif self.direction == Direction.right:
                self.direction = Direction.left
