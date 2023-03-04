# Python
import shutil
import os
from pathlib import Path

# 3rd Party

# 1st Party

class FileOperations():

    @staticmethod
    def copy_and_rename(path_to_src: Path, path_to_dst: Path):
        """ Helper function to copy and rename a single file.

        Args:
            path_to_src: Path to file which is to be copied and renamed.
            path_to_dst: Path to future file the src is to be copied and renamed to
        """
        path_to_dst_dir = path_to_dst.parent

        path_to_src_copy_in_dst_dir = shutil.copy(path_to_src, path_to_dst_dir)
        os.rename(path_to_src_copy_in_dst_dir, path_to_dst)

    @staticmethod
    def read_utf8_string(path_to_file: Path) -> str:
        with open(path_to_file, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def write_utf8_string(path_to_file: Path, data: str):
        with open(path_to_file, 'w', encoding="utf-8") as file:
            file.write(data)
        