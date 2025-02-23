import psutil
from scapy.all import *
import binascii
import json
import subprocess
from time import sleep
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import cv2
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.getenv('CONFIG_PATH', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 雷电模拟器adb配置
ADB_PATH = config["ADB_PATH"]
DEVICE_ID = config["DEVICE_ID"]

# 按钮坐标配置（720x1280分辨率）
BUTTONS = {
    '训练': (365, 945),
    '速': (60, 1040),
    '耐': (180, 1040),
    '力': (300, 1040),
    '根': (420, 1040),
    '智': (540, 1040),
    'SS': (660, 1040),
    '休息': (125, 945),
    '出行': (280, 1175),
    '比赛': (610, 1175),
    '参赛行程表': (610, 1080),
    '赛程表一': (610, 570),
    '赛程表二': (610, 790),
    '赛程表三': (610, 1000),
    '关闭': (360, 1210),
    '国外资质': (450, 1175),
    '友人':(350, 395),
    '担当':(350, 645),
    '确认参赛':(530, 885),
    '远征_确认参赛':(530, 1180),
    '观看结果':(240, 1205),
    '继续':(470, 1205),
    '确认':(360, 1100),
    '远征_根':(250, 100),
    '远征_耐':(470, 100),
    '远征_力':(135, 250),
    '远征_速':(360, 250),
    '远征_智':(590, 250),
    '远征_技能点':(135, 380),
    '远征_体力':(360, 380),
    '远征_友情':(590, 380),
    '远征_金克斯':(250, 510),
    '远征_连霸':(470, 510),
    '远征_升级':(510, 720),
    '返回':(60, 1250),
    '选择一':(50, 830),
    '选择二':(50, 720),
    '选择三':(50, 610),
    '选择四':(50, 500),
    '选择五':(50, 390),
    '目标竞赛':(530, 840),
    '打开选单':(650, 1230),
    '放弃':(550, 550),
    '确认放弃':(550, 860),
    '逃':(600, 750),
    '先':(440, 750),
    '差':(280, 750),
    '追':(140, 750),
}

# 配置参数
TARGET_EXE = config["TARGET_EXE"]
FIXED_DST_PORT = 4693
HEARTBEAT_MAX_LEN = 60

# 全局变量
target_ports = set()
executor = ThreadPoolExecutor(max_workers=4)
packet_buffer = asyncio.Queue()
processing = True
current_round = 0
best_action = None
lock = threading.Lock()
screenshot = None
loop = None

def adb_click(x, y, delay=0.8):
    cmd = f'"{ADB_PATH}" -s {DEVICE_ID} shell input tap {x} {y}'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"点击成功: ({x}, {y})")
        else:
            print(f"点击失败: {result.stderr}")
    except Exception as e:
        print(f"命令执行异常: {str(e)}")
    sleep(delay)

def perform_action(action_name):
    """执行完整的操作流程"""
    print(f"执行操作: {action_name}")
    
    actions = {
        "速训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(0.5)],
        "耐训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(0.5)],
        "力训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(0.5)],
        "根训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(0.5)],
        "智训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(0.5)],
        "SS训练": lambda: [adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['SS']), adb_click(*BUTTONS['SS']), sleep(0.5)],
        "休息": lambda: [adb_click(*BUTTONS['休息']), sleep(0.5)],
        "友人出行": lambda: [adb_click(*BUTTONS['出行']), adb_click(*BUTTONS['友人']), sleep(0.5)],
        "单独出行": lambda: [adb_click(*BUTTONS['出行']), adb_click(*BUTTONS['担当']), sleep(0.5)],
        "比赛": lambda: [adb_click(*BUTTONS['比赛']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "随机事件选择": lambda: [adb_click(*BUTTONS['选择二']), sleep(0.5)],
        "特殊事件选择": lambda: [adb_click(*BUTTONS['选择一']), sleep(0.5)],
        "出行事件选择": lambda: [adb_click(*BUTTONS['选择三']), sleep(0.5)],
        "目标选择一": lambda: [adb_click(*BUTTONS['选择五']), sleep(0.5)],
        "目标选择二": lambda: [adb_click(*BUTTONS['选择四']), sleep(0.5)],
        "目标选择三": lambda: [adb_click(*BUTTONS['选择三']), sleep(0.5)],
        "目标选择四": lambda: [adb_click(*BUTTONS['选择二']), sleep(0.5)],
        "目标选择五": lambda: [adb_click(*BUTTONS['选择一']), sleep(0.5)],
        "继承": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5)],
        "用闹钟": lambda: [adb_click(*BUTTONS['观看结果']), adb_click(*BUTTONS['继续']), adb_click(*BUTTONS['观看结果']), sleep(2), adb_click(*BUTTONS['观看结果']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "赛前点适性": lambda: [adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "呼出赛程一": lambda: [adb_click(*BUTTONS['比赛']), adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['赛程表一']), adb_click(*BUTTONS['关闭']), sleep(0.5), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "呼出赛程二": lambda: [adb_click(*BUTTONS['比赛']), adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['赛程表二']), adb_click(*BUTTONS['关闭']), sleep(0.5), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "呼出赛程三": lambda: [adb_click(*BUTTONS['比赛']), adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['赛程表三']), adb_click(*BUTTONS['关闭']), sleep(0.5), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "新人赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "开始比赛": lambda: [adb_click(*BUTTONS['观看结果']), sleep(4), adb_click(*BUTTONS['返回']), sleep(2), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "比赛结束": lambda: [adb_click(*BUTTONS['继续']), sleep(2), adb_click(*BUTTONS['继续']), sleep(0.5)],
        "比赛结束补": lambda: [adb_click(*BUTTONS['继续'])],
        "凯旋门失败": lambda: [adb_click(*BUTTONS['观看结果']), adb_click(*BUTTONS['继续']), sleep(2), adb_click(*BUTTONS['继续']), sleep(0.5)],
        "目标达成": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5)],
        "赛程赛": lambda: [adb_click(*BUTTONS['目标竞赛']), adb_click(*BUTTONS['目标竞赛']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "海外赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['远征_确认参赛']), sleep(0.5)],
        "确认补": lambda: [adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛'])],
        "海外确认参赛补": lambda: [adb_click(*BUTTONS['远征_确认参赛']), sleep(8), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回'])],
        "凯旋门": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['远征_确认参赛']), sleep(8), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回'])],
        "目标赛": lambda: [adb_click(*BUTTONS['确认']), sleep(1), adb_click(*BUTTONS['确认']), sleep(0.5), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "技能点适性": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_技能点']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "远征速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(0.5)],
        "远征耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(0.5)],
        "远征力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(0.5)],
        "远征根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(0.5)],
        "远征智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_智']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(0.5)],
        "体速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(0.5)],
        "体耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(0.5)],
        "体力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(0.5)],
        "体根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(0.5)],
        "体智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(0.5)],
        "远征体速": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['速']), adb_click(*BUTTONS['速']), sleep(0.5)],
        "远征体耐": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_耐']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['耐']), adb_click(*BUTTONS['耐']), sleep(0.5)],
        "远征体力": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['力']), adb_click(*BUTTONS['力']), sleep(0.5)],
        "远征体根": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_根']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['根']), adb_click(*BUTTONS['根']), sleep(0.5)],
        "远征体智": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_智']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1.5), adb_click(*BUTTONS['训练']), adb_click(*BUTTONS['智']), adb_click(*BUTTONS['智']), sleep(0.5)],
        "友情适性": lambda: [adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_友情']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "友情适性检查": lambda: [adb_click(*BUTTONS['国外资质']), adb_click(*BUTTONS['远征_友情']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(0.5)],
        "初次凯旋门适性检查": lambda: [adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['远征_技能点']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_智']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_速']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1)],
        "凯旋门适性检查": lambda: [adb_click(*BUTTONS['参赛行程表']), adb_click(*BUTTONS['远征_金克斯']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_连霸']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_技能点']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['远征_体力']), adb_click(*BUTTONS['远征_升级']), adb_click(*BUTTONS['确认']), adb_click(*BUTTONS['远征_确认参赛']), sleep(4), adb_click(*BUTTONS['返回']), adb_click(*BUTTONS['返回']), sleep(1)],
        "跑法改逃": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改先": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['先']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改差": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['差']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
        "跑法改追": lambda: [adb_click(*BUTTONS['逃']), adb_click(*BUTTONS['追']), adb_click(*BUTTONS['确认参赛']), sleep(0.5)],
    }
    
    if action := actions.get(action_name):
        action()
    else:
        print(f"未知的操作: {action_name}")

def parse_umaai_data(parameters):
    global current_round, best_action
    scores = {
        "回合数": float(parameters[1]),
        "速训练": float(parameters[6]) + config["normal_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["normal_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["normal_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["normal_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["normal_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["normal_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["normal_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["normal_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["normal_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["normal_scores"]["比赛"]
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_umaai_data_ss(parameters):
    global current_round, best_action
    scores = {
        "回合数": float(parameters[1]),
        "速训练": float(parameters[6]) + config["ss_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["ss_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["ss_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["ss_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["ss_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["ss_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["ss_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["ss_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["ss_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["ss_scores"]["比赛"]
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_umaai_data_summer1(parameters):
    global current_round, best_action
    scores = {
        "回合数": float(parameters[1]),
        "速训练": float(parameters[6]) + config["summer1_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["summer1_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["summer1_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["summer1_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["summer1_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["summer1_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["summer1_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["summer1_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["summer1_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["summer1_scores"]["比赛"],
        "远征速": float(parameters[16]) + config["summer1_scores"].get("远征速", 0),
        "远征耐": float(parameters[17]) + config["summer1_scores"].get("远征耐", 0),
        "远征力": float(parameters[18]) + config["summer1_scores"].get("远征力", 0),
        "远征根": float(parameters[19]) + config["summer1_scores"].get("远征根", 0),
        "远征智": float(parameters[20]) + config["summer1_scores"].get("远征智", 0),
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action

def parse_umaai_data_summer2(parameters):
    global current_round, best_action
    scores = {
        "回合数": float(parameters[1]),
        "速训练": float(parameters[6]) + config["summer2_scores"]["速训练"],
        "耐训练": float(parameters[7]) + config["summer2_scores"]["耐训练"],
        "力训练": float(parameters[8]) + config["summer2_scores"]["力训练"],
        "根训练": float(parameters[9]) + config["summer2_scores"]["根训练"],
        "智训练": float(parameters[10]) + config["summer2_scores"]["智训练"],
        "SS训练": float(parameters[11]) + config["summer2_scores"]["SS训练"],
        "休息": float(parameters[12]) + config["summer2_scores"]["休息"],
        "友人出行": float(parameters[13]) + config["summer2_scores"]["友人出行"],
        "单独出行": float(parameters[14]) + config["summer2_scores"]["单独出行"],
        "比赛": float(parameters[15]) + config["summer2_scores"]["比赛"],
        "远征速": float(parameters[16]) + config["summer2_scores"].get("远征速", 0),
        "远征耐": float(parameters[17]) + config["summer2_scores"].get("远征耐", 0),
        "远征力": float(parameters[18]) + config["summer2_scores"].get("远征力", 0),
        "远征根": float(parameters[19]) + config["summer2_scores"].get("远征根", 0),
        "远征智": float(parameters[20]) + config["summer2_scores"].get("远征智", 0),
        "体速": float(parameters[26]) + config["summer2_scores"].get("体速", 0),
        "体耐": float(parameters[27]) + config["summer2_scores"].get("体耐", 0),
        "体力": float(parameters[28]) + config["summer2_scores"].get("体力", 0),
        "体根": float(parameters[29]) + config["summer2_scores"].get("体根", 0),
        "体智": float(parameters[30]) + config["summer2_scores"].get("体智", 0),
        "远征体速": float(parameters[36]) + config["summer2_scores"].get("远征体速", 0),
        "远征体耐": float(parameters[37]) + config["summer2_scores"].get("远征体耐", 0),
        "远征体力": float(parameters[38]) + config["summer2_scores"].get("远征体力", 0),
        "远征体根": float(parameters[39]) + config["summer2_scores"].get("远征体根", 0),
        "远征体智": float(parameters[40]) + config["summer2_scores"].get("远征体智", 0),
    }

    current_round = int(scores["回合数"])
    best_action = max(scores, key=scores.get)
    print(f"当前回合: {current_round}, 建议操作: {best_action} (分数: {scores[best_action]})")
    return best_action


def get_target_ports_once():
    """启动时一次性获取目标端口"""
    global target_ports
    for conn in psutil.net_connections(kind='tcp'):
        if conn.status == 'ESTABLISHED' and conn.pid:
            try:
                process = psutil.Process(conn.pid)
                if process.exe() == TARGET_EXE:
                    target_ports.add(conn.laddr.port)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    print("爱脚本启动成功，如有问题请找作者QQ2269430789(小力)")
    print(f"初始目标端口: {target_ports}")

def websocket_decrypt(raw_data):
    """解密函数"""
    try:
        # 快速检查数据有效性
        if len(raw_data) < 16:  # 至少需要8字节
            return None
            
        # 直接处理二进制数据，跳过hex转换
        mask_key = raw_data[4:8]
        masked_payload = raw_data[8:]
        
        # 使用列表推导式优化解密过程
        decrypted = bytes(b ^ mask_key[i % 4] for i, b in enumerate(masked_payload))
        return decrypted.decode('utf-8', 'ignore')
    except Exception as e:
        print(f"解密异常: {str(e)}")
        return None

async def process_packet_queue():
    """异步处理数据包队列"""
    while processing:
        try:
            packet_data = await packet_buffer.get()
            if "PrintUmaAiResult" in packet_data:
                data = json.loads(packet_data)
                params = data["Parameters"][0].split()
                params = [float(p) if not p.startswith('-') and p.replace('.', '', 1).isdigit() else 0.0 
                         for p in params]
                
                if current_round >= 58 and len(params) >= 30:
                    parse_umaai_data_summer2(params)

                elif current_round >= 35 and current_round <= 41 and len(params) >= 25:
                    parse_umaai_data_summer1(params)

                elif len(params) >= 14 and current_round == 56:
                    parse_umaai_data_ss(params)

                elif len(params) >= 14:
                    parse_umaai_data(params)
            
            packet_buffer.task_done()
        except Exception as e:
            print(f"处理包异常: {str(e)}")

def init_async():
    """初始化异步相关内容"""
    global loop, packet_buffer
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 创建异步队列
    packet_buffer = asyncio.Queue()
    
    # 启动异步处理队列
    loop.create_task(process_packet_queue())
    
    # 在新线程中启动事件循环
    thread = threading.Thread(target=run_event_loop, daemon=True)
    thread.start()
    
    return thread

def run_event_loop():
    """在线程中运行事件循环"""
    global loop
    try:
        loop.run_forever()
    except Exception as e:
        print(f"事件循环异常: {str(e)}")
    finally:
        loop.close()

def packet_callback(packet):
    """数据包回调函数"""
    global loop
    try:
        if not packet.haslayer(TCP):
            return
            
        # 快速过滤
        if packet[TCP].dport != FIXED_DST_PORT or packet[TCP].sport not in target_ports:
            return
            
        # 检查是否有负载
        if not packet.haslayer(Raw):
            return
            
        payload = bytes(packet[Raw])
        if len(payload) < HEARTBEAT_MAX_LEN:
            return
            
        if result := websocket_decrypt(payload):
            if loop and not loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(packet_buffer.put(result), loop)
                future.result()  # 等待结果，确保数据被放入队列
            else:
                print("事件循环未运行或已关闭")
            
    except Exception as e:
        print(f"回调异常: {str(e)}")

def start_capture():
    """抓包函数"""
    print("启动高速流量监控...")
    
    # 设置BPF过滤器，在抓包层面就过滤
    filter_str = f"tcp and dst port {FIXED_DST_PORT} and ("
    filter_str += " or ".join(f"src port {port}" for port in target_ports)
    filter_str += ")"
    
    # 使用AsyncSniffer进行异步抓包
    sniffer = AsyncSniffer(
        iface=r'\Device\NPF_Loopback',
        filter=filter_str,
        prn=packet_callback,
        store=0  # 不保存包，减少内存使用
    )
    
    return sniffer

def capture_screenshot():
    """使用ADB截图并返回截图数据"""
    try:
        cmd = [
            ADB_PATH,
            '-s', DEVICE_ID,
            'exec-out', 'screencap', '-p'
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        nparr = np.frombuffer(result.stdout, np.uint8)
        screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        print(f"正在检测状态")
        return screenshot
    
    except subprocess.CalledProcessError as e:
        print(f"截图失败：{e.stderr.decode('utf-8')}")
        return None
    except Exception as e:
        print(f"发生未知错误：{str(e)}")
        return None

def check_game_state():
    """检查游戏状态"""
    global best_action, screenshot
    while True:
        with lock:
            screenshot = capture_screenshot()

        if screenshot is None:
            sleep(1)
            continue
        
        # 预加载所有图片
        images = {
            'lace_lose_img': cv2.imread(os.path.join(current_dir, 'picture/0.png')),
            'event_choice_img': cv2.imread(os.path.join(current_dir, 'picture/1.png')),
            'event_choice1_img': cv2.imread(os.path.join(current_dir, 'picture/13.png')),
            'five_choice_one_img': cv2.imread(os.path.join(current_dir, 'picture/2.png')),
            'greenhat_ask_img': cv2.imread(os.path.join(current_dir, 'picture/3.png')),
            'lace_tips_img': cv2.imread(os.path.join(current_dir, 'picture/4.png')),
            'object_lace_img': cv2.imread(os.path.join(current_dir, 'picture/5.png')),
            'communicate_lace_img': cv2.imread(os.path.join(current_dir, 'picture/6.png')),
            'training_img': cv2.imread(os.path.join(current_dir, 'picture/7.png')),
            'kaigai_training_img': cv2.imread(os.path.join(current_dir, 'picture/8.png')),
            'beats_img': cv2.imread(os.path.join(current_dir, 'picture/9.png')),
            'trip_img': cv2.imread(os.path.join(current_dir, 'picture/10.png')),
            'none_img': cv2.imread(os.path.join(current_dir, 'picture/11.png')),
            'continue_img': cv2.imread(os.path.join(current_dir, 'picture/12.png')),
            'before_lace_img': cv2.imread(os.path.join(current_dir, 'picture/14.png')),
            'clock_img': cv2.imread(os.path.join(current_dir, 'picture/15.png')),
            'lace_over1_img': cv2.imread(os.path.join(current_dir, 'picture/16.png')),
            'lace_over2_img': cv2.imread(os.path.join(current_dir, 'picture/17.png')),
            'lace_over3_img': cv2.imread(os.path.join(current_dir, 'picture/18.png')),
            'lace_over4_img': cv2.imread(os.path.join(current_dir, 'picture/19.png')),
            'add_training_img': cv2.imread(os.path.join(current_dir, 'picture/20.png')),
            'lace_confirm_img': cv2.imread(os.path.join(current_dir, 'picture/21.png')),
            'lace_kaigai_confirm_img': cv2.imread(os.path.join(current_dir, 'picture/22.png'))
        }

        # 定义所有ROI
        rois = {
            'lace_lose_roi': screenshot[1136:1226, 63:353],
            'event_choice_roi': screenshot[81:130, 615:700],
            'five_choice_one_roi': screenshot[198:328, 0:600],
            'greenhat_ask_roi': screenshot[200:287, 0:720],
            'lace_tips_roi': screenshot[388:588, 9:709],
            'object_lace_roi': screenshot[1030:1130, 74:169],
            'communicate_lace_roi': screenshot[1046:1123, 524:671],
            'training_roi': screenshot[938:1044, 70:170],
            'kaigai_training_roi': screenshot[937:1045, 70:165],
            'beats_roi': screenshot[1025:1077, 266:451],
            'trip_roi': screenshot[199:449, 1:711],
            'none_roi': screenshot[1195:1271, 522:580],
            'continue_roi': screenshot[1085:1137, 219:502],
            'before_lace_roi': screenshot[1140:1213, 175:335],
            'clock_roi': screenshot[1120:1280, 0:720],
            'lace_over1_roi': screenshot[1130:1280, 360:720],
            'lace_over2_roi': screenshot[1205:1280, 0:720],
            'lace_over3_roi': screenshot[699:899, 0:720],
            'add_training_roi': screenshot[235:285, 110:552],
            'lace_confirm_roi': screenshot[1038:1138, 1:511],
            'lace_kaigai_confirm_roi': screenshot[1130:1230, 0:720]
        }
        
        if screenshot is not None:
            if current_round == 22 and match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                perform_action("赛前点适性")
                sleep(2)
                if config["schedule_action"] == "呼出赛程二":
                    perform_action("呼出赛程二")
                elif config["schedule_action"] == "呼出赛程三":
                    perform_action("呼出赛程三")
                else:
                    perform_action("呼出赛程一")
                best_action = None
            elif current_round == 41 and match_template(rois['kaigai_training_roi'], images['kaigai_training_img']) and best_action is not None:
                perform_action("友情适性")
                sleep(2)
                executor.submit(perform_action, best_action)
                best_action = None
            elif current_round == 48 and match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                perform_action("友情适性检查")
                sleep(2)
                executor.submit(perform_action, best_action)
                best_action = None
            elif current_round == 41 and match_template(rois['object_lace_roi'], images['object_lace_img']):
                    print("检测到初次凯旋门")
                    perform_action("初次凯旋门适性检查")
                    perform_action("海外赛")
            elif current_round == 65 and match_template(rois['object_lace_roi'], images['object_lace_img']):
                    print("检测到最终凯旋门")
                    perform_action("凯旋门适性检查")
                    perform_action("凯旋门")
            elif (match_template(rois['event_choice_roi'], images['event_choice_img']) and match_template(rois['none_roi'], images['none_img'])) or (match_template(rois['event_choice_roi'], images['event_choice1_img']) and match_template(rois['none_roi'], images['none_img'])):
                sleep(3)
                screenshot = capture_screenshot()
                rois['five_choice_one_roi'] = screenshot[198:328, 0:600]  # 更新ROI
                rois['greenhat_ask_roi'] = screenshot[200:287, 0:720]
                rois['trip_roi'] = screenshot[199:449, 1:711]
                rois['event_choice_roi'] = screenshot[81:130, 615:700]
                rois['none_roi'] = screenshot[1195:1271, 522:580]
                rois['add_training_roi'] = screenshot[235:285, 110:552]
                if match_template(rois['five_choice_one_roi'], images['five_choice_one_img']):
                    print("检测到五选一")
                    if config["five_choice_one_action"] == "目标选择二":
                        perform_action("目标选择二")
                    elif config["five_choice_one_action"] == "目标选择三":
                        perform_action("目标选择三")
                    elif config["five_choice_one_action"] == "目标选择四":
                        perform_action("目标选择四")
                    elif config["five_choice_one_action"] == "目标选择五":
                        perform_action("目标选择五")
                    else:
                        perform_action("呼出赛程一")
                elif match_template(rois['trip_roi'], images['trip_img']):
                    print("检测到出行事件")
                    perform_action("出行事件选择")
                elif match_template(rois['greenhat_ask_roi'], images['greenhat_ask_img']) or (match_template(rois['event_choice_roi'], images['event_choice1_img']) and match_template(rois['none_roi'], images['none_img'])) or match_template(rois['add_training_roi'], images['add_training_img']):
                    print("检测到特殊事件")
                    perform_action("特殊事件选择")
                elif match_template(rois['event_choice_roi'], images['event_choice_img']) and match_template(rois['none_roi'], images['none_img']):
                    print("检测到事件选择")
                    perform_action("随机事件选择")
            elif match_template(rois['lace_tips_roi'], images['lace_tips_img']):
                print("检测到赛程赛")
                perform_action("赛程赛")
            elif match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                sleep(1)
                screenshot = capture_screenshot()
                rois['training_roi'] = screenshot[938:1044, 70:170]
                if match_template(rois['training_roi'], images['training_img']) and best_action is not None:
                    print("检测到训练界面")
                    executor.submit(perform_action, best_action)
                    best_action = None
            elif match_template(rois['kaigai_training_roi'], images['kaigai_training_img']) and best_action is not None:
                print("检测到远征训练界面")
                executor.submit(perform_action, best_action)
                best_action = None
            elif match_template(rois['beats_roi'], images['beats_img']):
                print("检测到继承")
                perform_action("继承")
            elif match_template(rois['communicate_lace_roi'], images['communicate_lace_img']):
                print("检测到交流战")
                perform_action("海外赛")
            elif match_template(rois['object_lace_roi'], images['object_lace_img']):
                if current_round == 10:
                    print("检测到出道战")
                    perform_action("新人赛")
                elif current_round in (32, 58):
                    print("检测到目标赛")
                    perform_action("目标赛")
                elif current_round in (39, 63):
                    print("检测到海外赛")
                    perform_action("海外赛")
            elif match_template(rois['before_lace_roi'], images['before_lace_img']):
                if current_round in config["run_styles"].get("逃", []):
                    print("更改跑法逃")
                    perform_action("跑法改逃")
                elif current_round in config["run_styles"].get("先", []):
                    print("更改跑法先")
                    perform_action("跑法改先")
                elif current_round in config["run_styles"].get("差", []):
                    print("更改跑法差")
                    perform_action("跑法改差")
                elif current_round in config["run_styles"].get("追", []):
                    print("更改跑法追")
                    perform_action("跑法改追")
                print("开始比赛")
                perform_action("开始比赛")
            elif match_template(rois['continue_roi'], images['continue_img']):
                print("检测到目标达成")
                perform_action("目标达成")
            elif current_round == 10 and match_template(rois['lace_lose_roi'], images['lace_lose_img']):
                print("检测到出道失败，闹钟启动一次")
                perform_action("用闹钟")
                perform_action("比赛结束")
            elif match_template(rois['lace_confirm_roi'], images['lace_confirm_img']):
                print("检测到漏点确认")
                perform_action("确认补")
            elif match_template(rois['lace_kaigai_confirm_roi'], images['lace_kaigai_confirm_img']):
                print("检测到漏点海外确认参赛")
                perform_action("海外确认参赛补")
            elif match_template(rois['lace_over3_roi'], images['lace_over3_img']) or match_template(rois['lace_over2_roi'], images['lace_over2_img']) or match_template(rois['lace_over2_roi'], images['lace_over4_img']):
                print("检测到比赛结束")
                perform_action("比赛结束补")
            elif match_template(rois['lace_over1_roi'], images['lace_over1_img']):
                print("检测到比赛结束")
                perform_action("比赛结束")
            elif current_round == 65 and match_template(rois['clock_roi'], images['clock_img']):
                print("检测到凯旋门失败")
                perform_action("凯旋门失败")
            
        sleep(1)

def match_template(roi, template):
    """模板匹配"""
    res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.99
    loc = np.where(res >= threshold)
    return len(loc[0]) > 0

def safe_perform_action(action):
    """带锁的执行操作"""
    with lock:
        perform_action(action)

def main():
    """主函数"""
    try:
        # 初始化目标端口
        get_target_ports_once()
        
        if not target_ports:
            print("错误: 未能获取到任何目标端口")
            return
            
        # 初始化异步相关内容
        loop_thread = init_async()
        
        # 启动游戏状态检查
        game_thread = threading.Thread(target=check_game_state, daemon=True)
        game_thread.start()
        
        # 启动抓包
        while True:
            try:
                sniffer = start_capture()
                if sniffer:
                    sniffer.start()
                    sniffer.join()
                else:
                    sleep(3)
            except Exception as e:
                print(f"捕获异常: {str(e)}，3秒后重试...")
                sleep(3)
                
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"主程序异常: {str(e)}")
    finally:
        # 清理资源
        cleanup()

def cleanup():
    """清理资源"""
    global processing, loop
    
    print("开始清理资源...")
    
    # 停止处理
    processing = False
    
    # 停止事件循环
    if loop and not loop.is_closed():
        try:
            loop.call_soon_threadsafe(loop.stop)
            loop.close()
        except Exception as e:
            print(f"关闭事件循环时出错: {str(e)}")
    
    print("资源清理完成")

if __name__ == '__main__':
    main()