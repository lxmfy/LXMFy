from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="LXMFy",
    version="0.5.0",
    packages=find_packages(),
    install_requires=["RNS", "LXMF"],
    author="Sudo-Ivan",
    author_email="",
    description="An easy to use bot framework for LXMF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lxmfy/LXMFy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
)
