import pygame
import sys
import os
import math


pygame.mixer.init()
pygame.mixer.music.load("Music game.mp3")
pygame.mixer.music.set_volume(0.15)
# Настройки игры
WIDTH = 1200
HEIGHT = 800
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
PENTA_HEIGHT = 5 * HEIGHT
DOUBLE_HEIGHT = 2 * HEIGHT
FPS = 60
TILE = 100
FPS_POS = (WIDTH - 65, 5)
DOUBLE_PI = math.pi * 2

# ray casting настройки
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = 300
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(HALF_FOV))
PROJ_COEFF = 3 * DIST * TILE
SCALE = WIDTH // NUM_RAYS

# Настройки текстур (1200 x 1200)
TEXTURE_WIDTH = 1200
TEXTURE_HEIGHT = 1200
TEXTURE_SCALE = TEXTURE_WIDTH // TILE

# Настройки игрока
player_pos = 150, 150
player_angle = 95
player_speed = 1.8

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 0, 0)
GREEN = (0, 80, 0)
BLUE = (0, 0, 255)
DARKGRAY = (40, 40, 40)
PURPLE = (120, 0, 120)
SKYBLUE = (0, 186, 255)
YELLOW = (220, 220, 0)
SANDY = (244, 164, 96)
DARKBROWN = (97, 61, 25)
DARKORANGE = (255, 140, 0)



def mapping(a, b):
    return (a // TILE) * TILE, (b // TILE) * TILE


def ray_casting(screen, player_pos, player_angle, textures):
    global yv, texture_v, depth_v, depth_h, xh, texture_h
    ox, oy = player_pos
    xm, ym = mapping(ox, oy)
    cur_angle = player_angle - HALF_FOV
    for ray in range(NUM_RAYS):
        sin_a = math.sin(cur_angle)
        cos_a = math.cos(cur_angle)
        sin_a = sin_a if sin_a else 0.000001
        cos_a = cos_a if cos_a else 0.000001

        # Вертикали
        x, dx = (xm + TILE, 1) if cos_a >= 0 else (xm, -1)
        for i in range(0, WIDTH, TILE):
            depth_v = (x - ox) / cos_a
            yv = oy + depth_v * sin_a
            tile_v = mapping(x + dx, yv)
            if tile_v in world_map:
                texture_v = world_map[tile_v]
                break
            x += dx * TILE

        # Горизонтали
        y, dy = (ym + TILE, 1) if sin_a >= 0 else (ym, -1)
        for i in range(0, HEIGHT, TILE):
            depth_h = (y - oy) / sin_a
            xh = ox + depth_h * cos_a
            tile_h = mapping(xh, y + dy)
            if tile_h in world_map:
                texture_h = world_map[tile_h]
                break
            y += dy * TILE
        # Проекция
        depth, offset, texture = (depth_v, yv, texture_v) if depth_v < depth_h else [depth_h, xh, texture_h]
        offset = int(offset) % TILE
        depth *= math.cos(player_angle - cur_angle)
        depth = max(depth, 0.00001)
        proj_height = min(int(PROJ_COEFF / depth), 2 * HEIGHT)
        wall_column = textures[texture].subsurface(offset * TEXTURE_SCALE, 0, TEXTURE_SCALE, TEXTURE_HEIGHT)
        wall_column = pygame.transform.scale(wall_column, (SCALE, proj_height))
        screen.blit(wall_column, (ray * SCALE, HALF_HEIGHT - proj_height // 2))

        cur_angle += DELTA_ANGLE


class Drawing:
    def __init__(self, sc):
        self.sc = sc
        self.font = pygame.font.SysFont('Arial', 36, bold=True)
        self.textures = {'1': pygame.image.load('Textures\wall3.png').convert(),
                         '2': pygame.image.load('Textures\wall4.png').convert(),
                         'S': pygame.image.load('Textures\sky2.png').convert(),
                         "3": pygame.image.load("Textures\wall6.png").convert()
                         }

    def background(self, angle):
        sky_offset = -5 * math.degrees(angle) % WIDTH
        self.sc.blit(self.textures['S'], (sky_offset, 0))
        self.sc.blit(self.textures['S'], (sky_offset - WIDTH, 0))
        self.sc.blit(self.textures['S'], (sky_offset + WIDTH, 0))
        pygame.draw.rect(self.sc, DARKGRAY, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

    def world(self, player_angle, player_pos):
        ray_casting(self.sc, player_pos, player_angle, self.textures)

    def fps(self, clock):
        display_fps = str(int(clock.get_fps()))
        render = self.font.render(display_fps, False, RED)
        self.sc.blit(render, FPS_POS)


class Player:
    def __init__(self):
        self.x, self.y = player_pos
        self.angle = player_angle
        self.sensitivity = 0.002
        # Параметры коллизии
        self.side = 50
        self.rect = pygame.Rect(*player_pos, self.side, self.side)

    def angle(self):
        return self.angle

    def pos(self):
        return (self.x, self.y)

    def detect_collision(self, dx, dy):
        next_rect = self.rect.copy()
        next_rect.move_ip(dx, dy)
        hit_indexes = next_rect.collidelistall(collision_walls)

        if len(hit_indexes):
            delta_x, delta_y = 0, 0
            for hit_index in hit_indexes:
                hit_rect = collision_walls[hit_index]
                if dx > 0:
                    delta_x += next_rect.right - hit_rect.left
                else:
                    delta_x += hit_rect.right - next_rect.left
                if dy > 0:
                    delta_y += next_rect.bottom - hit_rect.top
                else:
                    delta_y += hit_rect.bottom - next_rect.top

            if abs(delta_x - delta_y) < 10:
                dx, dy = 0, 0
            elif delta_x > delta_y:
                dy = 0
            elif delta_y > delta_x:
                dx = 0
        self.x += dx
        self.y += dy

    def keys_control(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            exit()

        if keys[pygame.K_w]:
            dx = player_speed * cos_a
            dy = player_speed * sin_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_s]:
            dx = -player_speed * cos_a
            dy = -player_speed * sin_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_a]:
            dx = player_speed * sin_a
            dy = -player_speed * cos_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_d]:
            dx = -player_speed * sin_a
            dy = player_speed * cos_a
            self.detect_collision(dx, dy)

        if keys[pygame.K_LEFT]:
            self.angle -= 0.02
        if keys[pygame.K_RIGHT]:
            self.angle += 0.02

    def mouse_control(self):
        if pygame.mouse.get_focused():
            difference = pygame.mouse.get_pos()[0] - HALF_WIDTH
            pygame.mouse.set_pos((HALF_WIDTH, HALF_HEIGHT))
            self.angle += difference * self.sensitivity

    def movement(self):
        self.keys_control()
        self.mouse_control()
        self.rect.center = self.x, self.y
        self.angle %= DOUBLE_PI
        if e == 1 and 1000 < self.x < 1100 and 1050 < self.y < 1100:
            intppo_text = ["ЭТО ПОБЕДА",
                           "ПОЗДРАВЛЯЮ!",
                           "Нажмите ENTER чтобы продолжить проходить лабиринт"]
            pygame.init()
            clock = pygame.time.Clock()
            pygame.display.set_caption("ПОБЕДА!")
            fonty = pygame.transform.scale(load_image('win.jpg'), (WIDTH, HEIGHT))
            seiopp = pygame.display.set_mode([WIDTH, HEIGHT])
            seiopp.blit(fonty, (0, 0))
            text_coord = 30
            fonty1 = pygame.font.Font(None, 30)
            for line in intppo_text:
                string_rendered = fonty1.render(line, True, pygame.Color("white"))
                intro_rect = string_rendered.get_rect()
                text_coord += 10
                intro_rect.top = text_coord
                intro_rect.x = 50
                text_coord += intro_rect.height
                seiopp.blit(string_rendered, intro_rect)
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                        running = False
                if pygame.key.get_pressed()[pygame.K_RETURN] == True:
                    start_game()
                pygame.display.flip()
                clock.tick(15)
            return start_game()
        elif e == 2 and 1925 < self.x < 1975 and 2050 < self.y < 2100:
            intppo_text = ["ЭТО ПОБЕДА",
                           "ЭТОТ УРОВЕЕНЬ БЫЛ НЕПРОС НО ВЫ СПРАВИЛИСЬ",
                           "ПОЗДРАВЛЯЮ!",
                           "Нажмите ENTER чтобы продолжить проходить лабиринт"]
            pygame.init()
            clock = pygame.time.Clock()
            pygame.display.set_caption("ПОБЕДА!")
            fonty = pygame.transform.scale(load_image('win.jpg'), (WIDTH, HEIGHT))
            seioppy = pygame.display.set_mode([WIDTH, HEIGHT])
            seioppy.blit(fonty, (0, 0))
            text_coord = 30
            fonty1 = pygame.font.Font(None, 30)
            for line in intppo_text:
                string_rendered = fonty1.render(line, True, pygame.Color("white"))
                intro_rect = string_rendered.get_rect()
                text_coord += 10
                intro_rect.top = text_coord
                intro_rect.x = 50
                text_coord += intro_rect.height
                seioppy.blit(string_rendered, intro_rect)
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                        running = False
                if pygame.key.get_pressed()[pygame.K_RETURN] == True:
                    start_game()
                pygame.display.flip()
                clock.tick(15)
            return start_game()
        elif e == 3 and 2800 < self.x < 2900 and 2900 < self.y < 3000:
            intppo_text = ["ЭТО ПОБЕДА",
                           "ВЫ ПРОШЛИ САМЫЙ СЛОЖНЫЙ УРОВЕНЬ ЛАБИРИНТА",
                           'ВЫ МАСТЕР ГОЛОВАЛОМОК',
                           "ПОЗДРАВЛЯЮ!",
                           "Нажмите ENTER чтобы продолжить проходить лабиринт"]
            pygame.init()
            clock = pygame.time.Clock()
            pygame.display.set_caption("ПОБЕДА!")
            fonty = pygame.transform.scale(load_image('win.jpg'), (WIDTH, HEIGHT))
            seioppyo = pygame.display.set_mode([WIDTH, HEIGHT])
            seioppyo.blit(fonty, (0, 0))
            text_coord = 30
            fonty1 = pygame.font.Font(None, 30)
            for line in intppo_text:
                string_rendered = fonty1.render(line, True, pygame.Color("white"))
                intro_rect = string_rendered.get_rect()
                text_coord += 10
                intro_rect.top = text_coord
                intro_rect.x = 50
                text_coord += intro_rect.height
                seioppyo.blit(string_rendered, intro_rect)
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                        running = False
                if pygame.key.get_pressed()[pygame.K_RETURN] == True:
                    start_game()
                pygame.display.flip()
                clock.tick(15)
            return start_game()

text_map1 = [
     '222222222222',
     '2..........2',
     '21.1111...12',
     '21.11...1..2',
     '21....111..2',
     '21.1111...12',
     '21.1....1112',
     '2..1111...12',
     '2.1.....1.12',
     '2.1.11.1...2',
     '2.1..1...1.2',
     '222222222232'
]

text_map2 = ['222222222222222222222',
             '2...................2',
             '2.1111111.111111111.2',
             '2.1111111.11111111112',
             '2.1111111.11111111112',
             '2.1111111.11111111112',
             '2..11.....11111111112',
             '211....11111111111112',
             '2...11.11111111111112',
             '2.1111.11111111111112',
             '21111....111111111112',
             '2.....11..11111111112',
             '2.11111..111111111112',
             '2.11111.1111111111112',
             '211.......11........2',
             '21..11111....11.111.2',
             '21.111111111111.11112',
             '21.111111111111.11112',
             '211111111111111.11112',
             '21111111111111......2',
             '21111111111111..11..2',
             '211111111111111111132'
             '222222222222222222222'
             ]

text_map3 = ['2222222222222222222222222222222',
             '2.............................2',
             '2.11111.111111111111111111111.2',
             '21......111111111111111111111.2',
             '21.11.11111111111111111111111.2',
             '21111.11111................11.2',
             '2.111.11111.1111111111.11111..2',
             '2.111.11111.1111111111.11111112',
             '2...........1111111111.11111112',
             '21111111111.1111111111.11111112',
             '21111111111.1111111111.11111112',
             '21111111111.1111111111.11111112',
             '21111111111.1111111111.11111112',
             '21111111111...11111111.11111112',
             '21111111111111.........11111112',
             '21111111111111.1111111.11111112',
             '21111111111111.11111.1.11111112',
             '2111111........11111.1.11111112',
             '2111111.1111.1.11111...11111112',
             '2111111.1111.111111111111111112',
             '21111111.111.11111111111111.112',
             '211111111.......11111111111.112',
             '211111111111111.111111......112',
             '211111111111111.111111.11111112',
             '211111111111111.111111.1.11.112',
             '211111111111111.111111.1.11.112',
             '21...1.................1....112',
             '2111.1.111111111111111.1.11.112',
             '2111...111111111111111...11.112',
             '2111111111111111....11111....12',
             '21111111111111...11.......11312',
             '2222222222222222222222222222222'
             ]
world_map = {}
text_map = []
collision_walls = []


def yte():
    pygame.mixer.music.play(-1)
    if e == 3:
        world_map.clear()
        collision_walls.clear()
        text_map = text_map3[:]
        for j, row in enumerate(text_map):
            for i, char in enumerate(row):
                if char != '.':
                    collision_walls.append(pygame.Rect(i * TILE, j * TILE, TILE, TILE))
                    if char == '1':
                        world_map[(i * TILE, j * TILE)] = '1'
                    elif char == '2':
                        world_map[(i * TILE, j * TILE)] = '2'
                    elif char == '3':
                        world_map[(i * TILE, j * TILE)] = '3'
    elif e == 2:
        world_map.clear()
        collision_walls.clear()
        text_map = text_map2[:]
        for j, row in enumerate(text_map):
            for i, char in enumerate(row):
                if char != '.':
                    collision_walls.append(pygame.Rect(i * TILE, j * TILE, TILE, TILE))
                    if char == '1':
                        world_map[(i * TILE, j * TILE)] = '1'
                    elif char == '2':
                        world_map[(i * TILE, j * TILE)] = '2'
                    elif char == '3':
                        world_map[(i * TILE, j * TILE)] = '3'
    else:
        world_map.clear()
        collision_walls.clear()
        text_map = text_map1[:]
        for j, row in enumerate(text_map):
            for i, char in enumerate(row):
                if char != '.':
                    collision_walls.append(pygame.Rect(i * TILE, j * TILE, TILE, TILE))
                    if char == '1':
                        world_map[(i * TILE, j * TILE)] = '1'
                    elif char == '2':
                        world_map[(i * TILE, j * TILE)] = '2'
                    elif char == '3':
                        world_map[(i * TILE, j * TILE)] = '3'


def level1p():
    yte()
    pygame.init()
    pygame.display.set_caption("уровeнь")
    screeny = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    player = Player()
    drawing = Drawing(screeny)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
        if pygame.key.get_pressed()[pygame.K_1] == True:
            start_game()

        player.movement()
        screeny.fill(BLACK)

        drawing.background(player.angle)
        drawing.world(player.angle, player.pos())
        drawing.fps(clock)

        pygame.display.flip()
        clock.tick(FPS)


def level3():
    global e
    intyo_text = ["Это самый сложный уровень лабиринта",
                  "Удачи в прохождении",
                  "(Автор уровня проходил 5 минут)",
                  "Нажмите 1 для начала"]
    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_caption("Правила 3 уровня")
    fonty = pygame.transform.scale(load_image('wall4.png'), (WIDTH, HEIGHT))
    seiop = pygame.display.set_mode([WIDTH, HEIGHT])
    seiop.blit(fonty, (0, 0))
    text_coord = 30
    fonty1 = pygame.font.Font(None, 30)
    for line in intyo_text:
        string_rendered = fonty1.render(line, True, pygame.Color("white"))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 50
        text_coord += intro_rect.height
        seiop.blit(string_rendered, intro_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                running = False
        if pygame.key.get_pressed()[pygame.K_1] == True:
            e = 3
            level1p()
        pygame.display.flip()
        clock.tick(15)
    return start_game()


def level2():
    global e
    intyu_text = ["Этот уровень пройдут могут пройти не все, но шансы есть",
                  "УДАЧИ",
                  "Нажмите 2 для начала"]
    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_caption("Правила 2 уровня")
    fonty = pygame.transform.scale(load_image('wall6.png'), (WIDTH, HEIGHT))
    seio = pygame.display.set_mode([WIDTH, HEIGHT])
    seio.blit(fonty, (0, 0))
    text_coord = 30
    fonty1 = pygame.font.Font(None, 30)
    for line in intyu_text:
        string_rendered = fonty1.render(line, True, pygame.Color("white"))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 50
        text_coord += intro_rect.height
        seio.blit(string_rendered, intro_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                running = False
        if pygame.key.get_pressed()[pygame.K_2] == True:
            e = 2
            level1p()
        pygame.display.flip()
        clock.tick(15)
    return start_game()


def level1():
    global e
    inty_text = ["Это самый простой уровень",
                 "Пройти его не составит у вас трудностей",
                 "Нажмите ENTER для начала"]
    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_caption("Правила 1 уровня")
    fonty = pygame.transform.scale(load_image('wall3.png'), (WIDTH, HEIGHT))
    sei = pygame.display.set_mode([WIDTH, HEIGHT])
    sei.blit(fonty, (0, 0))
    text_coord = 30
    fonty1 = pygame.font.Font(None, 30)
    for line in inty_text:
        string_rendered = fonty1.render(line, True, pygame.Color("white"))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 50
        text_coord += intro_rect.height
        sei.blit(string_rendered, intro_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                running = False
        if pygame.key.get_pressed()[pygame.K_RETURN] == True:
            e = 1
            level1p()
        pygame.display.flip()
        clock.tick(15)
    return start_game()


def start_game():
    pygame.mixer.music.stop()
    pygame.mouse.set_visible(True)
    texture = ''
    into_text = ["Уровни"]
    pygame.init()
    pygame.display.set_caption("Выбор уровня")
    buti = Button(80, 50)
    fonty = pygame.transform.scale(load_image('levels.jpg'), (WIDTH, HEIGHT))
    seo = pygame.display.set_mode([WIDTH, HEIGHT])
    seo.blit(fonty, (0, 0))
    text_coord = 30
    fonty1 = pygame.font.Font(None, 30)
    for line in into_text:
        string_rendered = fonty1.render(line, True, pygame.Color("white"))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 550
        text_coord += intro_rect.height
        seo.blit(string_rendered, intro_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                running = False
        buti.draw(150, 200, "1 level", level1, seo)
        buti.draw(550, 200, "2 level", level2, seo)
        buti.draw(1050, 200, "3 level", level3, seo)
        pygame.display.flip()

    return start_screen()


def settings():
    intro_text = ["ПРАВИЛА", "",
                  "Это головоломка для любителей лабиринта", "я уверен вы пройдете этот лабиринт",
                  "Здесь 3 уровня лабиринта",
                  "Сложность по возрастанию",
                  "",
                  "УПРАВЛЕНИЕ", "",
                  "W - идти вперед",
                  "A - идти налево",
                  "S - идти назад",
                  "D - идти направо",
                  "стрелочка налево - поворот камеры налево",
                  "стрелочка направо - поворот камеры направо",
                  "1 - выход в меню выбора уровня из лабиринта"]
    pygame.init()
    pygame.display.set_caption("Настройки")
    fon = pygame.transform.scale(load_image('settings.jpg'), (WIDTH, HEIGHT))
    se = pygame.display.set_mode([WIDTH, HEIGHT])
    se.blit(fon, (0, 0))
    fonte = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = fonte.render(line, True, pygame.Color("white"))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        if line == "УПРАВЛЕНИЕ" or line == "ПРАВИЛА":
            if line == "УПРАВЛЕНИЕ":
                intro_rect.x = 530
            else:
                intro_rect.x = 550
        text_coord += intro_rect.height
        se.blit(string_rendered, intro_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE] == True:
                running = False
        pygame.display.flip()

    return start_screen()


def print_text(mes, x, y, font_color=(0, 0, 0), font_type="PingPong.ttf", font_size=20):
    font_type = pygame.font.Font(font_type, font_size)
    text = font_type.render(mes, True, font_color)
    screen.blit(text, (x, y))


class Button:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ac = (23, 204, 58)
        self.inac = (13, 162, 58)

    def draw(self, x, y, mes, func, screen):
        mousee = pygame.mouse.get_pos()
        if x < mousee[0] < x + self.w and y < mousee[1] < y + self.h:
            pygame.draw.rect(screen, self.ac, (x, y, self.w, self.h))
            if pygame.mouse.get_pressed()[0] and func != None:
                pygame.time.delay(300)
                func()
        else:
            pygame.draw.rect(screen, self.inac, (x, y, self.w, self.h))
        print_text(mes, x + 10, y + 10)


def load_image(name, colorkey=None):
    fullname = os.path.join('Textures', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def start_screen():
    inteo_text = ["ЛАБИРИНТ"]
    pygame.display.set_caption("Лабиринт")
    fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 80)
    text_coord = 50
    button = Button(150, 50)
    clock = pygame.time.Clock()
    for line in inteo_text:
        string_rendered = font.render(line, True, pygame.Color("red"))
        intro_rect = string_rendered.get_rect()
        intro_rect.top = text_coord
        intro_rect.x = 450
        text_coord += intro_rect.width
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.update()
        button.draw(500, 200, "START", start_game, screen)
        button.draw(500, 400, "SETTINGS", settings, screen)
        pygame.display.flip()
        button.draw(500, 600, "QUIT", terminate, screen)
        clock.tick(FPS)


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    pygame.init()
    black_color = (0, 0, 0)
    screen = pygame.display.set_mode([WIDTH, HEIGHT])
    screen.fill(black_color)
    start_screen()
