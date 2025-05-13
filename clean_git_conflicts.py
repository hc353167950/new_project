# -*- coding: utf-8 -*-
"""
清理CSV文件中的Git合并冲突标记

此脚本用于清理CSV文件中的Git合并冲突标记，保留'Updated upstream'部分的数据。
"""

import os
import glob

# 要处理的文件列表
files_to_clean = [
    "d:\\uiproject\\message\\data\\generated_ssq.csv",
    "d:\\uiproject\\message\\data\\generated_qxc.csv",
    "d:\\uiproject\\message\\data\\generated_dlt.csv"
]

def clean_git_conflicts(file_path):
    """
    清理文件中的Git合并冲突标记
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否进行了清理操作
    """
    print(f"正在处理文件: {file_path}")
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return False
    
    # 标记是否有冲突
    has_conflicts = False
    # 标记是否在冲突区域
    in_conflict = False
    # 标记是否在stashed changes区域
    in_stashed = False
    # 新的文件内容
    new_lines = []
    
    # 处理每一行
    for line in lines:
        # 检查是否是冲突开始标记
        if line.strip() == '<<<<<<< Updated upstream':
            has_conflicts = True
            in_conflict = True
            in_stashed = False
            continue  # 跳过此行
        
        # 检查是否是冲突分隔标记
        elif line.strip() == '=======':
            in_stashed = True
            continue  # 跳过此行
        
        # 检查是否是冲突结束标记
        elif line.strip() == '>>>>>>> Stashed changes':
            in_conflict = False
            in_stashed = False
            continue  # 跳过此行
        
        # 如果在stashed changes区域，跳过此行
        if in_stashed:
            continue
        
        # 保留非冲突行和upstream部分的行
        new_lines.append(line)
    
    # 如果有冲突，写回文件
    if has_conflicts:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"已成功清理文件: {file_path}")
            return True
        except Exception as e:
            print(f"写入文件 {file_path} 时出错: {e}")
            return False
    else:
        print(f"文件 {file_path} 没有Git合并冲突标记")
        return False

def main():
    """
    主函数
    """
    print("开始清理CSV文件中的Git合并冲突标记...")
    
    cleaned_files = 0
    
    # 处理指定的文件
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            if clean_git_conflicts(file_path):
                cleaned_files += 1
        else:
            print(f"文件不存在: {file_path}")
    
    print(f"清理完成，共处理了 {cleaned_files} 个文件")

if __name__ == "__main__":
    main()