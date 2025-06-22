# Enhanced QR Code Generator

<br/><br/>

A comprehensive GUI application for creating styled QR codes with advanced features including batch generation, scanning, and extensive customization options.

<br/><br/>

## Features

<br/>

#### **Visual Styling**

- **Themes**: Classic squares, rounded corners, circles, gapped squares, vertical/horizontal bars

- **Color Effects**: Solid colors, radial gradients, square gradients, horizontal/vertical gradients, image-based color masks

- **Custom Colors**: Full hex color support with color picker

- **Size Control**: 100-1000px with precise border control

- **Error Correction**: L, M, Q, H levels for different reliability needs

<br/>

#### **Content Types**

- **General Text**: Any plain text content

- **URLs**: Websites with automatic protocol detection

- **WiFi Credentials**: SSID, password, security type, hidden networks

- **Business Cards**: vCard format with name, organization, phone, email, website

- **Email**: Pre-filled mailto links with subject and body

- **Phone Numbers**: Direct dial links

- **SMS**: Pre-filled text messages

<br/>

#### **Image Overlays**

- **Logo Integration**: Add center logos or images

- **Flexible Sizing**: 5-50% of QR code size

- **Background Options**: Match QR, custom color, or transparent

- **Padding Control**: Precise spacing around images

- **URL Support**: Load images from local files or web URLs

<br/>

#### **Advanced Features**

- **Configuration Management**: Save and load custom presets

- **Batch Generation**: Create multiple QR codes from CSV/JSON files with full styling support

- **QR Scanning**: Decode QR codes from image files (optional)

- **Universal Clipboard**: Works across Windows, macOS, Linux with multiple fallback methods

- **Export Formats**: PNG, JPEG, BMP

<br/><br/>

## Quick Start for GitHub Pages

<br/>

The web-based version of the application is available at [https://revalew.github.io/qr-generator/](https://revalew.github.io/qr-generator/). It provides a user-friendly interface for generating QR codes with various styling options, without the necessity for a local installation. This version was created using [`PyScript`](https://pyscript.net) and GitHub Pages.

<br/><br/>

## Quick Start for Local Installation

<br/>

#### **Automatic Installation (Recommended)**

<br/>

```bash
# Clone or download the project
git clone https://github.com/revalew/qr-generator.git
```

<br/>

```bash
cd qr-generator
```

<br/>

```bash
# Run the complete setup - handles everything automatically
python setup.py
```

<br/>

#### **Manual Installation**

<br/>

```bash
# Create virtual environment
python -m venv qr_env
```

<br/>

```bash
# Activate environment
# Windows:
qr_env\Scripts\activate
```

<br/>

```bash
# Linux/macOS:
source qr_env/bin/activate
```

<br/>

```bash
# Install all dependencies
pip install -r requirements.txt
```

<br/>

#### **Run the Application**

<br/>

```bash
# Activate environment
# Windows:
qr_env\Scripts\activate
```

<br/>

```bash
# Linux/macOS:
source qr_env/bin/activate
```

<br/>

```bash
# After installation, run:
python qr_generator.py
```

<br/><br/>

## Usage

<br/>

#### **GUI Application**

<br/>

```bash
# Activate environment
# Windows:
qr_env\Scripts\activate
```

<br/>

```bash
# Linux/macOS:
source qr_env/bin/activate
```

<br/>

```bash
python qr_generator.py
```

<br/>

1. Choose a content type (URL, WiFi, Business Card, etc.)

2. Enter your content

3. Customize style, colors, and effects

4. Add image overlay if desired

5. Generate and export your QR code

<br/>

#### **Command Line Utilities**

<br/>

```bash
# Batch generation from CSV/JSON
python qr_utils.py batch examples/sample_batch.csv
```

<br/>

```bash
# Scan QR codes from images (requires opencv + pyzbar)
python qr_utils.py scan --file qr_image.png --analyze
```

<br/>

```bash
# Create sample files
python qr_utils.py samples --all
```

<br/>

#### **Batch Generation**

<br/>

Create CSV files with these columns:

- `content`: The QR code content _(required)_

- `filename`: Output filename _(optional)_

- `theme`: rounded, circular, classic, gapped, vertical*bars, horizontal_bars *(optional)\_

- `color_mask`: solid, radial, square, horizontal, vertical, image _(optional)_

- `fg_color`: Foreground color in hex (e.g., #000000) _(optional)_

- `bg_color`: Background color in hex (e.g., #FFFFFF) _(optional)_

- `size`: Output size in pixels _(optional)_

- `error_correction`: L, M, Q, H _(optional)_

**Example CSV:**

<br/>

```csv
content,filename,theme,color_mask,fg_color,bg_color,size
https://example.com,website_qr,rounded,radial,#1a365d,#ffffff,400
WIFI:T:WPA;S:MyWiFi;P:password;H:false;,wifi_qr,circular,horizontal,#8B4513,#F5DEB3,350
mailto:contact@company.com,email_qr,classic,solid,#0066cc,#f0f8ff,300
```

<br/><br/>

## Project Structure

<br/>

```
qr-generator/
├── index.html                      # PyScript page
├── qr_generator.py                 # Main GUI application
├── qr_utils.py                     # Command line utilities
├── requirements.txt                # Dependencies
├── setup.py                        # Automatic installer
├── assets/                         # Assets (CSS, images)
│   ├── css/                        # CSS files for PyScript page
│   ├── images/                     # Example images for overlay and masks
│   ├── pyscript/                   # PyScript core (compiled dist)
│   ├── pyscript_config/            # PyScript configuration and code
│   ├── pyscript_example/           # PyScript example
│   ├── dist.zip                    # Archive of PyScript compilation
│   ├── pyscript-2025.5.1.zip       # Archive of PyScript repo
│   └── README.md                   # Local compilation instructions (for PyScript)
├── config/                         # User configurations
│   └── user_presets/               # Saved presets
├── examples/                       # Sample files
│   ├── sample_batch.csv            # Batch generation example
│   ├── sample_config.json          # Configuration example
│   └── example_config_files.json   # Preset library
└── exports/                        # Generated QR codes
    └── batch_output/               # Batch generation output
```

<br/><br/>

## **Styling Guide**

<br/>

#### **Theme Selection**

- **Classic**: Traditional squares, maximum compatibility

- **Rounded**: Modern look with rounded corners

- **Circular**: Artistic circles, may have scanner limitations

- **Gapped**: Unique spaced squares for branding

- **Vertical/Horizontal Bars**: Linear patterns for artistic effect

<br/>

#### **Color Combinations**

- **Professional**: Navy (#1a365d) on white (#ffffff)

- **Modern**: Dark gray (#2d3748) on light gray (#edf2f7)

- **Vibrant**: Purple (#7c3aed) on lavender (#f5f3ff)

- **Nature**: Green (#059669) on mint (#ecfdf5)

- **Ocean**: Blue (#0066cc) on light blue (#f0f8ff)

<br/>

#### **Error Correction Levels**

- **L (~7%)**: Perfect printing conditions

- **M (~15%)**: General purpose (recommended)

- **Q (~25%)**: Image overlays or damage expected

- **H (~30%)**: Maximum reliability, emergency use

<br/>

#### **Size Recommendations**

- **Business Cards**: 300-400px

- **Posters**: 500-800px

- **Digital Displays**: 400-600px

- **Print Materials**: 600-1000px

- **Mobile Screens**: 300-500px

<br/><br/>

## **Dependencies & Installation**

<br/>

#### **Core Dependencies (Required)**

<br/>

- Python 3.7+

- qrcode[pil] - QR code generation

- Pillow - Image processing

<br/>

#### **Optional Dependencies**

- **pyperclip** - Enhanced clipboard support

- **opencv-python-headless** - QR code scanning

- **pyzbar** - QR code decoding

<br/>

#### **Linux System Dependencies**

<br/>

The setup script will automatically detect and offer to install:

- **python3-tk** - GUI framework (required)

- **xclip/xsel** - Clipboard support

- **libzbar0** - QR scanning library

<br/>

#### **Troubleshooting**

<br/>

**Clipboard not working:**

- The app includes multiple fallback methods

- Works on all platforms without extra setup

<br/>

**QR scanning not available:**

- Run: `pip install opencv-python-headless pyzbar`

- Linux: Setup script will offer to install `libzbar0`

<br/>

**GUI not showing on Linux:**

- Setup script will offer to install `python3-tk`

<br/>

**Package installation fails:**

- Try Python 3.11 or 3.12 instead of 3.13

- Some packages may not be available for the latest Python

<br/><br/>

## **Examples**

<br/>

#### **Business Card QR Code**

<br/>

```
Content Type: Business Card (vCard)
Theme: Rounded Corners
Colors: #1a365d on #ffffff
Image Overlay: company_logo.png (20% size)
Error Correction: M
```

<br/>

#### **WiFi Sharing**

<br/>

```
Content Type: WiFi Credentials
Network: CoffeeShop_Guest
Password: welcome123
Theme: Circular
Colors: #8B4513 on #F5DEB3
Effect: Radial Gradient
```

<br/>

#### **Website Promotion**

<br/>

```
Content Type: URL
URL: https://mycompany.com
Theme: Gapped Squares
Colors: #2d3748 on #edf2f7
Effect: Square Gradient
Size: 500px
```

<br/><br/>

## **Support**

- Check the `examples/` folder for sample configurations
- Run `python qr_utils.py --help` for command line help
- The setup script handles most installation issues automatically

<br/><br/>
