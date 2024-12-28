from setuptools import setup, find_packages

setup(
    name="LXMFy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["RNS", "LXMF"],
    author="Sudo-Ivan",
    author_email="",
    description="A Discord.py-like bot framework for LXMF",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://gitlab.com/Sudo-Ivan/LXMFy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
)
