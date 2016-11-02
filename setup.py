import os
from setuptools import setup

setup(
    name="read-font",
    version="0.1.0",
    description="A tool that reads the bitmap representation of characters in fonts and outputs it in JSON format.",
    url='http://github.com/bogdanm/read-font',
    author='Bogdan Marinescu',
    author_email='bogdan.marinescu@gmail.com',
    license="MIT",
    packages=["read_font"],
    entry_points={
        'console_scripts': [
            'read-font=read_font.read_font:main'
        ]
    },
    install_requires=['freetype-py>=1.0.2']
)
