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

import os

from mcdreforged.api.event import PluginEvent

CONFIG_FILE = os.path.join('config', 'PermanentBackupX.json')
HELP_MESSAGE = '''
§7------§rMCDR Permanent Backup X§7------§r
一个创建永久备份的插件
§a【格式说明】§r
§7{0}§r 显示帮助信息
§7{0} make [<comment>]§r 创建一个备份。§7[<comment>]§r为可选注释信息
§7{0} list§r 显示最近的十个备份的信息
§7{0} listall§r 显示所有备份的信息
§7{0} reset_timer§r 重置计时器
'''.strip()
BACKUP_DONE_EVENT = PluginEvent("permanent_backup_x.backup_done")
