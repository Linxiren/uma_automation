from InquirerPy import inquirer
import os
import sys
import importlib.util

def get_config_path():
    """获取程序运行目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def ensure_config_exists():
    """确保config.json存在，如果不存在则创建默认配置"""
    config_dir = get_config_path()
    config_path = os.path.join(config_dir, 'config.json')
    
    if not os.path.exists(config_path):
        default_config = {
        "ADB_PATH": "E:\\leidian\\LDPlayer9\\adb.exe",
        "DEVICE_ID": "emulator-5554",
        "TARGET_EXE": "E:\\\u51ef\u65cb\u95e8\u9ed1\u677f\\UmaAi\u795e\u7ecf\u7f51\u7edc\u7248\uff08Nvidia\u663e\u5361\u4e13\u5c5e\uff09.exe",
        "schedule_action": "\u547c\u51fa\u8d5b\u7a0b\u4e00",
        "five_choice_one_action": "\u76ee\u6807\u9009\u62e9\u4e8c",
        "normal_scores": {"\u901f\u8bad\u7ec3": 0, "\u8010\u8bad\u7ec3": 0, "\u529b\u8bad\u7ec3": 0, "\u6839\u8bad\u7ec3": -20, "\u667a\u8bad\u7ec3": -50, "SS\u8bad\u7ec3": 0, "\u4f11\u606f": 0, "\u53cb\u4eba\u51fa\u884c": 0, "\u5355\u72ec\u51fa\u884c": 0, "\u6bd4\u8d5b": 0},
        "ss_scores": {"\u901f\u8bad\u7ec3": 0, "\u8010\u8bad\u7ec3": 0, "\u529b\u8bad\u7ec3": 0, "\u6839\u8bad\u7ec3": -20, "\u667a\u8bad\u7ec3": 240, "SS\u8bad\u7ec3": 320, "\u4f11\u606f": 160, "\u53cb\u4eba\u51fa\u884c": 400, "\u5355\u72ec\u51fa\u884c": 0, "\u6bd4\u8d5b": 0},
        "summer1_scores": {"\u901f\u8bad\u7ec3": 0, "\u8010\u8bad\u7ec3": 0, "\u529b\u8bad\u7ec3": 0, "\u6839\u8bad\u7ec3": -35, "\u667a\u8bad\u7ec3": -90, "SS\u8bad\u7ec3": 0, "\u4f11\u606f": 0, "\u53cb\u4eba\u51fa\u884c": 0, "\u5355\u72ec\u51fa\u884c": 0, "\u6bd4\u8d5b": 0, "\u8fdc\u5f81\u901f": 0, "\u8fdc\u5f81\u8010": 0, "\u8fdc\u5f81\u529b": 0, "\u8fdc\u5f81\u6839": -35, "\u8fdc\u5f81\u667a": -60},
        "summer2_scores": {"\u901f\u8bad\u7ec3": 0, "\u8010\u8bad\u7ec3": 0, "\u529b\u8bad\u7ec3": 0, "\u6839\u8bad\u7ec3": -35, "\u667a\u8bad\u7ec3": -80, "SS\u8bad\u7ec3": 0, "\u4f11\u606f": -50, "\u53cb\u4eba\u51fa\u884c": 0, "\u5355\u72ec\u51fa\u884c": 0, "\u6bd4\u8d5b": 0, "\u8fdc\u5f81\u901f": 0, "\u8fdc\u5f81\u8010": 0, "\u8fdc\u5f81\u529b": 0, "\u8fdc\u5f81\u6839": -45, "\u8fdc\u5f81\u667a": -100, "\u4f53\u901f": 0, "\u4f53\u8010": 0, "\u4f53\u529b": 0, "\u4f53\u6839": 0, "\u4f53\u667a": 0, "\u8fdc\u5f81\u4f53\u901f": 0, "\u8fdc\u5f81\u4f53\u8010": 0, "\u8fdc\u5f81\u4f53\u529b": 0, "\u8fdc\u5f81\u4f53\u6839": -20, "\u8fdc\u5f81\u4f53\u667a": -180},
        "run_styles": {"\u9003": [43], "\u5148": [39, 63], "\u5dee": [], "\u8ffd": []}
        }
        import json
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"创建配置文件失败: {str(e)}")
            input("按任意键退出...")
            sys.exit(1)

def run_script(script_name):
    """导入并运行指定的脚本"""
    try:
        # 获取完整路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        script_path = os.path.join(base_path, script_name)
        
        # 设置配置文件路径
        os.environ['CONFIG_PATH'] = os.path.join(get_config_path(), 'config.json')
        
        # 导入并运行模块
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 如果模块有main函数则运行
        if hasattr(module, 'main'):
            module.main()
            
    except Exception as e:
        print(f"运行 {script_name} 时发生错误: {str(e)}")
        input("按任意键继续...")


def run_adb_and_jt():
    run_script('adb_control.py')
    run_script('jt.py')

def run_gui():
    run_script('gui.py')

def main():
    ensure_config_exists()

    while True:
        try:
            menu_choice = inquirer.select(
                message="菜单(用↑和↓切换选项，回车确认，ctrl+c停止):",
                choices=["启动", "设置", "退出"],
            ).execute()

            if menu_choice == "启动":
                run_adb_and_jt()
            elif menu_choice == "设置":
                run_gui()
            elif menu_choice == "退出":
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n程序已停止")
            sys.exit(0)
        except Exception as e:
            print(f"发生错误: {str(e)}")
            input("按任意键继续...")

if __name__ == '__main__':
    main()