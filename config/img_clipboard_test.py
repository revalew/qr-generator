#!/usr/bin/env python3
"""
Comprehensive clipboard test for X11, Wayland, and tkinter approaches
Tests what actually works for image clipboard on Linux
"""
import tkinter as tk
from PIL import Image, ImageTk
import io
import os
import subprocess
import tempfile
from datetime import datetime
import platform


class ClipboardTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.title("Comprehensive Clipboard Test - X11/Wayland/tkinter")

        # Detect environment
        self.wayland_session = os.environ.get('WAYLAND_DISPLAY') is not None
        self.x11_session = os.environ.get('DISPLAY') is not None

        self.text_log = ""
        self.setup_ui()
        self.load_test_image()


    def setup_ui(self):
        # Environment info
        info_frame = tk.Frame(self.root, bg='#f0f0f0')
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        env_text = f"Environment: "
        if self.wayland_session:
            env_text += "Wayland ✓"
        if self.x11_session:
            env_text += " X11 ✓"
        if not self.wayland_session and not self.x11_session:
            env_text += "Unknown"

        tk.Label(info_frame, text=env_text, font=('Arial', 10, 'bold'),
                 bg='#f0f0f0').pack()

        # Canvas for image
        self.canvas = tk.Canvas(self.root, width=400, height=300, bg='white')
        self.canvas.pack(pady=10)

        # Button grid
        self.create_test_buttons()

        # Results area
        self.results_text = tk.Text(self.root, height=12, wrap=tk.WORD,
                                    font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar for results
        scrollbar = tk.Scrollbar(self.results_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)

    def create_test_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        # Row 1: tkinter tests
        row1 = tk.Frame(button_frame)
        row1.pack(pady=2)
        tk.Label(row1, text="tkinter Tests:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(row1, text="Your Code (Broken)", command=self.test_your_code,
                  bg='#ffcccc').pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="Base64 Text", command=self.test_base64_text,
                  bg='#ffffcc').pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="Text Only", command=self.test_text_only,
                  bg='#ccffcc').pack(side=tk.LEFT, padx=2)

        # Row 2: Wayland tests
        row2 = tk.Frame(button_frame)
        row2.pack(pady=2)
        tk.Label(row2, text="Wayland Tests:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(row2, text="wl-copy Image", command=self.test_wl_copy,
                  bg='#ccccff').pack(side=tk.LEFT, padx=2)
        tk.Button(row2, text="wl-paste Check", command=self.test_wl_paste,
                  bg='#ccccff').pack(side=tk.LEFT, padx=2)

        # Row 3: X11 tests
        row3 = tk.Frame(button_frame)
        row3.pack(pady=2)
        tk.Label(row3, text="X11 Tests:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(row3, text="xclip Image", command=self.test_xclip,
                  bg='#ffccff').pack(side=tk.LEFT, padx=2)
        tk.Button(row3, text="xclip Check", command=self.test_xclip_check,
                  bg='#ffccff').pack(side=tk.LEFT, padx=2)

        # Row 4: Utility tests
        row4 = tk.Frame(button_frame)
        row4.pack(pady=2)
        tk.Label(row4, text="Utilities:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(row4, text="Check Tools", command=self.check_available_tools,
                  bg='#ccffff').pack(side=tk.LEFT, padx=2)
        tk.Button(row4, text="Clear Results", command=self.clear_results,
                  bg='#f0f0f0').pack(side=tk.LEFT, padx=2)

    def load_test_image(self):
        try:
            if os.path.exists("./cosmos.jpg"):
                self.image = Image.open("./cosmos.jpg")
                self.log("✅ Loaded cosmos.jpg")
            else:
                # Create test image
                self.image = Image.new('RGB', (300, 200), 'navy')
                # Add some "stars"
                import random
                pixels = self.image.load()
                for _ in range(30):
                    x, y = random.randint(0, 299), random.randint(0, 199)
                    pixels[x, y] = (255, 255, 255)
                self.log("✅ Created test cosmos image")

            # Display on canvas
            self.image_tk = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(200, 150, image=self.image_tk)

        except Exception as e:
            self.log(f"❌ Failed to load image: {e}")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)

        self.text_log = self.text_log + f"[{timestamp}] {message}\n"
        # self.root.clipboard_clear()
        # self.root.clipboard_append(self.text_log)

        self.root.update()

    def clear_results(self):
        self.results_text.delete(1.0, tk.END)

    def select_all(self, event=None):
        """Select all text in results"""
        self.results_text.tag_add(tk.SEL, "1.0", tk.END)
        self.results_text.mark_set(tk.INSERT, "1.0")
        self.results_text.see(tk.INSERT)
        return 'break'

    def copy_selection(self, event=None):
        """Copy selected text to clipboard"""
        try:
            if self.results_text.tag_ranges(tk.SEL):
                selected_text = self.results_text.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.log("📋 Selected text copied to clipboard!")
            else:
                # If nothing selected, copy all
                all_text = self.results_text.get("1.0", tk.END)
                self.root.clipboard_clear()
                self.root.clipboard_append(all_text)
                self.log("📋 All logs copied to clipboard!")
        except Exception as e:
            print(f"Copy failed: {e}")
        return 'break'

    def setup_context_menu(self):
        """Add right-click context menu"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Select All (Ctrl+A)", command=self.select_all)
        self.context_menu.add_command(label="Copy (Ctrl+C)", command=self.copy_selection)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear Results", command=self.clear_results)

        def show_context_menu(event):
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

        self.results_text.bind("<Button-3>", show_context_menu)  # Right-click

    def test_your_code(self):
        """Test the user's current approach"""
        self.log("\n🔍 TESTING YOUR CURRENT CODE:")

        try:
            # Your code with fixes for obvious bugs
            canvas_image = self.image
            image_buffer = io.BytesIO()
            canvas_image.save(image_buffer, format="PNG")

            self.log("✅ Image saved to buffer")

            # Try to read it back (you forgot seek(0))
            image_buffer.seek(0)
            test_image = Image.open(image_buffer)
            self.log("✅ Image can be read from buffer")

            # Your clipboard line (will fail)
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(image_buffer, type="image/png", format="image/png")
                self.log("❌ This line should fail...")
            except Exception as e:
                self.log(f"❌ clipboard_append failed: {e}")

            # Try without format
            try:
                image_buffer.seek(0)
                self.root.clipboard_append(image_buffer)
                clipboard_content = self.root.clipboard_get()
                self.log(f"❌ Without format: '{clipboard_content}'")
            except Exception as e:
                self.log(f"❌ Also failed: {e}")

        except Exception as e:
            self.log(f"❌ Overall failure: {e}")

    def test_base64_text(self):
        """Test base64 approach"""
        self.log("\n🔍 TESTING BASE64 TEXT APPROACH:")

        try:
            import base64

            buffer = io.BytesIO()
            self.image.save(buffer, format='PNG')
            image_data = buffer.getvalue()
            base64_string = base64.b64encode(image_data).decode('ascii')

            self.root.clipboard_clear()
            self.root.clipboard_append(base64_string)
            self.root.update()

            # Verify
            clipboard_content = self.root.clipboard_get()
            if clipboard_content == base64_string:
                self.log(f"✅ Base64 copied successfully ({len(base64_string)} chars)")
                self.log(f"   Preview: {base64_string[:50]}...")
                self.log("⚠️  But this pastes as TEXT, not image!")
            else:
                self.log("❌ Base64 copy failed")

        except Exception as e:
            self.log(f"❌ Base64 test failed: {e}")

    def test_text_only(self):
        """Test simple text clipboard"""
        self.log("\n🔍 TESTING TEXT CLIPBOARD:")

        try:
            text = f"Image from canvas at {datetime.now().strftime('%H:%M:%S')}"

            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

            clipboard_content = self.root.clipboard_get()
            if clipboard_content == text:
                self.log(f"✅ Text copied: '{text}'")
            else:
                self.log(f"❌ Text mismatch: '{clipboard_content}'")

        except Exception as e:
            self.log(f"❌ Text clipboard failed: {e}")

    def test_wl_copy(self):
        """Test Wayland wl-copy for images"""
        self.log("\n🔍 TESTING WAYLAND wl-copy:")

        if not self.wayland_session:
            self.log("❌ Not in Wayland session")
            return

        try:
            # Check if wl-copy is available
            result = subprocess.run(['which', 'wl-copy'], capture_output=True)
            if result.returncode != 0:
                self.log("❌ wl-copy not found")
                self.log("   Install with: sudo apt install wl-clipboard")
                return

            # Save image to temp file
            temp_file = os.path.join(tempfile.gettempdir(), "test_image.png")
            self.image.save(temp_file)

            # Use wl-copy to copy image
            with open(temp_file, 'rb') as f:
                result = subprocess.run([
                    'wl-copy', '--type', 'image/png'
                ], stdin=f, capture_output=True)

            if result.returncode == 0:
                self.log("✅ wl-copy succeeded!")
                self.log("   Try pasting in an image editor now")
            else:
                self.log(f"❌ wl-copy failed: {result.stderr.decode()}")

            # Clean up
            os.unlink(temp_file)

        except Exception as e:
            self.log(f"❌ wl-copy test failed: {e}")

    def test_wl_paste(self):
        """Check what's in Wayland clipboard"""
        self.log("\n🔍 CHECKING WAYLAND CLIPBOARD:")

        try:
            # Check available types
            result = subprocess.run(['wl-paste', '--list-types'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                types = result.stdout.strip().split('\n')
                self.log(f"✅ Available clipboard types: {types}")

                # Check for image types
                image_types = [t for t in types if 'image' in t]
                if image_types:
                    self.log(f"✅ Image types found: {image_types}")
                else:
                    self.log("❌ No image types in clipboard")
            else:
                self.log(f"❌ wl-paste failed: {result.stderr}")

        except Exception as e:
            self.log(f"❌ wl-paste check failed: {e}")

    def test_xclip(self):
        """Test X11 xclip for images"""
        self.log("\n🔍 TESTING X11 xclip:")

        try:
            # Check if xclip is available
            result = subprocess.run(['which', 'xclip'], capture_output=True)
            if result.returncode != 0:
                self.log("❌ xclip not found")
                self.log("   Install with: sudo apt install xclip")
                return

            # Save image to temp file
            temp_file = os.path.join(tempfile.gettempdir(), "test_image.png")
            self.image.save(temp_file)

            # Use xclip to copy image
            result = subprocess.run([
                'xclip', '-selection', 'clipboard',
                '-t', 'image/png', '-i', temp_file
            ], capture_output=True)

            if result.returncode == 0:
                self.log("✅ xclip succeeded!")
                self.log("   Try pasting in an image editor now")
            else:
                self.log(f"❌ xclip failed: {result.stderr.decode()}")

            # Clean up
            os.unlink(temp_file)

        except Exception as e:
            self.log(f"❌ xclip test failed: {e}")

    def test_xclip_check(self):
        """Check what's in X11 clipboard"""
        self.log("\n🔍 CHECKING X11 CLIPBOARD:")

        try:
            # Check available targets
            result = subprocess.run([
                'xclip', '-selection', 'clipboard', '-o', '-t', 'TARGETS'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                targets = result.stdout.strip().split('\n')
                self.log(f"✅ Available clipboard targets: {targets}")

                # Check for image targets
                image_targets = [t for t in targets if 'image' in t]
                if image_targets:
                    self.log(f"✅ Image targets found: {image_targets}")
                else:
                    self.log("❌ No image targets in clipboard")
            else:
                self.log(f"❌ xclip targets check failed: {result.stderr}")

        except Exception as e:
            self.log(f"❌ xclip check failed: {e}")

    def check_available_tools(self):
        """Check what clipboard tools are available"""
        self.log("\n🔍 CHECKING AVAILABLE TOOLS:")

        tools = [
            ('wl-copy', 'Wayland clipboard'),
            ('wl-paste', 'Wayland paste'),
            ('xclip', 'X11 clipboard'),
            ('xsel', 'X11 selection'),
        ]

        for tool, description in tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True)
                if result.returncode == 0:
                    self.log(f"✅ {tool} - {description}")
                else:
                    self.log(f"❌ {tool} - not found")
            except:
                self.log(f"❌ {tool} - check failed")

        self.log(f"\n📊 Environment:")
        self.log(f"   WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'not set')}")
        self.log(f"   DISPLAY: {os.environ.get('DISPLAY', 'not set')}")
        self.log(f"   XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'not set')}")


def main():
    """Run the comprehensive clipboard test"""
    print("Starting comprehensive clipboard test...")
    print("This will test tkinter, Wayland, and X11 clipboard approaches")

    tester = ClipboardTester()
    tester.log("🚀 Clipboard tester ready!")
    tester.log("Click buttons to test different approaches")
    tester.log("Try 'Check Tools' first to see what's available")

    tester.root.mainloop()


if __name__ == "__main__":
    main()