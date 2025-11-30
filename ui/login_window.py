"""
Login window for adding email accounts
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QGroupBox, QFormLayout, QMessageBox,
                             QCheckBox, QProgressBar, QFrame, QWidget, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import config
from utils.helpers import validate_email


class LoginWindow(QDialog):
    """Login dialog for adding email accounts"""
    
    account_added = pyqtSignal(dict)  # Signal emitted when account is successfully added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Email Account")
        self.setFixedWidth(550)
        self.setFixedHeight(650)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components"""
        # Main layout for dialog
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #dadce0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #bdc1c6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Add Email Account")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Connect your email account to get started")
        subtitle.setStyleSheet("color: #5f6368; font-size: 14px; padding-bottom: 8px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Provider selection - always visible
        provider_group = QGroupBox("Select Email Provider")
        provider_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dadce0;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        provider_layout = QVBoxLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Gmail", "Outlook", "Yahoo Mail", "Custom IMAP/SMTP"])
        self.provider_combo.setFixedHeight(44)
        self.provider_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QComboBox:focus {
                border: 2px solid #1a73e8;
            }
            QComboBox:hover {
                border-color: #1a73e8;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #5f6368;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dadce0;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e8f0fe;
                selection-color: #202124;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                border-radius: 2px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f1f3f4;
            }
        """)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # OAuth button (for Gmail/Outlook)
        self.oauth_button = QPushButton()
        self.oauth_button.setFixedHeight(48)
        self.oauth_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #dadce0;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                color: #3c4043;
                text-align: center;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #1a73e8;
            }
            QPushButton:pressed {
                background-color: #f1f3f4;
            }
        """)
        self.oauth_button.clicked.connect(self.on_oauth_clicked)
        self.oauth_button.setVisible(False)
        layout.addWidget(self.oauth_button)
        
        # Separator with "or"
        self.separator_widget = QWidget()
        separator_layout = QHBoxLayout()
        separator_layout.setContentsMargins(0, 12, 0, 12)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("color: #dadce0; background-color: #dadce0; min-height: 1px;")
        separator_layout.addWidget(line1)
        
        or_label = QLabel("or")
        or_label.setStyleSheet("color: #5f6368; padding: 0 16px; font-size: 13px;")
        separator_layout.addWidget(or_label)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #dadce0; background-color: #dadce0; min-height: 1px;")
        separator_layout.addWidget(line2)
        
        self.separator_widget.setLayout(separator_layout)
        self.separator_widget.setVisible(False)
        layout.addWidget(self.separator_widget)
        
        # Email input group (only shown for Custom IMAP/SMTP)
        self.email_group = QGroupBox("Account Information")
        self.email_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dadce0;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        email_layout = QFormLayout()
        email_layout.setSpacing(12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@company.com")
        self.email_input.setFixedHeight(44)
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        email_layout.addRow("Email Address:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password or App Password")
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        password_label = QLabel("Password:")
        email_layout.addRow(password_label, self.password_input)
        
        # Help text for Gmail app password
        self.password_help_label = QLabel()
        self.password_help_label.setWordWrap(True)
        self.password_help_label.setStyleSheet("color: #5f6368; font-size: 12px; margin-top: 4px;")
        self.password_help_label.setText(
            "💡 For Gmail, use an App Password instead of your regular password.\n"
            "Generate one at: <a href='https://myaccount.google.com/apppasswords'>https://myaccount.google.com/apppasswords</a>"
        )
        self.password_help_label.setOpenExternalLinks(True)
        self.password_help_label.setVisible(False)
        email_layout.addRow("", self.password_help_label)
        
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Your Name (optional)")
        self.display_name_input.setFixedHeight(44)
        self.display_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        email_layout.addRow("Display Name:", self.display_name_input)
        
        self.email_group.setLayout(email_layout)
        self.email_group.setVisible(False)  # Hidden by default
        layout.addWidget(self.email_group)
        
        # Server settings (for custom)
        self.server_group = QGroupBox("Server Settings (Custom IMAP/SMTP)")
        self.server_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dadce0;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        server_layout = QFormLayout()
        server_layout.setSpacing(12)
        
        self.imap_server_input = QLineEdit()
        self.imap_server_input.setPlaceholderText("imap.example.com")
        self.imap_server_input.setFixedHeight(44)
        self.imap_server_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        server_layout.addRow("IMAP Server:", self.imap_server_input)
        
        self.imap_port_input = QLineEdit()
        self.imap_port_input.setText("993")
        self.imap_port_input.setFixedHeight(44)
        self.imap_port_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        server_layout.addRow("IMAP Port:", self.imap_port_input)
        
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.example.com")
        self.smtp_server_input.setFixedHeight(44)
        self.smtp_server_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        server_layout.addRow("SMTP Server:", self.smtp_server_input)
        
        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setText("587")
        self.smtp_port_input.setFixedHeight(44)
        self.smtp_port_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                color: #202124;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        server_layout.addRow("SMTP Port:", self.smtp_port_input)
        
        self.use_tls_checkbox = QCheckBox("Use TLS/SSL")
        self.use_tls_checkbox.setChecked(True)
        server_layout.addRow("", self.use_tls_checkbox)
        
        self.server_group.setLayout(server_layout)
        self.server_group.setVisible(False)  # Hidden by default
        layout.addWidget(self.server_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        self.login_button = QPushButton("Add Account")
        self.login_button.setDefault(True)
        self.login_button.setFixedHeight(48)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1765cc;
            }
            QPushButton:pressed {
                background-color: #1557b0;
            }
            QPushButton:disabled {
                background-color: #dadce0;
                color: #80868b;
            }
        """)
        self.login_button.clicked.connect(self.on_login_clicked)
        button_layout.addWidget(self.login_button)
        
        # Cancel button
        cancel_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #5f6368;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #dadce0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        cancel_layout.addStretch()
        cancel_layout.addWidget(self.cancel_button)
        cancel_layout.addStretch()
        button_layout.addLayout(cancel_layout)
        
        # Add buttons outside scroll area (always visible)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # Set layout on content widget
        content_widget.setLayout(layout)
        
        # Add content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Set main layout on dialog
        self.setLayout(main_layout)
        
        # Initialize based on default provider (Gmail)
        self.on_provider_changed("Gmail")
    
    def on_oauth_clicked(self):
        """Handle OAuth button click - start OAuth flow directly"""
        provider = self.provider_combo.currentText().lower()
        if provider not in ["gmail", "outlook"]:
            return
        
        # Emit account data with OAuth flag set
        account_data = {
            'email': '',  # Will be filled from OAuth
            'display_name': '',
            'provider': provider,
            'use_oauth': True,
            'password': '',
            'imap_server': '',
            'imap_port': 993,
            'smtp_server': '',
            'smtp_port': 587,
            'use_tls': True
        }
        
        self.account_added.emit(account_data)
    
    def on_provider_changed(self, provider_text: str):
        """Handle provider selection change"""
        if provider_text == "Custom IMAP/SMTP":
            # Show server settings and manual login for custom configuration
            self.server_group.setVisible(True)
            self.email_group.setVisible(True)
            self.oauth_button.setVisible(False)
            self.separator_widget.setVisible(False)
            self.password_help_label.setVisible(False)
            # Clear server inputs for custom entry
            self.imap_server_input.clear()
            self.imap_server_input.setPlaceholderText("imap.example.com")
            self.imap_port_input.setText("993")
            self.smtp_server_input.clear()
            self.smtp_server_input.setPlaceholderText("smtp.example.com")
            self.smtp_port_input.setText("587")
        else:
            # Hide server settings and manual login (use provider defaults and OAuth)
            self.server_group.setVisible(False)
            self.email_group.setVisible(False)  # Hide manual login
            
            # Set default servers based on provider (for internal use)
            if provider_text == "Gmail":
                self.imap_server_input.setText("imap.gmail.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.gmail.com")
                self.smtp_port_input.setText("587")
                # Show OAuth button only
                self.oauth_button.setText("🔐 Continue with Google")
                self.oauth_button.setVisible(True)
                self.separator_widget.setVisible(False)  # No separator needed
                self.password_help_label.setVisible(False)
            elif provider_text == "Outlook":
                self.imap_server_input.setText("outlook.office365.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.office365.com")
                self.smtp_port_input.setText("587")
                self.oauth_button.setText("🔐 Continue with Microsoft")
                self.oauth_button.setVisible(True)
                self.separator_widget.setVisible(False)
                self.password_help_label.setVisible(False)
            elif provider_text == "Yahoo Mail":
                self.imap_server_input.setText("imap.mail.yahoo.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.mail.yahoo.com")
                self.smtp_port_input.setText("587")
                # Yahoo doesn't support OAuth in this app currently
                # Show manual login interface for Yahoo
                self.server_group.setVisible(False)  # Hide server settings (using defaults)
                self.email_group.setVisible(True)  # Show manual login
                self.oauth_button.setVisible(False)
                self.separator_widget.setVisible(False)
                # Show help text for Yahoo app password
                self.password_help_label.setText(
                    "💡 For Yahoo Mail, use an App Password instead of your regular password.\n"
                    "Generate one at: <a href='https://login.yahoo.com/account/security/app-passwords'>https://login.yahoo.com/account/security/app-passwords</a>"
                )
                self.password_help_label.setVisible(True)
    
    def on_login_clicked(self):
        """Handle login button click - password-based authentication (for Custom IMAP/SMTP and Yahoo Mail)"""
        provider = self.provider_combo.currentText()
        
        # Allow manual login for Custom IMAP/SMTP and Yahoo Mail
        if provider not in ["Custom IMAP/SMTP", "Yahoo Mail"]:
            QMessageBox.warning(self, "Invalid Method", f"Please use the OAuth button to add a {provider} account.")
            return
        
        email = self.email_input.text().strip()
        if not email or not validate_email(email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Missing Password", "Please enter your password or app password.")
            return
        
        # Convert provider name to format expected by backend
        provider_name = provider.lower().replace(" ", "_")
        
        account_data = {
            'email': email,
            'display_name': self.display_name_input.text().strip() or email.split('@')[0],
            'provider': provider_name,
            'use_oauth': False,  # Password-based login
            'password': password,
            'imap_server': self.imap_server_input.text().strip(),
            'imap_port': int(self.imap_port_input.text() or "993"),
            'smtp_server': self.smtp_server_input.text().strip(),
            'smtp_port': int(self.smtp_port_input.text() or "587"),
            'use_tls': self.use_tls_checkbox.isChecked()
        }
        
        if provider_name == "custom_imap/smtp":
            if not account_data['imap_server'] or not account_data['smtp_server']:
                QMessageBox.warning(self, "Missing Information", "Please enter IMAP and SMTP server addresses.")
                return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.login_button.setEnabled(False)
        
        # Emit signal with account data (parent will handle authentication)
        self.account_added.emit(account_data)
    
    def reset_form(self):
        """Reset the form after successful login"""
        self.progress_bar.setVisible(False)
        self.login_button.setEnabled(True)
        self.email_input.clear()
        self.password_input.clear()
        self.display_name_input.clear()

