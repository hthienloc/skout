# Skout 🃏

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/licenses/GPL-3.0-or-later)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Framework: PySide6](https://img.shields.io/badge/Framework-PySide6-green.svg)](https://www.qt.io/qt-for-python)

**Skout** is a modern, digital implementation of the popular ladder-climbing card game. Built with Python and PySide6, it features a clean interface following KDE design principles, intelligent AI opponents, and smooth gameplay.

![Screenshot](https://raw.githubusercontent.com/hthienloc/skout/main/assets/screenshots/arena.png)

## ✨ Features

- **Strategic Gameplay:** Full implementation of the "Show", "Skout", and "Skout & Show" mechanics.
- **KDE Integration:** Follows Breeze design standards, supports system themes, and integrates with the Plasma taskbar.
- **Adaptive AI:** Opponents use dynamic strategies that change based on the game phase (Endgame, Blitz, etc.).
- **Professional Log:** Concise, numeric performance log for tracking every move.
- **User Friendly:** Responsive controls, flip previews, and an integrated digital handbook.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- PySide6

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hthienloc/skout.git
   cd skout
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the game:**
   ```bash
   python main.py
   ```

### System Integration (Linux/KDE)

To display the correct icon and name in your application menu and taskbar:

```bash
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cp data/org.kde.skout.desktop ~/.local/share/applications/
cp data/icons/hicolor/scalable/apps/org.kde.skout.svg ~/.local/share/icons/hicolor/scalable/apps/
update-desktop-database ~/.local/share/applications
```

## 📜 Game Rules

Need a refresher? The official rules reference is available within the game via the **Handbook** (F1) or you can read it directly [here](docs/rules.md).

## 🛠️ Tech Stack

- **Engine:** Pure Python game logic (deterministic).
- **UI:** PySide6 (Qt for Python).
- **Icons:** Custom SVG designed in KDE Breeze style.
- **Metadata:** AppStream and Freedesktop compliant.

## 🤝 Contributing

Contributions are welcome! Whether it's reporting a bug, improving the AI logic, or adding new card skins, feel free to open an issue or submit a pull request.

## ⚖️ License

Distributed under the GPL-3.0-or-later License. See `LICENSE` for more information.

---
*Disclaimer: Skout is an open-source fan project and is not affiliated with the original board game publishers.*
