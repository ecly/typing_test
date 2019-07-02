# pylint: disable=missing-docstring
from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='typing_test',
    version='0.1',
    description='Typing test in the terminal similar to 10fastfingers',
    license="MIT",
    long_description=long_description,
    author='Emil Lynegaard',
    author_email='ecly@mailbox.org',
    url="http://www.github.com/ecly/typing_test",
    packages=[],
    install_requires=[],
    scripts=['tt'],
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
