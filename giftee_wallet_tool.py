import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QDialog,
    QVBoxLayout,
    QWidget,
)


ROOT = Path(__file__).resolve().parent
NODE = "node"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = ROOT / "giftee_chrome_profile"
TEST_PROFILE_DIR = ROOT / "giftee_chrome_profile_test_empty"
TL_APP_PROFILE_DIR = PROFILE_DIR


class Pill(QFrame):
    def __init__(self, text, color="#16a085"):
        super().__init__()
        self.setObjectName("pill")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background:{color}; border-radius:4px;")
        label = QLabel(text)
        label.setObjectName("pillText")
        layout.addWidget(dot)
        layout.addWidget(label)


class StatCard(QFrame):
    def __init__(self, title, value, suffix="", accent="#0f766e"):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        row = QHBoxLayout()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        self.suffix_label = QLabel(suffix)
        self.suffix_label.setObjectName("statSuffix")
        row.addWidget(self.value_label)
        row.addWidget(self.suffix_label)
        row.addStretch()
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background:{accent}; border-radius:2px;")
        layout.addWidget(title_label)
        layout.addLayout(row)
        layout.addWidget(bar)

    def set_value(self, value, suffix=None):
        self.value_label.setText(str(value))
        if suffix is not None:
            self.suffix_label.setText(str(suffix))


class FilePicker(QWidget):
    def __init__(self, label, value, mode="open", pattern="Text files (*.txt);;All files (*.*)"):
        super().__init__()
        self.mode = mode
        self.pattern = pattern
        self.edit = QLineEdit(value)
        self.edit.setMinimumHeight(38)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        title = QLabel(label)
        title.setObjectName("fieldLabel")
        row = QHBoxLayout()
        row.setSpacing(8)
        button = QPushButton("Chọn")
        button.setObjectName("secondaryButton")
        button.setFixedWidth(76)
        button.clicked.connect(self.choose)
        row.addWidget(self.edit)
        row.addWidget(button)
        layout.addWidget(title)
        layout.addLayout(row)

    def choose(self):
        current = self.edit.text().strip()
        initial = str(Path(current).parent if current else ROOT)
        if self.mode == "save":
            path, _ = QFileDialog.getSaveFileName(self, "Chọn file", initial, self.pattern)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Chọn file", initial, self.pattern)
        if path:
            self.edit.setText(path)

    def text(self):
        return self.edit.text().strip()


class NumberField(QWidget):
    def __init__(self, label, value, minimum=0, maximum=999999):
        super().__init__()
        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setMinimumHeight(38)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        title = QLabel(label)
        title.setObjectName("fieldLabel")
        layout.addWidget(title)
        layout.addWidget(self.spin)

    def value(self):
        return self.spin.value()


class ActionCard(QFrame):
    def __init__(self, title, subtitle=""):
        super().__init__()
        self.setObjectName("actionCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 14, 18, 16)
        self.body.setSpacing(12)
        header = QVBoxLayout()
        header.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        header.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("cardSubtitle")
            subtitle_label.setWordWrap(True)
            header.addWidget(subtitle_label)
        self.body.addLayout(header)


class LoginGateDialog(QDialog):
    def __init__(self, parent, profile_dir=PROFILE_DIR):
        super().__init__(parent)
        self.parent_tool = parent
        self.profile_dir = Path(profile_dir)
        self.setWindowTitle("Đăng nhập Gift Wallet")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setObjectName("loginDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("Cần đăng nhập Gift Wallet")
        title.setObjectName("loginTitle")
        desc = QLabel(
            "Lần đầu chạy trên máy mới, tool sẽ tạo Chrome profile riêng. "
            "Bạn mở Chrome bằng nút bên dưới, login gift wallet, đóng Chrome sau khi login xong, "
            "rồi bấm kiểm tra lại."
        )
        desc.setObjectName("loginDesc")
        desc.setWordWrap(True)

        profile = QLabel(f"Profile local:\n{self.profile_dir}")
        profile.setObjectName("loginProfile")
        profile.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.status = QLabel("Chưa xác nhận session.")
        self.status.setObjectName("loginStatus")

        row = QHBoxLayout()
        open_btn = QPushButton("Mở Chrome để login")
        open_btn.setObjectName("primaryButton")
        open_btn.clicked.connect(lambda: parent.open_login_chrome(self.profile_dir))
        check_btn = QPushButton("Tôi đã login xong, kiểm tra lại")
        check_btn.setObjectName("secondaryButton")
        check_btn.clicked.connect(lambda: parent.check_login(show_success=True, dialog=self, profile_dir=self.profile_dir))
        skip_btn = QPushButton("Vào app")
        skip_btn.setObjectName("secondaryButton")
        skip_btn.clicked.connect(self.accept)
        row.addWidget(open_btn)
        row.addWidget(check_btn)
        row.addWidget(skip_btn)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(profile)
        layout.addWidget(self.status)
        layout.addLayout(row)

    def set_status(self, text, ok=False):
        self.status.setText(text)
        self.status.setStyleSheet("color: #0f766e; font-weight: 800;" if ok else "color: #b84d3c; font-weight: 800;")


class GifteeQtTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giftee Wallet Tool")
        self.resize(1240, 800)
        self.setMinimumSize(1120, 720)

        self.process = None
        self.tl_check_process = None
        self.pending_tl_date_mode = None
        self.current_mode = ""
        self.processed_count = 0
        self.total_hint = 0

        self._build_ui()
        self._apply_style()
        QTimer.singleShot(600, self.check_login_on_startup)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(26, 22, 26, 22)
        content_layout.setSpacing(18)
        root_layout.addWidget(content, 1)

        self.header_title = QLabel("Quản lý Giftee Wallet")
        self.header_title.setObjectName("heroTitle")
        subtitle = QLabel("Kiểm tra link còn point và nạp vào gift wallet bằng Chrome profile local.")
        subtitle.setObjectName("heroSubtitle")
        header_left = QVBoxLayout()
        header_left.setSpacing(4)
        header_left.addWidget(self.header_title)
        header_left.addWidget(subtitle)
        header = QHBoxLayout()
        header.addLayout(header_left)
        header.addStretch()
        header.addWidget(Pill("Chrome profile local"))
        content_layout.addLayout(header)

        stats = QGridLayout()
        stats.setHorizontalSpacing(12)
        stats.setVerticalSpacing(12)
        self.total_card = StatCard("Tổng link", "--", "links", "#0f766e")
        self.merged_card = StatCard("Đã nạp", "--", "links", "#2563eb")
        self.left_card = StatCard("Còn sót", "--", "links", "#dc6b52")
        self.point_card = StatCard("Point còn sót", "--", "JPY", "#b7791f")
        for col, card in enumerate([self.total_card, self.merged_card, self.left_card, self.point_card]):
            stats.addWidget(card, 0, col)
        content_layout.addLayout(stats)

        work = QHBoxLayout()
        work.setSpacing(18)
        content_layout.addLayout(work, 1)

        main_col = QVBoxLayout()
        main_col.setSpacing(14)
        work.addLayout(main_col, 2)

        self.stack = QStackedWidget()
        self._init_hidden_check_fields()
        self.stack.addWidget(self._build_tl_app_page())
        self.stack.addWidget(self._build_merge_page())
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        main_col.addWidget(self.stack, 0)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logBox")
        self.log.setFixedHeight(270)
        self.log.setPlaceholderText("Log sẽ hiển thị ở đây...")
        main_col.addWidget(self.log, 0)
        main_col.addStretch(1)

        right = self._build_right_panel()
        work.addWidget(right, 1)
        QTimer.singleShot(0, self.refresh_stats)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(226)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(16)

        logo_row = QHBoxLayout()
        logo = QLabel("G")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(42, 42)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        name = QLabel("Giftee Wallet")
        name.setObjectName("brandName")
        desc = QLabel("Automation Tool")
        desc.setObjectName("brandDesc")
        brand.addWidget(name)
        brand.addWidget(desc)
        logo_row.addWidget(logo)
        logo_row.addLayout(brand)
        layout.addLayout(logo_row)

        self.tl_app_nav = QPushButton("  Lấy link TL-APP")
        self.merge_nav = QPushButton("  Nạp vào ví")
        for btn in [self.tl_app_nav, self.merge_nav]:
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(42)
            layout.addWidget(btn)
        self.tl_app_nav.setChecked(True)
        self.tl_app_nav.clicked.connect(lambda: self._set_page(0))
        self.merge_nav.clicked.connect(lambda: self._set_page(1))

        layout.addStretch()
        session = QFrame()
        session.setObjectName("sessionBox")
        session_layout = QVBoxLayout(session)
        session_layout.setContentsMargins(12, 12, 12, 12)
        session_layout.setSpacing(6)
        session_title = QLabel("Session")
        session_title.setObjectName("sessionTitle")
        session_text = QLabel("giftee_chrome_profile\nLocal only")
        session_text.setObjectName("sessionText")
        session_layout.addWidget(session_title)
        session_layout.addWidget(session_text)
        layout.addWidget(session)
        return sidebar

    def _init_hidden_check_fields(self):
        self.check_input = FilePicker("Input links", str(ROOT / "input_giftee_links.txt"))
        self.check_csv = FilePicker("Scan results", str(ROOT / "giftee_scan_results.csv"), "save", "CSV files (*.csv);;All files (*.*)")
        self.check_left = FilePicker("Pending links", str(ROOT / "pending_giftee_links.txt"), "save")
        for widget in [self.check_input, self.check_csv, self.check_left]:
            widget.hide()

    def _build_tl_app_page(self):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = ActionCard("Lấy link từ TL-APP")
        self.tl_output = FilePicker("File link xuất ra", str(ROOT / "tl_app_links_today.txt"), "save")
        card.body.addWidget(self.tl_output)

        row = QHBoxLayout()
        login_btn = QPushButton("Chrome login TL-APP")
        login_btn.setObjectName("secondaryButton")
        login_btn.clicked.connect(self.open_tl_app_chrome)
        self.today_btn = QPushButton("Lấy link hôm nay")
        self.today_btn.setObjectName("primaryButton")
        self.today_btn.clicked.connect(lambda: self.run_scan_history("today"))
        self.all_btn = QPushButton("Scan tất cả link")
        self.all_btn.setObjectName("secondaryButton")
        self.all_btn.clicked.connect(lambda: self.run_scan_history("all"))
        open_btn = QPushButton("Mở thư mục")
        open_btn.setObjectName("secondaryButton")
        open_btn.clicked.connect(self.open_root)
        for btn in [login_btn, self.today_btn, self.all_btn, open_btn]:
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row.addWidget(btn)
        card.body.addLayout(row)
        layout.addWidget(card)
        return page

    def _build_merge_page(self):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = ActionCard("Nạp link vào ví")
        self.merge_input = FilePicker("File link chờ nạp", str(ROOT / "pending_giftee_links.txt"))
        card.body.addWidget(self.merge_input)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.merge_button = QPushButton("Nạp point vào ví")
        self.merge_button.setObjectName("primaryButton")
        self.merge_button.clicked.connect(self.run_merge)
        stop_btn = QPushButton("Dừng")
        stop_btn.setObjectName("dangerButton")
        stop_btn.clicked.connect(self.stop_process)
        open_btn = QPushButton("Mở thư mục")
        open_btn.setObjectName("secondaryButton")
        open_btn.clicked.connect(self.open_root)
        for btn in [self.merge_button, stop_btn, open_btn]:
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(self.merge_button, 2)
        row.addWidget(stop_btn, 1)
        row.addWidget(open_btn, 1)
        card.body.addLayout(row)
        layout.addWidget(card)
        return page

    def _build_right_panel(self):
        panel = QVBoxLayout()
        wrap = QFrame()
        wrap.setObjectName("rightPanel")
        wrap.setMinimumWidth(270)
        wrap.setLayout(panel)
        panel.setContentsMargins(16, 16, 16, 16)
        panel.setSpacing(14)

        progress_card = QFrame()
        progress_card.setObjectName("sideCard")
        p_layout = QVBoxLayout(progress_card)
        p_layout.setContentsMargins(14, 14, 14, 14)
        p_layout.setSpacing(10)
        title = QLabel("Tiến độ")
        title.setObjectName("sideTitle")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress_label = QLabel("Chưa chạy tiến trình nào")
        self.progress_label.setObjectName("mutedText")
        p_layout.addWidget(title)
        p_layout.addWidget(self.progress)
        p_layout.addWidget(self.progress_label)
        panel.addWidget(progress_card)

        recent = QFrame()
        recent.setObjectName("sideCard")
        r_layout = QVBoxLayout(recent)
        r_layout.setContentsMargins(14, 14, 14, 14)
        r_layout.setSpacing(10)
        r_title = QLabel("Trạng thái")
        r_title.setObjectName("sideTitle")
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setObjectName("statusBig")
        self.detail_label = QLabel("Chọn chức năng ở bên trái để bắt đầu.")
        self.detail_label.setObjectName("mutedText")
        self.detail_label.setWordWrap(True)
        r_layout.addWidget(r_title)
        r_layout.addWidget(self.status_label)
        r_layout.addWidget(self.detail_label)
        panel.addWidget(recent)

        files = QFrame()
        files.setObjectName("sideCard")
        f_layout = QVBoxLayout(files)
        f_layout.setContentsMargins(14, 14, 14, 14)
        f_layout.setSpacing(8)
        f_layout.addWidget(QLabel("Kết quả tự lưu", objectName="sideTitle"))
        for text in ["giftee_scan_results.csv", "pending_giftee_links.txt", "wallet_merge_results.csv"]:
            label = QLabel(text)
            label.setObjectName("fileChip")
            f_layout.addWidget(label)
        panel.addWidget(files)
        panel.addStretch()
        return wrap

    def _set_page(self, index):
        self.stack.setCurrentIndex(index)
        self.tl_app_nav.setChecked(index == 0)
        self.merge_nav.setChecked(index == 1)
        titles = ["Lấy link từ TL-APP", "Nạp point vào Gift Wallet"]
        self.header_title.setText(titles[index])

    def run_scan_history(self, date_mode):
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Đang chạy", "Một tiến trình đang chạy. Hãy dừng hoặc chờ xong.")
            return
        if self.tl_check_process and self.tl_check_process.state() != QProcess.NotRunning:
            return

        script = ROOT / "verify_tl_app_session.js"
        if not script.exists():
            QMessageBox.warning(self, "Thiếu script", f"Không tìm thấy {script}")
            return

        self.pending_tl_date_mode = date_mode
        self.update_scan_buttons(date_mode)
        self.progress.setRange(0, 0)
        self.status_label.setText("Đang kiểm tra TL-APP")
        self.detail_label.setText("Kiểm tra session TL-APP trong chrome profile local...")
        self.log.appendPlainText("\n=== VERIFY_TL_APP_SESSION START ===")

        self.tl_check_process = QProcess(self)
        self.tl_check_process.setWorkingDirectory(str(ROOT))
        self.tl_check_process.setProcessChannelMode(QProcess.MergedChannels)
        self.tl_check_process.finished.connect(self.tl_app_login_check_finished)
        self.tl_check_process.start(NODE, [str(script), "--profile", str(PROFILE_DIR)])
        return

    def update_scan_buttons(self, date_mode):
        if not hasattr(self, "today_btn") or not hasattr(self, "all_btn"):
            return
        self.today_btn.setObjectName("primaryButton" if date_mode == "today" else "secondaryButton")
        self.all_btn.setObjectName("primaryButton" if date_mode == "all" else "secondaryButton")
        self.today_btn.style().unpolish(self.today_btn)
        self.today_btn.style().polish(self.today_btn)
        self.all_btn.style().unpolish(self.all_btn)
        self.all_btn.style().polish(self.all_btn)

    def tl_app_login_check_finished(self, _code, _status):
        self.progress.setRange(0, 100)
        output = ""
        if self.tl_check_process:
            output = bytes(self.tl_check_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        raw = output.strip().splitlines()[-1] if output.strip() else "{}"
        try:
            data = json.loads(raw)
        except Exception:
            data = {"loggedIn": False, "note": "ERROR", "error": raw}

        if not data.get("loggedIn"):
            self.status_label.setText("TL-APP chưa login")
            self.detail_label.setText(data.get("note") or data.get("error") or "Cần login TL-APP trước khi scan.")
            self.log.appendPlainText(f"TL-APP login check: NOT_LOGGED_IN {data.get('error', '')}")
            QMessageBox.warning(
                self,
                "TL-APP chưa login",
                "Chưa thấy session TL-APP trong profile local. Tool sẽ mở Chrome để bạn login. Login xong quay lại bấm scan lại.",
            )
            self.open_tl_app_chrome()
            return

        username = data.get("username") or ""
        points = data.get("points")
        detail = data.get("url") or "https://tl-app.pro.vn/"
        if username:
            detail = f"{username} | {detail}"
        if points not in ("", None):
            detail = f"{detail} | {points} points"
        self.status_label.setText("TL-APP đã login")
        self.detail_label.setText(detail)
        self.log.appendPlainText(f"TL-APP login check: LOGGED_IN {username}".rstrip())
        self._start_history_scan(self.pending_tl_date_mode or "today")

    def _start_history_scan(self, date_mode):
        script = ROOT / "scan_tl_app_history.js"
        output = Path(self.tl_output.text())
        csv_output = output.with_suffix(".csv")
        cmd = [
            NODE,
            str(script),
            "--date",
            date_mode,
            "--output",
            str(output),
            "--csv",
            str(csv_output),
        ]
        self.total_hint = 0
        self.start_process(cmd, "SCAN_HISTORY")

    def run_merge(self):
        tl_left = ROOT / "pending_giftee_links.txt"
        if tl_left.exists():
            self.merge_input.edit.setText(str(tl_left))
        elif Path(self.merge_input.text()).name == "pending_giftee_links.txt":
            QMessageBox.information(
                self,
                "Chưa có danh sách chờ nạp",
                "Chưa có file pending_giftee_links.txt. Hãy scan TL-APP trước, tool sẽ tự tạo file này sau khi kiểm tra link.",
            )
            return
        left_count = self._count_links(self.merge_input.text(), 1, 0)
        if left_count == 0:
            QMessageBox.information(self, "Không có link cần nạp", "Danh sách link chờ nạp đang trống. Hãy scan TL-APP trước hoặc chọn file pending links khác.")
            self.set_stats(self.total_card.value_label.text(), self.merged_card.value_label.text(), 0, 0)
            return
        script = ROOT / "merge_giftee_points.js"
        output = ROOT / "wallet_merge_results.csv"
        cmd = [
            NODE,
            str(script),
            "--input",
            self.merge_input.text(),
            "--start",
            "1",
            "--limit",
            "0",
            "--output",
            str(output),
            "--wait",
            "1500",
            "--gap",
            "1000",
            "--no-prompt",
        ]
        self.total_hint = left_count
        self.start_process(cmd, "MERGE_POINTS")

    def start_process(self, cmd, mode):
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Đang chạy", "Một tiến trình đang chạy. Hãy dừng hoặc chờ xong.")
            return
        self.current_mode = mode
        self.processed_count = 0
        self.progress.setValue(0)
        self.status_label.setText("Đang chạy")
        self.detail_label.setText(" ".join(cmd))
        self.log.appendPlainText(f"\n=== {mode} START ===")
        self.log.appendPlainText(" ".join(f'"{p}"' if " " in p else p for p in cmd))

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(ROOT))
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        self.process.start(cmd[0], cmd[1:])

    def read_output(self):
        if not self.process:
            return
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if text:
            self.log.appendPlainText(text.rstrip())
            self._update_progress_from_text(text)

    def process_finished(self, code, _status):
        finished_mode = self.current_mode
        self.status_label.setText("Hoàn tất" if code == 0 else f"Lỗi code={code}")
        self.detail_label.setText("Xem log và file CSV đầu ra để kiểm tra chi tiết.")
        if code == 0:
            self.progress.setValue(100)
            if finished_mode == "SCAN_HISTORY":
                self.update_stats_from_tl_links(self.tl_output.text())
            elif finished_mode == "SCAN_GIFTEE":
                self.update_stats_from_check_csv(self.check_csv.text())
                self.merge_input.edit.setText(str(ROOT / "pending_giftee_links.txt"))
            elif finished_mode == "MERGE_POINTS":
                self.update_stats_from_merge_csv(ROOT / "wallet_merge_results.csv")
                self.show_merge_summary(ROOT / "wallet_merge_results.csv")
        self.log.appendPlainText(f"=== {finished_mode} END code={code} ===")
        if code == 0 and finished_mode == "SCAN_HISTORY":
            self.start_tl_app_auto_check()

    def start_tl_app_auto_check(self):
        script = ROOT / "scan_giftee_links.js"
        input_file = Path(self.tl_output.text())
        out_csv = ROOT / "giftee_scan_results.csv"
        out_left = ROOT / "pending_giftee_links.txt"
        link_count = self._count_links(input_file, 1, 0)
        if not input_file.exists() or link_count == 0:
            self.set_stats(0, 0, 0, 0)
            self.detail_label.setText("TL-APP không có link hợp lệ để kiểm tra.")
            return

        self.check_csv.edit.setText(str(out_csv))
        self.check_left.edit.setText(str(out_left))
        self.status_label.setText("Đang kiểm tra link")
        self.detail_label.setText("Đã lấy link TL-APP, đang kiểm tra trạng thái point...")
        self.total_hint = link_count
        cmd = [NODE, str(script), str(input_file), str(out_csv), str(out_left)]
        self.start_process(cmd, "SCAN_GIFTEE")

    def stop_process(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            QTimer.singleShot(3000, self.process.kill)
            self.log.appendPlainText("Requested stop.")

    def refresh_stats(self):
        check_csv = Path(self.check_csv.text()) if hasattr(self, "check_csv") else ROOT / "giftee_scan_results.csv"
        fallback_csv = ROOT / "giftee_scan_results.csv"
        if check_csv.exists():
            self.update_stats_from_check_csv(check_csv)
        elif fallback_csv.exists():
            self.update_stats_from_check_csv(fallback_csv)
        else:
            self.set_stats("--", "--", "--", "--")

    def set_stats(self, total, merged, left, points):
        self.total_card.set_value(self._fmt_stat(total), "links")
        self.merged_card.set_value(self._fmt_stat(merged), "links")
        self.left_card.set_value(self._fmt_stat(left), "links")
        self.point_card.set_value(self._fmt_stat(points), "JPY")

    def update_stats_from_check_csv(self, path):
        try:
            rows = self._read_csv_rows(path)
            total = len(rows)
            merged = sum(1 for row in rows if str(row.get("status", "")).upper() == "DA_NAP")
            left_rows = [row for row in rows if str(row.get("status", "")).upper() == "CHUA_NAP"]
            points = sum(self._to_int(row.get("point")) for row in left_rows)
            self.set_stats(total, merged, len(left_rows), points)
        except Exception as exc:
            self.log.appendPlainText(f"Stats error: {exc}")

    def update_stats_from_tl_links(self, path):
        total = self._count_links(path, 1, 0)
        self.total_card.set_value(self._fmt_stat(total), "links")
        self.merged_card.set_value("--", "links")
        self.left_card.set_value("--", "links")
        self.point_card.set_value("--", "JPY")

    def update_stats_from_merge_csv(self, path):
        try:
            rows = self._read_csv_rows(path)
            total = len(rows)
            merged = sum(1 for row in rows if str(row.get("status", "")).upper() == "DA_NAP")
            left = total - merged
            points = sum(self._to_int(row.get("point")) for row in rows if str(row.get("status", "")).upper() != "DA_NAP")
            self.set_stats(total, merged, left, points)
        except Exception as exc:
            self.log.appendPlainText(f"Stats error: {exc}")

    def show_merge_summary(self, path):
        try:
            rows = self._read_csv_rows(path)
        except Exception as exc:
            QMessageBox.warning(self, "Không đọc được kết quả nạp", f"Không đọc được file kết quả:\n{path}\n\n{exc}")
            return

        total = len(rows)
        merged = sum(1 for row in rows if str(row.get("status", "")).upper() == "DA_NAP")
        errors = sum(1 for row in rows if str(row.get("status", "")).upper() == "ERROR")
        pending = total - merged - errors
        initial_points = sum(self._to_int(row.get("initialPoint")) for row in rows)
        output_name = Path(path).name

        if errors or pending:
            self.status_label.setText("Cần kiểm tra lại")
            self.detail_label.setText(f"Đã nạp {merged}/{total} link. Còn {pending} pending, {errors} lỗi.")
            QMessageBox.warning(
                self,
                "Nạp point chưa hoàn tất",
                (
                    f"Đã xử lý: {total} link\n"
                    f"Đã nạp/đã có trong ví: {merged} link\n"
                    f"Còn pending: {pending} link\n"
                    f"Lỗi: {errors} link\n"
                    f"Tổng point trong batch: {self._fmt_stat(initial_points)} JPY\n\n"
                    f"File kết quả: {output_name}"
                ),
            )
            return

        self.status_label.setText("Nạp point hoàn tất")
        self.detail_label.setText(f"Đã nạp/ghi nhận {merged}/{total} link vào Gift Wallet.")
        QMessageBox.information(
            self,
            "Nạp point hoàn tất",
            (
                f"Đã xử lý: {total} link\n"
                f"Đã nạp/đã có trong ví: {merged} link\n"
                f"Tổng point trong batch: {self._fmt_stat(initial_points)} JPY\n\n"
                f"File kết quả: {output_name}"
            ),
        )

    def _read_csv_rows(self, path):
        with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))

    def _to_int(self, value):
        try:
            return int(float(str(value or "0").replace(",", "")))
        except Exception:
            return 0

    def _fmt_stat(self, value):
        if value in ("", None, "--"):
            return "--"
        try:
            return f"{int(value):,}"
        except Exception:
            return str(value)

    def open_login_chrome(self, profile_dir=PROFILE_DIR):
        profile_dir = Path(profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(
                [
                    CHROME_EXE,
                    f"--user-data-dir={profile_dir}",
                    "https://wallet.vaton.jp/",
                ],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.log.appendPlainText(f"Opened Chrome login profile: {profile_dir}")
        except Exception as exc:
            QMessageBox.critical(self, "Không mở được Chrome", str(exc))

    def open_tl_app_chrome(self):
        TL_APP_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(
                [
                    CHROME_EXE,
                    f"--user-data-dir={TL_APP_PROFILE_DIR}",
                    "https://tl-app.pro.vn/",
                ],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.log.appendPlainText(f"Opened TL-APP Chrome profile: {TL_APP_PROFILE_DIR}")
        except Exception as exc:
            QMessageBox.critical(self, "Không mở được Chrome", str(exc))

    def check_login_on_startup(self):
        self.check_login(show_success=False, startup=True)

    def check_login(self, show_success=False, startup=False, dialog=None, profile_dir=PROFILE_DIR):
        script = ROOT / "verify_wallet_session.js"
        if not script.exists():
            QMessageBox.warning(self, "Thiếu script", f"Không tìm thấy {script}")
            return

        try:
            result = subprocess.run(
                [NODE, str(script), "--profile", str(profile_dir)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            raw = (result.stdout or "").strip().splitlines()[-1]
            data = json.loads(raw)
        except Exception as exc:
            data = {"loggedIn": False, "note": "ERROR", "error": str(exc), "url": ""}

        logged_in = bool(data.get("loggedIn"))
        note = data.get("note", "")
        url = data.get("url", "")
        if logged_in:
            self.status_label.setText("Wallet đã login")
            self.detail_label.setText(url or "Session đã sẵn sàng.")
            self.log.appendPlainText("Wallet login check: LOGGED_IN")
            if dialog:
                dialog.set_status("Đã login. Bạn có thể vào app.", ok=True)
                QTimer.singleShot(500, dialog.accept)
            elif show_success:
                QMessageBox.information(self, "Đã login", "Gift Wallet session đã sẵn sàng.")
            return

        self.status_label.setText("Chưa login wallet")
        self.detail_label.setText(note or "Cần login trong Chrome profile local trước khi nạp.")
        self.log.appendPlainText(f"Wallet login check: NOT_LOGGED_IN {data.get('error', '')}")
        if dialog:
            dialog.set_status("Chưa thấy session login. Login xong hãy đóng Chrome rồi kiểm tra lại.", ok=False)
        elif startup:
            gate = LoginGateDialog(self, profile_dir)
            gate.set_status("Chưa thấy session login.", ok=False)
            gate.exec()
        elif show_success:
            QMessageBox.warning(
                self,
                "Chưa login",
                "Chưa thấy session login. Bấm 'Mở Chrome login', login xong đóng Chrome rồi kiểm tra lại.",
            )

    def verify_tl_app_session(self, show_success=False):
        script = ROOT / "verify_tl_app_session.js"
        if not script.exists():
            QMessageBox.warning(self, "Thiếu script", f"Không tìm thấy {script}")
            return False

        try:
            result = subprocess.run(
                [NODE, str(script), "--profile", str(PROFILE_DIR)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            raw = (result.stdout or "").strip().splitlines()[-1]
            data = json.loads(raw)
        except Exception as exc:
            data = {"loggedIn": False, "note": "ERROR", "error": str(exc), "url": ""}

        logged_in = bool(data.get("loggedIn"))
        username = data.get("username") or ""
        points = data.get("points")
        url = data.get("url") or "https://tl-app.pro.vn/"

        if logged_in:
            detail = url
            if username:
                detail = f"{username} | {detail}"
            if points not in ("", None):
                detail = f"{detail} | {points} points"
            self.status_label.setText("TL-APP đã login")
            self.detail_label.setText(detail)
            self.log.appendPlainText(f"TL-APP login check: LOGGED_IN {username}".rstrip())
            if show_success:
                QMessageBox.information(self, "TL-APP đã login", "Session TL-APP đã sẵn sàng.")
            return True

        self.status_label.setText("TL-APP chưa login")
        self.detail_label.setText(data.get("note") or "Cần login TL-APP trong Chrome profile local trước khi scan.")
        self.log.appendPlainText(f"TL-APP login check: NOT_LOGGED_IN {data.get('error', '')}")
        if show_success:
            QMessageBox.warning(
                self,
                "TL-APP chưa login",
                "Chưa thấy session TL-APP. Tool dùng chung chrome profile local, bạn chỉ cần login một lần trong Chrome đó.",
            )
        return False

    def test_not_logged_in_gate(self):
        if TEST_PROFILE_DIR.exists():
            QMessageBox.information(
                self,
                "Profile test đã tồn tại",
                f"Profile test đã có sẵn:\n{TEST_PROFILE_DIR}\n\nNếu profile này từng login, hãy xóa thư mục đó trước khi test.",
            )
        gate = LoginGateDialog(self, TEST_PROFILE_DIR)
        gate.set_status("Đây là màn hình khi profile chưa login. Dùng để test/demo flow lần đầu.", ok=False)
        gate.exec()

    def _update_progress_from_text(self, text):
        for line in text.splitlines():
            if line.startswith("[") and "]" in line:
                self.processed_count += 1
                if self.total_hint > 0:
                    self.progress.setValue(min(99, int(self.processed_count * 100 / self.total_hint)))
                self.progress_label.setText(f"Đã xử lý {self.processed_count} link")
            if "CHUA_NAP:" in line or "DA_NAP:" in line:
                self.detail_label.setText(line)

    def _count_links(self, file_path, start, limit):
        try:
            links = [x.strip() for x in Path(file_path).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
            count = max(0, len(links) - start + 1)
            return count if limit == 0 else min(count, limit)
        except Exception:
            return 0

    def open_root(self):
        os.startfile(str(ROOT))

    def _apply_style(self):
        self.setStyleSheet(
            """
            * {
                font-family: "Segoe UI";
                font-size: 13px;
                color: #1f2937;
            }
            #root { background: #f4f7fb; }
            #sidebar {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #17212b, stop:1 #263241);
                border-right: 1px solid #dbe3ea;
            }
            #logo {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #18a999, stop:1 #ee735d);
                color: white;
                font-size: 20px;
                font-weight: 800;
                border-radius: 12px;
            }
            #brandName { color: #ffffff; font-size: 16px; font-weight: 700; }
            #brandDesc { color: #aebdcc; font-size: 12px; }
            #navButton {
                color: #d7e0e8;
                text-align: left;
                border: none;
                border-radius: 10px;
                background: transparent;
                padding: 0 12px;
                font-weight: 600;
            }
            #navButton:hover { background: rgba(255,255,255,.08); }
            #navButton:checked {
                background: #0f766e;
                color: #ffffff;
            }
            #sessionBox {
                background: rgba(255,255,255,.08);
                border: 1px solid rgba(255,255,255,.12);
                border-radius: 12px;
            }
            #sessionTitle { color: #ffffff; font-weight: 700; }
            #sessionText { color: #c9d3dd; line-height: 1.4; }
            #content { background: #f4f7fb; }
            #heroTitle { font-size: 25px; font-weight: 800; color: #18212f; }
            #heroSubtitle { color: #607080; }
            #pill {
                background: #ecfdf5;
                border: 1px solid #b8ead5;
                border-radius: 14px;
            }
            #pillText { color: #0f766e; font-weight: 700; }
            #statCard, #actionCard, #sideCard {
                background: #ffffff;
                border: 1px solid #dce4ed;
                border-radius: 16px;
            }
            #statTitle { color: #667789; font-size: 12px; font-weight: 700; }
            #statValue { color: #18212f; font-size: 25px; font-weight: 800; }
            #statSuffix { color: #728295; padding-top: 7px; }
            #cardTitle { font-size: 18px; font-weight: 800; color: #18212f; }
            #cardSubtitle { color: #667789; line-height: 1.45; }
            #fieldLabel { color: #516173; font-weight: 700; font-size: 12px; }
            QLineEdit, QSpinBox {
                background: #ffffff;
                border: 1px solid #cfd9e4;
                border-radius: 10px;
                padding: 0 10px;
                selection-background-color: #0f766e;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #0f766e;
            }
            QPushButton {
                border-radius: 10px;
                min-height: 38px;
                padding: 0 10px;
                font-weight: 800;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
            #primaryButton {
                background: #0f766e;
                color: white;
                border: 1px solid #0f766e;
            }
            #primaryButton:hover { background: #0d6a63; }
            #secondaryButton {
                background: #ffffff;
                color: #27364a;
                border: 1px solid #cfd9e4;
            }
            #secondaryButton:hover { background: #f4f7fb; }
            #dangerButton {
                background: #fff5f2;
                color: #b84d3c;
                border: 1px solid #f0c7bd;
            }
            #rightPanel {
                background: #eef3f8;
                border: 1px solid #dce4ed;
                border-radius: 18px;
            }
            #sideTitle { font-size: 14px; font-weight: 800; color: #18212f; }
            #statusBig { font-size: 20px; font-weight: 800; color: #0f766e; }
            #mutedText { color: #667789; line-height: 1.45; }
            #fileChip {
                background: #f4f7fb;
                border: 1px solid #dce4ed;
                border-radius: 9px;
                padding: 9px;
                color: #445365;
            }
            QProgressBar {
                height: 10px;
                border: none;
                border-radius: 5px;
                background: #dde6ef;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f766e, stop:1 #ee735d);
            }
            #logBox {
                background: #111a24;
                color: #d9f0f2;
                border: 1px solid #203040;
                border-radius: 16px;
                padding: 12px;
                font-family: Consolas;
                font-size: 12px;
            }
            #loginDialog {
                background: #f4f7fb;
            }
            #loginTitle {
                font-size: 22px;
                font-weight: 800;
                color: #18212f;
            }
            #loginDesc {
                color: #516173;
                line-height: 1.5;
            }
            #loginProfile {
                background: #ffffff;
                border: 1px solid #dce4ed;
                border-radius: 12px;
                padding: 12px;
                color: #445365;
                font-family: Consolas;
            }
            #loginStatus {
                background: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 10px;
                padding: 10px;
            }
            QMessageBox {
                background: #f8fafc;
            }
            QMessageBox QLabel {
                color: #18212f;
                font-size: 13px;
                line-height: 1.45;
            }
            QMessageBox QPushButton {
                background: #0f766e;
                color: #ffffff;
                border: 1px solid #0f766e;
                border-radius: 9px;
                min-width: 86px;
                min-height: 32px;
                padding: 0 14px;
                font-weight: 800;
            }
            QMessageBox QPushButton:hover {
                background: #0d6a63;
            }
            """
        )


def main():
    app = QApplication(sys.argv)
    window = GifteeQtTool()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
