from setuptools import setup, find_packages

setup(
    name='txtarchive',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # Leave this list empty if you have no external dependencies
    ],
    entry_points={
        'console_scripts': [
            'txtarchive = txtarchive.__main__:main',
        ],
    },
    author='Harlan A Nelson',
    author_email='harlananelson@gmail.com',
    description='A package for archiving and unpacking text files.',
    # Add other metadata as needed (e.g., license, URL)
)