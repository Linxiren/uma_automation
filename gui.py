import gradio as gr
import json
import os
import sys

def get_config_path():
    """获取配置文件路径"""
    return os.getenv('CONFIG_PATH', 'config.json')

def save_config(
    adb_path, device_id, target_exe, schedule_action, five_choice_one_action,
    normal_scores, ss_scores, summer1_scores, summer2_scores,
    run_style_escape, run_style_front, run_style_stalk, run_style_chase
):
    config = {
        "ADB_PATH": adb_path,
        "DEVICE_ID": device_id,
        "TARGET_EXE": target_exe,
        "schedule_action": schedule_action,
        "five_choice_one_action": five_choice_one_action,
        "normal_scores": normal_scores,
        "ss_scores": ss_scores,
        "summer1_scores": summer1_scores,
        "summer2_scores": summer2_scores,
        "run_styles": {
            "逃": list(map(int, run_style_escape.split(','))) if run_style_escape else [],
            "先": list(map(int, run_style_front.split(','))) if run_style_front else [],
            "差": list(map(int, run_style_stalk.split(','))) if run_style_stalk else [],
            "追": list(map(int, run_style_chase.split(','))) if run_style_chase else [],
        }
    }
    with open(get_config_path(), 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return "设置已保存"

def load_config():
    try:
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
        return (
            config.get("ADB_PATH", ""),
            config.get("DEVICE_ID", ""),
            config.get("TARGET_EXE", ""),
            config.get("schedule_action", "呼出赛程一"),
            config.get("five_choice_one_action", "目标选择二"),
            config.get("normal_scores", {}),
            config.get("ss_scores", {}),
            config.get("summer1_scores", {}),
            config.get("summer2_scores", {}),
            ','.join(map(str, config.get("run_styles", {}).get("逃", []))),
            ','.join(map(str, config.get("run_styles", {}).get("先", []))),
            ','.join(map(str, config.get("run_styles", {}).get("差", []))),
            ','.join(map(str, config.get("run_styles", {}).get("追", [])))
        )
    except FileNotFoundError:
        return "", "", "", "呼出赛程一", {}, {}, {}, {}, "", "", "", ""

with gr.Blocks() as demo:
    gr.Markdown("# 爱脚本设置")
    
    with gr.Row():
        adb_path = gr.Textbox(label="雷电九的adb位置")
        device_id = gr.Textbox(label="模拟器设备号")
    
    target_exe = gr.Textbox(label="umaai的位置")
    
    schedule_action = gr.Dropdown(
        choices=["呼出赛程一", "呼出赛程二", "呼出赛程三"],
        value="呼出赛程一",
        label="选择赛程呼出"
    )

    five_choice_one_action = gr.Dropdown(
        choices=["目标选择一", "目标选择二", "目标选择三", "目标选择四", "目标选择五"],
        value="目标选择二",
        label="经典年一月下目标选择"
    )
    
    with gr.Tabs():
        with gr.TabItem("调整平时训练分数"):
            normal_scores = gr.JSON(label="平时训练分数配置", value={
                "速训练": 0, "耐训练": 0, "力训练": 0, "根训练": -20, "智训练": -50, "SS训练": 0,
                "休息": 0, "友人出行": 0, "单独出行": 0, "比赛": 0
            })
        
        with gr.TabItem("调整安田纪念与维多利亚一哩赛之间那一回合分数"):
            ss_scores = gr.JSON(label="安田纪念与维多利亚一哩赛分数配置", value={
                "速训练": 0, "耐训练": 0, "力训练": 0, "根训练": -20, "智训练": 240, "SS训练": 320,
                "休息": 160, "友人出行": 400, "单独出行": 0, "比赛": 0
            })
        
        with gr.TabItem("调整第一次远征训练分数"):
            summer1_scores = gr.JSON(label="第一次远征训练分数配置", value={
                "速训练": 0, "耐训练": 0, "力训练": 0, "根训练": -35, "智训练": -90, "SS训练": 0,
                "休息": 0, "友人出行": 0, "单独出行": 0, "比赛": 0, "远征速": 0, "远征耐": 0,
                "远征力": 0, "远征根": -35, "远征智": -60
            })
        
        with gr.TabItem("调整第二次远征训练分数"):
            summer2_scores = gr.JSON(label="第二次远征训练分数配置", value={
                "速训练": 0, "耐训练": 0, "力训练": 0, "根训练": -35, "智训练": -80, "SS训练": 0,
                "休息": -50, "友人出行": 0, "单独出行": 0, "比赛": 0, "远征速": 0, "远征耐": 0,
                "远征力": 0, "远征根": -45, "远征智": -100, "体速": 0, "体耐": 0, "体力": 0,
                "体根": 0, "体智": 0, "远征体速": 0, "远征体耐": 0, "远征体力": 0, "远征体根": -20,
                "远征体智": -180
            })
    
    with gr.Row():
        run_style_escape = gr.Textbox(label="逃跑法回合数")
        run_style_front = gr.Textbox(label="先跑法回合数")
        run_style_stalk = gr.Textbox(label="差跑法回合数")
        run_style_chase = gr.Textbox(label="追跑法回合数")
    
    save_button = gr.Button("保存设置")
    load_button = gr.Button("加载设置")
    
    save_button.click(
        save_config,
        inputs=[
            adb_path, device_id, target_exe, schedule_action, five_choice_one_action,
            normal_scores, ss_scores, summer1_scores, summer2_scores,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ],
        outputs=gr.Textbox(label="保存状态")
    )
    
    load_button.click(
        load_config,
        outputs=[
            adb_path, device_id, target_exe, schedule_action, five_choice_one_action,
            normal_scores, ss_scores, summer1_scores, summer2_scores,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ]
    )

demo.launch()

def main():
    demo.launch()

if __name__ == '__main__':
    main()