from setuptools import setup, find_packages

setup(
    name='txtarchive',  # Replace with your package name
    version='0.1.0',  # Replace with your package version
    packages=find_packages(),
    install_requires=[
        # List any dependencies your lhn package requires
        # For example: 'requests>=2.20.0',
    ],
    author='Harlan A Nelsson',  # Replace with your name
    author_email='hnelson3@iuhealth.org', #replace with your email
    description='Create and unpack TXT archive.  Can be used to create an LLM freindly version of a directory of code', #replace with an accurate description.
    # Add other metadata as needed (e.g., license, URL)
)
