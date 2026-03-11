from pathlib import Path
import psutil
import subprocess
import asyncio
from desktop_notifier import DesktopNotifier

# ===============================================================================
# GLOBALS
# ===============================================================================

CONFIG_PATH = Path.home() / ".config" / "suisave" / "comet.toml"
notifier = DesktopNotifier()

# ===============================================================================
# HELPER FUNCTIONS
# ===============================================================================


def notify(title: str, message: str, timeout: int = 2):
    asyncio.run(
        notifier.send(
            title=title,
            message=message,
            timeout=timeout,
        )
    )


def run_rsync(cmd: list[str], logger) -> None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        # if result.stdout:
        #     logger.info(result.stdout.strip())
        if result.stderr:
            logger.error(result.stderr.strip())

    except subprocess.CalledProcessError as e:
        logger.error(f"rsync failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"stdout:\n{e.stdout.strip()}")
        if e.stderr:
            logger.error(f"stderr:\n{e.stderr.strip()}")
        raise

    return result.stdout


def get_mountpoint(uuid: str) -> str | None:
    uuid_path = Path("/dev/disk/by-uuid") / uuid

    if not uuid_path.exists():
        return None

    device = str(uuid_path.resolve())

    for part in psutil.disk_partitions(all=True):
        if Path(part.device).resolve() == Path(device):
            return Path(part.mountpoint)

    return None


# ===============================================================================
# MISCELLANEOUS ERROR HANDLING FUNCTIONS
# ===============================================================================



# ===============================================================================
# ERRORS
# ===============================================================================


class SuisaveError(Exception):
    pass


class SuisaveConfigError(SuisaveError):
    pass


class SuisaveDriveError(SuisaveError):
    pass
