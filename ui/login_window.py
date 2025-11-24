"""
Login window for adding email accounts
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QGroupBox, QFormLayout, QMessageBox,
                             QCheckBox, QProgressBar, QFrame, QWidget)
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
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Log in")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Provider selection (hidden by default, shown for custom IMAP/SMTP)
        provider_group = QGroupBox("Email Provider")
        provider_layout = QVBoxLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Gmail", "Outlook", "Yahoo Mail", "Custom IMAP/SMTP"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(QLabel("Provider:"))
        provider_layout.addWidget(self.provider_combo)
        provider_group.setLayout(provider_layout)
        provider_group.setVisible(False)
        layout.addWidget(provider_group)
        
        # OAuth button (for Gmail/Outlook)
        self.oauth_button = QPushButton()
        self.oauth_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                color: #3c4043;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #dadce0;
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
        separator_layout.setContentsMargins(0, 8, 0, 8)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("color: #dadce0;")
        separator_layout.addWidget(line1)
        
        or_label = QLabel("or")
        or_label.setStyleSheet("color: #5f6368; padding: 0 16px;")
        separator_layout.addWidget(or_label)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #dadce0;")
        separator_layout.addWidget(line2)
        
        self.separator_widget.setLayout(separator_layout)
        self.separator_widget.setVisible(False)
        layout.addWidget(self.separator_widget)
        
        # Email input
        email_group = QGroupBox("Account Information")
        email_layout = QFormLayout()
        email_layout.setSpacing(12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@company.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        email_layout.addRow("Email Address:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
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
        self.display_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
            }
        """)
        email_layout.addRow("Display Name:", self.display_name_input)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        # Server settings (for custom)
        self.server_group = QGroupBox("Server Settings")
        server_layout = QFormLayout()
        
        self.imap_server_input = QLineEdit()
        self.imap_server_input.setPlaceholderText("imap.example.com")
        server_layout.addRow("IMAP Server:", self.imap_server_input)
        
        self.imap_port_input = QLineEdit()
        self.imap_port_input.setText("993")
        server_layout.addRow("IMAP Port:", self.imap_port_input)
        
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.example.com")
        server_layout.addRow("SMTP Server:", self.smtp_server_input)
        
        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setText("587")
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
        
        self.login_button = QPushButton("Log In")
        self.login_button.setDefault(True)
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
        
        # Forgot password and sign up links
        links_layout = QHBoxLayout()
        links_layout.setContentsMargins(0, 0, 0, 0)
        
        forgot_password = QLabel("<a href='#' style='color: #1a73e8; text-decoration: none;'>Forgot password?</a>")
        forgot_password.setOpenExternalLinks(False)
        links_layout.addWidget(forgot_password)
        
        links_layout.addStretch()
        
        sign_up_label = QLabel("Don't have an account? <a href='#' style='color: #1a73e8; text-decoration: none;'>Sign Up</a>")
        sign_up_label.setOpenExternalLinks(False)
        links_layout.addWidget(sign_up_label)
        
        button_layout.addLayout(links_layout)
        
        cancel_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #5f6368;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        cancel_layout.addStretch()
        cancel_layout.addWidget(self.cancel_button)
        cancel_layout.addStretch()
        button_layout.addLayout(cancel_layout)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
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
            self.server_group.setVisible(True)
            self.oauth_button.setVisible(False)
            self.separator_widget.setVisible(False)
            self.password_help_label.setVisible(False)
        else:
            self.server_group.setVisible(False)
            
            # Set default servers
            if provider_text == "Gmail":
                self.imap_server_input.setText("imap.gmail.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.gmail.com")
                self.smtp_port_input.setText("587")
                # Show OAuth button and separator
                self.oauth_button.setText("Use Google Account")
                self.oauth_button.setVisible(True)
                self.separator_widget.setVisible(True)
                self.password_help_label.setVisible(True)
            elif provider_text == "Outlook":
                self.imap_server_input.setText("outlook.office365.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.office365.com")
                self.smtp_port_input.setText("587")
                self.oauth_button.setText("Use Microsoft Account")
                self.oauth_button.setVisible(True)
                self.separator_widget.setVisible(True)
                self.password_help_label.setVisible(False)
            elif provider_text == "Yahoo Mail":
                self.imap_server_input.setText("imap.mail.yahoo.com")
                self.imap_port_input.setText("993")
                self.smtp_server_input.setText("smtp.mail.yahoo.com")
                self.smtp_port_input.setText("587")
                self.oauth_button.setVisible(False)
                self.separator_widget.setVisible(False)
                self.password_help_label.setVisible(False)
    
    def on_login_clicked(self):
        """Handle login button click - password-based authentication"""
        email = self.email_input.text().strip()
        
        if not email or not validate_email(email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        
        provider = self.provider_combo.currentText().lower().replace(" ", "_")
        password = self.password_input.text()
        
        if not password:
            QMessageBox.warning(self, "Missing Password", "Please enter a password or use the OAuth button above.")
            return
        
        account_data = {
            'email': email,
            'display_name': self.display_name_input.text().strip() or email.split('@')[0],
            'provider': provider,
            'use_oauth': False,  # Password-based login
            'password': password,
            'imap_server': self.imap_server_input.text().strip(),
            'imap_port': int(self.imap_port_input.text() or "993"),
            'smtp_server': self.smtp_server_input.text().strip(),
            'smtp_port': int(self.smtp_port_input.text() or "587"),
            'use_tls': self.use_tls_checkbox.isChecked()
        }
        
        if provider == "custom_imap/smtp":
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

