"""Setup script for Family Tree Application."""
from setuptools import setup, find_packages
from src import __version__, __author__, __license__, __description__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="family-tree-app",
    version=__version__,
    author=__author__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zacala1/family-tree-viewer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Sociology :: Genealogy",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.4.0",
        "openpyxl>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "familytree=main:main",
        ],
    },
    include_package_data=True,
    keywords="genealogy family-tree visualization pyqt6",
    project_urls={
        "Bug Reports": "https://github.com/zacala1/family-tree-viewer/issues",
        "Source": "https://github.com/zacala1/family-tree-viewer",
    },
)
