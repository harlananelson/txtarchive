# txtarchive/setup.py
from setuptools import setup, find_packages

setup(
    name='txtarchive',
    version='0.1.0',  # This is the source of truth
    packages=find_packages(),
    install_requires=[],
    author='Harlan A Nelson',
    author_email='hnelson3@iuhealth.org',
    description='Create and unpack TXT archives, with LLM-friendly options',
)