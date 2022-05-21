import socket
import traceback
import time
import pygame
import os
import random
import sys

# network vars
HEADER = 16
PORT = 4050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DIS'
SERVER = '192.168.1.23'
ADDR = (SERVER, PORT)

# game vars
username = ""
PARTY_CODE = ''
level = 0
lives = 0
high_score = 0
score = 0
music = True
last_music_time_playing = 0
music_toggle_cooldown = 0
FPS = 60

pygame.font.init()
pygame.mixer.init()

# initialize fonts
main_font = pygame.font.Font(os.getcwd() + "\\comic.ttf", 35)
title_font = pygame.font.Font(os.getcwd() + "\\comic.ttf", 50)
lost_font = pygame.font.Font(os.getcwd() + "\\comic.ttf", 40)
combo_font = pygame.font.Font(os.getcwd() + "\\comic.ttf", 25)

# initialize RGB colors
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
ORANGE = (252, 186, 3)

# player spaceship image
'''WINDOW_ICON = pygame.image.load(os.getcwd() + '\\images\\window_icon.png')
pygame.display.set_icon(WINDOW_ICON)
WIDTH, HEIGHT = 750, 750 # width and height of display
win = pygame.display.set_mode((WIDTH, HEIGHT)) # object used to draw & edit on display
pygame.display.set_caption("Space Invaders")'''

# load sounds
pygame.mixer.music.load(os.getcwd() + '\\sounds\\backgroundmusic.ogg')
explode = pygame.mixer.Sound(os.getcwd() + '\\sounds\\explode.wav')
shot = pygame.mixer.Sound(os.getcwd() + '\\sounds\\laser.wav')
level_up = pygame.mixer.Sound(os.getcwd() + '\\sounds\\levelup.wav')
ding = pygame.mixer.Sound(os.getcwd() + '\\sounds\\ding.wav')

ding.set_volume(0.1)

# load images
RED_SPACESHIP = pygame.image.load(os.getcwd() + '\\images\\pixel_ship_red_small.png')
GREEN_SPACESHIP = pygame.image.load(os.getcwd() + '\\images\\pixel_ship_green_small.png')
BLUE_SPACESHIP = pygame.image.load(os.getcwd() + '\\images\\pixel_ship_blue_small.png')

# player spaceship image
YELLOW_SPACESHIP = pygame.image.load(os.getcwd() + '\\images\\pixel_ship_yellow.png')

# lasers
RED_LASER = pygame.image.load(os.getcwd() + '\\images\\pixel_laser_red.png')
GREEN_LASER = pygame.image.load(os.getcwd() + '\\images\\pixel_laser_green.png')
BLUE_LASER = pygame.image.load(os.getcwd() + '\\images\\pixel_laser_blue.png')
YELLOW_LASER = pygame.image.load(os.getcwd() + '\\images\\pixel_laser_yellow.png')

WIDTH, HEIGHT = 750, 750 # width and height of display

# background
BG = pygame.transform.scale(pygame.image.load(os.getcwd() + '\\images\\background-black.png'), (WIDTH,HEIGHT))

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img,(self.x, self.y))

    def move(self, vel):
        self.y += vel # laser go up

    def off_screen(self, height): # if off screen (returns boolean)
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return colliding(self,obj)

class Ship:
    COOLDOWN = FPS/2 # half a second

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.player_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers: # draw lasers
            laser.draw(window)

    def move_lasers(self, vel, obj): # moving lasers every loop on every enemy and player
        self.cooldown()
        for laser in self.lasers: # move each laser
            laser.move(vel) # move leaser
            if laser.off_screen(HEIGHT): # if laser off screen
                self.lasers.remove(laser) # remove laser
            elif laser.collision(obj): # if laser hits ship
                obj.health -= 10
                self.lasers.remove(laser) # remove laser

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1 # while can't shoot, increment cool_down_counter

    def shoot(self,check_cooldown=True):
        if check_cooldown:
            if self.cool_down_counter == 0: # only create laser of cool_down_counter is 0
                laser = Laser(self.x, self.y, self.laser_img)
                self.lasers.append(laser) # add laser objects to list of lasers belonging to ship
                self.cool_down_counter = 1 # refresh cooldown
                #client('send','SHOT')
                shot.play()
        else:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser) # add laser objects to list of lasers belonging to ship
            #client('send','SHOT')
            shot.play()

    def get_width(self):
        return self.ship_img.get_width()
    
    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x, y, health = 100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACESHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.combos = 0
        self.last_combo = 0
        self.combo_texts = []
        self.mega_shoot = 0
        self.mega_shoot_cooldown = 0
        self.mega_shooting = False
        self.score = 0
        self.high_score = 0
        #self.client = client # client function for sending/receiving

    def move_lasers(self, vel, objs): # overrides parent class move_lasers
        global score
        self.cooldown()
        for laser in self.lasers: # move each laser
            laser.move(vel) # move leaser
            if laser.off_screen(HEIGHT): # if laser off screen
                self.lasers.remove(laser) # remove laser
            else:
                for obj in objs:
                    if laser.collision(obj): # if laser hits ship
                        if type(obj) == Enemy: # if object that got hit is an enemy
                            self.combos += 1
                            self.last_combo = time.time()
                            explode.play()
                            #client('send','EXPLODE')
                            score += 1
                            if self.combos > 1:
                                if self.health + (0.05*self.max_health)*self.combos-self.max_health*0.05 >= self.max_health:
                                    self.health = self.max_health
                                else:
                                    self.health += (0.05*self.max_health)*self.combos-self.max_health*0.05
                                if self.combos >= level+1:
                                    if self.mega_shoot + 5 > 10:
                                        self.mega_shoot = 10
                                    else:
                                        self.mega_shoot += 5
                                score += self.combos-1
                                self.combo_texts.append([obj.x,obj.y,'Combo x' + str(self.combos)+"!",time.time()])
                                #client('send','DING')
                                ding.play()
                            objs.remove(obj) # remove object from list of ship objects
                        if laser in self.lasers:
                            self.lasers.remove(laser) # remove laser

    def draw(self, window):
        super().draw(window)  
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, RED, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10)) # red bar for health lost
        pygame.draw.rect(window, GREEN, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10)) # green bar (on top) for heath remaining

class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACESHIP, RED_LASER),
        "green": (GREEN_SPACESHIP, GREEN_LASER),
        "blue": (BLUE_SPACESHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self): # override shoot methiod
        if self.cool_down_counter == 0: # only create laser of cool_down_counter is 0
            laser = Laser(self.x-10, self.y, self.laser_img)
            self.lasers.append(laser) # add laser objects to list of lasers belonging to ship
            self.cool_down_counter = 1 # refresh cooldown

def colliding(obj1, ob2): # check if any 2 objects overlapping
    offset_x = ob2.x - obj1.x # distance in x from ob1 and obj2
    offset_y = ob2.y - obj1.y # distance in y from ob1 and obj2
    return type(obj1.mask.overlap(ob2.mask, (offset_x, offset_y))) is tuple # return boolean

def solo():
    global level
    global lives
    global score
    global music
    global last_music_time_playing
    global high_score
    global music_toggle_cooldown
    
    if score > high_score: # if new high score
        high_score = score
    score = 0
    run = True
    level = 0
    lives = 5

    enemies = []
    wave_length = 5
    
    player_velocity = 5 # player movement speed (rate of pixels per frame)
    enemy_velocity = 1
    laser_velocity = 6

    player = Player(300, 630) # create player object, set position

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window(): # update & display changes
        global high_score
        win.blit(BG, (0,0)) # set background image
        # draw lives & levels
        lives_label = main_font.render(f"Lives: {lives}", 1, WHITE) # show lives left
        level_label = main_font.render(f"Level: {level}", 1, WHITE) # show current level

        win.blit(lives_label, (10,10)) # left corner of screen
        win.blit(level_label, (WIDTH - level_label.get_width() - 10, 10)) # right corner of screen

        for enemy in enemies:
            enemy.draw(win)

        for text in player.combo_texts:
            x = text[0]
            y = text[1]
            string = text[2]
            last_time = text[3]

            if time.time() - last_time > 1:
                player.combo_texts.remove(text)
                break
            combo_text = combo_font.render(string,1,ORANGE)

            alpha = (round((time.time()-last_time) * 255)-255)*-1
            textsurface=combo_text
            surface=pygame.Surface((textsurface.get_width(), textsurface.get_height()))
            surface.fill(BLACK)
            surface.blit(textsurface, (0,0))
            surface.set_alpha(alpha)
            if x > WIDTH-textsurface.get_width():
                print('sided!',str(x))
                print(WIDTH-textsurface.get_width())
                x = WIDTH - textsurface.get_width()
            win.blit(surface, (x,y))

        player.draw(win) # draw player on screen

        if lost: # if lost game
            lost_message = "Game Over! Score: " + str(score)
            if score > high_score: # if new high score
                lost_message = "Game Over! New High Score: " + str(score)
            lost_label = lost_font.render(lost_message, 1, WHITE)
            prev_high_score = main_font.render("Previous High Score: " + str(high_score), 1, WHITE)
            win.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, round(HEIGHT/2)))
            win.blit(prev_high_score, (WIDTH/2 - prev_high_score.get_width()/2, round(HEIGHT/1.5)))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0: # if all player lives lost or player has no more health left
            lost = True
            lost_count += 1

        if lost: # if player lost
            if lost_count > FPS * 3: # if lost message shown for three seconds
                run = False
            else:
                continue # stop rest of code from updating game

        if time.time() - last_music_time_playing > 2 and music:
            last_music_time_playing = 0
            pygame.mixer.music.set_volume(0.05)
        
        if len(enemies) == 0: # if no more enemies (level ended)
            if music:
                pygame.mixer.music.set_volume(0.02)
            level_up.play()
            last_music_time_playing = time.time()
            level += 1 # new level
            wave_length += 5 # add more enemies to spawn this level
            for i in range(wave_length): # spawn enemy objects
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(['red','green','blue']))
                enemies.append(enemy)

        for event in pygame.event.get(): # get pygame events
            if event.type == pygame.QUIT:
                sys.exit()

        keys = pygame.key.get_pressed() # get dict of key presses
        if keys[pygame.K_m]:
            print('Toggle music')
            if not music and time.time() - music_toggle_cooldown > 1: # if music off
                music = True
                pygame.mixer.music.set_volume(0.05)
                music_toggle_cooldown = time.time()
                print('Music on')
            if music and time.time() - music_toggle_cooldown > 1: # if music already on
                music = False
                pygame.mixer.music.set_volume(0.00)
                music_toggle_cooldown = time.time()
                print('Music off')
        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
            if keys[pygame.K_UP] and player.y - player_velocity < HEIGHT and player.y - player_velocity > 0: # up
                player.y -=  player_velocity
            if keys[pygame.K_DOWN] and player.y +  player_velocity + player.get_height() + 15 < HEIGHT: # down
                player.y +=  player_velocity
            if keys[pygame.K_LEFT] and player.x - player_velocity < WIDTH and player.x - player_velocity > 0: # left
                player.x -=  player_velocity
            if keys[pygame.K_RIGHT] and player.x +  player_velocity + player.get_width() < WIDTH: # right
                player.x +=  player_velocity
            if keys[pygame.K_SPACE]: # space bar to shoot
                player.shoot()
        else:
            if keys[pygame.K_w] and player.y - player_velocity < HEIGHT and player.y - player_velocity > 0: # up
                player.y -=  player_velocity
            if keys[pygame.K_s] and player.y +  player_velocity + player.get_height() + 15 < HEIGHT: # down
                player.y +=  player_velocity
            if keys[pygame.K_a] and player.x - player_velocity < WIDTH and player.x - player_velocity > 0: # left
                player.x -=  player_velocity
            if keys[pygame.K_d] and player.x +  player_velocity + player.get_width() < WIDTH: # right
                player.x +=  player_velocity
            if keys[pygame.K_SPACE]: # space bar to shoot
                player.shoot()

        if player.mega_shoot_cooldown == 0 and player.mega_shoot > 0:
            player.shoot(False)
            player.mega_shoot_cooldown += 20
            player.mega_shoot -= 1
            player.mega_shooting = True
        elif player.mega_shoot_cooldown > 0:
            player.mega_shooting = False 
            player.mega_shoot_cooldown -= 1

        for enemy in enemies: # loop through list of enenmies
            enemy.move(enemy_velocity) # move enemy
            enemy.move_lasers(laser_velocity, player)

            if random.randrange(0, 2*FPS) == 1: # random shoot or not
                enemy.shoot()

            if colliding(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT: # check if enemy is off screen
                lives -= 1 # lose life
                enemies.remove(enemy) # delete enemy

        if not player.mega_shooting:
            player.move_lasers(-laser_velocity, enemies) # pass in laser_velocity, and level enemies
        else:
            player.move_lasers(8, enemies) # pass in laser_velocity, and level enemies

        if player.combos > 0:
            if time.time() - player.last_combo >= 1: # if combo streak timed out
                last_combo = 0
                player.combos = 0     

def makeConnection():
    try:
        global client
        # deepcode ignore MissingClose: <NOT DONE PROGRAM>
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        print('Connected over here.')
        return True
    except Exception:
        traceback.print_exc()
        time.sleep(5)
        print("Could not establish connection with server",SERVER)
        return False

def start():
    global PARTY_CODE
    connected = True

    if makeConnection():
        print("Yay!")
        while connected:
            try:
                client.send(username.encode(FORMAT))
                usernameReply = client.recv(HEADER).decode(FORMAT)
                print("Server's username reply:",usernameReply)
                if usernameReply == 'GOT ' + username:
                    if PARTY_CODE == '': # no party code, means creating
                        print('Creating a party!')
                        client.send('CREATE'.encode(FORMAT))
                        party_codeReply = client.recv(HEADER).decode(FORMAT)
                        print('Party code reply:',party_codeReply)
                        if party_codeReply.startswith("PC_"):
                            PARTY_CODE = party_codeReply[3:]
                            print(PARTY_CODE)
                            client.send(('GOT ' + party_codeReply).encode(FORMAT))
                            confirm_code = client.recv(HEADER).decode(FORMAT)
                            print("Code confirmation:",confirm_code)
                            if confirm_code == "YES CODE": # is owner of game (because they're creating it anyway)
                                print("Successfully created party room", PARTY_CODE + "!")
                            else:
                                client.send(DISCONNECT_MESSAGE.encode(FORMAT))
                        else:
                            client.send(DISCONNECT_MESSAGE.encode(FORMAT))
                    else: # joining
                        print('Joining!')
                        client.send(("PC_"+PARTY_CODE).encode(FORMAT))
                        party_codeReply = client.recv(HEADER).decode(FORMAT)
                        print('Party code reply:',party_codeReply)
                        if party_codeReply.startswith("PC_"):
                            if party_codeReply[3:] == PARTY_CODE:
                                print('Server got the code right!')
                                client.send('YES PC'.encode(FORMAT)) # server received the correct party code!
                                codeExistsReply = client.recv(HEADER).decode(FORMAT)
                                print('Code exists reply:',codeExistsReply)
                                if codeExistsReply == "YES CODE":
                                    print("Successfully connected to party room", PARTY_CODE + "!")
                                elif codeExistsReply == "USER TAKEN": # if username already taken in that party
                                    client.send(DISCONNECT_MESSAGE.encode(FORMAT))
                                    print("The username", username, "is already taken!")
                                else:
                                    client.send(DISCONNECT_MESSAGE.encode(FORMAT))
                                    print('Disconnected from server')
                                    connected = False
                        else:
                            client.send(DISCONNECT_MESSAGE.encode(FORMAT))
                            print('Disconnected from server')
                            connected = False
                #client.send(DISCONNECT_MESSAGE.encode(FORMAT)) # nothing happened or game ended because, we reached this line
                #print('Disconnected from server')
                #connected = False
            except:
                connected = False
                traceback.print_exc()
        else:
            print('Could not connect with server')
    else:
        print('Could not connect with server')

    def game():
        global level
        global score
        global music
        global last_music_time_playing
        global high_score
        global music_toggle_cooldown
        
        if score > high_score: # if new high score
            high_score = score
        score = 0
        run = True
        level = 0
        lives = 5

        enemies = []
        wave_length = 5
        
        player_velocity = 5 # player movement speed (rate of pixels per frame)
        enemy_velocity = 1
        laser_velocity = 6

        player = Player(300, 630) # create player object, set position

        clock = pygame.time.Clock()

        lost = False
        lost_count = 0

        def redraw_window(): # update & display changes
            global high_score
            win.blit(BG, (0,0)) # set background image
            # draw lives & levels
            lives_label = main_font.render(f"Lives: {lives}", 1, WHITE) # show lives left
            level_label = main_font.render(f"Level: {level}", 1, WHITE) # show current level

            win.blit(lives_label, (10,10)) # left corner of screen
            win.blit(level_label, (WIDTH - level_label.get_width() - 10, 10)) # right corner of screen

            for enemy in enemies:
                enemy.draw(win)

            for text in player.combo_texts:
                x = text[0]
                y = text[1]
                string = text[2]
                last_time = text[3]

                if time.time() - last_time > 1:
                    player.combo_texts.remove(text)
                    break
                combo_text = combo_font.render(string,1,ORANGE)

                alpha = (round((time.time()-last_time) * 255)-255)*-1
                textsurface=combo_text
                surface=pygame.Surface((textsurface.get_width(), textsurface.get_height()))
                surface.fill(BLACK)
                surface.blit(textsurface, (0,0))
                surface.set_alpha(alpha)
                if x > WIDTH-textsurface.get_width():
                    print('sided!',str(x))
                    print(WIDTH-textsurface.get_width())
                    x = WIDTH - textsurface.get_width()
                win.blit(surface, (x,y))

            player.draw(win) # draw player on screen

            if lost: # if lost game
                lost_message = "Game Over! Score: " + str(score)
                if score > high_score: # if new high score
                    lost_message = "Game Over! New High Score: " + str(score)
                lost_label = lost_font.render(lost_message, 1, WHITE)
                prev_high_score = main_font.render("Previous High Score: " + str(high_score), 1, WHITE)
                win.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, round(HEIGHT/2)))
                win.blit(prev_high_score, (WIDTH/2 - prev_high_score.get_width()/2, round(HEIGHT/1.5)))

            pygame.display.update()

        while run:
            clock.tick(FPS)
            redraw_window()

            if lives <= 0 or player.health <= 0: # if all player lives lost or player has no more health left
                lost = True
                lost_count += 1

            if lost: # if player lost
                if lost_count > FPS * 3: # if lost message shown for three seconds
                    run = False
                else:
                    continue # stop rest of code from updating game

            if time.time() - last_music_time_playing > 2 and music:
                last_music_time_playing = 0
                pygame.mixer.music.set_volume(0.05)
            
            if len(enemies) == 0: # if no more enemies (level ended)
                if music:
                    pygame.mixer.music.set_volume(0.02)
                level_up.play()
                last_music_time_playing = time.time()
                level += 1 # new level
                wave_length += 5 # add more enemies to spawn this level
                for i in range(wave_length): # spawn enemy objects
                    enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(['red','green','blue']))
                    enemies.append(enemy)

            for event in pygame.event.get(): # get pygame events
                if event.type == pygame.QUIT:
                    sys.exit()

            keys = pygame.key.get_pressed() # get dict of key presses
            if keys[pygame.K_m]:
                print('Toggle music')
                if not music and time.time() - music_toggle_cooldown > 1: # if music off
                    music = True
                    pygame.mixer.music.set_volume(0.05)
                    music_toggle_cooldown = time.time()
                    print('Music on')
                if music and time.time() - music_toggle_cooldown > 1: # if music already on
                    music = False
                    pygame.mixer.music.set_volume(0.00)
                    music_toggle_cooldown = time.time()
                    print('Music off')
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                if keys[pygame.K_UP] and player.y - player_velocity < HEIGHT and player.y - player_velocity > 0: # up
                    player.y -=  player_velocity
                if keys[pygame.K_DOWN] and player.y +  player_velocity + player.get_height() + 15 < HEIGHT: # down
                    player.y +=  player_velocity
                if keys[pygame.K_LEFT] and player.x - player_velocity < WIDTH and player.x - player_velocity > 0: # left
                    player.x -=  player_velocity
                if keys[pygame.K_RIGHT] and player.x +  player_velocity + player.get_width() < WIDTH: # right
                    player.x +=  player_velocity
                if keys[pygame.K_SPACE]: # space bar to shoot
                    player.shoot()
            else:
                if keys[pygame.K_w] and player.y - player_velocity < HEIGHT and player.y - player_velocity > 0: # up
                    player.y -=  player_velocity
                if keys[pygame.K_s] and player.y +  player_velocity + player.get_height() + 15 < HEIGHT: # down
                    player.y +=  player_velocity
                if keys[pygame.K_a] and player.x - player_velocity < WIDTH and player.x - player_velocity > 0: # left
                    player.x -=  player_velocity
                if keys[pygame.K_d] and player.x +  player_velocity + player.get_width() < WIDTH: # right
                    player.x +=  player_velocity
                if keys[pygame.K_SPACE]: # space bar to shoot
                    player.shoot()

            if player.mega_shoot_cooldown == 0 and player.mega_shoot > 0:
                player.shoot(False)
                player.mega_shoot_cooldown += 20
                player.mega_shoot -= 1
                player.mega_shooting = True
            elif player.mega_shoot_cooldown > 0:
                player.mega_shooting = False 
                player.mega_shoot_cooldown -= 1

            for enemy in enemies: # loop through list of enenmies
                enemy.move(enemy_velocity) # move enemy
                enemy.move_lasers(laser_velocity, player)

                if random.randrange(0, 2*FPS) == 1: # random shoot or not
                    enemy.shoot()

                if colliding(enemy, player):
                    player.health -= 10
                    enemies.remove(enemy)
                elif enemy.y + enemy.get_height() > HEIGHT: # check if enemy is off screen
                    lives -= 1 # lose life
                    enemies.remove(enemy) # delete enemy

            if not player.mega_shooting:
                player.move_lasers(-laser_velocity, enemies) # pass in laser_velocity, and level enemies
            else:
                player.move_lasers(8, enemies) # pass in laser_velocity, and level enemies

            if player.combos > 0:
                if time.time() - player.last_combo >= 1: # if combo streak timed out
                    last_combo = 0
                    player.combos = 0 # game loop

def main():
    global username
    global PARTY_CODE
    global WIDTH, HEIGHT
    global win
    playing = True

    while playing: 
        playingSoloInput = "solo"#input("Are you playing solo or multiplayer? ").lower()

        if playingSoloInput == "solo":
            WINDOW_ICON = pygame.image.load(os.getcwd() + '\\images\\window_icon.png')
            pygame.display.set_icon(WINDOW_ICON)
            win = pygame.display.set_mode((WIDTH, HEIGHT)) # object used to draw & edit on display
            pygame.display.set_caption("Space Invaders")
            solo()

        elif playingSoloInput == "multiplayer":
            username = input("Enter your username: ")
            while len(username) > 10:
                username = input("Your username is too long! Enter your new username: ")

            creatingOrJoining = input("Are you creating a multiplayer game, or joining? ").lower()
            if creatingOrJoining == "creating":
                '''WINDOW_ICON = pygame.image.load(os.getcwd() + '\\images\\window_icon.png')
                pygame.display.set_icon(WINDOW_ICON)
                win = pygame.display.set_mode((WIDTH, HEIGHT)) # object used to draw & edit on display
                pygame.display.set_caption("Space Invaders")
                '''
                start()
            else:
                PARTY_CODE = input("Enter the party code: ")
                '''
                WINDOW_ICON = pygame.image.load(os.getcwd() + '\\images\\window_icon.png')
                pygame.display.set_icon(WINDOW_ICON)
                win = pygame.display.set_mode((WIDTH, HEIGHT)) # object used to draw & edit on display
                pygame.display.set_caption("Space Invaders")
                '''
                start()

if __name__ == "__main__":
    main()