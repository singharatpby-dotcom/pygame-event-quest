import pygame
pygame.init()
player_x, player_y = 0, 0
for event in pygame.event.get():
    if event.type == pygame.MOUSEMOTION:
        player_x, player_y = event.pos