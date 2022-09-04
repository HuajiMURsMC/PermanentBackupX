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
'''.strip()
BACKUP_DONE_EVENT = PluginEvent("permanent_backup_x.backup_done")
