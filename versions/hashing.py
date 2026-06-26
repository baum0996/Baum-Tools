from __future__ import annotations

import hashlib
from pathlib import Path


class HashGenerator:
    def sha256(self, path: Path) -> str:
        return self._hash_file(path, "sha256")

    def md5(self, path: Path) -> str:
        return self._hash_file(path, "md5")

    @staticmethod
    def _hash_file(path: Path, algorithm: str) -> str:
        digest = hashlib.new(algorithm)
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
