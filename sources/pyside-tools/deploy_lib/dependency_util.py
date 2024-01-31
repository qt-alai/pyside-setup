# Copyright (C) 2024 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import ast
import re
import os
import site
import warnings
import logging
import shutil
import sys
from pathlib import Path
from typing import List, Set

from . import IMPORT_WARNING_PYSIDE, run_command


def get_qt_libs_dir():
    """
    Finds the path to the Qt libs directory inside PySide6 package installation
    """
    pyside_install_dir = None
    for possible_site_package in site.getsitepackages():
        if possible_site_package.endswith("site-packages"):
            pyside_install_dir = Path(possible_site_package) / "PySide6"

    if not pyside_install_dir:
        print("Unable to find site-packages. Exiting ...")
        sys.exit(-1)

    if sys.platform == "win32":
        return pyside_install_dir

    return pyside_install_dir / "Qt" / "lib"  # for linux and macOS


def find_pyside_modules(project_dir: Path, extra_ignore_dirs: List[Path] = None,
                        project_data=None):
    """
    Searches all the python files in the project to find all the PySide modules used by
    the application.
    """
    all_modules = set()
    mod_pattern = re.compile("PySide6.Qt(?P<mod_name>.*)")

    def pyside_imports(py_file: Path):
        modules = []
        contents = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(contents)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    main_mod_name = node.module
                    if main_mod_name.startswith("PySide6"):
                        if main_mod_name == "PySide6":
                            # considers 'from PySide6 import QtCore'
                            for imported_module in node.names:
                                full_mod_name = imported_module.name
                                if full_mod_name.startswith("Qt"):
                                    modules.append(full_mod_name[2:])
                            continue

                        # considers 'from PySide6.QtCore import Qt'
                        match = mod_pattern.search(main_mod_name)
                        if match:
                            mod_name = match.group("mod_name")
                            modules.append(mod_name)
                        else:
                            logging.warning((
                                f"[DEPLOY] Unable to find module name from {ast.dump(node)}"))

                if isinstance(node, ast.Import):
                    for imported_module in node.names:
                        full_mod_name = imported_module.name
                        if full_mod_name == "PySide6":
                            logging.warning(IMPORT_WARNING_PYSIDE.format(str(py_file)))
        except Exception as e:
            raise RuntimeError(f"[DEPLOY] Finding module import failed on file {str(py_file)} with "
                               f"error {e}")

        return set(modules)

    py_candidates = []
    ignore_dirs = ["__pycache__", "env", "venv", "deployment"]

    if project_data:
        py_candidates = project_data.python_files
        ui_candidates = project_data.ui_files
        qrc_candidates = project_data.qrc_files
        ui_py_candidates = None
        qrc_ui_candidates = None

        if ui_candidates:
            ui_py_candidates = [(file.parent / f"ui_{file.stem}.py") for file in ui_candidates
                                if (file.parent / f"ui_{file.stem}.py").exists()]

            if len(ui_py_candidates) != len(ui_candidates):
                warnings.warn("[DEPLOY] The number of uic files and their corresponding Python"
                              " files don't match.", category=RuntimeWarning)

            py_candidates.extend(ui_py_candidates)

        if qrc_candidates:
            qrc_ui_candidates = [(file.parent / f"rc_{file.stem}.py") for file in qrc_candidates
                                 if (file.parent / f"rc_{file.stem}.py").exists()]

            if len(qrc_ui_candidates) != len(qrc_candidates):
                warnings.warn("[DEPLOY] The number of qrc files and their corresponding Python"
                              " files don't match.", category=RuntimeWarning)

            py_candidates.extend(qrc_ui_candidates)

        for py_candidate in py_candidates:
            all_modules = all_modules.union(pyside_imports(py_candidate))
        return list(all_modules)

    # incase there is not .pyproject file, search all python files in project_dir, except
    # ignore_dirs
    if extra_ignore_dirs:
        ignore_dirs.extend(extra_ignore_dirs)

    # find relevant .py files
    _walk = os.walk(project_dir)
    for root, dirs, files in _walk:
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        for py_file in files:
            if py_file.endswith(".py"):
                py_candidates.append(Path(root) / py_file)

    for py_candidate in py_candidates:
        all_modules = all_modules.union(pyside_imports(py_candidate))

    if not all_modules:
        ValueError("[DEPLOY] No PySide6 modules were found")

    return list(all_modules)


class QtDependencyReader:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.lib_reader_name = None
        self.qt_module_path_pattern = None
        self.lib_pattern = None
        self.command = None
        self.qt_libs_dir = None

        if sys.platform == "linux":
            self.lib_reader_name = "readelf"
            self.qt_module_path_pattern = "libQt6{module}.so.6"
            self.lib_pattern = re.compile("libQt6(?P<mod_name>.*).so.6")
            self.command_args = "-d"
        elif sys.platform == "darwin":
            self.lib_reader_name = "dyld_info"
            self.qt_module_path_pattern = "Qt{module}.framework/Versions/A/Qt{module}"
            self.lib_pattern = re.compile("@rpath/Qt(?P<mod_name>.*).framework/Versions/A/")
            self.command_args = "-dependents"
        elif sys.platform == "win32":
            self.lib_reader_name = "dumpbin"
            self.qt_module_path_pattern = "Qt6{module}.dll"
            self.lib_pattern = re.compile("Qt6(?P<mod_name>.*).dll")
            self.command_args = "/dependents"
        else:
            print(f"[DEPLOY] Deployment on unsupported platfrom {sys.platform}")
            sys.exit(1)

        self.qt_libs_dir = get_qt_libs_dir()
        self._lib_reader = shutil.which(self.lib_reader_name)

    @property
    def lib_reader(self):
        return self._lib_reader

    def find_dependencies(self, module: str, used_modules: Set[str] = None):
        """
        Given a Qt module, find all the other Qt modules it is dependent on and add it to the
        'used_modules' set
        """
        qt_module_path = self.qt_libs_dir / self.qt_module_path_pattern.format(module=module)
        if not qt_module_path.exists():
            warnings.warn(f"[DEPLOY] {qt_module_path.name} not found in {str(qt_module_path)}."
                          "Skipping finding its dependencies.", category=RuntimeWarning)
            return

        lib_pattern = re.compile(self.lib_pattern)
        command = [self.lib_reader, self.command_args, str(qt_module_path)]
        # print the command if dry_run is True.
        # Normally run_command is going to print the command in dry_run mode. But, this is a
        # special case where we need to print the command as well as to run it.
        if self.dry_run:
            command_str = " ".join(command)
            print(command_str + "\n")

        # We need to run this even for dry run, to see the full Nuitka command being executed
        _, output = run_command(command=command, dry_run=False, fetch_output=True)

        dependent_modules = set()
        for line in output.splitlines():
            line = line.decode("utf-8").lstrip()
            if sys.platform == "darwin" and line.startswith(f"Qt{module} [arm64]"):
                # macOS Qt frameworks bundles have both x86_64 and arm64 architectures
                # We only need to consider one as the dependencies are redundant
                break
            elif sys.platform == "win32" and line.startswith("Summary"):
                # the dependencies would be found before the `Summary` line
                break
            match = lib_pattern.search(line)
            if match:
                dep_module = match.group("mod_name")
                dependent_modules.add(dep_module)
                if dep_module not in used_modules:
                    used_modules.add(dep_module)
                    self.find_dependencies(module=dep_module, used_modules=used_modules)

        if dependent_modules:
            logging.info(f"[DEPLOY] Following dependencies found for {module}: {dependent_modules}")
        else:
            logging.info(f"[DEPLOY] No Qt dependencies found for {module}")
