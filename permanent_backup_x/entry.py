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

from threading import Lock, Timer
from functools import partial
from typing import Optional
import collections
import shutil
import time
import os

from mcdreforged.api.command import Literal, UnknownCommand, GreedyText, Integer
from mcdreforged.api.types import PluginServerInterface, CommandSource, ServerInterface
from mcdreforged.api.decorator.new_thread import new_thread

from permanent_backup_x.constant import HELP_MESSAGE, CONFIG_FILE, BACKUP_DONE_EVENT
from permanent_backup_x.compressor import compressors
from permanent_backup_x.config import Configure

game_saved = False
plugin_unloaded = False
creating_backup = Lock()
timer: Optional[Timer] = None
time_since_backup = time.time()


def info_message(source: CommandSource, msg: str, broadcast=False):
    for line in msg.splitlines():
        text = '[Permanent Backup X] ' + line
        if broadcast and source.is_player:
            source.get_server().broadcast(text)
        else:
            source.reply(text)


def touch_folders(config: Configure):
    os.makedirs(config.temp_folder, exist_ok=True)
    os.makedirs(config.backup_path, exist_ok=True)


def format_file_name(file_name):
    for c in ['/', '\\', ':', '*', '?', '"', '|', '<', '>']:
        file_name = file_name.replace(c, '')
    return file_name


@new_thread('Perma-Backup-X')
def create_backup(config: Configure, source: CommandSource, context: dict):
    server = source.get_server()
    comment = context.get('cmt', None)
    global creating_backup
    acquired = creating_backup.acquire(blocking=False)
    auto_save_on = True
    if not acquired:
        info_message(source, '§c正在备份中，请不要重复输入§r')
        return
    try:
        info_message(source, '备份中...请稍等', broadcast=True)
        start_time = time.time()

        # save world
        if config.turn_off_auto_save:
            server.execute('save-off')
            auto_save_on = False
        global game_saved
        game_saved = False
        server.execute('save-all flush')
        while True:
            time.sleep(0.01)
            if game_saved:
                break
            if plugin_unloaded:
                source.reply('§c插件卸载，备份中断！§r', broadcast=True)
                return

        # copy worlds
        def filter_ignore(_, files):
            return [file for file in files if file in config.ignore_files]
        touch_folders(config)
        for world in config.world_names:
            target_path = os.path.join(config.temp_folder, world)
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(os.path.join(config.server_path, world), target_path, ignore=filter_ignore)
        if not auto_save_on:
            server.execute('save-on')
            auto_save_on = True

        file_without_suffix = os.path.join(config.backup_path, time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()))
        if comment is not None:
            file_without_suffix += '_' + format_file_name(comment)

        # zipping worlds
        info_message(source, '创建压缩包中...', broadcast=True)
        with compressors[config.format](server, config, file_without_suffix) as comp:
            comp.write_all(config.temp_folder)
            output_file = str(comp.file)

        # cleaning worlds
        shutil.rmtree(config.temp_folder)

        info_message(source, '备份§a完成§r，耗时{}秒'.format(round(time.time() - start_time, 1)), broadcast=True)
    except Exception as e:
        info_message(source, '备份§a失败§r，错误代码{}'.format(e), broadcast=True)
        server.logger.exception('创建备份失败')
    finally:
        creating_backup.release()
        if config.turn_off_auto_save and not auto_save_on:
            server.execute('save-on')
    server.dispatch_event(BACKUP_DONE_EVENT, (output_file,))


def list_backup(config: Configure, source: CommandSource, context: dict, *, amount=10):
    amount = context.get('amount', amount)
    touch_folders(config)
    arr = []
    for name in os.listdir(config.backup_path):
        file_name = os.path.join(config.backup_path, name)
        if os.path.isfile(file_name):
            arr.append(collections.namedtuple('T', 'name stat')(os.path.basename(file_name), os.stat(file_name)))
    arr.sort(key=lambda x: x.stat.st_mtime, reverse=True)
    info_message(source, '共有§6{}§r个备份'.format(len(arr)))
    if amount == -1:
        amount = len(arr)
    for i in range(min(amount, len(arr))):
        source.reply('§7{}.§r §e{} §r{}MB'.format(i + 1, arr[i].name, round(arr[i].stat.st_size / 2 ** 20, 1)))


def register_command(server: PluginServerInterface, config: Configure):
    def permed_literal(literal: str):
        lvl = config.minimum_permission_level.get(literal, 0)
        return Literal(literal).requires(lambda src: src.has_permission(lvl), failure_message_getter=lambda: '§c权限不足！§r')

    server.register_command(
        Literal(config.prefix).
        runs(lambda src: src.reply(HELP_MESSAGE.format(config.prefix))).
        on_error(UnknownCommand, lambda src: src.reply('参数错误！请输入§7{}§r以获取插件帮助'.format(config.prefix)), handled=True).
        then(
            permed_literal('make').
            runs(partial(create_backup, config)).
            then(GreedyText('cmt').runs(partial(create_backup, config)))
        ).
        then(
            permed_literal('list').
            runs(partial(list_backup, config)).
            then(Integer('amount').runs(partial(list_backup, config)))
        ).
        then(
            permed_literal('listall').
            runs(lambda src: list_backup(config, src, {}, amount=-1))
        ).
        then(
            permed_literal('reset_timer').
            runs(partial(cmd_reset_timer, config))
        )
    )


def auto_create_backup(server: ServerInterface, config: Configure):
    source = server.get_plugin_command_source()
    info_message(source, "每§6{}§r分钟一次的定时备份触发".format(config.interval), broadcast=True)
    create_backup(config, source, {"cmt": "定时备份"})


def reset_timer(server: ServerInterface, config: Configure, cancel: bool = False) -> time.struct_time:
    global time_since_backup, timer
    time_since_backup = time.time()
    timer.cancel()
    if not cancel:
        timer = Timer(config.interval, lambda: auto_create_backup(server, config))
        timer.start()
    return time.localtime(time_since_backup + config.interval)


def cmd_reset_timer(config: Configure, source: CommandSource):
    if timer is None:
        info_message(source, "未开启自动备份功能")
        return
    next_time = reset_timer(source.get_server(), config)
    info_message(source, "已重置计时器")
    info_message(source, "下次自动备份时间: §3{}§r".format(time.strftime("%Y/%m/%d %H:%M:%S", next_time)))


def on_backup_done(config: Configure, server: ServerInterface, _):
    if timer is not None:
        source = server.get_plugin_command_source()
        info_message(source, "备份完毕，重置定时器", broadcast=True)
        next_time = reset_timer(server, config)
        info_message(source, "下次自动备份时间: §3{}§r".format(time.strftime("%Y/%m/%d %H:%M:%S", next_time)))


def on_info(_, info):
    if not info.is_user and info.content == 'Saved the game':
        global game_saved
        game_saved = True


def on_load(server: PluginServerInterface, old):
    global creating_backup, timer
    config = server.load_config_simple(CONFIG_FILE, target_class=Configure, in_data_folder=False)
    if config.format not in compressors:
        raise RuntimeError(f'"format" 选项的值为"{config.format}"，但其值必须在"{list(compressors)}"内')
    if hasattr(old, 'creating_backup') and type(old.creating_backup) == type(creating_backup):
        creating_backup = old.creating_backup
    server.register_help_message(config.prefix, '创建永久备份')
    register_command(server, config)
    server.register_event_listener(BACKUP_DONE_EVENT, partial(on_backup_done, config))
    if config.auto_backup:
        timer = Timer(config.interval, lambda: auto_create_backup(server, config))
        timer.start()


def on_unload(server: ServerInterface):
    global plugin_unloaded
    plugin_unloaded = True
    if timer is not None:
        info_message(server.get_plugin_command_source(), "插件卸载，停止时钟", broadcast=True)
        timer.cancel()


def on_mcdr_stop(server: PluginServerInterface):
    if creating_backup.locked():
        server.logger.info('Waiting for up to 300s for permanent backup to complete')
        if creating_backup.acquire(timeout=300):
            creating_backup.release()
