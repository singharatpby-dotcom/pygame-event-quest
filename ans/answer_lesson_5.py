import pygame
pygame.init()
for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
        print(event.pos)