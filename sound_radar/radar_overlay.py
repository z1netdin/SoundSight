"""SoundSight overlay - draws sound indicators on screen edges.

Shows directional bars that grow with sound proximity.
Designed for peripheral vision during competitive gameplay.
"""

import math
import ctypes
import numpy as np
from typing import Optional

from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush,
    QPainterPath, QPolygonF, QFont,
)

from .audio_analyzer import DirectionalFrame, NUM_SEGMENTS
from .config import load_config, save_config

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
user32 = ctypes.windll.user32


class RadarOverlay(QWidget):
    new_frame_signal = pyqtSignal(object)

    def __init__(self, config=None):
        super().__init__()
        self.config = config if config is not None else load_config()
        self.current_frame: Optional[DirectionalFrame] = None
        self.visible = True
        self.locked = True

        self.display_levels = np.zeros(NUM_SEGMENTS, dtype=np.float32)
        self._pulse_phase = 0.0  # For subtle pulsing effect

        self._setup_window()
        self._setup_timer()
        self.new_frame_signal.connect(self._on_new_frame)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Use full screen - overlay covers everything
        # Works with any game mode (fullscreen, borderless, windowed)
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width(), screen.height())
        self.move(0, 0)

    def showEvent(self, event):
        super().showEvent(event)
        self._set_click_through(True)

    def _set_click_through(self, enabled):
        try:
            hwnd = int(self.winId())
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enabled:
                style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            else:
                style &= ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)

    def _setup_timer(self):
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._tick)
        interval = self.config.get("render_interval", 33)  # User configurable
        self.render_timer.start(interval)

    def _tick(self):
        if self.current_frame is not None:
            segments = self.current_frame.segments
            max_e = np.max(segments)

            if max_e > 1e-6:
                # Scale so loudness = bar size
                # Far enemy (quiet): small bar ~0.15-0.3
                # Close enemy (loud): big bar ~0.7-1.0
                # Deathmatch: closest = biggest, others smaller
                fixed_ref = 0.05
                target = np.clip(segments / fixed_ref, 0, 1)

                # Always show minimum size so distant enemies are visible
                target = np.where(target > 0.001, np.maximum(target, 0.15), 0.0)
            else:
                target = np.zeros(NUM_SEGMENTS)
                self.display_levels *= 0.95

            # Instant on, slow enough off that tap-tap-tap stays solid
            diff = target - self.display_levels
            rising = diff > 0
            falling = ~rising

            # Rise: instant
            self.display_levels[rising] = target[rising]
            # Fall: slow enough to hold between footstep taps (~0.5s hold)
            self.display_levels[falling] *= 0.96

            self.display_levels[self.display_levels < 0.04] = 0
        else:
            self.display_levels *= 0.95
            self.display_levels[self.display_levels < 0.04] = 0

        # Pulse phase - subtle breathing effect on active glows

        self._pulse_phase = (self._pulse_phase + 0.06) % (2 * math.pi)

        self.update()

    def add_event(self, frame: DirectionalFrame):
        self.new_frame_signal.emit(frame)

    def _on_new_frame(self, frame: DirectionalFrame):
        self.current_frame = frame

    def _get_edge_sounds(self):
        """Get all active sounds per edge with their position and intensity.
        Returns dict: edge -> list of (position 0-1, intensity)"""
        edges = {
            "top":    (315, 405),   # Front
            "right":  (60, 120),    # Side Right
            "bottom": (125, 235),   # Rear
            "left":   (240, 300),   # Side Left
        }
        result = {}
        for edge, (start_a, end_a) in edges.items():
            # Find the single loudest point on this edge
            peak = 0.0
            peak_deg = start_a

            for deg in range(start_a, end_a + 1):
                seg = deg % 360
                level = self.display_levels[seg]
                if level > peak:
                    peak = level
                    peak_deg = deg

            if peak > 0.05:
                pos = (peak_deg - start_a) / (end_a - start_a)
                result[edge] = [(pos, peak)]

        return result

    def _get_edge_peaks(self):
        """Legacy: get one peak per edge for other visual modes."""
        edges = [
            (315, 405, "top"), (60, 120, "right"),
            (125, 235, "bottom"), (240, 300, "left"),
        ]
        results = []
        for start_a, end_a, edge in edges:
            peak = 0.0
            best_deg = start_a
            for deg in range(start_a, end_a):
                seg = deg % 360
                if self.display_levels[seg] > peak:
                    peak = self.display_levels[seg]
                    best_deg = deg
            if peak < 0.05:
                continue
            peak_pos = (best_deg - start_a) / (end_a - start_a)
            results.append((edge, peak, peak_pos))
        return results

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()

        color = self.config.get("color", [0, 255, 140])
        r, g, b = color[0], color[1], color[2]

        mode = self.config.get("visual_mode", "edge_glow")

        # All modes use the same sound data
        edge_sounds = self._get_edge_sounds()
        # Convert to edge_peaks format: list of (edge, peak, position)
        edge_peaks = []
        for edge_name, sounds in edge_sounds.items():
            for pos, intensity in sounds:
                edge_peaks.append((edge_name, intensity, pos))

        if mode == "edge_glow":
            self._draw_mode_edge_glow(painter, w, h, r, g, b, None)
        elif mode == "pulse_flash":
            self._draw_mode_pulse_flash(painter, w, h, r, g, b, edge_peaks)
        elif mode == "screen_tint":
            self._draw_mode_screen_tint(painter, w, h, r, g, b, edge_peaks)
        elif mode == "warm_cool":
            self._draw_mode_warm_cool(painter, w, h, edge_peaks)
        elif mode == "vibration":
            self._draw_mode_vibration(painter, w, h, r, g, b, edge_peaks)
        elif mode == "crosshair_ring":
            self._draw_mode_crosshair_ring(painter, w, h, r, g, b, edge_peaks)
        elif mode == "crosshair_icons":
            pass  # Icons drawn below

        # Crosshair icons mode
        if mode == "crosshair_icons" and self.current_frame is not None and edge_peaks:
            cx = w / 2
            cy = h / 2
            ring_radius = 120  # distance from crosshair

    

            for edge, peak, pos in edge_peaks:
                if edge == "top":
                    angle = -90 + (pos - 0.5) * 180
                elif edge == "right":
                    angle = (pos - 0.5) * 180
                elif edge == "bottom":
                    angle = 90 + (pos - 0.5) * 180
                elif edge == "left":
                    angle = 180 + (pos - 0.5) * 180
                else:
                    continue

                angle_rad = math.radians(angle)

                # Distance from center based on loudness
                # Closer sound = closer to crosshair
                dist = ring_radius + (1.0 - peak) * 40  # 120-160px

                ix = cx + math.cos(angle_rad) * dist
                iy = cy + math.sin(angle_rad) * dist

                alpha = int(120 + 135 * peak)
                icon_size_val = 14 + peak * 12  # 14-26px

                # Draw arrow pointing toward the sound direction
                arrow_size = 10 + peak * 8
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(r, g, b, alpha)))

                # Triangle arrow pointing outward
                tip_x = cx + math.cos(angle_rad) * (dist + arrow_size)
                tip_y = cy + math.sin(angle_rad) * (dist + arrow_size)
                perp = angle_rad + math.pi / 2
                base1_x = ix + math.cos(perp) * arrow_size * 0.5
                base1_y = iy + math.sin(perp) * arrow_size * 0.5
                base2_x = ix - math.cos(perp) * arrow_size * 0.5
                base2_y = iy - math.sin(perp) * arrow_size * 0.5

                triangle = QPolygonF([
                    QPointF(tip_x, tip_y),
                    QPointF(base1_x, base1_y),
                    QPointF(base2_x, base2_y),
                ])
                painter.drawPolygon(triangle)

                # Center dot
                painter.drawEllipse(QPointF(ix, iy), 4, 4)

        painter.end()

    def _map_edge(self, edge):
        """Map split edge names to actual screen edge + position offset."""
        if edge == "top":
            return "top", 0.0, 1.0
        elif edge == "bottom":
            return "bottom", 0.0, 1.0
        elif edge == "left":
            return "left", 0.2, 0.8
        elif edge == "right":
            return "right", 0.2, 0.8
        return edge, 0.0, 1.0

    def _get_sound_color(self):
        """Get color based on current sound type."""
        # Color per sound type:
        #   Footsteps = green (default) - most common, need to see clearly
        #   Gunshots = red/orange - danger!
        #   Abilities = purple - magic/skill
        #   Spike = yellow - objective important
        #   Unknown = user's chosen color
        if self.current_frame and self.current_frame.sound_type:
            stype = self.current_frame.sound_type
            if stype == "movement":
                return (0, 255, 120)      # Green - footsteps
            elif stype == "gun":
                return (255, 60, 40)      # Red - gunshots
            elif stype == "ability":
                return (180, 60, 255)     # Purple - abilities
            elif stype == "objective":
                return (255, 220, 0)      # Yellow - spike plant/defuse
            elif stype == "action":
                return (255, 160, 0)      # Orange - reload, weapon drop
        return None  # Use default color

    def _draw_mode_edge_glow(self, painter, w, h, r, g, b, edge_peaks):
        """Edge indicator designed for deaf competitive gaming.

        Design principles:
        - Far: thin subtle line (just info, don't need to react yet)
        - Close: thick bright bar (REACT NOW, enemy is near)
        - Thickness AND length grow with closeness
        - Always visible in peripheral vision without looking
        - Zero clutter when no sounds
        """
        edge_sounds = self._get_edge_sounds()
        painter.setPen(Qt.NoPen)
        sr, sg, sb = r, g, b

        # User settings
        base_thick = int(self.config.get("line_thick", 14))
        max_len = int(self.config.get("line_max_len", 300))
        base_alpha = int(self.config.get("line_alpha", 200))

        for edge_name in ["top", "bottom", "left", "right"]:
            sounds = edge_sounds.get(edge_name, [])
            if not sounds:
                continue

            for pos, intensity in sounds:
                # Length: grows from center in steps
                STEP = max(10, max_len // 10)
                steps = max(1, min(10, int(intensity * 10)))
                bar_len = STEP * steps

                # Thickness: thin when far, thick when close
                # Far (intensity 0.1): base_thick * 0.4 = thin
                # Close (intensity 1.0): base_thick * 2.0 = fat
                thick = max(4, int(base_thick * (0.4 + intensity * 1.6)))

                # Alpha: dim when far, bright when close
                alpha = min(255, int(base_alpha * (0.5 + intensity * 0.5)))

                if edge_name == "top":
                    ix = pos * w - bar_len / 2
                    ix = max(0, min(ix, w - bar_len))
                    painter.setBrush(QBrush(QColor(sr, sg, sb, alpha)))
                    painter.drawRect(QRectF(ix, 0, bar_len, thick))

                elif edge_name == "bottom":
                    ix = pos * w - bar_len / 2
                    ix = max(0, min(ix, w - bar_len))
                    painter.setBrush(QBrush(QColor(sr, sg, sb, alpha)))
                    painter.drawRect(QRectF(ix, h - thick, bar_len, thick))

                elif edge_name == "right":
                    iy = pos * h - bar_len / 2
                    iy = max(0, min(iy, h - bar_len))
                    painter.setBrush(QBrush(QColor(sr, sg, sb, alpha)))
                    painter.drawRect(QRectF(w - thick, iy, thick, bar_len))

                elif edge_name == "left":
                    iy = pos * h - bar_len / 2
                    iy = max(0, min(iy, h - bar_len))
                    painter.setBrush(QBrush(QColor(sr, sg, sb, alpha)))
                    painter.drawRect(QRectF(0, iy, thick, bar_len))

    def _draw_mode_pulse_flash(self, painter, w, h, r, g, b, edge_peaks):
        """Mode 2: Bold flash bars on edges. High visibility."""
        painter.setPen(Qt.NoPen)
        for edge, peak, pos in edge_peaks:
            alpha = int(80 + 175 * peak)
            bar_thick = int(15 + peak * 30)
            bar_len = 0.05 + peak * 0.35
            bright = QColor(min(255, r+80), min(255, g+80), min(255, b+80), alpha)

            if edge == "top":
                bw = w * bar_len
                bx = max(0, min(pos * w - bw / 2, w - bw))
                painter.setBrush(QBrush(QColor(r, g, b, alpha)))
                painter.drawRect(QRectF(bx, 0, bw, bar_thick))
                painter.setBrush(QBrush(bright))
                painter.drawRect(QRectF(bx, 0, bw, 3))
            elif edge == "bottom":
                bw = w * bar_len
                bx = max(0, min(pos * w - bw / 2, w - bw))
                painter.setBrush(QBrush(QColor(r, g, b, alpha)))
                painter.drawRect(QRectF(bx, h - bar_thick, bw, bar_thick))
                painter.setBrush(QBrush(bright))
                painter.drawRect(QRectF(bx, h - 3, bw, 3))
            elif edge == "right":
                bh = h * bar_len
                by = max(0, min(pos * h - bh / 2, h - bh))
                painter.setBrush(QBrush(QColor(r, g, b, alpha)))
                painter.drawRect(QRectF(w - bar_thick, by, bar_thick, bh))
                painter.setBrush(QBrush(bright))
                painter.drawRect(QRectF(w - 3, by, 3, bh))
            elif edge == "left":
                bh = h * bar_len
                by = max(0, min(pos * h - bh / 2, h - bh))
                painter.setBrush(QBrush(QColor(r, g, b, alpha)))
                painter.drawRect(QRectF(0, by, bar_thick, bh))
                painter.setBrush(QBrush(bright))
                painter.drawRect(QRectF(0, by, 3, bh))

    def _draw_mode_screen_tint(self, painter, w, h, r, g, b, edge_peaks):
        """Mode 3: Entire edge side tints with color."""
        # Combine all sounds per edge into one tint
        edge_max = {}
        for edge, peak, pos in edge_peaks:
            edge_max[edge] = max(edge_max.get(edge, 0), peak)

        painter.setPen(Qt.NoPen)
        for edge, peak in edge_max.items():
            alpha = int(20 + 60 * peak)
            depth = max(10, int(w * 0.15 * peak))

            if edge == "top":
                grad = QLinearGradient(0, 0, 0, depth)
                grad.setColorAt(0, QColor(r, g, b, alpha))
                grad.setColorAt(1, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(0, 0, w, depth))
            elif edge == "bottom":
                grad = QLinearGradient(0, h, 0, h - depth)
                grad.setColorAt(0, QColor(r, g, b, alpha))
                grad.setColorAt(1, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(0, h - depth, w, depth))
            elif edge == "right":
                grad = QLinearGradient(w, 0, w - depth, 0)
                grad.setColorAt(0, QColor(r, g, b, alpha))
                grad.setColorAt(1, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(w - depth, 0, depth, h))
            elif edge == "left":
                grad = QLinearGradient(0, 0, depth, 0)
                grad.setColorAt(0, QColor(r, g, b, alpha))
                grad.setColorAt(1, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(0, 0, depth, h))

    def _draw_mode_warm_cool(self, painter, w, h, edge_peaks):
        """Mode 4: Warm/Cool - color changes with distance."""
        bar_thick = 20
        painter.setPen(Qt.NoPen)

        for edge, peak, pos in edge_peaks:
            if peak > 0.7:
                cr, cg, cb = 255, 60, 30
            elif peak > 0.5:
                cr, cg, cb = 255, 140, 30
            elif peak > 0.3:
                cr, cg, cb = 255, 220, 50
            elif peak > 0.15:
                cr, cg, cb = 50, 200, 255
            else:
                cr, cg, cb = 30, 100, 255

            bar_len = 0.05 + peak * 0.35

            if edge == "top":
                bw = w * bar_len
                bx = max(0, min(pos * w - bw / 2, w - bw))
                painter.setBrush(QBrush(QColor(cr, cg, cb, 230)))
                painter.drawRect(QRectF(bx, 0, bw, bar_thick))
            elif edge == "bottom":
                bw = w * bar_len
                bx = max(0, min(pos * w - bw / 2, w - bw))
                painter.setBrush(QBrush(QColor(cr, cg, cb, 230)))
                painter.drawRect(QRectF(bx, h - bar_thick, bw, bar_thick))
            elif edge == "right":
                bh = h * bar_len
                by = max(0, min(pos * h - bh / 2, h - bh))
                painter.setBrush(QBrush(QColor(cr, cg, cb, 230)))
                painter.drawRect(QRectF(w - bar_thick, by, bar_thick, bh))
            elif edge == "left":
                bh = h * bar_len
                by = max(0, min(pos * h - bh / 2, h - bh))
                painter.setBrush(QBrush(QColor(cr, cg, cb, 230)))
                painter.drawRect(QRectF(0, by, bar_thick, bh))

    def _draw_mode_vibration(self, painter, w, h, r, g, b, edge_peaks):
        """Mode 5: Vibration rings - pulsing circles from the edge."""
        pulse_phase = (self._pulse_phase / (2 * math.pi)) % 1.0

        for edge, peak, pos in edge_peaks:
            alpha_base = int(60 + 150 * peak)

            if edge == "top":
                cx = pos * w
                cy = 0
            elif edge == "bottom":
                cx = pos * w
                cy = h
            elif edge == "right":
                cx = w
                cy = pos * h
            elif edge == "left":
                cx = 0
                cy = pos * h
            else:
                continue

            # Draw concentric rings pulsing outward
            num_rings = 3 if peak > 0.3 else 2 if peak > 0.1 else 1
            max_radius = 30 + peak * 100

            painter.setBrush(Qt.NoBrush)
            for ring in range(num_rings):
                ring_phase = (pulse_phase + ring * 0.3) % 1.0
                ring_radius = ring_phase * max_radius
                ring_alpha = int(alpha_base * (1.0 - ring_phase))

                if ring_alpha < 5:
                    continue

                pen_width = max(1, int(3 * peak * (1.0 - ring_phase)))
                painter.setPen(QPen(QColor(r, g, b, ring_alpha), pen_width))
                painter.drawEllipse(QPointF(cx, cy), ring_radius, ring_radius)

            painter.setPen(Qt.NoPen)

            # Center dot
            dot_size = 3 + peak * 8
            painter.setBrush(QBrush(QColor(r, g, b, alpha_base)))
            painter.drawEllipse(QPointF(cx, cy), dot_size, dot_size)

    # _get_sound_color is defined above with the edge_glow drawing

    def _draw_mode_crosshair_ring(self, painter, w, h, r, g, b, edge_peaks):
        """Mode 6: Ring around crosshair. Different colors per sound type."""
        cx = w / 2
        cy = h / 2
        ring_radius = 80

        # Get sound-specific color
        sound_color = self._get_sound_color()

        for edge, peak, pos in edge_peaks:
            if edge == "top":
                angle = -90 + (pos - 0.5) * 180
            elif edge == "right":
                angle = (pos - 0.5) * 180
            elif edge == "bottom":
                angle = 90 + (pos - 0.5) * 180
            elif edge == "left":
                angle = 180 + (pos - 0.5) * 180
            else:
                continue

            alpha = int(80 + 175 * peak)
            arc_size = 20 + peak * 40
            arc_thick = 4 + peak * 12
            angle_rad = math.radians(angle)

            cr, cg, cb = r, g, b

            # Draw arc
            pen = QPen(QColor(cr, cg, cb, alpha), arc_thick)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            rect_size = ring_radius * 2
            rect_x = cx - ring_radius
            rect_y = cy - ring_radius
            start_angle = int((90 - angle - arc_size / 2) * 16)
            span_angle = int(arc_size * 16)
            painter.drawArc(int(rect_x), int(rect_y), int(rect_size), int(rect_size),
                           start_angle, span_angle)

            # Bright inner arc with same sound color
            if peak > 0.2:
                pen2 = QPen(QColor(min(255, cr+80), min(255, cg+80), min(255, cb+80),
                           int(alpha * 0.7)), max(2, arc_thick * 0.4))
                pen2.setCapStyle(Qt.RoundCap)
                painter.setPen(pen2)
                inner_r = ring_radius - arc_thick * 0.3
                painter.drawArc(int(cx - inner_r), int(cy - inner_r),
                               int(inner_r * 2), int(inner_r * 2),
                               start_angle, span_angle)

            painter.setPen(Qt.NoPen)

    def _draw_edge_glow(self, painter, w, h, edge, pos, spread, depth,
                         r, g, b, alpha):
        """Draw a smooth glow on one screen edge at a specific position.

        The glow is brightest at 'pos' and fades out in both directions
        along the edge, and fades inward from the edge.
        """
        painter.setPen(Qt.NoPen)

        # Number of strips to draw for smooth gradient along the edge
        strips = 30

        for i in range(strips):
            # Position of this strip relative to the peak (-1 to 1)
            t = (i / strips - 0.5) * 2  # -1 to 1
            # Offset from peak position
            strip_pos = pos + t * spread

            if strip_pos < -0.1 or strip_pos > 1.1:
                continue

            # Fade based on distance from peak (gaussian)
            fade = math.exp(-(t * t) / (2 * 0.3 * 0.3))
            strip_alpha = int(alpha * fade)

            if strip_alpha < 5:
                continue

            strip_depth = depth * fade
            strip_width = 1.0 / strips

            if edge == "top":
                x = strip_pos * w
                sw = w * strip_width * spread * 2 + 2

                grad = QLinearGradient(0, 0, 0, strip_depth)
                grad.setColorAt(0.0, QColor(r, g, b, strip_alpha))
                grad.setColorAt(0.4, QColor(r, g, b, int(strip_alpha * 0.3)))
                grad.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(x - sw / 2, 0, sw, strip_depth))

            elif edge == "bottom":
                x = strip_pos * w
                sw = w * strip_width * spread * 2 + 2

                grad = QLinearGradient(0, h, 0, h - strip_depth)
                grad.setColorAt(0.0, QColor(r, g, b, strip_alpha))
                grad.setColorAt(0.4, QColor(r, g, b, int(strip_alpha * 0.3)))
                grad.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(x - sw / 2, h - strip_depth, sw, strip_depth))

            elif edge == "right":
                y = strip_pos * h
                sh = h * strip_width * spread * 2 + 2

                grad = QLinearGradient(w, 0, w - strip_depth, 0)
                grad.setColorAt(0.0, QColor(r, g, b, strip_alpha))
                grad.setColorAt(0.4, QColor(r, g, b, int(strip_alpha * 0.3)))
                grad.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(w - strip_depth, y - sh / 2, strip_depth, sh))

            elif edge == "left":
                y = strip_pos * h
                sh = h * strip_width * spread * 2 + 2

                grad = QLinearGradient(0, 0, strip_depth, 0)
                grad.setColorAt(0.0, QColor(r, g, b, strip_alpha))
                grad.setColorAt(0.4, QColor(r, g, b, int(strip_alpha * 0.3)))
                grad.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setBrush(QBrush(grad))
                painter.drawRect(QRectF(0, y - sh / 2, strip_depth, sh))

    def _draw_sound_icon(self, painter, x, y, icon_type, r, g, b, alpha):
        """Draw a small icon representing the sound type."""
        # QPolygonF already imported at top
        color = QColor(r, g, b, alpha)
        size = 12

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))

        if icon_type == "footstep":
            # Boot shape
            s = size * 0.6
            path = QPainterPath()
            path.moveTo(x - s * 0.4, y + s * 0.6)
            path.lineTo(x + s * 0.5, y + s * 0.6)
            path.lineTo(x + s * 0.5, y + s * 0.2)
            path.lineTo(x + s * 0.2, y - s * 0.4)
            path.lineTo(x - s * 0.1, y - s * 0.6)
            path.lineTo(x - s * 0.3, y - s * 0.1)
            path.closeSubpath()
            painter.drawPath(path)

        elif icon_type == "gunshot":
            # Crosshair
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            s = size * 0.7
            painter.drawLine(QPointF(x - s, y), QPointF(x + s, y))
            painter.drawLine(QPointF(x, y - s), QPointF(x, y + s))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), 2, 2)

        elif icon_type == "smoke":
            # Cloud shape (3 circles)
            s = size * 0.4
            painter.setBrush(QBrush(QColor(r, g, b, int(alpha * 0.6))))
            painter.drawEllipse(QPointF(x - s, y), s, s * 0.8)
            painter.drawEllipse(QPointF(x + s * 0.5, y - s * 0.2), s * 0.9, s * 0.7)
            painter.drawEllipse(QPointF(x + s * 0.2, y + s * 0.3), s * 0.7, s * 0.6)

        elif icon_type == "flash":
            # Lightning bolt
            s = size * 0.7
            path = QPainterPath()
            path.moveTo(x + s * 0.1, y - s)
            path.lineTo(x - s * 0.3, y)
            path.lineTo(x + s * 0.1, y - s * 0.1)
            path.lineTo(x - s * 0.1, y + s)
            path.lineTo(x + s * 0.3, y)
            path.lineTo(x - s * 0.1, y + s * 0.1)
            path.closeSubpath()
            painter.drawPath(path)

        elif icon_type == "molly":
            # Flame
            s = size * 0.6
            path = QPainterPath()
            path.moveTo(x, y - s)
            path.cubicTo(x + s, y - s * 0.3, x + s * 0.5, y + s * 0.5, x, y + s)
            path.cubicTo(x - s * 0.5, y + s * 0.5, x - s, y - s * 0.3, x, y - s)
            painter.drawPath(path)

        elif icon_type in ("spike_plant", "spike_defuse"):
            # Arrow up (plant) or down (defuse)
            s = size * 0.7
            direction = -1 if icon_type == "spike_plant" else 1
            poly = QPolygonF([
                QPointF(x, y + direction * (-s)),
                QPointF(x - s * 0.6, y + direction * s * 0.3),
                QPointF(x - s * 0.2, y + direction * s * 0.3),
                QPointF(x - s * 0.2, y + direction * s),
                QPointF(x + s * 0.2, y + direction * s),
                QPointF(x + s * 0.2, y + direction * s * 0.3),
                QPointF(x + s * 0.6, y + direction * s * 0.3),
            ])
            painter.drawPolygon(poly)

        elif icon_type in ("teleport", "dash"):
            # Two parallel arrows
            s = size * 0.5
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(x - s, y - s * 0.3), QPointF(x + s, y - s * 0.3))
            painter.drawLine(QPointF(x - s, y + s * 0.3), QPointF(x + s, y + s * 0.3))
            # Arrow tips
            painter.drawLine(QPointF(x + s * 0.5, y - s * 0.7), QPointF(x + s, y - s * 0.3))
            painter.drawLine(QPointF(x + s * 0.5, y + s * 0.1), QPointF(x + s, y - s * 0.3))
            painter.setPen(Qt.NoPen)

        elif icon_type in ("scan", "drone"):
            # Eye / radar sweep
            s = size * 0.6
            painter.setBrush(QBrush(QColor(r, g, b, int(alpha * 0.5))))
            painter.drawEllipse(QPointF(x, y), s, s * 0.5)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), s * 0.3, s * 0.3)

        elif icon_type in ("stun", "slow"):
            # Spiral / star
            s = size * 0.6
            pen = QPen(color, 1.5)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(x, y), s, s)
            painter.drawEllipse(QPointF(x, y), s * 0.4, s * 0.4)
            painter.setPen(Qt.NoPen)

        elif icon_type == "wall":
            # Rectangle / barrier
            s = size * 0.6
            painter.drawRect(QRectF(x - s, y - s * 0.3, s * 2, s * 0.6))

        elif icon_type == "heal":
            # Cross / plus
            s = size * 0.5
            painter.drawRect(QRectF(x - s, y - s * 0.25, s * 2, s * 0.5))
            painter.drawRect(QRectF(x - s * 0.25, y - s, s * 0.5, s * 2))

        elif icon_type == "ultimate":
            # Diamond
            s = size * 0.7
            poly = QPolygonF([
                QPointF(x, y - s),
                QPointF(x + s * 0.6, y),
                QPointF(x, y + s),
                QPointF(x - s * 0.6, y),
            ])
            painter.drawPolygon(poly)

        elif icon_type == "reload":
            # Circular arrow
            s = size * 0.5
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(int(x - s), int(y - s), int(s * 2), int(s * 2), 30 * 16, 300 * 16)
            painter.setPen(Qt.NoPen)

        elif icon_type == "drop":
            # Arrow pointing down
            s = size * 0.6
            poly = QPolygonF([
                QPointF(x, y + s),
                QPointF(x - s * 0.5, y - s * 0.2),
                QPointF(x + s * 0.5, y - s * 0.2),
            ])
            painter.drawPolygon(poly)

        elif icon_type == "trap":
            # Triangle with exclamation
            s = size * 0.7
            poly = QPolygonF([
                QPointF(x, y - s),
                QPointF(x + s * 0.7, y + s * 0.5),
                QPointF(x - s * 0.7, y + s * 0.5),
            ])
            painter.drawPolygon(poly)

        else:
            # Generic circle
            painter.drawEllipse(QPointF(x, y), size * 0.5, size * 0.5)

    # --- Controls ---
    def toggle_lock(self):
        self.locked = not self.locked
        self._set_click_through(self.locked)
        print(f"[Radar] {'LOCKED' if self.locked else 'UNLOCKED'}")

    def toggle_visibility(self):
        self.visible = not self.visible
        if not self.visible:
            self.hide()
        else:
            self.show()

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self._menu(e.globalPos())

    def _menu(self, pos):
        m = QMenu(self)
        # Theme applied globally
        settings_action = m.addAction("Settings...")
        settings_action.triggered.connect(self._open_settings)
        m.addSeparator()
        m.addAction("Quit").triggered.connect(QApplication.quit)
        m.exec_(pos)

    def _open_settings(self):
        from .settings_panel import SettingsPanel
        if not hasattr(self, '_settings') or self._settings is None or not self._settings.isVisible():
            self._settings = SettingsPanel(self.config, self)
            self._settings.settings_changed.connect(self._on_settings_changed)
            self._settings.show()
        else:
            self._settings.raise_()

    def _on_settings_changed(self):
        pass
