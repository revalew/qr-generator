#!/usr/bin/env python3
"""
Enhanced QR Code Generator - Complete Installation Script
Automatically sets up the entire application with all dependencies
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
import tempfile
import urllib.request


class QRGeneratorInstaller:
    def __init__(self):
        self.system = platform.system()
        self.python_exe = sys.executable
        self.project_dir = Path.cwd()
        self.venv_path = self.project_dir / "qr_env"
        self.success_count = 0
        self.total_steps = 12

    def print_step(self, step_num, description):
        """Print installation step"""
        print(f"\n[{step_num}/{self.total_steps}] 🔧 {description}")
        print("-" * 60)

    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")
        self.success_count += 1

    def print_warning(self, message):
        """Print warning message"""
        print(f"⚠️  {message}")

    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")

    def run_command(self, command, description, capture_output=True):
        """Run command with error handling"""
        try:
            if isinstance(command, str):
                result = subprocess.run(command, shell=True, check=True,
                                        capture_output=capture_output, text=True)
            else:
                result = subprocess.run(command, check=True,
                                        capture_output=capture_output, text=True)
            return True, result
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"Error output: {e.stderr}")
            return False, e

    def check_python_version(self):
        """Step 1: Check Python version"""
        self.print_step(1, "Checking Python Version")

        version = sys.version_info
        print(f"Python Version: {version.major}.{version.minor}.{version.micro}")

        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.print_error(f"Python 3.7+ required, found {version.major}.{version.minor}")
            return False
        elif version.major == 3 and version.minor >= 13:
            self.print_warning(f"Python 3.{version.minor} detected - some packages may not be available")
            self.print_warning("Consider using Python 3.11 or 3.12 for best compatibility")

        self.print_success("Python version is compatible")
        return True

    def check_system_requirements(self):
        """Step 2: Check system requirements"""
        self.print_step(2, "Checking System Requirements")

        # Check available disk space
        try:
            disk_usage = shutil.disk_usage(self.project_dir)
            free_gb = disk_usage.free / (1024 ** 3)
            if free_gb < 1:
                self.print_warning(f"Low disk space: {free_gb:.1f}GB available")
            else:
                self.print_success(f"Sufficient disk space: {free_gb:.1f}GB available")
        except:
            self.print_warning("Could not check disk space")

        # Check system-specific requirements
        if self.system == "Linux":
            print("Checking Linux-specific requirements...")
            # Check for tkinter
            success, _ = self.run_command([self.python_exe, "-c", "import tkinter"],
                                          "tkinter check")
            if not success:
                self.print_warning("tkinter not available - install with: sudo apt-get install python3-tk")
            else:
                self.print_success("tkinter available")

        self.print_success("System requirements check completed")
        return True

    def create_virtual_environment(self):
        """Step 3: Create virtual environment"""
        self.print_step(3, "Creating Virtual Environment")

        if self.venv_path.exists():
            print("Virtual environment already exists")
            choice = input("Remove and recreate? (y/N): ").strip().lower()
            if choice == 'y':
                shutil.rmtree(self.venv_path)
            else:
                self.print_success("Using existing virtual environment")
                return True

        success, _ = self.run_command([self.python_exe, "-m", "venv", str(self.venv_path)],
                                      "virtual environment creation")
        if success:
            self.print_success("Virtual environment created")
            return True
        return False

    def activate_virtual_environment(self):
        """Step 4: Set up virtual environment paths"""
        self.print_step(4, "Setting Up Virtual Environment")

        if self.system == "Windows":
            self.venv_python = self.venv_path / "Scripts" / "python.exe"
            self.venv_pip = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_path / "bin" / "python"
            self.venv_pip = self.venv_path / "bin" / "pip"

        if not self.venv_python.exists():
            self.print_error("Virtual environment Python not found")
            return False

        self.print_success("Virtual environment configured")
        return True

    def upgrade_pip(self):
        """Step 5: Upgrade pip"""
        self.print_step(5, "Upgrading pip")

        success, _ = self.run_command([str(self.venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                                      "pip upgrade")
        if success:
            self.print_success("pip upgraded")
            return True
        return False

    def install_core_packages(self):
        """Step 6: Install core packages"""
        self.print_step(6, "Installing Core Packages")

        core_packages = [
            "qrcode[pil]==7.4.2",
            "Pillow>=10.0.0"
        ]

        for package in core_packages:
            print(f"Installing {package}...")
            success, _ = self.run_command([str(self.venv_python), "-m", "pip", "install", package],
                                          f"{package} installation")
            if success:
                self.print_success(f"{package} installed")
            else:
                self.print_error(f"Failed to install {package}")
                return False

        return True

    def install_optional_packages(self):
        """Step 7: Install optional packages"""
        self.print_step(7, "Installing Optional Packages")

        optional_packages = [
            ("pyperclip==1.8.2", "Clipboard functionality"),
            ("opencv-python-headless>=4.8.0", "QR scanning"),
            ("pyzbar>=0.1.9", "QR scanning")
        ]

        installed_count = 0
        for package, description in optional_packages:
            print(f"Installing {package} ({description})...")
            success, result = self.run_command([str(self.venv_python), "-m", "pip", "install", package],
                                               f"{package} installation")
            if success:
                self.print_success(f"{package} installed")
                installed_count += 1
            else:
                self.print_warning(f"Failed to install {package} - {description} will not be available")

        print(f"📊 {installed_count}/{len(optional_packages)} optional packages installed")
        self.print_success("Optional packages installation completed")
        return True

    def install_system_dependencies(self):
        """Step 8: Install system dependencies (Enhanced Linux Support)"""
        self.print_step(8, "Installing System Dependencies")

        if self.system != "Linux":
            self.print_success("No system dependencies needed for this platform")
            return True

        print("🐧 Linux detected - checking for system dependencies...")

        # Detect package manager
        package_managers = {
            'apt-get': {
                'check_cmd': ['which', 'apt-get'],
                'update_cmd': ['sudo', 'apt-get', 'update'],
                'install_cmd': ['sudo', 'apt-get', 'install', '-y'],
                'packages': {
                    'python3-tk': 'GUI framework (required for application)',
                    'xclip': 'Primary clipboard support',
                    'xsel': 'Alternative clipboard support',
                    'libzbar0': 'QR code scanning library'
                }
            },
            'dnf': {
                'check_cmd': ['which', 'dnf'],
                'update_cmd': ['sudo', 'dnf', 'check-update'],
                'install_cmd': ['sudo', 'dnf', 'install', '-y'],
                'packages': {
                    'tkinter': 'GUI framework (required for application)',
                    'xclip': 'Primary clipboard support',
                    'xsel': 'Alternative clipboard support',
                    'zbar': 'QR code scanning library'
                }
            },
            'pacman': {
                'check_cmd': ['which', 'pacman'],
                'update_cmd': ['sudo', 'pacman', '-Sy'],
                'install_cmd': ['sudo', 'pacman', '-S', '--noconfirm'],
                'packages': {
                    'tk': 'GUI framework (required for application)',
                    'xclip': 'Primary clipboard support',
                    'xsel': 'Alternative clipboard support',
                    'zbar': 'QR code scanning library'
                }
            },
            'zypper': {
                'check_cmd': ['which', 'zypper'],
                'update_cmd': ['sudo', 'zypper', 'refresh'],
                'install_cmd': ['sudo', 'zypper', 'install', '-y'],
                'packages': {
                    'python3-tkinter': 'GUI framework (required for application)',
                    'xclip': 'Primary clipboard support',
                    'xsel': 'Alternative clipboard support',
                    'libzbar0': 'QR code scanning library'
                }
            }
        }

        # Find available package manager
        detected_pm = None
        for pm_name, pm_info in package_managers.items():
            success, _ = self.run_command(pm_info['check_cmd'], f"{pm_name} detection")
            if success:
                detected_pm = pm_name
                break

        if not detected_pm:
            self.print_warning("No supported package manager found (apt-get, dnf, pacman, zypper)")
            self.print_warning("You may need to install dependencies manually:")
            self.print_warning("- GUI framework: python3-tk/tkinter")
            self.print_warning("- Clipboard: xclip, xsel")
            self.print_warning("- QR scanning: libzbar0/zbar")
            return True

        pm_config = package_managers[detected_pm]
        packages = pm_config['packages']

        print(f"📦 Found package manager: {detected_pm}")
        print(f"💡 The following system packages enhance functionality:")

        for pkg, desc in packages.items():
            status = "🔴 REQUIRED" if 'required' in desc.lower() else "🟡 OPTIONAL"
            print(f"   {status} {pkg}: {desc}")

        print(f"\n⚠️  This requires sudo access to install system packages.")

        # Ask user preference
        install_choice = input("\nInstall system dependencies? (Y/n/individual): ").strip().lower()

        if install_choice == 'n':
            self.print_warning("System dependencies not installed - some features may be limited")
            return True

        # Update package database first
        if install_choice in ['y', 'yes', '', 'individual', 'i']:
            print(f"🔄 Updating package database...")
            success, _ = self.run_command(pm_config['update_cmd'], "package database update", capture_output=False)
            if not success:
                self.print_warning("Package database update failed, continuing anyway...")

        installed_count = 0

        if install_choice in ['individual', 'i']:
            # Install individually with user confirmation
            for pkg, desc in packages.items():
                is_required = 'required' in desc.lower()
                status = "REQUIRED" if is_required else "OPTIONAL"

                user_choice = input(f"\nInstall {pkg} ({status})? {desc} (Y/n): ").strip().lower()

                if user_choice in ['y', 'yes', '']:
                    print(f"Installing {pkg}...")
                    success, _ = self.run_command(pm_config['install_cmd'] + [pkg],
                                                  f"{pkg} installation", capture_output=False)
                    if success:
                        self.print_success(f"{pkg} installed successfully")
                        installed_count += 1
                    else:
                        self.print_error(f"Failed to install {pkg}")
                        if is_required:
                            self.print_warning("This may cause issues with the application")
                else:
                    self.print_warning(f"Skipped {pkg}")
                    if is_required:
                        self.print_warning("Application may not work properly without this package")

        else:
            # Install all at once
            all_packages = list(packages.keys())
            print(f"Installing all packages: {', '.join(all_packages)}")
            success, _ = self.run_command(pm_config['install_cmd'] + all_packages,
                                          "system dependencies installation", capture_output=False)
            if success:
                installed_count = len(all_packages)
                self.print_success(f"All {installed_count} system packages installed")
            else:
                self.print_error("Batch installation failed, trying individual installation...")
                # Fallback to individual installation
                for pkg, desc in packages.items():
                    success, _ = self.run_command(pm_config['install_cmd'] + [pkg],
                                                  f"{pkg} installation", capture_output=False)
                    if success:
                        installed_count += 1
                        self.print_success(f"{pkg} installed")
                    else:
                        self.print_warning(f"Failed to install {pkg}")

        print(f"\n📊 System Dependencies Summary:")
        print(f"   Installed: {installed_count}/{len(packages)} packages")

        if installed_count == len(packages):
            self.print_success("All system dependencies installed successfully")
        elif installed_count > 0:
            self.print_success(f"Partial installation completed ({installed_count}/{len(packages)})")
            self.print_warning("Some features may be limited")
        else:
            self.print_warning("No system dependencies installed")
            self.print_warning("The application will work but with reduced functionality")

        return True

    def install_pip_packages(self):
        """Step 6: Install pip packages from requirements.txt"""
        self.print_step(6, "Installing Python Packages")

        requirements_file = self.project_dir / "requirements.txt"

        if not requirements_file.exists():
            self.print_warning("requirements.txt not found, installing core packages manually")
            return self.install_core_packages_manual()

        print("📋 Installing packages from requirements.txt...")
        success, result = self.run_command([str(self.venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
                                           "requirements.txt installation")

        if success:
            self.print_success("All pip packages installed successfully")

            # Test core imports
            print("🧪 Testing core functionality...")
            test_imports = [
                ("qrcode", "QR code generation"),
                ("PIL", "Image processing"),
                ("tkinter", "GUI framework")
            ]

            working_features = []
            for module, feature in test_imports:
                success, _ = self.run_command([str(self.venv_python), "-c", f"import {module}"],
                                              f"{module} test")
                if success:
                    working_features.append(feature)
                    self.print_success(f"{feature} working")
                else:
                    self.print_warning(f"{feature} may have issues")

            print(f"✅ Core features ready: {', '.join(working_features)}")
            return True
        else:
            self.print_error("Failed to install from requirements.txt")
            print("Attempting manual installation of core packages...")
            return self.install_core_packages_manual()

    def install_core_packages_manual(self):
        """Fallback manual installation of core packages"""
        core_packages = [
            "qrcode[pil]==7.4.2",
            "Pillow>=10.0.0"
        ]

        for package in core_packages:
            print(f"Installing {package}...")
            success, _ = self.run_command([str(self.venv_python), "-m", "pip", "install", package],
                                          f"{package} installation")
            if success:
                self.print_success(f"{package} installed")
            else:
                self.print_error(f"Failed to install {package}")
                return False

        return True

    def create_directory_structure(self):
        """Step 9: Create directory structure"""
        self.print_step(9, "Creating Directory Structure")

        directories = [
            "config",
            "config/user_presets",
            "exports",
            "exports/batch_output",
            "examples",
            # "docs"
        ]

        for directory in directories:
            dir_path = self.project_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")

        self.print_success("Directory structure created")
        return True

    def create_example_files(self):
        """Step 10: Create example files"""
        self.print_step(10, "Creating Example Files")

        # Create sample CSV
        sample_csv = """content,filename,theme,color_mask,fg_color,bg_color,size
https://www.python.org,python_website,rounded,radial,#3776ab,#ffffff,400
WIFI:T:WPA;S:Example_WiFi;P:password123;H:false;,wifi_example,circular,horizontal,#8B4513,#F5DEB3,350
mailto:contact@example.com,email_contact,classic,solid,#1f4e79,#ffffff,300"""

        csv_path = self.project_dir / "examples" / "sample_batch.csv"
        csv_path.write_text(sample_csv)
        self.print_success("Sample CSV created")

        # Create sample JSON
        sample_json = [
            {
                "content": "https://github.com",
                "filename": "github_qr",
                "theme": "rounded",
                "color_mask": "vertical",
                "fg_color": "#24292e",
                "bg_color": "#ffffff",
                "size": 500
            }
        ]

        json_path = self.project_dir / "examples" / "sample_batch.json"
        with open(json_path, 'w') as f:
            json.dump(sample_json, f, indent=2)
        self.print_success("Sample JSON created")

        # Create sample configuration
        sample_config = {
            "preset": "url",
            "theme": "Rounded Corners",
            "color_mask": "Radial Gradient",
            "size": 400,
            "border": 4,
            "error_correction": "M",
            "fg_color": "#1a365d",
            "bg_color": "#ffffff",
            "content": "https://example.com"
        }

        config_path = self.project_dir / "examples" / "sample_config.json"
        with open(config_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        self.print_success("Sample configuration created")

        return True

    def test_installation(self):
        """Step 11: Test installation"""
        self.print_step(11, "Testing Installation")

        # Test core imports
        test_imports = [
            ("tkinter", "GUI framework"),
            ("qrcode", "QR code generation"),
            ("PIL", "Image processing"),
            ("json", "JSON handling")
        ]

        for module, description in test_imports:
            success, _ = self.run_command([str(self.venv_python), "-c", f"import {module}"],
                                          f"{module} import test")
            if success:
                self.print_success(f"{description} working")
            else:
                self.print_error(f"{description} failed")
                return False

        # Test QR generation
        qr_test_code = """
import qrcode
from PIL import Image
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data('Installation Test')
qr.make(fit=True)
img = qr.make_image(fill_color='black', back_color='white')
print('QR generation successful')
"""

        success, _ = self.run_command([str(self.venv_python), "-c", qr_test_code],
                                      "QR generation test")
        if success:
            self.print_success("QR generation working")
        else:
            self.print_error("QR generation failed")
            return False

        return True

    def create_shortcuts(self):
        """Step 12: Create shortcuts and launchers"""
        self.print_step(12, "Creating Shortcuts and Launchers")

        # Create activation script
        if self.system == "Windows":
            activate_script = f"""@echo off
echo Activating QR Generator environment...
call "{self.venv_path}\\Scripts\\activate.bat"
echo Environment activated! You can now run:
echo   python qr_generator.py
echo   python launcher.py
echo   python qr_utils.py --help
cmd /k
"""
            script_path = self.project_dir / "activate.bat"
            script_path.write_text(activate_script)
            self.print_success("Windows activation script created")

        else:  # Linux/macOS
            activate_script = f"""#!/bin/bash
echo "Activating QR Generator environment..."
source "{self.venv_path}/bin/activate"
echo "Environment activated! You can now run:"
echo "  python qr_generator.py"
echo "  python launcher.py" 
echo "  python qr_utils.py --help"
exec bash
"""
            script_path = self.project_dir / "activate.sh"
            script_path.write_text(activate_script)
            script_path.chmod(0o755)
            self.print_success("Unix activation script created")

        # Create run script
        if self.system == "Windows":
            run_script = f"""@echo off
cd /d "{self.project_dir}"
"{self.venv_python}" launcher.py
pause
"""
            run_path = self.project_dir / "run_qr_generator.bat"
            run_path.write_text(run_script)

        else:
            run_script = f"""#!/bin/bash
cd "{self.project_dir}"
"{self.venv_python}" launcher.py
"""
            run_path = self.project_dir / "run_qr_generator.sh"
            run_path.write_text(run_script)
            run_path.chmod(0o755)

        self.print_success("Run scripts created")
        return True

    def print_installation_summary(self):
        """Print installation summary"""
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION COMPLETED!")
        print("=" * 60)

        print(f"\n📊 Installation Summary:")
        print(f"✅ Steps completed: {self.success_count}/{self.total_steps}")
        print(f"🎯 Success rate: {(self.success_count / self.total_steps) * 100:.1f}%")

        print(f"\n📁 Installation Directory: {self.project_dir}")
        print(f"🐍 Python Environment: {self.venv_python}")

        print(f"\n🚀 Getting Started:")

        if self.system == "Windows":
            print("1. Double-click 'run_qr_generator.bat' to start")
            print("2. Or run 'activate.bat' then 'python launcher.py'")
        else:
            print("1. Run './run_qr_generator.sh' to start")
            print("2. Or run 'source activate.sh' then 'python launcher.py'")

        print(f"\n📖 Available Commands:")
        print("  python qr_generator.py    - Launch GUI application")
        print("  python launcher.py        - Smart launcher with menu")
        print("  python qr_utils.py --help - Command line utilities")
        print("  python troubleshoot.py    - Troubleshooting tools")

        print(f"\n📁 Important Files:")
        print("  examples/sample_batch.csv   - Sample batch file")
        print("  examples/sample_config.json - Sample configuration")
        print("  config/                     - Your saved configurations")
        print("  exports/                    - Your generated QR codes")

        if self.success_count < self.total_steps:
            print(f"\n⚠️  Some steps had issues. Run 'python troubleshoot.py' for diagnosis.")

        print(f"\n🎯 Quick Test:")
        print("  Run the launcher and create your first QR code!")

    def run_installation(self):
        """Run complete installation"""
        print("🛠️  Enhanced QR Code Generator - Installation")
        print("=" * 60)
        print("This installer will set up everything you need.")

        proceed = input("\nProceed with installation? (Y/n): ").strip().lower()
        if proceed == 'n':
            print("Installation cancelled.")
            return False

        installation_steps = [
            self.check_python_version,
            self.check_system_requirements,
            self.create_virtual_environment,
            self.activate_virtual_environment,
            self.upgrade_pip,
            self.install_core_packages,
            self.install_optional_packages,
            self.install_system_dependencies,
            self.create_directory_structure,
            self.create_example_files,
            self.test_installation,
            # self.create_shortcuts
        ]

        for step in installation_steps:
            try:
                if not step():
                    print(f"\n❌ Installation failed at step: {step.__name__}")
                    print("Run 'python troubleshoot.py' for diagnosis.")
                    return False
            except Exception as e:
                print(f"\n❌ Unexpected error in {step.__name__}: {e}")
                return False

        self.print_installation_summary()
        return True


def main():
    """Main installation function"""
    try:
        installer = QRGeneratorInstaller()
        success = installer.run_installation()

        if success:
            print("\n🎉 Installation successful! Enjoy your QR generator!")
        else:
            print("\n💔 Installation had issues. Check the output above.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Installation interrupted by user")
    except Exception as e:
        print(f"\n💥 Installation failed with error: {e}")
        print("Please report this issue with the full error message.")


if __name__ == "__main__":
    main()