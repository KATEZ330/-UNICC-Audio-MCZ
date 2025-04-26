from setuptools import setup, find_packages

setup(
    name="media_analyzer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "urllib3==2.0.7",
        "python-dotenv==1.0.0",
        "tkinter"
    ],
) 