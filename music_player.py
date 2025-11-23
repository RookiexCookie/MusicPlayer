import sys
import os
import re
import math
from mutagen import File
from mutagen.id3 import ID3
import syncedlyrics

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QSlider, QListWidget, 
                             QListWidgetItem, QFileDialog, QGraphicsBlurEffect, 
                             QFrame, QSplitter, QLineEdit, QStackedWidget, QAbstractItemView, QSizePolicy, QStyle)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QSize, QPoint, QTimer, QRect
from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter, QPainterPath, QBrush, QPen, QLinearGradient, QAction

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- THEMES ---
DEFAULT_THEME = {
    "bg": "#121212", "player": "#181818", "sidebar": "#000000",
    "accent": "#1DB954", "text": "#FFFFFF", "dim": "#B3B3B3", "hover": "#282828"
}

THEMES = {
    "Spotify": DEFAULT_THEME,
    "Cyberpunk": {
        "bg": "#0b0c15", "player": "#151621", "sidebar": "#05060a",
        "accent": "#ff007f", "text": "#e0e0e0", "dim": "#8a8a9b", "hover": "#1f202e"
    },
    "Ocean": {
        "bg": "#0f172a", "player": "#1e293b", "sidebar": "#020617",
        "accent": "#38bdf8", "text": "#f8fafc", "dim": "#94a3b8", "hover": "#334155"
    },
    "Dracula": {
        "bg": "#282a36", "player": "#44475a", "sidebar": "#21222c",
        "accent": "#bd93f9", "text": "#f8f8f2", "dim": "#6272a4", "hover": "#44475a"
    },
    "Sunset": {
        "bg": "#2d1b2e", "player": "#452c48", "sidebar": "#1f1020",
        "accent": "#ff9e64", "text": "#ffd7c4", "dim": "#b07e86", "hover": "#5e3e61"
    },
    "Forest": {
        "bg": "#1a2f23", "player": "#243e30", "sidebar": "#0f1c15",
        "accent": "#73d98d", "text": "#e8f5e9", "dim": "#81c784", "hover": "#2f523e"
    },
    "Royal": {
        "bg": "#181026", "player": "#261a3b", "sidebar": "#0e0917",
        "accent": "#d4af37", "text": "#f2e6ff", "dim": "#8c7ae6", "hover": "#362452"
    }
}

def get_safe_color(pixmap):
    """Extracts color but ensures it's readable (High Brightness/Saturation)."""
    if not pixmap: return QColor("#1DB954")
    
    img = pixmap.toImage().scaled(1, 1) # Scale to 1 pixel
    col = img.pixelColor(0, 0)
    
    # Convert to HSL to manipulate brightness/saturation
    h, s, l, a = col.getHsl()
    
    # Force Saturation high (colorful)
    if s < 100: s = 150
    
    # Force Lightness high (readable on dark bg)
    if l < 130: l = 160 
    elif l > 220: l = 200 # Cap it so it's not pure white
    
    return QColor.fromHsl(h, s, l, a)

# --- CUSTOM SLIDER ---
class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width())
            self.setValue(val)
            self.sliderMoved.emit(val) # Notify parent
        super().mousePressEvent(event)

# --- WORKER ---
class LyricsWorker(QThread):
    lyrics_found = pyqtSignal(list)
    def __init__(self, track, artist):
        super().__init__()
        self.track, self.artist = track, artist
    def run(self):
        try:
            t = re.sub(r'\s*[\(\[].*?[\)\]]', '', self.track)
            term = f"{t} {self.artist}"
            lrc = syncedlyrics.search(term)
            self.lyrics_found.emit(self.parse(lrc))
        except: self.lyrics_found.emit([])
    def parse(self, lrc):
        data = []
        if not lrc: return data
        for line in lrc.split('\n'):
            m = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', line)
            if m:
                ms = (int(m.group(1))*60000) + (int(m.group(2))*1000) + (int(m.group(3))*10)
                if m.group(4).strip(): data.append((ms, m.group(4).strip()))
        return data

# --- CUSTOM WIDGETS ---
class TitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0)
        self.layout.addStretch()
        self.btn_min = self.create_btn("—"); self.btn_min.clicked.connect(parent.showMinimized)
        self.btn_max = self.create_btn("□"); self.btn_max.clicked.connect(self.toggle_max)
        self.btn_close = self.create_btn("✕", hover_color="#ff5555"); self.btn_close.clicked.connect(parent.close)
        self.layout.addWidget(self.btn_min); self.layout.addWidget(self.btn_max); self.layout.addWidget(self.btn_close)
        self.start = QPoint(0, 0); self.pressing = False
    def create_btn(self, text, hover_color="#444444"):
        btn = QPushButton(text); btn.setFixedSize(30, 30)
        btn.setStyleSheet(f"QPushButton {{ border: none; color: #B3B3B3; font-weight: bold; background: transparent; border-radius: 4px; }} QPushButton:hover {{ background-color: {hover_color}; color: white; }}")
        return btn
    def toggle_max(self):
        if self.parent.isMaximized(): self.parent.showNormal()
        else: self.parent.showMaximized()
    def mousePressEvent(self, event): self.start = self.mapToGlobal(event.pos()); self.pressing = True
    def mouseMoveEvent(self, event):
        if self.pressing:
            end = self.mapToGlobal(event.pos()); movement = end - self.start
            self.parent.setGeometry(self.parent.x() + movement.x(), self.parent.y() + movement.y(), self.parent.width(), self.parent.height())
            self.start = end
    def mouseReleaseEvent(self, event): self.pressing = False

class RotatingDisc(QWidget):
    def __init__(self, size=300):
        super().__init__()
        self.setFixedSize(size, size); self.angle = 0
        self.timer = QTimer(self); self.timer.timeout.connect(self.rotate)
        self.pixmap = None
    def set_image(self, pixmap):
        self.pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation) if pixmap else None
        self.update()
    def rotate(self): self.angle = (self.angle + 0.5) % 360; self.update()
    def start_anim(self): self.timer.start(20)
    def stop_anim(self): self.timer.stop()
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        painter.translate(w/2, h/2); painter.rotate(self.angle); painter.translate(-w/2, -h/2)
        path = QPainterPath(); path.addEllipse(2, 2, w-4, h-4); painter.setClipPath(path)
        if self.pixmap: painter.drawPixmap(0, 0, self.pixmap)
        else: painter.setBrush(QBrush(QColor("#222"))); painter.drawEllipse(0, 0, w, h)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QColor(255, 255, 255, 30)); grad.setColorAt(0.5, QColor(255, 255, 255, 0)); grad.setColorAt(1, QColor(255, 255, 255, 30))
        painter.setBrush(QBrush(grad)); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(0, 0, w, h)
        painter.setClipping(False); painter.setBrush(QBrush(QColor("#121212"))); painter.drawEllipse(int(w/2)-15, int(h/2)-15, 30, 30)

class MediaButton(QPushButton):
    def __init__(self, icon_type="play", size=40, color="#FFFFFF", hover_color="#1DB954", bg_color=None):
        super().__init__()
        self.setFixedSize(size, size); self.icon_type = icon_type
        self.base_color = QColor(color); self.hover_color = QColor(hover_color); self.bg_color = QColor(bg_color) if bg_color else None
        self.current_color = self.base_color; self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setStyleSheet("background: transparent; border: none;")
    def set_icon(self, icon_type): self.icon_type = icon_type; self.update()
    def set_active(self, active): self.is_active = active; self.update()
    def enterEvent(self, event): self.current_color = self.hover_color; self.update(); super().enterEvent(event)
    def leaveEvent(self, event): self.current_color = self.base_color; self.update(); super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.bg_color: painter.setBrush(QBrush(self.bg_color)); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(0, 0, self.width(), self.height())
        paint_color = self.hover_color if self.is_active else self.current_color
        painter.setBrush(QBrush(paint_color)); painter.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height(); path = QPainterPath()
        if self.icon_type == "play": path.moveTo(w*0.38, h*0.25); path.lineTo(w*0.72, h*0.5); path.lineTo(w*0.38, h*0.75)
        elif self.icon_type == "pause": 
            rw, rh, gap = w*0.12, h*0.4, w*0.1; x1 = (w - (2*rw + gap)) / 2
            path.addRoundedRect(x1, (h-rh)/2, rw, rh, 2, 2); path.addRoundedRect(x1+rw+gap, (h-rh)/2, rw, rh, 2, 2)
        elif self.icon_type == "next": path.moveTo(w*0.28, h*0.3); path.lineTo(w*0.58, h*0.5); path.lineTo(w*0.28, h*0.7); path.closeSubpath(); path.addRoundedRect(w*0.60, h*0.3, w*0.08, h*0.4, 1, 1)
        elif self.icon_type == "prev": path.addRoundedRect(w*0.32, h*0.3, w*0.08, h*0.4, 1, 1); path.moveTo(w*0.72, h*0.3); path.lineTo(w*0.42, h*0.5); path.lineTo(w*0.72, h*0.7)
        elif self.icon_type == "rw10":
            pen = QPen(paint_color, 2); painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(w*0.2), int(h*0.2), int(w*0.6), int(h*0.6), 90*16, 270*16)
            painter.setBrush(QBrush(paint_color)); painter.setPen(Qt.PenStyle.NoPen)
            path.moveTo(w*0.5, h*0.2); path.lineTo(w*0.4, h*0.1); path.lineTo(w*0.4, h*0.3); path.closeSubpath()
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold)); painter.drawText(QRect(0,0,w,h), Qt.AlignmentFlag.AlignCenter, "10"); return
        elif self.icon_type == "fw10":
            pen = QPen(paint_color, 2); painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(w*0.2), int(h*0.2), int(w*0.6), int(h*0.6), 90*16, -270*16)
            painter.setBrush(QBrush(paint_color)); painter.setPen(Qt.PenStyle.NoPen)
            path.moveTo(w*0.5, h*0.2); path.lineTo(w*0.6, h*0.1); path.lineTo(w*0.6, h*0.3); path.closeSubpath()
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold)); painter.drawText(QRect(0,0,w,h), Qt.AlignmentFlag.AlignCenter, "10"); return
        elif self.icon_type == "loop":
            pen = QPen(paint_color, 2); painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(w*0.2), int(h*0.3), int(w*0.6), int(h*0.4), 0, 180*16); painter.drawArc(int(w*0.2), int(h*0.3), int(w*0.6), int(h*0.4), 180*16, 180*16)
            painter.setBrush(QBrush(paint_color)); painter.setPen(Qt.PenStyle.NoPen)
            path.moveTo(w*0.8, h*0.5); path.lineTo(w*0.7, h*0.4); path.lineTo(w*0.7, h*0.6); path.closeSubpath()
            path.moveTo(w*0.2, h*0.5); path.lineTo(w*0.3, h*0.4); path.lineTo(w*0.3, h*0.6); path.closeSubpath()
        painter.drawPath(path)

class AnimatedButton(QPushButton):
    def __init__(self, text="", theme=DEFAULT_THEME, is_action=False):
        super().__init__(text); self.theme = theme; self.is_action = is_action 
        bg = theme['hover'] if is_action else 'transparent'; fg = theme['text'] if is_action else theme['dim']
        border = f"border: 1px solid {theme['dim']};" if is_action and "Theme" in text else "border: none;"
        self.base_style = f"QPushButton {{ background-color: {bg}; color: {fg}; {border} border-radius: {20 if is_action else 5}px; font-size: 14px; font-family: 'Segoe UI'; text-align: {'center' if is_action else 'left'}; padding: {'12px' if is_action else '10px'}; font-weight: {'bold' if is_action else 'normal'}; }}"
        self.setStyleSheet(self.base_style); self.setCursor(Qt.CursorShape.PointingHandCursor)
    def enterEvent(self, event):
        c_bg = self.theme['accent'] if self.is_action else self.theme['hover']; c_fg = "black" if self.is_action else self.theme['text']
        self.setStyleSheet(self.base_style + f"QPushButton {{ background-color: {c_bg}; color: {c_fg}; border: none; }}"); super().enterEvent(event)
    def leaveEvent(self, event): self.setStyleSheet(self.base_style); super().leaveEvent(event)

# --- MAIN APP ---
class SpotifyClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = DEFAULT_THEME
        self.dynamic_color = QColor(DEFAULT_THEME['accent'])
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1280, 850)
        
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.5)
        
        self.playlist = [] 
        self.filtered_playlist = [] 
        self.current_index = -1
        self.lyrics_data = []
        self.is_looping = False
        
        self.init_ui()
        self.setup_shortcuts()
        self.connect_signals()
        self.apply_theme(self.current_theme)

    def clean_title(self, title):
        title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)
        if '-' in title: title = title.split('-')[0]
        return title.strip()

    def init_ui(self):
        main_widget = QWidget(); self.setCentralWidget(main_widget); main_widget.setObjectName("MainWidget")
        self.main_layout = QVBoxLayout(main_widget); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self.title_bar = TitleBar(self); self.main_layout.addWidget(self.title_bar)
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(0)

        # SIDEBAR
        self.sidebar = QFrame(); self.sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(self.sidebar); sb_layout.setContentsMargins(20, 20, 20, 20)
        logo = QLabel("♫ Rook's Music"); logo.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {self.current_theme['text']}; margin-bottom: 20px;")
        sb_layout.addWidget(logo)
        self.search_bar = QLineEdit(); self.search_bar.setPlaceholderText("🔍 Search Library..."); self.search_bar.textChanged.connect(self.filter_library)
        sb_layout.addWidget(self.search_bar)

        sb_layout.addSpacing(10)
        self.btn_theme = AnimatedButton("🎨 Change Theme", theme=self.current_theme, is_action=True); self.btn_theme.clicked.connect(self.cycle_theme); sb_layout.addWidget(self.btn_theme)
        self.btn_open = AnimatedButton("+ Open Folder", theme=self.current_theme, is_action=True); self.btn_open.clicked.connect(self.open_folder); sb_layout.addWidget(self.btn_open)
        sb_layout.addStretch()

        # CONTENT
        self.content_frame = QFrame(); self.content_frame.setLayout(QVBoxLayout()); self.content_frame.layout().setContentsMargins(0,0,0,0)
        self.bg_label = QLabel(self.content_frame); self.bg_label.setScaledContents(True); self.bg_label.setGeometry(-50, -50, 1400, 1000)
        blur = QGraphicsBlurEffect(); blur.setBlurRadius(100); self.bg_label.setGraphicsEffect(blur); self.bg_label.lower()
        self.overlay = QLabel(self.content_frame); self.overlay.lower()
        
        # Lyrics
        lyrics_widget = QWidget(self.content_frame); l_layout = QVBoxLayout(lyrics_widget); l_layout.setContentsMargins(50, 0, 50, 0) # 0 Vertical margin
        self.lyrics_list = QListWidget(); self.lyrics_list.setWordWrap(True)
        self.lyrics_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lyrics_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lyrics_list.setStyleSheet("background: transparent; border: none;"); self.lyrics_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lyrics_list.itemDoubleClicked.connect(self.seek_lyrics)
        l_layout.addWidget(self.lyrics_list); self.content_frame.layout().addWidget(lyrics_widget)

        # QUEUE
        self.queue_frame = QFrame(); self.queue_frame.setFixedWidth(280); q_layout = QVBoxLayout(self.queue_frame)
        q_layout.addWidget(QLabel("Next Up", styleSheet=f"color: {self.current_theme['dim']}; font-weight: bold; margin-top: 10px;"))
        self.queue_list = QListWidget(); self.queue_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_list.setStyleSheet("background: transparent; border: none;"); self.queue_list.itemDoubleClicked.connect(self.play_queue_item)
        q_layout.addWidget(self.queue_list)

        splitter.addWidget(self.sidebar); splitter.addWidget(self.content_frame); splitter.addWidget(self.queue_frame); splitter.setStretchFactor(1, 1)

        # PLAYER BAR
        self.player_bar = QFrame(); self.player_bar.setFixedHeight(130); pb_layout = QHBoxLayout(self.player_bar); pb_layout.setContentsMargins(20, 5, 20, 5)
        
        w_left = QWidget(); wl = QHBoxLayout(w_left); wl.setContentsMargins(0,0,0,0)
        self.bar_disc = RotatingDisc(90); self.bar_title = QLabel(""); self.bar_artist = QLabel(""); self.bar_title.setStyleSheet("font-weight: bold; font-size: 14px;"); self.bar_artist.setStyleSheet(f"color: {self.current_theme['dim']};")
        l_box = QVBoxLayout(); l_box.setAlignment(Qt.AlignmentFlag.AlignVCenter); l_box.addWidget(self.bar_title); l_box.addWidget(self.bar_artist)
        wl.addWidget(self.bar_disc); wl.addLayout(l_box)
        
        w_center = QWidget(); wc = QVBoxLayout(w_center); wc.setAlignment(Qt.AlignmentFlag.AlignVCenter); wc.setSpacing(5)
        ctrls = QHBoxLayout(); ctrls.setAlignment(Qt.AlignmentFlag.AlignCenter); ctrls.setSpacing(20) 
        self.btn_loop = MediaButton("loop", 30, "#B3B3B3", "#FFFFFF"); self.btn_loop.clicked.connect(self.toggle_loop)
        self.btn_rw = MediaButton("rw10", 32, "#B3B3B3", "#FFFFFF"); self.btn_rw.clicked.connect(lambda: self.player.setPosition(max(0, self.player.position()-10000)))
        self.btn_prev = MediaButton("prev", 36, "#B3B3B3", "#FFFFFF"); self.btn_prev.clicked.connect(self.prev_song)
        self.btn_play = MediaButton("play", 50, "black", "black", "#FFFFFF"); self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next = MediaButton("next", 36, "#B3B3B3", "#FFFFFF"); self.btn_next.clicked.connect(self.next_song)
        self.btn_fw = MediaButton("fw10", 32, "#B3B3B3", "#FFFFFF"); self.btn_fw.clicked.connect(lambda: self.player.setPosition(min(self.player.duration(), self.player.position()+10000)))
        ctrls.addWidget(self.btn_loop); ctrls.addWidget(self.btn_rw); ctrls.addWidget(self.btn_prev); ctrls.addWidget(self.btn_play); ctrls.addWidget(self.btn_next); ctrls.addWidget(self.btn_fw)
        
        s_box = QHBoxLayout(); self.lbl_curr = QLabel("0:00")
        # CLICKABLE SLIDER
        self.slider = ClickableSlider(Qt.Orientation.Horizontal); self.slider.setFixedHeight(25); self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_total = QLabel("0:00")
        s_box.addWidget(self.lbl_curr); s_box.addWidget(self.slider); s_box.addWidget(self.lbl_total)
        wc.addLayout(ctrls); wc.addLayout(s_box)

        w_right = QWidget(); wr = QHBoxLayout(w_right); wr.setAlignment(Qt.AlignmentFlag.AlignRight)
        vol_slider = ClickableSlider(Qt.Orientation.Horizontal); vol_slider.setFixedWidth(100); vol_slider.setValue(50); vol_slider.valueChanged.connect(lambda v: self.audio.setVolume(v/100))
        wr.addWidget(QLabel("🔊")); wr.addWidget(vol_slider)

        pb_layout.addWidget(w_left, 2); pb_layout.addWidget(w_center, 5); pb_layout.addWidget(w_right, 2)
        self.main_layout.addWidget(splitter); self.main_layout.addWidget(self.player_bar)

    def setup_shortcuts(self):
        self.addAction(QAction("Toggle Play", self, shortcut=Qt.Key.Key_Space, triggered=self.toggle_play))
        self.addAction(QAction("Next", self, shortcut=Qt.Key.Key_Right, triggered=self.next_song))
        self.addAction(QAction("Prev", self, shortcut=Qt.Key.Key_Left, triggered=self.prev_song))
        self.addAction(QAction("Next Media", self, shortcut=Qt.Key.Key_MediaNext, triggered=self.next_song))
        self.addAction(QAction("Prev Media", self, shortcut=Qt.Key.Key_MediaPrevious, triggered=self.prev_song))
        self.addAction(QAction("Play/Pause Media", self, shortcut=Qt.Key.Key_MediaPlay, triggered=self.toggle_play))

    def mouseMoveEvent(self, event):
        center_x, center_y = self.width() / 2, self.height() / 2
        diff_x = event.pos().x() - center_x; diff_y = event.pos().y() - center_y
        self.bg_label.move(int(diff_x * -0.03) - 50, int(diff_y * -0.03) - 50)
        super().mouseMoveEvent(event)

    def apply_theme(self, theme):
        self.current_theme = theme
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme['bg']}; }} QWidget {{ color: {theme['text']}; font-family: 'Segoe UI'; }} QFrame#MainWidget {{ background-color: {theme['bg']}; }}")
        self.title_bar.setStyleSheet(f"background-color: {theme['bg']};")
        self.sidebar.setStyleSheet(f"background-color: {theme['sidebar']};")
        self.player_bar.setStyleSheet(f"background-color: {theme['player']}; border-top: 1px solid #222;")
        self.queue_frame.setStyleSheet(f"background-color: {theme['bg']}; border-left: 1px solid #222;")
        self.search_bar.setStyleSheet(f"background-color: {theme['hover']}; color: {theme['text']}; border-radius: 5px; padding: 8px; border: none;")
        self.overlay.setStyleSheet(f"background-color: {theme['bg']}cc;")
        
        accent = self.dynamic_color.name()
        slider_css = f"QSlider::groove:horizontal {{ height: 6px; background: {theme['hover']}; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {theme['text']}; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }} QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 3px; }}"
        self.slider.setStyleSheet(slider_css)
        self.btn_play.bg_color = QColor(theme['text']); self.btn_play.base_color = QColor("black"); self.btn_play.hover_color = QColor("#333"); self.btn_play.update()
        self.update_queue_ui()

    def cycle_theme(self):
        themes = list(THEMES.keys())
        curr = [k for k, v in THEMES.items() if v == self.current_theme][0]
        next_t = THEMES[themes[(themes.index(curr) + 1) % len(themes)]]
        self.apply_theme(next_t)

    def connect_signals(self):
        self.player.positionChanged.connect(self.update_progress)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.slider.sliderMoved.connect(self.player.setPosition)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music")
        if not folder: return
        self.playlist = []
        exts = ['.mp3', '.flac', '.wav', '.m4a']
        for f in os.listdir(folder):
            if any(f.lower().endswith(e) for e in exts):
                self.playlist.append(self.extract_meta(os.path.join(folder, f)))
        self.filtered_playlist = self.playlist
        if self.playlist: self.load_song(0); self.update_queue_ui()

    def filter_library(self, text):
        if not text: self.filtered_playlist = self.playlist
        else: self.filtered_playlist = [s for s in self.playlist if text.lower() in s['title'].lower()]
        self.update_queue_ui(use_filtered=True)

    def extract_meta(self, path):
        meta = {"path": path, "title": self.clean_title(os.path.basename(path)), "artist": "Unknown", "art": None}
        try:
            audio = File(path)
            if audio:
                if isinstance(audio.tags, ID3):
                    t = str(audio.tags.get('TIT2', meta["title"])); meta["title"] = self.clean_title(t)
                    meta["artist"] = str(audio.tags.get('TPE1', meta["artist"]))
                    for k in audio.tags.keys():
                        if k.startswith("APIC"): meta["art"] = audio.tags[k].data; break
                elif hasattr(audio, 'tags'):
                    t = audio.tags.get('title', [meta["title"]])[0]; meta["title"] = self.clean_title(t)
                    meta["artist"] = audio.tags.get('artist', [meta["artist"]])[0]
                    if audio.pictures: meta["art"] = audio.pictures[0].data
        except: pass
        return meta

    def load_song(self, idx):
        target = self.filtered_playlist[idx]
        real_idx = self.playlist.index(target)
        self.current_index = real_idx
        song = self.playlist[real_idx]
        
        self.player.setSource(QUrl.fromLocalFile(song['path'])); self.player.play()
        self.btn_play.set_icon("pause"); self.bar_disc.start_anim()
        self.bar_title.setText(song['title']); self.bar_artist.setText(song['artist'])
        
        pix = QPixmap()
        if song['art']: pix.loadFromData(song['art'])
        else: pix = QPixmap(300, 300); pix.fill(QColor("#333"))
        
        # Use new SAFE color logic
        self.dynamic_color = get_safe_color(pix)
        self.bar_disc.set_image(pix); self.bg_label.clear()
        
        self.apply_theme(self.current_theme)
        self.update_queue_ui()
        
        # Lyrics
        self.lyrics_list.clear()
        self.lyrics_list.addItem(QListWidgetItem("Fetching Lyrics..."))
        self.worker = LyricsWorker(song['title'], song['artist'])
        self.worker.lyrics_found.connect(self.on_lyrics_found)
        self.worker.start()

    def update_queue_ui(self, use_filtered=False):
        self.queue_list.clear()
        source = self.filtered_playlist if use_filtered else self.playlist
        accent_hex = self.dynamic_color.name()
        for i, song in enumerate(source):
            item = QListWidgetItem(f"{i+1}. {song['title']}\n    {song['artist']}"); item.setData(Qt.ItemDataRole.UserRole, i)
            if (song == self.playlist[self.current_index]) if self.playlist and self.current_index >= 0 else False:
                item.setForeground(QBrush(QColor(accent_hex)))
                font = item.font(); font.setBold(True); item.setFont(font)
                self.queue_list.addItem(item); self.queue_list.setCurrentItem(item)
            else:
                item.setForeground(QBrush(QColor(self.current_theme['text'])))
                self.queue_list.addItem(item)
        if not use_filtered and self.queue_list.currentItem():
            self.queue_list.scrollToItem(self.queue_list.currentItem(), QAbstractItemView.ScrollHint.PositionAtCenter)

    def play_queue_item(self, item): self.load_song(item.data(Qt.ItemDataRole.UserRole))

    def on_lyrics_found(self, data):
        self.lyrics_data = data
        self.lyrics_list.clear()
        
        # --- CALCULATE SPACER HEIGHT ---
        # Get current height of the list widget, default to 400 if not rendered yet
        h = self.lyrics_list.height() if self.lyrics_list.height() > 0 else 400
        half_height = int(h / 2) - 30 # Subtract 30px to account for the text height itself
        
        # 1. TOP SPACER (Forces first lyric to center)
        top_spacer = QListWidgetItem("")
        top_spacer.setFlags(Qt.ItemFlag.NoItemFlags) # Unclickable
        top_spacer.setSizeHint(QSize(10, half_height))
        self.lyrics_list.addItem(top_spacer)

        if not data: 
            item = QListWidgetItem("Instrumental / No Lyrics")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QBrush(QColor(self.current_theme['dim'])))
            self.lyrics_list.addItem(item)
        else:
            for _, t in data:
                item = QListWidgetItem(t)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor(self.current_theme['dim'])))
                # Set initial font
                font = QFont("Segoe UI", 18)
                font.setBold(False)
                item.setFont(font)
                self.lyrics_list.addItem(item)
                
        # 2. BOTTOM SPACER (Allows last lyric to scroll to center)
        bot_spacer = QListWidgetItem("")
        bot_spacer.setFlags(Qt.ItemFlag.NoItemFlags)
        bot_spacer.setSizeHint(QSize(10, half_height))
        self.lyrics_list.addItem(bot_spacer)
    def update_progress(self, pos):
        # Update Slider
        if not self.slider.isSliderDown(): 
            self.slider.setValue(pos)
        self.lbl_curr.setText(self.fmt_time(pos))
        
        # Lyrics Logic
        if self.lyrics_data:
            idx = -1
            # Find which lyric line we are on based on time
            for i, (ms, _) in enumerate(self.lyrics_data):
                if ms > pos: break
                idx = i
            
            if idx != -1:
                # Add offset: +1 because index 0 is now the TOP SPACER
                row = idx + 1 
                curr_item = self.lyrics_list.item(row)
                
                # Only update if the line actually changed
                if self.lyrics_list.currentItem() != curr_item:
                    self.lyrics_list.setCurrentItem(curr_item)
                    
                    # FORCE SCROLL TO CENTER
                    self.lyrics_list.scrollToItem(curr_item, QAbstractItemView.ScrollHint.PositionAtCenter)
                    
                    # --- UPDATE VISUALS FOR ALL ITEMS ---
                    # We loop through EVERY item to guarantee the fade is correct
                    total_items = self.lyrics_list.count()
                    
                    for j in range(total_items):
                        it = self.lyrics_list.item(j)
                        
                        # Skip if it's the invisible spacers
                        if not it.text(): continue 
                        
                        # Calculate distance from the active row
                        dist = abs(j - row)
                        font = it.font()
                        
                        if dist == 0:
                            # === ACTIVE LINE ===
                            # Bright, Big, Bold
                            it.setForeground(QBrush(self.dynamic_color.lighter(130)))
                            font.setPixelSize(32) # Bigger size
                            font.setBold(True)
                        else:
                            # === INACTIVE LINES ===
                            # Calculate fade based on distance
                            # The further away, the more transparent and smaller
                            base_color = QColor(self.current_theme['text'])
                            
                            # Opacity math: start at 100, subtract 25 for every step away, min 10
                            alpha = max(10, 255 - (dist * 40)) 
                            base_color.setAlpha(alpha)
                            it.setForeground(QBrush(base_color))
                            
                            # Size math: start at 20, shrink down to 14
                            size = max(14, 24 - (dist * 2))
                            font.setPixelSize(size)
                            font.setBold(False)
                        
                        it.setFont(font)
    def update_duration(self, d): self.slider.setRange(0, d); self.lbl_total.setText(self.fmt_time(d))
    def fmt_time(self, ms): return f"{ms//60000}:{(ms//1000)%60:02}"
    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.player.pause(); self.btn_play.set_icon("play"); self.bar_disc.stop_anim()
        else: self.player.play(); self.btn_play.set_icon("pause"); self.bar_disc.start_anim()
    def toggle_loop(self): self.is_looping = not self.is_looping; self.btn_loop.set_active(self.is_looping)
    def next_song(self): 
        if self.playlist: self.load_song((self.current_index + 1) % len(self.playlist))
    def prev_song(self): 
        if self.playlist: self.load_song((self.current_index - 1) % len(self.playlist))
    def on_media_status(self, s):
        if s == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.is_looping: self.player.play()
            else: self.next_song()
    def seek_lyrics(self, item):
        row = self.lyrics_list.row(item)
        # Offset is 1 because index 0 is the Top Spacer
        data_idx = row - 1 
        if 0 <= data_idx < len(self.lyrics_data): 
            self.player.setPosition(self.lyrics_data[data_idx][0])
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpotifyClone()
    window.show()
    sys.exit(app.exec())