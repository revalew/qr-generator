# Enhanced QR Code Generator

A comprehensive GUI application for creating styled QR codes with advanced features including batch generation, scanning, and extensive customization options.

## Features

### **Visual Styling**

- **Themes**: Classic squares, rounded corners, circles, gapped squares, vertical/horizontal bars

- **Color Effects**: Solid colors, radial gradients, square gradients, horizontal/vertical gradients, image-based color masks

- **Custom Colors**: Full hex color support with color picker

- **Size Control**: 100-1000px with precise border control

- **Error Correction**: L, M, Q, H levels for different reliability needs

### **Content Types**

- **General Text**: Any plain text content

- **URLs**: Websites with automatic protocol detection

- **WiFi Credentials**: SSID, password, security type, hidden networks

- **Business Cards**: vCard format with name, organization, phone, email, website

- **Email**: Pre-filled mailto links with subject and body

- **Phone Numbers**: Direct dial links

- **SMS**: Pre-filled text messages

### **Image Overlays**

- **Logo Integration**: Add center logos or images

- **Flexible Sizing**: 5-50% of QR code size

- **Background Options**: Match QR, custom color, or transparent

- **Padding Control**: Precise spacing around images

- **URL Support**: Load images from local files or web URLs

### **Advanced Features**

- **Configuration Management**: Save and load custom presets

- **Batch Generation**: Create multiple QR codes from CSV/JSON files with full styling support

- **QR Scanning**: Decode QR codes from image files (optional)

- **Universal Clipboard**: Works across Windows, macOS, Linux with multiple fallback methods

- **Export Formats**: PNG, JPEG, BMP

## Quick Start

### **Automatic Installation (Recommended)**

```bash
# Clone or download the project
git clone <repository-url>
cd qr-generator

# Run the complete setup - handles everything automatically
python setup.py
```

### **Manual Installation**

```bash
# Create virtual environment
python -m venv qr_env

# Activate environment
# Windows:
qr_env\Scripts\activate
# Linux/macOS:
source qr_env/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### **Run the Application**

```bash
# After installation, run:
python qr_generator.py
```

## Usage

### **GUI Application**

```bash
python qr_generator.py
```

1. Choose a content type (URL, WiFi, Business Card, etc.)

2. Enter your content

3. Customize style, colors, and effects

4. Add image overlay if desired

5. Generate and export your QR code

### **Command Line Utilities**

```bash
# Batch generation from CSV/JSON
python qr_utils.py batch examples/sample_batch.csv

# Scan QR codes from images (requires opencv + pyzbar)
python qr_utils.py scan --file qr_image.png --analyze

# Create sample files
python qr_utils.py samples --all
```

### **Batch Generation**

Create CSV files with these columns:

- `content`: The QR code content *(required)*

- `filename`: Output filename *(optional)*

- `theme`: rounded, circular, classic, gapped, vertical_bars, horizontal_bars *(optional)*

- `color_mask`: solid, radial, square, horizontal, vertical, image *(optional)*

- `fg_color`: Foreground color in hex (e.g., #000000) *(optional)*

- `bg_color`: Background color in hex (e.g., #FFFFFF) *(optional)*

- `size`: Output size in pixels *(optional)*

- `error_correction`: L, M, Q, H *(optional)*

**Example CSV:**

```csv
content,filename,theme,color_mask,fg_color,bg_color,size
https://example.com,website_qr,rounded,radial,#1a365d,#ffffff,400
WIFI:T:WPA;S:MyWiFi;P:password;H:false;,wifi_qr,circular,horizontal,#8B4513,#F5DEB3,350
mailto:contact@company.com,email_qr,classic,solid,#0066cc,#f0f8ff,300
```

## Project Structure

```
qr-generator/
├── qr_generator.py                 # Main GUI application
├── qr_utils.py                     # Command line utilities
├── setup.py                        # Automatic installer
├── requirements.txt                # Dependencies
├── config/                         # User configurations
│   ├── user_presets/               # Saved presets
│   └── *.png, *.jpg                # Image assets
├── examples/                       # Sample files
│   ├── sample_batch.csv            # Batch generation example
│   ├── sample_config.json          # Configuration example
│   └── example_config_files.json   # Preset library
└── exports/                        # Generated QR codes
    └── batch_output/               # Batch generation output
```

## **Styling Guide**

### **Theme Selection**

- **Classic**: Traditional squares, maximum compatibility

- **Rounded**: Modern look with rounded corners

- **Circular**: Artistic circles, may have scanner limitations

- **Gapped**: Unique spaced squares for branding

- **Vertical/Horizontal Bars**: Linear patterns for artistic effect

### **Color Combinations**

- **Professional**: Navy (#1a365d) on white (#ffffff)

- **Modern**: Dark gray (#2d3748) on light gray (#edf2f7)

- **Vibrant**: Purple (#7c3aed) on lavender (#f5f3ff)

- **Nature**: Green (#059669) on mint (#ecfdf5)

- **Ocean**: Blue (#0066cc) on light blue (#f0f8ff)

### **Error Correction Levels**

- **L (~7%)**: Perfect printing conditions

- **M (~15%)**: General purpose (recommended)

- **Q (~25%)**: Image overlays or damage expected

- **H (~30%)**: Maximum reliability, emergency use

### **Size Recommendations**

- **Business Cards**: 300-400px

- **Posters**: 500-800px

- **Digital Displays**: 400-600px

- **Print Materials**: 600-1000px

- **Mobile Screens**: 300-500px

## **Dependencies & Installation**

### **Core Dependencies (Required)**

- Python 3.7+

- qrcode[pil] - QR code generation

- Pillow - Image processing

### **Optional Dependencies**

- **pyperclip** - Enhanced clipboard support

- **opencv-python-headless** - QR code scanning

- **pyzbar** - QR code decoding

### **Linux System Dependencies**

The setup script will automatically detect and offer to install:

- **python3-tk** - GUI framework (required)

- **xclip/xsel** - Clipboard support

- **libzbar0** - QR scanning library

### **Troubleshooting**

**Clipboard not working:**

- The app includes multiple fallback methods

- Works on all platforms without extra setup

**QR scanning not available:**

- Run: `pip install opencv-python-headless pyzbar`

- Linux: Setup script will offer to install `libzbar0`

**GUI not showing on Linux:**

- Setup script will offer to install `python3-tk`

**Package installation fails:**

- Try Python 3.11 or 3.12 instead of 3.13

- Some packages may not be available for the latest Python

## **Examples**

### **Business Card QR Code**

```
Content Type: Business Card (vCard)
Theme: Rounded Corners
Colors: #1a365d on #ffffff
Image Overlay: company_logo.png (20% size)
Error Correction: M
```

### **WiFi Sharing**

```
Content Type: WiFi Credentials
Network: CoffeeShop_Guest
Password: welcome123
Theme: Circular
Colors: #8B4513 on #F5DEB3
Effect: Radial Gradient
```

### **Website Promotion**

```
Content Type: URL
URL: https://mycompany.com
Theme: Gapped Squares
Colors: #2d3748 on #edf2f7
Effect: Square Gradient
Size: 500px
```

## **Support**

- Check the `examples/` folder for sample configurations
- Run `python qr_utils.py --help` for command line help
- The setup script handles most installation issues automatically