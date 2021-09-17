from setuptools import setup
import project


setup(
    name=project.name,
    version=project.version,
    py_modules=["proteus"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        proteus=proteus:main
    """,
)
