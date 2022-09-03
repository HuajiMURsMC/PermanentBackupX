from typing import List, Dict

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
