from typing import List, Tuple
from pathlib import Path

from datetime import datetime, timedelta

from ruxit.api.base_plugin import BasePlugin
from ruxit.api.selectors import HostSelector


class OldFilesExtension(BasePlugin):

    def query(self, **kwargs):

        for line in self.config.get("folders").splitlines():
            path, recursive, minutes = line.split("|")
            recursive = True if recursive == "true" else False
            minutes = int(minutes)
            self.logger.info(f"Processing path: '{path}', recursive: {recursive}, minutes: {minutes}")

            custom_properties = {}
            try:
                for bad_file, age in get_files_older_than(path, minutes, recursive):
                    custom_properties[f"{bad_file}"] = f"{age}"
                    # 0.001 * 60 * 24 * 365 = 526.5
                    # This is optional, send a metric instead of an event
                    self.results_builder.absolute(key="file_age", value=age.total_seconds(), dimensions={"File": f"{bad_file}"})

                if custom_properties:
                    self.results_builder.report_error_event(
                        description=f"Found files older than {minutes} minutes in folder '{path}'",
                        title="Old Files Check - found old files",
                        properties=custom_properties
                    )
            except Exception as e:
                self.results_builder.report_error_event(
                    description=f"Error running the old files extension: {e}",
                    title="Error running the old files"
                )


def get_files_recursively(path: Path, recurse=True):
    if path.exists():
        for file in path.iterdir():
            if file.is_file():
                yield file
            elif file.is_dir() and recurse:
                yield from get_files_recursively(file)
    else:
        raise Exception(f"Path: {path} does not exist")


def get_files_older_than(folder: str, age_threshold: int, recursive: bool) -> List[Tuple[str, timedelta]]:
    now = datetime.now()
    age_threshold = timedelta(minutes=age_threshold)

    path = Path(folder)
    for file in get_files_recursively(path, recursive):
        modified_date = datetime.fromtimestamp(file.stat().st_mtime)
        file_age = (now - modified_date)
        if file_age > age_threshold:
            yield file, file_age











