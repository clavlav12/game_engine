from pygame import init
init()
import Engine.base_sprites
import Engine.base_control
base_control.init(base_sprites.player, base_sprites.Magazine, base_sprites.GunBullet)
import Engine.pygame_structures
pygame_structures.init(Engine.base_sprites.Tile, Engine.base_sprites.air,
                       Engine.base_sprites.BaseSprite, Engine.base_sprites.clock)
import CollisionManifold
from Engine import AdvancedRigidBody

CollisionManifold.initialize(
    Engine.base_sprites.BaseSprite,
    Engine.base_sprites.BaseRigidBody,
    # AdvancedRigidBody.AdvancedRigidBody,
    base_sprites.Tile
)
