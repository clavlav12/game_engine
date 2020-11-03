import pygame, sys

pygame.init()
# Create the window, saving it to a variable.
surface = pygame.display.set_mode((350, 250), pygame.RESIZABLE)
pygame.display.set_caption("Example resizable window")

while True:
    surface.fill((255,255,255))

    # Draw a red rectangle that resizes with the window.
    pygame.draw.rect(surface, (200,0,0), (surface.get_width()/3,
      surface.get_height()/3, surface.get_width()/3,
      surface.get_height()/3))

    pygame.display.update()

    events = pygame.event.get()
    for idx, event in enumerate(events):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        if event.type == pygame.VIDEORESIZE:
            # is_in = False
            # for evnt in events[idx:]:
            #     if evnt.type == pygame.VIDEORESIZE:
            #         is_in = True
            # if is_in:
            #     continue

            old_surface_saved = surface
            surface = pygame.display.set_mode((event.w, event.h),
                                              pygame.RESIZABLE)
            # On the next line, if only part of the window
            # needs to be copied, there's some other options.
            surface.blit(old_surface_saved, (0,0))
            del old_surface_saved

