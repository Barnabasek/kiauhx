#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
from pathlib import Path
from typing import List

from kiauh.core.backup_manager import BACKUP_ROOT_DIR
from kiauh.utils.common import get_current_date
from kiauh.utils.logger import Logger


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BackupManager:
    def __init__(self, backup_root_dir: Path = BACKUP_ROOT_DIR):
        self._backup_root_dir = backup_root_dir
        self._ignore_folders = None

    @property
    def backup_root_dir(self) -> Path:
        return self._backup_root_dir

    @backup_root_dir.setter
    def backup_root_dir(self, value: Path):
        self._backup_root_dir = value

    @property
    def ignore_folders(self) -> List[str]:
        return self._ignore_folders

    @ignore_folders.setter
    def ignore_folders(self, value: List[str]):
        self._ignore_folders = value

    def backup_file(
        self, files: List[Path] = None, target: Path = None, custom_filename=None
    ):
        if not files:
            raise ValueError("Parameter 'files' cannot be None or an empty List!")

        target = self.backup_root_dir if target is None else target
        for file in files:
            Logger.print_status(f"Creating backup of {file} ...")
            if Path(file).is_file():
                date = get_current_date().get("date")
                time = get_current_date().get("time")
                filename = f"{file.stem}-{date}-{time}{file.suffix}"
                filename = custom_filename if custom_filename is not None else filename
                try:
                    Path(target).mkdir(exist_ok=True)
                    shutil.copyfile(file, target.joinpath(filename))
                except OSError as e:
                    Logger.print_error(f"Unable to backup '{file}':\n{e}")
                    continue
            else:
                Logger.print_info(f"File '{file}' not found ...")

    def backup_directory(self, name: str, source: Path, target: Path = None) -> None:
        if source is None or not Path(source).exists():
            raise OSError("Parameter 'source' is None or Path does not exist!")

        target = self.backup_root_dir if target is None else target
        try:
            log = f"Creating backup of {name} in {target} ..."
            Logger.print_status(log)
            date = get_current_date().get("date")
            time = get_current_date().get("time")
            shutil.copytree(
                source,
                target.joinpath(f"{name.lower()}-{date}-{time}"),
                ignore=self.ignore_folders_func,
            )
        except OSError as e:
            Logger.print_error(f"Unable to backup directory '{source}':\n{e}")
            return

        Logger.print_ok("Backup successfull!")

    def ignore_folders_func(self, dirpath, filenames):
        return (
            [f for f in filenames if f in self._ignore_folders]
            if self._ignore_folders is not None
            else []
        )
