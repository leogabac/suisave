from pathlib import Path
import psutil


def get_mountpoint(uuid: str) -> str | None:
    uuid_path = Path("/dev/disk/by-uuid") / uuid

    if not uuid_path.exists():
        return None

    device = str(uuid_path.resolve())

    for part in psutil.disk_partitions(all=True):
        if Path(part.device).resolve() == Path(device):
            return part.mountpoint

    return None


class SuisaveError(Exception):
    pass


class SuisaveConfigError(SuisaveError):
    pass


class SuisaveDriveError(SuisaveError):
    pass


CONFIG_PATH = Path.home() / ".config" / "suisave" / "comet.toml"
