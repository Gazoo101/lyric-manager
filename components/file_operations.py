# Python
import shutil
import os

# 3rd Party

# 1st Party

class FileOperations():

    @staticmethod
    def copy_and_rename(path_to_src, path_to_dst):
        ''' Helper function to copy and rename a single file.

        Args:
            path_to_src: Path to file which is to be copied and renamed.
            path_to_dst: Path to future file the src is to be copied and renamed to
        ''' 
        path_to_dst_dir = path_to_dst.parent

        path_to_src_copy_in_dst_dir = shutil.copy(path_to_src, path_to_dst_dir)
        os.rename(path_to_src_copy_in_dst_dir, path_to_dst)
