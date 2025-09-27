import tkinter as tk
import random
import math
import os

# -----------------
# Game Settings
# -----------------
PLAYER_SPEED = 8
BULLET_SPEED = 15
ENEMY_SPEED = 2
PLAYER_HEALTH = 100
GRAVITY = 1
JUMP_STRENGTH = -18
GROUND_Y = 500
LEVEL_LENGTH = 5000

def safe_load_image(filename, width=40, height=40, color="red"):
    """Try to load image, else create colored placeholder."""
    if os.path.exists(filename):
        try:
            return tk.PhotoImage(file=filename)
        except Exception:
            pass
    # fallback
    img = tk.PhotoImage(width=width, height=height)
    img.put(color, to=(0, 0, width, height))
    return img

class SideScrollerGame:
    def __init__(self, root):
        self.root = root
        self.width = root.winfo_screenwidth()
        self.height = root.winfo_screenheight()
        self.root.attributes("-fullscreen", True)

        # Canvas
        self.canvas = tk.Canvas(root, bg="skyblue", width=self.width, height=self.height)
        self.canvas.pack(fill="both", expand=True)

        # -------------------
        # Load Sprites (fallback if missing)
        # -------------------
        # Player animations
        self.player_walk_frames = [safe_load_image(f"player_walk{i}.png", 40, 60, "blue") for i in range(1, 5)]
        self.player_jump_frame = safe_load_image("player_jump.png", 40, 60, "purple")
        self.player_idle_frame = safe_load_image("player_idle.png", 40, 60, "blue")

        # Enemy animation
        self.enemy_walk_frames = [safe_load_image(f"enemy_walk{i}.png", 40, 60, "green") for i in range(1, 5)]

        # Bullet & ground
        self.bullet_sprite = safe_load_image("bullet.png", 10, 10, "yellow")
        self.ground_sprite = safe_load_image("ground.png", 64, 64, "brown")

        # Background layers
        self.bg_far = safe_load_image("bg_far.png", 800, 400, "lightblue")
        self.bg_mid = safe_load_image("bg_mid.png", 800, 300, "lightgreen")
        self.bg_near = safe_load_image("bg_near.png", 800, 200, "darkgreen")

        # Camera
        self.camera_x = 0

        # Background tiles (parallax)
        self.bg_far_tiles, self.bg_mid_tiles, self.bg_near_tiles = [], [], []
        for i in range((LEVEL_LENGTH // self.bg_far.width()) + 3):
            self.bg_far_tiles.append(self.canvas.create_image(i * self.bg_far.width(), self.height-400,
                                                              image=self.bg_far, anchor="sw"))
        for i in range((LEVEL_LENGTH // self.bg_mid.width()) + 3):
            self.bg_mid_tiles.append(self.canvas.create_image(i * self.bg_mid.width(), self.height-300,
                                                              image=self.bg_mid, anchor="sw"))
        for i in range((LEVEL_LENGTH // self.bg_near.width()) + 3):
            self.bg_near_tiles.append(self.canvas.create_image(i * self.bg_near.width(), self.height-200,
                                                               image=self.bg_near, anchor="sw"))

        # Ground tiles
        self.ground_tiles = []
        for i in range((LEVEL_LENGTH // 64) + 2):
            tile = self.canvas.create_image(i*64, GROUND_Y+32, image=self.ground_sprite, anchor="s")
            self.ground_tiles.append(tile)

        # Player
        self.player_x = 200
        self.player_y = GROUND_Y
        self.player = self.canvas.create_image(self.player_x, self.player_y,
                                               image=self.player_idle_frame, anchor="s")
        self.player_health = PLAYER_HEALTH
        self.vel_y = 0
        self.player_frame_index = 0
        self.player_anim_counter = 0
        self.player_facing_right = True

        # Entities
        self.bullets = []
        self.enemies = []

        # Controls
        self.keys_pressed = set()
        root.bind("<KeyPress>", self.key_press)
        root.bind("<KeyRelease>", self.key_release)
        root.bind("<Button-1>", self.shoot_bullet)
        root.bind("<Motion>", self.update_mouse_position)
        root.bind("<Escape>", lambda e: root.destroy())

        # Mouse
        self.mouse_x, self.mouse_y = self.width // 2, self.height // 2

        # HUD
        self.score = 0
        self.wave = 1
        self.running = True
        self.health_text = self.canvas.create_text(20, 20, text=f"❤️ {self.player_health}",
                                                   fill="red", font=("Press Start 2P", 16), anchor="nw")
        self.score_text = self.canvas.create_text(self.width - 20, 20, text=f"Score: {self.score}",
                                                  fill="white", font=("Press Start 2P", 16), anchor="ne")

        # Start
        self.spawn_wave()
        self.update_game()

    # -------------------
    # Controls
    # -------------------
    def key_press(self, event):
        self.keys_pressed.add(event.keysym)
        if event.keysym in ("w", "space"):
            self.jump()

    def key_release(self, event):
        if event.keysym in self.keys_pressed:
            self.keys_pressed.remove(event.keysym)

    def update_mouse_position(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y

    # -------------------
    # Shooting
    # -------------------
    def shoot_bullet(self, event=None):
        px, py = self.player_x, self.player_y
        target_x = self.mouse_x + self.camera_x
        target_y = self.mouse_y
        angle = math.atan2(target_y - py, target_x - px)
        dx = BULLET_SPEED * math.cos(angle)
        dy = BULLET_SPEED * math.sin(angle)

        bullet = {"x": px, "y": py - 20, "dx": dx, "dy": dy,
                  "id": self.canvas.create_image(0, 0, image=self.bullet_sprite)}
        self.bullets.append(bullet)

    # -------------------
    # Player
    # -------------------
    def jump(self):
        if self.player_y >= GROUND_Y:
            self.vel_y = JUMP_STRENGTH

    def move_player(self):
        dx = 0
        if "a" in self.keys_pressed:
            dx -= PLAYER_SPEED
            self.player_facing_right = False
        if "d" in self.keys_pressed:
            dx += PLAYER_SPEED
            self.player_facing_right = True

        # gravity
        self.vel_y += GRAVITY
        self.player_y += self.vel_y

        if self.player_y >= GROUND_Y:
            self.player_y = GROUND_Y
            self.vel_y = 0

        self.player_x += dx
        self.player_x = max(0, min(LEVEL_LENGTH, self.player_x))

        # camera follow
        self.camera_x = self.player_x - self.width // 2
        self.camera_x = max(0, min(self.camera_x, LEVEL_LENGTH - self.width))

    def update_player_animation(self):
        if self.player_y < GROUND_Y:  # jumping
            frame = self.player_jump_frame
        elif "a" in self.keys_pressed or "d" in self.keys_pressed:  # walking
            self.player_anim_counter += 1
            if self.player_anim_counter % 5 == 0:
                self.player_frame_index = (self.player_frame_index + 1) % len(self.player_walk_frames)
            frame = self.player_walk_frames[self.player_frame_index]
        else:  # idle
            frame = self.player_idle_frame

        self.canvas.itemconfig(self.player, image=frame)

    # -------------------
    # Enemies
    # -------------------
    def spawn_wave(self):
        for _ in range(self.wave * 5):
            x = random.randint(300, LEVEL_LENGTH-100)
            enemy = {"x": x, "y": GROUND_Y,
                     "frame_index": 0, "anim_counter": 0,
                     "id": self.canvas.create_image(0, 0, image=self.enemy_walk_frames[0], anchor="s")}
            self.enemies.append(enemy)

    def update_enemies(self):
        for enemy in self.enemies:
            direction = 1 if self.player_x > enemy["x"] else -1
            enemy["x"] += direction * ENEMY_SPEED

            # animate
            enemy["anim_counter"] += 1
            if enemy["anim_counter"] % 6 == 0:
                enemy["frame_index"] = (enemy["frame_index"] + 1) % len(self.enemy_walk_frames)
                self.canvas.itemconfig(enemy["id"], image=self.enemy_walk_frames[enemy["frame_index"]])

    # -------------------
    # Game Loop
    # -------------------
    def update_game(self):
        if not self.running:
            return

        self.move_player()
        self.update_player_animation()
        self.update_bullets()
        self.update_enemies()
        self.check_collisions()
        self.render()

        if not self.enemies:
            self.wave += 1
            self.spawn_wave()

        self.root.after(30, self.update_game)

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            if (bullet["x"] < 0 or bullet["x"] > LEVEL_LENGTH or
                bullet["y"] < 0 or bullet["y"] > self.height):
                self.canvas.delete(bullet["id"])
                self.bullets.remove(bullet)

    def check_collisions(self):
        # Enemy vs Player
        for enemy in self.enemies[:]:
            if abs(self.player_x - enemy["x"]) < 40 and abs(self.player_y - enemy["y"]) < 40:
                self.player_health -= 5
                self.canvas.itemconfig(self.health_text, text=f"❤️ {self.player_health}")
                if self.player_health <= 0:
                    self.game_over()
                self.canvas.delete(enemy["id"])
                self.enemies.remove(enemy)

        # Bullet vs Enemy
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if abs(bullet["x"] - enemy["x"]) < 30 and abs(bullet["y"] - enemy["y"]) < 40:
                    self.score += 10
                    self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
                    self.canvas.delete(enemy["id"])
                    self.enemies.remove(enemy)
                    self.canvas.delete(bullet["id"])
                    self.bullets.remove(bullet)
                    break

    def render(self):
        # Background parallax
        for i, tile in enumerate(self.bg_far_tiles):
            self.canvas.coords(tile, i*self.bg_far.width() - self.camera_x*0.3, self.height-400)
        for i, tile in enumerate(self.bg_mid_tiles):
            self.canvas.coords(tile, i*self.bg_mid.width() - self.camera_x*0.6, self.height-300)
        for i, tile in enumerate(self.bg_near_tiles):
            self.canvas.coords(tile, i*self.bg_near.width() - self.camera_x*0.8, self.height-200)

        # Ground
        for i, tile in enumerate(self.ground_tiles):
            self.canvas.coords(tile, i*64 - self.camera_x, GROUND_Y+32)

        # Player
        self.canvas.coords(self.player, self.player_x - self.camera_x, self.player_y)

        # Enemies
        for enemy in self.enemies:
            self.canvas.coords(enemy["id"], enemy["x"] - self.camera_x, enemy["y"])

        # Bullets
        for bullet in self.bullets:
            self.canvas.coords(bullet["id"], bullet["x"] - self.camera_x, bullet["y"])

    def game_over(self):
        self.running = False
        self.canvas.delete("all")
        self.canvas.create_text(
            self.width // 2, self.height // 2,
            text=f"GAME OVER\nFinal Score: {self.score}",
            fill="red", font=("Press Start 2P", 32)
        )

# -------------------
# Run
# -------------------
if __name__ == "__main__":
    root = tk.Tk()
    game = SideScrollerGame(root)
    root.mainloop()
