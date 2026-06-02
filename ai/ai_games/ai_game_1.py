import pygame
import sys
import random

# 1. 初始化 Pygame
pygame.init()

# 2. 遊戲常數定義
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "AI Space Shooter"
FPS = 60

# 顏色定義 (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# 創建螢幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# 3. 玩家類別 (Player Class)
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 替換為您自己的圖片，這裡用一個簡單的矩形代替
        self.image = pygame.Surface([50, 50])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        
        # 核心屬性：生命值
        self.health = 100
        self.max_health = 100
        self.movement_speed = 7

    def update(self):
        # 處理鍵盤移動輸入
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.movement_speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.movement_speed

        # 處理滑鼠水平移動 (自動跟隨滑鼠 X 座標)
        mouse_x, _ = pygame.mouse.get_pos()
        self.rect.centerx = mouse_x
        
        # 限制玩家在螢幕邊界內移動
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def take_damage(self, damage):
        """接收傷害的函數，並確保生命值不會超過 0"""
        self.health -= damage
        if self.health < 0:
            self.health = 0
        print(f"玩家受到 {damage} 點傷害。剩餘生命值: {self.health}")
        # 可以在這裡加入閃爍效果或擊退效果

    def draw_health_bar(self, surface):
        """在螢幕上繪製生命值條"""
        bar_width = 150
        bar_height = 20
        # 定位在螢幕頂部中央
        x = SCREEN_WIDTH // 2 - bar_width // 2
        y = 20
        
        # 繪製背景 (最大生命值)
        pygame.draw.rect(surface, RED, (x, y, bar_width, bar_height), 2)
        
        # 繪製當前生命值
        current_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(surface, GREEN, (x, y, current_width, bar_height))

# 子彈類別
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([6, 15])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -12

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# 4. 遊戲實例化
player = Player()

# 遊戲組件組件
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

# 子彈群組
bullets = pygame.sprite.Group()

# 5. 主遊戲循環 (Main Game Loop)
running = True
game_over = False

while running:
    # 控制遊戲速度
    clock.tick(FPS)

    # --- 事件處理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 範例：當按下 'D' 鍵時，模擬受到傷害
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d and not game_over:
                player.take_damage(20) # 模擬受到 20 點傷害
            
            # 範例：如果遊戲結束，按 'R' 鍵重啟
            if event.key == pygame.K_r and game_over:
                # 重新啟動遊戲 (這裡需要更完整的重置邏輯)
                pygame.quit()
                pygame.init()
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                player = Player()
                all_sprites.empty()
                all_sprites.add(player)
                bullets.empty()
                game_over = False

        # 滑鼠左鍵發射子彈
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
            bullet = Bullet(player.rect.centerx, player.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)


    if not game_over:
        # --- 更新遊戲狀態 ---
        all_sprites.update()

        # 模擬敵機的攻擊 (為了測試傷害系統，我們每隔幾幀觸發一次)
        if random.randint(1, FPS) == 1:
            player.take_damage(5) # 隨機受到小傷害

        # 檢查遊戲是否結束
        if player.health <= 0:
            game_over = True
            print("=== GAME OVER ===")

    # --- 繪製畫面 ---
    screen.fill(BLACK) # 清空背景
    
    # 繪製所有圖層
    all_sprites.draw(screen)
    
    # 繪製玩家的生命值條 (必須在繪製所有元素之後)
    player.draw_health_bar(screen)

    # 繪製遊戲狀態提示
    if game_over:
        font = pygame.font.Font(None, 74)
        text = font.render("GAME OVER", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(text, text_rect)
        
        font_small = pygame.font.Font(None, 36)
        restart_text = font_small.render("Press 'R' key cont", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
        screen.blit(restart_text, restart_rect)


    # 更新整個螢幕
    pygame.display.flip()

# 退出遊戲
pygame.quit()
sys.exit()