
import pygame
import random
import math
import json
import sys

pygame.init()

# ================= SCREEN =================
W, H = 1000, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("FISH WORLD V4")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (10, 20, 35)
BLUE = (20, 130, 220)
CYAN = (40, 230, 255)
GOLD = (255, 200, 20)
RED = (240, 60, 70)
GREEN = (50, 220, 130)
PURPLE = (180, 80, 255)

font = pygame.font.SysFont("Arial", 23, bold=True)
medium = pygame.font.SysFont("Arial", 38, bold=True)
big = pygame.font.SysFont("Arial", 65, bold=True)

# ================= SAVE SYSTEM =================
SAVE = "fish_v4_save.json"

data = {
    "coins": 0,
    "high_score": 0,
    "unlocked": [0]
}

def load_save():
    global data
    try:
        with open(SAVE, "r") as f:
            saved = json.load(f)
            data.update(saved)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def save_game():
    with open(SAVE, "w") as f:
        json.dump(data, f)

load_save()

# ================= STATES =================
MENU = "menu"
SELECT = "select"
SHOP = "shop"
PLAY = "play"
PAUSE = "pause"
OVER = "over"
HELP = "help"

state = MENU

# ================= SKINS =================
skins = [
    ("Gold Fish", (255, 190, 20), 0),
    ("Ocean Fish", (40, 220, 160), 30),
    ("Purple Fish", (190, 80, 255), 60),
    ("Fire Fish", (255, 90, 40), 100)
]

selected = 0

# ================= PLAYER =================
player = {
    "x": W // 2,
    "y": H // 2,
    "size": 25,
    "speed": 5,
    "color": skins[0][1]
}

score = 0
lives = 3
level = 1
shield = 0
boost = 0
dash_timer = 0
dash_cooldown = 0
damage_timer = 0
boss_hp = 100
boss = None
boss_defeated = False
mission_rewarded = False

# ================= BACKGROUND =================
bubbles = [
    [random.randint(0, W), random.randint(0, H),
     random.randint(3, 8), random.uniform(0.5, 2)]
    for _ in range(50)
]

wave = 0

def draw_background():
    global wave
    wave += 0.03

    screen.fill((5, 35, 100))

    # Ocean gradient
    for y in range(H):
        shade = int(35 + y * 0.13)
        pygame.draw.line(
            screen,
            (5, min(shade, 125), min(shade + 65, 210)),
            (0, y), (W, y)
        )

    # Moving sunlight
    for i in range(4):
        x = int(150 + i * 250 + math.sin(wave + i) * 35)
        pygame.draw.polygon(
            screen, (12, 90, 145),
            [(x, 0), (x + 60, 0),
             (x + 180, H - 30), (x + 110, H - 30)]
        )

    # Ocean floor
    pygame.draw.rect(screen, (160, 125, 65), (0, H-25, W, 25))

    # Animated plants
    for x in range(40, W, 110):
        bend = math.sin(wave + x) * 8
        pygame.draw.line(
            screen, GREEN,
            (x, H-25), (x + 15 + bend, H-100), 5
        )
        pygame.draw.line(
            screen, (30, 170, 90),
            (x, H-25), (x - 15 - bend, H-80), 5
        )

    # Bubbles
    for b in bubbles:
        pygame.draw.circle(
            screen, (190, 230, 255),
            (int(b[0]), int(b[1])), b[2], 1
        )
        b[1] -= b[3]

        if b[1] < 0:
            b[1] = H
            b[0] = random.randint(0, W)

# ================= TEXT =================
def write(text, x, y, color=WHITE, style="normal"):
    f = big if style == "big" else medium if style == "medium" else font
    img = f.render(str(text), True, color)
    screen.blit(img, (x, y))

# ================= BUTTON =================
def button(text, x, y, w, h):
    rect = pygame.Rect(x, y, w, h)
    mouse = pygame.mouse.get_pos()

    color = (40, 180, 220) if rect.collidepoint(mouse) else (20, 100, 175)

    pygame.draw.rect(screen, color, rect, border_radius=13)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=13)

    label = font.render(text, True, WHITE)
    screen.blit(
        label,
        (x + (w-label.get_width())//2,
         y + (h-label.get_height())//2)
    )
    return rect

# ================= FISH DRAWING =================
def draw_fish(x, y, size, color, direction=1):
    x, y = int(x), int(y)

    # Tail
    pygame.draw.polygon(
        screen, color,
        [
            (x-direction*size, y),
            (x-direction*size*1.8, y-size),
            (x-direction*size*1.8, y+size)
        ]
    )

    # Body
    pygame.draw.ellipse(
        screen, color,
        (x-size, y-size//2, size*2, size)
    )

    # Fin
    pygame.draw.polygon(
        screen, color,
        [(x-5, y-5), (x+5, y-size), (x+15, y-5)]
    )

    # Eye
    pygame.draw.circle(
        screen, WHITE,
        (x+direction*size//2, y-4), 5
    )
    pygame.draw.circle(
        screen, BLACK,
        (x+direction*size//2+1, y-4), 2
    )

# ================= SMALL FISH =================
class SmallFish:
    def __init__(self):
        self.size = random.randint(10, 20)
        self.x = random.randint(0, W)
        self.y = random.randint(80, H-70)
        self.speed = random.uniform(1, 2.5)
        self.direction = random.choice([-1, 1])
        self.color = random.choice([
            GOLD, RED, GREEN, CYAN, PURPLE
        ])
        self.phase = random.random() * 6

    def move(self):
        self.x += self.speed * self.direction
        self.y += math.sin(wave + self.phase) * 0.5

        if self.x < -80 or self.x > W+80:
            self.direction *= -1

    def draw(self):
        draw_fish(
            self.x, self.y, self.size,
            self.color, self.direction
        )

# ================= ENEMY =================
class Enemy:
    def __init__(self):
        self.size = random.randint(30, 42)
        self.x = random.choice([-60, W+60])
        self.y = random.randint(100, H-100)
        self.speed = random.uniform(1, 1.8)
        self.color = RED

    def move(self):
        dx = player["x"] - self.x
        dy = player["y"] - self.y
        distance = max(1, math.hypot(dx, dy))

        self.x += dx / distance * self.speed
        self.y += dy / distance * self.speed

    def draw(self):
        direction = 1 if player["x"] < self.x else -1
        draw_fish(self.x, self.y, self.size, self.color, direction)

# ================= BOSS =================
class Boss:
    def __init__(self):
        self.x = W - 100
        self.y = H // 2
        self.size = 70
        self.hp = 100
        self.speed = 1.4
        self.phase = 0

    def move(self):
        self.phase += 0.04

        dx = player["x"] - self.x
        dy = player["y"] - self.y
        distance = max(1, math.hypot(dx, dy))

        self.x += dx / distance * self.speed
        self.y += dy / distance * self.speed

        self.y += math.sin(self.phase) * 1.2

    def draw(self):
        draw_fish(self.x, self.y, self.size, (120, 145, 165), -1)

        # Boss health bar
        pygame.draw.rect(screen, BLACK, (330, 20, 340, 24))
        pygame.draw.rect(screen, RED, (330, 20, 340, 24), 2)

        health_width = max(0, int(336 * self.hp / 100))
        pygame.draw.rect(
            screen, GREEN,
            (332, 22, health_width, 20)
        )

        write("BOSS SHARK", 405, 48, WHITE)

# ================= WORLD =================
fishes = []
enemies = []
coins = []
powerups = []

def new_coin():
    return {
        "x": random.randint(40, W-40),
        "y": random.randint(80, H-80)
    }

def create_world():
    global fishes, enemies, coins, powerups
    global boss, boss_hp, boss_defeated

    fishes = [SmallFish() for _ in range(18)]
    enemies = [Enemy() for _ in range(2)]
    coins = [new_coin() for _ in range(5)]
    powerups = []

    boss = None
    boss_hp = 100
    boss_defeated = False

def reset_game():
    global score, lives, level
    global shield, boost, dash_timer
    global dash_cooldown, damage_timer
    global state, mission_rewarded

    score = 0
    lives = 3
    level = 1
    shield = 0
    boost = 0
    dash_timer = 0
    dash_cooldown = 0
    damage_timer = 0
    mission_rewarded = False

    player["x"] = W//2
    player["y"] = H//2
    player["size"] = 25
    player["color"] = skins[selected][1]

    create_world()
    state = PLAY

# ================= POWERUPS =================
def spawn_powerup():
    powerups.append({
        "x": random.randint(50, W-50),
        "y": random.randint(80, H-80),
        "type": random.choice(["shield", "boost"])
    })

# ================= PLAYER DAMAGE =================
def damage_player():
    global lives, damage_timer, state

    if damage_timer == 0 and shield == 0:
        lives -= 1
        damage_timer = 100

        if lives <= 0:
            state = OVER

# ================= GAME LOOP =================
running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            save_game()
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                if state == PLAY:
                    state = PAUSE
                elif state == PAUSE:
                    state = PLAY

            if event.key == pygame.K_p and state == PAUSE:
                state = PLAY

            if event.key == pygame.K_r and state == OVER:
                reset_game()

            # DASH
            if event.key == pygame.K_SPACE and state == PLAY:
                if dash_cooldown == 0:
                    dash_timer = 12
                    dash_cooldown = 100

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if state == MENU:

                if pygame.Rect(390, 245, 220, 55).collidepoint(mx, my):
                    state = SELECT

                elif pygame.Rect(390, 315, 220, 55).collidepoint(mx, my):
                    state = SHOP

                elif pygame.Rect(390, 385, 220, 55).collidepoint(mx, my):
                    state = HELP

                elif pygame.Rect(390, 455, 220, 55).collidepoint(mx, my):
                    running = False

            elif state == SELECT:

                for i in range(4):
                    rect = pygame.Rect(150+i*180, 260, 130, 120)
                    if rect.collidepoint(mx, my):
                        if i in data["unlocked"]:
                            selected = i

                if pygame.Rect(390, 460, 220, 55).collidepoint(mx, my):
                    reset_game()

            elif state == SHOP:

                for i in range(4):
                    rect = pygame.Rect(145+i*180, 270, 140, 140)

                    if rect.collidepoint(mx, my):
                        if i not in data["unlocked"]:
                            price = skins[i][2]

                            if data["coins"] >= price:
                                data["coins"] -= price
                                data["unlocked"].append(i)
                                selected = i
                                save_game()
                        else:
                            selected = i
                            save_game()

                if pygame.Rect(390, 490, 220, 55).collidepoint(mx, my):
                    state = MENU

            elif state == HELP:
                state = MENU

            elif state == PAUSE:

                if pygame.Rect(390, 300, 220, 55).collidepoint(mx, my):
                    state = PLAY

                elif pygame.Rect(390, 375, 220, 55).collidepoint(mx, my):
                    state = MENU

            elif state == OVER:

                if pygame.Rect(390, 420, 220, 55).collidepoint(mx, my):
                    reset_game()

                elif pygame.Rect(390, 490, 220, 55).collidepoint(mx, my):
                    state = MENU

    draw_background()

    # ================= MENU =================
    if state == MENU:

        write("FISH WORLD V4", 270, 100, GOLD, "big")
        write("ULTIMATE OCEAN SURVIVAL", 330, 180, CYAN)

        button("PLAY GAME", 390, 245, 220, 55)
        button("FISH SHOP", 390, 315, 220, 55)
        button("HOW TO PLAY", 390, 385, 220, 55)
        button("EXIT", 390, 455, 220, 55)

        write("Coins: "+str(data["coins"]), 20, 20, GOLD)
        write("High Score: "+str(data["high_score"]), 20, 55)

        draw_fish(150, 400, 40, GOLD)
        draw_fish(820, 430, 50, CYAN)

    # ================= SELECT FISH =================
    elif state == SELECT:

        write("SELECT YOUR FISH", 340, 140, GOLD, "medium")

        for i, skin in enumerate(skins):
            x = 150+i*180

            rect = pygame.Rect(x, 260, 130, 120)
            color = GREEN if selected == i else BLUE

            pygame.draw.rect(screen, color, rect, border_radius=15)
            draw_fish(x+65, 305, 27, skin[1])

            write(skin[0], x-5, 390)

            if i in data["unlocked"]:
                write("UNLOCKED", x+10, 420, GREEN)
            else:
                write("LOCKED", x+15, 420, RED)

        button("START GAME", 390, 460, 220, 55)

    # ================= SHOP =================
    elif state == SHOP:

        write("FISH SHOP", 365, 120, GOLD, "big")
        write("Coins: "+str(data["coins"]), 410, 210, GOLD)

        for i, skin in enumerate(skins):
            x = 145+i*180

            rect = pygame.Rect(x, 270, 140, 140)
            pygame.draw.rect(screen, BLUE, rect, border_radius=15)

            draw_fish(x+70, 305, 27, skin[1])
            write(skin[0], x+5, 350)

            if i in data["unlocked"]:
                write("OWNED", x+25, 385, GREEN)
            else:
                write(str(skin[2])+" COINS", x+15, 385, GOLD)

        button("BACK", 390, 490, 220, 55)

    # ================= HELP =================
    elif state == HELP:

        write("HOW TO PLAY", 340, 100, GOLD, "big")

        instructions = [
            "WASD / Arrow Keys = Move",
            "SPACE = Dash ability",
            "Eat smaller fish to grow",
            "Avoid larger enemy fish",
            "Collect coins for new skins",
            "Blue powerup = Shield",
            "Green powerup = Speed boost",
            "Level 4 = Boss Shark battle",
            "ESC = Pause | P = Resume"
        ]

        for i, line in enumerate(instructions):
            write(line, 250, 200+i*43)

        button("BACK TO MENU", 390, 590, 220, 50)

    # ================= GAMEPLAY =================
    elif state == PLAY:

        keys = pygame.key.get_pressed()

        speed = player["speed"] + (3 if boost > 0 else 0)

        if dash_timer > 0:
            speed = 12
            dash_timer -= 1

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player["x"] -= speed

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player["x"] += speed

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player["y"] -= speed

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player["y"] += speed

        player["x"] = max(
            player["size"],
            min(W-player["size"], player["x"])
        )

        player["y"] = max(
            player["size"],
            min(H-player["size"], player["y"])
        )

        if boost > 0:
            boost -= 1

        if shield > 0:
            shield -= 1

        if damage_timer > 0:
            damage_timer -= 1

        if dash_cooldown > 0:
            dash_cooldown -= 1

        level = min(5, 1+score//100)

        # SMALL FISH
        for fish in fishes[:]:
            fish.move()
            fish.draw()

            distance = math.hypot(
                player["x"]-fish.x,
                player["y"]-fish.y
            )

            if distance < player["size"]+fish.size:

                if player["size"] > fish.size:
                    score += 10
                    player["size"] = min(70, player["size"]+2)

                    fishes.remove(fish)
                    fishes.append(SmallFish())

        # COINS
        for coin in coins[:]:

            pygame.draw.circle(
                screen, GOLD,
                (coin["x"], coin["y"]), 13
            )

            pygame.draw.circle(
                screen, WHITE,
                (coin["x"], coin["y"]), 13, 2
            )

            distance = math.hypot(
                player["x"]-coin["x"],
                player["y"]-coin["y"]
            )

            if distance < player["size"]+13:
                data["coins"] += 5
                coins.remove(coin)
                coins.append(new_coin())
                save_game()

        # POWERUPS
        if random.random() < 0.002 and len(powerups) < 2:
            spawn_powerup()

        for power in powerups[:]:

            color = CYAN if power["type"] == "shield" else GREEN

            pygame.draw.circle(
                screen, color,
                (power["x"], power["y"]), 18
            )

            distance = math.hypot(
                player["x"]-power["x"],
                player["y"]-power["y"]
            )

            if distance < player["size"]+18:

                if power["type"] == "shield":
                    shield = 300
                else:
                    boost = 300

                powerups.remove(power)

        # ENEMIES
        for enemy in enemies[:]:
            enemy.speed = 1.2+level*0.15
            enemy.move()
            enemy.draw()

            distance = math.hypot(
                player["x"]-enemy.x,
                player["y"]-enemy.y
            )

            if distance < player["size"]+enemy.size:

                if player["size"] > enemy.size and not dash_timer:
                    score += 20
                    enemies.remove(enemy)
                    enemies.append(Enemy())
                else:
                    damage_player()

        # BOSS SPAWN
        if level >= 4 and boss is None and not boss_defeated:
            boss = Boss()

        # BOSS BATTLE
        if boss is not None:

            boss.move()
            boss.draw()

            distance = math.hypot(
                player["x"]-boss.x,
                player["y"]-boss.y
            )

            # Dash collision damages boss
            if distance < player["size"]+boss.size and dash_timer > 0:
                boss.hp -= 2

            elif distance < player["size"]+boss.size:
                damage_player()

            if boss.hp <= 0:
                score += 100
                data["coins"] += 50
                boss = None
                boss_defeated = True
                save_game()

        # MISSION
        if score >= 200 and not mission_rewarded:
            mission_rewarded = True
            data["coins"] += 25
            save_game()

        # PLAYER
        if damage_timer == 0 or damage_timer % 10 < 5:
            draw_fish(
                player["x"], player["y"],
                player["size"], player["color"]
            )

        if shield > 0:
            pygame.draw.circle(
                screen, CYAN,
                (int(player["x"]), int(player["y"])),
                player["size"]+13, 3
            )

        # HUD
        write("Score: "+str(score), 15, 12)
        write("Level: "+str(level), 15, 45)
        write("Lives: "+str(lives), 15, 78, RED)
        write("Coins: "+str(data["coins"]), 15, 111, GOLD)
        write("High: "+str(data["high_score"]), 15, 144, GOLD)

        if dash_cooldown == 0:
            write("DASH READY", 790, 15, GREEN)
        else:
            write("DASH: "+str(dash_cooldown//60+1), 790, 15)

        if shield > 0:
            write("SHIELD ACTIVE", 790, 50, CYAN)

        if boost > 0:
            write("SPEED BOOST", 790, 85, GREEN)

        if score > data["high_score"]:
            data["high_score"] = score
            save_game()

    # ================= PAUSE =================
    elif state == PAUSE:

        write("GAME PAUSED", 320, 180, GOLD, "big")
        button("RESUME", 390, 300, 220, 55)
        button("MAIN MENU", 390, 375, 220, 55)

    # ================= GAME OVER =================
    elif state == OVER:

        write("GAME OVER!", 330, 170, RED, "big")
        write("Score: "+str(score), 410, 275)
        write("High Score: "+str(data["high_score"]), 370, 320, GOLD)
        write("Coins: "+str(data["coins"]), 410, 365, GOLD)

        button("RESTART", 390, 420, 220, 55)
        button("MAIN MENU", 390, 490, 220, 55)

    pygame.display.flip()

save_game()
pygame.quit()
sys.exit()
