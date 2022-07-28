from setuptools import setup, find_packages
import project


with open("requirements/prod.txt") as source:
    requirements = source.read().splitlines()

setup(
    name=project.name,
    version=project.version,
    packages=find_packages(),
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        proteus=cli.cli:main
    """,
)
