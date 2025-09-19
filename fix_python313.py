#!/usr/bin/env python3
"""
Fix for Python 3.13 compatibility issues
Run this script to install compatible packages
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    """Install packages with Python 3.13 compatibility"""
    print("Installing packages compatible with Python 3.13...")

    # Core packages in order of dependency
    packages = [
        "typing-extensions>=4.9.0",
        "setuptools>=68.0.0",
        "wheel>=0.41.0",
        "Werkzeug>=3.0.0",
        "MarkupSafe>=2.1.0",
        "Jinja2>=3.1.0",
        "itsdangerous>=2.1.0",
        "click>=8.1.0",
        "blinker>=1.6.0",
        "Flask>=3.0.0",
        "greenlet>=2.0.0",
        "SQLAlchemy>=2.0.25",
        "Flask-SQLAlchemy>=3.1.0",
        "Flask-Login>=0.6.0",
        "Flask-CORS>=4.0.0",
        "bcrypt>=4.1.0",
        "reportlab>=4.0.0",
        "python-dateutil>=2.8.0",
        "pytest>=7.4.0",
        "pytest-flask>=1.3.0"
    ]

    failed_packages = []

    for package in packages:
        if not install_package(package):
            failed_packages.append(package)

    if failed_packages:
        print(f"\n⚠️  Some packages failed to install: {failed_packages}")
        print("You may need to install these manually or use older Python version")
    else:
        print("\n✅ All packages installed successfully!")
        print("You can now run: python seed_data.py")

if __name__ == "__main__":
    main()