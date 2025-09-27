# game.py
import tkinter as tk
import random
import pygame
import sys

PLAYER_BASE_HEALTH = 100


class Game:
    def __init__(self, root, difficulty="Easy", resolution="800x600"):
        self.root = root
        self.difficulty = difficulty
        res_width, res_height = map(int, resolution.split("x"))
        self.base_width = res_width
        self.base_height = res_height
        self.resolution = resolution

        # Fullscreen & resolution
        if root:
            root.attributes("-fullscreen", True)
            root.update_idletasks()
            self.width = root.winfo_screenwidth()
            self.height = root.winfo_screenheight()
        else:
            self.width, self.height = res_width, res_height

        # scaling factors
        self.scale_x = self.width / self.base_width
        self.scale_y = self.height / self.base_height
        self.scale = min(self.scale_x, self.scale_y)

        # Try init pygame mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            print(f"[Audio] mixer init failed: {e}")

        # Canvas
        self.canvas = tk.Canvas(root, bg="black", width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Background stars
        self.stars = [self.create_star() for _ in range(80)]

        # Player
        self.player_size = max(16, int(30 * self.scale_x))
        self.player = self.canvas.create_rectangle(
            self.width // 2, self.height - 3 * self.player_size,
            self.width // 2 + self.player_size, self.height - 2 * self.player_size,
            fill="white"
        )
        self.player_x_speed = 0

        # Scroll speed
        self.scroll_speed = 5 if difficulty == "Easy" else 8 if difficulty == "Medium" else 12
        self.base_scroll_speed = self.scroll_speed

        # Entities
        self.platforms = []
        self.generate_platforms()
        self.enemies = []
        self.powerups = []

        # Stats
        self.health = PLAYER_BASE_HEALTH
        self.score = 0
        self.multiplier = 1

        # HUD (lazy init later)
        self.health_text = None
        self.score_text = None

        # Controls
        root.bind("<KeyPress>", self.key_press)
        root.bind("<KeyRelease>", self.key_release)
        root.bind("p", lambda e: self.toggle_pause())
        root.bind("<Escape>", lambda e: self.exit_game())

        self.paused = False
        self.pause_frame = None
        self.running = True

        # Start screen
        self.show_start_screen()

    # -------------------
    # Font helper
    # -------------------
    def get_font(self, size, weight="normal"):
        scaled_size = max(10, int(size * self.scale))
        return ("Arial", scaled_size, weight)

    # -------------------
    # Helpers
    # -------------------
    def create_star(self):
        x = random.randint(0, self.width)
        y = random.randint(0, self.height)
        size = random.randint(1, 3)
        return self.canvas.create_oval(x, y, x + size, y + size, fill="white", outline="")

    def generate_platforms(self):
        self.platforms.clear()
        for i in range(6):
            max_w = max(1, self.width - int(200 * self.scale_x))
            x1 = random.randint(0, max_w)
            y1 = self.height - i * int(100 * self.scale_y)
            x2 = x1 + random.randint(int(100 * self.scale_x), int(200 * self.scale_x))
            platform = self.canvas.create_rectangle(
                x1, y1, x2, y1 + int(20 * self.scale_y), fill="green"
            )
            self.platforms.append(platform)

    def spawn_enemy(self):
        size = max(8, int(25 * self.scale_x))
        x = random.randint(0, max(0, self.width - size))
        enemy = self.canvas.create_rectangle(x, 0, x + size, size, fill="red")
        self.enemies.append(enemy)

    def spawn_powerup(self):
        size = max(6, int(20 * self.scale_x))
        x = random.randint(0, max(0, self.width - size))
        kind = random.choice(["health", "score"])
        color = "cyan" if kind == "health" else "yellow"
        powerup = self.canvas.create_oval(x, 0, x + size, size, fill=color)
        self.powerups.append((powerup, kind))

    # -------------------
    # Input
    # -------------------
    def key_press(self, event):
        if event.keysym == "a":
            self.player_x_speed = -10 * self.scale_x
        elif event.keysym == "d":
            self.player_x_speed = 10 * self.scale_x
        elif event.keysym == "w":
            self.scroll_speed = min(self.base_scroll_speed * 2, self.scroll_speed + 3)
        elif event.keysym == "s":
            self.scroll_speed = max(2, self.scroll_speed - 3)

    def key_release(self, event):
        if event.keysym in ("a", "d"):
            self.player_x_speed = 0
        elif event.keysym == "w":
            self.scroll_speed = max(self.base_scroll_speed, self.scroll_speed - 3)
        elif event.keysym == "s":
            self.scroll_speed = min(self.base_scroll_speed * 2, self.scroll_speed + 3)

    # -------------------
    # Start Screen
    # -------------------
    def show_start_screen(self):
        font_title = self.get_font(36, "bold")
        header_font = self.get_font(20, "bold")
        desc_font = self.get_font(14)
        orb_size = max(12, int(20 * self.scale))

        self.start_frame = tk.Frame(self.root, bg="black")
        self.start_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            self.start_frame, text="CLICK TO BEGIN",
            fg="white", bg="black", font=font_title
        ).pack(pady=30)

        legend_frame = tk.Frame(
            self.start_frame, bg="gray20",
            highlightbackground="white", highlightthickness=2
        )
        legend_frame.pack(pady=10, padx=10)

        tk.Label(legend_frame, text="Legend", font=header_font,
                 fg="white", bg="gray20").pack(pady=(10, 6))

        descriptions = [
            ("cyan", "Green/Cyan orb — +20 Health"),
            ("yellow", "Yellow orb — +200 Score"),
            ("red", "Red enemy — damages you (-5)"),
            ("green", "Green platform — damaging terrain (-1/sec)"),
        ]

        for color, desc in descriptions:
            row = tk.Frame(legend_frame, bg="gray20")
            row.pack(fill="x", pady=4, padx=8)

            orb_canvas = tk.Canvas(row, width=orb_size * 2, height=orb_size * 2,
                                   bg="gray20", highlightthickness=0)
            orb_canvas.pack(side="left", padx=6)
            orb_canvas.create_oval(2, 2, orb_size * 2 - 2, orb_size * 2 - 2, fill=color, outline="white")

            tk.Label(row, text=desc, font=desc_font, fg="white", bg="gray20",
                     anchor="w").pack(side="left", padx=8)

        self.root.bind("<Button-1>", self.start_after_click)

    def start_after_click(self, event=None):
        try:
            self.root.unbind("<Button-1>")
            self.start_frame.destroy()
        except:
            pass

        try:
            pygame.mixer.music.load("music.mp3")
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading music: {e}")

        self.health = PLAYER_BASE_HEALTH
        self.score = 0
        self.multiplier = 1

        if not self.health_text:
            self.health_text = self.canvas.create_text(
                int(self.width * 0.05), int(self.height * 0.05),
                text=f"Health: {self.health}", fill="red",
                font=self.get_font(20, "bold"), anchor="w"
            )
        else:
            self.canvas.itemconfig(self.health_text, text=f"Health: {self.health}")

        if not self.score_text:
            self.score_text = self.canvas.create_text(
                int(self.width * 0.95), int(self.height * 0.05),
                text=f"Score: {self.score}", fill="white",
                font=self.get_font(20, "bold"), anchor="e"
            )
        else:
            self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")

        self.update_game()

    # -------------------
    # Game loop, collisions, game over...
    # -------------------
    def update_game(self):
        if not self.running or self.paused:
            return
        self.canvas.move(self.player, self.player_x_speed, 0)
        self.root.after(30, self.update_game)

    def toggle_pause(self):
        self.paused = not self.paused

    def exit_game(self):
        self.running = False
        self.root.destroy()


# -------------------
# Loading Screen (centered & scaled)
# -------------------
class LoadingScreen:
    def __init__(self, root, difficulty, resolution):
        self.root = root
        self.difficulty = difficulty
        self.resolution = resolution
        res_width, res_height = map(int, resolution.split("x"))

        # scale factors
        self.scale_x = res_width / 800
        self.scale_y = res_height / 600
        self.scale = min(self.scale_x, self.scale_y)

        self.canvas = tk.Canvas(root, bg="black", width=res_width, height=res_height)
        self.canvas.pack(fill="both", expand=True)

        # fonts and bar sizing
        title_font = ("Arial", max(20, int(40 * self.scale)), "bold")
        bar_width = int(res_width * 0.6)
        bar_height = max(20, int(30 * self.scale))

        center_x = res_width // 2
        center_y = res_height // 2

        self.bar_x1 = center_x - bar_width // 2
        self.bar_y1 = center_y - bar_height // 2
        self.bar_x2 = center_x + bar_width // 2
        self.bar_y2 = center_y + bar_height // 2

        # text above bar
        self.text = self.canvas.create_text(
            center_x,
            self.bar_y1 - int(1.5 * bar_height),
            text="Loading Game...",
            fill="white",
            font=title_font
        )

        self.bar_outline = self.canvas.create_rectangle(
            self.bar_x1, self.bar_y1, self.bar_x2, self.bar_y2,
            outline="white", width=3
        )
        self.bar_fill = self.canvas.create_rectangle(
            self.bar_x1, self.bar_y1, self.bar_x1, self.bar_y2,
            fill="white", width=0
        )

        self.progress = 0
        self.colors = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta"]
        self.update_bar()

    def update_bar(self):
        if self.progress <= 100:
            color = self.colors[self.progress % len(self.colors)]
            self.canvas.itemconfig(self.bar_fill, fill=color)
            fill_x = self.bar_x1 + (self.progress / 100) * (self.bar_x2 - self.bar_x1)
            self.canvas.coords(self.bar_fill, self.bar_x1, self.bar_y1, fill_x, self.bar_y2)
            self.progress += 2
            self.root.after(80, self.update_bar)
        else:
            self.start_game()

    def start_game(self):
        try:
            self.canvas.destroy()
        except:
            pass
        Game(self.root, self.difficulty, self.resolution)


# -------------------
# Entry Point
# -------------------
def start_game_window(difficulty="Easy", resolution="800x600", fullscreen=False, skip_loading=False):
    root = tk.Tk()
    if fullscreen:
        root.attributes("-fullscreen", True)
    else:
        root.geometry(resolution)

    if skip_loading:
        Game(root, difficulty, resolution)
    else:
        LoadingScreen(root, difficulty, resolution)
    root.mainloop()


if __name__ == "__main__":
    start_game_window(fullscreen=True)
