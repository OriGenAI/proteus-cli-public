from setuptools import setup
import project
import distutils
import os


class DockerScriptsCommand(distutils.cmd.Command):
    """Creates all the docker files and the update scripts"""

    description = "creates docker files and update scripts"
    user_options = [
        # The format is (long option, short option, description).
        ("folder=", None, "path to the template files"),
    ]

    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.folder = "templates"

    def finalize_options(self):
        """Post-process options."""
        if self.folder:
            assert os.path.exists(self.folder), (
                "template folder %s does not exist." % self.folder
            )

    def run(self):
        from string import Template

        terms = {
            "project_name": project.name,
            "project_version": project.version,
            "project": project.project,  # Parent project
        }
        for template_filename in os.listdir(self.folder):
            with open(f"{self.folder}/{template_filename}", "r") as source:
                target_filename = template_filename.replace(".tmpl", "")
                with open(target_filename, "w") as target:
                    target_filename = template_filename.replace(".tmpl", "")
                    template = Template(source.read())
                    target.write(template.substitute(terms))
                    print(
                        f"generated {target_filename} from {template_filename}"
                    )


setup(
    name=project.name,
    version=project.version,
    py_modules=["command"],
    install_requires=[
        "Click",
    ],
    cmdclass={"docker": DockerScriptsCommand},
    entry_points="""
        [console_scripts]
        run=command:run
    """,
)
