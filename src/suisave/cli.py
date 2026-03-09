import sys
import logging
import suisave.cmds as cmd
from suisave.core import SuisaveError
from suisave.struct.logger import get_logger


VERSION = "0.2.0-pre"


def main():
    job_names = ["hi"]
    logger = get_logger(name="suisave", level=logging.DEBUG)
    try:
        cmd.run_jobs(logger, job_names)
    except SuisaveError as e:
        # print(f"{e.__class__.__name__}: {e}")
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        exit(1)


def config():
    print("hello 2")
