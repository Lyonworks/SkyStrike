
# -*- coding: utf-8 -*-
"""
Plane Battle - Pygbag Web Edition
@author: Lyon
"""

import asyncio
import random
import pygame
from pygame.locals import *
from gameRole import *

# Dark blue theme
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (230, 240, 255)

pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=2048
)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SkyStrike")

clock = pygame.time.Clock()

# Audio
def load_sound(path, volume=0.3):
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        return sound
    except (pygame.error, FileNotFoundError):
        return None

bullet_sound = load_sound("resources/sound/bullet.wav")
enemy1_down_sound = load_sound("resources/sound/enemy1_down.wav")
game_over_sound = load_sound("resources/sound/game_over.wav")

try:
    pygame.mixer.music.load("resources/sound/game_music.wav")
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
except (pygame.error, FileNotFoundError):
    pass

# Images
background = pygame.image.load(
    "resources/image/background.png"
).convert()

game_over_img = pygame.image.load(
    "resources/image/gameover.png"
).convert_alpha()

plane_img = pygame.image.load(
    "resources/image/shoot.png"
).convert_alpha()

bullet_img = plane_img.subsurface(
    pygame.Rect(1004, 987, 9, 21)
).copy()

enemy1_rect = pygame.Rect(534, 612, 57, 43)
enemy1_img = plane_img.subsurface(enemy1_rect).copy()

enemy1_down_imgs = [
    plane_img.subsurface(pygame.Rect(267, 347, 57, 43)).copy(),
    plane_img.subsurface(pygame.Rect(873, 697, 57, 43)).copy(),
    plane_img.subsurface(pygame.Rect(267, 296, 57, 43)).copy(),
    plane_img.subsurface(pygame.Rect(930, 697, 57, 43)).copy(),
]

score_font = pygame.font.Font(None, 36)
final_font = pygame.font.Font(None, 48)
button_font = pygame.font.Font(None, 40)

button_rect = pygame.Rect(0, 0, 200, 56)
button_rect.center = (
    SCREEN_WIDTH // 2,
    SCREEN_HEIGHT // 2 + 110
)


def create_player():
    player_rects = [
        pygame.Rect(0, 99, 102, 126),
        pygame.Rect(165, 360, 102, 126),
        pygame.Rect(165, 234, 102, 126),
        pygame.Rect(330, 624, 102, 126),
        pygame.Rect(330, 498, 102, 126),
        pygame.Rect(432, 624, 102, 126),
    ]

    return Player(plane_img, player_rects, [200, 600])


def play_sound(sound):
    if sound is not None:
        sound.play()


async def run_game():
    player = create_player()
    enemies = pygame.sprite.Group()
    enemies_down = pygame.sprite.Group()

    shoot_frequency = 0
    enemy_frequency = 0
    player_down_index = 16
    score = 0

    running = True

    while running:
        # Process browser/window events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        # Shooting
        if not player.is_hit:
            if shoot_frequency % 15 == 0:
                play_sound(bullet_sound)
                player.shoot(bullet_img)

            shoot_frequency = (shoot_frequency + 1) % 15

        # Spawn enemies
        if enemy_frequency % 50 == 0:
            enemy_pos = [
                random.randint(0, SCREEN_WIDTH - enemy1_rect.width),
                0
            ]
            enemies.add(
                Enemy(enemy1_img, enemy1_down_imgs, enemy_pos)
            )

        enemy_frequency = (enemy_frequency + 1) % 100

        # Move bullets safely
        for bullet in list(player.bullets):
            bullet.move()
            if bullet.rect.bottom < 0:
                player.bullets.remove(bullet)

        # Move enemies and detect collisions
        for enemy in list(enemies):
            enemy.move()

            if pygame.sprite.collide_circle(enemy, player):
                enemies_down.add(enemy)
                enemies.remove(enemy)
                player.is_hit = True
                play_sound(game_over_sound)
                break

            if enemy.rect.top > SCREEN_HEIGHT:
                enemies.remove(enemy)

        # Bullet/enemy collisions
        hits = pygame.sprite.groupcollide(
            enemies, player.bullets, True, True
        )

        for enemy in hits:
            enemies_down.add(enemy)

        # Background
        screen.fill(BLACK)
        screen.blit(background, (0, 0))

        # Player animation
        if not player.is_hit:
            player.img_index = min(shoot_frequency // 8, 1)
            screen.blit(player.image[player.img_index], player.rect)
        else:
            player.img_index = min(player_down_index // 8, 5)
            screen.blit(player.image[player.img_index], player.rect)

            player_down_index += 1

            if player_down_index > 47:
                running = False

        # Enemy explosions
        for enemy in list(enemies_down):
            if enemy.down_index == 0:
                play_sound(enemy1_down_sound)

            if enemy.down_index > 7:
                enemies_down.remove(enemy)
                score += 1
                continue

            screen.blit(
                enemy.down_imgs[enemy.down_index // 2],
                enemy.rect
            )
            enemy.down_index += 1

        # Draw sprites
        player.bullets.draw(screen)
        enemies.draw(screen)

        score_text = score_font.render(
            f"Score: {score}", True, WHITE
        )
        screen.blit(score_text, (10, 10))

        pygame.display.flip()

        # Keyboard controls
        keys = pygame.key.get_pressed()

        if not player.is_hit:
            if keys[K_w] or keys[K_UP]:
                player.moveUp()
            if keys[K_s] or keys[K_DOWN]:
                player.moveDown()
            if keys[K_a] or keys[K_LEFT]:
                player.moveLeft()
            if keys[K_d] or keys[K_RIGHT]:
                player.moveRight()

        clock.tick(45)

        # Essential: yield control back to the browser
        await asyncio.sleep(0)

    return score


def draw_button(hovered):
    fill = BLUE if hovered else BLACK
    text_color = BLACK if hovered else WHITE

    pygame.draw.rect(
        screen, fill, button_rect, border_radius=8
    )
    pygame.draw.rect(
        screen, BLUE, button_rect, 3, border_radius=8
    )

    label = button_font.render(
        "Play Again", True, text_color
    )
    screen.blit(label, label.get_rect(center=button_rect.center))


async def show_game_over(score):
    snapshot = screen.copy()

    score_text = final_font.render(
        f"Score: {score}", True, WHITE
    )
    score_rect = score_text.get_rect(
        centerx=SCREEN_WIDTH // 2,
        centery=SCREEN_HEIGHT // 2 + 24
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    return True

            if event.type == pygame.KEYDOWN:
                if event.key in (
                    K_RETURN, K_KP_ENTER, K_SPACE, K_r
                ):
                    return True

        screen.blit(snapshot, (0, 0))
        screen.blit(game_over_img, (0, 0))
        screen.blit(score_text, score_rect)

        draw_button(
            button_rect.collidepoint(pygame.mouse.get_pos())
        )

        pygame.display.flip()
        clock.tick(30)

        # Essential for Pygbag
        await asyncio.sleep(0)


async def main():
    try:
        while True:
            final_score = await run_game()

            if final_score is None:
                break

            play_again = await show_game_over(final_score)

            if not play_again:
                break
    finally:
        pygame.quit()


asyncio.run(main())
