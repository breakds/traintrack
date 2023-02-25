from setuptools import setup, find_packages

setup(
    name='traintrack',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'agent=traintrack.agent:main',
            'central=traintrack.central:main',
            'traintrack=traintrack.cli:cli',
        ],
    },
    install_requires=[
        "loguru",
        "libtmux",
        "fastapi",
        "prompt-toolkit",
        "uvicorn",
        "pydantic",
        "paramiko",
        "requests",
        "questionary",
        "jinja2",
        "rich",
    ],
)
