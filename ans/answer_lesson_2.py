import pygame
pygame.init()
running = True
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        running = False