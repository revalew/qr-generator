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
from qrcode.image.styles.colormasks import (
    SolidFillColorMask,
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask,
    ImageColorMask,
)
from PIL import Image, ImageDraw
import io
import base64
import json
import urllib.parse
from js import document, window, Blob, URL, console, File, FileReader
from pyodide.ffi import create_proxy
import asyncio


class EnhancedQRGenerator:
    def __init__(self):
        self.current_qr_image = None
        self.current_content = ""
        self.overlay_image = None
        self.mask_image = None
        self.config = self.get_default_config()

        # Initialize UI
        self.setup_ui()
        self.setup_event_handlers()

        # Generate initial QR
        self.generate_qr()

    def get_default_config(self):
        return {
            "content_type": "general",
            "theme": "classic",
            "color_mask": "solid",
            "size": 400,
            "border": 4,
            "error_correction": "Q",
            "fg_color": "#000000",
            "bg_color": "#ffffff",
            "use_image": False,
            "image_size": 20,
            "image_bg": "match",
            "image_bg_color": "#ffffff",
            "image_padding": 0,
        }

    def setup_ui(self):
        """Initialize UI state"""
        # Update loading status
        qr_display = document.getElementById("qr-display")
        qr_display.innerHTML = '<div class="loading-text">✅ Python loaded! Ready to generate QR codes.</div>'

        # Initialize tab switching
        tab_buttons = document.querySelectorAll(".tab-btn")
        for btn in tab_buttons:
            btn.addEventListener("click", create_proxy(self.switch_tab))

        # Initialize content type switching
        preset_buttons = document.querySelectorAll(".preset-btn")
        for btn in preset_buttons:
            btn.addEventListener("click", create_proxy(self.switch_content_type))

    def setup_event_handlers(self):
        """Setup all event handlers"""

        # Form inputs for auto-generation
        auto_generate_elements = [
            "general-text",
            "url-input",
            "wifi-ssid",
            "wifi-password",
            "vcard-name",
            "vcard-org",
            "vcard-phone",
            "vcard-email",
            "vcard-url",
            "email-to",
            "email-subject",
            "email-body",
            "phone-number",
            "sms-number",
            "sms-message",
            "theme-select",
            "color-mask-select",
            "fg-color",
            "fg-color-text",
            "bg-color",
            "bg-color-text",
            "qr-size",
            "qr-border",
            "image-size",
            "image-padding",
            "image-bg-color",
            "image-bg-color-text",
        ]

        for element_id in auto_generate_elements:
            element = document.getElementById(element_id)
            if element:
                element.addEventListener("input", create_proxy(self.on_input_change))
                element.addEventListener("change", create_proxy(self.on_input_change))

        # Radio buttons
        radio_groups = ["wifi-security", "error-correction", "image-bg"]
        for group in radio_groups:
            radios = document.querySelectorAll(f'input[name="{group}"]')
            for radio in radios:
                radio.addEventListener("change", create_proxy(self.on_input_change))

        # Checkboxes
        checkbox_ids = ["wifi-hidden", "use-image-overlay"]
        for cb_id in checkbox_ids:
            element = document.getElementById(cb_id)
            if element:
                element.addEventListener(
                    "change", create_proxy(self.on_checkbox_change)
                )

        # Slider displays
        sliders = [
            ("qr-size", "size-display", "px"),
            ("qr-border", "border-display", ""),
            ("image-size", "image-size-display", "%"),
            ("image-padding", "padding-display", "px"),
        ]
        for slider_id, display_id, unit in sliders:
            element = document.getElementById(slider_id)
            if element:
                element.addEventListener(
                    "input",
                    create_proxy(
                        lambda e, d=display_id, u=unit: self.update_slider_display(
                            e, d, u
                        )
                    ),
                )

        # Color synchronization
        color_pairs = [
            ("fg-color", "fg-color-text"),
            ("bg-color", "bg-color-text"),
            ("image-bg-color", "image-bg-color-text"),
        ]
        for color_id, text_id in color_pairs:
            color_element = document.getElementById(color_id)
            text_element = document.getElementById(text_id)
            if color_element and text_element:
                color_element.addEventListener(
                    "input",
                    create_proxy(lambda e, t=text_id: self.sync_color_to_text(e, t)),
                )
                text_element.addEventListener(
                    "input",
                    create_proxy(lambda e, c=color_id: self.sync_text_to_color(e, c)),
                )

        # Color mask change
        mask_select = document.getElementById("color-mask-select")
        if mask_select:
            mask_select.addEventListener(
                "change", create_proxy(self.on_color_mask_change)
            )

        # File uploads
        self.setup_file_handlers()

        # Action buttons
        button_handlers = {
            "generate-btn": self.generate_qr,
            "download-btn": self.download_qr,
            "download-btn-2": self.download_qr,
            "download-btn-3": self.download_qr,
            "copy-image-btn": self.copy_image,
            "copy-image-btn-2": self.copy_image,
            "copy-text-btn": self.copy_text,
            "share-btn": self.share_qr,
            # "print-btn": self.print_qr,
            "print-btn-2": self.print_qr_fallback,
            "save-config-btn": self.save_config,
            "load-config-btn": self.load_config,
        }

        for btn_id, handler in button_handlers.items():
            element = document.getElementById(btn_id)
            if element:
                element.addEventListener("click", create_proxy(handler))

        format_select = document.getElementById("export-format")
        if format_select:
            format_select.addEventListener(
                "change", create_proxy(self.on_format_change)
            )

    def setup_file_handlers(self):
        """Simple file upload handlers with working drag & drop"""

        # 1. Smart global drag prevention - allow only in specific zones
        def smart_drag_prevention(event):
            # Check if we're in an allowed drop zone
            target = event.target
            current = target

            # Check up to 5 levels in DOM
            for _ in range(5):
                if not current:
                    break
                if hasattr(current, "id") and current.id in [
                    "overlay-image-upload",
                    "mask-image-upload",
                ]:
                    # We're in allowed zone - DO NOT block
                    return
                if hasattr(current, "parentElement"):
                    current = current.parentElement
                else:
                    break

            # Not in allowed zone - block it
            event.preventDefault()
            event.stopPropagation()
            return False

        # Add smart prevention to document only
        for event_name in ["dragenter", "dragover", "dragleave", "drop"]:
            document.addEventListener(
                event_name, create_proxy(smart_drag_prevention), True
            )

        # 2. Overlay image handlers
        overlay_upload = document.getElementById("overlay-image-upload")
        overlay_input = document.getElementById("overlay-image-input")

        if overlay_upload and overlay_input:
            # Click handler
            overlay_upload.addEventListener(
                "click", create_proxy(lambda e: overlay_input.click())
            )
            overlay_input.addEventListener(
                "change", create_proxy(self.handle_overlay_image)
            )

            # Drag handlers - these will work because smart prevention allows them
            def handle_overlay_dragenter(event):
                event.preventDefault()
                event.stopPropagation()
                overlay_upload.classList.add("dragover")
                # console.log("Overlay drag enter")

            def handle_overlay_dragover(event):
                event.preventDefault()
                event.stopPropagation()
                overlay_upload.classList.add("dragover")

            def handle_overlay_dragleave(event):
                event.preventDefault()
                event.stopPropagation()
                # Check if really leaving the element
                rect = overlay_upload.getBoundingClientRect()
                if (
                    event.clientX < rect.left
                    or event.clientX > rect.right
                    or event.clientY < rect.top
                    or event.clientY > rect.bottom
                ):
                    overlay_upload.classList.remove("dragover")
                    # console.log("Overlay drag leave")

            def handle_overlay_drop(event):
                event.preventDefault()
                event.stopPropagation()
                overlay_upload.classList.remove("dragover")
                # console.log("Overlay drop")

                files = event.dataTransfer.files
                if files.length > 0:
                    overlay_input.files = files
                    overlay_input.dispatchEvent(window.Event.new("change"))

            # Add all drag event listeners
            overlay_upload.addEventListener(
                "dragenter", create_proxy(handle_overlay_dragenter)
            )
            overlay_upload.addEventListener(
                "dragover", create_proxy(handle_overlay_dragover)
            )
            overlay_upload.addEventListener(
                "dragleave", create_proxy(handle_overlay_dragleave)
            )
            overlay_upload.addEventListener("drop", create_proxy(handle_overlay_drop))

        # 3. Mask image handlers - identical logic
        mask_upload = document.getElementById("mask-image-upload")
        mask_input = document.getElementById("mask-image-input")

        if mask_upload and mask_input:
            # Click handler
            mask_upload.addEventListener(
                "click", create_proxy(lambda e: mask_input.click())
            )
            mask_input.addEventListener("change", create_proxy(self.handle_mask_image))

            # Drag handlers
            def handle_mask_dragenter(event):
                event.preventDefault()
                event.stopPropagation()
                mask_upload.classList.add("dragover")
                # console.log("Mask drag enter")

            def handle_mask_dragover(event):
                event.preventDefault()
                event.stopPropagation()
                mask_upload.classList.add("dragover")

            def handle_mask_dragleave(event):
                event.preventDefault()
                event.stopPropagation()
                rect = mask_upload.getBoundingClientRect()
                if (
                    event.clientX < rect.left
                    or event.clientX > rect.right
                    or event.clientY < rect.top
                    or event.clientY > rect.bottom
                ):
                    mask_upload.classList.remove("dragover")
                    # console.log("Mask drag leave")

            def handle_mask_drop(event):
                event.preventDefault()
                event.stopPropagation()
                mask_upload.classList.remove("dragover")
                # console.log("Mask drop")

                files = event.dataTransfer.files
                if files.length > 0:
                    mask_input.files = files
                    mask_input.dispatchEvent(window.Event.new("change"))

            # Add all drag event listeners
            mask_upload.addEventListener(
                "dragenter", create_proxy(handle_mask_dragenter)
            )
            mask_upload.addEventListener("dragover", create_proxy(handle_mask_dragover))
            mask_upload.addEventListener(
                "dragleave", create_proxy(handle_mask_dragleave)
            )
            mask_upload.addEventListener("drop", create_proxy(handle_mask_drop))

        # 4. Other file handlers (click only)
        config_input = document.getElementById("config-file-input")
        if config_input:
            config_input.addEventListener(
                "change", create_proxy(self.handle_config_file)
            )

        # Batch file
        batch_upload = document.getElementById("batch-file-upload")
        batch_input = document.getElementById("batch-file-input")
        if batch_upload and batch_input:
            batch_upload.addEventListener(
                "click", create_proxy(lambda e: batch_input.click())
            )
            batch_input.addEventListener("change", create_proxy(self.handle_batch_file))

        # Scan file
        scan_upload = document.getElementById("scan-file-upload")
        scan_input = document.getElementById("scan-file-input")
        if scan_upload and scan_input:
            scan_upload.addEventListener(
                "click", create_proxy(lambda e: scan_input.click())
            )
            scan_input.addEventListener("change", create_proxy(self.handle_scan_file))

    def switch_tab(self, event):
        """Switch between tabs"""
        # Remove active class from all tabs and contents
        tab_buttons = document.querySelectorAll(".tab-btn")
        tab_contents = document.querySelectorAll(".tab-content")

        for btn in tab_buttons:
            btn.classList.remove("active")
        for content in tab_contents:
            content.classList.remove("active")

        # Add active class to clicked tab
        event.target.classList.add("active")
        tab_name = event.target.getAttribute("data-tab")
        tab_content = document.getElementById(f"{tab_name}-tab")
        if tab_content:
            tab_content.classList.add("active")

    def switch_content_type(self, event):
        """Switch content type and show appropriate form"""
        # Remove active class from all preset buttons
        preset_buttons = document.querySelectorAll(".preset-btn")
        for btn in preset_buttons:
            btn.classList.remove("active")

        # Add active class to clicked button
        event.target.classList.add("active")

        # Hide all content forms
        content_forms = document.querySelectorAll(".content-form")
        for form in content_forms:
            form.classList.remove("active")

        # Show selected form
        content_type = event.target.getAttribute("data-type")
        form = document.getElementById(f"{content_type}-form")
        if form:
            form.classList.add("active")

        # Set default content based on type
        self.set_default_content(content_type)
        self.generate_qr()

    def set_default_content(self, content_type):
        """Set default content for each type"""
        defaults = {
            "general": ("general-text", "Welcome to QR Generator!"),
            "url": ("url-input", "https://github.com/revalew/qr-generator"),
            "wifi": None,  # Multiple fields
            "vcard": None,  # Multiple fields
            "email": ("email-to", "contact@example.com"),
            "phone": ("phone-number", "+1-555-123-4567"),
            "sms": ("sms-number", "+1-555-123-4567"),
        }

        if defaults[content_type]:
            element_id, value = defaults[content_type]
            element = document.getElementById(element_id)
            if element:
                element.value = value

    def on_input_change(self, event):
        """Handle input changes"""
        self.generate_qr()

    def on_checkbox_change(self, event):
        """Handle checkbox changes"""
        checkbox_id = event.target.id

        if checkbox_id == "use-image-overlay":
            options = document.getElementById("image-overlay-options")
            if options:
                options.style.display = "block" if event.target.checked else "none"

        self.generate_qr()

    def on_color_mask_change(self, event):
        """Handle color mask selection change"""
        mask_type = event.target.value
        mask_group = document.getElementById("mask-image-group")

        if mask_group:
            mask_group.style.display = "block" if mask_type == "image" else "none"

        # Enable/disable color inputs for image mask
        # color_inputs = ['fg-color', 'fg-color-text', 'bg-color', 'bg-color-text']
        color_inputs = ["fg-color", "fg-color-text"]
        disabled = mask_type == "image"

        for input_id in color_inputs:
            element = document.getElementById(input_id)
            if element:
                element.disabled = disabled
                element.style.opacity = "0.5" if disabled else "1"

        self.generate_qr()

    def on_format_change(self, event):
        """Show format information when format changes"""
        format_value = event.target.value

        format_info = {
            "png": "PNG: Best quality, supports transparency, larger file size",
            "jpeg": "JPEG: Good compression, no transparency, smaller file size",
            # "svg": "SVG: Vector format, infinite scalability, perfect for print",
            "webp": "WebP: Modern format, excellent compression, good quality",
            "bmp": "BMP: Uncompressed, large file size, maximum quality",
            "tiff": "TIFF: Professional format, lossless compression, large file",
            # "ico": "ICO: Icon format for Windows, multiple sizes, up to 256px (NOT Recommended)",
        }

        info_text = format_info.get(format_value, "")

        # Update status with format info
        if info_text:
            self.show_status(f"ℹ️ {info_text}", "info")

    def update_slider_display(self, event, display_id, unit):
        """Update slider value display"""
        display_element = document.getElementById(display_id)
        if display_element:
            display_element.textContent = f"{event.target.value}{unit}"
        self.generate_qr()

    def sync_color_to_text(self, event, text_id):
        """Sync color picker to text input"""
        text_element = document.getElementById(text_id)
        if text_element:
            text_element.value = event.target.value
        self.generate_qr()

    def sync_text_to_color(self, event, color_id):
        """Sync text input to color picker"""
        value = event.target.value
        if len(value) == 7 and value.startswith("#"):
            color_element = document.getElementById(color_id)
            if color_element:
                color_element.value = value
        self.generate_qr()

    async def handle_overlay_image(self, event):
        """
        Handle overlay image file selection

        https://stackoverflow.com/questions/73105350/from-pyscript-how-can-i-access-the-file-that-i-load-from-html
        """
        files = event.target.files.to_py()
        if files.length > 0:
            for file in files:
                await self.load_image_file(file, "overlay")
            # await self.load_image_file(files, 'overlay')

    async def handle_mask_image(self, event):
        """
        Handle mask image file selection

        https://stackoverflow.com/questions/73105350/from-pyscript-how-can-i-access-the-file-that-i-load-from-html
        """
        files = event.target.files.to_py()
        if files.length > 0:
            # console.log(f"{files = }")
            for file in files:
                # console.log(f"{file = }")
                await self.load_image_file(file, "mask")
            # await self.load_image_file(files, 'mask')

    async def load_image_file(self, file, image_type):
        """Load and optimize image file using FileReader with size limits"""
        try:
            # console.log(f"Loading {image_type} image: {file.name}, size: {file.size} bytes")

            # Sprawdź rozmiar pliku (max 10MB)
            if file.size > 10 * 1024 * 1024:
                self.show_status(
                    f"❌ File too large: {file.size / (1024*1024):.1f}MB (max 10MB)",
                    "error",
                )
                return

            # Sprawdź typ pliku
            if not file.type.startswith("image/"):
                self.show_status(f"❌ Invalid file type: {file.type}", "error")
                return

            # Create a promise-based file reader
            def create_reader_promise():
                from pyodide.ffi import create_once_callable
                import asyncio

                reader = FileReader.new()
                future = asyncio.Future()

                def on_load(event):
                    try:
                        # console.log("FileReader onload triggered")
                        result = event.target.result

                        if not result:
                            future.set_exception(
                                Exception("No data received from FileReader")
                            )
                            return

                        # Convert to PIL Image with optimization
                        import base64

                        base64_data = result.split(",")[1]
                        img_data = base64.b64decode(base64_data)
                        # console.log(f"Decoded image data: {len(img_data)} bytes")

                        # Load image
                        img = Image.open(io.BytesIO(img_data))
                        # console.log(f"Original image size: {img.size}")

                        # Optimize image size for better performance
                        max_size = 2048 if image_type == "overlay" else 1024

                        if img.width > max_size or img.height > max_size:
                            # Resize keeping aspect ratio
                            img.thumbnail(
                                (max_size, max_size), Image.Resampling.LANCZOS
                            )
                            # console.log(f"Resized image to: {img.size}")

                        # Convert to RGB if necessary (for better compatibility)
                        if img.mode not in ("RGB", "RGBA"):
                            if "transparency" in img.info:
                                img = img.convert("RGBA")
                            else:
                                img = img.convert("RGB")
                            # console.log(f"Converted image mode to: {img.mode}")

                        future.set_result(img)

                    except Exception as e:
                        console.log(f"Error in FileReader onload: {e}")
                        future.set_exception(e)

                def on_error(event):
                    console.log("FileReader error occurred")
                    future.set_exception(Exception("FileReader failed to load file"))

                reader.onload = create_once_callable(on_load)
                reader.onerror = create_once_callable(on_error)

                # console.log("Starting FileReader.readAsDataURL")
                reader.readAsDataURL(file)

                return future

            # Use the reader promise
            # console.log("Creating FileReader promise")
            img = await create_reader_promise()

            # console.log(f"Successfully loaded {image_type} image")

            # Store image
            if image_type == "overlay":
                self.overlay_image = img
                upload_elem = document.getElementById("overlay-image-upload")
                if upload_elem:
                    text_elem = upload_elem.querySelector(".file-upload-text")
                    if text_elem:
                        text_elem.innerHTML = f"<p>✅ Image loaded: {file.name}</p><p>Size: {img.size[0]}x{img.size[1]}</p>"
            elif image_type == "mask":
                self.mask_image = img
                upload_elem = document.getElementById("mask-image-upload")
                if upload_elem:
                    text_elem = upload_elem.querySelector(".file-upload-text")
                    if text_elem:
                        text_elem.innerHTML = f"<p>✅ Mask loaded: {file.name}</p><p>Size: {img.size[0]}x{img.size[1]}</p>"

            # Regenerate QR after a short delay to allow UI update
            def delayed_generate():
                try:
                    self.generate_qr()
                except Exception as e:
                    console.log(f"Error in delayed QR generation: {e}")
                    self.show_status(
                        f"⚠️ Image loaded but QR generation failed: {str(e)}", "error"
                    )

            # Use setTimeout to avoid blocking
            window.setTimeout(create_proxy(delayed_generate), 100)

            self.show_status(
                f"✅ {image_type.title()} image loaded successfully!", "success"
            )

        except Exception as e:
            console.log(f"File handling error: {e}")
            self.show_status(f"❌ Error loading image: {str(e)}", "error")

    def get_content_string(self):
        """Get content string based on selected type"""
        # Find active content type
        active_btn = document.querySelector(".preset-btn.active")
        if not active_btn:
            return ""

        content_type = active_btn.getAttribute("data-type")

        if content_type == "general":
            element = document.getElementById("general-text")
            return element.value if element else ""

        elif content_type == "url":
            element = document.getElementById("url-input")
            url = element.value.strip() if element else ""
            if url and not url.startswith(("http://", "https://", "ftp://", "ftps://")):
                url = "https://" + url
            return url

        elif content_type == "wifi":
            ssid_elem = document.getElementById("wifi-ssid")
            pwd_elem = document.getElementById("wifi-password")
            hidden_elem = document.getElementById("wifi-hidden")

            ssid = ssid_elem.value.strip() if ssid_elem else ""
            password = pwd_elem.value.strip() if pwd_elem else ""
            hidden = "true" if (hidden_elem and hidden_elem.checked) else "false"

            # Get security type
            security_radios = document.querySelectorAll('input[name="wifi-security"]')
            security = ""
            for radio in security_radios:
                if radio.checked:
                    security = radio.value
                    break

            if ssid:
                return f"WIFI:T:{security};S:{ssid};P:{password};H:{hidden};"
            return ""

        elif content_type == "vcard":
            name = self.get_element_value("vcard-name")
            org = self.get_element_value("vcard-org")
            phone = self.get_element_value("vcard-phone")
            email = self.get_element_value("vcard-email")
            url = self.get_element_value("vcard-url")

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

        elif content_type == "email":
            to = self.get_element_value("email-to")
            subject = self.get_element_value("email-subject")
            body = self.get_element_value("email-body")

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

        elif content_type == "phone":
            phone = self.get_element_value("phone-number")
            return f"tel:{phone}" if phone else ""

        elif content_type == "sms":
            number = self.get_element_value("sms-number")
            message = self.get_element_value("sms-message")

            if number:
                sms_str = f"sms:{number}"
                if message:
                    sms_str += f"?body={urllib.parse.quote(message)}"
                return sms_str
            return ""

        return ""

    def get_element_value(self, element_id):
        """Helper to get element value safely"""
        element = document.getElementById(element_id)
        return element.value.strip() if element else ""

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        try:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except:
            return (0, 0, 0)

    def mix_colors(self, color1, color2, weight=0.5):
        """Mix two RGB colors"""
        return tuple(
            int(c1 * (1 - weight) + c2 * weight) for c1, c2 in zip(color1, color2)
        )

    def get_color_mask(self):
        """Get appropriate color mask"""
        mask_select = document.getElementById("color-mask-select")
        if not mask_select:
            # Fallback when no mask select element
            return SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255))
            # return None

        mask_type = mask_select.value
        fg_color = self.hex_to_rgb(self.get_element_value("fg-color"))
        bg_color = self.hex_to_rgb(self.get_element_value("bg-color"))

        try:
            if mask_type == "solid":
                return SolidFillColorMask(front_color=fg_color, back_color=bg_color)

            elif mask_type == "radial":
                middle_color = self.mix_colors(fg_color, bg_color)
                return RadialGradiantColorMask(
                    back_color=bg_color, center_color=middle_color, edge_color=fg_color
                )

            elif mask_type == "square":
                middle_color = self.mix_colors(fg_color, bg_color)
                return SquareGradiantColorMask(
                    back_color=bg_color, center_color=middle_color, edge_color=fg_color
                )

            elif mask_type == "horizontal":
                middle_color = self.mix_colors(fg_color, bg_color)
                return HorizontalGradiantColorMask(
                    back_color=bg_color, left_color=middle_color, right_color=fg_color
                )

            elif mask_type == "vertical":
                middle_color = self.mix_colors(fg_color, bg_color)
                return VerticalGradiantColorMask(
                    back_color=bg_color, top_color=middle_color, bottom_color=fg_color
                )

            elif mask_type == "image" and self.mask_image:
                try:
                    return ImageColorMask(
                        back_color=bg_color, color_mask_image=self.mask_image
                    )
                except Exception as e:
                    console.log(f"Image mask error: {e}")
                    # Fallback to solid when image mask fails
                    return SolidFillColorMask(front_color=fg_color, back_color=bg_color)

            # Fallback for unknown mask types
            return SolidFillColorMask(front_color=fg_color, back_color=bg_color)

        except Exception as e:
            console.log(f"Color mask error: {e}")
            # Fallback for any other errors
            return SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255))

    def get_module_drawer(self):
        """Get appropriate module drawer"""
        theme_select = document.getElementById("theme-select")
        if not theme_select:
            return None

        theme = theme_select.value

        if theme == "rounded":
            return RoundedModuleDrawer()
        elif theme == "circular":
            return CircleModuleDrawer()
        elif theme == "gapped":
            try:
                # from decimal import Decimal
                # return GappedSquareModuleDrawer(size_ratio=0.8)
                return GappedSquareModuleDrawer()
            except:
                return SquareModuleDrawer()
        elif theme == "vertical_bars":
            return VerticalBarsDrawer()
        elif theme == "horizontal_bars":
            return HorizontalBarsDrawer()
        else:
            # These would need to be implemented or imported
            return None

    def add_image_overlay(self, qr_img):
        """Add image overlay to QR code"""
        if not self.overlay_image:
            return qr_img

        try:
            # Get settings
            size_percent = int(self.get_element_value("image-size") or 20)
            padding = int(self.get_element_value("image-padding") or 0)

            # Get background type
            bg_radios = document.querySelectorAll('input[name="image-bg"]')
            bg_type = "match"
            for radio in bg_radios:
                if radio.checked:
                    bg_type = radio.value
                    break

            # Calculate overlay size
            qr_size = qr_img.size[0]
            overlay_size = int(qr_size * size_percent / 100)

            # Resize overlay maintaining aspect ratio
            overlay = self.overlay_image.copy()
            overlay.thumbnail((overlay_size, overlay_size), Image.Resampling.LANCZOS)
            
            # Handle rectangular background properly
            final_overlay = overlay  # This will be the final overlay to paste

            # Create background if needed
            if bg_type in ["match", "custom"]:
                # Calculate both width and height for rectangular background
                bg_width = overlay.size[0] + 2 * padding
                bg_height = overlay.size[1] + 2 * padding

                if bg_type == "match":
                    bg_color = self.get_element_value("bg-color")
                else:
                    bg_color = self.get_element_value("image-bg-color")

                # Create rectangular background instead of square
                background = Image.new("RGB", (bg_width, bg_height), bg_color)

                # Center the overlay image on the rectangular background
                overlay_x = (bg_width - overlay.size[0]) // 2
                overlay_y = (bg_height - overlay.size[1]) // 2

                # Handle transparency
                if overlay.mode in ("RGBA", "LA") or (
                    overlay.mode == "P" and "transparency" in overlay.info
                ):
                    background.paste(overlay, (overlay_x, overlay_y), overlay)
                else:
                    background.paste(overlay, (overlay_x, overlay_y))

                final_overlay = background

            # Convert images for transparency support
            if final_overlay.mode != "RGBA":
                final_overlay = final_overlay.convert("RGBA")

            qr_img = qr_img.convert("RGBA")

            # Calculate position to center the final overlay (which might be rectangular)
            overlay_pos = (
                (qr_size - final_overlay.size[0]) // 2,
                (qr_size - final_overlay.size[1]) // 2,
            )

            # Paste overlay
            qr_img.paste(final_overlay, overlay_pos, final_overlay)

            return qr_img.convert("RGB")

        except Exception as e:
            console.log(f"Overlay error: {e}")
            return qr_img

    def generate_qr(self, event=None):
        """Generate QR code with all features"""
        try:
            # Get content
            content = self.get_content_string()
            if not content:
                qr_display = document.getElementById("qr-display")
                qr_display.innerHTML = (
                    '<div class="loading-text">Enter content to generate QR code</div>'
                )
                return

            self.current_content = content

            # Get settings
            size = int(self.get_element_value("qr-size") or 400)
            border = int(self.get_element_value("qr-border") or 4)
            fg_color = self.get_element_value("fg-color") or "#000000"
            bg_color = self.get_element_value("bg-color") or "#ffffff"

            # Get error correction
            error_radios = document.querySelectorAll('input[name="error-correction"]')
            error_level = "Q"
            for radio in error_radios:
                if radio.checked:
                    error_level = radio.value
                    break

            # Error correction mapping
            error_levels = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H,
            }

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_levels.get(
                    error_level, qrcode.constants.ERROR_CORRECT_Q
                ),
                box_size=10,
                border=border,
            )

            qr.add_data(content)
            qr.make(fit=True)

            # Get styling with fallback
            try:
                color_mask = self.get_color_mask()
                module_drawer = self.get_module_drawer()

            except Exception as e:
                console.log(f"Style error: {e}")
                color_mask = None
                module_drawer = None

            # Generate image with safe fallback
            try:
                if module_drawer or color_mask:
                    qr_img = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=module_drawer,
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color,
                    )
                else:
                    qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            except Exception as e:
                console.log(f"QR styling error: {e}, falling back to basic QR")
                # Fallback to basic QR if styled generation fails
                qr_img = qr.make_image(fill_color=fg_color, back_color=bg_color)

            # Resize to target size
            qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

            # Add image overlay if enabled
            use_overlay = document.getElementById("use-image-overlay")
            if use_overlay and use_overlay.checked:
                qr_img = self.add_image_overlay(qr_img)

            # Store current image
            self.current_qr_image = qr_img

            # Convert to base64 for display
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format="PNG")
            img_data = base64.b64encode(img_buffer.getvalue()).decode()

            # Display in browser
            data_url = f"data:image/png;base64,{img_data}"
            qr_display = document.getElementById("qr-display")
            qr_display.innerHTML = f'<img src="{data_url}" alt="Generated QR Code">'

            # Update status
            self.show_status("✅ QR code generated successfully!", "success")

        except Exception as e:
            console.log(f"QR generation error: {e}")
            self.show_status(f"❌ Error: {str(e)}", "error")
            qr_display = document.getElementById("qr-display")
            qr_display.innerHTML = f'<div class="loading-text">Error: {str(e)}</div>'

    def download_qr(self, event):
        """Download QR code with custom filename and multiple formats"""
        if not self.current_qr_image:
            self.show_status("❌ Please generate a QR code first", "error")
            return

        try:
            # Get filename and format
            filename_input = document.getElementById("export-filename")
            format_select = document.getElementById("export-format")

            filename = filename_input.value if filename_input else "my-qr-code"
            file_format = format_select.value if format_select else "png"

            # Handle SVG separately (vector format)
            if file_format.upper() == "SVG":
                svg_data = self.generate_svg_qr()
                if svg_data:
                    # Create SVG download
                    blob = Blob.new([svg_data], {"type": "image/svg+xml"})
                    url = URL.createObjectURL(blob)

                    link = document.createElement("a")
                    link.href = url
                    link.download = f"{filename}.svg"
                    document.body.appendChild(link)
                    link.click()
                    document.body.removeChild(link)
                    URL.revokeObjectURL(url)

                    self.show_status("✅ SVG QR code downloaded!", "success")
                    return
                else:
                    self.show_status("❌ Failed to generate SVG", "error")
                    return

            # Handle raster formats
            img_buffer = io.BytesIO()

            if file_format.upper() == "JPEG":
                # Convert to RGB for JPEG (no transparency)
                rgb_img = self.current_qr_image.convert("RGB")
                rgb_img.save(img_buffer, format="JPEG", quality=95, optimize=True)
                mime_type = "image/jpeg"

            elif file_format.upper() == "BMP":
                # BMP format
                self.current_qr_image.save(img_buffer, format="BMP")
                mime_type = "image/bmp"

            elif file_format.upper() == "TIFF":
                # TIFF format with compression
                self.current_qr_image.save(img_buffer, format="TIFF", compression="lzw")
                mime_type = "image/tiff"

            elif file_format.upper() == "ICO":
                # ICO format (icon file)
                # ICO works best with smaller sizes
                ico_size = min(256, self.current_qr_image.size[0])
                ico_img = self.current_qr_image.resize(
                    (ico_size, ico_size), Image.Resampling.LANCZOS
                )
                ico_img.save(img_buffer, format="ICO")
                mime_type = "image/x-icon"

            elif file_format.upper() == "WEBP":
                # WebP format (modern, good compression)
                try:
                    self.current_qr_image.save(
                        img_buffer, format="WEBP", quality=90, lossless=True
                    )
                    mime_type = "image/webp"
                except Exception as e:
                    console.log(f"WebP not supported: {e}")
                    # Fallback to PNG
                    self.current_qr_image.save(img_buffer, format="PNG", optimize=True)
                    mime_type = "image/png"
                    file_format = "png"

            else:  # PNG (default)
                self.current_qr_image.save(img_buffer, format="PNG", optimize=True)
                mime_type = "image/png"

            # Create download for raster formats
            img_data = base64.b64encode(img_buffer.getvalue()).decode()
            data_url = f"data:{mime_type};base64,{img_data}"

            link = document.createElement("a")
            link.href = data_url
            link.download = f"{filename}.{file_format.lower()}"
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)

            self.show_status(f"✅ {file_format.upper()} QR code downloaded!", "success")

        except Exception as e:
            console.log(f"Download error: {e}")
            self.show_status(f"❌ Download failed: {str(e)}", "error")

    def generate_svg_qr(self):
        """Generate SVG version of current QR code - WITH THEME, MASK AND OVERLAY SUPPORT"""
        try:
            # Get current content
            content = self.current_content
            if not content:
                return None

            # Import SVG factory
            from qrcode.image.svg import SvgPathImage

            # Get current settings
            border = int(self.get_element_value("qr-border") or 1)

            # Get error correction
            error_radios = document.querySelectorAll('input[name="error-correction"]')
            error_level = "Q"
            for radio in error_radios:
                if radio.checked:
                    error_level = radio.value
                    break

            error_levels = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H,
            }

            # Create QR code for SVG with larger box_size for better quality
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_levels.get(
                    error_level, qrcode.constants.ERROR_CORRECT_Q
                ),
                box_size=20,
                border=border,
            )

            qr.add_data(content)
            qr.make(fit=True)

            theme_select = document.getElementById("theme-select")
            mask_select = document.getElementById("color-mask-select")
            use_overlay = document.getElementById("use-image-overlay")

            has_complex_styles = False

            # Sprawdź theme
            if theme_select and theme_select.value != "classic":
                has_complex_styles = True

            # Sprawdź mask
            if mask_select and mask_select.value not in ["solid"]:
                has_complex_styles = True

            # Sprawdź overlay
            if use_overlay and use_overlay.checked and self.overlay_image:
                has_complex_styles = True

            if has_complex_styles:
                # console.log("Complex styles detected - generating PNG-based SVG")

                # Użyj obecnego PNG QR z wszystkimi stylami
                if self.current_qr_image:
                    # Konwertuj PNG na SVG (embedded)
                    img_buffer = io.BytesIO()
                    self.current_qr_image.save(img_buffer, format="PNG")
                    img_data = base64.b64encode(img_buffer.getvalue()).decode()

                    # Utwórz SVG z embedded PNG
                    qr_size = self.current_qr_image.size[0]
                    svg_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <svg width="100%" height="100%" viewBox="0 0 {qr_size} {qr_size}" 
        preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
    <image x="0" y="0" width="{qr_size}" height="{qr_size}" 
            href="data:image/png;base64,{img_data}"/>
    </svg>"""
                    return svg_data
                else:
                    # console.log("No current QR image available")
                    return None

            # console.log("Simple styles - generating native SVG")

            # Generate SVG - FIXED: Handle both bytes and string output
            img = qr.make_image(image_factory=SvgPathImage)

            # Get SVG data - try multiple methods
            svg_data = None

            # Method 1: Try to get string directly
            try:
                if hasattr(img, "to_string"):
                    svg_data = img.to_string()
                    if isinstance(svg_data, bytes):
                        svg_data = svg_data.decode("utf-8")
            except:
                pass

            # Method 2: Try BytesIO and decode
            if not svg_data:
                try:
                    svg_buffer = io.BytesIO()
                    img.save(svg_buffer)
                    svg_bytes = svg_buffer.getvalue()
                    svg_data = svg_bytes.decode("utf-8")
                except:
                    pass

            # Method 3: Try StringIO (fallback)
            if not svg_data:
                try:
                    svg_buffer = io.StringIO()
                    img.save(svg_buffer)
                    svg_data = svg_buffer.getvalue()
                except:
                    pass

            if not svg_data:
                # console.log("Failed to extract SVG data")
                return None

            import re

            # Usunięcie atrybutów width i height z tagu <svg>
            svg_data = re.sub(r'\s*width="[^"]*"', "", svg_data)
            svg_data = re.sub(r'\s*height="[^"]*"', "", svg_data)

            # Dodanie atrybutów pozwalających na skalowanie
            svg_data = re.sub(
                r"<svg([^>]*?)>",
                r'<svg\1 width="100%" height="100%" preserveAspectRatio="xMidYMid meet">',
                svg_data,
            )

            # Apply colors to SVG
            fg_color = self.get_element_value("fg-color") or "#000000"
            bg_color = self.get_element_value("bg-color") or "#ffffff"

            # Simple color replacement in SVG
            svg_data = svg_data.replace('fill="black"', f'fill="{fg_color}"')
            svg_data = svg_data.replace('fill="#000000"', f'fill="{fg_color}"')
            svg_data = svg_data.replace('fill="#000"', f'fill="{fg_color}"')

            if bg_color.lower() not in ["#ffffff", "#fff", "white"]:
                # Znajdź tag <svg> i dodaj rect jako tło
                viewbox_match = re.search(r'viewBox="([^"]*)"', svg_data)
                if viewbox_match:
                    viewbox = viewbox_match.group(1)
                    coords = viewbox.split()
                    if len(coords) >= 4:
                        width, height = coords[2], coords[3]
                        bg_rect = f'<rect x="0" y="0" width="{width}" height="{height}" fill="{bg_color}"/>'
                        # Wstaw rect zaraz po tagu <svg>
                        svg_data = re.sub(r"(<svg[^>]*>)", r"\1" + bg_rect, svg_data)

            return svg_data

        except Exception as e:
            console.log(f"SVG generation error: {e}")
            return None

    async def copy_image(self, event):
        """Copy QR image to clipboard"""
        if not self.current_qr_image:
            self.show_status("❌ Please generate a QR code first", "error")
            return

        try:
            from pyodide.ffi import to_js
            from js import Uint8Array, ClipboardItem, Object

            # Convert image to PNG blob
            img_buffer = io.BytesIO()
            self.current_qr_image.save(img_buffer, format="PNG")
            img_data = img_buffer.getvalue()

            # Create Uint8Array
            uint8_array = Uint8Array.new(len(img_data))
            for i, byte in enumerate(img_data):
                uint8_array[i] = byte

            # Create Blob
            blob = Blob.new([uint8_array], to_js({"type": "image/png"}))
            # console.log(f"{blob.type = }")

            # Check if clipboard API is available
            if hasattr(window.navigator, "clipboard") and hasattr(
                window.navigator.clipboard, "write"
            ):
                # Firefox doesn't support ClipboardItem for images (or so i thought, it just does not appear in the clipboard manager)
                #
                # user_agent = window.navigator.userAgent
                # if "Firefox" in user_agent:
                #     is_firefox = True
                # else:
                #     is_firefox = False
                # is_firefox = False
                #
                # if is_firefox:
                #     blob_url = URL.createObjectURL(blob)
                #     window.open(blob_url)
                #     self.show_status("✅ Firefox doesn't support ClipboardItem! Opening image in new tab...", "success")
                #
                # else:
                # clipboard_item = ClipboardItem.new(to_js({"image/png": blob}))
                clipboard_item = ClipboardItem.new(to_js({blob.type: blob}))

                # Build JS object with correct MIME type key
                # clipboard_data = Object.fromEntries([[blob.type, blob]])
                # clipboard_item = ClipboardItem.new(clipboard_data)
                # console.log(clipboard_item)

                await window.navigator.clipboard.write(
                    [clipboard_item]
                )  # ✅ await is important
                self.show_status(
                    "✅ Image copied to clipboard! It might not appear in the clipboard manager",
                    "success",
                )

            else:
                self.show_status("❌ Clipboard API not available", "error")

        except Exception as e:
            console.log(f"Copy image error: {e}")
            self.show_status(f"❌ Copy failed: {str(e)}", "error")

    def copy_text(self, event):
        """Copy QR content to clipboard"""
        content = self.current_content
        if not content:
            self.show_status("❌ No content to copy", "error")
            return

        try:
            window.navigator.clipboard.writeText(content)
            self.show_status("✅ Content copied to clipboard!", "success")
        except Exception as e:
            console.log(f"Copy text error: {e}")
            self.show_status("❌ Copy failed", "error")

    def share_qr(self, event):
        """Share QR code using Web Share API"""
        if not self.current_content:
            self.show_status("❌ No content to share", "error")
            return

        try:
            if hasattr(window.navigator, "share"):
                share_data = {
                    "title": "QR Code",
                    "text": f"Check out this QR code: {self.current_content}",
                    "url": window.location.href,
                }
                window.navigator.share(share_data)
            else:
                # Fallback: copy share URL
                share_url = f"{window.location.href}?content={window.encodeURIComponent(self.current_content)}"
                window.navigator.clipboard.writeText(share_url)
                self.show_status("✅ Share link copied to clipboard!", "success")

        except Exception as e:
            console.log(f"Share error: {e}")
            self.show_status("❌ Sharing failed", "error")

    def print_qr(self, event):
        """Print QR code using SVG for best quality"""
        if not self.current_qr_image:
            self.show_status("❌ Please generate a QR code first", "error")
            return

        # 🔧 EASY SIZE CONTROL - Change this value to adjust QR code size
        qr_size_cm = 12  # Size in centimeters

        try:
            # Try SVG first (best quality for printing)
            svg_data = self.generate_svg_qr()

            if svg_data:
                # Use SVG for printing - much better quality
                print_window = window.open("", "_blank")
                print_window.document.write(
                    f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>QR Code</title>
                        <style>
                            @page {{
                                margin: 2cm;
                                size: A4;
                            }}
                            body {{
                                margin: 0;
                                padding: 0;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                min-height: 100vh;
                                font-family: Arial, sans-serif;
                            }}
                            .qr-container {{
                                text-align: center;
                                page-break-inside: avoid;
                            }}
                            .qr-code {{
                                width: {qr_size_cm}cm !important;
                                height: {qr_size_cm}cm !important;
                                max-width: {qr_size_cm}cm !important;
                                max-height: {qr_size_cm}cm !important;
                                display: block;
                            }}
                            .qr-code svg {{
                                width: 100% !important;
                                height: 100% !important;
                                display: block;
                            }}
                            .footer {{
                                margin-top: 1cm;
                                font-size: 10px;
                                color: #888;
                            }}
                            @media print {{
                                body {{
                                    margin: 0;
                                    padding: 0;
                                }}
                                .qr-code {{
                                    width: {qr_size_cm}cm !important;
                                    height: {qr_size_cm}cm !important;
                                }}
                                .qr-code svg {{
                                    width: 100% !important;
                                    height: 100% !important;
                                }}
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="qr-container">
                            <div class="qr-code">
                                {svg_data}
                            </div>
                            <div class="footer">
                                Generated with QR Generator - Vector Print Quality
                            </div>
                        </div>
                    </body>
                    </html>
                """
                )
                print_window.document.close()
                print_window.print()
                print_window.close()

                self.show_status(
                    "✅ Print dialog opened (SVG quality with all styles)", "success"
                )

            else:
                # Fallback to PNG if SVG fails
                self.print_qr_fallback(event)

        except Exception as e:
            console.log(f"SVG print error: {e}")
            # Fallback to PNG
            self.print_qr_fallback(event)

    def print_qr_fallback(self, event):
        """Fallback print function using PNG - SINGLE PAGE VERSION"""
        if not self.current_qr_image:
            self.show_status("❌ Please generate a QR code first", "error")
            return

        # 🔧 EASY SIZE CONTROL - Change this value to adjust QR code size
        qr_size_cm = 12  # Size in centimeters

        try:
            # Create print window with PNG
            img_buffer = io.BytesIO()
            self.current_qr_image.save(img_buffer, format="PNG")
            img_data = base64.b64encode(img_buffer.getvalue()).decode()
            data_url = f"data:image/png;base64,{img_data}"

            print_window = window.open("", "_blank")
            print_window.document.write(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>QR_code</title>
                    <style>
                        @page {{
                            margin: 2cm;
                            size: A4;
                        }}
                        html, body {{
                            margin: 0;
                            padding: 0;
                            width: 100%;
                            height: auto;
                            font-family: Arial, sans-serif;
                        }}
                        .qr-container {{
                            width: 100%;
                            text-align: center;
                            padding-top: 3cm;
                            page-break-inside: avoid;
                            page-break-after: avoid;
                        }}
                        .qr-code {{
                            width: {qr_size_cm}cm;
                            height: {qr_size_cm}cm;
                            max-width: {qr_size_cm}cm;
                            max-height: {qr_size_cm}cm;
                            display: block;
                            margin: 0 auto;
                        }}
                        .footer {{
                            margin-top: 1cm;
                            font-size: 10px;
                            color: #888;
                            text-align: center;
                            page-break-inside: avoid;
                        }}
                        @media print {{
                            html, body {{
                                margin: 0 !important;
                                padding: 0 !important;
                                height: auto !important;
                            }}
                            .qr-container {{
                                page-break-inside: avoid !important;
                                page-break-after: avoid !important;
                                padding-top: 2cm;
                            }}
                            .qr-code {{
                                width: {qr_size_cm}cm !important;
                                height: {qr_size_cm}cm !important;
                                display: block !important;
                                margin: 0 auto !important;
                            }}
                            .footer {{
                                page-break-inside: avoid !important;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="qr-container">
                        <img src="{data_url}" alt="QR_code" class="qr-code" />
                        <div class="footer">
                            Generated with QR Generator - PNG Quality
                        </div>
                    </div>
                </body>
                </html>
            """
            )
            print_window.document.close()
            print_window.print()
            print_window.close()

            self.show_status(
                "✅ Print dialog opened (PNG quality - single page)", "success"
            )

        except Exception as e:
            console.log(f"Print error: {e}")
            self.show_status(f"❌ Print failed: {str(e)}", "error")

    def save_config(self, event):
        """Save current configuration"""
        try:
            config = {
                "content": self.current_content,
                "theme": self.get_element_value("theme-select"),
                "color_mask": self.get_element_value("color-mask-select"),
                "size": self.get_element_value("qr-size"),
                "border": self.get_element_value("qr-border"),
                "fg_color": self.get_element_value("fg-color"),
                "bg_color": self.get_element_value("bg-color"),
                "error_correction": self.get_checked_radio("error-correction"),
                "use_image": document.getElementById("use-image-overlay").checked,
                "image_size": self.get_element_value("image-size"),
                "image_bg": self.get_checked_radio("image-bg"),
                "image_bg_color": self.get_element_value("image-bg-color"),
                "image_padding": self.get_element_value("image-padding"),
            }

            # Create download link for config
            config_data = json.dumps(config, indent=2)
            blob = Blob.new([config_data], {"type": "application/json"})
            url = URL.createObjectURL(blob)

            link = document.createElement("a")
            link.href = url
            link.download = "qr-config.json"
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)

            self.show_status("✅ Configuration saved!", "success")

        except Exception as e:
            console.log(f"Save config error: {e}")
            self.show_status(f"❌ Save failed: {str(e)}", "error")

    def load_config(self, event):
        """Load configuration from file"""
        config_input = document.getElementById("config-file-input")
        if config_input:
            config_input.click()

    async def handle_config_file(self, event):
        """Handle configuration file loading"""
        files = event.target.files
        if files.length > 0:
            try:
                # file = files[0]
                for f in files:
                    file = f

                # Read file content
                from pyodide.ffi import create_once_callable

                reader = FileReader.new()

                def on_load(event):
                    try:
                        config_text = event.target.result
                        config = json.loads(config_text)

                        # Apply configuration
                        self.apply_config(config)
                        self.show_status("✅ Configuration loaded!", "success")

                    except Exception as e:
                        console.log(f"Config parse error: {e}")
                        self.show_status(f"❌ Invalid config file: {str(e)}", "error")

                reader.onload = create_once_callable(on_load)
                reader.readAsText(file)

            except Exception as e:
                console.log(f"Config file error: {e}")
                self.show_status(f"❌ File load error: {str(e)}", "error")

    def apply_config(self, config):
        """Apply loaded configuration"""
        try:
            # Set form values
            form_mappings = {
                "theme": "theme-select",
                "color_mask": "color-mask-select",
                "size": "qr-size",
                "border": "qr-border",
                "fg_color": "fg-color",
                "bg_color": "bg-color",
                "image_size": "image-size",
                "image_bg_color": "image-bg-color",
                "image_padding": "image-padding",
            }

            for config_key, element_id in form_mappings.items():
                if config_key in config:
                    element = document.getElementById(element_id)
                    if element:
                        element.value = str(config[config_key])

            # Set radio buttons
            radio_groups = {
                "error_correction": "error-correction",
                "image_bg": "image-bg",
            }

            for config_key, group_name in radio_groups.items():
                if config_key in config:
                    radios = document.querySelectorAll(f'input[name="{group_name}"]')
                    for radio in radios:
                        radio.checked = radio.value == config[config_key]

            # Set checkboxes
            if "use_image" in config:
                element = document.getElementById("use-image-overlay")
                if element:
                    element.checked = config["use_image"]
                    # Trigger change event
                    self.on_checkbox_change(type("Event", (), {"target": element})())

            # Update displays
            self.update_all_displays()

            # Regenerate QR
            self.generate_qr()

        except Exception as e:
            console.log(f"Apply config error: {e}")
            self.show_status(f"❌ Error applying config: {str(e)}", "error")

    def get_checked_radio(self, group_name):
        """Get value of checked radio button"""
        radios = document.querySelectorAll(f'input[name="{group_name}"]')
        for radio in radios:
            if radio.checked:
                return radio.value
        return ""

    def update_all_displays(self):
        """Update all slider displays"""
        displays = [
            ("qr-size", "size-display", "px"),
            ("qr-border", "border-display", ""),
            ("image-size", "image-size-display", "%"),
            ("image-padding", "padding-display", "px"),
        ]

        for slider_id, display_id, unit in displays:
            slider = document.getElementById(slider_id)
            display = document.getElementById(display_id)
            if slider and display:
                display.textContent = f"{slider.value}{unit}"

    async def handle_batch_file(self, event):
        """Handle batch file processing"""
        files = event.target.files
        if files.length > 0:
            self.show_status("🔄 Processing batch file...", "info")
            # Implementation for batch processing would go here
            self.show_status("⚠️ Batch processing coming soon!", "info")

    async def handle_scan_file(self, event):
        """Handle QR code scanning"""
        files = event.target.files
        if files.length > 0:
            self.show_status("🔍 Scanning QR code...", "info")
            # Implementation for QR scanning would go here
            self.show_status("⚠️ QR scanning coming soon!", "info")

    def show_status(self, message, status_type):
        """Show status message with better error handling"""
        try:
            status_area = document.getElementById("status-area")
            if status_area:
                status_area.innerHTML = (
                    f'<div class="status-message status-{status_type}">{message}</div>'
                )
                # console.log(f"Status: {message}")

                # Auto-clear success/info messages
                if status_type in ["success", "info"]:

                    def clear_status():
                        try:
                            if status_area:
                                status_area.innerHTML = ""
                        except:
                            pass

                    window.setTimeout(create_proxy(clear_status), 4000)
            else:
                console.log(f"Status area not found: {message}")

        except Exception as e:
            console.log(f"Error showing status: {e}")
            console.log(f"Original message was: {message}")

    def clear_status(self):
        """Clear status message"""
        status_area = document.getElementById("status-area")
        if status_area:
            status_area.innerHTML = ""


# Initialize the QR generator
qr_generator = EnhancedQRGenerator()
