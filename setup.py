# setup.py
# setup.py
import os  # Add this line


from setuptools import setup, find_packages

setup(
    name="txtarchive",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={
        'console_scripts': [
            'txtarchive = txtarchive.__main__:main',
        ],
    },
    author="Your Name",
    author_email="harlananelson@gmail.com",
    description="A utility for archiving and unpacking text files",
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7.6',
)