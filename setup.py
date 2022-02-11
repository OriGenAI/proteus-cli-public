from setuptools import setup, find_packages
import project


def translate_local(source):
    print("source", source)
    if "==" in source:
        return source
    return ""


with open("requirements/prod.txt") as f:
    sources = f.read().splitlines()
    requirements = map(translate_local, sources)

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
