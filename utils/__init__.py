import hashlib
import os
import json


def calculate_file_hash(file_path):
    """计算文件内容的哈希值（MD5）"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # 分块读取避免内存占用过高
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def count_unique_files(folder_path):
    file_hashes = set()
    for root, _, files in os.walk(folder_path):  # 遍历文件夹及子文件夹
        for file in files:
            file_path = os.path.join(root, file)
            file_hashes.add(calculate_file_hash(file_path))
    return len(file_hashes)


def count_files(directory):
    result = {}
    total_files = 0

    for root, dirs, files in os.walk(directory):
        # 获取当前目录中的文件数
        file_count = len(files)
        # 记录当前目录的文件数
        relative_path = os.path.relpath(root, directory)
        if relative_path == ".":
            relative_path = "Root"
        result[relative_path] = file_count

    result = json.dumps(result, indent=4, ensure_ascii=False)
    return result, total_files
