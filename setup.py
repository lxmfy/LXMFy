from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lxmfy",
    version="0.7.1",
    packages=find_packages(),
    install_requires=["RNS", "LXMF"],
    author="Quad4",
    author_email="team@quad4.io",
    description="An easy to use bot framework for LXMF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lxmfy/LXMFy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
