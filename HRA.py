import tkinter
import random
import json
import os
import math
from PIL import Image, ImageTk, ImageSequence


class Player:
    def __init__(self, canvas, x, y, base_img=None):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.speed = 6

        self.sprite = None
        self.visible = True

        self.angle = 0
        self.base_img = base_img
        self.current_image = None

        if self.base_img is not None:
            self.width, self.height = self.base_img.size
        else:
            self.width = 40
            self.height = 40

    def update(self, world_width, world_height):
        self.x += self.vx
        self.y += self.vy

        if self.x < self.width // 2:
            self.x = self.width // 2
        if self.x > world_width - self.width // 2:
            self.x = world_width - self.width // 2

        line_y = world_height//4
        min_y = line_y+self.height//2
        if self.y < min_y:
            self.y = min_y
        if self.y > world_height - self.height // 2:
            self.y = world_height - self.height // 2

    def get_bbox(self):
        return (self.x - self.width // 2,
                self.y - self.height // 2,
                self.x + self.width // 2,
                self.y + self.height // 2)

    def draw(self):
        if not self.visible:
            if self.sprite is not None:
                self.canvas.delete(self.sprite)
                self.sprite = None
            return

        if self.sprite is not None:
            self.canvas.delete(self.sprite)

        if self.base_img is not None:
            rotated = self.base_img.rotate(-self.angle - 90, expand=True)
            self.current_image = ImageTk.PhotoImage(rotated)
            self.sprite = self.canvas.create_image(
                self.x,
                self.y,
                image=self.current_image
            )
            self.width, self.height = rotated.size

        else:
            self.sprite = self.canvas.create_rectangle(
                self.x - self.width // 2,
                self.y - self.height // 2,
                self.x + self.width // 2,
                self.y + self.height // 2,
                fill="cyan"
            )

class Enemy:
    def __init__(self, canvas, x, y, vy,
                 can_shoot=False,
                 image_normal=None,
                 image_hit=None,
                 vx=0,
                 effect_frames=None,
                 kind = "basic",
                 projectile_color="lightblue",
                 projectile_speed_mult=1.0):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vy = vy
        self.vx = vx
        self.kind = kind
        self.projectile_color = projectile_color
        self.projectile_speed_mult = projectile_speed_mult
        if image_normal is not None:
            self.width = image_normal.width()
            self.height = image_normal.height()
        else:
            self.width = 30
            self.height = 30

        self.can_shoot = can_shoot
        self.shoot_cooldown = random.randint(5, 20) if can_shoot else -1

        self.image_normal = image_normal
        self.image_hit = image_hit
        self.sprite = None

        self.is_dying = False
        self.death_timer = 0

        self.zigzag_phase = random.uniform(0, 2 * math.pi)
        self.zigzag_ampl = random.randint(40, 120)
        self.zigzag_speed = random.uniform(0.03, 0.07)
        self.base_x = x

        self.effect_frames = effect_frames or []
        self.effect_index = 0
        self.effect_speed = 3
        self.effect_counter = 0

    def start_dying(self):
        self.is_dying = True
        self.death_timer = 10
        self.can_shoot = False
        self.vx *= 0.5
        self.vy *= 0.5

    def update(self, spawn_projectile_callback, player=None, level=1):
        canvas_height = self.canvas.winfo_height()
        line_y = canvas_height // 4

        if self.kind == "chaser" and player is not None and not self.is_dying:
            dx = player.x - self.x
            dy = player.y - self.y
            length = math.hypot(dx, dy) or 1.0

            speed = 4.0 + level * 0.3
            self.x += dx / length * speed
            self.y += dy / length * speed

        else:
            self.y += self.vy

            if self.kind == "zigzag":
                self.zigzag_phase += self.zigzag_speed
                self.x = self.base_x + math.sin(self.zigzag_phase) * self.zigzag_ampl

            else:
                self.x += self.vx

        if self.can_shoot and self.kind != "chaser" and self.y > line_y and not self.is_dying:
            self.shoot_cooldown -= 1
            if self.shoot_cooldown <= 0:
                self.shoot_cooldown = random.randint(30, 50)

                base_speed = 6 + level * 0.3
                speed = base_speed * self.projectile_speed_mult

                if player is not None:
                    t = 15
                    target_x = player.x + player.vx * t
                    target_y = player.y + player.vy * t

                    dx = target_x - self.x
                    dy = target_y - (self.y + self.height // 2)
                    length = math.hypot(dx, dy) or 1.0

                    vx = dx / length * speed
                    vy = dy / length * speed

                    vx += random.uniform(-1.0, 1.0)
                    vy += random.uniform(-0.5, 0.5)
                else:
                    vx = random.uniform(-1.5, 1.5)
                    vy = speed

                spawn_projectile_callback(
                    self.x,
                    self.y + self.height // 2,
                    vx,
                    vy,
                    color=self.projectile_color
                )

        if self.effect_frames:
            self.effect_counter += 1
            if self.effect_counter >= self.effect_speed:
                self.effect_counter = 0
                self.effect_index = (self.effect_index + 1) % len(self.effect_frames)

    def draw(self):
        if self.sprite is not None:
            self.canvas.delete(self.sprite)

        if getattr(self, "effect_frames", None):
            eff = self.effect_frames[self.effect_index % len(self.effect_frames)]
            self.canvas.create_image(self.x, self.y, image=eff)

        if self.is_dying:
            r = int(min(self.width, self.height) * 0.6)

            if self.death_timer % 2 == 0:
                farba = "#ffcc33"
            else:
                farba = "#ff8800"

            self.canvas.create_oval(
                self.x - r,
                self.y - r,
                self.x + r,
                self.y + r,
                fill=farba,
                outline=""
            )

            if self.image_hit is not None:
                img = self.image_hit if self.death_timer % 2 == 0 else self.image_normal
            else:
                img = self.image_normal

            if img is not None:
                self.sprite = self.canvas.create_image(self.x, self.y, image=img)
            else:
                self.sprite = self.canvas.create_oval(
                    self.x - self.width // 2,
                    self.y - self.height // 2,
                    self.x + self.width // 2,
                    self.y + self.height // 2,
                    fill=farba,
                    outline=""
                )
            return

        if self.image_normal:
            self.sprite = self.canvas.create_image(self.x, self.y, image=self.image_normal)
        else:
            farba = "red" if self.can_shoot else "orange"
            r = min(self.width, self.height) // 2
            self.sprite = self.canvas.create_oval(
                self.x - r,
                self.y - r,
                self.x + r,
                self.y + r,
                fill=farba,
                outline=""
            )

    def get_bbox(self):
        return (self.x - self.width // 2,
                self.y - self.height // 2,
                self.x + self.width // 2,
                self.y + self.height // 2)

class Projectile:
    def __init__(self, canvas, x, y, vx=0, vy=7, color="lightblue"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vy = vy
        self.vx = vx
        self.size = 8
        self.sprite = None
        self.color = color

    def update(self):
        self.y += self.vy
        self.x += self.vx

    def draw(self):
        if self.sprite is not None:
            self.canvas.delete(self.sprite)
        dlzka = 25
        vlen = (self.vx**2+self.vy**2)**0.5
        if vlen == 0:
            vlen =1

        dx = self.vx / vlen * dlzka
        dy = self.vy / vlen * dlzka
        self.sprite = self.canvas.create_line(
            self.x,self.y,
            self.x+dx, self.y+dy,
            width=5,
            fill=self.color)

    def get_bbox(self):
        return (self.x - self.size,
                self.y - self.size,
                self.x + self.size,
                self.y + self.size)

class PlayerBullet:
    def __init__(self, canvas, x, y, vx, vy, color="green", frames_pil = None):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.length = 40
        self.sprite = None

        self.frames_pil = frames_pil or []
        self.anim_index = 0
        self.anim_speed = 2
        self.anim_counter = 0
        self.tk_image = None


    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        if self.sprite is not None:
            self.canvas.delete(self.sprite)

        if self.frames_pil:
            self.anim_counter += 1
            if self.anim_counter >= self.anim_speed:
                self.anim_counter = 0
                self.anim_index = (self.anim_index + 1) % len(self.frames_pil)
            base = self.frames_pil[self.anim_index]
            angle = math.degrees(math.atan2(self.vy, self.vx))
            rotated = base.rotate(-angle, expand=True)
            self.tk_image = ImageTk.PhotoImage(rotated)
            self.sprite = self.canvas.create_image(
                self.x,
                self.y,
                image=self.tk_image
            )
        else:
            vlen = (self.vx ** 2 + self.vy ** 2) ** 0.5 or 1
            dlzka = 40
            dx = self.vx / vlen * dlzka
            dy = self.vy / vlen * dlzka

            self.sprite = self.canvas.create_line(
                self.x,
                self.y,
                self.x + dx,
                self.y + dy,
                width=10,
                fill=self.color
            )

    def get_bbox(self):
        r = 10
        return (self.x - r,
                self.y - r,
                self.x + r,
                self.y + r)

class Shield:
    def __init__(self, canvas, x, y, image=None, radius=25):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.sprite = None
        self.image = image

        if self.image is not None:
            self.width = self.image.width()
            self.height = self.image.height()
        else:
            self.width = radius * 2
            self.height = radius * 2

    def get_bbox(self):
        return (
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.x + self.width // 2,
            self.y + self.height // 2
        )

    def draw(self):
        if self.sprite is not None:
            self.canvas.delete(self.sprite)

        if self.image is not None:
            self.sprite = self.canvas.create_image(
                self.x,
                self.y,
                image=self.image
            )
        else:
            r = self.width // 2
            self.sprite = self.canvas.create_oval(
                self.x - r,
                self.y - r,
                self.x + r,
                self.y + r,
                outline="cyan",
                width=3
            )


class Program:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title("SPACE SHOOTER")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.canvas = tkinter.Canvas(self.root,
                                     width=self.width,
                                     height=self.height,
                                     bg="black")
        self.canvas.pack()

        self.crosshair_x = self.width//2
        self.crosshair_y = self.height//2
        self.crosshair_active = True

        self.menu_button = (
            self.width // 2 - 150,
            self.height // 2 - 50,
            self.width // 2 + 150,
            self.height // 2 + 50
        )
        btn_y = self.height // 2 + 80
        btn_w = 160
        btn_h = 40
        gap = 20
        self.mode_button_classic = (
            self.width // 2 - btn_w - gap // 2,
            btn_y,
            self.width // 2 - gap // 2,
            btn_y + btn_h
        )
        self.mode_button_hardcore = (
            self.width // 2 + gap // 2,
            btn_y,
            self.width // 2 + btn_w,
            btn_y + btn_h
        )
        row_y = self.height // 2 + 170
        btn_w = 160
        btn_h = 40
        gap = 20

        self.reset_score_button = (
            self.width // 2 - btn_w - gap // 2,
            row_y,
            self.width // 2 - gap // 2,
            row_y + btn_h
        )

        self.info_button = (
            self.width // 2 + gap // 2,
            row_y,
            self.width // 2 + btn_w,
            row_y + btn_h
        )
        offset = -110

        def shift(rect, dy):
            x1, y1, x2, y2 = rect
            return (x1, y1 + dy, x2, y2 + dy)

        self.menu_button = shift(self.menu_button, offset)
        self.mode_button_classic = shift(self.mode_button_classic, offset)
        self.mode_button_hardcore = shift(self.mode_button_hardcore, offset)
        self.reset_score_button = shift(self.reset_score_button, offset)
        self.info_button = shift(self.info_button, offset)


        self.line_y = self.height // 4
        img = Image.open("game_bg_space_1280x720.png").convert("RGBA")
        img = img.resize((self.width, self.height - self.line_y), Image.LANCZOS)
        self.playfield_bg = ImageTk.PhotoImage(img)

        player_base_img = Image.open("pngwing.com.png").convert("RGBA")
        player_base_img = player_base_img.resize((60, 60), Image.LANCZOS)
        self.player = Player(self.canvas, self.width // 2, self.height - 50, base_img=player_base_img)

        img_e = Image.open("pngwing2.png").convert("RGBA")
        img_e = img_e.resize((60, 60), Image.LANCZOS)
        self.enemy_image_normal = ImageTk.PhotoImage(img_e)

        overlay = Image.new("RGBA", img_e.size, (255, 140, 0, 160))
        tinted = Image.alpha_composite(img_e, overlay)
        self.enemy_image_hit = ImageTk.PhotoImage(tinted)

        overlay_chaser = Image.new("RGBA", img_e.size, (120, 255, 120, 160))
        alpha_mask = img_e.split()[3]
        overlay_chaser.putalpha(alpha_mask)
        chaser_tinted = Image.alpha_composite(img_e, overlay_chaser)
        self.enemy_image_chaser = ImageTk.PhotoImage(chaser_tinted)

        gif = Image.open("fire-17010_256.gif")
        self.enemy_effect_frames = []
        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGBA")
            frame = frame.resize((120, 85), Image.LANCZOS)
            self.enemy_effect_frames.append(ImageTk.PhotoImage(frame))

        laser_gif = Image.open("giphy.gif")

        self.laser_frames_pil = []
        for frame in ImageSequence.Iterator(laser_gif):
            frame = frame.convert("RGBA")
            frame = frame.resize((60, 120), Image.LANCZOS)
            tk_frame = ImageTk.PhotoImage(frame)
            self.laser_frames_pil.append(frame)

        self.max_lives = 3
        self.lives = self.max_lives
        img_heart = Image.open("heartpng.png").convert("RGBA")
        img_heart = img_heart.resize((30, 30), Image.LANCZOS)
        self.heart_image = ImageTk.PhotoImage(img_heart)

        shield_img = Image.open("shield.png").convert("RGBA")
        shield_img = shield_img.resize((50, 50), Image.LANCZOS)
        self.shield_image = ImageTk.PhotoImage(shield_img)

        im = Image.open("menu_bg_animated_1280x720.gif")
        self.menu_bg_frames = []
        for frame in ImageSequence.Iterator(im):
            frame = frame.convert("RGBA")
            frame = frame.resize((self.width, self.height), Image.LANCZOS)
            self.menu_bg_frames.append(ImageTk.PhotoImage(frame))
        self.menu_bg_index = 0

        self.stars = []
        for i in range(70):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(10, 20)
            self.stars.append((x, y, size))
        self.enemies = []
        self.projectiles = []
        self.player_bullets = []
        self.shields = []
        self.has_shield = False
        self.shield_spawn_timer = 400

        self.invincible = False
        self.pause_exit_button = None
        self.blink_count = 0
        self.score = 0
        self.best_score = 0
        self.level = 1
        self.state = "menu"
        self.game_mode = "hardcore"
        self.running = False
        self.game_over = False
        self.spawn_timer = 0
        self.max_fire_cooldown = 20
        self.fire_cooldown = 0
        self.score_file = "scores.json"
        self.description_file = "info.txt"
        self.description_lines = []
        self.load_description_text()
        self.load_scores()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.game_loop()
        self.root.mainloop()

    def start_game(self):
        self.state = "game"
        self.running = True
        self.game_over = False
        self.reset_game()

    def on_mouse_move(self, event):
        if self.state != "game":
            self.crosshair_active = False
            self.canvas.config(cursor="arrow")
            return

        if not self.running or self.game_over:
            self.crosshair_active = False
            self.canvas.config(cursor="arrow")
            return

        line_y = self.height // 4

        if event.y < line_y:
            self.crosshair_active = False
            self.canvas.config(cursor="arrow")
        else:
            self.crosshair_active = True
            self.canvas.config(cursor="none")
            self.crosshair_x = event.x
            self.crosshair_y = event.y

    def on_key_press(self, event):
        if event.keysym in ("Left", "a", "A"):
            self.player.vx = -self.player.speed
        elif event.keysym in ("Right", "d", "D"):
            self.player.vx = self.player.speed
        elif event.keysym in ("Up", "w", "W"):
            self.player.vy = -self.player.speed
        elif event.keysym in ("Down", "s", "S"):
            self.player.vy = self.player.speed
        elif event.keysym == "space":
            if not self.game_over:
                self.running = not self.running

                if not self.running:
                    self.crosshair_active = False
                    self.canvas.config(cursor="arrow")
                else:
                    pass

    def on_key_release(self, event):
        if event.keysym in ("Left", "a", "A", "Right", "d", "D"):
            self.player.vx = 0
        if event.keysym in ("Up", "w", "W", "Down", "s", "S"):
            self.player.vy = 0

    def fire_bullet(self):
        if not self.crosshair_active:
            return

        if self.fire_cooldown>0:
            return
        dx = self.crosshair_x - self.player.x
        dy = self.crosshair_y - self.player.y

        if dx == 0 and dy == 0:
            return
        speed = 20

        length = (dx ** 2 + dy ** 2) ** 0.5
        vx = dx / length * speed
        vy = dy / length * speed

        bullet = PlayerBullet(
            self.canvas,
            self.player.x,
            self.player.y,
            vx,
            vy,
            color="cyan",
            frames_pil=self.laser_frames_pil
        )
        self.player_bullets.append(bullet)

        self.fire_cooldown = self.max_fire_cooldown

    def on_click(self, event):
        x, y = event.x, event.y

        if self.state == "menu":
            x1, y1, x2, y2 = self.menu_button
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.start_game()
                return

            cx1, cy1, cx2, cy2 = self.mode_button_classic
            if cx1 <= x <= cx2 and cy1 <= y <= cy2:
                self.game_mode = "classic"
                return

            hx1, hy1, hx2, hy2 = self.mode_button_hardcore
            if hx1 <= x <= hx2 and hy1 <= y <= hy2:
                self.game_mode = "hardcore"
                return

            rx1, ry1, rx2, ry2 = self.reset_score_button
            if rx1 <= x <= rx2 and ry1 <= y <= ry2:
                self.best_score = 0
                self.save_scores()
                return

            ix1, iy1, ix2, iy2 = self.info_button
            if ix1 <= x <= ix2 and iy1 <= y <= iy2:
                self.state = "about"
                return

            return

        if self.game_over:
            self.reset_game()
            self.state = "game"
            self.running = True
            return

        if self.state == "game" and not self.running and not self.game_over:
            if self.pause_exit_button is not None:
                x1, y1, x2, y2 = self.pause_exit_button
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.reset_game()
                    self.running = False
                    self.game_over = False
                    self.state = "menu"
                    return
            return

        if self.state == "game" and self.running:
            self.fire_bullet()

        if self.state == "about":
            if hasattr(self, "about_back_button") and self.about_back_button is not None:
                bx1, by1, bx2, by2 = self.about_back_button
                if bx1 <= x <= bx2 and by1 <= y <= by2:
                    self.state = "menu"
                    return
            return

    def load_description_text(self):
        if os.path.exists(self.description_file):
            try:
                with open(self.description_file, "r", encoding="utf-8") as f:
                    text = f.read()
                self.description_lines = text.splitlines()
            except Exception as e:
                print("Chyba pri čítaní description.txt:", e)
                self.description_lines = ["Chyba pri nacitani popisu hry."]
        else:
            self.description_lines = [
                "SPACE SHOOTER",
                "",
                "Subor description.txt nebol najdeny.",
                "Vytvor ho v rovnakom priecinku ako hra."
            ]

    def load_scores(self):
        if os.path.exists(self.score_file):
            try:
                with open(self.score_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.best_score = data.get("best_score", 0)
            except Exception:
                self.best_score = 0

    def save_scores(self):
        data = {"best_score": self.best_score}
        with open(self.score_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


    def reset_game(self):
        self.enemies = []
        self.projectiles = []
        self.player_bullets = []
        self.shields = []
        self.has_shield = False
        self.shield_spawn_timer = 100

        self.score = 0
        self.level = 1
        self.player.x = self.width // 2
        self.player.vx = 0
        self.lives = self.max_lives
        self.running = True
        self.game_over = False
        self.invincible = False
        self.blink_count = 0
        self.player.visible = True
        self.fire_cooldown = 0
        if self.game_mode == "hardcore":
            self.lives = 1
        else:
            self.lives = self.max_lives

    def spawn_enemy(self):
        line_y = self.height // 4

        if random.random() < 0.2:
            side = random.choice(["left", "right"])
            y = random.randint(line_y + 50, self.height - 50)
            vy = 0
            speed = random.randint(3, 6)
            if side == "left":
                x = -40
                vx = speed
            else:
                x = self.width + 40
                vx = -speed
        else:
            x = random.randint(30, self.width - 30)
            y = -20
            vy = random.randint(2, 3 + self.level)
            vx = 0

        shoot_chance = min(0.5 + self.level * 0.05, 0.8)
        can_shoot = random.random() < shoot_chance

        if self.level <= 2:
            kind = "basic"
        else:
            kinds = ["basic", "zigzag", "chaser"]
            if self.level < 5:
                weights = [0.4, 0.35, 0.25]
            else:
                weights = [0.25, 0.4, 0.35]
            kind = random.choices(kinds, weights=weights)[0]

        image_normal = self.enemy_image_normal
        image_hit = self.enemy_image_hit
        projectile_color = "lightblue"
        projectile_speed_mult = 1.0

        if kind == "zigzag":
            projectile_color = "#ff66ff"
            projectile_speed_mult = 0.6

        elif kind == "chaser":
            can_shoot = False
            image_normal = self.enemy_image_chaser
            projectile_color = "#ff4444"
            projectile_speed_mult = 1.0

        enemy = Enemy(
            self.canvas,
            x, y, vy,
            can_shoot=can_shoot,
            image_normal=image_normal,
            image_hit=image_hit,
            vx=vx,
            effect_frames=self.enemy_effect_frames,
            kind=kind,
            projectile_color=projectile_color,
            projectile_speed_mult=projectile_speed_mult
        )
        self.enemies.append(enemy)

    def spawn_shield(self):
        line_y = self.height // 4

        x = random.randint(50, self.width - 50)
        y = random.randint(line_y + 50, self.height - 80)

        shield = Shield(self.canvas, x, y,image= self.shield_image,)
        self.shields.append(shield)

    def spawn_projectile(self, x, y, vx,vy, color = "lightblue"):
        proj = Projectile(self.canvas, x, y, vx=vx, vy=vy, color=color)
        self.projectiles.append(proj)

    def check_collision(self, bbox1, bbox2):
        x1a, y1a, x1b, y1b = bbox1
        x2a, y2a, x2b, y2b = bbox2
        return not (x1b < x2a or x1a > x2b or y1b < y2a or y1a > y2b)

    def game_loop(self):
        self.canvas.delete("all")

        if self.state == "menu":
            if self.menu_bg_frames:
                self.menu_bg_index = (self.menu_bg_index + 1) % len(self.menu_bg_frames)
            self.draw_menu()

        elif self.state == "about":
            self.draw_about()

        else:
            if self.running and not self.game_over:
                self.tick_game()

            self.draw_bg()
            self.draw_all()
            self.draw_hud()

        self.root.after(25, self.game_loop)

    def tick_game(self):
        self.level = 1 + self.score // 10

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        self.player.update(self.width,self.height)
        dx = self.crosshair_x - self.player.x
        dy = self.crosshair_y - self.player.y
        if dx != 0 or dy != 0:
            self.player.angle = math.degrees(math.atan2(dy, dx))

        if len(self.shields) < 5:
            self.shield_spawn_timer -= 1
            if self.shield_spawn_timer <= 0:
                self.spawn_shield()
                self.shield_spawn_timer = random.randint(100, 300)

        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = max(25, 50 - self.level * 5)

        for enemy in self.enemies[:]:
            enemy.update(
                self.spawn_projectile,
                player=self.player,
                level=self.level
            )

            if enemy.is_dying:
                enemy.death_timer -= 1
                if enemy.death_timer <= 0:
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                continue

            if enemy.y > self.height + 40 or enemy.x < -40 or enemy.x > self.width + 40:
                self.enemies.remove(enemy)

        for proj in self.projectiles[:]:
            proj.update()
            if (proj.x < -50 or proj.x > self.width + 50 or
                    proj.y < -50 or proj.y > self.height + 50):
                self.projectiles.remove(proj)

        for b in self.player_bullets[:]:
            b.update()
            if (b.x < -50 or b.x > self.width + 50 or
                    b.y < -50 or b.y > self.height + 50):
                self.player_bullets.remove(b)

        for b in self.player_bullets[:]:
            bb = b.get_bbox()
            hit = False
            for enemy in self.enemies:
                if enemy.is_dying:
                    continue
                if self.check_collision(bb, enemy.get_bbox()):
                    enemy.start_dying()
                    hit = True
                    self.score += 1
                    break
            if hit:
                self.player_bullets.remove(b)

        player_bb = self.player.get_bbox()

        for sh in self.shields[:]:
            if self.check_collision(player_bb, sh.get_bbox()):
                if self.has_shield:
                    continue

                self.has_shield = True
                self.shields.remove(sh)

        if not self.invincible:
            for enemy in self.enemies:
                if enemy.is_dying:
                    continue
                if self.check_collision(player_bb, enemy.get_bbox()):
                    self.hit_player()
                    return

            for proj in self.projectiles[:]:
                if self.check_collision(player_bb, proj.get_bbox()):
                    if self.has_shield:
                        self.has_shield = False
                        self.projectiles.remove(proj)
                    else:
                        self.hit_player()
                        return

    def hit_player(self):
        self.has_shield = False
        self.lives -= 1

        if self.lives <= 0:
            self.end_game()
            return

        self.player.x = self.width // 2
        self.player.y = self.height - 50
        self.player.vx = 0
        self.player.vy = 0
        self.projectiles = []

        self.invincible = True
        self.blink_count = 10
        self.player.visible = True
        self.blink_player()

    def blink_player(self):
        self.player.visible = not self.player.visible
        self.blink_count -= 1

        if self.blink_count > 0:
            self.root.after(100, self.blink_player)
        else:
            self.player.visible = True
            self.invincible = False

    def flash_enemy_death(self, x, y, steps=6, delay=50):
        size = 20

        def step(i):
            if i >= steps:
                return

            color = "yellow" if i % 2 == 0 else "orange"
            oid = self.canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=color,
                outline=""
            )
            self.root.after(
                delay,
                lambda oid=oid, i=i: (self.canvas.delete(oid), step(i + 1))
            )
        step(0)


    def end_game(self):
        self.game_over = True
        self.running = False
        if self.score > self.best_score:
            self.best_score = self.score
            self.save_scores()

    def draw_all(self):
        line_y = self.height//4
        self.canvas.create_image(
            0, line_y,
            image=self.playfield_bg,
            anchor="nw"
        )
        for sh in self.shields:
            sh.draw()

        self.player.draw()

        if self.has_shield:
            r = max(self.player.width, self.player.height) // 2 + 10

            self.canvas.create_oval(
                self.player.x - r,
                self.player.y - r,
                self.player.x + r,
                self.player.y + r,
                outline="cyan",
                width=3
            )

        for enemy in self.enemies:
            enemy.draw()

        for proj in self.projectiles:
            proj.draw()

        for b in self.player_bullets:
            b.draw()

    def draw_bg(self):
        ...

    def draw_menu(self):
        frame = self.menu_bg_frames[self.menu_bg_index]
        self.canvas.create_image(0, 0, image=frame, anchor="nw")
        try:
            self.canvas.create_text(
                self.width // 2,
                self.height // 3,
                text="SPACE SHOOTER",
                fill="white",
                font=("Press Start 2P", 40),
                anchor="center"
            )
        except:
            pass
        x1, y1, x2, y2 = self.menu_button
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#aa0000",
            outline="yellow",
            width=3
        )
        self.canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text="START",
            fill="white",
            font=("Press Start 2P", 30),
            anchor="center"
        )

        cx1, cy1, cx2, cy2 = self.mode_button_classic
        hx1, hy1, hx2, hy2 = self.mode_button_hardcore

        if self.game_mode == "classic":
            classic_fill = "#00aa00"
            classic_outline = "white"
            hardcore_fill = "#333333"
            hardcore_outline = "gray"
        else:
            classic_fill = "#333333"
            classic_outline = "gray"
            hardcore_fill = "#aa5500"
            hardcore_outline = "white"

        self.canvas.create_rectangle(
            cx1, cy1, cx2, cy2,
            fill=classic_fill,
            outline=classic_outline,
            width=3
        )
        self.canvas.create_text(
            (cx1 + cx2) // 2,
            (cy1 + cy2) // 2,
            text="CLASSIC",
            fill="white",
            font=("Press Start 2P", 12)
        )

        self.canvas.create_rectangle(
            hx1, hy1, hx2, hy2,
            fill=hardcore_fill,
            outline=hardcore_outline,
            width=3
        )
        self.canvas.create_text(
            (hx1 + hx2) // 2,
            (hy1 + hy2) // 2,
            text="HARDCORE",
            fill="white",
            font=("Press Start 2P", 12)
        )

        rx1, ry1, rx2, ry2 = self.reset_score_button

        self.canvas.create_text(
            self.width // 2,
            ry1 - 25,
            text=f"NAJLEPSIE SKORE: {self.best_score}",
            fill="white",
            font=("Press Start 2P", 14),
            anchor="center"
        )

        self.canvas.create_rectangle(
            rx1, ry1, rx2, ry2,
            fill="#444444",
            outline="yellow",
            width=3
        )
        self.canvas.create_text(
            (rx1 + rx2) // 2,
            (ry1 + ry2) // 2,
            text="RESET",
            fill="white",
            font=("Press Start 2P", 12),
            anchor="center"
        )

        ix1, iy1, ix2, iy2 = self.info_button
        self.canvas.create_rectangle(
            ix1, iy1, ix2, iy2,
            fill="#333388",
            outline="yellow",
            width=3
        )
        self.canvas.create_text(
            (ix1 + ix2) // 2,
            (iy1 + iy2) // 2,
            text="INFO",
            fill="white",
            font=("Press Start 2P", 12),
            anchor="center"
        )

    def draw_about(self):
        frame = self.menu_bg_frames[self.menu_bg_index]
        self.canvas.create_image(0, 0, image=frame, anchor="nw")

        w = self.width * 0.6
        h = self.height * 0.6
        x1 = (self.width - w) // 2
        y1 = (self.height - h) // 2
        x2 = x1 + w
        y2 = y1 + h

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="black",
            outline="yellow",
            width=3
        )

        try:
            font_title = ("Press Start 2P", 20)
            font_text = ("Press Start 2P", 10)
        except:
            font_title = ("Arial", 20, "bold")
            font_text = ("Arial", 12)

        self.canvas.create_text(
            (x1 + x2) // 2,
            y1 + 40,
            text="O HRE",
            fill="white",
            font=font_title,
            anchor="center"
        )

        text_x = x1 + 40
        text_y = y1 + 80
        line_height = 20

        for i, line in enumerate(self.description_lines):
            if text_y + i * line_height > y2 - 80:
                break
            self.canvas.create_text(
                text_x,
                text_y + i * line_height,
                text=line,
                fill="white",
                font=font_text,
                anchor="nw"
            )

        btn_w = 200
        btn_h = 40
        bx1 = (x1 + x2) // 2 - btn_w // 2
        bx2 = bx1 + btn_w
        by2 = y2 - 40
        by1 = by2 - btn_h

        self.about_back_button = (bx1, by1, bx2, by2)

        self.canvas.create_rectangle(
            bx1, by1, bx2, by2,
            fill="#444444",
            outline="yellow",
            width=3
        )
        self.canvas.create_text(
            (bx1 + bx2) // 2,
            (by1 + by2) // 2,
            text="SPAT",
            fill="white",
            font=font_text,
            anchor="center"
        )

    def draw_outlined_text(self,canvas, x, y, text, fill="white", outline="black", width=2, **kwargs):
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx == 0 and dy == 0:
                    continue
                canvas.create_text(
                    x + dx,
                    y + dy,
                    text=text,
                    fill=outline,
                    **kwargs
                )
        canvas.create_text(
            x, y,
            text=text,
            fill=fill,
            **kwargs
        )

    def draw_hud(self):
        line_y = self.height // 4

        self.canvas.create_rectangle(0,0,self.width, line_y-50, fill="black")
        self.canvas.create_rectangle(0, line_y-50, self.width, line_y, fill="lightblue")

        for i in range(self.lives):
            x = 150 + i * 35
            y = line_y-40
            self.canvas.create_image(x, y, image=self.heart_image, anchor="nw")

        self.draw_outlined_text(
            self.canvas,
            80, line_y-22,
            text="ZIVOTY:",
            font=("Press Start 2P", 14),
            fill="red",
            outline="black"
        )

        self.draw_outlined_text(self.canvas,
            self.width // 2,
            self.height -(self.height-60),
            text="SPACE SHOOTER",
            fill="lightblue",
            font=("Press Start 2P", 40),
            anchor="center"
        )

        self.canvas.create_line(
            0, line_y,
            self.width, line_y, width=10,
            fill=None
        )
        if self.crosshair_active:
            cs = 10
            self.canvas.create_line(
                self.crosshair_x - cs, self.crosshair_y,
                self.crosshair_x + cs, self.crosshair_y,
                fill="red", width=2
            )
            self.canvas.create_line(
                self.crosshair_x, self.crosshair_y - cs,
                self.crosshair_x, self.crosshair_y + cs,
                fill="red", width=2
            )
            if self.game_mode != "hardcore":
                self.canvas.create_line(
                    self.player.x, self.player.y,
                    self.crosshair_x, self.crosshair_y,
                    dash=5, fill="yellow"
                )
        bar_width = 60
        bar_height = 8
        bar_x1 = self.player.x - bar_width // 2
        bar_y1 = self.player.y + self.player.height // 2
        bar_x2 = bar_x1 + bar_width
        bar_y2 = bar_y1 + bar_height

        self.canvas.create_rectangle(
            bar_x1, bar_y1,
            bar_x2, bar_y2,
            fill="gray20",
            outline="black",
            width=1
        )

        if self.max_fire_cooldown > 0:
            ratio = self.fire_cooldown / self.max_fire_cooldown
        else:
            ratio = 0

        fill_width = bar_width * ratio

        if self.fire_cooldown > 0:
            self.canvas.create_rectangle(
                bar_x1, bar_y1,
                bar_x1 + fill_width, bar_y2,
                fill="orange",
                outline=""
            )
        else:
            self.canvas.create_rectangle(
                bar_x1, bar_y1,
                bar_x2, bar_y2,
                fill="lime",
                outline=""
            )

        if self.fire_cooldown != 0:
            cd_text = str(self.fire_cooldown)
            cd_color = "white"

            self.draw_outlined_text(
            self.canvas,
            self.player.x,
            bar_y2 + 12,
            text=cd_text,
            fill=cd_color,
            outline="black",
            font=("Press Start 2P", 10),
            anchor="center"
        )


        self.draw_outlined_text(
            self.canvas,
            258, line_y-35,
            text=f"SCORE:{self.score}",
            anchor="nw",
            fill="white",
            outline="black",
            font=("Press Start 2P", 15)
        )
        self.draw_outlined_text(
            self.canvas,
            455, line_y-35,
            text=f"NAJLEPSIE:{self.best_score}",
            anchor="nw",
            fill="white",
            outline="black",
            font=("Press Start 2P", 15)
        )
        self.draw_outlined_text(
            self.canvas,
            self.width//2 - 100, line_y - 40,
            text=f"LEVEL {self.level}",
            anchor="nw",
            fill="orange",
            outline="black",
            font=("Press Start 2P", 20)
        )
        origin_y = self.height // 4
        local_x = int(self.player.x)-40
        local_y = int(self.player.y - origin_y)-40
        self.draw_outlined_text(
            self.canvas,
            self.width - 300, line_y - 35,
            text=f"PLAYER_X:{local_x}  PLAYER_Y:{local_y}",
            anchor="ne",
            fill="white",
            outline="black",
            font=("Press Start 2P", 12)
        )

        if not self.running and not self.game_over:
            x1 = self.width // 4
            y1 = self.height // 2 - 80
            x2 = 3 * self.width // 4
            y2 = self.height // 2 + 100

            offset = 5
            self.canvas.create_rectangle(
                x1 + offset, y1 + offset,
                x2 + offset, y2 + offset,
                fill="lightyellow",
                outline=""
            )
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#aa0000",
                outline="yellow",
                width=4
            )
            self.draw_outlined_text(
                self.canvas,
                (x1 + x2) // 2,
                y1 + 50,
                text="POZASTAVENE",
                fill="white",
                outline="black",
                font=("Press Start 2P", 30),
                anchor="center"
            )
            self.draw_outlined_text(
                self.canvas,
                (x1 + x2) // 2,
                y1 + 90,
                text="STLAC SPACE PRE POKRACOVANIE",
                fill="yellow",
                outline="black",
                font=("Press Start 2P", 12),
                anchor="center"
            )
            btn_w = 260
            btn_h = 40
            btn_x1 = (x1 + x2) // 2 - btn_w // 2
            btn_x2 = btn_x1 + btn_w
            btn_y1 = y1 + 130
            btn_y2 = btn_y1 + btn_h

            self.pause_exit_button = (btn_x1, btn_y1, btn_x2, btn_y2)

            self.canvas.create_rectangle(
                btn_x1, btn_y1, btn_x2, btn_y2,
                fill="#444444",
                outline="yellow",
                width=3
            )

            self.draw_outlined_text(
                self.canvas,
                (btn_x1 + btn_x2) // 2,
                (btn_y1 + btn_y2) // 2,
                text="UKONCI HRU",
                fill="white",
                outline="black",
                font=("Press Start 2P", 14),
                anchor="center"
            )

        else:
            self.pause_exit_button = None

        if self.game_over:
            self.canvas.create_text(
                self.width // 2, self.height // 2 - 30,
                text="HRA SKONCILA\n", fill="red", font=("Press Start 2P", 54, "bold")
            )
            self.canvas.create_text(
                self.width // 2, self.height // 2 + 20,
                text="klikni mysou pre restart",
                fill="white", font=("Press Start 2P", 20)
            )

Program()
