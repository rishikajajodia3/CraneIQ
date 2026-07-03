
import pygame
import time
import math
import random


class OperatorInput:
    """
    Captures keyboard input from a Pygame window and maps
    key presses to crane operator actions while rendering a
    first-person crane cabin simulator.
    """

    KEY_MAPPING = {
        pygame.K_w: "BOOM_UP",
        pygame.K_s: "BOOM_DOWN",
        pygame.K_a: "SWING_LEFT",
        pygame.K_d: "SWING_RIGHT",
        pygame.K_SPACE: "STOP",
        pygame.K_h: "HOIST",
    }

    def __init__(self, width=900, height=620):
        pygame.init()

        self.width = max(width, 900)
        self.height = max(height, 620)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("CraneIQ — First-Person Crane Cabin Simulator")

        self.running = True
        self.latest_action = None
        self.latest_timestamp = None

        # Crane physical state
        self.boom_angle = 15.0        # Elevation from horizontal (5 to 40 degrees)
        self.swing_angle = 0.0        # Azimuth rotation (0 to 360)
        self.hoist_len = 120.0        # Cable length in pixels (50 to 250)
        self.hoist_direction = 1
        self.emergency_stop = False
        self.start_time = time.time()

        # Viewport geometry
        self.view_top = 0
        self.view_bottom = self.height - 170   # Dashboard starts here
        self.view_height = self.view_bottom - self.view_top
        self.horizon_base = self.view_top + int(self.view_height * 0.38)

        # Generate random city skyline (heights relative to horizon)
        random.seed(42)
        self.buildings = []
        x = 0
        while x < 3600:    # Wide enough for full 360 rotation
            w = random.randint(20, 55)
            h = random.randint(30, 130)
            shade = random.randint(35, 70)
            windows = random.choice([True, False, True])
            self.buildings.append((x, w, h, shade, windows))
            x += w + random.randint(2, 8)
        self.city_width = x

        # Fonts
        self.font_title = pygame.font.SysFont("Consolas", 16, bold=True)
        self.font_large = pygame.font.SysFont("Consolas", 28, bold=True)
        self.font_medium = pygame.font.SysFont("Consolas", 14, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 11)
        self.font_hud = pygame.font.SysFont("Consolas", 13, bold=True)

        # Colors
        self.col_sky_top = (15, 25, 50)
        self.col_sky_bottom = (40, 65, 110)
        self.col_ground_near = (55, 50, 40)
        self.col_ground_far = (40, 38, 32)
        self.col_steel = (170, 180, 195)
        self.col_yellow = (245, 180, 30)
        self.col_green = (16, 185, 129)
        self.col_red = (220, 50, 50)
        self.col_cyan = (14, 165, 233)
        self.col_muted = (100, 110, 125)
        self.col_dash_bg = (18, 20, 25)
        self.col_dash_border = (50, 55, 65)
        self.col_cabin_frame = (45, 42, 38)

    def update(self):
        """
        Process keyboard events and update crane kinematics.

        Returns
        -------
        tuple(str | None, float | None)
        """

        action = None
        timestamp = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                action = self.KEY_MAPPING.get(event.key)
                if action:
                    timestamp = time.time()
                    self.latest_action = action
                    self.latest_timestamp = timestamp

                    if action == "STOP":
                        self.emergency_stop = True
                    else:
                        self.emergency_stop = False

                    print(f"[Operator Cabin] {action}")

        # Smooth kinematics on key hold
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.boom_angle = min(40.0, self.boom_angle + 0.4)
            self.latest_action = "BOOM_UP"
            self.emergency_stop = False
        elif keys[pygame.K_s]:
            self.boom_angle = max(5.0, self.boom_angle - 0.4)
            self.latest_action = "BOOM_DOWN"
            self.emergency_stop = False

        if keys[pygame.K_a]:
            self.swing_angle = (self.swing_angle - 1.2) % 360.0
            self.latest_action = "SWING_LEFT"
            self.emergency_stop = False
        elif keys[pygame.K_d]:
            self.swing_angle = (self.swing_angle + 1.2) % 360.0
            self.latest_action = "SWING_RIGHT"
            self.emergency_stop = False

        if keys[pygame.K_h]:
            self.latest_action = "HOIST"
            self.emergency_stop = False
            self.hoist_len += self.hoist_direction * 1.5
            if self.hoist_len > 250.0 or self.hoist_len < 50.0:
                self.hoist_direction *= -1

        if keys[pygame.K_SPACE]:
            self.latest_action = "STOP"
            self.emergency_stop = True

        self._draw()

        return action, timestamp

    # ------------------------------------------------------------------
    # DRAWING — First-Person View
    # ------------------------------------------------------------------

    def _draw_sky(self):
        """Gradient sky filling the viewport above the horizon."""
        for y in range(self.view_top, self.horizon_base):
            t = (y - self.view_top) / max(1, self.horizon_base - self.view_top)
            r = int(self.col_sky_top[0] + (self.col_sky_bottom[0] - self.col_sky_top[0]) * t)
            g = int(self.col_sky_top[1] + (self.col_sky_bottom[1] - self.col_sky_top[1]) * t)
            b = int(self.col_sky_top[2] + (self.col_sky_bottom[2] - self.col_sky_top[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

    def _draw_ground(self):
        """Perspective ground plane below the horizon with grid lines."""
        for y in range(self.horizon_base, self.view_bottom):
            t = (y - self.horizon_base) / max(1, self.view_bottom - self.horizon_base)
            r = int(self.col_ground_far[0] + (self.col_ground_near[0] - self.col_ground_far[0]) * t)
            g = int(self.col_ground_far[1] + (self.col_ground_near[1] - self.col_ground_far[1]) * t)
            b = int(self.col_ground_far[2] + (self.col_ground_near[2] - self.col_ground_far[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

        # Perspective grid on the ground
        cx = self.width // 2
        swing_offset = self.swing_angle * 3.0
        for i in range(-8, 9):
            # Vertical lines that converge at horizon
            base_x = cx + i * 110 - int(swing_offset) % 110
            pygame.draw.line(
                self.screen, (60, 55, 48),
                (base_x, self.view_bottom),
                (cx + (base_x - cx) // 6, self.horizon_base), 1
            )

        # Horizontal grid lines (closer = wider spacing)
        for j in range(1, 7):
            gy = self.horizon_base + int((self.view_bottom - self.horizon_base) * (j / 7.0) ** 1.5)
            pygame.draw.line(self.screen, (58, 53, 46), (0, gy), (self.width, gy), 1)

    def _draw_cityscape(self):
        """Scrolling city skyline that moves with swing rotation."""
        # Convert swing angle to pixel offset into the city strip
        scroll = (self.swing_angle / 360.0) * self.city_width

        for bx, bw, bh, shade, has_windows in self.buildings:
            # Position relative to the scrolling viewport
            screen_x = bx - scroll
            # Wrap around
            if screen_x < -bw - 100:
                screen_x += self.city_width
            if screen_x > self.width + 100:
                screen_x -= self.city_width

            # Still off-screen after wrapping? Skip.
            if screen_x + bw < -50 or screen_x > self.width + 50:
                continue

            building_top = self.horizon_base - bh
            col = (shade, shade + 5, shade + 12)

            pygame.draw.rect(self.screen, col,
                             (int(screen_x), building_top, bw, bh))
            # Building edge highlight
            pygame.draw.line(self.screen, (shade + 20, shade + 22, shade + 28),
                             (int(screen_x), building_top),
                             (int(screen_x), self.horizon_base), 1)

            # Windows
            if has_windows and bw > 18:
                for wy in range(building_top + 6, self.horizon_base - 6, 12):
                    for wx in range(int(screen_x) + 4, int(screen_x) + bw - 4, 10):
                        glow = random.Random(wx * 1000 + wy).randint(0, 3)
                        if glow < 2:
                            wc = (180, 160, 80) if glow == 0 else (100, 140, 180)
                            pygame.draw.rect(self.screen, wc, (wx, wy, 5, 6))

    def _draw_boom_fp(self):
        """
        Draw the boom arm in first-person perspective extending from the
        bottom-center of the viewport outward toward the horizon.
        The boom angle controls how high above the horizon the tip goes.
        """
        cx = self.width // 2
        # Boom base: bottom center of viewport (where cabin roof meets the view)
        base_y = self.view_bottom - 5
        base_x = cx

        # Boom tip: projects toward horizon center, angled upward
        boom_screen_len = self.view_height * 0.75
        tip_y = self.horizon_base - int(math.tan(math.radians(self.boom_angle)) * boom_screen_len * 0.4)
        tip_x = cx     # Boom always points straight ahead in FPV

        # Perspective: boom gets narrower toward the tip
        base_half_w = 18
        tip_half_w = 4

        # Boom truss — left and right chords
        pygame.draw.line(self.screen, self.col_yellow,
                         (base_x - base_half_w, base_y),
                         (tip_x - tip_half_w, tip_y), 3)
        pygame.draw.line(self.screen, self.col_yellow,
                         (base_x + base_half_w, base_y),
                         (tip_x + tip_half_w, tip_y), 3)

        # Cross-bracing along the boom
        num_segments = 10
        for i in range(num_segments + 1):
            t = i / num_segments
            lx = int(base_x - base_half_w + (tip_x - tip_half_w - base_x + base_half_w) * t)
            rx = int(base_x + base_half_w + (tip_x + tip_half_w - base_x - base_half_w) * t)
            sy = int(base_y + (tip_y - base_y) * t)

            # Horizontal rung
            pygame.draw.line(self.screen, (200, 180, 60), (lx, sy), (rx, sy), 1)

            # Diagonal bracing
            if i < num_segments:
                t2 = (i + 1) / num_segments
                lx2 = int(base_x - base_half_w + (tip_x - tip_half_w - base_x + base_half_w) * t2)
                rx2 = int(base_x + base_half_w + (tip_x + tip_half_w - base_x - base_half_w) * t2)
                sy2 = int(base_y + (tip_y - base_y) * t2)
                pygame.draw.line(self.screen, (180, 165, 50), (lx, sy), (rx2, sy2), 1)
                pygame.draw.line(self.screen, (180, 165, 50), (rx, sy), (lx2, sy2), 1)

        # Trolley at about 70% along the boom
        trolley_t = 0.72
        trolley_x = cx
        trolley_y = int(base_y + (tip_y - base_y) * trolley_t)
        trolley_hw = int(base_half_w + (tip_half_w - base_half_w) * trolley_t)
        pygame.draw.rect(self.screen, self.col_red,
                         (trolley_x - trolley_hw - 2, trolley_y - 3,
                          (trolley_hw + 2) * 2, 6))

        # Hoist cable hanging from trolley
        cable_bottom_y = trolley_y + int(self.hoist_len * 0.7)
        # Clamp so it doesn't go below ground
        cable_bottom_y = min(cable_bottom_y, self.view_bottom - 20)

        pygame.draw.line(self.screen, (200, 200, 200),
                         (trolley_x, trolley_y + 3),
                         (trolley_x, cable_bottom_y), 2)

        # Hook block
        hk_y = cable_bottom_y
        pygame.draw.rect(self.screen, self.col_yellow,
                         (trolley_x - 6, hk_y, 12, 7))
        pygame.draw.arc(self.screen, self.col_steel,
                        (trolley_x - 5, hk_y + 5, 10, 12),
                        math.radians(180), math.radians(360), 2)

        # Cargo container
        cargo_top = hk_y + 15
        if cargo_top + 18 < self.view_bottom - 10:
            # Perspective: container gets smaller the higher up
            depth_factor = max(0.3, 1.0 - (self.view_bottom - cargo_top) / self.view_height * 0.6)
            cw = int(28 * depth_factor)
            ch = int(18 * depth_factor)
            pygame.draw.rect(self.screen, (180, 70, 40),
                             (trolley_x - cw // 2, cargo_top, cw, ch))
            pygame.draw.rect(self.screen, self.col_yellow,
                             (trolley_x - cw // 2, cargo_top, cw, ch), 1)

        return tip_x, tip_y, trolley_x, trolley_y

    def _draw_cabin_frame(self):
        """
        Draw the cabin window frame — thick dark borders simulating
        the steel frame of the crane cabin windshield you're looking through.
        """
        frame_col = self.col_cabin_frame
        thick = 22

        # Left pillar
        pygame.draw.rect(self.screen, frame_col, (0, 0, thick, self.view_bottom))
        # Right pillar
        pygame.draw.rect(self.screen, frame_col,
                         (self.width - thick, 0, thick, self.view_bottom))
        # Top beam
        pygame.draw.rect(self.screen, frame_col, (0, 0, self.width, thick))

        # Center vertical strut (thin)
        strut_w = 4
        pygame.draw.rect(self.screen, frame_col,
                         (self.width // 2 - strut_w // 2, 0,
                          strut_w, thick + 8))

        # Inner edge highlights to simulate depth
        highlight = (65, 60, 52)
        pygame.draw.line(self.screen, highlight, (thick, thick), (thick, self.view_bottom), 1)
        pygame.draw.line(self.screen, highlight,
                         (self.width - thick, thick),
                         (self.width - thick, self.view_bottom), 1)
        pygame.draw.line(self.screen, highlight, (thick, thick), (self.width - thick, thick), 1)

        # Small rivets on the frame
        for ry in range(40, self.view_bottom, 60):
            pygame.draw.circle(self.screen, (70, 65, 55), (8, ry), 2)
            pygame.draw.circle(self.screen, (70, 65, 55), (self.width - 8, ry), 2)

    def _draw_hud_overlay(self):
        """Heads-up display elements drawn on the windshield glass."""
        # Crosshair at center
        cx, cy = self.width // 2, self.horizon_base
        ch_col = (80, 200, 80, 120)
        pygame.draw.line(self.screen, (80, 200, 80), (cx - 20, cy), (cx - 6, cy), 1)
        pygame.draw.line(self.screen, (80, 200, 80), (cx + 6, cy), (cx + 20, cy), 1)
        pygame.draw.line(self.screen, (80, 200, 80), (cx, cy - 20), (cx, cy - 6), 1)
        pygame.draw.line(self.screen, (80, 200, 80), (cx, cy + 6), (cx, cy + 20), 1)

        # Compass heading at top
        heading_txt = f"HDG {self.swing_angle:05.1f}"
        hs = self.font_hud.render(heading_txt, True, self.col_cyan)
        self.screen.blit(hs, (cx - hs.get_width() // 2, 28))

        # Boom angle indicator on left
        boom_txt = f"ELEV {self.boom_angle:.1f}"
        bs = self.font_hud.render(boom_txt, True, self.col_cyan)
        self.screen.blit(bs, (30, self.horizon_base - 10))

        # Hoist depth on right
        hoist_m = self.hoist_len / 10.0
        ht = self.font_hud.render(f"CABLE {hoist_m:.1f}m", True, self.col_cyan)
        self.screen.blit(ht, (self.width - 30 - ht.get_width(), self.horizon_base - 10))

    def _draw_dashboard(self):
        """
        Dashboard cockpit panel at the bottom of the screen with
        gauges, status readouts, and interactive control buttons.
        """
        dash_y = self.view_bottom
        dash_h = self.height - dash_y

        # Dashboard background
        pygame.draw.rect(self.screen, self.col_dash_bg,
                         (0, dash_y, self.width, dash_h))
        # Top edge — metallic strip
        pygame.draw.rect(self.screen, (70, 68, 62),
                         (0, dash_y, self.width, 3))
        pygame.draw.line(self.screen, (90, 85, 75),
                         (0, dash_y + 1), (self.width, dash_y + 1), 1)

        # ----- Left section: Telemetry Gauges -----
        gauge_x = 20
        gauge_y = dash_y + 14
        gauge_w = 230

        self._draw_dash_gauge(gauge_x, gauge_y, gauge_w, "BOOM ELEVATION",
                              self.boom_angle, 5.0, 40.0, self.col_cyan)
        self._draw_dash_gauge(gauge_x, gauge_y + 36, gauge_w, "HOIST CABLE",
                              self.hoist_len / 10.0, 5.0, 25.0, self.col_cyan)
        self._draw_dash_gauge(gauge_x, gauge_y + 72, gauge_w, "SWING AZIMUTH",
                              self.swing_angle, 0.0, 360.0, self.col_cyan)
        # Load gauge
        load_col = self.col_green if not self.emergency_stop else self.col_red
        self._draw_dash_gauge(gauge_x, gauge_y + 108, gauge_w, "HOOK LOAD",
                              14.2, 0.0, 25.0, load_col)

        # ----- Center section: Status Banner -----
        banner_x = 270
        banner_w = self.width - 540
        banner_rect = pygame.Rect(banner_x, dash_y + 12, banner_w, 30)

        if self.emergency_stop:
            b_bg = (120, 15, 15)
            b_border = self.col_red
            b_txt_col = (255, 255, 255)
            b_text = "EMERGENCY STOP ACTIVE"
        elif self.latest_action:
            b_bg = (12, 35, 22)
            b_border = self.col_green
            b_txt_col = self.col_green
            b_text = f"ACTIVE: {self.latest_action}"
        else:
            b_bg = (25, 28, 35)
            b_border = self.col_dash_border
            b_txt_col = self.col_muted
            b_text = "STANDBY — AWAITING SIGNAL"

        pygame.draw.rect(self.screen, b_bg, banner_rect)
        pygame.draw.rect(self.screen, b_border, banner_rect, 1)
        bt = self.font_medium.render(b_text, True, b_txt_col)
        self.screen.blit(bt, (banner_rect.centerx - bt.get_width() // 2,
                              banner_rect.centery - bt.get_height() // 2))

        # Compass display below banner
        comp_cx = banner_x + banner_w // 2
        comp_cy = dash_y + 75
        comp_r = 28
        pygame.draw.circle(self.screen, (25, 30, 40), (comp_cx, comp_cy), comp_r)
        pygame.draw.circle(self.screen, self.col_dash_border, (comp_cx, comp_cy), comp_r, 1)

        # Cardinal labels
        for label, angle in [("N", 0), ("E", 90), ("S", 180), ("W", 270)]:
            a = math.radians(angle - 90)
            lx = comp_cx + int((comp_r - 8) * math.cos(a))
            ly = comp_cy + int((comp_r - 8) * math.sin(a))
            ls = self.font_small.render(label, True, self.col_muted)
            self.screen.blit(ls, (lx - ls.get_width() // 2, ly - ls.get_height() // 2))

        # Needle showing current heading
        needle_a = math.radians(self.swing_angle - 90)
        nx = comp_cx + int((comp_r - 3) * math.cos(needle_a))
        ny = comp_cy + int((comp_r - 3) * math.sin(needle_a))
        pygame.draw.line(self.screen, self.col_red, (comp_cx, comp_cy), (nx, ny), 2)
        pygame.draw.circle(self.screen, self.col_yellow, (comp_cx, comp_cy), 3)

        # Runtime timer below compass
        elapsed = int(time.time() - self.start_time)
        ts = self.font_small.render(
            f"RUNTIME {elapsed // 60:02d}:{elapsed % 60:02d}",
            True, self.col_muted)
        self.screen.blit(ts, (comp_cx - ts.get_width() // 2, comp_cy + comp_r + 6))

        # System status line
        if self.emergency_stop:
            stat_col = self.col_red
            stat_txt = "SYS: BRAKES ENGAGED"
        else:
            stat_col = self.col_green
            stat_txt = "SYS: OPERATIONAL"
        ss = self.font_small.render(stat_txt, True, stat_col)
        self.screen.blit(ss, (comp_cx - ss.get_width() // 2, comp_cy + comp_r + 22))

        # ----- Right section: Control Buttons -----
        btn_x = self.width - 250
        btn_y = dash_y + 12

        buttons = [
            ("BOOM_UP", "[W] BOOM UP", pygame.K_w),
            ("BOOM_DOWN", "[S] BOOM DOWN", pygame.K_s),
            ("SWING_LEFT", "[A] SWING LEFT", pygame.K_a),
            ("SWING_RIGHT", "[D] SWING RIGHT", pygame.K_d),
            ("HOIST", "[H] HOIST", pygame.K_h),
            ("STOP", "[SPACE] E-STOP", pygame.K_SPACE),
        ]

        keys_pressed = pygame.key.get_pressed()
        cols = 2
        btn_w = 110
        btn_h = 24

        for idx, (act, label, key_code) in enumerate(buttons):
            r = idx // cols
            c = idx % cols
            bx = btn_x + c * (btn_w + 8)
            by = btn_y + r * (btn_h + 6)
            br = pygame.Rect(bx, by, btn_w, btn_h)

            is_active = (self.latest_action == act) or keys_pressed[key_code]
            if is_active:
                if act == "STOP":
                    bg, border, txt = (140, 20, 20), (255, 80, 80), (255, 255, 255)
                else:
                    bg, border, txt = (12, 50, 32), self.col_green, self.col_green
            else:
                bg, border, txt = (25, 28, 35), (45, 50, 58), self.col_steel

            pygame.draw.rect(self.screen, bg, br)
            pygame.draw.rect(self.screen, border, br, 1 if not is_active else 2)

            ls = self.font_small.render(label, True, txt)
            self.screen.blit(ls, (br.centerx - ls.get_width() // 2,
                                  br.centery - ls.get_height() // 2))

    def _draw_dash_gauge(self, x, y, w, label, val, vmin, vmax, color):
        """Small horizontal gauge for the dashboard."""
        # Label
        ls = self.font_small.render(label, True, self.col_muted)
        self.screen.blit(ls, (x, y))
        # Value
        vs = self.font_small.render(f"{val:.1f}", True, color)
        self.screen.blit(vs, (x + w - vs.get_width(), y))
        # Bar
        bar_y = y + 15
        bar_h = 6
        pygame.draw.rect(self.screen, (12, 14, 18), (x, bar_y, w, bar_h))
        ratio = max(0.0, min(1.0, (val - vmin) / max(0.001, vmax - vmin)))
        fill = int(w * ratio)
        if fill > 0:
            pygame.draw.rect(self.screen, color, (x, bar_y, fill, bar_h))
        pygame.draw.rect(self.screen, self.col_dash_border, (x, bar_y, w, bar_h), 1)

    def _draw(self):
        """Draw the complete first-person crane cabin view."""
        self.screen.fill((0, 0, 0))

        # 1. Sky
        self._draw_sky()
        # 2. City skyline (scrolls with swing)
        self._draw_cityscape()
        # 3. Ground plane
        self._draw_ground()
        # 4. Boom arm in first-person perspective
        self._draw_boom_fp()
        # 5. Cabin window frame overlay
        self._draw_cabin_frame()
        # 6. HUD overlay on windshield
        self._draw_hud_overlay()
        # 7. Dashboard cockpit panel
        self._draw_dashboard()

        pygame.display.flip()

    def close(self):
        pygame.quit()


if __name__ == "__main__":
    operator = OperatorInput(width=900, height=620)
    clock = pygame.time.Clock()

    print("=== CraneIQ First-Person Crane Cabin Simulator ===")
    print("W/S = Boom Up/Down | A/D = Swing Left/Right | H = Hoist | SPACE = E-Stop")

    while operator.running:
        action, timestamp = operator.update()
        if action:
            print({"action": action, "timestamp": timestamp})
        clock.tick(60)

    operator.close()