from settings import *
import pygame

text_map = [
     '222222222222222222222222222222',
     '2.....1......................2',
     '2....................1.......2',
     '2....................1.......2',
     '2....................1.......2',
     '2..1.....1...................2',
     '2.......1....................2',
     '2..............1.............2',
     '2.............11.............2',
     '2..................1.........2',
     '222222222222222222222222222222'
]


world_map = {}
collision_walls = []
for j, row in enumerate(text_map):
    for i, char in enumerate(row):
        if char != '.':
            collision_walls.append(pygame.Rect(i * TILE, j * TILE, TILE, TILE))
            if char == '1':
                world_map[(i * TILE, j * TILE)] = '1'
            elif char == '2':
                world_map[(i * TILE, j * TILE)] = '2'
