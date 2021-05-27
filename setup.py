from setuptools import setup
import project
import distutils
import os


setup(
    name=project.name,
    version=project.version,
    py_modules=["command"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        upload=command:upload
        login=command:login
        jobstatus=command:jobstatus
    """,
)
