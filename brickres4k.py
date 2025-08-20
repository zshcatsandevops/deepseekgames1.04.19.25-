import pygame
import random
import math
import sys

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PS1 Breakout")

# Colors - PS1 limited palette
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (180, 180, 180)
WHITE = (200, 200, 200)
RED = (180, 30, 30)
BLUE = (30, 60, 180)
GREEN = (30, 180, 30)
YELLOW = (180, 180, 30)
PURPLE = (180, 30, 180)

# PS1-style sound effects
def create_beep_sound(freq, duration):
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate))
    buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
    max_sample = 2**(16 - 1) - 1
    for s in range(n_samples):
        t = float(s) / sample_rate
        buf[s][0] = int(max_sample * math.sin(2 * math.pi * freq * t) * 0.2)  # Left channel
        buf[s][1] = int(max_sample * math.sin(2 * math.pi * freq * t) * 0.2)  # Right channel
    return pygame.sndarray.make_sound(buf)

try:
    import numpy
    hit_sound = create_beep_sound(440, 0.1)
    brick_sound = create_beep_sound(880, 0.1)
    wall_sound = create_beep_sound(220, 0.1)
    lose_sound = create_beep_sound(110, 0.5)
except ImportError:
    # Fallback if numpy is not available
    hit_sound = wall_sound = brick_sound = lose_sound = None

# Game objects
class Paddle:
    def __init__(self):
        self.width = 80
        self.height = 15
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 30
        self.speed = 6
        self.color = LIGHT_GRAY
        
    def draw(self):
        # PS1-style low poly paddle
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Add some polygon edges for that PS1 look
        pygame.draw.polygon(screen, WHITE, [
            (self.x, self.y), 
            (self.x + self.width, self.y),
            (self.x + self.width - 5, self.y + 5),
            (self.x + 5, self.y + 5)
        ])
        pygame.draw.polygon(screen, DARK_GRAY, [
            (self.x, self.y + self.height), 
            (self.x + self.width, self.y + self.height),
            (self.x + self.width - 5, self.y + self.height - 5),
            (self.x + 5, self.y + self.height - 5)
        ])
        
    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < WIDTH - self.width:
            self.x += self.speed

class Ball:
    def __init__(self):
        self.radius = 8
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = -4
        self.color = WHITE
        
    def draw(self):
        # PS1-style low poly ball (actually just a low-res circle)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # Add a "highlight" for that PS1 look
        pygame.draw.circle(screen, LIGHT_GRAY, (int(self.x - self.radius//3), int(self.y - self.radius//3)), self.radius//3)
        
    def move(self):
        self.x += self.dx
        self.y += self.dy
        
        # Wall collisions
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.dx *= -1
            if wall_sound:
                wall_sound.play()
        if self.y <= self.radius:
            self.dy *= -1
            if wall_sound:
                wall_sound.play()
                
    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = -4

class Brick:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.visible = True
        
    def draw(self):
        if not self.visible:
            return
            
        # PS1-style low poly brick
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Add some polygon edges for that PS1 look
        pygame.draw.polygon(screen, tuple(min(c + 40, 255) for c in self.color), [
            (self.x, self.y), 
            (self.x + self.width, self.y),
            (self.x + self.width - 3, self.y + 3),
            (self.x + 3, self.y + 3)
        ])
        pygame.draw.polygon(screen, tuple(max(c - 40, 0) for c in self.color), [
            (self.x, self.y + self.height), 
            (self.x + self.width, self.y + self.height),
            (self.x + self.width - 3, self.y + self.height - 3),
            (self.x + 3, self.y + self.height - 3)
        ])

# Create game objects
paddle = Paddle()
ball = Ball()

# Create bricks
bricks = []
brick_width = 50
brick_height = 20
brick_colors = [RED, BLUE, GREEN, YELLOW, PURPLE]

for row in range(5):
    for col in range(WIDTH // brick_width):
        if col % 5 < len(brick_colors):
            color = brick_colors[col % 5]
            bricks.append(Brick(col * brick_width, row * brick_height + 50, brick_width, brick_height, color))

# Game state
score = 0
lives = 3
game_over = False
font = pygame.font.SysFont('Arial', 24, bold=True)

# PS1-style vertex wobble effect
def apply_ps1_effect(surface):
    wobble_intensity = 0.7
    for _ in range(10):  # Add some random "wobble" lines for that PS1 look
        x1 = random.randint(0, WIDTH)
        y1 = random.randint(0, HEIGHT)
        x2 = x1 + random.randint(-10, 10)
        y2 = y1 + random.randint(-10, 10)
        pygame.draw.line(surface, DARK_GRAY, (x1, y1), (x2, y2), 1)

# Main game loop
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                # Reset game
                paddle = Paddle()
                ball = Ball()
                for brick in bricks:
                    brick.visible = True
                score = 0
                lives = 3
                game_over = False
    
    if not game_over:
        # Move paddle with keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move("left")
        if keys[pygame.K_RIGHT]:
            paddle.move("right")
            
        # Move ball
        ball.move()
        
        # Ball-paddle collision
        if (ball.y + ball.radius >= paddle.y and 
            ball.x >= paddle.x and 
            ball.x <= paddle.x + paddle.width and
            ball.dy > 0):
            
            # Adjust ball direction based on where it hit the paddle
            relative_x = (ball.x - paddle.x) / paddle.width
            angle = relative_x * math.pi - math.pi/2
            ball.dx = 5 * math.cos(angle)
            ball.dy = -abs(ball.dy)
            if hit_sound:
                hit_sound.play()
        
        # Ball-brick collision
        for brick in bricks:
            if (brick.visible and 
                ball.x >= brick.x and 
                ball.x <= brick.x + brick.width and
                ball.y - ball.radius <= brick.y + brick.height and
                ball.y + ball.radius >= brick.y):
                
                brick.visible = False
                ball.dy *= -1
                score += 10
                if brick_sound:
                    brick_sound.play()
        
        # Ball out of bounds
        if ball.y > HEIGHT:
            lives -= 1
            if lose_sound:
                lose_sound.play()
            if lives <= 0:
                game_over = True
            else:
                ball.reset()
        
        # Check win condition
        if all(not brick.visible for brick in bricks):
            game_over = True
    
    # Clear screen with PS1-style dark background
    screen.fill(BLACK)
    
    # Draw a grid for that PS1 look
    for x in range(0, WIDTH, 20):
        pygame.draw.line(screen, DARK_GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 20):
        pygame.draw.line(screen, DARK_GRAY, (0, y), (WIDTH, y), 1)
    
    # Draw game objects
    for brick in bricks:
        brick.draw()
    paddle.draw()
    ball.draw()
    
    # Draw score and lives
    score_text = font.render(f"SCORE: {score}", True, WHITE)
    lives_text = font.render(f"LIVES: {lives}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (WIDTH - 100, 10))
    
    # Draw game over message
    if game_over:
        if all(not brick.visible for brick in bricks):
            message = "YOU WIN! PRESS R TO RESTART"
        else:
            message = "GAME OVER! PRESS R TO RESTART"
        game_over_text = font.render(message, True, WHITE)
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2))
    
    # Apply PS1-style vertex wobble effect
    apply_ps1_effect(screen)
    
    # Update display
    pygame.display.flip()
    clock.tick(60)
