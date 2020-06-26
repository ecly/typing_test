# pylint: disable=missing-docstring
from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="typing_test",
    version="0.1.0",
    description="Typing test in the terminal similar to 10fastfingers",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Emil Lynegaard",
    author_email="ecly@mailbox.org",
    url="http://www.github.com/ecly/typing_test",
    packages=["typing_test"],
    package_data={"typing_test": ["data/vocab"]},
    install_requires=[],
    scripts=["scripts/tt"],
    keywords=[
        "typing",
        "typing test",
        "10fastfingers",
        "cmd",
        "terminal",
        "game",
        "ncurses",
        "curses",
    ],
)
