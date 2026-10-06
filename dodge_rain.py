
import random
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodge Rain - Giết thời gian")
clock = pygame.time.Clock()

font_big = pygame.font.Font(None, 64)
font = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 26)

PLAYER_W, PLAYER_H = 48, 48
PLAYER_SPEED = 7

def reset_game():
    player = pygame.Rect(
        WIDTH // 2 - PLAYER_W // 2,
        HEIGHT - 80,
        PLAYER_W,
        PLAYER_H,
    )
    obstacles = []
    score = 0.0
    spawn_timer = 0
    game_over = False
    return player, obstacles, score, spawn_timer, game_over

player, obstacles, score, spawn_timer, game_over = reset_game()
best_score = 0.0

running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_r and game_over:
                player, obstacles, score, spawn_timer, game_over = reset_game()

    keys = pygame.key.get_pressed()

    if not game_over:
        # Di chuyển người chơi
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += PLAYER_SPEED

        player.x += dx
        player.y += dy

        player.clamp_ip(screen.get_rect())

        # Điểm tăng theo thời gian sống
        score += dt

        # Càng sống lâu, vật cản càng nhanh và xuất hiện dày hơn
        difficulty = 1.0 + score / 20.0
        spawn_interval = max(0.16, 0.55 - score / 250.0)

        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0

            size = random.randint(18, 45)
            x = random.randint(0, WIDTH - size)

            obstacle = {
                "rect": pygame.Rect(x, -size, size, size),
                "speed": random.uniform(220, 330) * difficulty,
            }
            obstacles.append(obstacle)

        # Di chuyển vật cản
        for obstacle in obstacles[:]:
            obstacle["rect"].y += int(obstacle["speed"] * dt)

            if obstacle["rect"].top > HEIGHT:
                obstacles.remove(obstacle)
                continue

            if player.colliderect(obstacle["rect"]):
                game_over = True
                best_score = max(best_score, score)

    # ---------------- DRAW ----------------
    screen.fill((18, 20, 28))

    # Lưới nền
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (30, 33, 43), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (30, 33, 43), (0, y), (WIDTH, y))

    # Người chơi
    pygame.draw.rect(screen, (80, 210, 150), player, border_radius=10)

    # Mắt nhỏ cho vui
    pygame.draw.circle(screen, (18, 20, 28), (player.x + 15, player.y + 17), 4)
    pygame.draw.circle(screen, (18, 20, 28), (player.x + 33, player.y + 17), 4)

    # Vật cản
    for obstacle in obstacles:
        pygame.draw.rect(
            screen,
            (235, 90, 90),
            obstacle["rect"],
            border_radius=6,
        )

    score_text = font.render(f"Điểm: {int(score)}", True, (240, 240, 240))
    screen.blit(score_text, (20, 18))

    best_text = font_small.render(
        f"Kỷ lục: {int(best_score)}",
        True,
        (190, 195, 205),
    )
    screen.blit(best_text, (20, 58))

    help_text = font_small.render(
        "WASD / Phím mũi tên để di chuyển • ESC để thoát",
        True,
        (150, 155, 170),
    )
    screen.blit(help_text, (WIDTH - help_text.get_width() - 20, 22))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        title = font_big.render("GAME OVER", True, (245, 245, 245))
        final_score = font.render(
            f"Bạn sống được {int(score)} giây",
            True,
            (230, 230, 230),
        )
        restart = font_small.render(
            "Nhấn R để chơi lại • ESC để thoát",
            True,
            (190, 195, 205),
        )

        screen.blit(
            title,
            (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 90),
        )
        screen.blit(
            final_score,
            (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2 - 20),
        )
        screen.blit(
            restart,
            (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 35),
        )

    pygame.display.flip()

pygame.quit()
sys.exit()
