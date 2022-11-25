# -*- coding: utf-8 -*-
# Copyright (C) 2022  Huaji_MUR233
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from contextlib import AbstractContextManager
from typing import Dict, Union, Type
from pathlib import Path
from abc import ABC
import tarfile
import os

from mcdreforged.api.types import ServerInterface
import pyzipper
import py7zr

from permanent_backup_x.config import Configure

compressors: Dict[str, Type['AbstractCompressor']] = {}


def register(clazz: Type['AbstractCompressor']):
    compressors[clazz._format] = clazz
    return clazz


class AbstractCompressor(AbstractContextManager, ABC):
    _format: str
    _suffix: str

    def __init__(self, server: ServerInterface, config: Configure, file: str):
        self.server = server
        self.config = config
        if not file.endswith(suffix := self.suffix):
            file += suffix
        self.file = Path(file)

    @property
    def format(self) -> str:
        return self._format

    @property
    def suffix(self) -> str:
        return self._suffix

    def write_all(self, directory: Union[Path, str]):
        cwd = os.getcwd()
        files_or_dirs = os.listdir(directory)
        os.chdir(directory)
        for file_or_dir in files_or_dirs:
            self._write_all(Path(file_or_dir))
        os.chdir(cwd)

    def _write_all(self, path: Path):
        if path.is_file():
            self.write(path)
        elif path.is_dir():
            if not path.samefile("."):
                self.write(path)
            for nm in sorted(os.listdir(str(path))):
                self._write_all(path.joinpath(nm))
        else:
            return

    def write(self, path: Path):
        raise NotImplementedError

    def __enter__(self) -> 'AbstractCompressor':
        raise NotImplementedError


@register
class ZipCompressor(AbstractCompressor):
    _format = "zip"
    _suffix = ".zip"

    def write(self, path: Path):
        if self.config.backup_password is not None:
            self.zf.setpassword(self.config.backup_password.encode("utf8"))
        self.zf.write(path)

    def __enter__(self) -> 'AbstractCompressor':
        if self.config.backup_password is not None:
            self.zf = pyzipper.AESZipFile(self.file, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES)
        else:
            self.zf = pyzipper.ZipFile(self.file, 'w', compression=pyzipper.ZIP_DEFLATED)
        return self

    def __exit__(self, __exc_type, __exc_value, __traceback):
        self.zf.close()


@register
class SevenZipCompressor(AbstractCompressor):
    _format = "7z"
    _suffix = ".7z"

    def write(self, path: Path):
        self.zf.write(path)

    def __enter__(self) -> 'AbstractCompressor':
        self.zf = py7zr.SevenZipFile(self.file, 'w', password=self.config.backup_password if self.config.backup_password is not None else None)
        return self

    def __exit__(self, __exc_type, __exc_value, __traceback):
        self.zf.close()


@register
class TarCompressor(AbstractCompressor):
    _format = "tar"
    _suffix = ".tar"

    def write(self, path: Path):
        self.tarfile.add(path)

    def __enter__(self) -> 'AbstractCompressor':
        if self.config.backup_password is not None:
            self.server.logger.warning("配置文件中配置了备份密码，但当前格式并不支持加密，创建的归档文件将不会进行任何加密")
        self.tarfile = tarfile.open(self.file, f'w:{self.format}')
        return self
    
    def __exit__(self, __exc_type, __exc_value, __traceback):
        self.tarfile.close()


@register
class GZipCompressor(TarCompressor):
    _format = "gz"
    _suffix = ".tar.gz"


@register
class BZip2Compressor(TarCompressor):
    _format = "bz2"
    _suffix = ".tar.bz2"


@register
class XZipCompressor(TarCompressor):
    _format = "xz"
    _suffix = ".tar.xz"
