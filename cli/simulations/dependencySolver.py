import os
from datetime import datetime
from multiprocessing.dummy import Pool

from dateutil import tz

from cli.runtime import proteus
from cli.config import config


class DependencySolver:
    def __init__(
        self,
        batch_url,
        dependencies,
        case_number,
        source_folder,
        has_case_folder=False,
        reupload=False,
    ):
        """Class to solve all the dependencies of a case
        Arguments:
            batch_url {string}: the path of the case
            dependencies {List<CaseDependency>}: list of dependencies
            case_number {number}: the number of the simulation case
            source_folder {string}: the folder that holds all batch cases
            has_case_folder {bool}: flag to check if you are uploading
            from a case folder
        """
        self.batch_url = batch_url
        self.dependencies = dependencies
        self.case_number = case_number
        self.source_folder = source_folder
        self.has_case_folder = has_case_folder
        self.reupload = reupload

        self.do_not_retry_list = []
        self.workers_count = config.WORKERS_COUNT

    def upload_file_to_batch(self, source_path, filepath):
        """Uploads the given file to the url

        Args:
            url (string): the url to upload to
            source_path (string): the source path for this file (locally)
            filepath (string): the dest path for this file (remote location)

        Returns:
            string: the response for the upload request
        """
        try:
            modification_ts = os.path.getmtime(source_path)
            modified = datetime.fromtimestamp(modification_ts, tz.tzlocal())
            with open(source_path, "rb") as source:
                response = proteus.api.post_file(self.batch_url, filepath, content=source, modified=modified)
                response_json = response.json()
                assert "case" in response_json
                return response_json.get("case")
        except FileNotFoundError:
            print(f"File not found: {source_path}")
            return {"file_to_ignore": filepath}

    def async_dependency_upload(self, filepath):
        source_folder = self.source_folder

        # Transform source folder
        if self.has_case_folder:
            source_folder.replace("./", "./cases/")

        source_folder = source_folder.split("/")
        source_folder = source_folder[:-1] if len(source_folder) > 1 else source_folder
        source_folder = "/".join(source_folder)

        source_path = f"{source_folder}/{filepath}"
        return self.upload_file_to_batch(source_path, filepath)

    def provide_case_dependencies(self):
        """Loops through a single case's dependencies,
        and uploads to the batch input folder"""
        pending_dependencies = [
            dependency.get("path")
            for dependency in self.dependencies
            if self.reupload
            or dependency.get("status") != "solved"
            and dependency.get("path") not in self.do_not_retry_list
        ]

        with Pool(processes=self.workers_count) as pool:
            for res in pool.imap_unordered(self.async_dependency_upload, pending_dependencies):
                if res:
                    if "file_to_ignore" in res:
                        self.do_not_retry_list.append(res.get("file_to_ignore"))

        return not pending_dependencies

    def solve_dependencies(self):
        """Recursive function that solves all the cases dependencies"""
        # Upload all dependencies
        should_stop = self.provide_case_dependencies()

        # Check for new dependencies
        simulation_case_url = f"{self.batch_url}/{self.case_number}"
        response = proteus.api.get(simulation_case_url)
        new_dependencies = response.json().get("dependencies")

        pending_dependencies = [dependency for dependency in new_dependencies if dependency.get("status") == "pending"]
        if pending_dependencies and not should_stop:
            self.dependencies = pending_dependencies
            self.solve_dependencies()
