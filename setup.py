from setuptools import setup
import project
import distutils
import os
with open("requirements/prod.txt") as f:
    requirements = f.read().splitlines()



setup(
    name=project.name,
    version=project.version,
    py_modules=["proteus"],
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        proteus=proteus:main
    """,
)