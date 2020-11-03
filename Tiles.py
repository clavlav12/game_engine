class Tile(pygame.sprite.Sprite):
    id = 0
    blocks_list = pygame.sprite.Group()

    def __init__(self, img, x, y):
        super(Tile, self).__init__()
        self.image = img
        self.rect = img.get_rect()
        self.rect.topleft = x, y
        Tile.blocks_list.add(self)

    def sprite_collide(self, _sprite, axis):
        pass

    def update(self, screen):
        self.draw(screen)

    def draw(self, screen: Surface):
        screen.blit(self.image, self.rect.topleft - Camera.scroller)

    @classmethod
    def update_all(cls, screen):
        for platform in cls.blocks_list:
            platform._update()


class BlockingTile(Tile):
    id = 1

    def __init__(self, img, x, y):
        super(BlockingTile, self).__init__(img, x, y)
        self.friction_coeff = 1  # change to mul
        self.max_stopping_friction = float('inf')  # change if want to simulate ice or something with low friction coeff
        # self.max_stopping_friction = 0  # change if want to simulate ice or something with low friction coeff

    def sprite_collide(self, _sprite, axis):
        # if not sprite.collide_mask(self, _sprite):
        #     return
        if not isinstance(_sprite, AdvancedSprite):
            return

        if axis == Direction.vertical:
            if _sprite.velocity.y > 0:  # hit from top
                # while sprite.collide_mask(_sprite, self):
                #     _sprite.position.y -= 1
                #     _sprite.rect.y -= 1
                _sprite.rect.bottom = self.rect.top
                was_on = _sprite.on_platform
                self.friction(_sprite, was_on)
                _sprite.on_platform = self
            else:  # hit from bottom
                _sprite.rect.top = self.rect.bottom
            _sprite.position.y = _sprite.rect.y
            _sprite.force.y = 0
            _sprite.velocity.y = 0
            if hasattr(_sprite.control, 'jumping') and _sprite.control.jumping:
                _sprite.control.jumping = False
                _sprite.on_platform = None

        else:
            if _sprite.velocity.x > 0:  # hit from left
                _sprite.rect.right = self.rect.left
            else:  # hit from right
                _sprite.rect.left = self.rect.right
            _sprite.position.x = _sprite.rect.x
            _sprite.force.x = 0
            _sprite.velocity.x = 0

    def friction(self, _sprite, was_on):
        if not was_on:  # he fell on the platform
            _sprite.add_force(Vector2.Cartesian(min(-_sprite.velocity.x, self.max_stopping_friction)), 'super friction')
        else:  # normal friction
            _sprite.add_force(Vector2.Cartesian(-sign(_sprite.velocity.x) * min(self.friction_coeff,
                                                                                abs(_sprite.velocity.x))), 'friction')


class Spike(BlockingTile):
    id = 2
    def sprite_collide(self, _sprite, axis):
        if isinstance(_sprite, AdvancedSprite) and _sprite.resistance_timer and axis == Direction.vertical:
            _sprite.hit_points -= 1
            _sprite.resistance_timer.activate()
        super(Spike, self).sprite_collide(_sprite, axis)
