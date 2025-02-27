import gradio as gr
import json
import os
import sys

def get_config_path():
    """获取配置文件路径"""
    return os.getenv('CONFIG_PATH', 'config.json')

def save_config(
    adb_path, device_id, target_exe, schedule_action, five_choice_one_action,
    normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
    normal_rest, normal_friend, normal_solo, normal_race,
    ss_speed, ss_stamina, ss_power, ss_guts, ss_wisdom, ss_ss,
    ss_rest, ss_friend, ss_solo, ss_race,
    summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
    summer1_rest, summer1_friend, summer1_solo, summer1_race,
    summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
    summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
    summer2_rest, summer2_friend, summer2_solo, summer2_race,
    summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
    summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
    summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
    run_style_escape, run_style_front, run_style_stalk, run_style_chase
):
    config = {
        "ADB_PATH": adb_path,
        "DEVICE_ID": device_id,
        "TARGET_EXE": target_exe,
        "schedule_action": schedule_action,
        "five_choice_one_action": five_choice_one_action,
        "normal_scores": {
            "速训练": normal_speed, "耐训练": normal_stamina, "力训练": normal_power,
            "根训练": normal_guts, "智训练": normal_wisdom, "SS训练": normal_ss,
            "休息": normal_rest, "友人出行": normal_friend, "单独出行": normal_solo,
            "比赛": normal_race
        },
        "ss_scores": {
            "速训练": ss_speed, "耐训练": ss_stamina, "力训练": ss_power,
            "根训练": ss_guts, "智训练": ss_wisdom, "SS训练": ss_ss,
            "休息": ss_rest, "友人出行": ss_friend, "单独出行": ss_solo,
            "比赛": ss_race
        },
        "summer1_scores": {
            "速训练": summer1_speed, "耐训练": summer1_stamina, "力训练": summer1_power,
            "根训练": summer1_guts, "智训练": summer1_wisdom, "SS训练": summer1_ss,
            "休息": summer1_rest, "友人出行": summer1_friend, "单独出行": summer1_solo,
            "比赛": summer1_race,
            "远征速": summer1_exp_speed, "远征耐": summer1_exp_stamina, "远征力": summer1_exp_power,
            "远征根": summer1_exp_guts, "远征智": summer1_exp_wisdom
        },
        "summer2_scores": {
            "速训练": summer2_speed, "耐训练": summer2_stamina, "力训练": summer2_power,
            "根训练": summer2_guts, "智训练": summer2_wisdom, "SS训练": summer2_ss,
            "休息": summer2_rest, "友人出行": summer2_friend, "单独出行": summer2_solo,
            "比赛": summer2_race,
            "远征速": summer2_exp_speed, "远征耐": summer2_exp_stamina, "远征力": summer2_exp_power,
            "远征根": summer2_exp_guts, "远征智": summer2_exp_wisdom,
            "体速": summer2_body_speed, "体耐": summer2_body_stamina, "体力": summer2_body_power,
            "体根": summer2_body_guts, "体智": summer2_body_wisdom,
            "远征体速": summer2_exp_body_speed, "远征体耐": summer2_exp_body_stamina,
            "远征体力": summer2_exp_body_power, "远征体根": summer2_exp_body_guts,
            "远征体智": summer2_exp_body_wisdom
        },
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
            
        normal = config.get("normal_scores", {})
        ss = config.get("ss_scores", {})
        summer1 = config.get("summer1_scores", {})
        summer2 = config.get("summer2_scores", {})
        
        return [
            config.get("ADB_PATH", ""),
            config.get("DEVICE_ID", ""),
            config.get("TARGET_EXE", ""),
            config.get("schedule_action", "呼出赛程一"),
            config.get("five_choice_one_action", "目标选择三"),
            # normal scores
            normal.get("速训练", 0), normal.get("耐训练", 0), normal.get("力训练", 0),
            normal.get("根训练", -20), normal.get("智训练", -50), normal.get("SS训练", 0),
            normal.get("休息", 0), normal.get("友人出行", 0), normal.get("单独出行", -60),
            normal.get("比赛", 0),
            # ss scores
            ss.get("速训练", 0), ss.get("耐训练", 0), ss.get("力训练", 0),
            ss.get("根训练", -20), ss.get("智训练", 240), ss.get("SS训练", 320),
            ss.get("休息", 160), ss.get("友人出行", 400), ss.get("单独出行", 0),
            ss.get("比赛", 0),
            # summer1 scores
            summer1.get("速训练", 0), summer1.get("耐训练", 0), summer1.get("力训练", 0),
            summer1.get("根训练", -35), summer1.get("智训练", -90), summer1.get("SS训练", 0),
            summer1.get("休息", 0), summer1.get("友人出行", 0), summer1.get("单独出行", 0),
            summer1.get("比赛", 0),
            summer1.get("远征速", 0), summer1.get("远征耐", 0), summer1.get("远征力", 0),
            summer1.get("远征根", -35), summer1.get("远征智", -60),
            # summer2 scores
            summer2.get("速训练", 0), summer2.get("耐训练", 0), summer2.get("力训练", 0),
            summer2.get("根训练", -35), summer2.get("智训练", -80), summer2.get("SS训练", 0),
            summer2.get("休息", -50), summer2.get("友人出行", 0), summer2.get("单独出行", 0),
            summer2.get("比赛", 0),
            summer2.get("远征速", 0), summer2.get("远征耐", 0), summer2.get("远征力", 0),
            summer2.get("远征根", -45), summer2.get("远征智", -100),
            summer2.get("体速", 0), summer2.get("体耐", 0), summer2.get("体力", 0),
            summer2.get("体根", 0), summer2.get("体智", 0),
            summer2.get("远征体速", 0), summer2.get("远征体耐", 0), summer2.get("远征体力", 0),
            summer2.get("远征体根", -20), summer2.get("远征体智", -180),
            # run styles
            ','.join(map(str, config.get("run_styles", {}).get("逃", []))),
            ','.join(map(str, config.get("run_styles", {}).get("先", []))),
            ','.join(map(str, config.get("run_styles", {}).get("差", []))),
            ','.join(map(str, config.get("run_styles", {}).get("追", [])))
        ]
    except FileNotFoundError:
        return [""] * 59  # 返回相应数量的空值

def create_number_box(label, value=0):
    return gr.Number(label=label, value=value)

with gr.Blocks() as demo:
    gr.Markdown("# 爱脚本设置（第一次打开后请务必保存设置。不管更改了什么，都请点击保存设置再关闭）")
    
    with gr.Row():
        adb_path = gr.Textbox(label="雷电九的adb位置（除非已经会了，否则请务必看使用说明.pdf）")
        device_id = gr.Textbox(label="模拟器设备号（正常来说填emulator-5554即可，但还是推荐先看使用说明.pdf）")
    
    target_exe = gr.Textbox(label="umaai的位置（除非已经会了，否则请务必看使用说明.pdf）")
    
    schedule_action = gr.Dropdown(
        choices=["呼出赛程一", "呼出赛程二", "呼出赛程三"],
        value="呼出赛程一",
        label="选择赛程呼出"
    )

    five_choice_one_action = gr.Dropdown(
        choices=["目标选择一", "目标选择二", "目标选择三", "目标选择四", "目标选择五"],
        value="目标选择三",
        label="经典年一月下目标选择"
    )
    
    with gr.Tabs():
        with gr.TabItem("调整平时训练分数"):
            with gr.Group():
                normal_speed = create_number_box("速训练")
                normal_stamina = create_number_box("耐训练")
                normal_power = create_number_box("力训练")
                normal_guts = create_number_box("根训练", -20)
                normal_wisdom = create_number_box("智训练", -50)
                normal_ss = create_number_box("SS训练")
                normal_rest = create_number_box("休息")
                normal_friend = create_number_box("友人出行")
                normal_solo = create_number_box("单独出行", -60)
                normal_race = create_number_box("比赛")
        
        with gr.TabItem("调整安田纪念与维多利亚一哩赛之间那一回合分数"):
            with gr.Group():
                ss_speed = create_number_box("速训练")
                ss_stamina = create_number_box("耐训练")
                ss_power = create_number_box("力训练")
                ss_guts = create_number_box("根训练", -20)
                ss_wisdom = create_number_box("智训练", 240)
                ss_ss = create_number_box("SS训练", 320)
                ss_rest = create_number_box("休息", 160)
                ss_friend = create_number_box("友人出行", 400)
                ss_solo = create_number_box("单独出行")
                ss_race = create_number_box("比赛")
        
        with gr.TabItem("调整第一次远征训练分数"):
            with gr.Group():
                summer1_speed = create_number_box("速训练")
                summer1_stamina = create_number_box("耐训练")
                summer1_power = create_number_box("力训练")
                summer1_guts = create_number_box("根训练", -35)
                summer1_wisdom = create_number_box("智训练", -90)
                summer1_ss = create_number_box("SS训练")
                summer1_rest = create_number_box("休息")
                summer1_friend = create_number_box("友人出行")
                summer1_solo = create_number_box("单独出行")
                summer1_race = create_number_box("比赛")
                summer1_exp_speed = create_number_box("远征速")
                summer1_exp_stamina = create_number_box("远征耐")
                summer1_exp_power = create_number_box("远征力")
                summer1_exp_guts = create_number_box("远征根", -35)
                summer1_exp_wisdom = create_number_box("远征智", -60)
        
        with gr.TabItem("调整第二次远征训练分数"):
            with gr.Group():
                summer2_speed = create_number_box("速训练")
                summer2_stamina = create_number_box("耐训练")
                summer2_power = create_number_box("力训练")
                summer2_guts = create_number_box("根训练", -35)
                summer2_wisdom = create_number_box("智训练", -80)
                summer2_ss = create_number_box("SS训练")
                summer2_rest = create_number_box("休息", -50)
                summer2_friend = create_number_box("友人出行")
                summer2_solo = create_number_box("单独出行")
                summer2_race = create_number_box("比赛")
                summer2_exp_speed = create_number_box("远征速")
                summer2_exp_stamina = create_number_box("远征耐")
                summer2_exp_power = create_number_box("远征力")
                summer2_exp_guts = create_number_box("远征根", -45)
                summer2_exp_wisdom = create_number_box("远征智", -100)
                summer2_body_speed = create_number_box("体速")
                summer2_body_stamina = create_number_box("体耐")
                summer2_body_power = create_number_box("体力")
                summer2_body_guts = create_number_box("体根")
                summer2_body_wisdom = create_number_box("体智")
                summer2_exp_body_speed = create_number_box("远征体速")
                summer2_exp_body_stamina = create_number_box("远征体耐")
                summer2_exp_body_power = create_number_box("远征体力")
                summer2_exp_body_guts = create_number_box("远征体根", -20)
                summer2_exp_body_wisdom = create_number_box("远征体智", -180)
    
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
            normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
            normal_rest, normal_friend, normal_solo, normal_race,
            ss_speed, ss_stamina, ss_power, ss_guts, ss_wisdom, ss_ss,
            ss_rest, ss_friend, ss_solo, ss_race,
            summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
            summer1_rest, summer1_friend, summer1_solo, summer1_race,
            summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
            summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
            summer2_rest, summer2_friend, summer2_solo, summer2_race,
            summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
            summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
            summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ],
        outputs=gr.Textbox(label="保存状态")
    )
    
    load_button.click(
        load_config,
        outputs=[
            adb_path, device_id, target_exe, schedule_action, five_choice_one_action,
            normal_speed, normal_stamina, normal_power, normal_guts, normal_wisdom, normal_ss,
            normal_rest, normal_friend, normal_solo, normal_race,
            ss_speed, ss_stamina, ss_power, ss_guts, ss_wisdom, ss_ss,
            ss_rest, ss_friend, ss_solo, ss_race,
            summer1_speed, summer1_stamina, summer1_power, summer1_guts, summer1_wisdom, summer1_ss,
            summer1_rest, summer1_friend, summer1_solo, summer1_race,
            summer1_exp_speed, summer1_exp_stamina, summer1_exp_power, summer1_exp_guts, summer1_exp_wisdom,
            summer2_speed, summer2_stamina, summer2_power, summer2_guts, summer2_wisdom, summer2_ss,
            summer2_rest, summer2_friend, summer2_solo, summer2_race,
            summer2_exp_speed, summer2_exp_stamina, summer2_exp_power, summer2_exp_guts, summer2_exp_wisdom,
            summer2_body_speed, summer2_body_stamina, summer2_body_power, summer2_body_guts, summer2_body_wisdom,
            summer2_exp_body_speed, summer2_exp_body_stamina, summer2_exp_body_power, summer2_exp_body_guts, summer2_exp_body_wisdom,
            run_style_escape, run_style_front, run_style_stalk, run_style_chase
        ]
    )

def main():
    # 启动界面时自动打开浏览器
    demo.launch(inbrowser=True)

if __name__ == '__main__':
    main()
