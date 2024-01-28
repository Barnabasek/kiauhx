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
import subprocess
from pathlib import Path
from typing import List

from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.mainsail import MAINSAIL_DIR, MAINSAIL_CONFIG_DIR
from kiauh.modules.mainsail.mainsail_utils import backup_config_json
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from kiauh.utils.filesystem_utils import remove_file
from kiauh.utils.logger import Logger


def run_mainsail_removal(
    remove_mainsail: bool,
    remove_ms_config: bool,
    backup_ms_config_json: bool,
    remove_mr_updater_section: bool,
    remove_msc_printer_cfg_include: bool,
) -> None:
    if backup_ms_config_json:
        backup_config_json()
    if remove_mainsail:
        remove_mainsail_dir()
        remove_nginx_config()
        remove_nginx_logs()
        if remove_mr_updater_section:
            remove_updater_section("update_manager mainsail")
    if remove_ms_config:
        remove_mainsail_cfg_dir()
        remove_mainsail_cfg_symlink()
        if remove_mr_updater_section:
            remove_updater_section("update_manager mainsail-config")
        if remove_msc_printer_cfg_include:
            remove_printer_cfg_include()


def remove_mainsail_dir() -> None:
    Logger.print_status("Removing Mainsail ...")
    if not MAINSAIL_DIR.exists():
        Logger.print_info(f"'{MAINSAIL_DIR}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(MAINSAIL_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{MAINSAIL_DIR}':\n{e}")


def remove_nginx_config() -> None:
    Logger.print_status("Removing Mainsails NGINX config ...")
    try:
        remove_file(NGINX_SITES_AVAILABLE.joinpath("mainsail"), True)
        remove_file(NGINX_SITES_ENABLED.joinpath("mainsail"), True)

    except subprocess.CalledProcessError as e:
        log = f"Unable to remove Mainsail NGINX config:\n{e.stderr.decode()}"
        Logger.print_error(log)


def remove_nginx_logs() -> None:
    Logger.print_status("Removing Mainsails NGINX logs ...")
    try:
        remove_file(Path("/var/log/nginx/mainsail-access.log"), True)
        remove_file(Path("/var/log/nginx/mainsail-error.log"), True)

        im = InstanceManager(Klipper)
        instances: List[Klipper] = im.instances
        if not instances:
            return

        for instance in instances:
            remove_file(instance.log_dir.joinpath("mainsail-access.log"))
            remove_file(instance.log_dir.joinpath("mainsail-error.log"))

    except (OSError, subprocess.CalledProcessError) as e:
        Logger.print_error(f"Unable to NGINX logs:\n{e}")


def remove_updater_section(name: str) -> None:
    Logger.print_status("Remove updater section from moonraker.conf ...")
    im = InstanceManager(Moonraker)
    instances: List[Moonraker] = im.instances
    if not instances:
        Logger.print_info("Moonraker not installed. Skipped ...")
        return

    for instance in instances:
        Logger.print_status(f"Remove section '{name}' in '{instance.cfg_file}' ...")

        if not instance.cfg_file.is_file():
            Logger.print_info(f"'{instance.cfg_file}' does not exist. Skipped ...")
            continue

        cm = ConfigManager(instance.cfg_file)
        if not cm.config.has_section(name):
            Logger.print_info("Section not present. Skipped ...")
            continue

        cm.config.remove_section(name)
        cm.write_config()


def remove_mainsail_cfg_dir() -> None:
    Logger.print_status("Removing mainsail-config ...")
    if not MAINSAIL_CONFIG_DIR.exists():
        Logger.print_info(f"'{MAINSAIL_CONFIG_DIR}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(MAINSAIL_CONFIG_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{MAINSAIL_CONFIG_DIR}':\n{e}")


def remove_mainsail_cfg_symlink() -> None:
    Logger.print_status("Removing mainsail.cfg symlinks ...")
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    for instance in instances:
        Logger.print_status(f"Removing symlink from '{instance.cfg_file}' ...")
        try:
            remove_file(instance.cfg_dir.joinpath("mainsail.cfg"))
        except subprocess.CalledProcessError:
            Logger.print_error("Failed to remove symlink!")


def remove_printer_cfg_include() -> None:
    Logger.print_status("Remove mainsail-config include from printer.cfg ...")
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    if not instances:
        Logger.print_info("Klipper not installed. Skipping ...")
        return

    for instance in instances:
        log = f"Removing include from '{instance.cfg_file}' ..."
        Logger.print_status(log)

        if not instance.cfg_file.is_file():
            continue

        cm = ConfigManager(instance.cfg_file)
        if not cm.config.has_section("include mainsail.cfg"):
            Logger.print_info("Section not present. Skipped ...")
            continue

        cm.config.remove_section("include mainsail.cfg")
        cm.write_config()
