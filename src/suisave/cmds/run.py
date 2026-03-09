from suisave.struct.comet import Comet
from suisave.struct.context import Job
from suisave.core import CONFIG_PATH
from pathlib import Path
from typing import List


def run_single(job: Job):
    pass


def run_jobs(logger, job_names: List[str] | bool = True):
    """
    Run the selected job names given to the cli
    If none are given, then by default it takes a boolean.
    """

    # here we first want to parse the config file
    comet = Comet(CONFIG_PATH, logger = logger)
    comet.load()
    print(comet.jobs)

    if job_names is True:
        print("hi")
