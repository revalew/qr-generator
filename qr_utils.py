#!/usr/bin/env python3
"""
Enhanced QR Code Utilities
Additional tools for batch generation, scanning, and file operations
"""

import csv
import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer
)

# Import color masks if available
try:
    from qrcode.image.styles.colormasks import (
        SolidFillColorMask, SquareGradiantColorMask, RadialGradiantColorMask,
        HorizontalGradiantColorMask, VerticalGradiantColorMask
    )

    COLOR_MASKS_AVAILABLE = True
except ImportError:
    COLOR_MASKS_AVAILABLE = False

from PIL import Image
import sys
import urllib.request
import urllib.parse
import io


class QRBatchGenerator:
    """Enhanced batch generation with theme and color mask support"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for batch generation"""
        return {
            'size': 400,
            'border': 4,
            'error_correction': 'M',
            'format': 'PNG',
            'theme': 'classic',
            'color_mask': 'solid',
            'fg_color': '#000000',
            'bg_color': '#FFFFFF'
        }

    def load_config(self, config_file: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                self.config.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")

    def load_image_from_path_or_url(self, path_or_url: str) -> Image.Image:
        """Load image from local path or URL"""
        try:
            if path_or_url.startswith(('http://', 'https://')):
                with urllib.request.urlopen(path_or_url) as response:
                    image_data = response.read()
                    return Image.open(io.BytesIO(image_data))
            else:
                return Image.open(path_or_url)
        except Exception as e:
            raise Exception(f"Could not load image: {str(e)}")

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def get_enhanced_color_mask(self, config):
        """Enhanced color mask with proper RGB conversion and all types"""
        if not COLOR_MASKS_AVAILABLE:
            return None

        mask_type = config.get('color_mask', 'solid')
        fg_color = self.hex_to_rgb(config.get('fg_color', '#000000'))
        bg_color = self.hex_to_rgb(config.get('bg_color', '#FFFFFF'))

        # Create intermediate colors for gradients
        mid_color = tuple(
            int((fg + bg) / 2) for fg, bg in zip(fg_color, bg_color)
        )

        try:
            if mask_type == 'solid':
                return SolidFillColorMask(front_color=fg_color, back_color=bg_color)
            elif mask_type == 'radial':
                return RadialGradiantColorMask(
                    back_color=bg_color,
                    center_color=mid_color,
                    edge_color=fg_color
                )
            elif mask_type == 'square':
                return SquareGradiantColorMask(
                    back_color=bg_color,
                    center_color=mid_color,
                    edge_color=fg_color
                )
            elif mask_type == 'horizontal':
                return HorizontalGradiantColorMask(
                    back_color=bg_color,
                    left_color=mid_color,
                    right_color=fg_color
                )
            elif mask_type == 'vertical':
                return VerticalGradiantColorMask(
                    back_color=bg_color,
                    top_color=mid_color,
                    bottom_color=fg_color
                )
            elif mask_type == 'image':
                # ImageColorMask support
                image_path = config.get('mask_image_path', '')
                if image_path:
                    try:
                        from qrcode.image.styles.colormasks import ImageColorMask
                        mask_image = self.load_image_from_path_or_url(image_path)
                        return ImageColorMask(back_color=bg_color, color_mask_image=mask_image)
                    except ImportError:
                        print(f"Warning: ImageColorMask not available, using solid fill")
                        return SolidFillColorMask(front_color=fg_color, back_color=bg_color)
                    except Exception as e:
                        print(f"Warning: Failed to load mask image: {e}")
                        return SolidFillColorMask(front_color=fg_color, back_color=bg_color)
                else:
                    return SolidFillColorMask(front_color=fg_color, back_color=bg_color)
        except Exception as e:
            print(f"Warning: Color mask creation failed: {e}, using solid fill")
            return SolidFillColorMask(front_color=fg_color, back_color=bg_color)

        return None

    def add_image_overlay(self, qr_image, config):
        """Add image overlay support to batch generation"""
        if not config.get('use_image', False) or not config.get('image_path'):
            return qr_image

        try:
            # Load overlay image
            overlay = self.load_image_from_path_or_url(config['image_path'])
            qr_size = qr_image.size[0]
            overlay_size = int(qr_size * config.get('image_size', 20) / 100)

            # Resize overlay maintaining aspect ratio
            overlay.thumbnail((overlay_size, overlay_size), Image.Resampling.LANCZOS)

            # Create background if specified
            bg_type = config.get('image_bg', 'match')
            if bg_type in ['match', 'custom']:
                padding = config.get('image_padding', 10)
                bg_size = overlay.size[0] + 2 * padding

                if bg_type == 'match':
                    bg_color = config.get('bg_color', '#FFFFFF')
                else:
                    bg_color = config.get('image_bg_color', '#FFFFFF')

                background = Image.new('RGB', (bg_size, bg_size), bg_color)

                # Handle transparency in overlay
                if overlay.mode in ('RGBA', 'LA') or (overlay.mode == 'P' and 'transparency' in overlay.info):
                    background.paste(overlay, (padding, padding), overlay)
                else:
                    background.paste(overlay, (padding, padding))

                overlay = background

            # Convert to RGBA for transparency support
            if overlay.mode != 'RGBA':
                overlay = overlay.convert('RGBA')

            qr_image = qr_image.convert('RGBA')
            overlay_pos = ((qr_size - overlay.size[0]) // 2, (qr_size - overlay.size[1]) // 2)
            qr_image.paste(overlay, overlay_pos, overlay)

            return qr_image.convert('RGB')

        except Exception as e:
            print(f"Warning: Failed to add image overlay: {e}")
            return qr_image

    def generate_from_csv(self, csv_file: str, output_dir: str = "./exports/batch_output") -> None:
        """Enhanced CSV generation with full feature support"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print(f"🏭 Starting batch generation from CSV: {csv_file}")
        print(f"📁 Output directory: {output_dir}")

        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                total_rows = 0
                success_count = 0

                for i, row in enumerate(reader):
                    total_rows += 1
                    try:
                        # Get content and filename from row
                        content = row.get('content', row.get('text', ''))
                        filename = row.get('filename', f'qr_{i + 1:03d}')

                        if not content:
                            print(f"⚠️  Row {i + 1}: Empty content, skipping")
                            continue

                        # Build configuration from row with defaults
                        row_config = self.config.copy()

                        # Map all possible CSV columns to config
                        config_mapping = {
                            'size': ('size', int, 400),
                            'theme': ('theme', str, 'classic'),
                            'color_mask': ('color_mask', str, 'solid'),
                            'fg_color': ('fg_color', str, '#000000'),
                            'bg_color': ('bg_color', str, '#FFFFFF'),
                            'error_correction': ('error_correction', str, 'M'),
                            'border': ('border', int, 4),
                            'format': ('format', str, 'PNG'),
                            'use_image': ('use_image', bool, False),
                            'image_path': ('image_path', str, ''),
                            'image_size': ('image_size', int, 20),
                            'image_bg': ('image_bg', str, 'match'),
                            'image_bg_color': ('image_bg_color', str, '#FFFFFF'),
                            'image_padding': ('image_padding', int, 10),
                            'mask_image_path': ('mask_image_path', str, '')
                        }

                        for csv_key, (config_key, converter, default) in config_mapping.items():
                            if csv_key in row and row[csv_key]:
                                try:
                                    if converter == bool:
                                        value = row[csv_key].lower() in ['true', '1', 'yes', 'on']
                                    else:
                                        value = converter(row[csv_key])
                                    row_config[config_key] = value
                                except (ValueError, TypeError):
                                    print(f"⚠️  Row {i + 1}: Invalid {csv_key} value '{row[csv_key]}', using default")
                                    row_config[config_key] = default

                        # Generate QR code
                        qr_image = self.generate_qr_code(content, row_config)

                        # Save image
                        output_path = Path(output_dir) / f"{filename}.{row_config['format'].lower()}"
                        qr_image.save(output_path)

                        print(f"✅ Row {i + 1}: Generated {output_path.name}")
                        success_count += 1

                    except Exception as e:
                        print(f"❌ Row {i + 1}: Error - {e}")

                print(f"\n📊 Batch Generation Complete:")
                print(f"   Total rows: {total_rows}")
                print(f"   Successful: {success_count}")
                print(f"   Failed: {total_rows - success_count}")
                print(f"   Success rate: {(success_count / total_rows) * 100:.1f}%" if total_rows > 0 else "   No rows processed")

        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")

    def generate_from_json(self, json_file: str, output_dir: str = "./exports/batch_output") -> None:
        """Enhanced JSON generation with full feature support"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print(f"🏭 Starting batch generation from JSON: {json_file}")
        print(f"📁 Output directory: {output_dir}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list of objects and single object
            if isinstance(data, dict):
                data = [data]

            total_items = len(data)
            success_count = 0

            for i, item in enumerate(data):
                try:
                    content = item.get('content', item.get('text', ''))
                    filename = item.get('filename', f'qr_{i + 1:03d}')

                    if not content:
                        print(f"⚠️  Item {i + 1}: Empty content, skipping")
                        continue

                    # Override config with item-specific settings
                    item_config = self.config.copy()
                    item_config.update(item)  # JSON can contain any config keys

                    # Generate QR code
                    qr_image = self.generate_qr_code(content, item_config)

                    # Save image
                    output_path = Path(output_dir) / f"{filename}.{item_config.get('format', 'PNG').lower()}"
                    qr_image.save(output_path)

                    print(f"✅ Item {i + 1}: Generated {output_path.name}")
                    success_count += 1

                except Exception as e:
                    print(f"❌ Item {i + 1}: Error - {e}")

            print(f"\n📊 Batch Generation Complete:")
            print(f"   Total items: {total_items}")
            print(f"   Successful: {success_count}")
            print(f"   Failed: {total_items - success_count}")
            print(f"   Success rate: {(success_count / total_items) * 100:.1f}%" if total_items > 0 else "   No items processed")

        except Exception as e:
            print(f"❌ Error reading JSON file: {e}")

    def generate_qr_code(self, content: str, config: Dict[str, Any] = None) -> Image.Image:
        """Generate a single QR code with enhanced configuration support"""
        if config is None:
            config = self.config

        # Error correction mapping
        error_levels = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }

        qr = qrcode.QRCode(
            version=1,
            error_correction=error_levels.get(config.get('error_correction', 'M'), qrcode.constants.ERROR_CORRECT_M),
            box_size=10,
            border=config.get('border', 4),
        )

        qr.add_data(content)
        qr.make(fit=True)

        # Get colors
        fg_color = config.get('fg_color', '#000000')
        bg_color = config.get('bg_color', '#FFFFFF')

        # Apply theme and color mask
        theme = config.get('theme', 'classic')
        color_mask = self.get_enhanced_color_mask(config)

        # Generate image based on theme with proper error handling
        try:
            if theme == 'rounded':
                qr_image = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=RoundedModuleDrawer(),
                    color_mask=color_mask,
                    fill_color=fg_color,
                    back_color=bg_color
                )
            elif theme == 'circular':
                qr_image = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=CircleModuleDrawer(),
                    color_mask=color_mask,
                    fill_color=fg_color,
                    back_color=bg_color
                )
            elif theme == 'gapped':
                try:
                    from decimal import Decimal
                    qr_image = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=SquareModuleDrawer(size_ratio=Decimal(0.8)),
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color
                    )
                except Exception:
                    # Fallback if SquareModuleDrawer doesn't support size_ratio
                    qr_image = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=SquareModuleDrawer(),
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color
                    )
            elif theme in ['vertical_bars', 'horizontal_bars']:
                try:
                    # Try to import advanced drawers
                    if theme == 'vertical_bars':
                        from qrcode.image.styles.moduledrawers import VerticalBarsDrawer
                        drawer = VerticalBarsDrawer()
                    else:
                        from qrcode.image.styles.moduledrawers import HorizontalBarsDrawer
                        drawer = HorizontalBarsDrawer()

                    qr_image = qr.make_image(
                        image_factory=StyledPilImage,
                        module_drawer=drawer,
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color
                    )
                except ImportError:
                    print(f"Warning: {theme} not available, using classic theme")
                    if color_mask:
                        qr_image = qr.make_image(
                            image_factory=StyledPilImage,
                            color_mask=color_mask,
                            fill_color=fg_color,
                            back_color=bg_color
                        )
                    else:
                        qr_image = qr.make_image(fill_color=fg_color, back_color=bg_color)
            else:  # classic or unknown
                if color_mask:
                    qr_image = qr.make_image(
                        image_factory=StyledPilImage,
                        color_mask=color_mask,
                        fill_color=fg_color,
                        back_color=bg_color
                    )
                else:
                    qr_image = qr.make_image(fill_color=fg_color, back_color=bg_color)

        except Exception as e:
            print(f"Warning: Theme '{theme}' failed ({e}), using basic generation")
            qr_image = qr.make_image(fill_color=fg_color, back_color=bg_color)

        # Resize to target size
        target_size = config.get('size', 400)
        qr_image = qr_image.resize((target_size, target_size), Image.Resampling.LANCZOS)

        # Add image overlay if configured
        qr_image = self.add_image_overlay(qr_image, config)

        return qr_image


class QRScanner:
    """Enhanced QR code scanning with better error handling"""

    def __init__(self):
        self.opencv_available = self._check_opencv()
        self.pyzbar_available = self._check_pyzbar()

    def _check_opencv(self) -> bool:
        """Check if OpenCV is available"""
        try:
            import cv2
            return True
        except ImportError:
            return False

    def _check_pyzbar(self) -> bool:
        """Check if pyzbar is available"""
        try:
            import pyzbar
            return True
        except ImportError:
            return False

    def scan_from_file(self, image_path: str) -> List[Dict[str, Any]]:
        """Scan QR codes from image file with detailed results"""
        if not self.opencv_available or not self.pyzbar_available:
            print("Error: OpenCV and pyzbar are required for QR scanning")
            print("Install with: pip install opencv-python-headless pyzbar")
            return []

        try:
            import cv2
            from pyzbar import pyzbar

            # Read image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Could not read image {image_path}")
                return []

            # Decode QR codes
            decoded_objects = pyzbar.decode(image)

            results = []
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                result = {
                    'content': data,
                    'type': obj.type,
                    'quality': 'good' if len(data) > 0 else 'poor',
                    'position': {
                        'x': obj.rect.left,
                        'y': obj.rect.top,
                        'width': obj.rect.width,
                        'height': obj.rect.height
                    }
                }
                results.append(result)
                print(f"Found QR code: {data}")

            return results

        except Exception as e:
            print(f"Error scanning QR code: {e}")
            return []

    def analyze_content_type(self, content: str) -> Dict[str, Any]:
        """Analyze QR content and determine type"""
        analysis = {
            'content': content,
            'type': 'text',
            'details': {}
        }

        if content.startswith(('http://', 'https://')):
            analysis['type'] = 'url'
            try:
                from urllib.parse import urlparse
                parsed = urlparse(content)
                analysis['details'] = {
                    'domain': parsed.netloc,
                    'path': parsed.path,
                    'secure': content.startswith('https://')
                }
            except:
                pass
        elif content.startswith('mailto:'):
            analysis['type'] = 'email'
            email_part = content.replace('mailto:', '').split('?')[0]
            analysis['details'] = {'email': email_part}
        elif content.startswith('WIFI:'):
            analysis['type'] = 'wifi'
            wifi_parts = content.replace('WIFI:', '').split(';')
            details = {}
            for part in wifi_parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if key == 'S':
                        details['ssid'] = value
                    elif key == 'T':
                        details['security'] = value
                    elif key == 'P':
                        details['password'] = value
                    elif key == 'H':
                        details['hidden'] = value.lower() == 'true'
            analysis['details'] = details
        elif content.startswith('BEGIN:VCARD'):
            analysis['type'] = 'vcard'
            vcard_lines = content.split('\n')
            details = {}
            for line in vcard_lines:
                if line.startswith('FN:'):
                    details['name'] = line.replace('FN:', '')
                elif line.startswith('ORG:'):
                    details['organization'] = line.replace('ORG:', '')
                elif line.startswith('TEL:'):
                    details['phone'] = line.replace('TEL:', '')
                elif line.startswith('EMAIL:'):
                    details['email'] = line.replace('EMAIL:', '')
            analysis['details'] = details
        elif content.startswith('tel:'):
            analysis['type'] = 'phone'
            analysis['details'] = {'number': content.replace('tel:', '')}
        elif content.startswith('sms:'):
            analysis['type'] = 'sms'
            parts = content.replace('sms:', '').split('?')
            analysis['details'] = {'number': parts[0]}
            if len(parts) > 1 and 'body=' in parts[1]:
                analysis['details']['message'] = parts[1].split('body=')[1]

        return analysis


def create_sample_csv_enhanced():
    """Create an enhanced sample CSV file with all features"""
    sample_data = [
        {
            'content': 'https://www.python.org',
            'filename': 'python_website',
            'theme': 'rounded',
            'color_mask': 'radial',
            'fg_color': '#3776ab',
            'bg_color': '#ffffff',
            'size': 400,
            'error_correction': 'M',
            'use_image': 'true',
            'image_path': 'config/LogoPlaceHolders192.png',
            'image_size': 25,
            'image_bg': 'custom',
            'image_bg_color': '#f8f9fa',
            'image_padding': 15
        },
        {
            'content': 'WIFI:T:WPA;S:CoffeeShop;P:password123;H:false;',
            'filename': 'wifi_coffee',
            'theme': 'circular',
            'color_mask': 'horizontal',
            'fg_color': '#8B4513',
            'bg_color': '#F5DEB3',
            'size': 350,
            'border': 3
        },
        {
            'content': 'mailto:contact@company.com?subject=Hello&body=Thanks for visiting!',
            'filename': 'contact_email',
            'theme': 'classic',
            'color_mask': 'solid',
            'fg_color': '#1f4e79',
            'bg_color': '#ffffff',
            'size': 300
        },
        {
            'content': 'BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nORG:Tech Company\nTEL:+1-555-123-4567\nEMAIL:john@company.com\nEND:VCARD',
            'filename': 'business_card',
            'theme': 'gapped',
            'color_mask': 'square',
            'fg_color': '#2c3e50',
            'bg_color': '#ecf0f1',
            'error_correction': 'Q'
        }
    ]

    fieldnames = [
        'content', 'filename', 'theme', 'color_mask', 'fg_color', 'bg_color',
        'size', 'error_correction', 'border', 'use_image', 'image_path',
        'image_size', 'image_bg', 'image_bg_color', 'image_padding'
    ]

    with open('enhanced_batch.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)

    print("✅ Created enhanced_batch.csv with full feature support")
    print("📝 Includes: themes, color masks, image overlays, error correction")
    print("💡 Edit the CSV to customize your batch generation")


def create_sample_json_enhanced():
    """Create an enhanced sample JSON file"""
    sample_data = [
        {
            'content': 'https://github.com',
            'filename': 'github_qr',
            'theme': 'rounded',
            'color_mask': 'vertical',
            'fg_color': '#24292e',
            'bg_color': '#ffffff',
            'size': 500,
            'error_correction': 'M'
        },
        {
            'content': 'tel:+1-800-555-0199',
            'filename': 'phone_support',
            'theme': 'circular',
            'color_mask': 'radial',
            'fg_color': '#0066cc',
            'bg_color': '#f0f8ff'
        },
        {
            'content': 'sms:+1-555-123-4567?body=Thanks for your service!',
            'filename': 'sms_thanks',
            'theme': 'classic',
            'color_mask': 'horizontal',
            'fg_color': '#228B22',
            'bg_color': '#F0FFF0'
        }
    ]

    with open('enhanced_batch.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)

    print("✓ Created enhanced_batch.json with advanced styling options")


def create_config_template():
    """Create a configuration template file"""
    config_template = {
        "description": "QR Code Generator Configuration Template",
        "version": "2.0",

        "defaults": {
            "size": 400,
            "border": 4,
            "error_correction": "M",
            "format": "PNG",
            "theme": "classic",
            "color_mask": "solid",
            "fg_color": "#000000",
            "bg_color": "#FFFFFF"
        },

        "themes": {
            "classic": "Traditional square modules",
            "rounded": "Rounded corner modules",
            "circular": "Circular modules",
            "gapped": "Squares with gaps between them"
        },

        "color_masks": {
            "solid": "Single solid color",
            "radial": "Radial gradient from center",
            "square": "Square gradient pattern",
            "horizontal": "Horizontal gradient",
            "vertical": "Vertical gradient"
        },

        "error_correction_levels": {
            "L": "~7% error recovery",
            "M": "~15% error recovery (recommended)",
            "Q": "~25% error recovery",
            "H": "~30% error recovery"
        },

        "example_batch_entry": {
            "content": "https://example.com",
            "filename": "example_qr",
            "theme": "rounded",
            "color_mask": "radial",
            "fg_color": "#1a365d",
            "bg_color": "#ffffff",
            "size": 400,
            "error_correction": "M"
        }
    }

    with open('config_template.json', 'w', encoding='utf-8') as f:
        json.dump(config_template, f, indent=2)

    print("✓ Created config_template.json with documentation")


def main():
    """Enhanced command line interface"""
    parser = argparse.ArgumentParser(description='Enhanced QR Code Utilities')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Batch generation commands
    batch_parser = subparsers.add_parser('batch', help='Batch generate QR codes')
    batch_parser.add_argument('input_file', help='Input CSV or JSON file')
    batch_parser.add_argument('--output', '-o', default='./exports/batch_output', help='Output directory')
    batch_parser.add_argument('--config', '-c', help='Configuration file')

    # Enhanced scanning commands
    scan_parser = subparsers.add_parser('scan', help='Scan and analyze QR codes')
    scan_parser.add_argument('--file', '-f', required=True, help='Image file to scan')
    scan_parser.add_argument('--analyze', '-a', action='store_true', help='Analyze content type')
    scan_parser.add_argument('--output', '-o', help='Save analysis to file')

    # Sample generation commands
    sample_parser = subparsers.add_parser('samples', help='Create sample and template files')
    sample_parser.add_argument('--csv', action='store_true', help='Create enhanced sample CSV')
    sample_parser.add_argument('--json', action='store_true', help='Create enhanced sample JSON')
    sample_parser.add_argument('--config', action='store_true', help='Create configuration template')
    sample_parser.add_argument('--all', action='store_true', help='Create all sample files')

    args = parser.parse_args()

    if args.command == 'batch':
        generator = QRBatchGenerator()

        if args.config:
            generator.load_config(args.config)

        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file {args.input_file} not found")
            return

        print(f"Processing {args.input_file}...")
        if input_path.suffix.lower() == '.csv':
            generator.generate_from_csv(args.input_file, args.output)
        elif input_path.suffix.lower() == '.json':
            generator.generate_from_json(args.input_file, args.output)
        else:
            print("Error: Input file must be CSV or JSON")

        print(f"Batch generation complete! Check {args.output} directory.")

    elif args.command == 'scan':
        scanner = QRScanner()

        if not scanner.opencv_available or not scanner.pyzbar_available:
            print("Error: Scanning requires opencv-python-headless and pyzbar")
            print("Install with: pip install opencv-python-headless pyzbar")
            return

        results = scanner.scan_from_file(args.file)

        if not results:
            print("No QR codes found in image")
            return

        print(f"\nFound {len(results)} QR code(s):")
        print("=" * 50)

        for i, result in enumerate(results, 1):
            print(f"\nQR Code {i}:")
            print(f"Content: {result['content']}")
            print(f"Type: {result['type']}")
            print(f"Position: {result['position']}")

            if args.analyze:
                analysis = scanner.analyze_content_type(result['content'])
                print(f"Content Type: {analysis['type']}")
                if analysis['details']:
                    print(f"Details: {analysis['details']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nAnalysis saved to {args.output}")

    elif args.command == 'samples':
        if args.all or args.csv:
            create_sample_csv_enhanced()
        if args.all or args.json:
            create_sample_json_enhanced()
        if args.all or args.config:
            create_config_template()

        if not any([args.csv, args.json, args.config, args.all]):
            # Default: create all
            create_sample_csv_enhanced()
            create_sample_json_enhanced()
            create_config_template()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()