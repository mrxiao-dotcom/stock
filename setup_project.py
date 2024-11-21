import os
import shutil

def setup_project():
    # 要创建的目录结构
    directories = [
        'app',
        'app/routes',
        'app/services',
        'config',
        'scripts',
        'utils',
        'static',
        'templates',
        'logs'
    ]

    # 创建目录
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")

    # 要移动的文件
    files_to_move = {
        'imigrate.py': 'scripts/imigrate.py',
        'init_database.py': 'scripts/init_database.py',
        'data_updater.py': 'app/services/data_updater.py',
        'sector_updater.py': 'app/services/sector_updater.py',
    }

    # 移动文件
    for src, dst in files_to_move.items():
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"移动文件: {src} -> {dst}")
        else:
            print(f"警告: 文件不存在 {src}")

    # 要保留的文件（在根目录）
    files_to_keep = {
        'requirements.txt',
        'README.md',
        'run.py',
        'setup_project.py'
    }

    # 删除根目录下所有其他文件
    for file in os.listdir('.'):
        if os.path.isfile(file) and file not in files_to_keep:
            try:
                os.remove(file)
                print(f"删除文件: {file}")
            except Exception as e:
                print(f"无法删除文件 {file}: {str(e)}")

    print("\n保留的文件:")
    for file in files_to_keep:
        if os.path.exists(file):
            print(f"- {file}")
        else:
            print(f"警告: 文件不存在 {file}")

if __name__ == "__main__":
    try:
        print("开始重组项目结构...")
        setup_project()
        print("\n项目重组完成!")
    except Exception as e:
        print(f"错误: {str(e)}") 