import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


class DirStats:
    def __init__(self, path: Path):
        self.name = path.name
        self.path = path
        self.parent = path.parent

        self.size_bytes: int = None
        self.size_human: float = None
        self.files: int = None
        self.directories: int = None
        self.last_modified: str = None
        self.newest_file: str = None
        self.oldest_file: str = None

        self.is_computed: bool = False

    def compute(self):
        path = Path(self.path).resolve()

        total_size = 0
        n_files = 0
        n_dirs = 0
        newest_mtime = 0
        oldest_mtime = float("inf")

        stack = [path]

        while stack:
            current = stack.pop()

            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            n_dirs += 1
                            stack.append(entry.path)

                        elif entry.is_file(follow_symlinks=False):
                            stat = entry.stat()
                            size = stat.st_size
                            mtime = stat.st_mtime

                            total_size += size
                            n_files += 1

                            newest_mtime = max(newest_mtime, mtime)
                            oldest_mtime = min(oldest_mtime, mtime)

                    except OSError:
                        # skip files we cannot access
                        pass

        root_stat = path.stat()

        self.size_bytes = total_size
        self.size_human = self._human_size()
        self.files = n_files
        self.directories = n_dirs
        self.last_modified = datetime.fromtimestamp(root_stat.st_mtime)
        self.newest_file = datetime.fromtimestamp(newest_mtime) if n_files else None
        self.oldest_file = datetime.fromtimestamp(oldest_mtime) if n_files else None

        self.is_computed = True

    def _human_size(self):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if self.size_bytes < 1024:
                return f"{self.size_bytes:.2f} {unit}"
            self.size_bytes /= 1024

    def compare_with(self, other: Path, skip_header = False):
        # print(other)
        stats2 = DirStats(other)
        stats2.compute()

        rows = [
            ("name", self.name, stats2.name),
            ("path", self.path, stats2.path),
            ("size", self.size_human, stats2.size_human),
            ("files", self.files, stats2.files),
            ("dirs", self.directories, stats2.directories),
        ]

        header = f"{' ':<12} {'source':<30} {'target':<30}"
        sep = "=" * 80

        if skip_header:
            lines = []
        else:
            lines = [sep, header, sep]

        for field, old, new in rows:
            lines.append(f"{field:<12} {str(old):<30} {str(new):<30}")

        return "\n".join(lines)

    def __str__(self):
        if not self.is_computed:
            return

        msg = [
            f"name: \t {self.name}",
            f"path: \t {self.path._str}",
            f"size: \t {self.size_human}",
            f"files: \t {self.files}",
            f"dirs: \t {self.directories}",
        ]
        return "\n".join(msg)
