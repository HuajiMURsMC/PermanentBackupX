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

from typing import List, Dict, Optional

from mcdreforged.api.utils.serializer import Serializable


class Configure(Serializable):
    prefix: str = "!!backupx"
    turn_off_auto_save: bool = True
    ignore_files: List[str] = [
        "session.lock"
    ]
    temp_folder: str = './backupx_temp'
    backup_path: str = './backupx'
    server_path: str = './server'
    format: str = 'zip'
    backup_password: Optional[str] = None
    world_names: List[str] = [
        'world'
    ]
    # 0: guest, 1: user, 2: helper, 3: admin, 4: owner
    minimum_permission_level: Dict[str, int] = {
        'make': 2,
        'list': 0,
        'listall': 2
    }
    auto_backup: bool = False
    auto_backup_interval: float = 30.0

    @property
    def interval(self):
        return self.auto_backup_interval * 60
