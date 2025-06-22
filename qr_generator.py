#!/usr/bin/env python3
"""
Enhanced Advanced QR Code Generator with GUI - FIXED VERSION
Fixes for color application, image mask loading, and config loading issues.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer,
    CircleModuleDrawer,
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)

# Import color masks including ImageColorMask
try:
    from qrcode.image.styles.colormasks import (
        SolidFillColorMask,
        SquareGradiantColorMask,
        RadialGradiantColorMask,
        HorizontalGradiantColorMask,
        VerticalGradiantColorMask,
        ImageColorMask,
    )

    COLOR_MASKS_AVAILABLE = True
    IMAGE_COLOR_MASK_AVAILABLE = True
except ImportError:
    try:
        from qrcode.image.styles.colormasks import (
            SolidFillColorMask,
            SquareGradiantColorMask,
            RadialGradiantColorMask,
            HorizontalGradiantColorMask,
            VerticalGradiantColorMask,
        )

        COLOR_MASKS_AVAILABLE = True
        IMAGE_COLOR_MASK_AVAILABLE = False
    except ImportError:
        COLOR_MASKS_AVAILABLE = False
        IMAGE_COLOR_MASK_AVAILABLE = False

try:
    from qrcode.image.styles.moduledrawers import (
        VerticalBarsDrawer,
        HorizontalBarsDrawer,
    )

    ADVANCED_DRAWERS = True
except ImportError:
    ADVANCED_DRAWERS = False

from PIL import Image, ImageTk, ImageDraw, ImageFilter
import json
import os
from datetime import datetime
import webbrowser
import subprocess
import platform
import tempfile
import io
import urllib.request
import urllib.parse

# Clipboard handling with better cross-platform support
try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Scanning support
try:
    import cv2
    import pyzbar

    SCANNING_AVAILABLE = True
except ImportError:
    SCANNING_AVAILABLE = False


class QRCodeGenerator:
    def __init__(self, root: tk.Tk):
        self.root: tk.Tk = root
        self.root.title("Enhanced QR Code Generator - FIXED")
        self.root.geometry("1200x900")
        self.root.configure(bg='#2b2b2b')

        # Initialize variables
        self.qr_image = None
        self.preview_image = None
        self.current_config = {}

        # Create the GUI
        self.create_widgets()
        self.load_default_config()

    def create_widgets(self):
        # Create main frames
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel for controls
        left_frame = ttk.LabelFrame(main_frame, text="QR Code Settings", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right panel for preview
        right_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.create_control_panel(left_frame)
        self.create_preview_panel(right_frame)

    def create_control_panel(self, parent):
        # Notebook for different sections
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Content tab
        content_frame = ttk.Frame(notebook)
        notebook.add(content_frame, text="Content")
        self.create_content_tab(content_frame)

        # Style tab
        style_frame = ttk.Frame(notebook)
        notebook.add(style_frame, text="Style & Colors")
        self.create_style_tab(style_frame)

        # Image overlay tab
        image_frame = ttk.Frame(notebook)
        notebook.add(image_frame, text="Image Overlay")
        self.create_image_tab(image_frame)

        # Advanced tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Export / Advanced")
        self.create_advanced_tab(advanced_frame)

    def create_content_tab(self, parent):
        # Preset selection
        ttk.Label(parent, text="Content Type:").pack(anchor=tk.W, pady=(0, 5))
        self.preset_var = tk.StringVar(value="general")
        preset_frame = ttk.Frame(parent)
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        presets = [
            ("General Text", "general"),
            ("URL/Website", "url"),
            ("WiFi Credentials", "wifi"),
            ("Business Card", "vcard"),
            ("Email", "email"),
            ("Phone Number", "phone"),
            ("SMS", "sms"),
        ]

        for text, value in presets:
            ttk.Radiobutton(
                preset_frame,
                text=text,
                variable=self.preset_var,
                value=value,
                command=self.on_preset_change,
            ).pack(anchor=tk.W)

        # Dynamic content area
        self.content_frame = ttk.LabelFrame(parent, text="Content Details", padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.create_general_content()

    def create_general_content(self):
        # Clear existing widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.preset_var.get() == "general":
            ttk.Label(self.content_frame, text="Text Content:").pack(anchor=tk.W)
            self.text_content = tk.Text(self.content_frame, height=5, wrap=tk.WORD)
            self.text_content.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
            self.text_content.bind('<KeyRelease>', self.on_content_change)

        elif self.preset_var.get() == "url":
            ttk.Label(self.content_frame, text="URL:").pack(anchor=tk.W)
            self.url_var = tk.StringVar()
            url_entry = ttk.Entry(self.content_frame, textvariable=self.url_var)
            url_entry.pack(fill=tk.X, pady=(5, 10))
            url_entry.bind('<Control-a>', self.select_all_text)
            self.url_var.trace('w', self.on_content_change)

        elif self.preset_var.get() == "wifi":
            self.create_wifi_form()

        elif self.preset_var.get() == "vcard":
            self.create_vcard_form()

        elif self.preset_var.get() == "email":
            self.create_email_form()

        elif self.preset_var.get() == "phone":
            ttk.Label(self.content_frame, text="Phone Number:").pack(anchor=tk.W)
            self.phone_var = tk.StringVar()
            phone_entry = ttk.Entry(self.content_frame, textvariable=self.phone_var)
            phone_entry.pack(fill=tk.X, pady=(5, 10))
            phone_entry.bind('<Control-a>', self.select_all_text)
            self.phone_var.trace('w', self.on_content_change)

        elif self.preset_var.get() == "sms":
            self.create_sms_form()

    def create_wifi_form(self):
        ttk.Label(self.content_frame, text="Network Name (SSID):").pack(anchor=tk.W)
        self.wifi_ssid = tk.StringVar()
        ssid_entry = ttk.Entry(self.content_frame, textvariable=self.wifi_ssid)
        ssid_entry.pack(fill=tk.X, pady=(5, 10))
        ssid_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Password:").pack(anchor=tk.W)
        self.wifi_password = tk.StringVar()
        pwd_entry = ttk.Entry(
            self.content_frame, textvariable=self.wifi_password, show="*"
        )
        pwd_entry.pack(fill=tk.X, pady=(5, 10))
        pwd_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Security Type:").pack(anchor=tk.W)
        self.wifi_security = tk.StringVar(value="WPA")
        security_frame = ttk.Frame(self.content_frame)
        security_frame.pack(fill=tk.X, pady=(5, 10))
        ttk.Radiobutton(
            security_frame, text="WPA/WPA2", variable=self.wifi_security, value="WPA"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            security_frame, text="WEP", variable=self.wifi_security, value="WEP"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            security_frame, text="None", variable=self.wifi_security, value=""
        ).pack(side=tk.LEFT)

        self.wifi_hidden = tk.BooleanVar()
        ttk.Checkbutton(
            self.content_frame, text="Hidden Network", variable=self.wifi_hidden
        ).pack(anchor=tk.W)

        # Bind events
        self.wifi_ssid.trace('w', self.on_content_change)
        self.wifi_password.trace('w', self.on_content_change)
        self.wifi_security.trace('w', self.on_content_change)

    def create_vcard_form(self):
        # Basic info
        ttk.Label(self.content_frame, text="Full Name:").pack(anchor=tk.W)
        self.vcard_name = tk.StringVar()
        name_entry = ttk.Entry(self.content_frame, textvariable=self.vcard_name)
        name_entry.pack(fill=tk.X, pady=(5, 5))
        name_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Organization:").pack(anchor=tk.W)
        self.vcard_org = tk.StringVar()
        org_entry = ttk.Entry(self.content_frame, textvariable=self.vcard_org)
        org_entry.pack(fill=tk.X, pady=(5, 5))
        org_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Phone:").pack(anchor=tk.W)
        self.vcard_phone = tk.StringVar()
        phone_entry = ttk.Entry(self.content_frame, textvariable=self.vcard_phone)
        phone_entry.pack(fill=tk.X, pady=(5, 5))
        phone_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Email:").pack(anchor=tk.W)
        self.vcard_email = tk.StringVar()
        email_entry = ttk.Entry(self.content_frame, textvariable=self.vcard_email)
        email_entry.pack(fill=tk.X, pady=(5, 5))
        email_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Website:").pack(anchor=tk.W)
        self.vcard_url = tk.StringVar()
        url_entry = ttk.Entry(self.content_frame, textvariable=self.vcard_url)
        url_entry.pack(fill=tk.X, pady=(5, 10))
        url_entry.bind('<Control-a>', self.select_all_text)

        # Bind events
        for var in [
            self.vcard_name,
            self.vcard_org,
            self.vcard_phone,
            self.vcard_email,
            self.vcard_url,
        ]:
            var.trace('w', self.on_content_change)

    def create_email_form(self):
        ttk.Label(self.content_frame, text="Email Address:").pack(anchor=tk.W)
        self.email_to = tk.StringVar()
        to_entry = ttk.Entry(self.content_frame, textvariable=self.email_to)
        to_entry.pack(fill=tk.X, pady=(5, 5))
        to_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Subject:").pack(anchor=tk.W)
        self.email_subject = tk.StringVar()
        subj_entry = ttk.Entry(self.content_frame, textvariable=self.email_subject)
        subj_entry.pack(fill=tk.X, pady=(5, 5))
        subj_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Message:").pack(anchor=tk.W)
        self.email_body = tk.Text(self.content_frame, height=4)
        self.email_body.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        self.email_to.trace('w', self.on_content_change)
        self.email_subject.trace('w', self.on_content_change)
        self.email_body.bind('<KeyRelease>', self.on_content_change)

    def create_sms_form(self):
        ttk.Label(self.content_frame, text="Phone Number:").pack(anchor=tk.W)
        self.sms_number = tk.StringVar()
        number_entry = ttk.Entry(self.content_frame, textvariable=self.sms_number)
        number_entry.pack(fill=tk.X, pady=(5, 5))
        number_entry.bind('<Control-a>', self.select_all_text)

        ttk.Label(self.content_frame, text="Message:").pack(anchor=tk.W)
        self.sms_message = tk.Text(self.content_frame, height=4)
        self.sms_message.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        self.sms_number.trace('w', self.on_content_change)
        self.sms_message.bind('<KeyRelease>', self.on_content_change)

    def create_style_tab(self, parent):
        # Theme selection
        ttk.Label(parent, text="Module Style:").pack(anchor=tk.W, pady=(0, 5))
        self.theme_var = tk.StringVar(value="Classic Squares")

        theme_frame = ttk.Frame(parent)
        theme_frame.pack(fill=tk.X, pady=(0, 10))

        # Use combobox for themes
        themes = [
            ("Classic Squares", "classic"),
            ("Rounded Corners", "rounded"),
            ("Circles", "circular"),
            ("Gapped Squares", "gapped"),
            ("Vertical Bars", "vertical_bars"),
            ("Horizontal Bars", "horizontal_bars"),
        ]

        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=[theme[0] for theme in themes],
            state="readonly",
        )
        theme_combo.pack(fill=tk.X)
        theme_combo.bind('<<ComboboxSelected>>', self.on_style_change)

        # Map display names to values
        self.theme_map = {theme[0]: theme[1] for theme in themes}
        self.theme_reverse_map = {theme[1]: theme[0] for theme in themes}

        # Color Mask selection (if available)
        if COLOR_MASKS_AVAILABLE:
            ttk.Label(parent, text="Color Effect:").pack(anchor=tk.W, pady=(10, 5))
            self.color_mask_var = tk.StringVar(value="Solid Fill")

            color_mask_frame = ttk.Frame(parent)
            color_mask_frame.pack(fill=tk.X, pady=(0, 10))

            # Updated color masks including ImageColorMask
            color_masks = [
                ("Solid Fill", "solid"),
                ("Radial Gradient", "radial"),
                ("Square Gradient", "square"),
                ("Horizontal Gradient", "horizontal"),
                ("Vertical Gradient", "vertical"),
            ]

            # Add ImageColorMask option if available
            if IMAGE_COLOR_MASK_AVAILABLE:
                color_masks.append(("Image Color Mask", "image"))

            color_mask_combo = ttk.Combobox(
                color_mask_frame,
                textvariable=self.color_mask_var,
                values=[mask[0] for mask in color_masks],
                state="readonly",
            )
            color_mask_combo.pack(fill=tk.X)
            color_mask_combo.bind('<<ComboboxSelected>>', self.on_style_change)

            self.color_mask_map = {mask[0]: mask[1] for mask in color_masks}
            self.color_mask_reverse_map = {mask[1]: mask[0] for mask in color_masks}

            # Image Color Mask settings (only show if ImageColorMask is selected)
            self.image_mask_frame = ttk.LabelFrame(
                parent, text="Image Color Mask Settings", padding=10
            )

            ttk.Label(self.image_mask_frame, text="Mask Image Path:").pack(anchor=tk.W)
            self.mask_image_path_var = tk.StringVar()
            mask_path_frame = ttk.Frame(self.image_mask_frame)
            mask_path_frame.pack(fill=tk.X, pady=(5, 0))

            mask_path_entry = ttk.Entry(
                mask_path_frame, textvariable=self.mask_image_path_var
            )
            mask_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            mask_path_entry.bind('<Control-a>', self.select_all_text)

            ttk.Button(
                mask_path_frame, text="Browse", command=self.browse_mask_image
            ).pack(side=tk.RIGHT, padx=(5, 0))

            self.mask_image_path_var.trace('w', self.on_style_change)

        else:
            self.color_mask_var = tk.StringVar(value="solid")

        # Color settings
        color_frame = ttk.LabelFrame(parent, text="Colors", padding=10)
        color_frame.pack(fill=tk.X, pady=(10, 0))

        # Foreground color
        fg_frame = ttk.Frame(color_frame)
        fg_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(fg_frame, text="Foreground:").pack(side=tk.LEFT)
        self.fg_color = tk.StringVar(value="#000000")

        fg_color_frame = ttk.Frame(fg_frame)
        fg_color_frame.pack(side=tk.RIGHT)

        self.fg_color_btn = tk.Button(
            fg_color_frame,
            width=3,
            bg=self.fg_color.get(),
            command=lambda: self.choose_color(self.fg_color, self.fg_color_btn),
        )
        self.fg_color_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # fg_entry = ttk.Entry(fg_color_frame, textvariable=self.fg_color, width=8)
        self.fg_entry = ttk.Entry(fg_color_frame, textvariable=self.fg_color, width=8)
        self.fg_entry.pack(side=tk.RIGHT)
        self.fg_entry.bind('<KeyRelease>', self.on_color_change)
        self.fg_entry.bind('<Control-a>', self.select_all_text)

        # Background color
        bg_frame = ttk.Frame(color_frame)
        bg_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(bg_frame, text="Background:").pack(side=tk.LEFT)
        self.bg_color = tk.StringVar(value="#FFFFFF")

        bg_color_frame = ttk.Frame(bg_frame)
        bg_color_frame.pack(side=tk.RIGHT)

        self.bg_color_btn = tk.Button(
            bg_color_frame,
            width=3,
            bg=self.bg_color.get(),
            command=lambda: self.choose_color(self.bg_color, self.bg_color_btn),
        )
        self.bg_color_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.bg_entry = ttk.Entry(bg_color_frame, textvariable=self.bg_color, width=8)
        self.bg_entry.pack(side=tk.RIGHT)
        self.bg_entry.bind('<KeyRelease>', self.on_color_change)
        self.bg_entry.bind('<Control-a>', self.select_all_text)

        self.color_info_label = ttk.Label(
            color_frame, text="", foreground='gray', font=('Arial', 8)
        )
        self.color_info_label.pack(anchor=tk.W, pady=(5, 0))

        # Size settings
        size_frame = ttk.LabelFrame(parent, text="Size Settings", padding=10)
        size_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(size_frame, text="QR Code Size:").pack(anchor=tk.W)
        self.size_var = tk.IntVar(value=800)

        # Create frame for size control
        size_control_frame = ttk.Frame(size_frame)
        size_control_frame.pack(fill=tk.X, pady=(5, 5))

        # Size scale
        size_scale = ttk.Scale(
            size_control_frame,
            from_=100,
            to=1000,
            variable=self.size_var,
            orient=tk.HORIZONTAL,
            command=self.on_style_change,
        )
        size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Size entry for precise input
        size_entry = ttk.Entry(size_control_frame, textvariable=self.size_var, width=6)
        size_entry.pack(side=tk.RIGHT)
        size_entry.bind('<KeyRelease>', self.on_style_change)
        size_entry.bind('<Control-a>', self.select_all_text)

        self.size_label = ttk.Label(size_frame, text="800 px")
        self.size_label.pack(anchor=tk.W)

        # Border size
        ttk.Label(size_frame, text="Border Size:").pack(anchor=tk.W, pady=(10, 0))
        self.border_var = tk.IntVar(value=1)
        border_scale = ttk.Scale(
            size_frame,
            from_=0,
            to=20,
            variable=self.border_var,
            orient=tk.HORIZONTAL,
            command=self.on_style_change,
        )
        border_scale.pack(fill=tk.X, pady=(5, 5))
        self.border_label = ttk.Label(size_frame, text="1 modules")
        self.border_label.pack(anchor=tk.W)

        # Error correction
        ttk.Label(size_frame, text="Error Correction:").pack(anchor=tk.W, pady=(10, 0))
        self.error_correction_var = tk.StringVar(value="Q")
        error_frame = ttk.Frame(size_frame)
        error_frame.pack(fill=tk.X, pady=(5, 0))

        for text, value in [
            ("Low (L)", "L"),
            ("Medium (M)", "M"),
            ("Quartile (Q)", "Q"),
            ("High (H)", "H"),
        ]:
            ttk.Radiobutton(
                error_frame,
                text=text,
                variable=self.error_correction_var,
                value=value,
                command=self.on_style_change,
            ).pack(anchor=tk.W)

        # Initially hide image mask frame
        self.toggle_image_mask_frame()

    def create_image_tab(self, parent):
        # Enable image overlay
        self.use_image_var = tk.BooleanVar()
        ttk.Checkbutton(
            parent,
            text="Add center image overlay",
            variable=self.use_image_var,
            command=self.toggle_image_options,
        ).pack(anchor=tk.W, pady=(0, 10))

        # Image options frame
        self.image_options_frame = ttk.LabelFrame(
            parent, text="Image Settings", padding=10
        )
        self.image_options_frame.pack(fill=tk.X, pady=(0, 10))

        # Image path
        path_frame = ttk.Frame(self.image_options_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(path_frame, text="Image Path or URL:").pack(anchor=tk.W)
        self.image_path_var = tk.StringVar()
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))

        path_entry = ttk.Entry(path_entry_frame, textvariable=self.image_path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        path_entry.bind('<Control-a>', self.select_all_text)

        ttk.Button(path_entry_frame, text="Browse", command=self.browse_image).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # Image size
        ttk.Label(self.image_options_frame, text="Image Size (% of QR):").pack(
            anchor=tk.W
        )
        self.image_size_var = tk.IntVar(value=20)
        size_scale = ttk.Scale(
            self.image_options_frame,
            from_=5,
            to=50,
            variable=self.image_size_var,
            orient=tk.HORIZONTAL,
            command=self.on_image_change,
        )
        size_scale.pack(fill=tk.X, pady=(5, 5))
        self.image_size_label = ttk.Label(self.image_options_frame, text="20%")
        self.image_size_label.pack(anchor=tk.W)

        # Background settings
        bg_frame = ttk.LabelFrame(
            self.image_options_frame, text="Image Background", padding=5
        )
        bg_frame.pack(fill=tk.X, pady=(10, 0))

        self.image_bg_var = tk.StringVar(value="match")
        ttk.Radiobutton(
            bg_frame,
            text="Match QR background color",
            variable=self.image_bg_var,
            value="match",
            command=self.on_image_change,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            bg_frame,
            text="Custom color",
            variable=self.image_bg_var,
            value="custom",
            command=self.on_image_change,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            bg_frame,
            text="No background (transparent)",
            variable=self.image_bg_var,
            value="none",
            command=self.on_image_change,
        ).pack(anchor=tk.W)

        # Custom background color
        custom_bg_frame = ttk.Frame(bg_frame)
        custom_bg_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(custom_bg_frame, text="Custom background:").pack(side=tk.LEFT)
        self.image_bg_color = tk.StringVar(value="#FFFFFF")

        self.image_bg_color_btn = tk.Button(
            custom_bg_frame,
            width=3,
            bg=self.image_bg_color.get(),
            command=lambda: self.choose_color(
                self.image_bg_color, self.image_bg_color_btn
            ),
        )
        self.image_bg_color_btn.pack(side=tk.RIGHT, padx=(5, 0))

        img_bg_entry = ttk.Entry(
            custom_bg_frame, textvariable=self.image_bg_color, width=8
        )
        img_bg_entry.pack(side=tk.RIGHT)
        img_bg_entry.bind('<KeyRelease>', self.on_image_change)
        img_bg_entry.bind('<Control-a>', self.select_all_text)

        # Padding
        ttk.Label(bg_frame, text="Background Padding:").pack(anchor=tk.W, pady=(10, 0))
        self.image_padding_var = tk.IntVar(value=0)
        padding_scale = ttk.Scale(
            bg_frame,
            from_=0,
            to=30,
            variable=self.image_padding_var,
            orient=tk.HORIZONTAL,
            command=self.on_image_change,
        )
        padding_scale.pack(fill=tk.X, pady=(5, 5))
        self.image_padding_label = ttk.Label(bg_frame, text="0 px")
        self.image_padding_label.pack(anchor=tk.W)

        # Initially disable image options
        self.toggle_image_options()

        # Bind events
        self.image_path_var.trace('w', self.on_image_change)

    def create_advanced_tab(self, parent):
        # File operations
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Save Config", command=self.save_config).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Load Config", command=self.load_config).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Export QR", command=self.export_qr).pack(
            side=tk.LEFT
        )

        # Quick actions
        action_frame = ttk.LabelFrame(parent, text="Quick Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        action_btn_frame = ttk.Frame(action_frame)
        action_btn_frame.pack(fill=tk.X)

        # First row of buttons
        action_row1 = ttk.Frame(action_btn_frame)
        action_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            action_row1, text="Copy Image", command=self.copy_image_to_clipboard
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            action_row1, text="Copy Text", command=self.copy_text_to_clipboard
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_row1, text="Share QR", command=self.share_qr).pack(
            side=tk.LEFT
        )

        # Second row of buttons
        action_row2 = ttk.Frame(action_btn_frame)
        action_row2.pack(fill=tk.X)

        if SCANNING_AVAILABLE:
            ttk.Button(action_row2, text="Scan QR", command=self.scan_qr_file).pack(
                side=tk.LEFT
            )
        else:
            ttk.Button(
                action_row2,
                text="Install Scanning",
                command=self.show_scanning_install_help,
            ).pack(side=tk.LEFT)

    def create_preview_panel(self, parent):
        # Preview canvas
        self.canvas = tk.Canvas(parent, width=450, height=450, bg='white')
        self.canvas.pack(pady=(0, 10))

        # Generate button
        ttk.Button(parent, text="Generate QR Code", command=self.generate_qr).pack(
            pady=(0, 10)
        )

        # Status label
        self.status_label = ttk.Label(parent, text="Ready to generate QR code")
        self.status_label.pack()

    def select_all_text(self, event):
        """Select all text in entry widget"""
        event.widget.select_range(0, tk.END)
        return 'break'

    def on_preset_change(self):
        self.create_general_content()
        self.generate_qr()

    def on_content_change(self, *args):
        self.generate_qr()

    def on_style_change(self, *args):
        # Update labels
        try:
            self.size_label.config(text=f"{int(self.size_var.get())} px")
            self.border_label.config(text=f"{int(self.border_var.get())} modules")
        except:
            pass  # Ignore if widgets don't exist yet

        self.toggle_image_mask_frame()
        self.toggle_color_inputs()
        self.generate_qr()

    def on_color_change(self, *args):
        """Handle manual hex color input - FIXED VERSION"""
        try:
            # Validate and update color buttons
            fg_color = self.fg_color.get()
            if len(fg_color) == 7 and fg_color.startswith('#'):
                try:
                    # Validate hex color by trying to use it
                    self.root.winfo_rgb(fg_color)
                    self.fg_color_btn.config(bg=fg_color)
                except tk.TclError:
                    pass  # Invalid color, ignore

            bg_color = self.bg_color.get()
            if len(bg_color) == 7 and bg_color.startswith('#'):
                try:
                    # Validate hex color by trying to use it
                    self.root.winfo_rgb(bg_color)
                    self.bg_color_btn.config(bg=bg_color)
                except tk.TclError:
                    pass  # Invalid color, ignore

            # Force regeneration after color change
            self.root.after_idle(self.generate_qr)

        except Exception as e:
            print(f"Color change error: {e}")
            pass  # Don't let color errors break the app

    def on_image_change(self, *args):
        try:
            self.image_size_label.config(text=f"{int(self.image_size_var.get())}%")
            self.image_padding_label.config(
                text=f"{int(self.image_padding_var.get())} px"
            )
        except:
            pass
        self.generate_qr()

    def toggle_image_options(self):
        state = 'normal' if self.use_image_var.get() else 'disabled'
        for child in self.image_options_frame.winfo_children():
            self._toggle_widget_state(child, state)
        self.generate_qr()

    def toggle_image_mask_frame(self):
        """Show/hide image mask settings based on color mask selection"""
        if hasattr(self, 'image_mask_frame') and hasattr(self, 'color_mask_var'):
            try:
                if self.color_mask_map.get(self.color_mask_var.get()) == "image":
                    self.image_mask_frame.pack(fill=tk.X, pady=(10, 0))
                else:
                    self.image_mask_frame.pack_forget()
            except:
                pass  # Ignore if widgets don't exist yet

    def toggle_color_inputs(self):
        """Enable/disable color inputs when ImageColorMask is selected"""
        if hasattr(self, 'color_mask_var'):
            try:
                # Check if ImageColorMask is selected
                is_image_mask = (
                    self.color_mask_map.get(self.color_mask_var.get()) == "image"
                )

                # Set widget states
                state = 'disabled' if is_image_mask else 'normal'
                bg_state = 'normal'

                # Toggle entry widgets
                if hasattr(self, 'fg_entry'):
                    self.fg_entry.config(state=state)
                if hasattr(self, 'bg_entry'):
                    self.bg_entry.config(state=bg_state)

                # Toggle color picker buttons
                if hasattr(self, 'fg_color_btn'):
                    self.fg_color_btn.config(state=state)
                if hasattr(self, 'bg_color_btn'):
                    self.bg_color_btn.config(state=bg_state)

                # Visual feedback and explanation
                if is_image_mask:
                    # Gray out disabled buttons
                    if hasattr(self, 'fg_color_btn'):
                        self.fg_color_btn.config(bg='#d0d0d0', relief='flat')
                    # if hasattr(self, 'bg_color_btn'):
                    #     self.bg_color_btn.config(bg='#d0d0d0', relief='flat')

                    # Show explanation
                    if hasattr(self, 'color_info_label'):
                        self.color_info_label.config(
                            text="Colors taken from mask image", foreground="red"
                        )
                else:
                    # Restore normal button colors
                    if hasattr(self, 'fg_color_btn'):
                        self.fg_color_btn.config(
                            bg=self.fg_color.get(), relief='raised'
                        )
                    if hasattr(self, 'bg_color_btn'):
                        self.bg_color_btn.config(
                            bg=self.bg_color.get(), relief='raised'
                        )

                    # Hide explanation
                    if hasattr(self, 'color_info_label'):
                        self.color_info_label.config(text="")

            except Exception as e:
                print(f"Warning: Error toggling color inputs: {e}")
                pass  # Don't break the app

    def _toggle_widget_state(self, widget, state):
        """Recursively toggle widget state"""
        if isinstance(widget, (ttk.Frame, ttk.LabelFrame)):
            for child in widget.winfo_children():
                self._toggle_widget_state(child, state)
        elif hasattr(widget, 'config'):
            try:
                if isinstance(
                    widget, (ttk.Entry, ttk.Button, ttk.Scale, ttk.Radiobutton)
                ):
                    widget.config(state=state)
                elif isinstance(widget, tk.Button):
                    widget.config(state=state)
            except tk.TclError:
                pass

    def choose_color(self, color_var, button):
        color = colorchooser.askcolor(color=color_var.get())[1]
        if color:
            color_var.set(color)
            button.config(bg=color)
            self.generate_qr()

    def browse_image(self):
        filename = filedialog.askopenfilename(
            title="Select Image",
            initialdir="./config",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")],
        )
        if filename:
            self.image_path_var.set(filename)

    def browse_mask_image(self):
        """Browse for image color mask"""
        filename = filedialog.askopenfilename(
            title="Select Mask Image",
            initialdir="./config",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")],
        )
        if filename:
            self.mask_image_path_var.set(filename)

    def get_content_string(self):
        preset = self.preset_var.get()

        if preset == "general":
            return self.text_content.get(1.0, tk.END).strip()

        elif preset == "url":
            url = self.url_var.get().strip()
            if url:
                # Add protocol if missing
                if not url.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
                    url = 'https://' + url
            return url

        elif preset == "wifi":
            ssid = self.wifi_ssid.get().strip()
            password = self.wifi_password.get().strip()
            security = self.wifi_security.get()
            hidden = "true" if self.wifi_hidden.get() else "false"

            if ssid:
                return f"WIFI:T:{security};S:{ssid};P:{password};H:{hidden};"
            return ""

        elif preset == "vcard":
            name = self.vcard_name.get().strip()
            org = self.vcard_org.get().strip()
            phone = self.vcard_phone.get().strip()
            email = self.vcard_email.get().strip()
            url = self.vcard_url.get().strip()

            if name:
                vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\n"
                if org:
                    vcard += f"ORG:{org}\n"
                if phone:
                    vcard += f"TEL:{phone}\n"
                if email:
                    vcard += f"EMAIL:{email}\n"
                if url:
                    vcard += f"URL:{url}\n"
                vcard += "END:VCARD"
                return vcard
            return ""

        elif preset == "email":
            to = self.email_to.get().strip()
            subject = self.email_subject.get().strip()
            body = self.email_body.get(1.0, tk.END).strip()

            if to:
                email_str = f"mailto:{to}"
                params = []
                if subject:
                    params.append(f"subject={urllib.parse.quote(subject)}")
                if body:
                    params.append(f"body={urllib.parse.quote(body)}")
                if params:
                    email_str += "?" + "&".join(params)
                return email_str
            return ""

        elif preset == "phone":
            phone = self.phone_var.get().strip()
            return f"tel:{phone}" if phone else ""

        elif preset == "sms":
            number = self.sms_number.get().strip()
            message = self.sms_message.get(1.0, tk.END).strip()

            if number:
                sms_str = f"sms:{number}"
                if message:
                    sms_str += f"?body={urllib.parse.quote(message)}"
                return sms_str
            return ""

        return ""

    def load_image_from_path_or_url(self, path_or_url):
        """Load image from local path or URL - FIXED VERSION"""
        if not path_or_url or path_or_url.strip() == "":
            raise Exception("Empty image path provided")

        try:
            path_or_url = path_or_url.strip()
            # print(f"{path_or_url = }")
            if path_or_url.startswith(('http://', 'https://')):
                # print("URL")
                # Load from URL
                with urllib.request.urlopen(path_or_url) as response:
                    image_data = response.read()
                    return Image.open(io.BytesIO(image_data))
            else:
                # print("PATH")
                # Load from local path
                if not os.path.exists(path_or_url):
                    raise Exception(f"File not found: {path_or_url}")

                return Image.open(path_or_url)

        except Exception as e:
            raise Exception(f"Could not load image: {str(e)}")

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def mix_colors(
        self,
        color1: tuple[int, int, int],
        color2: tuple[int, int, int],
        weight: float = 0.5,
    ) -> tuple[int, int, int]:
        """Zwraca kolor będący mieszanką dwóch kolorów.
        weight=0.0 => color1, weight=1.0 => color2"""
        return tuple(
            int(c1 * (1 - weight) + c2 * weight) for c1, c2 in zip(color1, color2)
        )

    def get_color_mask(self):
        """Get color mask based on selection - FIXED VERSION"""
        if not COLOR_MASKS_AVAILABLE:
            return None

        mask_type = self.color_mask_map.get(self.color_mask_var.get(), "solid")

        fg_color = self.fg_color.get()
        bg_color = self.bg_color.get()

        # print(f"before: {fg_color = }")
        # print(f"before: {bg_color = }")

        fg_color = self.hex_to_rgb(fg_color)
        bg_color = self.hex_to_rgb(bg_color)

        middle_color = self.mix_colors(fg_color, bg_color)

        # print(f"after: {fg_color = }")
        # print(f"after: {bg_color = }")

        if mask_type == "solid":
            return SolidFillColorMask(front_color=fg_color, back_color=bg_color)
        elif mask_type == "radial":
            return RadialGradiantColorMask(
                back_color=bg_color, center_color=middle_color, edge_color=fg_color
            )
        elif mask_type == "square":
            return SquareGradiantColorMask(
                back_color=bg_color, center_color=middle_color, edge_color=fg_color
            )
        elif mask_type == "horizontal":
            return HorizontalGradiantColorMask(
                back_color=bg_color, left_color=middle_color, right_color=fg_color
            )
        elif mask_type == "vertical":
            return VerticalGradiantColorMask(
                back_color=bg_color, top_color=middle_color, bottom_color=fg_color
            )
        elif mask_type == "image" and IMAGE_COLOR_MASK_AVAILABLE:
            # ImageColorMask requires a background image - FIXED VERSION
            try:
                if hasattr(self, 'mask_image_path_var'):
                    mask_path = self.mask_image_path_var.get().strip()
                    if mask_path:
                        # return ImageColorMask(
                        #     back_color=bg_color,
                        #     color_mask_path=mask_path
                        # )
                        mask_image = self.load_image_from_path_or_url(mask_path)
                        return ImageColorMask(
                            back_color=bg_color, color_mask_image=mask_image
                        )

                # No mask image provided, fallback to solid
                # print("No mask image path provided, using solid fill")
                return SolidFillColorMask()

            except Exception as e:
                print(f"Error loading mask image: {e}")
                return SolidFillColorMask()

        return None

    def generate_qr(self):
        """Generate QR code - FIXED VERSION with better color handling"""
        # Don't generate if UI isn't fully initialized yet
        if not hasattr(self, 'canvas') or not hasattr(self, 'status_label'):
            return

        try:
            content = self.get_content_string()
            if not content:
                self.canvas.delete("all")
                self.status_label.config(text="No content to generate QR code")
                return

            # Error correction mapping
            error_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }

            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_levels[self.error_correction_var.get()],
                box_size=10,
                border=self.border_var.get(),
            )

            qr.add_data(content)
            qr.make(fit=True)

            # Get colors - FIXED: Ensure valid hex colors
            fg_color = self.fg_color.get()
            bg_color = self.bg_color.get()

            # Validate colors
            if not fg_color.startswith('#') or len(fg_color) != 7:
                fg_color = "#000000"
                self.fg_color.set(fg_color)
            if not bg_color.startswith('#') or len(bg_color) != 7:
                bg_color = "#FFFFFF"
                self.bg_color.set(bg_color)

            # Apply theme/style
            theme = self.theme_map.get(self.theme_var.get(), "classic")

            # Get color mask
            color_mask = self.get_color_mask()

            # Generate QR image based on theme
            if theme == "classic":
                if color_mask:
                    qr_img = qr.make_image(
                        image_factory=StyledPilImage,
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color,
                    )
                else:
                    qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            elif theme == "rounded":
                qr_img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=RoundedModuleDrawer(),
                    color_mask=color_mask,
                    fill_color=fg_color,
                    back_color=bg_color,
                )
            elif theme == "circular":
                qr_img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=CircleModuleDrawer(),
                    color_mask=color_mask,
                    fill_color=fg_color,
                    back_color=bg_color,
                )
            elif theme == "gapped":
                # Create gapped squares using SquareModuleDrawer with size ratio
                try:
                    # from decimal import Decimal

                    qr_img = qr.make_image(
                        image_factory=StyledPilImage,
                        # module_drawer=GappedSquareModuleDrawer(size_ratio=Decimal(0.8)),
                        module_drawer=GappedSquareModuleDrawer(),
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color,
                    )
                except:
                    qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            elif theme == "vertical_bars" and ADVANCED_DRAWERS:
                try:
                    qr_img = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=VerticalBarsDrawer(),
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color,
                    )
                except:
                    qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            elif theme == "horizontal_bars" and ADVANCED_DRAWERS:
                try:
                    qr_img = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=HorizontalBarsDrawer(),
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color,
                    )
                except:
                    qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            else:
                qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)

            # Resize to desired size
            target_size = self.size_var.get()
            qr_img = qr_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

            # Add image overlay if enabled
            if self.use_image_var.get() and self.image_path_var.get():
                qr_img = self.add_image_overlay(qr_img)

            self.qr_image = qr_img

            # Update preview
            self.update_preview()
            self.status_label.config(text="QR code generated successfully")

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            print(f"QR Generation Error: {str(e)}")

    def add_image_overlay(self, qr_img):
        try:
            # Load overlay image
            overlay = self.load_image_from_path_or_url(self.image_path_var.get())

            # Calculate overlay size
            qr_size = qr_img.size[0]
            overlay_size = int(qr_size * self.image_size_var.get() / 100)

            # Resize overlay maintaining aspect ratio
            overlay.thumbnail((overlay_size, overlay_size), Image.Resampling.LANCZOS)

            # Create background if needed
            bg_type = self.image_bg_var.get()
            if bg_type in ["match", "custom"]:
                padding = self.image_padding_var.get()
                bg_size = overlay.size[0] + 2 * padding

                if bg_type == "match":
                    bg_color = self.bg_color.get()
                else:  # custom
                    bg_color = self.image_bg_color.get()

                background = Image.new('RGB', (bg_size, bg_size), bg_color)

                # Handle transparency in overlay
                if overlay.mode in ('RGBA', 'LA') or (
                    overlay.mode == 'P' and 'transparency' in overlay.info
                ):
                    background.paste(overlay, (padding, padding), overlay)
                else:
                    background.paste(overlay, (padding, padding))

                overlay = background

            # Convert to RGBA for transparency support
            if overlay.mode != 'RGBA':
                overlay = overlay.convert('RGBA')

            # Paste overlay on QR code
            qr_img = qr_img.convert('RGBA')
            overlay_pos = (
                (qr_size - overlay.size[0]) // 2,
                (qr_size - overlay.size[1]) // 2,
            )
            qr_img.paste(overlay, overlay_pos, overlay)

            return qr_img.convert('RGB')

        except Exception as e:
            messagebox.showerror(
                "Image Error", f"Failed to add image overlay: {str(e)}"
            )
            return qr_img

    def update_preview(self):
        if self.qr_image:
            # Resize for preview (max 400x400)
            preview_size = min(400, self.qr_image.size[0])
            preview_img = self.qr_image.resize(
                (preview_size, preview_size), Image.Resampling.LANCZOS
            )

            self.preview_image = ImageTk.PhotoImage(preview_img)

            # Clear canvas and center image
            self.canvas.delete("all")
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            x = (canvas_width - preview_size) // 2
            y = (canvas_height - preview_size) // 2

            self.canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image)

    def copy_image_to_clipboard(self):
        """Copy QR image to clipboard - CROSS-PLATFORM VERSION"""
        if not self.qr_image:
            messagebox.showwarning("Warning", "No QR code to copy. Generate one first.")
            return

        success = False
        error_msg = ""

        try:
            # Method 1: Try Windows clipboard (most reliable on Windows)
            if platform.system() == "Windows":
                try:
                    import io
                    from PIL import Image

                    # Convert image to bitmap format for Windows clipboard
                    output = io.BytesIO()
                    # Convert to RGB if not already (Windows clipboard needs RGB)
                    img_copy = self.qr_image.convert('RGB')
                    img_copy.save(output, format='BMP')
                    data = output.getvalue()[14:]  # Remove BMP header for clipboard
                    output.close()

                    # Use win32clipboard if available
                    try:
                        import win32clipboard

                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                        win32clipboard.CloseClipboard()
                        success = True
                    except ImportError:
                        # Fallback: Save temp file and use PowerShell
                        temp_file = os.path.join(tempfile.gettempdir(), "qr_temp.png")
                        self.qr_image.save(temp_file)

                        powershell_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("{temp_file}")
[System.Windows.Forms.Clipboard]::SetImage($img)
$img.Dispose()
'''
                        subprocess.run(
                            ["powershell", "-Command", powershell_cmd],
                            capture_output=True,
                            check=True,
                        )
                        os.unlink(temp_file)  # Clean up
                        success = True

                except Exception as e:
                    error_msg = f"Windows clipboard failed: {e}"

            # Method 2: Try macOS clipboard
            elif platform.system() == "Darwin":
                try:
                    temp_file = os.path.join(tempfile.gettempdir(), "qr_temp.png")
                    self.qr_image.save(temp_file)

                    # Use osascript to copy image to clipboard
                    applescript = f'''
tell application "System Events"
    set the clipboard to (read file POSIX file "{temp_file}" as «class PNGf»)
end tell
'''
                    subprocess.run(["osascript", "-e", applescript], check=True)
                    os.unlink(temp_file)  # Clean up
                    success = True

                except Exception as e:
                    error_msg = f"macOS clipboard failed: {e}"

            # Method 3: Try Linux clipboard
            elif platform.system() == "Linux":
                try:
                    temp_file = os.path.join(tempfile.gettempdir(), "qr_temp.png")
                    self.qr_image.save(temp_file)

                    # Try different Linux clipboard utilities
                    linux_commands = [
                        [
                            "xclip",
                            "-selection",
                            "clipboard",
                            "-t",
                            "image/png",
                            "-i",
                            temp_file,
                        ],
                        ["wl-copy", "--type", "image/png"],  # Wayland
                    ]

                    for cmd in linux_commands:
                        try:
                            if cmd[0] == "wl-copy":
                                # Wayland needs input from stdin
                                with open(temp_file, 'rb') as f:
                                    subprocess.run(cmd, stdin=f, check=True)
                            else:
                                subprocess.run(cmd, check=True)
                            success = True
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue

                    os.unlink(temp_file)  # Clean up

                    if not success:
                        error_msg = "No suitable Linux clipboard utility found (tried xclip, wl-copy)"

                except Exception as e:
                    error_msg = f"Linux clipboard failed: {e}"

            # Method 4: Universal fallback - save to desktop/downloads
            if not success:
                try:
                    # Save to desktop or downloads
                    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                    downloads = os.path.join(os.path.expanduser("~"), "Downloads")

                    if os.path.exists(desktop):
                        save_dir = desktop
                    elif os.path.exists(downloads):
                        save_dir = downloads
                    else:
                        save_dir = os.path.expanduser("~")

                    filename = f"QR_Code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = os.path.join(save_dir, filename)
                    self.qr_image.save(filepath)

                    messagebox.showinfo(
                        "Image Saved",
                        f"Image clipboard not available.\n\n"
                        f"QR code saved to:\n{filepath}\n\n"
                        f"You can manually copy it from there.",
                    )
                    return

                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Failed to copy image to clipboard:\n{error_msg}\n\n"
                        f"Also failed to save fallback file: {str(e)}",
                    )
                    return

            if success:
                messagebox.showinfo("Success", "QR code image copied to clipboard!")
            else:
                messagebox.showerror(
                    "Error", f"Failed to copy image to clipboard:\n{error_msg}"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error copying image: {str(e)}")

    def copy_text_to_clipboard(self):
        """Copy QR text content to clipboard (renamed from copy_to_clipboard)"""
        # This is the existing copy_to_clipboard method renamed
        content = self.get_content_string()
        if not content:
            messagebox.showwarning("Warning", "No content to copy")
            return

        success = False
        error_msg = ""

        # Method 1: Try tkinter clipboard (most reliable)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()  # Ensure clipboard is updated
            success = True
        except Exception as e:
            error_msg = f"Tkinter clipboard failed: {e}"

        # Method 2: Try pyperclip if available
        if not success and CLIPBOARD_AVAILABLE:
            try:
                import pyperclip

                pyperclip.copy(content)
                success = True
            except Exception as e:
                error_msg += f"\nPyperclip failed: {e}"

        # Method 3: Try system commands
        if not success:
            system = platform.system()
            try:
                if system == "Windows":
                    subprocess.run(['clip'], input=content.encode(), check=True)
                    success = True
                elif system == "Darwin":  # macOS
                    subprocess.run(['pbcopy'], input=content.encode(), check=True)
                    success = True
                elif system == "Linux":
                    # Try multiple Linux clipboard utilities
                    for cmd in [
                        ['xclip', '-selection', 'clipboard'],
                        ['xsel', '--clipboard', '--input'],
                        ['wl-copy'],
                    ]:  # Wayland support
                        try:
                            subprocess.run(cmd, input=content.encode(), check=True)
                            success = True
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
            except Exception as e:
                error_msg += f"\nSystem clipboard failed: {e}"

        # Method 4: Fallback - save to temp file
        if not success:
            temp_file = os.path.join(tempfile.gettempdir(), "qr_content.txt")
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo(
                    "Clipboard Alternative",
                    f"Clipboard not available. Content saved to:\n{temp_file}\n\nYou can open this file and copy the content manually.",
                )
                return
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"All clipboard methods failed:\n{error_msg}\n\nFinal error: {str(e)}",
                )
                return

        if success:
            messagebox.showinfo("Success", "Content copied to clipboard!")
        else:
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n{error_msg}")

    # Keep the old method name for backward compatibility but make it copy image by default
    def copy_to_clipboard(self):
        """Copy QR image to clipboard (default behavior)"""
        self.copy_image_to_clipboard()

    def export_qr(self):
        if not self.qr_image:
            messagebox.showwarning(
                "Warning", "No QR code to export. Generate one first."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Save QR Code",
            initialdir="./exports",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*"),
            ],
        )

        if filename:
            try:
                self.qr_image.save(filename)
                self.status_label.config(text=f"QR code saved as {filename}")
                messagebox.showinfo("Success", f"QR code saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save QR code: {str(e)}")

    def save_config(self):
        """Save configuration - FIXED VERSION"""
        try:
            config = {
                'preset': self.preset_var.get(),
                'theme': self.theme_var.get(),
                'color_mask': getattr(
                    self, 'color_mask_var', tk.StringVar(value="Solid Fill")
                ).get(),
                'size': self.size_var.get(),
                'border': self.border_var.get(),
                'error_correction': self.error_correction_var.get(),
                'fg_color': self.fg_color.get(),
                'bg_color': self.bg_color.get(),
                'use_image': self.use_image_var.get(),
                'image_path': self.image_path_var.get(),
                'image_size': self.image_size_var.get(),
                'image_bg': self.image_bg_var.get(),
                'image_bg_color': self.image_bg_color.get(),
                'image_padding': self.image_padding_var.get(),
                'mask_image_path': getattr(
                    self, 'mask_image_path_var', tk.StringVar()
                ).get(),
                'content': self.get_content_string(),
            }

            filename = filedialog.asksaveasfilename(
                title="Save Configuration",
                initialdir="./config/user_presets",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if filename:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Success", "Configuration saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def load_config(self):
        """Load configuration - FIXED VERSION"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            initialdir="./config/user_presets",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)

                # Apply configuration safely
                try:
                    # Basic settings
                    self.preset_var.set(config.get('preset', 'general'))

                    # Theme mapping - handle both old and new formats
                    theme_value = config.get('theme', 'classic')
                    if theme_value in self.theme_reverse_map:
                        self.theme_var.set(self.theme_reverse_map[theme_value])
                    else:
                        self.theme_var.set(theme_value)

                    # Color mask mapping
                    if hasattr(self, 'color_mask_var'):
                        mask_value = config.get('color_mask', 'solid')
                        if (
                            hasattr(self, 'color_mask_reverse_map')
                            and mask_value in self.color_mask_reverse_map
                        ):
                            self.color_mask_var.set(
                                self.color_mask_reverse_map[mask_value]
                            )
                        else:
                            self.color_mask_var.set(mask_value)

                    # Size settings
                    self.size_var.set(config.get('size', 400))
                    self.border_var.set(config.get('border', 4))
                    self.error_correction_var.set(config.get('error_correction', 'M'))

                    # Colors
                    self.fg_color.set(config.get('fg_color', '#000000'))
                    self.bg_color.set(config.get('bg_color', '#FFFFFF'))

                    # Image settings
                    self.use_image_var.set(config.get('use_image', False))
                    self.image_path_var.set(config.get('image_path', ''))
                    self.image_size_var.set(config.get('image_size', 20))
                    self.image_bg_var.set(config.get('image_bg', 'match'))
                    self.image_bg_color.set(config.get('image_bg_color', '#FFFFFF'))
                    self.image_padding_var.set(config.get('image_padding', 10))

                    # Mask image path
                    if hasattr(self, 'mask_image_path_var'):
                        self.mask_image_path_var.set(config.get('mask_image_path', ''))

                    # Update color buttons safely
                    try:
                        self.fg_color_btn.config(bg=self.fg_color.get())
                        self.bg_color_btn.config(bg=self.bg_color.get())
                        self.image_bg_color_btn.config(bg=self.image_bg_color.get())
                    except Exception as e:
                        print(f"Color button update error: {e}")

                    # Update UI state
                    self.on_preset_change()
                    self.toggle_image_options()
                    self.toggle_image_mask_frame()

                    # Restore content if available and applicable
                    content = config.get('content', '')
                    if content:
                        preset = self.preset_var.get()
                        if preset == 'general' and hasattr(self, 'text_content'):
                            self.text_content.delete(1.0, tk.END)
                            self.text_content.insert(1.0, content)
                        elif preset == 'url' and hasattr(self, 'url_var'):
                            self.url_var.set(content)
                        # Add more preset-specific content restoration as needed

                    messagebox.showinfo("Success", "Configuration loaded successfully")

                except Exception as e:
                    messagebox.showerror(
                        "Configuration Error", f"Error applying configuration: {str(e)}"
                    )

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON file: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def load_default_config(self):
        """Load default configuration"""
        # Set default text content
        if hasattr(self, 'text_content'):
            self.text_content.insert(1.0, "Welcome to Enhanced QR Generator!")

        # Initialize mask image path if available
        if IMAGE_COLOR_MASK_AVAILABLE and not hasattr(self, 'mask_image_path_var'):
            self.mask_image_path_var = tk.StringVar()

        # Initialize color input state after widgets are created
        self.root.after(50, self.toggle_color_inputs)  # Add this line

        # Generate initial QR after a short delay
        self.root.after(100, self.generate_qr)

    def share_qr(self):
        """Share QR code via various methods"""
        if not self.qr_image:
            messagebox.showwarning(
                "Warning", "No QR code to share. Generate one first."
            )
            return

        # Create share dialog
        share_window = tk.Toplevel(self.root)
        share_window.title("Share QR Code")
        share_window.geometry("300x200")

        ttk.Label(
            share_window, text="Choose sharing method:", font=('Arial', 12, 'bold')
        ).pack(pady=10)

        # Share options
        ttk.Button(
            share_window,
            text="📁 Save & Open Folder",
            command=lambda: self.share_via_folder(share_window),
        ).pack(pady=5, fill=tk.X, padx=20)
        ttk.Button(
            share_window,
            text="📋 Copy Content",
            command=lambda: self.share_copy_content(share_window),
        ).pack(pady=5, fill=tk.X, padx=20)

        ttk.Button(share_window, text="Cancel", command=share_window.destroy).pack(
            pady=10
        )

    def share_via_folder(self, share_window):
        """Save QR code and open containing folder"""
        try:
            # Save to desktop or downloads
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")

            if os.path.exists(desktop):
                save_dir = desktop
            elif os.path.exists(downloads):
                save_dir = downloads
            else:
                save_dir = os.path.expanduser("~")

            default_filename = f"QR_Code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(save_dir, default_filename)

            self.qr_image.save(filepath)

            # Open folder containing the file
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", "/select,", filepath])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-R", filepath])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(filepath)])

            messagebox.showinfo("Success", f"QR code saved to {filepath}")
            share_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save and open folder: {str(e)}")

    def share_copy_content(self, share_window):
        """Copy QR content for sharing"""
        self.copy_to_clipboard()
        share_window.destroy()

    def check_scanning_dependencies(self):
        """Check what scanning dependencies are available"""
        opencv_available = False
        pyzbar_available = False
        zbar_system_available = False

        try:
            import cv2

            opencv_available = True
        except ImportError:
            pass

        try:
            import pyzbar

            pyzbar_available = True
        except ImportError:
            pass

        # Check system zbar library
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["pkg-config", "--exists", "zbar"], capture_output=True
                )
                zbar_system_available = result.returncode == 0
            except:
                # Fallback: check for library files
                lib_paths = [
                    "/usr/lib/libzbar.so",
                    "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
                    "/usr/local/lib/libzbar.so",
                ]
                zbar_system_available = any(os.path.exists(path) for path in lib_paths)
        else:
            zbar_system_available = True  # Assume available on Windows/macOS

        return opencv_available, pyzbar_available, zbar_system_available

    def scan_qr_file(self):
        """Enhanced QR scanning with comprehensive dependency checking"""
        opencv_available, pyzbar_available, zbar_system_available = (
            self.check_scanning_dependencies()
        )

        if not opencv_available or not pyzbar_available:
            missing = []
            if not opencv_available:
                missing.append("opencv-python-headless")
            if not pyzbar_available:
                missing.append("pyzbar")

            message = f"QR scanning requires additional packages:\n\n"
            message += f"Missing: {', '.join(missing)}\n\n"
            message += f"Install with:\n"
            message += f"pip install {' '.join(missing)}\n\n"

            if not zbar_system_available and platform.system() == "Linux":
                message += f"Also install system library:\n"
                message += f"sudo apt-get install libzbar0  # Ubuntu/Debian\n"
                message += f"sudo dnf install zbar          # Fedora\n"
                message += f"sudo pacman -S zbar           # Arch\n\n"

            message += f"Then restart the application."

            messagebox.showinfo("Scanning Dependencies Required", message)
            return

        if not zbar_system_available:
            message = f"QR scanning requires the zbar system library:\n\n"
            if platform.system() == "Linux":
                message += f"Install with:\n"
                message += f"sudo apt-get install libzbar0  # Ubuntu/Debian\n"
                message += f"sudo dnf install zbar          # Fedora\n"
                message += f"sudo pacman -S zbar           # Arch\n\n"
                message += f"Then restart the application."
            else:
                message += f"This should be automatically available on your system."

            messagebox.showinfo("System Library Required", message)
            return

        # All dependencies available, proceed with scanning
        filename = filedialog.askopenfilename(
            title="Select QR Code Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico *.tiff *.webp")
            ],
        )

        if filename:
            try:
                import cv2
                from pyzbar import pyzbar

                # Read image with better error handling
                image = cv2.imread(filename)
                if image is None:
                    # Try different image reading methods
                    try:
                        from PIL import Image as PILImage
                        import numpy as np

                        pil_image = PILImage.open(filename)
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    except Exception:
                        messagebox.showerror(
                            "Error", f"Could not read image file: {filename}"
                        )
                        return

                # Decode QR codes
                decoded_objects = pyzbar.decode(image)

                if not decoded_objects:
                    # Try image preprocessing to improve detection
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # Try different preprocessing methods
                    methods = [
                        ("Original", gray),
                        ("Gaussian Blur", cv2.GaussianBlur(gray, (5, 5), 0)),
                        (
                            "Threshold",
                            cv2.threshold(
                                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                            )[1],
                        ),
                        (
                            "Adaptive Threshold",
                            cv2.adaptiveThreshold(
                                gray,
                                255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY,
                                11,
                                2,
                            ),
                        ),
                    ]

                    for method_name, processed in methods:
                        decoded_objects = pyzbar.decode(processed)
                        if decoded_objects:
                            break

                    if not decoded_objects:
                        messagebox.showinfo(
                            "No QR Codes Found",
                            "No QR codes found in the image.\n\n"
                            "Tips:\n"
                            "• Ensure the QR code is clearly visible\n"
                            "• Try a higher resolution image\n"
                            "• Make sure the image is not rotated\n"
                            "• Check that the QR code is not damaged",
                        )
                        return

                # Process results
                results = []
                for i, obj in enumerate(decoded_objects):
                    try:
                        content = obj.data.decode('utf-8')
                        results.append(
                            {
                                'content': content,
                                'type': obj.type,
                                'position': (
                                    obj.rect.left,
                                    obj.rect.top,
                                    obj.rect.width,
                                    obj.rect.height,
                                ),
                            }
                        )
                    except UnicodeDecodeError:
                        # Handle binary data
                        results.append(
                            {
                                'content': f"[Binary data: {len(obj.data)} bytes]",
                                'type': obj.type,
                                'position': (
                                    obj.rect.left,
                                    obj.rect.top,
                                    obj.rect.width,
                                    obj.rect.height,
                                ),
                            }
                        )

                # Show results
                if len(results) == 1:
                    content = results[0]['content']
                    qr_type = results[0]['type']
                    messagebox.showinfo(
                        "QR Code Found", f"Type: {qr_type}\n\nContent:\n{content}"
                    )
                else:
                    result_text = f"Found {len(results)} QR codes:\n\n"
                    for i, result in enumerate(results, 1):
                        result_text += (
                            f"{i}. {result['type']}: {result['content'][:100]}\n"
                        )
                        if len(result['content']) > 100:
                            result_text += "   ...\n"
                    messagebox.showinfo("Multiple QR Codes Found", result_text)

            except ImportError as e:
                messagebox.showerror(
                    "Import Error", f"Required library not available: {e}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Scanning Error", f"Failed to scan QR code: {str(e)}"
                )

    def show_scanning_install_help(self):
        """Enhanced installation help with step-by-step instructions"""
        opencv_available, pyzbar_available, zbar_system_available = (
            self.check_scanning_dependencies()
        )

        # Create detailed help window
        help_window = tk.Toplevel(self.root)
        help_window.title("QR Scanning Setup Guide")
        help_window.geometry("700x500")
        help_window.configure(bg='#f0f0f0')

        # Create scrollable text area
        frame = ttk.Frame(help_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Consolas', 10), bg='white')
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Generate help content based on current status
        help_content = "📱 QR Code Scanning Setup Guide\n"
        help_content += "=" * 50 + "\n\n"

        help_content += "📊 Current Status:\n"
        help_content += (
            f"  OpenCV: {'✅ Available' if opencv_available else '❌ Missing'}\n"
        )
        help_content += (
            f"  PyZBar: {'✅ Available' if pyzbar_available else '❌ Missing'}\n"
        )
        help_content += f"  ZBar System Library: {'✅ Available' if zbar_system_available else '❌ Missing'}\n\n"

        if opencv_available and pyzbar_available and zbar_system_available:
            help_content += (
                "🎉 All dependencies are installed! QR scanning should work.\n\n"
            )
            help_content += "If scanning still doesn't work:\n"
            help_content += "• Restart the application\n"
            help_content += "• Try a clearer image\n"
            help_content += "• Ensure QR code is not damaged\n"
        else:
            help_content += "🔧 Installation Steps:\n\n"

            step = 1
            if not opencv_available:
                help_content += f"{step}. Install OpenCV:\n"
                help_content += "   pip install opencv-python-headless\n\n"
                step += 1

            if not pyzbar_available:
                help_content += f"{step}. Install PyZBar:\n"
                help_content += "   pip install pyzbar\n\n"
                step += 1

            if not zbar_system_available:
                help_content += f"{step}. Install ZBar system library:\n"
                if platform.system() == "Linux":
                    help_content += "   Ubuntu/Debian: sudo apt-get install libzbar0\n"
                    help_content += "   Fedora/RHEL:   sudo dnf install zbar\n"
                    help_content += "   Arch Linux:    sudo pacman -S zbar\n"
                elif platform.system() == "Darwin":
                    help_content += "   macOS: brew install zbar\n"
                else:
                    help_content += "   Windows: Usually included with pyzbar\n"
                help_content += "\n"
                step += 1

            help_content += f"{step}. Restart the application\n\n"

        help_content += "💡 Alternative Installation:\n"
        help_content += "If you have issues, try installing all at once:\n"
        help_content += "pip install opencv-python-headless pyzbar\n\n"

        help_content += "🐧 Linux Users:\n"
        help_content += "If you used the setup script, it should have offered\n"
        help_content += "to install system dependencies automatically.\n\n"

        help_content += "🆘 Still Having Issues?\n"
        help_content += "• Check that you're using Python 3.7-3.12\n"
        help_content += "• Try: pip install --upgrade pip\n"
        help_content += "• Some packages may not work with Python 3.13+\n"

        text_widget.insert(tk.END, help_content)
        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)


def main():
    root = tk.Tk()
    app = QRCodeGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
