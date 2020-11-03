import MySprites
import pygame

class Particle(pygame.sprite.Sprite):
    particle_list = pygame.sprite.Group()
    particle_sprite_list = pygame.sprite.Group()  # particles who need to check collide with sprites

    def __init__(self, image, center_position, collide):
        super(Particle, self).__init__()
        self.rect = image.get_rect(center=center_position)
        self.image = image
        Particle.particle_list.add(self)
        if collide:
            Particle.particle_sprite_list.add(self)

    def draw(self):
        MySprites.Camera.blit(self.image, self.rect.topleft - MySprites.Camera.scroller)
        # self.draw_rect()
        
    def update(self):
        self.draw()

    @classmethod
    def update_all(cls):
        for sprite in cls.particle_list:
            sprite.update()

    def collide(self, other):
        pass

    def draw_rect(self, clr=pygame.Color('red')):
        r = pygame.Rect(self.rect)
        r.topleft = r.topleft - MySprites.Camera.scroller
        pygame.draw.rect(MySprites.Camera.screen, clr, r, 1)

    @classmethod
    def check_all_collision(cls):
        for particle in cls.particle_sprite_list:
            lst = pygame.sprite.spritecollide(particle, MySprites.BaseSprite.sprites_list, False)
            for sprite in lst:
                particle.collide(sprite)


class Explosion(Particle):
    IMAGE_LIST = MySprites.get_images_list(r'animation\explostions\\*.png', 1)

    def __init__(self, center_position, fpi=20, collide_function=None):
        self.animation = MySprites.Animation.by_images_list(Explosion.IMAGE_LIST, frames_per_image=fpi, repeat=False)
        self.collide_function = collide_function
        super(Explosion, self).__init__(self.animation.get_image(), center_position, collide_function is not None)

    def update(self):
        if self.animation.finished():
            self.kill()
            return
        self.image = self.animation.get_image()
        super(Explosion, self).update()

    def collide(self, other):
        self.collide_function(other)
