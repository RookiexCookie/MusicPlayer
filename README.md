# 🎵 Rook's Ethereal Music Player

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?style=for-the-badge&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=for-the-badge)

**A visually immersive, frameless local music player that turns your audio library into a stunning visual experience.**

Rook's Music Player isn't just about playback; it's about atmosphere. Built with **PyQt6**, it combines a modern frameless design with intelligent color adaptation, a physics-based rotating vinyl animation, and a karaoke-style lyric engine that keeps you synced with the music.

---

## ✨ Key Features

### 👁️ Intelligent Visuals
* **Adaptive Color Engine:** The UI automatically extracts the dominant color from your album art and calculates the perfect "safe" saturation and brightness. This ensures the interface creates a matching mood while keeping text readable.
* **Glassmorphism Background:** Features a dynamic, blurred parallax background that uses the current track's art to add depth to the window.
* **Rotating Vinyl Animation:** A smooth, custom-painted disc animation that spins when music plays and halts when paused, complete with groove details and lighting gradients.

### 🎤 The Lyric Experience
* **Auto-Synced Lyrics:** Integrates with `syncedlyrics` to fetch time-synchronized lyrics from the web automatically in the background.
* **Always-Centered Focus:** A smart scrolling engine ensures the active line is **always** vertically centered on the screen.
* **Dynamic Focus Fading:** Active lyrics glow and enlarge, while surrounding lines fade out and shrink based on their distance from the center, creating a beautiful, distraction-free reading experience.

### 🎨 7+ Hand-Crafted Themes
Switch instantly between diverse visual styles to match your mood:
* **Spotify** (Classic Dark)
* **Cyberpunk** (Neon & Navy)
* **Dracula** (Vampiric Purple)
* **Ocean** (Deep Blue)
* **Sunset** (Warm Orange)
* **Forest** (Natural Green)
* **Royal** (Gold & Purple)

### ⚡ Power & Usability
* **Frameless UI:** A custom title bar with window snapping and minimizing capabilities.
* **Clickable Progress Bar:** Jump instantly to any part of the song.
* **Keyboard Shortcuts:** Full support for media keys and keyboard navigation.

---

## 📸 Screenshots

| **The Player Interface**

<img width="1366" height="722" alt="image" src="https://github.com/user-attachments/assets/e705d85c-b478-4416-9255-9a6929d1aec9" /> 

---

## 🛠️ Installation

### Prerequisites
Ensure you have Python installed. This project relies on the following powerful libraries:

* **PyQt6**: For the modern GUI.
* **Mutagen**: For reading metadata (MP3, FLAC, M4A tags).
* **Syncedlyrics**: For fetching time-synced LRC files.

### Setup Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/RookiexCookie/MusicPlayer.git
    cd MusicPlayer
    ```

2.  **Install Dependencies**
    ```bash
    pip install PyQt6 mutagen syncedlyrics
    ```

3.  **Run the Application**
    ```bash
    python music_player.py
    ```

---

## 🎮 Controls & Shortcuts

| Key | Action |
| :--- | :--- |
| **Spacebar** | Toggle Play / Pause |
| **Right Arrow** | Next Song |
| **Left Arrow** | Previous Song |
| **Media Play** | Toggle Play (System Key) |
| **Media Next** | Next Song (System Key) |
| **Click Slider** | Seek to position |

---

## 🧠 Technical Highlights

For the developers interested in the logic under the hood:

* **Threaded Architecture:** Lyric fetching happens on a separate `QThread` (`LyricsWorker`) to ensure the UI remains buttery smooth and never freezes while searching the web.
* **Custom Painting:** The `RotatingDisc` and `MediaButton` classes use `QPainter` to draw vector-quality graphics directly, rather than relying on static image assets.
* **Mathematical Centering:** The lyric engine uses dynamic spacers calculated at runtime: `half_height = int(h / 2) - 30`. This guarantees that the first and last lines of a song can still be scrolled to the perfect center of the view.

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ by Rook
</p>
