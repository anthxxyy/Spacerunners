import tkinter as tk
import pygame  # for music
import webbrowser
import sys
import subprocess


# -------------------
# Music Controls
# -------------------
def play_menu_music():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load("menu_music.mp3")
        pygame.mixer.music.set_volume(0.3)  # 🔊 default volume (30%)
        pygame.mixer.music.play(-1)  # loop forever
    except Exception as e:
        print(f"Error playing menu music: {e}")


def stop_menu_music():
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Error stopping menu music: {e}")


def set_volume(val):
    try:
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)
    except Exception as e:
        print(f"Error setting volume: {e}")


# -------------------
# Menu UI
# -------------------
def main_menu():
    global root, canvas
    root = tk.Tk()
    root.title("Game Hub")

    # Fullscreen
    root.attributes("-fullscreen", True)
    root.update_idletasks()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()

    canvas = tk.Canvas(root, bg="black", width=width, height=height, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Dynamic scaling
    title_font_size = max(36, width // 20)
    tile_font_size = max(18, width // 45)
    button_font_size = max(16, width // 55)
    coffee_font_size = max(18, width // 40)

    # Title
    canvas.create_text(
        width // 2, height // 8,
        text="🎮 Game Hub 🎮", font=("Arial", title_font_size, "bold"), fill="white"
    )

    # ---- Game Tiles (2x2 grid) ----
    tile_w = int(width * 0.25)
    tile_h = int(height * 0.25)
    spacing_x = int(width * 0.2)
    spacing_y = int(height * 0.3)

    games = [
        ("Space Runner", open_space_runner),   # ✅ launches in new process
        ("Survive Together", open_survival),   # ✅ launches in new process
        ("Coming Soon 1", lambda: placeholder("Coming Soon 1")),
        ("Coming Soon 2", lambda: placeholder("Coming Soon 2")),
    ]

    x_positions = [spacing_x, spacing_x * 2 + tile_w]
    y_positions = [spacing_y, spacing_y + tile_h + int(height * 0.05)]

    idx = 0
    for y in y_positions:
        for x in x_positions:
            if idx >= len(games):
                break
            name, command = games[idx]

            frame = tk.Frame(root, width=tile_w, height=tile_h,
                             bg="gray20", highlightbackground="white", highlightthickness=2)
            frame.pack_propagate(False)

            btn = tk.Button(
                frame, text=name,
                font=("Arial", tile_font_size, "bold"),
                fg="white", bg="black", activebackground="gray30",
                command=command
            )
            btn.pack(fill="both", expand=True)

            canvas.create_window(x, y, window=frame, anchor="nw")
            idx += 1

    # Coffee button
    coffee_btn = tk.Button(
        root,
        text="❤️ Buy me a coffee!",
        font=("Arial", coffee_font_size, "bold"),
        fg="white", bg="black", activebackground="gray30",
        command=lambda: webbrowser.open("https://www.google.com")
    )
    canvas.create_window(width // 2, height // 2, window=coffee_btn)

    # Options + Exit
    options_btn = tk.Button(
        root, text="Options", font=("Arial", button_font_size, "bold"),
        command=show_options
    )
    canvas.create_window(int(width * 0.05), int(height * 0.90), window=options_btn, anchor="sw")

    exit_btn = tk.Button(root, text="Exit", font=("Arial", button_font_size), command=root.destroy)
    canvas.create_window(int(width * 0.05), int(height * 0.95), window=exit_btn, anchor="sw")

    play_menu_music()
    root.mainloop()


# -------------------
# Space Runner
# -------------------
import subprocess, sys

def open_space_runner():
    stop_menu_music()
    root.destroy()
    # run game.py as a blocking process (takes over after menu closes)
    subprocess.run([sys.executable, "game.py"], check=True)



# -------------------
# Survive Together
# -------------------
def open_survival():
    stop_menu_music()
    root.destroy()
    subprocess.run([sys.executable, "survive.py"], check=True)

# -------------------
# Placeholder
# -------------------
def placeholder(name):
    popup = tk.Toplevel(root, bg="black")
    popup.update_idletasks()
    screen_w = popup.winfo_screenwidth()
    screen_h = popup.winfo_screenheight()
    popup_w = int(screen_w * 0.3)
    popup_h = int(screen_h * 0.25)
    x = (screen_w // 2) - (popup_w // 2)
    y = (screen_h // 2) - (popup_h // 2)
    popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
    popup.title("Coming Soon")

    rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    text = "More coming soon!"
    text_frame = tk.Frame(popup, bg="black")
    text_frame.pack(pady=20)
    labels = []
    for char in text:
        lbl = tk.Label(text_frame, text=char, font=("Arial", 16, "bold"), bg="black")
        lbl.pack(side="left")
        labels.append(lbl)

    github_btn = tk.Button(
        popup,
        text="Check GitHub for updates",
        font=("Arial", 12, "bold"),
        command=lambda: webbrowser.open("https://github.com/anthxxyy?tab=projects"),
        bg="black", fg="white", activebackground="gray20"
    )
    github_btn.pack(pady=10)

    def animate_all(offset=0):
        color = rainbow_colors[offset % len(rainbow_colors)]
        for i, lbl in enumerate(labels):
            lbl.config(fg=rainbow_colors[(i + offset) % len(rainbow_colors)])
        github_btn.config(fg=color)
        popup.after(300, lambda: animate_all(offset + 1))

    animate_all()


# -------------------
# Options Window
# -------------------
def show_options():
    popup = tk.Toplevel(root, bg="black")
    popup.title("Options")
    popup.geometry("400x300")

    lbl = tk.Label(popup, text="Options", font=("Arial", 18, "bold"), fg="white", bg="black")
    lbl.pack(pady=20)

    volume_lbl = tk.Label(popup, text="Music Volume", fg="white", bg="black")
    volume_lbl.pack(pady=5)

    slider = tk.Scale(
        popup, from_=0, to=100, orient="horizontal",
        command=set_volume, length=200,
        bg="black", fg="white", highlightthickness=0, troughcolor="gray20"
    )
    try:
        slider.set(int(pygame.mixer.music.get_volume() * 100))
    except:
        slider.set(30)
    slider.pack(pady=10)

    btn = tk.Button(popup, text="Close", command=popup.destroy)
    btn.pack(pady=20)


if __name__ == "__main__":
    main_menu()
