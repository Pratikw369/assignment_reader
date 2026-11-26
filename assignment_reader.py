#!/usr/bin/env python3
"""Assignment Reader: offline chunk-by-chunk dictation for Ubuntu 22.04."""
import os, re, sys, json, time, signal, shutil, tempfile, subprocess, socket, urllib.request, urllib.error
from urllib.parse import urlencode
from pathlib import Path
import yaml
from PySide6.QtCore import Qt, QTimer, QProcess, QThread, Signal, QSettings, QSignalBlocker
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor, QTextCharFormat, QColor, QGuiApplication
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QTextBrowser, QPushButton, QLabel, QSpinBox, QSlider, QGroupBox,
    QFormLayout, QMessageBox, QComboBox, QCheckBox, QFileDialog, QAbstractSpinBox, QToolButton)

APP_NAME = "Assignment Reader"
DEFAULT_VOICE_DIR = Path.home() / "assignment-reader" / "voices"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
PIPER_MODEL = "en_US-lessac-medium"
PIPER_PORT = 5000

LIGHT_QSS = """
QMainWindow, QWidget { background:#f4f6fa; color:#1d2633; }
QGroupBox { border:1px solid #d5dbe5; border-radius:10px; margin-top:10px; padding:12px 12px 10px 12px; }
QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; font-weight:600; }
QTextEdit, QTextBrowser, QComboBox { background:#ffffff; color:#1d2633; border:1px solid #d0d7e2; border-radius:8px; padding:6px 10px; min-height:24px; }
QSpinBox { background:#ffffff; color:#1d2633; border:1px solid #d0d7e2; border-radius:8px; padding:4px 10px; min-height:28px; min-width:110px; font-size:14px; font-weight:500; }
QSpinBox::up-button, QSpinBox::down-button { width:0px; height:0px; border:none; }
QSpinBox QLineEdit { background:transparent; color:#1d2633; border:none; padding:0px; margin:0px; selection-background-color:#245fbd; selection-color:#ffffff; }
QPushButton { background:#ffffff; color:#1d2633; border:1px solid #cbd3df; border-radius:8px; padding:7px 14px; font-weight:500; }
QPushButton:hover { background:#eaf1fb; border-color:#adc0de; }
QPushButton:pressed { background:#dce8f8; }
QPushButton:default, QPushButton#primaryBtn { background:#245fbd; color:#ffffff; border-color:#245fbd; font-weight:600; }
QPushButton:default:hover, QPushButton#primaryBtn:hover { background:#1d52a8; }
QPushButton#accentBtn { background:#edf4ff; color:#1b4f9c; border:1px solid #b7cff5; font-weight:600; }
QPushButton#accentBtn:hover { background:#dceaff; }
QToolButton#stepper { background:#e9eef6; color:#36465c; border:1px solid #cbd3df; border-radius:4px; padding:0; font-size:9px; font-weight:700; }
QToolButton#stepper:hover { background:#d8e5f7; }
QToolButton#stepper:pressed { background:#c4d6f0; }
QLabel#headline { font-size:21px; font-weight:700; }
QLabel#subtle { color:#5a6679; }
QLabel#fieldTag { color:#36465c; font-weight:500; }
QCheckBox { spacing:8px; color:#1d2633; font-weight:500; }
QCheckBox::indicator { width:18px; height:18px; border:1px solid #b8c2d1; border-radius:4px; background:#ffffff; }
QCheckBox::indicator:hover { border-color:#245fbd; }
QCheckBox::indicator:checked { background:#245fbd; border-color:#245fbd; }
QSlider::groove:horizontal { height:6px; background:#d7deea; border-radius:3px; }
QSlider::handle:horizontal { background:#245fbd; width:16px; margin:-5px 0; border-radius:8px; }
QProgressBar { border:1px solid #d0d7e2; border-radius:6px; height:10px; background:#ffffff; }
QProgressBar::chunk { background:#245fbd; border-radius:5px; }
QComboBox QAbstractItemView { background:#ffffff; color:#1d2633; selection-background-color:#245fbd; selection-color:#ffffff; }
"""
DARK_QSS = """
QMainWindow, QWidget { background:#171a21; color:#e8eaf0; }
QGroupBox { border:1px solid #353b49; border-radius:10px; margin-top:10px; padding:12px 12px 10px 12px; }
QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; font-weight:600; }
QTextEdit, QTextBrowser, QComboBox { background:#202530; color:#e8eaf0; border:1px solid #3b4353; border-radius:8px; padding:6px 10px; min-height:24px; }
QSpinBox { background:#202530; color:#e8eaf0; border:1px solid #3b4353; border-radius:8px; padding:4px 10px; min-height:28px; min-width:110px; font-size:14px; font-weight:500; }
QSpinBox::up-button, QSpinBox::down-button { width:0px; height:0px; border:none; }
QSpinBox QLineEdit { background:transparent; color:#e8eaf0; border:none; padding:0px; margin:0px; selection-background-color:#548cf0; selection-color:#ffffff; }
QPushButton { background:#252b38; color:#e8eaf0; border:1px solid #3b4353; border-radius:8px; padding:7px 14px; font-weight:500; }
QPushButton:hover { background:#30394b; border-color:#4d5970; }
QPushButton:pressed { background:#394459; }
QPushButton:default, QPushButton#primaryBtn { background:#316ed1; color:#ffffff; border-color:#316ed1; font-weight:600; }
QPushButton:default:hover, QPushButton#primaryBtn:hover { background:#3d7ce0; }
QPushButton#accentBtn { background:#23324a; color:#9ec3ff; border:1px solid #3d5a85; font-weight:600; }
QPushButton#accentBtn:hover { background:#2b3e5c; }
QToolButton#stepper { background:#303747; color:#dfe7f5; border:1px solid #465168; border-radius:4px; padding:0; font-size:9px; font-weight:700; }
QToolButton#stepper:hover { background:#3c4860; }
QToolButton#stepper:pressed { background:#4b5d7b; }
QLabel#headline { font-size:21px; font-weight:700; }
QLabel#subtle { color:#a4adbc; }
QLabel#fieldTag { color:#c3cad9; font-weight:500; }
QCheckBox { spacing:8px; color:#e8eaf0; font-weight:500; }
QCheckBox::indicator { width:18px; height:18px; border:1px solid #56627a; border-radius:4px; background:#202530; }
QCheckBox::indicator:hover { border-color:#76a7ff; }
QCheckBox::indicator:checked { background:#316ed1; border-color:#76a7ff; }
QSlider::groove:horizontal { height:6px; background:#3b4353; border-radius:3px; }
QSlider::handle:horizontal { background:#76a7ff; width:16px; margin:-5px 0; border-radius:8px; }
QProgressBar { border:1px solid #3b4353; border-radius:6px; height:10px; background:#202530; }
QProgressBar::chunk { background:#548cf0; border-radius:5px; }
QComboBox QAbstractItemView { background:#202530; color:#e8eaf0; selection-background-color:#316ed1; selection-color:#ffffff; }
"""

class PiperWorker(QThread):
    result_ready = Signal(int, bytes, str)

    def __init__(self, token, text, speed, port, parent=None):
        super().__init__(parent)
        self.token, self.text, self.speed, self.port = token, text, speed, port

    @staticmethod
    def _wav_or_error(audio, headers=None):
        if audio[:4] == b"RIFF":
            return audio, ""
        content_type = headers.get("Content-Type", "") if headers is not None else ""
        snippet = audio[:240].decode("utf-8", errors="replace").replace("\\n", " ").strip()
        extra = " Server response: " + snippet if snippet else ""
        return b"", f"Piper endpoint did not return WAV audio (Content-Type: {content_type or 'unknown'})." + extra

    def run(self):
        payload = json.dumps({
            "text": self.text,
            "length_scale": max(.5, min(2.2, 160.0 / float(self.speed))),
        }).encode("utf-8")
        base_url = f"http://127.0.0.1:{self.port}"
        last_error = "Piper server did not respond."

        # Current official Piper HTTP docs specify POST /synthesize.
        # Retain fallbacks for older Piper package versions and forks.
        endpoints = [
            ("POST", "/synthesize"),
            ("POST", "/"),
            ("GET", "/?" + urlencode({"text": self.text})),
        ]

        for _ in range(35):
            last_non_wav_error = None
            retryable_startup = False
            for method, path in endpoints:
                try:
                    if method == "POST":
                        req = urllib.request.Request(
                            base_url + path,
                            data=payload,
                            headers={"Content-Type": "application/json", "Accept": "audio/wav"},
                            method="POST",
                        )
                    else:
                        req = urllib.request.Request(base_url + path, method="GET")

                    with urllib.request.urlopen(req, timeout=60) as response:
                        body = response.read()
                        audio, format_error = self._wav_or_error(body, response.headers)
                        if audio:
                            self.result_ready.emit(self.token, audio, "")
                            return
                        last_non_wav_error = format_error
                        # A 200 HTML/JSON response is not a connection-startup issue.
                        continue

                except urllib.error.HTTPError as http_error:
                    body = http_error.read(240).decode("utf-8", errors="replace").replace("\\n", " ")
                    last_error = f"HTTP {http_error.code} for {method} {path}."
                    if body:
                        last_error += " " + body
                    if http_error.code in (404, 405, 501):
                        continue
                    # Validation or model errors should be surfaced rather than hidden.
                    self.result_ready.emit(self.token, b"", last_error)
                    return
                except (urllib.error.URLError, TimeoutError, ConnectionError) as ex:
                    last_error = str(ex)
                    retryable_startup = True
                    break
                except Exception as ex:
                    self.result_ready.emit(self.token, b"", f"{type(ex).__name__}: {ex}")
                    return

            if last_non_wav_error and not retryable_startup:
                self.result_ready.emit(self.token, b"", last_non_wav_error)
                return
            time.sleep(.4)

        self.result_ready.emit(self.token, b"", last_error)



def speech_words_with_source_map(source):
    """Return spoken tokens and source character spans while removing common Markdown syntax."""
    text = source
    source_map = list(range(len(source)))

    def transform(pattern, group=None, flags=0):
        nonlocal text, source_map
        rx = re.compile(pattern, flags)
        out_parts, out_map = [], []
        cursor = 0
        for match in rx.finditer(text):
            out_parts.append(text[cursor:match.start()])
            out_map.extend(source_map[cursor:match.start()])
            if group is not None:
                a, b = match.span(group)
                out_parts.append(text[a:b])
                out_map.extend(source_map[a:b])
            cursor = match.end()
        out_parts.append(text[cursor:])
        out_map.extend(source_map[cursor:])
        text = ''.join(out_parts)
        source_map = out_map

    # Keep link labels and image alt text, map them back to their original source spans.
    transform(r'!\[([^\]]*)\]\([^)]+\)', group=1)
    transform(r'\[([^\]]+)\]\([^)]+\)', group=1)
    # Strip fenced-code markers, heading/list prefixes, and inline emphasis markers.
    transform(r'(?m)^[ \t]*```[^\n]*\n?', group=None)
    transform(r'(?m)^[ \t]{0,3}#{1,6}[ \t]*', group=None)
    transform(r'(?m)^[ \t]*(?:[-*+][ \t]+|\d+[.)][ \t]+)', group=None)
    transform(r'[*_~`>|]', group=None)

    words, spans = [], []
    for match in re.finditer(r'\S+', text):
        word = match.group(0)
        a, b = match.start(), match.end()
        if a >= b or not source_map:
            continue
        original_start = min(source_map[a:b])
        original_end = max(source_map[a:b]) + 1
        words.append(word)
        spans.append((original_start, original_end))
    return words, spans

class AssignmentReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assignment Reader — Offline Dictation")
        self.setMinimumSize(820, 580)
        self._apply_initial_window_size(1180, 780)
        self.voice_dir = DEFAULT_VOICE_DIR
        self.config_path = DEFAULT_CONFIG_PATH
        self.words, self.word_spans = [], []
        self.index = 0
        self.current_chunk = ""
        self.current_chunk_start = 0
        self.current_chunk_end = 0
        self.auto_run = False
        self.paused = False
        self.dark_mode = True
        self.request_id = 0
        self.active_process = None
        self.active_kind = None
        self.piper_thread = None
        self.piper_threads = []
        self.piper_server = None
        self.piper_port = None
        self.temp_audio = None
        self.seeking = False
        self.seek_resume_after = False
        self.seek_was_paused = False
        self.settings = QSettings("OpenAI", "AssignmentReader")

        self._build_ui()
        self.load_settings()
        if not self.settings.contains("engine") and not self.config_path.exists():
            if self.piper_installed() and (self.voice_dir / f"{PIPER_MODEL}.onnx").exists():
                self.engine.setCurrentIndex(0)
            else:
                self.engine.setCurrentIndex(1)
        self.connect_setting_signals()
        self.apply_theme()
        self.refresh_engine_status()

    def _apply_initial_window_size(self, default_w, default_h):
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            w = min(default_w, max(820, int(avail.width() * 0.9)))
            h = min(default_h, max(580, int(avail.height() * 0.88)))
            self.resize(w, h)
        else:
            self.resize(default_w, default_h)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 14, 18, 15)
        outer.setSpacing(10)

        heading = QHBoxLayout()
        title = QLabel("Assignment Reader")
        title.setObjectName("headline")
        heading.addWidget(title)
        heading.addStretch()
        self.status = QLabel("Checking voice engines…")
        self.status.setObjectName("subtle")
        heading.addWidget(self.status)
        self.theme_btn = QPushButton("Switch to light mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        heading.addWidget(self.theme_btn)
        outer.addLayout(heading)

        intro = QLabel("Paste your assignment in the editor. The current spoken chunk is highlighted while audio plays.")
        intro.setObjectName("subtle")
        outer.addWidget(intro)

        self.editor = QTextEdit()
        self.editor.setObjectName("mainEditor")
        self.editor.setPlaceholderText(
            "Paste your assignment here…\n\n"
            "Rich text copied from a webpage can keep its formatting. Markdown text is also supported.\n"
            "Click Prepare speech, then Play All to read chunk by chunk."
        )
        self.editor.setFont(QFont("DejaVu Sans", 14))
        self.editor.setAcceptRichText(True)
        outer.addWidget(self.editor, 1)

        controls = QGroupBox("Playback and display controls")
        form = QFormLayout(controls)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.engine = QComboBox()
        self.engine.addItem("Piper neural voice (more natural)", "piper")
        self.engine.addItem("eSpeak NG (lowest latency)", "espeak")
        self.engine.currentIndexChanged.connect(self.on_engine_changed)
        row.addWidget(self.engine, 1)
        self.setup_btn = QPushButton("Piper setup instructions")
        self.setup_btn.clicked.connect(self.show_piper_setup)
        row.addWidget(self.setup_btn)
        self.voice_dir_btn = QPushButton("Voice folder…")
        self.voice_dir_btn.clicked.connect(self.choose_voice_dir)
        row.addWidget(self.voice_dir_btn)
        form.addRow("Voice engine", row)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(1, 20)
        self.chunk_size.setValue(2)
        self.chunk_size.setSuffix(" words")
        row.addWidget(self.make_stepper(self.chunk_size))
        row.addSpacing(14)
        text_size_lbl = QLabel("Text size:")
        text_size_lbl.setObjectName("fieldTag")
        row.addWidget(text_size_lbl)
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 40)
        self.font_size.setValue(17)
        self.font_size.setSuffix(" px")
        self.font_size.valueChanged.connect(self.apply_font_size)
        row.addWidget(self.make_stepper(self.font_size))
        row.addStretch()
        form.addRow("Chunk size", row)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(80, 300)
        self.speed_slider.setValue(180)
        self.speed_label = QLabel("180 words/min")
        self.speed_label.setMinimumWidth(98)
        self.speed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v} words/min"))
        row.addWidget(self.speed_slider, 1)
        row.addWidget(self.speed_label)
        form.addRow("Speech speed", row)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.word_gap = QSpinBox()
        self.word_gap.setRange(0, 2000)
        self.word_gap.setSingleStep(50)
        self.word_gap.setValue(250)
        self.word_gap.setSuffix(" ms")
        self.word_gap.setToolTip("Used by eSpeak NG. Piper keeps the neural voice's natural word timing.")
        row.addWidget(self.make_stepper(self.word_gap))
        row.addSpacing(14)
        chunk_gap_lbl = QLabel("Between-chunk gap:")
        chunk_gap_lbl.setObjectName("fieldTag")
        row.addWidget(chunk_gap_lbl)
        self.chunk_gap = QSpinBox()
        self.chunk_gap.setRange(0, 15000)
        self.chunk_gap.setSingleStep(250)
        self.chunk_gap.setValue(1800)
        self.chunk_gap.setSuffix(" ms")
        row.addWidget(self.make_stepper(self.chunk_gap))
        row.addSpacing(14)
        self.loop_check = QCheckBox("Loop after finishing")
        self.loop_check.setToolTip("Play All restarts from the beginning until you press Stop.")
        row.addWidget(self.loop_check)
        row.addStretch()
        form.addRow("Word gap", row)

        config_row = QHBoxLayout()
        config_row.setSpacing(8)
        self.save_config_btn = QPushButton("💾 Save Configuration")
        self.save_config_btn.setObjectName("accentBtn")
        self.save_config_btn.setToolTip("Save current speed and settings to the active YAML configuration file (and default config.yaml).")
        self.save_config_btn.clicked.connect(self.save_config_yaml)
        config_row.addWidget(self.save_config_btn)

        self.save_config_as_btn = QPushButton("Save Profile As…")
        self.save_config_as_btn.setToolTip("Save personalised settings to a custom .yaml profile file.")
        self.save_config_as_btn.clicked.connect(self.save_config_yaml_as)
        config_row.addWidget(self.save_config_as_btn)

        self.load_config_btn = QPushButton("Load Profile…")
        self.load_config_btn.setToolTip("Load personalised settings from a .yaml configuration file.")
        self.load_config_btn.clicked.connect(self.load_config_yaml_dialog)
        config_row.addWidget(self.load_config_btn)

        self.config_status_lbl = QLabel(f"Profile: {self.config_path.name}")
        self.config_status_lbl.setObjectName("subtle")
        config_row.addSpacing(8)
        config_row.addWidget(self.config_status_lbl)
        config_row.addStretch()
        form.addRow("User configuration", config_row)

        outer.addWidget(controls)

        buttons = QHBoxLayout()
        self.prepare_btn = QPushButton("Prepare speech")
        self.prepare_btn.clicked.connect(self.prepare_text)
        buttons.addWidget(self.prepare_btn)
        buttons.addStretch()
        self.repeat_btn = QPushButton("Repeat previous")
        self.repeat_btn.clicked.connect(self.repeat_previous)
        buttons.addWidget(self.repeat_btn)
        self.next_btn = QPushButton("Speak Next")
        self.next_btn.clicked.connect(self.speak_next_manual)
        buttons.addWidget(self.next_btn)
        self.play_btn = QPushButton("▶ Play All")
        self.play_btn.setObjectName("primaryBtn")
        self.play_btn.setDefault(True)
        self.play_btn.setMinimumWidth(118)
        self.play_btn.clicked.connect(self.play_all_or_resume)
        buttons.addWidget(self.play_btn)
        self.pause_btn = QPushButton("Ⅱ Pause")
        self.pause_btn.setMinimumWidth(96)
        self.pause_btn.clicked.connect(self.pause_playback)
        buttons.addWidget(self.pause_btn)
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setMinimumWidth(86)
        self.stop_btn.clicked.connect(self.stop_playback)
        buttons.addWidget(self.stop_btn)
        outer.addLayout(buttons)

        seek_row = QHBoxLayout()
        seek_title = QLabel("Jump to chunk")
        seek_row.addWidget(seek_title)
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setEnabled(False)
        self.seek_slider.setToolTip("Drag to select a chunk, then release to jump to it.")
        self.seek_slider.sliderPressed.connect(self.on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self.on_seek_released)
        self.seek_slider.valueChanged.connect(self.update_seek_label)
        seek_row.addWidget(self.seek_slider, 1)
        self.seek_label = QLabel("Chunk 0 / 0")
        self.seek_label.setMinimumWidth(100)
        self.seek_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        seek_row.addWidget(self.seek_label)
        outer.addLayout(seek_row)

        self.progress = QLabel("Paste your assignment and click Prepare speech. Space toggles play/pause when the editor is not focused; Ctrl+Space works anywhere.")
        self.progress.setObjectName("subtle")
        self.progress.setWordWrap(True)
        outer.addWidget(self.progress)

        self.ctrl_space_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.ctrl_space_shortcut.setContext(Qt.WindowShortcut)
        self.ctrl_space_shortcut.activated.connect(lambda: self.space_action(force=True))
        self.next_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.next_shortcut.activated.connect(self.speak_next_manual)
        self.stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.stop_shortcut.activated.connect(self.stop_playback)

    def make_stepper(self, spin):
        """Spin box with a readable internal editor and compact repeat buttons."""
        # Keep UpDownArrows so Qt 6 QStyleSheetStyle does not collapse SC_SpinBoxEditField to 1px;
        # the built-in subcontrol buttons are hidden via QSpinBox::up-button/down-button in QSS.
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        spin.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        spin.setFixedWidth(130)
        spin.setFixedHeight(36)
        spin.setAccelerated(True)

        editor = spin.lineEdit()
        editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        editor.setTextMargins(6, 0, 6, 0)

        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        row.addWidget(spin, 0)

        col_widget = QWidget()
        col_widget.setFixedWidth(24)
        col = QVBoxLayout(col_widget)
        col.setContentsMargins(0, 1, 0, 1)
        col.setSpacing(2)

        up = QToolButton()
        up.setObjectName("stepper")
        up.setText("▲")
        up.setFixedSize(24, 16)
        up.setToolTip("Increase value")

        down = QToolButton()
        down.setObjectName("stepper")
        down.setText("▼")
        down.setFixedSize(24, 16)
        down.setToolTip("Decrease value")

        for button in (up, down):
            button.setAutoRepeat(True)
            button.setAutoRepeatDelay(350)
            button.setAutoRepeatInterval(75)

        up.clicked.connect(
            lambda: spin.setValue(min(spin.maximum(), spin.value() + spin.singleStep()))
        )
        down.clicked.connect(
            lambda: spin.setValue(max(spin.minimum(), spin.value() - spin.singleStep()))
        )

        col.addWidget(up)
        col.addWidget(down)
        row.addWidget(col_widget, 0)
        return container

    def apply_theme(self):
        QApplication.instance().setStyleSheet(DARK_QSS if self.dark_mode else LIGHT_QSS)
        self.theme_btn.setText("Switch to light mode" if self.dark_mode else "Switch to dark mode")
        if self.dark_mode:
            css = "body {color:#e8eaf0;background-color:#202530;} a{color:#8db6ff;} blockquote{color:#bac4d4;} pre,code{background-color:#2b3240;color:#f2d59a;} table,th,td{border:1px solid #4a5364;}"
        else:
            css = "body {color:#1d2633;background-color:#ffffff;} a{color:#245fbd;} blockquote{color:#526071;} pre,code{background-color:#f0f3f7;color:#7a4010;} table,th,td{border:1px solid #d5dbe5;}"
        self.editor.document().setDefaultStyleSheet(css)
        self.apply_font_size()
        self.highlight_chunk(self.current_chunk_start, self.current_chunk_end, scroll=False)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()

    def apply_font_size(self, *_):
        font = self.editor.font()
        font.setPointSize(self.font_size.value())
        self.editor.setFont(font)

    def get_config_dict(self):
        return {
            "dark_mode": bool(self.dark_mode),
            "engine": str(self.selected_engine() or "piper"),
            "voice_dir": str(self.voice_dir),
            "chunk_size": int(self.chunk_size.value()),
            "font_size": int(self.font_size.value()),
            "speech_speed": int(self.speed_slider.value()),
            "word_gap_ms": int(self.word_gap.value()),
            "chunk_gap_ms": int(self.chunk_gap.value()),
            "loop_after_finish": bool(self.loop_check.isChecked()),
        }

    def apply_config_dict(self, data):
        if not isinstance(data, dict):
            return
        if "dark_mode" in data:
            self.dark_mode = bool(data["dark_mode"])
        if "voice_dir" in data and data["voice_dir"]:
            self.voice_dir = Path(str(data["voice_dir"])).expanduser()
        if "engine" in data and data["engine"]:
            idx = self.engine.findData(str(data["engine"]))
            if idx >= 0:
                self.engine.setCurrentIndex(idx)
        if "chunk_size" in data:
            self.chunk_size.setValue(int(data["chunk_size"]))
        if "font_size" in data:
            self.font_size.setValue(int(data["font_size"]))
        if "speech_speed" in data:
            self.speed_slider.setValue(int(data["speech_speed"]))
        if "word_gap_ms" in data:
            self.word_gap.setValue(int(data["word_gap_ms"]))
        if "chunk_gap_ms" in data:
            self.chunk_gap.setValue(int(data["chunk_gap_ms"]))
        if "loop_after_finish" in data:
            self.loop_check.setChecked(bool(data["loop_after_finish"]))

    def write_config_to_yaml(self, path):
        target = Path(path).expanduser()
        if target.suffix.lower() not in (".yaml", ".yml"):
            target = target.with_suffix(".yaml")
        target.parent.mkdir(parents=True, exist_ok=True)
        config_data = self.get_config_dict()
        with open(target, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f, sort_keys=False, default_flow_style=False)
        return target

    def load_config_from_yaml(self, path, notify=False):
        target = Path(path).expanduser()
        if not target.exists():
            return False
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError("Configuration YAML root must be a mapping/dictionary.")
            self.apply_config_dict(data)
            self.config_path = target
            self.settings.setValue("config_path", str(self.config_path))
            if hasattr(self, "config_status_lbl"):
                self.config_status_lbl.setText(f"Profile: {self.config_path.name}")
                self.config_status_lbl.setToolTip(str(self.config_path))
            self.apply_theme()
            self.refresh_engine_status()
            self.refresh_seek_slider_range()
            self.save_settings()
            if notify and hasattr(self, "progress"):
                self.progress.setText(f"Loaded configuration from {self.config_path}")
            return True
        except Exception as ex:
            if notify:
                QMessageBox.warning(self, "Could not load configuration", f"Failed to read {target}:\n{ex}")
            return False

    def save_config_yaml(self):
        try:
            saved_path = self.write_config_to_yaml(self.config_path)
            self.config_path = saved_path
            if saved_path.resolve() != DEFAULT_CONFIG_PATH.resolve():
                self.write_config_to_yaml(DEFAULT_CONFIG_PATH)
            self.settings.setValue("config_path", str(self.config_path))
            self.save_settings()
            self.config_status_lbl.setText(f"Profile: {self.config_path.name} (saved)")
            self.config_status_lbl.setToolTip(str(self.config_path))
            self.progress.setText(f"Configuration saved to {self.config_path}")
        except Exception as ex:
            QMessageBox.critical(self, "Could not save configuration", f"Failed to save YAML configuration:\n{ex}")

    def save_config_yaml_as(self):
        initial = str(self.config_path if self.config_path else DEFAULT_CONFIG_PATH)
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration Profile (.yaml)",
            initial,
            "YAML Configuration (*.yaml *.yml);;All Files (*)",
        )
        if not chosen:
            return
        try:
            saved_path = self.write_config_to_yaml(chosen)
            self.config_path = saved_path
            # Also update default config.yaml so the app remembers the latest saved configuration by default
            if saved_path.resolve() != DEFAULT_CONFIG_PATH.resolve():
                self.write_config_to_yaml(DEFAULT_CONFIG_PATH)
            self.settings.setValue("config_path", str(self.config_path))
            self.save_settings()
            self.config_status_lbl.setText(f"Profile: {self.config_path.name} (saved)")
            self.config_status_lbl.setToolTip(str(self.config_path))
            self.progress.setText(f"Configuration profile saved to {self.config_path}")
        except Exception as ex:
            QMessageBox.critical(self, "Could not save configuration", f"Failed to save YAML configuration:\n{ex}")

    def load_config_yaml_dialog(self):
        start_dir = str(self.config_path.parent if self.config_path else DEFAULT_CONFIG_PATH.parent)
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration Profile (.yaml)",
            start_dir,
            "YAML Configuration (*.yaml *.yml);;All Files (*)",
        )
        if not chosen:
            return
        if self.load_config_from_yaml(chosen, notify=True):
            # Sync default config.yaml with the newly loaded profile
            try:
                if Path(chosen).resolve() != DEFAULT_CONFIG_PATH.resolve():
                    self.write_config_to_yaml(DEFAULT_CONFIG_PATH)
            except Exception:
                pass

    def load_settings(self):
        s = self.settings
        self.dark_mode = s.value("dark_mode", True, type=bool)
        self.voice_dir = Path(s.value("voice_dir", str(DEFAULT_VOICE_DIR))).expanduser()
        saved_engine = s.value("engine", "")
        if saved_engine:
            idx = self.engine.findData(saved_engine)
            if idx >= 0:
                self.engine.setCurrentIndex(idx)
        self.chunk_size.setValue(s.value("chunk_size", 2, type=int))
        self.font_size.setValue(s.value("font_size", 17, type=int))
        self.speed_slider.setValue(s.value("speech_speed", 180, type=int))
        self.word_gap.setValue(s.value("word_gap_ms", 250, type=int))
        self.chunk_gap.setValue(s.value("chunk_gap_ms", 1800, type=int))
        self.loop_check.setChecked(s.value("loop_after_finish", False, type=bool))

        # Prefer YAML configuration if present (either last used profile or default config.yaml)
        saved_config_path = Path(s.value("config_path", str(DEFAULT_CONFIG_PATH))).expanduser()
        if saved_config_path.exists():
            self.load_config_from_yaml(saved_config_path, notify=False)
        elif DEFAULT_CONFIG_PATH.exists():
            self.load_config_from_yaml(DEFAULT_CONFIG_PATH, notify=False)

    def connect_setting_signals(self):
        self.engine.currentIndexChanged.connect(self.save_settings)
        self.chunk_size.valueChanged.connect(self.save_settings)
        self.chunk_size.valueChanged.connect(self.refresh_seek_slider_range)
        self.font_size.valueChanged.connect(self.save_settings)
        self.speed_slider.valueChanged.connect(self.save_settings)
        self.word_gap.valueChanged.connect(self.save_settings)
        self.chunk_gap.valueChanged.connect(self.save_settings)
        self.loop_check.stateChanged.connect(self.save_settings)

    def save_settings(self, *_):
        if not hasattr(self, "settings") or not hasattr(self, "chunk_gap"):
            return
        s = self.settings
        s.setValue("dark_mode", self.dark_mode)
        s.setValue("voice_dir", str(self.voice_dir))
        s.setValue("engine", self.selected_engine())
        s.setValue("chunk_size", self.chunk_size.value())
        s.setValue("font_size", self.font_size.value())
        s.setValue("speech_speed", self.speed_slider.value())
        s.setValue("word_gap_ms", self.word_gap.value())
        s.setValue("chunk_gap_ms", self.chunk_gap.value())
        s.setValue("loop_after_finish", self.loop_check.isChecked())
        s.setValue("config_path", str(self.config_path))
        s.sync()

    def prepare_text(self):
        self.stop_playback(reset_position=False)
        raw = self.editor.toPlainText()
        self.words, self.word_spans = speech_words_with_source_map(raw)
        self.index = 0
        self.current_chunk = ""
        self.current_chunk_start = 0
        self.current_chunk_end = 0
        self.editor.setExtraSelections([])
        self.refresh_seek_slider_range()
        self.set_seek_value(0)
        self.progress.setText(f"Prepared {len(self.words)} words. Click Play All for automatic chunk-by-chunk reading, or Speak Next for manual control.")
        if not self.words:
            QMessageBox.information(self, "No text", "Paste assignment text first, then click Prepare speech.")

    def highlight_chunk(self, start_word, end_word, scroll=True):
        if not self.word_spans or end_word <= start_word or start_word >= len(self.word_spans):
            self.editor.setExtraSelections([])
            return
        start_word = max(0, start_word)
        end_word = min(len(self.word_spans), end_word)
        source_start = self.word_spans[start_word][0]
        source_end = self.word_spans[end_word - 1][1]
        cursor = QTextCursor(self.editor.document())
        cursor.setPosition(max(0, source_start))
        cursor.setPosition(min(len(self.editor.toPlainText()), source_end), QTextCursor.MoveMode.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        fmt = QTextCharFormat()
        if self.dark_mode:
            fmt.setBackground(QColor("#405f91"))
            fmt.setForeground(QColor("#ffffff"))
        else:
            fmt.setBackground(QColor("#ffe08a"))
            fmt.setForeground(QColor("#172033"))
        fmt.setFontWeight(QFont.Weight.Bold)
        selection.format = fmt
        self.editor.setExtraSelections([selection])
        if scroll:
            rect = self.editor.cursorRect(cursor)
            viewport_height = max(1, self.editor.viewport().height())
            if rect.top() < 10 or rect.bottom() > viewport_height - 10:
                bar = self.editor.verticalScrollBar()
                bar.setValue(max(0, bar.value() + rect.top() - viewport_height // 3))

    def refresh_seek_slider_range(self, *_):
        total = (len(self.words) + self.chunk_size.value() - 1) // self.chunk_size.value() if self.words else 0
        blocker = QSignalBlocker(self.seek_slider)
        self.seek_slider.setRange(0, max(0, total - 1))
        self.seek_slider.setEnabled(total > 0)
        if total:
            active_index = min(total - 1, max(0, self.current_chunk_start // self.chunk_size.value()))
            self.seek_slider.setValue(active_index)
        else:
            self.seek_slider.setValue(0)
        del blocker
        self.update_seek_label(self.seek_slider.value())

    def set_seek_value(self, value):
        blocker = QSignalBlocker(self.seek_slider)
        self.seek_slider.setValue(value)
        del blocker
        self.update_seek_label(value)

    def update_seek_label(self, value):
        total = (len(self.words) + self.chunk_size.value() - 1) // self.chunk_size.value() if self.words else 0
        self.seek_label.setText(f"Chunk {value + 1 if total else 0} / {total}")

    def on_seek_pressed(self):
        self.seeking = True
        self.seek_resume_after = self.auto_run and not self.paused
        self.seek_was_paused = self.paused

    def on_seek_released(self):
        if not self.words:
            self.seeking = False
            return
        target_chunk = self.seek_slider.value()
        should_resume = self.seek_resume_after
        should_remain_paused = self.seek_was_paused
        self.seeking = False
        # Invalidate a pending Piper response and stop any audio currently playing.
        self.auto_run = False
        self.paused = False
        self.request_id += 1
        self._kill_active_process()
        self.index = min(len(self.words), target_chunk * self.chunk_size.value())
        self.current_chunk_start = self.index
        self.current_chunk_end = min(len(self.words), self.index + self.chunk_size.value())
        self.current_chunk = " ".join(self.words[self.current_chunk_start:self.current_chunk_end])
        self.highlight_chunk(self.current_chunk_start, self.current_chunk_end)
        self.progress.setText(f"Selected chunk {target_chunk + 1}. Position set to word {self.index + 1} of {len(self.words)}.")
        if should_remain_paused:
            self.auto_run = True
            self.paused = True
            self.play_btn.setText("▶ Resume")
            self.pause_btn.setText("Ⅱ Paused")
            self.progress.setText(f"Paused at chunk {target_chunk + 1}. Press Resume or Space to continue.")
        elif should_resume:
            self.auto_run = True
            self.paused = False
            self.play_btn.setText("▶ Playing…")
            self.pause_btn.setText("Ⅱ Pause")
            QTimer.singleShot(0, self.advance_chunk)
        else:
            self.play_btn.setText("▶ Play All")
            self.pause_btn.setText("Ⅱ Pause")

    def selected_engine(self): return self.engine.currentData()
    def piper_installed(self):
        try:
            import importlib.util
            return importlib.util.find_spec("piper") is not None
        except Exception: return False
    def on_engine_changed(self): self.refresh_engine_status()
    def refresh_engine_status(self):
        if not hasattr(self, "status"):
            return
        if self.selected_engine() == "piper":
            if not self.piper_installed():
                self.status.setText("Piper not installed in this Python environment — open setup instructions.")
            elif not (self.voice_dir / f"{PIPER_MODEL}.onnx").exists():
                self.status.setText(f"Piper model missing from {self.voice_dir}")
            else:
                self.status.setText("Piper neural voice ready; local/offline speech after setup")
        else:
            if not shutil.which("espeak-ng"):
                self.status.setText("eSpeak NG missing — install it with: sudo apt install espeak-ng")
            else:
                self.status.setText("eSpeak NG selected — fastest, fully offline, robotic voice")
    def show_piper_setup(self):
        msg=("Piper is a neural voice that sounds more natural than eSpeak NG. It works offline after a one-time download.\n\n"
        "Open Terminal and run:\n\nsource ~/assignment-reader-env/bin/activate\npip install 'piper-tts[http]'\nmkdir -p ~/assignment-reader/voices\npython -m piper.download_voices en_US-lessac-medium --data-dir ~/assignment-reader/voices\n\n"
        "Restart this app using the same environment. Select Piper neural voice. The app starts Piper's local server when needed.\n\n"
        "For audio playback tools run: sudo apt install pulseaudio-utils alsa-utils\n\n"
        "Piper model CLI docs: https://github.com/hawkhai/piper-tts/blob/main/docs/CLI.md")
        QMessageBox.information(self,"Set up Piper neural voice",msg)
    def choose_voice_dir(self):
        chosen=QFileDialog.getExistingDirectory(self,"Choose Piper voice model folder",str(self.voice_dir))
        if chosen: self.voice_dir=Path(chosen).expanduser(); self.refresh_engine_status(); self.save_settings()
    def ensure_piper_server(self):
        if not self.piper_installed():
            self.show_piper_setup()
            return False
        model_path = self.voice_dir / f"{PIPER_MODEL}.onnx"
        if not model_path.exists():
            QMessageBox.warning(
                self, "Piper voice not found",
                f"Could not find {model_path}\nChoose the correct folder or open Piper setup instructions."
            )
            return False

        # Reuse only the server launched by this app. Do not assume port 5000
        # belongs to Piper; another program may be listening there.
        if self.piper_server and self.piper_server.poll() is None and self.piper_port:
            return True

        try:
            # Let the OS choose an available localhost port.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_socket:
                port_socket.bind(("127.0.0.1", 0))
                self.piper_port = port_socket.getsockname()[1]

            self.piper_server = subprocess.Popen(
                [
                    sys.executable, "-m", "piper.http_server",
                    "-m", PIPER_MODEL,
                    "--data-dir", str(self.voice_dir),
                    "--host", "127.0.0.1",
                    "--port", str(self.piper_port),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as ex:
            QMessageBox.critical(self, "Could not start Piper", str(ex))
            return False

    def space_action(self, force=False):
        # Plain Space is reserved for typing while the editor has focus.
        # Ctrl+Space toggles playback even when the editor is focused.
        if self.editor.hasFocus() and not force:
            return
        if self.paused:
            self.play_all_or_resume()
        elif self.auto_run:
            self.pause_playback()
        else:
            self.play_all_or_resume()
    def play_all_or_resume(self):
        if not self.words: self.prepare_text()
        if not self.words: return
        if self.paused:
            self.paused=False; self.auto_run=True
            if self.piper_thread and self.piper_thread.isRunning():
                self.progress.setText("Resuming; waiting for the current neural voice chunk…"); self.play_btn.setText("▶ Playing…"); self.pause_btn.setText("Ⅱ Pause"); return
            if self.active_process and self.active_process.state()!=QProcess.NotRunning:
                try: os.kill(int(self.active_process.processId()),signal.SIGCONT)
                except Exception: pass
                self.progress.setText("Resumed playback."); self.play_btn.setText("▶ Playing…"); self.pause_btn.setText("Ⅱ Pause"); return
            self.play_btn.setText("▶ Playing…"); self.pause_btn.setText("Ⅱ Pause"); self.advance_chunk(); return
        if self.index>=len(self.words): self.index=0
        # If a manual chunk is already in progress, turn on auto-advance after it finishes.
        if (self.active_process and self.active_process.state()!=QProcess.NotRunning) or (self.piper_thread and self.piper_thread.isRunning()):
            self.auto_run=True; self.paused=False; self.play_btn.setText("▶ Playing…"); self.pause_btn.setText("Ⅱ Pause"); return
        self.auto_run=True; self.paused=False; self.play_btn.setText("▶ Playing…"); self.pause_btn.setText("Ⅱ Pause"); self.advance_chunk()
    def pause_playback(self):
        if not self.auto_run and not (self.active_process and self.active_process.state()!=QProcess.NotRunning): self.progress.setText("Playback is not running."); return
        self.paused=True
        if self.active_process and self.active_process.state()!=QProcess.NotRunning:
            try: os.kill(int(self.active_process.processId()),signal.SIGSTOP)
            except Exception: pass
        self.play_btn.setText("▶ Resume"); self.pause_btn.setText("Ⅱ Paused"); self.progress.setText("Paused. Click Resume to continue.")
    def stop_playback(self,reset_position=True):
        self.auto_run=False; self.paused=False; self.request_id+=1; self._kill_active_process()
        self.play_btn.setText("▶ Play All"); self.pause_btn.setText("Ⅱ Pause")
        if reset_position: self.progress.setText(f"Stopped. Next position: word {self.index+1} of {len(self.words)}.")
    def _kill_active_process(self):
        if self.active_process and self.active_process.state()!=QProcess.NotRunning: self.active_process.kill()
        self.active_process=None; self.active_kind=None
        if self.temp_audio:
            try: os.unlink(self.temp_audio)
            except OSError: pass
            self.temp_audio=None
    def speak_next_manual(self):
        if not self.words: self.prepare_text()
        if not self.words: return
        self.stop_playback(reset_position=False); self.advance_chunk(manual=True)
    def repeat_previous(self):
        if not self.current_chunk: self.progress.setText("Nothing to repeat yet. Prepare text and speak a chunk first."); return
        self.stop_playback(reset_position=False); self._speak(self.current_chunk,repeated=True)
    def advance_chunk(self, manual=False):
        if self.paused or self.seeking:
            return
        if self.index >= len(self.words):
            if self.auto_run and self.loop_check.isChecked():
                self.index = 0
            else:
                self.auto_run = False
                self.play_btn.setText("▶ Play All")
                self.pause_btn.setText("Ⅱ Pause")
                self.progress.setText("Finished reading all prepared text.")
                return
        start = self.index
        end = min(len(self.words), start + self.chunk_size.value())
        self.current_chunk_start = start
        self.current_chunk_end = end
        self.current_chunk = " ".join(self.words[start:end])
        self.index = end
        self.highlight_chunk(start, end)
        self.set_seek_value(min(start // self.chunk_size.value(), max(0, self.seek_slider.maximum())))
        self.progress.setText(f"Speaking words {start + 1}–{end} of {len(self.words)}  |  “{self.current_chunk}”")
        self._speak(self.current_chunk)
    def _speak(self,text,repeated=False):
        self.request_id+=1; token=self.request_id
        if self.selected_engine()=="piper":
            if not self.ensure_piper_server(): self.auto_run=False; self.play_btn.setText("▶ Play All"); return
            self.active_kind="piper_synth"; worker=PiperWorker(token,text,self.speed_slider.value(),self.piper_port or PIPER_PORT,self); self.piper_thread=worker; self.piper_threads.append(worker); worker.result_ready.connect(self.on_piper_audio_ready); worker.start(); return
        exe=shutil.which("espeak-ng")
        if not exe:
            QMessageBox.warning(self,"eSpeak NG not found","Install it with: sudo apt install espeak-ng"); self.auto_run=False; return
        process=QProcess(self); process.setProgram(exe); process.setArguments(["-s",str(self.speed_slider.value()),"-g",str(max(0,min(200,round(self.word_gap.value()/10)))),"--stdin"]); process.setStandardOutputFile(os.devnull)
        process.finished.connect(lambda code,status,p=process,tok=token:self.on_espeak_finished(code,status,p,tok)); self.active_process=process; self.active_kind="espeak"; process.start()
        if process.waitForStarted(1000): process.write(text.encode("utf-8")); process.closeWriteChannel()
        else: self.progress.setText("Could not start eSpeak NG."); self.auto_run=False
    def on_espeak_finished(self,code,status,process,token):
        if token!=self.request_id: return
        if process==self.active_process: self.active_process=None; self.active_kind=None
        if self.auto_run and not self.paused and not self.seeking: QTimer.singleShot(self.chunk_gap.value(),lambda: self.advance_chunk() if self.auto_run and not self.paused and not self.seeking else None)
        elif not self.auto_run: self.play_btn.setText("▶ Play All")
    def on_piper_audio_ready(self,token,audio,error):
        thread=self.sender()
        if thread and thread.isRunning(): thread.wait(50)
        if thread in self.piper_threads: self.piper_threads.remove(thread)
        is_current = token == self.request_id
        if self.piper_thread is thread: self.piper_thread=None
        if not is_current:
            # If Play All was pressed while an old synthesis request was winding down,
            # continue with the current cursor position instead of getting stuck.
            if self.auto_run and not self.paused and not self.seeking and not (self.active_process and self.active_process.state()!=QProcess.NotRunning) and not (self.piper_thread and self.piper_thread.isRunning()):
                QTimer.singleShot(0, self.advance_chunk)
            return
        if self.seeking:
            return
        if error:
            self.progress.setText(f"Piper error: {error}. Check Piper setup; eSpeak NG remains available.")
            self.auto_run=False; self.play_btn.setText("▶ Play All"); return
        try:
            fd,path=tempfile.mkstemp(prefix="assignment-reader-",suffix=".wav"); os.close(fd)
            with open(path,"wb") as f: f.write(audio)
            self.temp_audio=path; player=next((shutil.which(n) for n in ("paplay","aplay","ffplay") if shutil.which(n)),None)
            if not player:
                os.unlink(path); self.temp_audio=None; QMessageBox.warning(self,"Audio player not found","Install a player with: sudo apt install pulseaudio-utils alsa-utils"); self.auto_run=False; self.play_btn.setText("▶ Play All"); return
            p=QProcess(self)
            if Path(player).name=="paplay": p.setProgram(player); p.setArguments([path])
            elif Path(player).name=="aplay": p.setProgram(player); p.setArguments(["-q",path])
            else: p.setProgram(player); p.setArguments(["-nodisp","-autoexit","-loglevel","quiet",path])
            p.setStandardOutputFile(os.devnull); p.setStandardErrorFile(os.devnull); p.finished.connect(lambda c,s,proc=p,tok=token:self.on_audio_finished(c,s,proc,tok))
            self.active_process=p; self.active_kind="piper_audio"; p.start()
            if not p.waitForStarted(1000): self.progress.setText("Could not start audio player. Install pulseaudio-utils or alsa-utils."); self.auto_run=False; self.play_btn.setText("▶ Play All")
            elif self.paused:
                QTimer.singleShot(150,lambda proc=p:self._suspend_if_paused(proc))
        except Exception as ex:
            self.progress.setText(f"Audio playback error: {ex}"); self.auto_run=False; self.play_btn.setText("▶ Play All")
    def _suspend_if_paused(self,proc):
        if self.paused and proc.state()!=QProcess.NotRunning:
            try: os.kill(int(proc.processId()),signal.SIGSTOP)
            except Exception: pass
    def on_audio_finished(self,code,status,process,token):
        if token!=self.request_id: return
        if process==self.active_process: self.active_process=None; self.active_kind=None
        if self.temp_audio:
            try: os.unlink(self.temp_audio)
            except OSError: pass
            self.temp_audio=None
        if self.auto_run and not self.paused and not self.seeking: QTimer.singleShot(self.chunk_gap.value(),lambda: self.advance_chunk() if self.auto_run and not self.paused and not self.seeking else None)
        elif not self.auto_run: self.play_btn.setText("▶ Play All")
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not self.editor.hasFocus():
            self.space_action()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self,event):
        self.save_settings()
        self.auto_run=False; self._kill_active_process()
        if self.piper_server and self.piper_server.poll() is None:
            self.piper_server.terminate()
            try: self.piper_server.wait(timeout=2)
            except subprocess.TimeoutExpired: self.piper_server.kill()
        for worker in list(self.piper_threads):
            if worker.isRunning(): worker.wait(1000)
        event.accept()

def main():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); win=AssignmentReader(); win.show(); sys.exit(app.exec())
if __name__=="__main__": main()
