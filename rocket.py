import pygame
import random
from pygame.locals import RLEACCEL, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_ESCAPE, K_SPACE, K_p, KEYDOWN, QUIT
import time

###
# constants
###

# screen dimension
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# death reasons
OUT_OF_SCREEN = -1
SHOT = 0
COLLIDED = 1
RANDOMLY_KILLED = 2

# game states
EXIT_GAME = -1
GAMING = 0
PAUSED = 1

# colors
BLACK = (0,0,0)
WHITE = (255,255,255)
SCREEN_BGC = (50,100,200)
SCORE_COLOR = (200, 100, 125)
PAUSE_COLOR = (200, 200, 50)

# math constants
EPSILON = 0.001

def load_image_sequence(path, num, dims = None, ext='png'):
    seq = []
    for index in range(num):
        img = pygame.image.load("{p}{i}.{e}".format(p=path, i=index, e=ext)).convert()
        if dims:
            img = pygame.transform.scale(img, dims)
        seq.append(img)
    return seq
    

class Player(pygame.sprite.Sprite):
    def __init__(self, img):
        super(Player, self).__init__()
        
        self.surf = img
        self.surf.set_colorkey(BLACK, RLEACCEL)
        self.rect = self.surf.get_rect()
        self.shot_blocked = False
        self.score = 0
        self.alive = True
        
    def update_movement(self, pressed_keys):
        if pressed_keys[K_UP]:
            self.rect.move_ip(0, -5)
        if pressed_keys[K_DOWN]:
            self.rect.move_ip(0, 5)
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-5, 0)
        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(5, 0)
            
        # block movment out of screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
        
    def update_actions(self, pressed_keys):
        if pressed_keys[K_SPACE]:
            self.shoot()
        
    def update(self, *args, **kwargs):
        pressed_keys = kwargs.get('pressed_keys')
        if pressed_keys:
            self.update_movement(pressed_keys)
            self.update_actions(pressed_keys)
        
    def shoot(self):
        pygame.event.post(pygame.event.Event(ADDSHOT))
        
    def damage(self):
        self.score -= 1
        self.alive = self.score >= 0
        
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self, img):
        super(Enemy, self).__init__()
        rand_missile = random.randrange(0,2)
        
        self.surf = img
        self.surf = pygame.transform.scale(self.surf, (75, 50))
        self.surf.set_colorkey(BLACK, RLEACCEL)
        
        self.rect = self.surf.get_rect(
            center=(
                random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100),
                random.randint(0, SCREEN_HEIGHT),
            )
        )
        self.speed = random.randint(5,20)
        
    def update(self, *args, **kwargs):
        self.rect.move_ip(-self.speed, 0)
        if self.rect.right < 0:
            self.kill(reason=OUT_OF_SCREEN)
            
        kill_factor = kwargs.get('random_factor')
        if kill_factor and abs(kill_factor - random.random()) < EPSILON:
            self.kill(reason=RANDOMLY_KILLED)
            
    def kill(self, reason=OUT_OF_SCREEN):
        super(Enemy, self).kill()
        pygame.event.post(
            pygame.event.Event(
                ENEMYKILLED, 
                reason=reason,
                center=self.rect.center
            )
        )
        
            
class EnemyExplosion(pygame.sprite.Sprite):
    def __init__(self, center, img):
        super(EnemyExplosion, self).__init__()
        
        self.explosion_sequence = img
        self.counter = 0
        self.current = 0
        self.surf = self.explosion_sequence[self.current]
        self.surf.set_colorkey(BLACK, RLEACCEL)
        self.rect = self.surf.get_rect(center=center)
        self.exp_rate = 2
        self.speed_x = 3
        self.speed_y = 3
        
    def update(self, *args, **kwargs):
        if self.current >= len(self.explosion_sequence):
            self.kill()
            return
        
        self.counter += 1
        if self.counter == self.exp_rate and self.current < len(self.explosion_sequence):
            self.counter = 0
            self.surf = self.explosion_sequence[self.current]
            self.surf.set_colorkey(BLACK, RLEACCEL)
            self.current += 1
            
        self.rect.move_ip(-self.speed_x, -self.speed_y)
            
        
class Cloud(pygame.sprite.Sprite):
    def __init__(self, img):
        super(Cloud,self).__init__()
        self.surf = img
        self.surf.set_colorkey(BLACK, RLEACCEL)
        self.speed = 5
        
        self.rect = self.surf.get_rect(
            center=(
                random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100),
                random.randint(0, SCREEN_HEIGHT),
            )
        )
        
    def update(self, *args, **kwargs):
        self.rect.move_ip(-self.speed, 0)
        if self.rect.right < 0:
            self.kill()


class Shot(pygame.sprite.Sprite):
    def __init__(self, center, img):
        super(Shot, self).__init__()
        self.shot_sequence = img
        self.surf = self.shot_sequence[0]
        self.surf.set_colorkey(BLACK, RLEACCEL)
        self.rect = self.surf.get_rect(center=center)
        self.counter = 0
        self.current = 0
        self.speed = 15
        self.shot_rate = 2
        
    def update(self, *args, **kwargs):
        self.counter += 1
        if self.counter == self.shot_rate:
            self.counter = 0
            self.surf = self.shot_sequence[self.current]
            self.surf.set_colorkey(BLACK, RLEACCEL)
            self.current = (self.current + 1) % len(self.shot_sequence)
        self.rect.move_ip(15, 0)
        
        if self.rect.right > SCREEN_WIDTH:
            self.kill()


class Window(pygame.sprite.Sprite):
    def __init__(self, title="", dimensions=None, img=None, center=None):
        super(Window, self).__init__()
        if not dimensions:
            dimensions = (SCREEN_WIDTH, SCREEN_HEIGHT)
        if not img:
            img = pygame.Surface(size=dimensions)
            img.fill(PAUSE_COLOR)
        else:
            img = pygame.transform.scale(img, dimensions)
        if not center:
            center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)

        self.surf = img
        self.rect = self.surf.get_rect(center=center)

    def update(*args, **kwargs):
        pass

class PauseWindow(Window):
    def __init__(self, img=None):
        super(PauseWindow, self).__init__(title="Paused", dimensions=(400, 244), img=img)
        self.score_font = pygame.font.SysFont('chalkduster.ttf', 72)

    def kill(self):
        super(PauseWindow, self).kill()
        # self.texts.

pygame.init()

###
# Events
###

# define events
ADDENEMY = pygame.USEREVENT + 1
ADDCLOUD = pygame.USEREVENT + 2
ADDSHOT = pygame.USEREVENT + 3
FREESHOT = pygame.USEREVENT + 4
ENEMYKILLED = pygame.USEREVENT + 5

# set timed events
pygame.time.set_timer(ADDCLOUD, 1000)
pygame.time.set_timer(ADDENEMY, 250)

# set world time
clock = pygame.time.Clock()

###
# init screen
###

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# score font
score_font = pygame.font.SysFont('chalkduster.ttf', 72)

###
# initialize assets and sprites
###

cloud_image = pygame.image.load("assets/grey_cloud1.png").convert()
player_image = pygame.image.load("assets/jetfighter.png").convert()
enemy_image1 = pygame.image.load("assets/Missile04N.png").convert()
enemy_image2 = pygame.image.load("assets/Missile05.png").convert()
explosion_images = load_image_sequence("assets/exp", 16, (50,50))
shot_images = load_image_sequence("assets/shot", 4, (30, 20))
pause_screen = pygame.image.load("assets/pause_screen.png")

# create player
player = Player(player_image)

# init sprite containers
enemies = pygame.sprite.Group()
enemy_explosions = pygame.sprite.Group()
clouds = pygame.sprite.Group()
shots = pygame.sprite.Group()
windows = pygame.sprite.Group()

all_sprites = pygame.sprite.Group()
all_sprites.add(player)

# window hanlders
pause_window = None

###
# This is the main game loop
###

state = GAMING
while state >= 0:
    ###
    # poll pygame events
    ###
    if state == GAMING:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    state = EXIT_GAME
                if event.key == K_p:
                    pause_window = PauseWindow(img=pause_screen)
                    windows.add(pause_window)
                    all_sprites.add(pause_window)
                    state = PAUSED

            elif event.type == QUIT:
                state = EXIT_GAME

            elif event.type == ADDENEMY:
                if random.random() > 0.5:
                    new_enemy = Enemy(enemy_image1)
                else:
                    new_enemy = Enemy(enemy_image2)

                enemies.add(new_enemy)
                all_sprites.add(new_enemy)

            elif event.type == ADDCLOUD:
                new_cloud = Cloud(cloud_image)
                clouds.add(new_cloud)
                all_sprites.add(new_cloud)

            elif event.type == ADDSHOT:
                if not player.shot_blocked:
                    player.shot_blocked = True
                    shot_center = (player.rect.left, (player.rect.top + player.rect.bottom)/2)
                    new_shot = Shot(shot_center, shot_images)
                    shots.add(new_shot)
                    all_sprites.add(new_shot)
                    pygame.time.set_timer(FREESHOT, 100)

            elif event.type == FREESHOT:
                player.shot_blocked = False

            elif event.type == ENEMYKILLED:
                # check if killed by user
                if event.reason >= SHOT:
                    new_exp = EnemyExplosion(event.center, explosion_images)
                    enemy_explosions.add(new_exp)
                    all_sprites.add(new_exp)

                if event.reason == SHOT:
                    player.score += 1


        # poll pressed keys
        pressed_keys = pygame.key.get_pressed()

        # update sprites location
        rand_kill_factor = random.random()
        all_sprites.update(pressed_keys=pressed_keys, random_factor=rand_kill_factor)

        ###
        # most dynamic game logic is here, some is in the event handling:
        ###

        # check if a collision happened between an enemy and the player
        enemy_collided = pygame.sprite.spritecollideany(player, enemies)
        if enemy_collided:
            player.damage()
            enemy_collided.kill(reason=COLLIDED)


        # check if a collision happened between an enemy and a player shot
        for shot in shots:
            enemy_shot = pygame.sprite.spritecollideany(shot, enemies)
            if enemy_shot:
                enemy_shot.kill(reason=SHOT)
                shot.kill()

    elif state == PAUSED:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    state = EXIT_GAME
                if event.key == K_p:
                    pause_window.kill()
                    state = GAMING

    
    ###
    # update screen
    ###

    # background
    screen.fill(SCREEN_BGC) 
    # color in each entity
    for entity in all_sprites: 
        screen.blit(entity.surf, entity.rect)
    
    # score display
    score_img = score_font.render('{0}'.format(player.score), True, SCORE_COLOR)
    screen.blit(score_img, (SCREEN_WIDTH-200, 25))
    pygame.display.flip()

    # throttle frame rate
    clock.tick(30)
    