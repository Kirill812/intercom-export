"""
Setup configuration for intercom-export package.
"""

from setuptools import setup, find_packages

setup(
    name="intercom-export",
    version="0.1.0",
    description="Tool for exporting and formatting Intercom conversations",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.25.0",
        "PyYAML>=5.4.0",
    ],
    entry_points={
        "console_scripts": [
            "intercom-export=intercom_export.cli:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
