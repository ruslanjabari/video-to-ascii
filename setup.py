from setuptools import setup, find_packages
import sys

install_requires = [
    'opencv-python',
    'xtermcolor',
    'ffmpeg-python',
    'paramiko'
]

if "--with-audio" in sys.argv:
    install_requires.extend(['pyaudio'])
    sys.argv.remove("--with-audio")

if "--with-server" in sys.argv:
    install_requires.extend(['paramiko'])
    sys.argv.remove("--with-server")

setup(
    name="video_to_ascii",
    version="1.3.0",
    author="Joel Ibaceta",
    author_email="mail@joelibaceta.com",
    license='MIT',
    description="It is a simple python package to play videos in the terminal",
    long_description="A simple tool to play a video using ascii characters instead of pixels",
    url="https://github.com/joelibaceta/video-to-ascii",
    project_urls={
        'Source': 'https://github.com/joelibaceta/video-to-ascii',
        'Tracker': 'https://github.com/joelibaceta/video-to-ascii/issues'
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='video ascii terminal opencv ssh',
    entry_points={
        "console_scripts": [
            'video-to-ascii=video_to_ascii.cli:main',
            'video-to-ascii-server=video_to_ascii.ssh_server:main'
        ]
    }
)
