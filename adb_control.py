import os
import subprocess
import json

def run_adb_commands(adb_path):
    # 获取 ADB 的文件夹路径
    adb_dir = os.path.dirname(adb_path)
    
    # 构建命令列表
    commands = [
        f'"{adb_path}" kill-server',
        f'"{adb_path}" start-server'
    ]
    
    # 使用 subprocess 模块执行命令
    for command in commands:
        process = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=adb_dir)
        if process.returncode != 0:
            print(f"命令 '{command}' 执行失败: {process.stderr}")
        else:
            print(f"命令 '{command}' 执行成功: {process.stdout}")

def main():
    try:
        # 从配置文件中读取 ADB_PATH
        config_path = os.getenv('CONFIG_PATH', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        adb_path = config["ADB_PATH"]
        
        # 运行 ADB 命令
        run_adb_commands(adb_path)
    except Exception as e:
        print(f"ADB 控制异常: {str(e)}")
        input("按任意键继续...")

if __name__ == "__main__":
    main()