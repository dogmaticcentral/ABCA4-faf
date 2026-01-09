_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

from pathlib import Path, PurePath

from utils.utils import comfort, scream, shrug


def construct_report_filepath(workdir: Path | str,  name_stem: str,  filetype: str, should_exist: bool = False) -> Path:
    """Creates conventional name for a compilation (report) file.
    :param workdir: Path | str
        Full path to the work directory
    :param name_stem: str
        The name stem. (E.g. 'overlay', or 'histogram'.)
    :param filetype: str
        The expected file type (not checked; e.g. 'pdf', 'pptx', or 'txt')
    :param should_exist:
        Specify whether the file should already exist, or if we want to create a new one.
        In the latter case the parent directory will be created if it does not exist.
    :return: Path
        THe conventional path to the auxiliary (working) file.
        A note: these files are expected to be replaceable with relative ease (compared to the original
        and manually created files, which should probably not be stored in the workdir.)
    """

    workdir = Path(workdir)
    target_dir   = Path(PurePath(workdir, 'reports'))
    file_name = f"{name_stem}.{filetype}"
    file_path =  target_dir.joinpath(file_name)
    if should_exist:
        if not target_dir.exists():
            scream(f"Directory {target_dir} not found.")
            exit()
        if not file_path.exists():
            shrug(f"Directory {target_dir} found, however")
            scream(f"the file {file_name} not found therein.")
            exit()
    else:
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

    return file_path


def construct_workfile_path(workdir: Path | str, orig_img_path: Path | str, alias: str, purpose: str, filetype: str,
                            eye: str="", should_exist: bool = False) -> Path:
    """Creates conventional name for a file with particular purpose in the workdir.
    :param eye:
    :param workdir: Path | str
        Full path to the work directory
    :param orig_img_path:  Path | str
        Full path to the original image
    :param alias: str
        The patient alias
    :param purpose: str
        The purpose of the file. (E.g. 'overlay', or 'histogram'.)
    :param filetype: str
        The expected file type (not checked; e.g. 'png', 'svg', or 'txt')
     :param eye: str
        Eye laterality ("OD", "OS", or ""); default ""
    :param should_exist:
        Specify whether the file should already exist, or if we want to create a new one.
        In the latter case the parent directory will be created if it does not exist.
    :return: Path
        THe conventional path to the auxiliary (working) file.
        A note: these files are expected to be replaceable with relative ease (compared to the original
        and manually created files, which should probably not be stored in the workdir.)
    """

    workdir = Path(workdir)
    orig_img_path = Path(orig_img_path)
    alias = alias.replace(" ", "_")  # just in case
    path_parts = [workdir, alias, purpose + 's']
    if eye: path_parts.append(eye)
    purpose_dir   = Path(PurePath(*path_parts))
    workfile_name = orig_img_path.stem + f".{purpose}.{filetype}"
    workfile_path = purpose_dir.joinpath(workfile_name)
    if should_exist:
        if not purpose_dir.exists():
            scream(f"Directory {purpose_dir} not found.")
            exit()
        if not workfile_path.exists():
            shrug(f"Directory {purpose_dir} found, however")
            scream(f"the file {workfile_name} not found therein.")
            exit()
    else:
        if not purpose_dir.exists():
            purpose_dir.mkdir(parents=True, exist_ok=True)

    return workfile_path


def original_2_aux_file_path(original_file: Path | str, aux_extension: str):
    original_file = Path(original_file)
    return original_file.parent / (original_file.stem + aux_extension)
