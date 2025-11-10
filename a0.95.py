# -*- coding: utf-8 -*
#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk
from tkinter import StringVar
from tkinter import colorchooser
from datetime import datetime
import socket
import threading
import time
import json
import os
import re
import sys

# ============ 初始化全局变量和文件 ============
# 读取球队名单（使用FileManager将在导入后初始化）
away_list = []
home_list = []

# 全局变量（球队名称和比分等，实际值在MY_GUI初始化时从VmixController获取）
teamname_home = "主队"
teamname_away = "客队"
score_home = "0"
score_away = "0"
session_period = "上半场"
team_home_color = "#3498DB"  # 默认主队颜色
team_away_color = "#E74C3C"  # 默认客队颜色

def initialize_files():
    """初始化文件（需要在FileManager类定义之后调用）"""
    global away_list, home_list
    
    # 读取球队名单
    away_list = FileManager.read_lines('away.txt')
    home_list = FileManager.read_lines('home.txt')
    
    # 初始化比分文件（使用默认值，实际值会在MY_GUI初始化时从VmixController获取并更新）
    # 这样可以避免重复读取配置文件，由VmixController统一管理配置
    scoreboard_content = f"主队,0,#3498DB\n客队,0,#E74C3C\n上半场"
    FileManager.write_csv('scoreboard.csv', scoreboard_content, mode='w+')
    
    # 初始化所有数据文件（每次启动时刷新）
    csv_files_to_clear = [
        'goal.csv',
        'red_card.csv',
        'yellow_card.csv',
        'substitutions.csv',
    ]
    for filename in csv_files_to_clear:
        FileManager.clear_file(filename)

# ============ 现代化UI配色方案 ============
COLORS = {
    # 主色调
    'primary': '#2C3E50',      # 深蓝灰
    'primary_light': '#34495E',
    'secondary': '#3498DB',    # 天蓝色
    'accent': '#E74C3C',       # 红色强调
    
    # 背景色
    'bg_main': '#ECF0F1',      # 浅灰背景
    'bg_dark': '#2C3E50',      # 深色背景
    'bg_card': '#FFFFFF',      # 卡片背景
    'bg_hover': '#BDC3C7',     # 悬停背景
    
    # 功能色
    'success': '#27AE60',      # 绿色（成功/增加）
    'warning': '#F39C12',      # 橙色（警告）
    'danger': '#E74C3C',       # 红色（危险/删除）
    'info': '#3498DB',         # 蓝色（信息）
    
    # 文字色
    'text_dark': '#2C3E50',    # 深色文字
    'text_light': '#FFFFFF',   # 浅色文字
    'text_muted': '#95A5A6',   # 次要文字
    
    # 边框色
    'border': '#BDC3C7',       # 边框
    'border_light': '#ECF0F1', # 浅边框
}

FONTS = {
    'title': ('Microsoft YaHei UI', 18, 'bold'),      # 大标题
    'heading': ('Microsoft YaHei UI', 13, 'bold'),    # 页面标题
    'subheading': ('Microsoft YaHei UI', 11, 'bold'), # 子标题
    'body': ('Microsoft YaHei UI', 10),               # 正文
    'small': ('Microsoft YaHei UI', 9),               # 小文字
    'tiny': ('Microsoft YaHei UI', 8),                # 极小文字
    'score': ('Microsoft YaHei UI', 42, 'bold'),      # 比分显示
    'button': ('Microsoft YaHei UI', 10),             # 按钮文字
    'input': ('Microsoft YaHei UI', 10),              # 输入框文字
}

SPACING = {
    'xs': 3,   # 极小间距
    'sm': 6,   # 小间距
    'md': 10,  # 中等间距
    'lg': 14,  # 大间距
    'xl': 18,  # 极大间距
}

# 组件尺寸
SIZES = {
    'border_width': 1,
    'button_height': 32,
    'input_height': 30,
    'card_min_width': 160,
    'icon_size': 16,
}

# ============ 常量定义 ============
# 超时时间配置（秒）
TIMEOUTS = {
    'CONNECTION': 3,          # 连接超时
    'HEARTBEAT': 0.5,         # 心跳检查超时
    'CHECK_INTERVAL': 3000,   # 连接检查间隔（毫秒）
}

# 延迟时间配置（秒）
DELAYS = {
    'RED_CARD': 8,      # 红牌延迟
    'YELLOW_CARD': 8,   # 黄牌延迟
    'SUB': 5,           # 换人延迟
    'GOAL': 8,          # 进球延迟
}

# UI更新间隔（毫秒）
UI_UPDATE_INTERVALS = {
    'COUNTDOWN': 50,    # 倒计时更新间隔
    'CONNECTION_CHECK': 3000,  # 连接检查间隔
}

# ============ 文件管理器类 ============
class FileManager:
    """统一管理文件操作，解决路径硬编码问题
    编译后所有文件操作（读取和写入）都使用exe所在目录
    """
    
    _base_dir = None
    
    @classmethod
    def _get_base_dir(cls):
        """获取文件基目录（单例模式）
        支持PyInstaller打包后的exe环境
        编译后使用exe所在目录，开发环境使用脚本所在目录
        """
        if cls._base_dir is None:
            # 判断是否运行在PyInstaller打包的exe中
            if getattr(sys, 'frozen', False):
                # 如果是打包的exe，使用exe所在的目录
                cls._base_dir = os.path.dirname(sys.executable)
            else:
                # 如果是开发环境，使用脚本所在的目录
                cls._base_dir = os.path.dirname(os.path.abspath(__file__))
        return cls._base_dir
    
    @staticmethod
    def get_file_path(filename):
        """获取文件的绝对路径（exe所在目录）"""
        return os.path.join(FileManager._get_base_dir(), filename)
    
    @staticmethod
    def write_csv(filename, content, mode='w'):
        """通用CSV写入方法（始终写入到exe所在目录）"""
        # CSV文件应该始终写入到exe所在目录，而不是资源目录
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)
            return True
        except (IOError, OSError, PermissionError) as e:
            print(f"写入文件 {filename} 失败: {e}")
            return False
    
    @staticmethod
    def read_csv(filename):
        """通用CSV读取方法（从exe所在目录读取）"""
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, IOError, OSError) as e:
            print(f"读取文件 {filename} 失败: {e}")
            return None
    
    @staticmethod
    def read_lines(filename):
        """读取文件所有行（从exe所在目录读取）"""
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return [x.strip() for x in f.readlines()]
        except (FileNotFoundError, IOError, OSError) as e:
            print(f"读取文件 {filename} 失败: {e}")
            return []
    
    @staticmethod
    def write_json(filename, data):
        """写入JSON文件（始终写入到exe所在目录）"""
        # JSON文件应该始终写入到exe所在目录，而不是资源目录
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError, PermissionError, ValueError, TypeError) as e:
            print(f"写入JSON文件 {filename} 失败: {e}")
            return False
    
    @staticmethod
    def read_json(filename):
        """读取JSON文件（从exe所在目录读取）"""
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, IOError, OSError, ValueError, json.JSONDecodeError) as e:
            print(f"读取JSON文件 {filename} 失败: {e}")
            return None
    
    @staticmethod
    def clear_file(filename):
        """清空文件内容（始终操作exe所在目录的文件）"""
        # 文件应该始终在exe所在目录操作，而不是资源目录
        filepath = os.path.join(FileManager._get_base_dir(), filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('')
            return True
        except (IOError, OSError, PermissionError) as e:
            print(f"清空文件 {filename} 失败: {e}")
            return False

# ============ 工具函数 ============
def get_contrast_text_color(bg_color):
    """
    根据背景颜色计算合适的文字颜色（确保对比度）
    返回 'white' 或 '#2C3E50'（深色）
    """
    try:
        # 处理None或空值
        if not bg_color:
            return COLORS['text_light']
        
        # 转换为字符串并去除空格
        bg_color = str(bg_color).strip()
        
        # 处理常见的颜色名称（转换为十六进制）
        color_names = {
            'white': '#FFFFFF',
            'black': '#000000',
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'cyan': '#00FFFF',
            'magenta': '#FF00FF',
        }
        bg_color_lower = bg_color.lower()
        if bg_color_lower in color_names:
            bg_color = color_names[bg_color_lower]
        
        # 去除#号并转换为RGB
        if bg_color.startswith('#'):
            hex_color = bg_color[1:]
        else:
            hex_color = bg_color
        
        # 如果是3位十六进制，转换为6位
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # 转换为RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # 计算亮度（使用标准亮度公式）
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)
        
        # 如果背景较亮，使用深色文字；如果背景较暗，使用浅色文字
        if brightness > 128:
            return COLORS['text_dark']  # 深色文字
        else:
            return COLORS['text_light']  # 浅色文字
    except (ValueError, IndexError, AttributeError, TypeError) as e:
        # 如果解析失败，默认返回浅色文字
        print(f"颜色解析失败: {bg_color}, 错误: {e}")
        return COLORS['text_light']

# ============ vMix连接管理类 ============
class VmixController:
    def __init__(self):
        self.config_file = "config.json"  # 统一配置文件
        
        # 默认配置
        self.host = "127.0.0.1"
        self.port = 8099
        self.connected = False
        self.socket = None
        
        # 球队配置（合并到统一配置文件）
        self.team_name_home = "主队"  # 默认主队名称
        self.team_name_away = "客队"  # 默认客队名称
        self.team_home_color = "#3498DB"  # 默认主队颜色
        self.team_away_color = "#E74C3C"  # 默认客队颜色
        
        # 配置项
        self.red_card_input = "1"
        self.red_card_layer = "0"
        self.red_card_delay = 8  # 红牌自动下字幕延迟（秒）
        
        self.yellow_card_input = "1"
        self.yellow_card_layer = "1"
        self.yellow_card_delay = 8  # 黄牌自动下字幕延迟（秒）
        
        self.sub_input = "2"
        self.sub_layer = "0"
        self.sub_delay = 5  # 换人自动下字幕延迟（秒）
        
        self.goal_input = "3"
        self.goal_layer = "0"
        self.goal_delay = 8  # 进球自动下字幕延迟（秒）
        
        self.hide_timers = {}  # 存储自动下字幕的定时器
        
        # 加载配置
        self.load_config()
    
    def connect(self):
        """连接到vMix"""
        try:
            if self.socket:
                try:
                    self.socket.close()
                except (OSError, socket.error):
                    pass
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUTS['CONNECTION'])
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ 成功连接到 vMix {self.host}:{self.port}")
            return True
        except (socket.timeout, socket.error, OSError, ConnectionRefusedError) as e:
            self.connected = False
            self.socket = None
            print(f"✗ vMix连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        # 取消所有正在运行的定时器（避免资源泄漏）
        for subtitle_type, timer in list(self.hide_timers.items()):
            try:
                timer.cancel()
            except (AttributeError, RuntimeError):
                pass
        self.hide_timers.clear()
        
        if self.socket:
            try:
                self.socket.close()
            except (OSError, socket.error):
                pass
        self.socket = None
        self.connected = False
        print("✓ 已断开 vMix 连接")
    
    def send_command(self, command):
        """发送命令到vMix"""
        if not self.connected or not self.socket:
            return False
        
        try:
            full_command = f"FUNCTION {command}\r\n"
            self.socket.send(full_command.encode('utf-8'))
            return True
        except (OSError, socket.error, BrokenPipeError, ConnectionResetError) as e:
            print(f"✗ 发送命令失败: {e}")
            self.connected = False
            return False
    
    def overlay_on(self, input_num, layer_num="0"):
        """打开字幕叠加"""
        command = f"OverlayInput{layer_num} Input={input_num}"
        return self.send_command(command)
    
    def overlay_off(self, layer_num="0"):
        """关闭字幕叠加"""
        command = f"OverlayInput{layer_num}Off"
        return self.send_command(command)
    
    def show_subtitle(self, subtitle_type):
        """显示字幕并自动下字幕"""
        # 取消之前的自动下字幕定时器
        if subtitle_type in self.hide_timers:
            try:
                self.hide_timers[subtitle_type].cancel()
            except (AttributeError, RuntimeError):
                pass
        
        # 根据类型选择配置
        if subtitle_type == "red_card":
            input_num = self.red_card_input
            layer_num = self.red_card_layer
            delay = self.red_card_delay
        elif subtitle_type == "yellow_card":
            input_num = self.yellow_card_input
            layer_num = self.yellow_card_layer
            delay = self.yellow_card_delay
        elif subtitle_type == "sub":
            input_num = self.sub_input
            layer_num = self.sub_layer
            delay = self.sub_delay
        elif subtitle_type == "goal":
            input_num = self.goal_input
            layer_num = self.goal_layer
            delay = self.goal_delay
        else:
            return False
        
        # 上字幕
        if self.overlay_on(input_num, layer_num):
            print(f"✓ 已显示 {subtitle_type} 字幕，将在 {delay} 秒后自动下字幕")
            
            # 设置自动下字幕定时器
            timer = threading.Timer(delay, 
                                   lambda: self.hide_subtitle(subtitle_type, auto=True))
            timer.start()
            self.hide_timers[subtitle_type] = timer
            return True
        return False
    
    def get_delay(self, subtitle_type):
        """获取指定类型的延迟时间"""
        if subtitle_type == "red_card":
            return self.red_card_delay
        elif subtitle_type == "yellow_card":
            return self.yellow_card_delay
        elif subtitle_type == "sub":
            return self.sub_delay
        elif subtitle_type == "goal":
            return self.goal_delay
        return 5
    
    def save_config(self):
        """保存配置到文件（合并所有配置）"""
        config = {
            # vMix连接配置
            'host': self.host,
            'port': self.port,
            # vMix字幕配置
            'red_card_input': self.red_card_input,
            'red_card_layer': self.red_card_layer,
            'red_card_delay': self.red_card_delay,
            'yellow_card_input': self.yellow_card_input,
            'yellow_card_layer': self.yellow_card_layer,
            'yellow_card_delay': self.yellow_card_delay,
            'sub_input': self.sub_input,
            'sub_layer': self.sub_layer,
            'sub_delay': self.sub_delay,
            'goal_input': self.goal_input,
            'goal_layer': self.goal_layer,
            'goal_delay': self.goal_delay,
            # 球队配置
            'team_name_home': self.team_name_home,
            'team_name_away': self.team_name_away,
            'team_home_color': self.team_home_color,
            'team_away_color': self.team_away_color
        }
        
        if FileManager.write_json(self.config_file, config):
            print(f"✓ 配置已保存到 {self.config_file}")
            return True
        else:
            print(f"✗ 保存配置失败")
            return False
    
    def load_config(self):
        """从文件加载配置（合并所有配置）"""
        # 尝试加载新配置文件
        config = FileManager.read_json(self.config_file)
        if config:
            # vMix连接配置
            self.host = config.get('host', self.host)
            self.port = config.get('port', self.port)
            # vMix字幕配置
            self.red_card_input = config.get('red_card_input', self.red_card_input)
            self.red_card_layer = config.get('red_card_layer', self.red_card_layer)
            self.red_card_delay = config.get('red_card_delay', self.red_card_delay)
            self.yellow_card_input = config.get('yellow_card_input', self.yellow_card_input)
            self.yellow_card_layer = config.get('yellow_card_layer', self.yellow_card_layer)
            self.yellow_card_delay = config.get('yellow_card_delay', self.yellow_card_delay)
            self.sub_input = config.get('sub_input', self.sub_input)
            self.sub_layer = config.get('sub_layer', self.sub_layer)
            self.sub_delay = config.get('sub_delay', self.sub_delay)
            self.goal_input = config.get('goal_input', self.goal_input)
            self.goal_layer = config.get('goal_layer', self.goal_layer)
            self.goal_delay = config.get('goal_delay', self.goal_delay)
            # 球队配置
            self.team_name_home = config.get('team_name_home', self.team_name_home)
            self.team_name_away = config.get('team_name_away', self.team_name_away)
            self.team_home_color = config.get('team_home_color', self.team_home_color)
            self.team_away_color = config.get('team_away_color', self.team_away_color)
            
            print(f"✓ 已从 {self.config_file} 加载配置")
            return
        
        # 保存配置到文件
        self.save_config()
        print(f"✓ 配置已加载并保存到 {self.config_file}")
    
    def hide_subtitle(self, subtitle_type, auto=False):
        """隐藏字幕"""
        # 根据类型选择配置
        if subtitle_type == "red_card":
            layer_num = self.red_card_layer
        elif subtitle_type == "yellow_card":
            layer_num = self.yellow_card_layer
        elif subtitle_type == "sub":
            layer_num = self.sub_layer
        elif subtitle_type == "goal":
            layer_num = self.goal_layer
        else:
            return False
        
        # 下字幕
        if self.overlay_off(layer_num):
            if auto:
                print(f"✓ 自动下 {subtitle_type} 字幕")
            else:
                print(f"✓ 手动下 {subtitle_type} 字幕")
            
            # 清除定时器
            if subtitle_type in self.hide_timers:
                del self.hide_timers[subtitle_type]
            return True
        return False

# ============ 带倒计时的字幕控制按钮 ============
class SubtitleButton:
    def __init__(self, parent, vmix_controller, subtitle_type, text="上字幕", 
                 width=200, height=60, font_size=14):
        self.parent = parent
        self.vmix = vmix_controller
        self.subtitle_type = subtitle_type
        self.text = text
        self.width = width
        self.height = height
        self.is_active = False
        self.remaining_time = 0
        self.total_time = 0
        self.timer_thread = None
        self.stop_timer = False
        
        # 创建画布
        self.canvas = Canvas(parent, width=width, height=height, 
                            highlightthickness=2, highlightbackground=COLORS['border'])
        self.canvas.pack()
        
        # 初始状态：绿色背景
        self.bg_color = COLORS['success']
        self.text_color = COLORS['text_light']
        self.progress_color = "#ff4444"
        
        # 绘制初始状态
        self.draw_button()
        
        # 绑定点击事件
        self.canvas.bind('<Button-1>', self.on_click)
        
        # 绑定大小变化事件，以便在容器大小改变时重新绘制
        self.canvas.bind('<Configure>', lambda e: self.draw_button())
        
    def draw_button(self):
        """绘制按钮"""
        self.canvas.delete("all")
        
        # 获取canvas的实际尺寸（支持动态高度）
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # 如果canvas还没有实际尺寸，使用默认值
        if canvas_width <= 1:
            canvas_width = self.width
        if canvas_height <= 1:
            canvas_height = self.height
        
        if not self.is_active:
            # 未激活状态：显示"上字幕"和延迟时间
            self.canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                        fill=self.bg_color, outline="")
            # 主文字
            self.canvas.create_text(canvas_width/2, canvas_height/2 - 8,
                                   text=self.text, fill=self.text_color,
                                   font=('Arial', 16, 'bold'))
            # 延迟时间提示
            delay = self.vmix.get_delay(self.subtitle_type)
            self.canvas.create_text(canvas_width/2, canvas_height/2 + 12,
                                   text=f"({delay}秒后自动下)", fill=self.text_color,
                                   font=('Arial', 9))
        else:
            # 激活状态：显示倒计时和进度条
            # 计算进度
            if self.total_time > 0:
                progress = self.remaining_time / self.total_time
            else:
                progress = 0
            
            # 绘制进度条背景（红色）
            self.canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                        fill="#ff4444", outline="")
            
            # 绘制剩余时间的进度条（深红色）
            progress_width = canvas_width * progress
            if progress_width > 0:
                self.canvas.create_rectangle(0, 0, progress_width, canvas_height,
                                            fill="#cc0000", outline="")
            
            # 显示倒计时文字
            time_text = f"点击下字幕 {self.remaining_time:.1f}s"
            self.canvas.create_text(canvas_width/2, canvas_height/2,
                                   text=time_text, fill="white",
                                   font=('Arial', 14, 'bold'))
    
    def on_click(self, event=None):
        """按钮点击事件"""
        if not self.is_active:
            # 上字幕
            self.show_subtitle()
        else:
            # 下字幕
            self.hide_subtitle()
    
    def show_subtitle(self):
        """显示字幕并开始倒计时"""
        if self.vmix.show_subtitle(self.subtitle_type):
            self.is_active = True
            self.total_time = self.vmix.get_delay(self.subtitle_type)
            self.remaining_time = self.total_time
            self.stop_timer = False
            self.start_time = time.time()
            
            # 使用tkinter的after方法进行倒计时，避免线程问题
            self.countdown()
    
    def hide_subtitle(self):
        """隐藏字幕并停止倒计时"""
        self.stop_timer = True
        self.vmix.hide_subtitle(self.subtitle_type, auto=False)
        self.is_active = False
        self.draw_button()
    
    def update_subtitle_type(self, new_subtitle_type):
        """更新字幕类型（仅在未激活时更新）"""
        if not self.is_active:
            self.subtitle_type = new_subtitle_type
            self.draw_button()
    
    def countdown(self):
        """倒计时 - 使用after方法避免卡顿"""
        if self.stop_timer or not self.is_active:
            return
        
        # 基于实际时间计算剩余时间
        elapsed = time.time() - self.start_time
        self.remaining_time = max(0, self.total_time - elapsed)
        
        # 更新显示
        self.draw_button()
        
        if self.remaining_time > 0:
            # 使用常量定义的更新间隔
            self.canvas.after(UI_UPDATE_INTERVALS['COUNTDOWN'], self.countdown)
        else:
            # 时间到，自动下字幕
            self.is_active = False
            self.draw_button()

class MY_GUI():
    def __init__(self,init_window_name):
        self.init_window_name = init_window_name
        self.vmix = VmixController()  # 创建vMix控制器实例（已加载所有配置）
        
        # 从vMix控制器获取球队配置（已合并到统一配置）
        self.team_home_color = self.vmix.team_home_color
        self.team_away_color = self.vmix.team_away_color
        
        # 从配置获取球队名称（不再从txt读取）
        global teamname_home, teamname_away
        teamname_home = self.vmix.team_name_home
        teamname_away = self.vmix.team_name_away
        
        # 使用StringVar实现球队名称的动态更新
        self.home_name_var = StringVar(value=f"[主队]{teamname_home}")
        self.away_name_var = StringVar(value=f"[客队]{teamname_away}")
        # 计分板专用的球队名称（不带前缀）
        self.scoreboard_home_name_var = StringVar(value=teamname_home)
        self.scoreboard_away_name_var = StringVar(value=teamname_away)
        
        # 存储所有需要更新颜色的球队Label引用
        self.home_color_labels = []
        self.away_color_labels = []
        
        # vMix连接管理相关变量
        self.is_first_connect_attempt = True  # 标记是否是首次连接尝试
        self.reconnect_attempt_count = 0  # 重连尝试次数
        self.last_connected_state = False  # 上一次的连接状态
        self.should_auto_reconnect = True  # 是否应该自动重连（弹窗后设为False，手动连接后重置）
        self.has_alerted_disconnect = False  # 是否已经弹窗提醒过断开（避免重复弹窗）
    #设置窗口
    def set_init_window(self):
        # 生成版本号：V + 年月日时分 (例如 V202511110055)
        version = datetime.now().strftime("V%Y%m%d%H%M")
        self.init_window_name.title(f"足球比赛字幕控制系统 {version}")
        self.init_window_name.geometry('1400x800+50+50')
        self.init_window_name.resizable(1,1)
        self.init_window_name["bg"] = COLORS['bg_main']
        
        # 设置窗口图标
        try:
            # 获取图标文件路径（支持开发环境和打包后的环境）
            if getattr(sys, 'frozen', False):
                # 打包后的环境：PyInstaller会解压文件到临时目录
                if hasattr(sys, '_MEIPASS'):
                    # 单文件打包模式：资源在临时目录
                    base_path = sys._MEIPASS
                else:
                    # 目录模式：exe文件所在目录
                    base_path = os.path.dirname(sys.executable)
            else:
                # 开发环境：脚本所在目录
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, 'app.ico')
            if os.path.exists(icon_path):
                self.init_window_name.iconbitmap(icon_path)
            else:
                # 尝试当前工作目录
                if os.path.exists('app.ico'):
                    self.init_window_name.iconbitmap('app.ico')
        except Exception as e:
            # 如果设置图标失败，不影响程序运行
            print(f"提示: 无法设置窗口图标 ({e})")
        
        self.sessionVar = StringVar()
        self.sessionVar.set("上半场")

        self.scoreHomeVar = IntVar()
        self.scoreHomeVar.set(0)

        self.scoreAwayVar = IntVar()
        self.scoreAwayVar.set(0)

        # === 底部状态栏（首先创建，确保在最底层） ===
        self.create_status_bar()
        
        # 绑定窗口配置变化事件，确保状态栏始终可见
        def on_window_configure(event):
            if hasattr(self, 'status_frame'):
                self.status_frame.lift()
        self.init_window_name.bind('<Configure>', on_window_configure)
        
        # 创建主容器：使用Grid布局实现响应式
        main_container = Frame(self.init_window_name, bg=COLORS['bg_main'])
        main_container.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=(SPACING['md'], SPACING['md']))
        
        # 配置Grid权重实现40:60比例
        main_container.grid_columnconfigure(0, weight=2, minsize=400)  # 左侧40%
        main_container.grid_columnconfigure(1, weight=3, minsize=600)  # 右侧60%
        main_container.grid_rowconfigure(0, weight=1)

        # === 左侧面板 ===
        left_panel = Frame(main_container, bg=COLORS['bg_main'])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING['sm']))
        
        # 左侧使用Grid分成上下两部分
        left_panel.grid_rowconfigure(0, weight=1, minsize=300)  # 记分板
        left_panel.grid_rowconfigure(1, weight=1, minsize=300)  # 菜单
        left_panel.grid_columnconfigure(0, weight=1)

        # === 左上：记分板区域 ===
        scoreboard_container = Frame(left_panel, bg=COLORS['bg_card'], relief=FLAT, bd=0, highlightthickness=1, highlightbackground=COLORS['border'])
        scoreboard_container.grid(row=0, column=0, sticky="nsew", pady=(0, SPACING['sm']))

        # === 左下：功能菜单区域 ===
        buttons_container = Frame(left_panel, bg=COLORS['bg_card'], relief=FLAT, bd=0, highlightthickness=1, highlightbackground=COLORS['border'])
        buttons_container.grid(row=1, column=0, sticky="nsew")

        # 菜单按钮容器 - 使用Grid布局创建卡片式菜单（已删除标题横幅）
        menu_buttons_frame = Frame(buttons_container, bg=COLORS['bg_main'])
        menu_buttons_frame.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        # 配置Grid布局 - 2列
        menu_buttons_frame.grid_columnconfigure(0, weight=1)
        menu_buttons_frame.grid_columnconfigure(1, weight=1)

        # 卡片式菜单按钮
        def create_menu_card(parent, text, icon, color, command, row, col):
            """创建卡片式菜单按钮"""
            card = Frame(parent, bg=color, relief=RAISED, bd=2, cursor="hand2",
                        highlightthickness=0)
            card.grid(row=row, column=col, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")
            
            # 配置行权重使卡片平均分布
            parent.grid_rowconfigure(row, weight=1)
            
            # 内容容器
            content = Frame(card, bg=color)
            content.pack(expand=True, fill=BOTH, padx=SPACING['md'], pady=SPACING['lg'])
            
            # 图标（大号显示）
            icon_label = Label(content, text=icon, font=FONTS['title'], 
                              bg=color, fg=COLORS['primary'])
            icon_label.pack(pady=(0, SPACING['xs']))
            
            # 文本（居中显示）
            text_label = Label(content, text=text, font=FONTS['subheading'], 
                              bg=color, fg=COLORS['text_dark'])
            text_label.pack()
            
            # 绑定点击事件到所有元素
            widgets = [card, content, icon_label, text_label]
            for widget in widgets:
                widget.bind('<Button-1>', lambda e: command())
            
            # 悬停效果
            def on_enter(e):
                card.config(relief=SUNKEN, bd=3)
                for widget in widgets:
                    widget.config(bg=COLORS['bg_hover'])
            
            def on_leave(e):
                card.config(relief=RAISED, bd=2)
                for widget in widgets:
                    widget.config(bg=color)
            
            for widget in widgets:
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            
            return card

        # 创建菜单卡片（2列布局）
        create_menu_card(menu_buttons_frame, "球队名单", "[名单]", "#E8F4F8", 
                        lambda: self.show_panel('player_list'), 0, 0)
        create_menu_card(menu_buttons_frame, "换人管理", "[换人]", "#FFF4E6", 
                        lambda: self.show_panel('sub'), 0, 1)
        create_menu_card(menu_buttons_frame, "红黄牌", "[牌]", "#FFEBEE", 
                        lambda: self.show_panel('cards'), 1, 0)
        create_menu_card(menu_buttons_frame, "进球信息", "[进球]", "#E8F5FD", 
                        lambda: self.show_panel('goal'), 1, 1)
        create_menu_card(menu_buttons_frame, "vMix设置", "[连接]", "#E8F5E9", 
                        lambda: self.show_panel('vmix'), 2, 0)
        create_menu_card(menu_buttons_frame, "球队设置", "[设置]", "#FFF3E0", 
                        lambda: self.show_panel('team_settings'), 2, 1)

        # === 右侧：内容显示区域 ===
        right_panel = Frame(main_container, bg=COLORS['bg_main'])
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        self.right_content = Frame(right_panel, bg=COLORS['bg_card'], relief=FLAT, bd=0, highlightthickness=1, highlightbackground=COLORS['border'])
        self.right_content.grid(row=0, column=0, sticky="nsew")

        # 创建各个内容面板（统一高度约束）
        self.frame_player_list = Frame(self.right_content, bg=COLORS['bg_card'])
        self.frame_sub = Frame(self.right_content, bg=COLORS['bg_card'])
        self.frame_red_yellow_card = Frame(self.right_content, bg=COLORS['bg_card'])
        self.frame_goal = Frame(self.right_content, bg=COLORS['bg_card'])
        self.frame_vmix_config = Frame(self.right_content, bg=COLORS['bg_card'])
        self.frame_team_settings = Frame(self.right_content, bg=COLORS['bg_card'])
        
        # 确保所有面板都能正确填充可用空间
        for frame in [self.frame_player_list, self.frame_sub, self.frame_red_yellow_card, 
                     self.frame_goal, self.frame_vmix_config, self.frame_team_settings]:
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

        # 默认显示球队名单面板
        self.frame_player_list.pack(fill=BOTH, expand=True)

        # 记分板直接放在左上
        self.frame_scoreboard = scoreboard_container

        # 当前显示的面板
        self.current_panel = self.frame_player_list

        #组件

        '''名单显示'''
        # 配置Grid布局实现左右响应式
        self.frame_player_list.grid_rowconfigure(0, weight=1)
        self.frame_player_list.grid_columnconfigure(0, weight=1)
        self.frame_player_list.grid_columnconfigure(1, weight=1)
        
        # 主队容器
        frame_home = Frame(self.frame_player_list, bg=COLORS['bg_card'])
        frame_home.grid(row=0, column=0, sticky="nsew", padx=(SPACING['md'], SPACING['xs']))
        
        # 主队标题栏
        home_header = Frame(frame_home, height=40)
        home_header.pack(fill=X)
        home_header.pack_propagate(False)
        home_header.config(bg=self.team_home_color)
        home_text_color = get_contrast_text_color(self.team_home_color)
        home_label = Label(home_header, textvariable=self.home_name_var, font=FONTS['heading'],
                          bg=self.team_home_color, fg=home_text_color)
        home_label.pack(expand=True)
        self.home_color_labels.append((home_header, home_label))
        
        # 主队名单容器
        home_list_container = Frame(frame_home, bg=COLORS['bg_card'])
        home_list_container.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        # 主队名单（带滚动条）
        home_scrollbar = Scrollbar(home_list_container)
        home_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.list_home = Listbox(home_list_container, selectmode=SINGLE,
                                bg=COLORS['bg_card'], bd=0, font=FONTS['body'],
                                fg=COLORS['text_dark'], highlightthickness=1,
                                highlightbackground=COLORS['border'],
                                selectbackground=COLORS['info'],
                                selectforeground=COLORS['text_light'],
                                yscrollcommand=home_scrollbar.set)
        for item in home_list:
            self.list_home.insert(END, item)
        self.list_home.pack(side=LEFT, fill=BOTH, expand=True)
        home_scrollbar.config(command=self.list_home.yview)
        
        # 客队容器
        frame_away = Frame(self.frame_player_list, bg=COLORS['bg_card'])
        frame_away.grid(row=0, column=1, sticky="nsew", padx=(SPACING['xs'], SPACING['md']))
        
        # 客队标题栏
        away_header = Frame(frame_away, height=40)
        away_header.pack(fill=X)
        away_header.pack_propagate(False)
        away_header.config(bg=self.team_away_color)
        away_text_color = get_contrast_text_color(self.team_away_color)
        away_label = Label(away_header, textvariable=self.away_name_var, font=FONTS['heading'],
                          bg=self.team_away_color, fg=away_text_color)
        away_label.pack(expand=True)
        self.away_color_labels.append((away_header, away_label))
        
        # 客队名单容器
        away_list_container = Frame(frame_away, bg=COLORS['bg_card'])
        away_list_container.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        # 客队名单（带滚动条）
        away_scrollbar = Scrollbar(away_list_container)
        away_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.list_away = Listbox(away_list_container, selectmode=SINGLE,
                                bg=COLORS['bg_card'], bd=0, font=FONTS['body'],
                                fg=COLORS['text_dark'], highlightthickness=1,
                                highlightbackground=COLORS['border'],
                                selectbackground=COLORS['accent'],
                                selectforeground=COLORS['text_light'],
                                yscrollcommand=away_scrollbar.set)
        for item in away_list:
            self.list_away.insert(END, item)
        self.list_away.pack(side=LEFT, fill=BOTH, expand=True)
        away_scrollbar.config(command=self.list_away.yview)


        '''换人模块'''
        # 配置Grid布局（取消标题横幅，改为左右布局）
        self.frame_sub.grid_rowconfigure(0, weight=0)  # 上字幕按钮和预览区域（左右布局）
        self.frame_sub.grid_rowconfigure(1, weight=1)  # 主队
        self.frame_sub.grid_rowconfigure(2, weight=1)  # 客队
        self.frame_sub.grid_columnconfigure(0, weight=1)
        
        # === 预览区域（包含上字幕按钮） ===
        control_preview_row = Frame(self.frame_sub, bg=COLORS['bg_main'])
        control_preview_row.grid(row=0, column=0, sticky="ew", padx=SPACING['md'], pady=SPACING['md'])
        control_preview_row.grid_columnconfigure(0, weight=1)  # 预览区域占满宽度
        
        # 换人预览区域
        preview_container = Frame(control_preview_row, bg=COLORS['bg_dark'], 
                                 highlightthickness=2, 
                                 highlightbackground=COLORS['warning'])
        preview_container.grid(row=0, column=0, sticky="nsew")
        
        # 预览标题（动态显示队伍名称和颜色）
        preview_header = Frame(preview_container, bg=COLORS['warning'], height=40)
        preview_header.pack(fill=X)
        preview_header.pack_propagate(False)
        self.sub_preview_title_var = StringVar(value="当前换人字幕预览")
        self.sub_preview_title_label = Label(preview_header, textvariable=self.sub_preview_title_var, 
                                            font=FONTS['heading'],
                                            bg=COLORS['warning'], fg=COLORS['text_light'])
        self.sub_preview_title_label.pack(expand=True)
        # 保存header引用以便更新背景颜色
        self.sub_preview_header = preview_header
        
        # 预览内容 - 使用Grid布局，左侧预览信息，右侧按钮（紧凑布局）
        preview_content = Frame(preview_container, bg=COLORS['bg_dark'])
        preview_content.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['xs'])
        preview_content.grid_columnconfigure(0, weight=1)  # 左侧预览内容占满剩余空间
        preview_content.grid_columnconfigure(1, weight=0, minsize=220)  # 右侧按钮区域固定宽度
        preview_content.grid_rowconfigure(0, weight=0)  # 不扩展行，让内容根据实际大小自适应
        
        # 左侧：预览信息容器（占满宽度，降低高度）
        preview_info_frame = Frame(preview_content, bg=COLORS['bg_dark'])
        preview_info_frame.grid(row=0, column=0, sticky="ew", padx=(0, SPACING['md']))  # 横向填充
        
        # 换下区域（上方，高度翻倍）
        out_container = Frame(preview_info_frame, bg=COLORS['danger'], relief=FLAT, 
                             highlightthickness=2, 
                             highlightbackground=COLORS['danger'])
        out_container.pack(fill=X, pady=(0, SPACING['xs']))
        Label(out_container, text="⬇️ 换下", font=FONTS['small'], 
              bg=COLORS['danger'], fg=COLORS['text_light'], padx=SPACING['md'], pady=SPACING['xs']*2).pack(side=LEFT)
        self.sub_current_out_label = Label(out_container, text="-- --", font=FONTS['subheading'],
                                           bg=COLORS['danger'], fg=COLORS['text_light'], 
                                           padx=SPACING['lg'], pady=SPACING['xs']*2)
        self.sub_current_out_label.pack(side=LEFT, expand=True)
        
        # 换上区域（下方，高度翻倍）
        in_container = Frame(preview_info_frame, bg=COLORS['success'], relief=FLAT,
                            highlightthickness=2, 
                            highlightbackground=COLORS['success'])
        in_container.pack(fill=X)
        Label(in_container, text="⬆️ 换上", font=FONTS['small'], 
              bg=COLORS['success'], fg=COLORS['text_light'], padx=SPACING['md'], pady=SPACING['xs']*2).pack(side=LEFT)
        self.sub_current_in_label = Label(in_container, text="-- --", font=FONTS['subheading'],
                                          bg=COLORS['success'], fg=COLORS['text_light'], 
                                          padx=SPACING['lg'], pady=SPACING['xs']*2)
        self.sub_current_in_label.pack(side=LEFT, expand=True)
        
        # 右侧：上字幕按钮（高度精确匹配两个标题的总高度）
        btn_wrapper = Frame(preview_content, bg=COLORS['bg_dark'])
        btn_wrapper.grid(row=0, column=1, sticky="nw")  # 顶部对齐，不填充
        
        # 创建按钮容器，立即pack显示
        btn_container = Frame(btn_wrapper, bg=COLORS['bg_dark'])
        btn_container.pack(fill=BOTH, expand=True)
        
        # 创建换人字幕控制按钮
        self.sub_button = SubtitleButton(btn_container, self.vmix, "sub", 
                                        text="【上字幕】", width=200, height=50)
        
        # 让按钮的canvas填满容器高度
        self.sub_button.canvas.pack_forget()
        # 先使用默认方式pack，后续同步时再调整
        self.sub_button.canvas.pack(fill=BOTH, expand=True)
        
        # 保存上次高度，避免重复设置
        self._last_preview_height = 0
        self._syncing_heights = False
        
        # 同步按钮容器高度与预览信息容器高度的函数
        def sync_heights(*args):
            # 如果正在同步，跳过避免递归
            if self._syncing_heights:
                return
            
            try:
                self._syncing_heights = True
                preview_info_frame.update_idletasks()
                # 使用实际高度而不是请求高度
                preview_height = preview_info_frame.winfo_height()
                if preview_height <= 1:
                    preview_height = preview_info_frame.winfo_reqheight()
                
                # 只在高度发生变化时更新，避免无限循环
                if preview_height > 1 and preview_height != self._last_preview_height:
                    self._last_preview_height = preview_height
                    
                    # 强制设置固定高度，防止自动扩展
                    btn_wrapper.config(height=preview_height)
                    btn_wrapper.grid_propagate(False)  # 禁止自动调整大小
                    
                    # 更新canvas高度以匹配预览容器
                    self.sub_button.canvas.config(height=preview_height)
            except Exception as e:
                pass
            finally:
                self._syncing_heights = False
        
        # 绑定预览容器大小变化事件，同步按钮高度
        preview_info_frame.bind('<Configure>', lambda e: sync_heights())
        
        # 立即同步一次，然后延迟再次同步确保正确
        sync_heights()
        self.init_window_name.after(50, sync_heights)
        self.init_window_name.after(200, sync_heights)
        
        # 同时保留原有的label引用（用于兼容现有代码）
        self.sub_away_out_label = self.sub_current_out_label
        self.sub_away_in_label = self.sub_current_in_label
        self.sub_home_out_label = self.sub_current_out_label
        self.sub_home_in_label = self.sub_current_in_label
        
        # 使用统一方法创建主队/客队面板（调整行索引：从3,4改为1,2）
        frame_sub_home, self.sub_home_entry, self.sub_home_cards_frame = self.create_team_panel(
            self.frame_sub, 1, 'home', "所有记录（点击选择）", "换人编号",
            cards_frame_attr='sub_home_cards_frame',
            add_command=self.sub_home_add, clear_command=self.sub_clear_home
        )
        
        frame_sub_away, self.sub_away_entry, self.sub_away_cards_frame = self.create_team_panel(
            self.frame_sub, 2, 'away', "所有记录（点击选择）", "换人编号",
            cards_frame_attr='sub_away_cards_frame',
            add_command=self.sub_away_add, clear_command=self.sub_clear_away
        )

        # 存储换人列表
        self.sub_away_list = []
        self.sub_home_list = []


        '''红黄牌'''
        # 配置Grid布局
        self.frame_red_yellow_card.grid_rowconfigure(0, weight=0)  # 预览区域
        self.frame_red_yellow_card.grid_rowconfigure(1, weight=1)  # 主队
        self.frame_red_yellow_card.grid_rowconfigure(2, weight=1)  # 客队
        self.frame_red_yellow_card.grid_columnconfigure(0, weight=1)
        
        # === 统一的红黄牌预览区域（左右分布）- 加大显示 ===
        card_preview_container = Frame(self.frame_red_yellow_card, bg=COLORS['bg_dark'], 
                                      highlightthickness=2, 
                                      highlightbackground=COLORS['warning'])
        card_preview_container.grid(row=0, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])
        
        # 预览标题 - 动态显示球队名称
        self.card_preview_header = Frame(card_preview_container, bg=COLORS['warning'], height=40)
        self.card_preview_header.pack(fill=X)
        self.card_preview_header.pack_propagate(False)
        self.card_preview_title_var = StringVar(value="当前红黄牌字幕预览")
        self.card_preview_title_label = Label(self.card_preview_header, textvariable=self.card_preview_title_var, font=FONTS['heading'],
              bg=COLORS['warning'], fg=COLORS['text_light'])
        self.card_preview_title_label.pack(expand=True)
        
        # 预览内容区域 - 左右分布（红牌、黄牌、按钮在同一行）
        self.card_preview_content = Frame(card_preview_container, bg=COLORS['bg_dark'])
        self.card_preview_content.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        # 配置三列：红牌色块、黄牌色块、按钮
        self.card_preview_content.grid_columnconfigure(0, weight=1)  # 红牌（可变）
        self.card_preview_content.grid_columnconfigure(1, weight=1)  # 黄牌（可变）
        self.card_preview_content.grid_columnconfigure(2, weight=0, minsize=200)  # 按钮（固定200）
        
        # 左侧：红牌预览（加强色彩）
        red_card_frame = Frame(self.card_preview_content, bg="#C62828", relief=FLAT,
                              highlightthickness=3, highlightbackground="#E53935")
        red_card_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING['sm']))
        
        self.red_card_display_label = Label(red_card_frame, text="", 
                                            font=FONTS['subheading'],
                                            bg="#C62828", fg=COLORS['text_light'],
                                            relief=FLAT, wraplength=300)
        self.red_card_display_label.pack(fill=BOTH, expand=True, padx=SPACING['sm'], pady=SPACING['sm'])
        
        # 中间：黄牌预览（加强色彩）
        yellow_card_frame = Frame(self.card_preview_content, bg="#F9A825", relief=FLAT,
                                 highlightthickness=3, highlightbackground="#FFEB3B")
        yellow_card_frame.grid(row=0, column=1, sticky="nsew", padx=SPACING['sm'])
        
        self.yellow_card_display_label = Label(yellow_card_frame, text="", 
                                               font=FONTS['subheading'],
                                               bg="#F9A825", fg="black",
                                               relief=FLAT, wraplength=300)
        self.yellow_card_display_label.pack(fill=BOTH, expand=True, padx=SPACING['sm'], pady=SPACING['sm'])
        
        # 右侧：vMix控制按钮（统一按钮，根据当前卡片类型动态调整）
        btn_container = Frame(self.card_preview_content, bg=COLORS['bg_dark'])
        btn_container.grid(row=0, column=2, sticky="nsew", padx=(SPACING['sm'], 0))
        
        # 创建统一的红黄牌字幕按钮（初始为红牌类型）
        self.card_button = SubtitleButton(btn_container, self.vmix, "red_card", 
                                         text="【上字幕】", width=200, height=50)
        
        # 存储当前卡片类型（用于判断是红牌还是黄牌）
        self.current_card_type = None  # "red_card" 或 "yellow_card"
        
        # 创建红黄牌输入区域（支持红牌/黄牌按钮）
        def create_card_input_area(parent, team_type, red_cmd, yellow_cmd, clear_cmd):
            """创建红黄牌专用输入区域"""
            input_frame = Frame(parent, bg=COLORS['bg_card'])
            input_frame.pack(fill=X, padx=SPACING['md'], pady=SPACING['md'])
            
            # 球队标签
            team_name_var = self.home_name_var if team_type == 'home' else self.away_name_var
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            text_color = get_contrast_text_color(team_color)
            team_label = Label(input_frame, textvariable=team_name_var, font=FONTS['subheading'],
                             bg=team_color, fg=text_color, width=10, relief=FLAT,
                             padx=SPACING['md'], pady=SPACING['sm'])
            team_label.pack(side=LEFT, padx=(0, SPACING['md']))
            color_labels = self.home_color_labels if team_type == 'home' else self.away_color_labels
            color_labels.append((None, team_label))
            
            Label(input_frame, text="球员编号", font=FONTS['small'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=LEFT, padx=(0, SPACING['xs']))
            
            # 输入框
            highlight = COLORS['info'] if team_type == 'home' else COLORS['accent']
            entry = Entry(input_frame, font=FONTS['input'], relief=FLAT,
                         highlightthickness=SIZES['border_width'], 
                         highlightbackground=COLORS['border'], highlightcolor=highlight,
                         width=12, bg='white', fg='black')
            entry.pack(side=LEFT, padx=SPACING['xs'], ipady=3)
            
            # 红牌/黄牌/清空按钮（统一风格）
            Button(input_frame, text="■ 红牌", bg="#E53935", fg="white",
                  font=FONTS['subheading'], relief=RAISED, cursor="hand2", bd=3,
                  padx=SPACING['lg'], pady=SPACING['sm'], command=red_cmd,
                  activebackground="#C62828", activeforeground="white").pack(side=LEFT, padx=SPACING['sm'])
            
            Button(input_frame, text="■ 黄牌", bg="#FFEB3B", fg="black",
                  font=FONTS['subheading'], relief=RAISED, cursor="hand2", bd=3,
                  padx=SPACING['lg'], pady=SPACING['sm'], command=yellow_cmd,
                  activebackground="#FDD835", activeforeground="black").pack(side=LEFT, padx=SPACING['sm'])
            
            self.create_button(input_frame, "清空", COLORS['danger'], clear_cmd)
            return entry
        
        # 主队红黄牌面板
        frame_red_home = Frame(self.frame_red_yellow_card, bg=COLORS['bg_card'],
                              highlightthickness=SIZES['border_width'],
                              highlightbackground=COLORS['border'])
        frame_red_home.grid(row=1, column=0, sticky="nsew", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['xs']))
        self.red_home_entry = create_card_input_area(frame_red_home, 'home',
                                                    self.red_home_add, self.yellow_home_add, self.red_home_clear)
        self.red_home_current_label = self.red_card_display_label
        _, _, _ = self.create_scrollable_canvas(frame_red_home, 'red_home_cards_frame')
        
        # 客队红黄牌面板
        frame_red_away = Frame(self.frame_red_yellow_card, bg=COLORS['bg_card'],
                              highlightthickness=SIZES['border_width'],
                              highlightbackground=COLORS['border'])
        frame_red_away.grid(row=2, column=0, sticky="nsew", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['md']))
        self.red_away_entry = create_card_input_area(frame_red_away, 'away',
                                                    self.red_away_add, self.yellow_away_add, self.red_away_clear)
        self.red_away_current_label = self.red_card_display_label
        _, _, _ = self.create_scrollable_canvas(frame_red_away, 'red_away_cards_frame')

        # 存储红黄牌列表
        self.red_home_list = []
        self.red_away_list = []

        '''进球信息'''
        # 配置Grid布局
        self.frame_goal.grid_rowconfigure(0, weight=0)  # 预览区域
        self.frame_goal.grid_rowconfigure(1, weight=1)  # 主队
        self.frame_goal.grid_rowconfigure(2, weight=1)  # 客队
        self.frame_goal.grid_columnconfigure(0, weight=1)
        
        # === 进球预览区域 ===
        goal_preview_container = Frame(self.frame_goal, bg=COLORS['bg_dark'], 
                                      highlightthickness=2, 
                                      highlightbackground=COLORS['success'])
        goal_preview_container.grid(row=0, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])
        
        # 预览标题 - 动态显示球队名称
        self.goal_preview_header = Frame(goal_preview_container, bg=COLORS['success'], height=40)
        self.goal_preview_header.pack(fill=X)
        self.goal_preview_header.pack_propagate(False)
        self.goal_preview_title_var = StringVar(value="当前进球字幕预览")
        self.goal_preview_title_label = Label(self.goal_preview_header, textvariable=self.goal_preview_title_var, font=FONTS['heading'],
              bg=COLORS['success'], fg=COLORS['text_light'])
        self.goal_preview_title_label.pack(expand=True)
        
        # 预览内容区域 - 进球色块和按钮在同一行
        goal_preview_content = Frame(goal_preview_container, bg=COLORS['bg_dark'])
        goal_preview_content.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        # 配置两列：进球色块（可变）、按钮（固定200）
        goal_preview_content.grid_columnconfigure(0, weight=1)  # 进球色块（可变）
        goal_preview_content.grid_columnconfigure(1, weight=0, minsize=200)  # 按钮（固定200）
        
        # 左侧：进球预览
        goal_display_frame = Frame(goal_preview_content, bg="#1E7E34", relief=FLAT,
                                   highlightthickness=3, highlightbackground="#28A745")
        goal_display_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING['sm']))
        
        self.goal_display_label = Label(goal_display_frame, text="--- 等待输入 ---", 
                                        font=FONTS['subheading'],
                                        bg="#1E7E34", fg=COLORS['text_light'],
                                        relief=FLAT, wraplength=400)
        self.goal_display_label.pack(fill=BOTH, expand=True, padx=SPACING['sm'], pady=SPACING['sm'])
        
        # 右侧：vMix控制按钮
        btn_container = Frame(goal_preview_content, bg=COLORS['bg_dark'])
        btn_container.grid(row=0, column=1, sticky="nsew", padx=(SPACING['sm'], 0))
        
        self.goal_button = SubtitleButton(btn_container, self.vmix, "goal", 
                                         text="【上字幕】", width=200, height=50)
        
        # 创建进球专用输入区域（支持进球按钮）
        def create_goal_input_area(parent, team_type, goal_cmd, clear_cmd):
            """创建进球专用输入区域"""
            input_frame = Frame(parent, bg=COLORS['bg_card'])
            input_frame.pack(fill=X, padx=SPACING['md'], pady=SPACING['md'])
            
            # 球队标签
            team_name_var = self.home_name_var if team_type == 'home' else self.away_name_var
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            team_label = Label(input_frame, textvariable=team_name_var, font=FONTS['subheading'],
                             bg=team_color, fg=COLORS['text_light'], width=10, relief=FLAT,
                             padx=SPACING['md'], pady=SPACING['sm'])
            team_label.pack(side=LEFT, padx=(0, SPACING['md']))
            color_labels = self.home_color_labels if team_type == 'home' else self.away_color_labels
            color_labels.append((None, team_label))
            
            Label(input_frame, text="进球球员编号", font=FONTS['small'],
                 bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=LEFT, padx=(0, SPACING['xs']))
            
            # 输入框
            highlight = COLORS['info'] if team_type == 'home' else COLORS['accent']
            entry = Entry(input_frame, font=FONTS['input'], relief=FLAT,
                         highlightthickness=SIZES['border_width'], 
                         highlightbackground=COLORS['border'], highlightcolor=highlight,
                         width=12, bg='white', fg='black')
            entry.pack(side=LEFT, padx=SPACING['xs'], ipady=3)
            entry.bind('<Return>', lambda e: goal_cmd())
            
            # 进球/清空按钮（统一风格）
            Button(input_frame, text="记录进球", bg="#28A745", fg="white",
                  font=FONTS['subheading'], relief=RAISED, cursor="hand2", bd=2,
                  padx=SPACING['lg'], pady=SPACING['sm'], command=goal_cmd,
                  activebackground="#1E7E34", activeforeground="white").pack(side=LEFT, padx=SPACING['sm'])
            
            self.create_button(input_frame, "清空", COLORS['danger'], clear_cmd)
            return entry
        
        # 主队进球面板
        frame_goal_home = Frame(self.frame_goal, bg=COLORS['bg_card'],
                               highlightthickness=SIZES['border_width'],
                               highlightbackground=COLORS['border'])
        frame_goal_home.grid(row=1, column=0, sticky="nsew", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['xs']))
        self.goal_home_entry = create_goal_input_area(frame_goal_home, 'home',
                                                      self.goal_home_add, self.goal_home_clear)
        _, _, _ = self.create_scrollable_canvas(frame_goal_home, 'goal_home_cards_frame')
        
        # 客队进球面板
        frame_goal_away = Frame(self.frame_goal, bg=COLORS['bg_card'],
                               highlightthickness=SIZES['border_width'],
                               highlightbackground=COLORS['border'])
        frame_goal_away.grid(row=2, column=0, sticky="nsew", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['md']))
        self.goal_away_entry = create_goal_input_area(frame_goal_away, 'away',
                                                      self.goal_away_add, self.goal_away_clear)
        _, _, _ = self.create_scrollable_canvas(frame_goal_away, 'goal_away_cards_frame')

        # 存储进球列表
        self.goal_home_list = []
        self.goal_away_list = []

        '''vMix配置'''
        # 配置Grid布局
        self.frame_vmix_config.grid_rowconfigure(0, weight=0)  # 标题
        self.frame_vmix_config.grid_rowconfigure(1, weight=0)  # 连接配置
        self.frame_vmix_config.grid_rowconfigure(2, weight=0)  # 字幕配置
        self.frame_vmix_config.grid_rowconfigure(3, weight=1)  # 占位
        self.frame_vmix_config.grid_columnconfigure(0, weight=1)
        
        # 使用统一标题栏方法
        self.create_header(self.frame_vmix_config, "vMix 连接设置", COLORS['primary'], 40)
        
        # === 连接配置区域 ===
        conn_frame = Frame(self.frame_vmix_config, bg=COLORS['bg_card'],
                          highlightthickness=SIZES['border_width'],
                          highlightbackground=COLORS['border'])
        conn_frame.grid(row=1, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])
        
        # 连接配置标题
        Label(conn_frame, text="📡 连接配置", font=FONTS['subheading'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(anchor=W, padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        # IP和端口
        conn_input_frame = Frame(conn_frame, bg=COLORS['bg_card'])
        conn_input_frame.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        Label(conn_input_frame, text="IP地址:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=12, anchor=W).pack(side=LEFT)
        
        self.vmix_ip_entry = Entry(conn_input_frame, font=FONTS['input'], relief=FLAT,
                                   bg='white', fg='black',
                                   highlightthickness=SIZES['border_width'],
                                   highlightbackground=COLORS['border'], width=20)
        self.vmix_ip_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.vmix_ip_entry.insert(0, self.vmix.host)
        
        Label(conn_input_frame, text="端口:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=6, anchor=W).pack(side=LEFT, padx=(SPACING['lg'], 0))
        
        self.vmix_port_entry = Entry(conn_input_frame, font=FONTS['input'], relief=FLAT,
                                     bg='white', fg='black',
                                     highlightthickness=SIZES['border_width'],
                                     highlightbackground=COLORS['border'], width=10)
        self.vmix_port_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.vmix_port_entry.insert(0, str(self.vmix.port))
        
        # 连接按钮和状态
        conn_btn_frame = Frame(conn_frame, bg=COLORS['bg_card'])
        conn_btn_frame.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        self.create_button(conn_btn_frame, "连接", COLORS['success'], self.vmix_connect,
                          padx=SPACING['lg'])
        self.create_button(conn_btn_frame, "断开", COLORS['danger'], self.vmix_disconnect,
                          padx=SPACING['lg'])
        
        # 状态指示灯
        self.vmix_status_frame = Frame(conn_btn_frame, bg=COLORS['bg_card'])
        self.vmix_status_frame.pack(side=LEFT, padx=(SPACING['lg'], 0))
        
        self.vmix_status_indicator = Label(self.vmix_status_frame, text="●", font=('Arial', 20),
                                           bg=COLORS['bg_card'], fg="gray")
        self.vmix_status_indicator.pack(side=LEFT)
        
        self.vmix_status_label = Label(self.vmix_status_frame, text="未连接", font=FONTS['body'],
                                       bg=COLORS['bg_card'], fg=COLORS['text_muted'])
        self.vmix_status_label.pack(side=LEFT, padx=(SPACING['xs'], 0))
        
        # === 字幕配置区域 ===
        subtitle_frame = Frame(self.frame_vmix_config, bg=COLORS['bg_card'],
                              highlightthickness=SIZES['border_width'],
                              highlightbackground=COLORS['border'])
        subtitle_frame.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=(0, SPACING['lg']))
        
        # 字幕配置标题
        Label(subtitle_frame, text="字幕配置", font=FONTS['subheading'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(anchor=W, padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        # 配置表格
        config_container = Frame(subtitle_frame, bg=COLORS['bg_card'])
        config_container.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # 表头
        header_frame = Frame(config_container, bg=COLORS['primary_light'])
        header_frame.pack(fill=X, pady=(0, SPACING['xs']))
        Label(header_frame, text="字幕类型", font=FONTS['body'], bg=COLORS['primary_light'],
              fg=COLORS['text_light'], width=12, anchor=W).pack(side=LEFT, padx=SPACING['md'], pady=SPACING['xs'])
        Label(header_frame, text="Input通道", font=FONTS['body'], bg=COLORS['primary_light'],
              fg=COLORS['text_light'], width=12, anchor=W).pack(side=LEFT, padx=SPACING['md'], pady=SPACING['xs'])
        Label(header_frame, text="图层编号", font=FONTS['body'], bg=COLORS['primary_light'],
              fg=COLORS['text_light'], width=12, anchor=W).pack(side=LEFT, padx=SPACING['md'], pady=SPACING['xs'])
        Label(header_frame, text="延迟时间(秒)", font=FONTS['body'], bg=COLORS['primary_light'],
              fg=COLORS['text_light'], width=12, anchor=W).pack(side=LEFT, padx=SPACING['md'], pady=SPACING['xs'])
        
        # 红牌配置
        self._create_subtitle_config_row(config_container, "[红牌]", "red")
        
        # 黄牌配置
        self._create_subtitle_config_row(config_container, "[黄牌]", "yellow")
        
        # 换人配置
        self._create_subtitle_config_row(config_container, "[换人]", "sub")
        
        # 进球配置
        self._create_subtitle_config_row(config_container, "[进球]", "goal")
        
        # 保存按钮
        save_frame = Frame(subtitle_frame, bg=COLORS['bg_card'])
        save_frame.pack(fill=X, padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        
        self.create_button(save_frame, "保存配置", COLORS['secondary'], self.vmix_save_config,
                          padx=SPACING['xl'], pady=SPACING['sm'], side=TOP)
        
        # 说明信息
        info_vmix = Frame(subtitle_frame, bg=COLORS['info'])
        info_vmix.pack(fill=X, pady=(SPACING['md'], 0))
        Label(info_vmix, text="提示: 配置完成后，在换人和红黄牌预览界面可以直接控制字幕上下",
              font=FONTS['small'], bg=COLORS['info'], fg=COLORS['text_light'],
              padx=SPACING['md'], pady=SPACING['sm']).pack()

        '''球队设置'''
        # 配置Grid布局
        self.frame_team_settings.grid_rowconfigure(0, weight=0)  # 标题
        self.frame_team_settings.grid_rowconfigure(1, weight=0)  # 球队名称设置
        self.frame_team_settings.grid_rowconfigure(2, weight=0)  # 球队颜色设置
        self.frame_team_settings.grid_rowconfigure(3, weight=1)  # 占位
        self.frame_team_settings.grid_columnconfigure(0, weight=1)
        
        # 使用统一标题栏方法
        self.create_header(self.frame_team_settings, "球队设置", COLORS['primary'], 40)
        
        # === 球队名称设置 ===
        name_frame = Frame(self.frame_team_settings, bg=COLORS['bg_card'],
                          highlightthickness=SIZES['border_width'],
                          highlightbackground=COLORS['border'])
        name_frame.grid(row=1, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])
        
        Label(name_frame, text="球队名称设置", font=FONTS['subheading'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(anchor=W, padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        # 主队名称
        home_name_row = Frame(name_frame, bg=COLORS['bg_card'])
        home_name_row.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        Label(home_name_row, text="[主队]名称:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=15, anchor=W).pack(side=LEFT)
        
        self.team_home_name_entry = Entry(home_name_row, font=FONTS['input'], relief=FLAT,
                                          bg='white', fg='black',
                                          highlightthickness=SIZES['border_width'],
                                          highlightbackground=COLORS['border'], width=30)
        self.team_home_name_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.team_home_name_entry.insert(0, teamname_home)
        
        # 客队名称
        away_name_row = Frame(name_frame, bg=COLORS['bg_card'])
        away_name_row.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        Label(away_name_row, text="[客队]名称:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=15, anchor=W).pack(side=LEFT)
        
        self.team_away_name_entry = Entry(away_name_row, font=FONTS['input'], relief=FLAT,
                                          bg='white', fg='black',
                                          highlightthickness=SIZES['border_width'],
                                          highlightbackground=COLORS['border'], width=30)
        self.team_away_name_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.team_away_name_entry.insert(0, teamname_away)
        
        # === 球队颜色设置 ===
        color_frame = Frame(self.frame_team_settings, bg=COLORS['bg_card'],
                           highlightthickness=SIZES['border_width'],
                           highlightbackground=COLORS['border'])
        color_frame.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=(0, SPACING['lg']))
        
        Label(color_frame, text="球队颜色设置", font=FONTS['subheading'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(anchor=W, padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        # 主队颜色
        home_color_row = Frame(color_frame, bg=COLORS['bg_card'])
        home_color_row.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        Label(home_color_row, text="[主队]颜色:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=15, anchor=W).pack(side=LEFT)
        
        self.team_home_color_entry = Entry(home_color_row, font=FONTS['input'], relief=FLAT,
                                           bg='white', fg='black',
                                           highlightthickness=SIZES['border_width'],
                                           highlightbackground=COLORS['border'], width=15)
        self.team_home_color_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.team_home_color_entry.insert(0, self.team_home_color)
        
        home_preview_text_color = get_contrast_text_color(self.team_home_color)
        self.team_home_color_preview = Label(home_color_row, text="   预览   ", font=FONTS['body'],
                                             bg=self.team_home_color, fg=home_preview_text_color, relief=RAISED, padx=SPACING['lg'], pady=SPACING['xs'])
        self.team_home_color_preview.pack(side=LEFT, padx=SPACING['md'])
        
        Button(home_color_row, text="选择颜色", bg=COLORS['secondary'], fg='black',
               font=FONTS['button'], relief=FLAT, cursor="hand2",
               padx=SPACING['md'], pady=SPACING['xs'],
               activeforeground='black',
               command=lambda: self.choose_team_color('home')).pack(side=LEFT)
        
        # 客队颜色
        away_color_row = Frame(color_frame, bg=COLORS['bg_card'])
        away_color_row.pack(fill=X, padx=SPACING['md'], pady=SPACING['sm'])
        
        Label(away_color_row, text="[客队]颜色:", font=FONTS['body'],
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], width=15, anchor=W).pack(side=LEFT)
        
        self.team_away_color_entry = Entry(away_color_row, font=FONTS['input'], relief=FLAT,
                                           bg='white', fg='black',
                                           highlightthickness=SIZES['border_width'],
                                           highlightbackground=COLORS['border'], width=15)
        self.team_away_color_entry.pack(side=LEFT, padx=SPACING['sm'], ipady=3)
        self.team_away_color_entry.insert(0, self.team_away_color)
        
        away_preview_text_color = get_contrast_text_color(self.team_away_color)
        self.team_away_color_preview = Label(away_color_row, text="   预览   ", font=FONTS['body'],
                                             bg=self.team_away_color, fg=away_preview_text_color, relief=RAISED, padx=SPACING['lg'], pady=SPACING['xs'])
        self.team_away_color_preview.pack(side=LEFT, padx=SPACING['md'])
        
        self.create_button(away_color_row, "选择颜色", COLORS['secondary'],
                          lambda: self.choose_team_color('away'))
        
        # 保存按钮
        team_save_frame = Frame(self.frame_team_settings, bg=COLORS['bg_card'])
        team_save_frame.grid(row=3, column=0, sticky="n", pady=SPACING['lg'])
        
        self.create_button(team_save_frame, "保存球队设置", COLORS['success'], self.save_team_settings,
                          padx=SPACING['xl'], pady=SPACING['sm'], side=TOP)
        
        # 说明信息
        info_team = Frame(color_frame, bg=COLORS['info'])
        info_team.pack(fill=X, pady=(SPACING['md'], 0))
        Label(info_team, text="提示: 颜色格式为十六进制 如 #3498DB。保存后立即生效",
              font=FONTS['small'], bg=COLORS['info'], fg=COLORS['text_light'],
              padx=SPACING['md'], pady=SPACING['sm']).pack()
        
        # 右下角：开发信息和反馈提示
        feedback_frame = Frame(self.frame_team_settings, bg=COLORS['bg_card'])
        feedback_frame.grid(row=3, column=0, sticky="se", padx=SPACING['lg'], pady=(0, SPACING['lg']))
        
        feedback_text = ("本软件由重庆寰网致博体育文化传播有限公司开发\n"
                        "使用过程中如遇到bug或有更好的建议，欢迎反馈给我们\n"
                        "可通过手机号 18523999949 添加微信联系我们")
        feedback_label = Label(feedback_frame, text=feedback_text, font=FONTS['small'],
                              bg=COLORS['bg_card'], fg=COLORS['text_muted'],
                              justify=LEFT, anchor=W)
        feedback_label.pack(anchor=E)

        '''记分板'''
        # 配置记分板Grid布局（已删除标题横幅和独立控制区域）
        self.frame_scoreboard.grid_rowconfigure(0, weight=1)  # 比分显示（包含控制按钮）
        self.frame_scoreboard.grid_rowconfigure(1, weight=0)  # 场次选择
        self.frame_scoreboard.grid_columnconfigure(0, weight=1)
        
        # 比分显示区域 - 使用卡片式设计
        score_display_container = Frame(self.frame_scoreboard, bg=COLORS['bg_main'])
        score_display_container.grid(row=0, column=0, sticky="nsew", pady=SPACING['sm'], padx=SPACING['md'])
        score_display_container.grid_columnconfigure(0, weight=1)
        score_display_container.grid_columnconfigure(1, weight=0)
        score_display_container.grid_columnconfigure(2, weight=1)
        score_display_container.grid_rowconfigure(0, weight=1)
        
        # 主队卡片
        home_card = Frame(score_display_container, bg=COLORS['bg_card'], relief=RAISED, bd=2,
                         highlightthickness=0)
        home_card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING['xs']))
        
        # 主队颜色条
        home_color_bar = Frame(home_card, bg=self.team_home_color, height=6)
        home_color_bar.pack(fill=X)
        self.home_color_labels.append(home_color_bar)
        
        # 主队内容 - 使用pack顺序控制布局
        home_content = Frame(home_card, bg=COLORS['bg_card'])
        home_content.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        Label(home_content, text="主队", font=FONTS['small'], 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()
        
        Label(home_content, textvariable=self.scoreboard_home_name_var, font=FONTS['subheading'], 
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(pady=(0, SPACING['sm']))
        
        self.scoreboard_home_score_title = Label(home_content, textvariable=self.scoreHomeVar,
                                                 font=FONTS['score'], bg=COLORS['bg_card'], 
                                                 fg=self.team_home_color)
        self.scoreboard_home_score_title.pack(expand=True)  # 占据中间空间
        self.home_color_labels.append(self.scoreboard_home_score_title)
        
        # 主队比分控制按钮 - 放在卡片底部（加按钮70%，减按钮30%，高度一致）
        home_btn_frame = Frame(home_content, bg=COLORS['bg_card'])
        home_btn_frame.pack(side=BOTTOM, fill=X, pady=(SPACING['xs'], 0))
        home_btn_frame.grid_columnconfigure(0, weight=7)  # 加按钮占70%
        home_btn_frame.grid_columnconfigure(1, weight=3)  # 减按钮占30%
        
        self.scoreboard_home_scoreplus_button = Button(home_btn_frame, text="+1", 
                                                       bg=COLORS['success'], fg='black',
                                                       font=FONTS['body'], relief=FLAT, cursor="hand2",
                                                       pady=SPACING['sm'], bd=0,
                                                       command=self.scoreboard_home_scoreplus,
                                                       activebackground=COLORS['success'],
                                                       activeforeground='black')
        self.scoreboard_home_scoreplus_button.grid(row=0, column=0, sticky="ew", padx=(0, SPACING['xs']))
        
        self.scoreboard_home_scoreminus_button = Button(home_btn_frame, text="-1",
                                                        bg=COLORS['danger'], fg='black',
                                                        font=FONTS['body'], relief=FLAT, cursor="hand2",
                                                        pady=SPACING['sm'], bd=0,
                                                        command=self.scoreboard_home_scoreminus,
                                                        activebackground=COLORS['danger'],
                                                        activeforeground='black')
        self.scoreboard_home_scoreminus_button.grid(row=0, column=1, sticky="ew")
        
        # VS 分隔符 - 更大更明显
        vs_frame = Frame(score_display_container, bg=COLORS['bg_main'], width=50)
        vs_frame.grid(row=0, column=1, sticky="nsew", padx=SPACING['xs'])
        vs_frame.grid_propagate(False)
        
        vs_label = Label(vs_frame, text="VS", font=FONTS['title'], 
              bg=COLORS['bg_main'], fg=COLORS['text_muted'])
        vs_label.pack(expand=True)
        
        # 客队卡片
        away_card = Frame(score_display_container, bg=COLORS['bg_card'], relief=RAISED, bd=2,
                         highlightthickness=0)
        away_card.grid(row=0, column=2, sticky="nsew", padx=(SPACING['xs'], 0))
        
        # 客队颜色条
        away_color_bar = Frame(away_card, bg=self.team_away_color, height=6)
        away_color_bar.pack(fill=X)
        self.away_color_labels.append(away_color_bar)
        
        # 客队内容 - 使用pack顺序控制布局
        away_content = Frame(away_card, bg=COLORS['bg_card'])
        away_content.pack(fill=BOTH, expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        Label(away_content, text="客队", font=FONTS['small'], 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack()
        
        Label(away_content, textvariable=self.scoreboard_away_name_var, font=FONTS['subheading'], 
              bg=COLORS['bg_card'], fg=COLORS['text_dark']).pack(pady=(0, SPACING['sm']))
        
        self.scoreboard_away_score_title = Label(away_content, textvariable=self.scoreAwayVar,
                                                 font=FONTS['score'], bg=COLORS['bg_card'], 
                                                 fg=self.team_away_color)
        self.scoreboard_away_score_title.pack(expand=True)  # 占据中间空间
        self.away_color_labels.append(self.scoreboard_away_score_title)
        
        # 客队比分控制按钮 - 放在卡片底部（加按钮70%，减按钮30%，高度一致）
        away_btn_frame = Frame(away_content, bg=COLORS['bg_card'])
        away_btn_frame.pack(side=BOTTOM, fill=X, pady=(SPACING['xs'], 0))
        away_btn_frame.grid_columnconfigure(0, weight=7)  # 加按钮占70%
        away_btn_frame.grid_columnconfigure(1, weight=3)  # 减按钮占30%
        
        self.scoreboard_away_scoreplus_button = Button(away_btn_frame, text="+1",
                                                       bg=COLORS['success'], fg='black',
                                                       font=FONTS['body'], relief=FLAT, cursor="hand2",
                                                       pady=SPACING['sm'], bd=0,
                                                       command=self.scoreboard_away_scoreplus,
                                                       activebackground=COLORS['success'],
                                                       activeforeground='black')
        self.scoreboard_away_scoreplus_button.grid(row=0, column=0, sticky="ew", padx=(0, SPACING['xs']))
        
        self.scoreboard_away_scoreminus_button = Button(away_btn_frame, text="-1",
                                                        bg=COLORS['danger'], fg='black',
                                                        font=FONTS['body'], relief=FLAT, cursor="hand2",
                                                        pady=SPACING['sm'], bd=0,
                                                        command=self.scoreboard_away_scoreminus,
                                                        activebackground=COLORS['danger'],
                                                        activeforeground='black')
        self.scoreboard_away_scoreminus_button.grid(row=0, column=1, sticky="ew")
        
        # 场次显示与选择 - 优化布局，节省空间
        session_container = Frame(self.frame_scoreboard, bg=COLORS['bg_main'])
        session_container.grid(row=1, column=0, sticky="ew", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['sm']))
        
        # 紧凑布局：场次选择按钮（取消预览文字，通过按钮高亮显示）
        session_row = Frame(session_container, bg=COLORS['bg_card'], relief=FLAT, bd=1)
        session_row.pack(fill=X)
        
        # 场次选择按钮 - 单行紧凑布局，选中状态高亮显示
        session_buttons = Frame(session_row, bg=COLORS['bg_card'])
        session_buttons.pack(side=LEFT, fill=X, expand=True, padx=SPACING['sm'], pady=SPACING['xs'])
        session_buttons.grid_columnconfigure(0, weight=1)
        session_buttons.grid_columnconfigure(1, weight=1)
        session_buttons.grid_columnconfigure(2, weight=1)
        session_buttons.grid_columnconfigure(3, weight=1)
        
        # 单行排列所有按钮 - 选中时文字为白色，背景为主色调
        self.scoreboard_session_first_radio = Radiobutton(session_buttons, text="上半场", value="上半场",
                                                          bg=COLORS['bg_card'], font=FONTS['small'],
                                                          variable=self.sessionVar, 
                                                          command=self.scoreboard_session_switch,
                                                          activebackground=COLORS['bg_card'],
                                                          indicatoron=0, relief=FLAT, bd=1,
                                                          selectcolor=COLORS['primary'], 
                                                          fg=COLORS['text_dark'],
                                                          activeforeground=COLORS['text_light'],
                                                          pady=SPACING['xs'], cursor="hand2")
        self.scoreboard_session_first_radio.grid(row=0, column=0, sticky="ew", padx=(0, SPACING['xs']))
        
        self.scoreboard_session_halftime_radio = Radiobutton(session_buttons, text="上半场比分", value="上半场比分",
                                                             bg=COLORS['bg_card'], font=FONTS['small'],
                                                             variable=self.sessionVar,
                                                             command=self.scoreboard_session_switch,
                                                             activebackground=COLORS['bg_card'],
                                                             indicatoron=0, relief=FLAT, bd=1,
                                                             selectcolor=COLORS['primary'],
                                                             fg=COLORS['text_dark'],
                                                             activeforeground=COLORS['text_light'],
                                                             pady=SPACING['xs'], cursor="hand2")
        self.scoreboard_session_halftime_radio.grid(row=0, column=1, sticky="ew", padx=SPACING['xs'])
        
        self.scoreboard_session_second_radio = Radiobutton(session_buttons, text="下半场", value="下半场",
                                                           bg=COLORS['bg_card'], font=FONTS['small'],
                                                           variable=self.sessionVar,
                                                           command=self.scoreboard_session_switch,
                                                           activebackground=COLORS['bg_card'],
                                                           indicatoron=0, relief=FLAT, bd=1,
                                                           selectcolor=COLORS['primary'],
                                                           fg=COLORS['text_dark'],
                                                           activeforeground=COLORS['text_light'],
                                                           pady=SPACING['xs'], cursor="hand2")
        self.scoreboard_session_second_radio.grid(row=0, column=2, sticky="ew", padx=SPACING['xs'])
        
        self.scoreboard_session_fulltime_radio = Radiobutton(session_buttons, text="全场比分", value="全场比分",
                                                             bg=COLORS['bg_card'], font=FONTS['small'],
                                                             variable=self.sessionVar,
                                                             command=self.scoreboard_session_switch,
                                                             activebackground=COLORS['bg_card'],
                                                             indicatoron=0, relief=FLAT, bd=1,
                                                             selectcolor=COLORS['primary'],
                                                             fg=COLORS['text_dark'],
                                                             activeforeground=COLORS['text_light'],
                                                             pady=SPACING['xs'], cursor="hand2")
        self.scoreboard_session_fulltime_radio.grid(row=0, column=3, sticky="ew", padx=(SPACING['xs'], 0))
        
        # 存储所有场次按钮引用，用于更新选中状态的文字颜色
        self.session_radios = [
            self.scoreboard_session_first_radio,
            self.scoreboard_session_halftime_radio,
            self.scoreboard_session_second_radio,
            self.scoreboard_session_fulltime_radio
        ]
        
        # 监听sessionVar变化，更新选中状态的文字颜色
        self.sessionVar.trace('w', self._update_session_button_colors)
        self._update_session_button_colors()  # 初始化颜色
        
        # 重置按钮 - 放在场次选择行右侧
        self.scoreboard_score_clear_button = Button(session_row, text="重置",
                                                    bg=COLORS['bg_card'], fg=COLORS['text_dark'],
                                                    font=FONTS['small'], relief=FLAT, cursor="hand2",
                                                    pady=SPACING['xs'], padx=SPACING['sm'], bd=1,
                                                    command=self.scoreboard_score_clear,
                                                    activebackground=COLORS['bg_hover'])
        self.scoreboard_score_clear_button.pack(side=RIGHT, padx=(SPACING['xs'], SPACING['sm']), pady=SPACING['xs'])
        
        # 确保初始化时所有球队名称标签的文字颜色正确设置（特别是白色背景时）
        self._ensure_team_label_colors()
    
    def _ensure_team_label_colors(self):
        """确保所有球队相关标签的文字颜色正确设置（初始化时调用）"""
        # 更新主队标签颜色
        for item in self.home_color_labels:
            try:
                if isinstance(item, tuple):
                    # 格式: (frame, label)
                    frame, label = item
                    if label and hasattr(label, 'config'):
                        try:
                            # 获取当前背景色
                            bg = label.cget('bg') if hasattr(label, 'cget') else self.team_home_color
                            # 确保文字颜色与背景色匹配
                            text_color = get_contrast_text_color(bg)
                            label.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
                elif hasattr(item, 'config'):
                    # 直接是Label对象
                    try:
                        bg = item.cget('bg') if hasattr(item, 'cget') else self.team_home_color
                        text_color = get_contrast_text_color(bg)
                        item.config(fg=text_color)
                    except (TclError, AttributeError):
                        pass
            except (TclError, AttributeError):
                pass
        
        # 更新客队标签颜色
        for item in self.away_color_labels:
            try:
                if isinstance(item, tuple):
                    # 格式: (frame, label)
                    frame, label = item
                    if label and hasattr(label, 'config'):
                        try:
                            # 获取当前背景色
                            bg = label.cget('bg') if hasattr(label, 'cget') else self.team_away_color
                            # 确保文字颜色与背景色匹配
                            text_color = get_contrast_text_color(bg)
                            label.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
                elif hasattr(item, 'config'):
                    # 直接是Label对象
                    try:
                        bg = item.cget('bg') if hasattr(item, 'cget') else self.team_away_color
                        text_color = get_contrast_text_color(bg)
                        item.config(fg=text_color)
                    except (TclError, AttributeError):
                        pass
            except (TclError, AttributeError):
                pass
        
        # 更新预览标签颜色
        if hasattr(self, 'team_home_color_preview'):
            try:
                bg = self.team_home_color_preview.cget('bg') if hasattr(self.team_home_color_preview, 'cget') else self.team_home_color
                text_color = get_contrast_text_color(bg)
                self.team_home_color_preview.config(fg=text_color)
            except (TclError, AttributeError):
                pass
        
        if hasattr(self, 'team_away_color_preview'):
            try:
                bg = self.team_away_color_preview.cget('bg') if hasattr(self.team_away_color_preview, 'cget') else self.team_away_color
                text_color = get_contrast_text_color(bg)
                self.team_away_color_preview.config(fg=text_color)
            except (TclError, AttributeError):
                pass

    # ============ UI工厂方法 - 减少重复代码，统一视觉效果 ============
    def create_header(self, parent, text, bg_color=COLORS['primary'], height=40, info_text=None):
        """创建统一标题栏（带可选说明信息）"""
        header_frame = Frame(parent, bg=bg_color, height=height)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        Label(header_frame, text=text, font=FONTS['heading'],
              bg=bg_color, fg=COLORS['text_light']).pack(expand=True)
        
        if info_text:
            info_frame = Frame(parent, bg=COLORS['info'], height=32)
            info_frame.grid(row=1, column=0, sticky="ew")
            info_frame.grid_propagate(False)
            Label(info_frame, text=info_text, font=FONTS['small'],
                  bg=COLORS['info'], fg=COLORS['text_light']).pack(expand=True)
            return header_frame
        return header_frame
    
    def create_scrollable_canvas(self, parent, frame_attr_name=None):
        """创建带滚动条的Canvas容器（统一风格，支持Grid布局）"""
        # 卡片容器（换人、红黄牌、进球）使用更紧凑的间距
        is_card_container = frame_attr_name and ('sub' in frame_attr_name or 'red' in frame_attr_name or 'goal' in frame_attr_name)
        padding = SPACING['xs'] if is_card_container else SPACING['md']
        container = Frame(parent, bg=COLORS['bg_card'])
        container.pack(fill=BOTH, expand=True, padx=padding, pady=(0, padding))
        
        canvas = Canvas(container, bg=COLORS['bg_card'], highlightthickness=0)
        scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
        cards_frame = Frame(canvas, bg=COLORS['bg_card'])
        
        # 如果是卡片容器（换人、红黄牌、进球），预先配置Grid布局为7列（降低卡片宽度）
        if is_card_container:
            cards_frame.grid_columnconfigure(0, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(1, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(2, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(3, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(4, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(5, weight=1, uniform="card_col")
            cards_frame.grid_columnconfigure(6, weight=1, uniform="card_col")
        
        canvas.create_window((0, 0), window=cards_frame, anchor="nw", tags="cards_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_configure(event):
            canvas.itemconfig("cards_frame", width=event.width)
        
        cards_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        if frame_attr_name:
            setattr(self, frame_attr_name, cards_frame)
            # 自动保存canvas引用（用于兼容现有代码）
            canvas_attr_name = frame_attr_name.replace('_cards_frame', '_canvas')
            setattr(self, canvas_attr_name, canvas)
        
        return container, canvas, cards_frame
    
    def create_input_area(self, parent, team_type, input_label, entry_bind_key=None,
                         add_command=None, add_text="添加", clear_command=None,
                         highlight_color=None):
        """创建统一输入区域（球队标签+输入框+按钮）"""
        input_frame = Frame(parent, bg=COLORS['bg_card'])
        input_frame.pack(fill=X, padx=SPACING['md'], pady=SPACING['md'])
        
        # 球队名称标签
        team_name_var = self.home_name_var if team_type == 'home' else self.away_name_var
        team_color = self.team_home_color if team_type == 'home' else self.team_away_color
        text_color = get_contrast_text_color(team_color)
        team_label = Label(input_frame, textvariable=team_name_var, font=FONTS['subheading'],
                          bg=team_color, fg=text_color, width=10, relief=FLAT,
                          padx=SPACING['md'], pady=SPACING['sm'])
        team_label.pack(side=LEFT, padx=(0, SPACING['md']))
        color_labels = self.home_color_labels if team_type == 'home' else self.away_color_labels
        color_labels.append((None, team_label))
        
        # 输入提示
        Label(input_frame, text=input_label, font=FONTS['small'],
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=LEFT, padx=(0, SPACING['xs']))
        
        # 输入框
        highlight = highlight_color or (COLORS['info'] if team_type == 'home' else COLORS['accent'])
        entry = Entry(input_frame, font=FONTS['input'], relief=FLAT,
                     highlightthickness=SIZES['border_width'], 
                     highlightbackground=COLORS['border'], highlightcolor=highlight,
                     width=12, bg='white', fg='black')
        entry.pack(side=LEFT, padx=SPACING['xs'], ipady=3)
        
        if entry_bind_key and callable(entry_bind_key):
            entry.bind('<Return>', lambda e: entry_bind_key())
        
        # 操作按钮
        if add_command:
            Button(input_frame, text=add_text, bg=COLORS['success'], fg='black',
                   font=FONTS['button'], relief=FLAT, cursor="hand2",
                   padx=SPACING['md'], pady=SPACING['xs'], activeforeground='black',
                   command=add_command).pack(side=LEFT, padx=SPACING['xs'])
        
        if clear_command:
            Button(input_frame, text="清空", bg=COLORS['danger'], fg='black',
                   font=FONTS['button'], relief=FLAT, cursor="hand2",
                   padx=SPACING['md'], pady=SPACING['xs'], activeforeground='black',
                   command=clear_command).pack(side=LEFT, padx=SPACING['xs'])
        
        return entry
    
    def create_team_panel(self, parent, row, team_type, title_label, input_label, 
                          input_width=12, cards_frame_attr=None, add_command=None,
                          clear_command=None, extra_buttons=None):
        """创建统一的主队/客队面板（输入区域+卡片容器）"""
        # 主面板Frame
        panel_frame = Frame(parent, bg=COLORS['bg_card'],
                          highlightthickness=SIZES['border_width'],
                          highlightbackground=COLORS['border'])
        # 动态计算间距：第一个面板（row较小）顶部间距，最后一个面板底部间距较大
        # 获取父容器的行配置数量来判断是否是最后一行
        pady_top = SPACING['xs']
        # 检查是否是最后一个可配置的行（如果是偶数行或较大的行，给底部更多间距）
        pady_bottom = SPACING['md'] if row >= 2 else SPACING['xs']
        panel_frame.grid(row=row, column=0, sticky="nsew", padx=SPACING['md'], pady=(pady_top, pady_bottom))
        
        # 输入区域
        entry = self.create_input_area(panel_frame, team_type, input_label,
                                      entry_bind_key=add_command, add_command=add_command,
                                      clear_command=clear_command)
        
        # 记录标题
        Label(panel_frame, text=title_label, font=FONTS['small'],
             bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(anchor=W, padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        # 卡片容器（带滚动条）
        container, canvas, cards_frame = self.create_scrollable_canvas(panel_frame, cards_frame_attr)
        
        # 存储canvas引用（如果需要）
        if cards_frame_attr:
            setattr(self, cards_frame_attr.replace('_frame', '_canvas'), canvas)
        
        return panel_frame, entry, cards_frame
    
    def create_preview_container(self, parent, row, title, preview_bg, preview_content_creator):
        """创建统一预览容器"""
        preview_container = Frame(parent, bg=COLORS['bg_dark'],
                                 highlightthickness=2, highlightbackground=COLORS['warning'])
        preview_container.grid(row=row, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])
        
        # 预览标题
        preview_header = Frame(preview_container, bg=COLORS['warning'], height=40)
        preview_header.pack(fill=X)
        preview_header.pack_propagate(False)
        Label(preview_header, text=title, font=FONTS['heading'],
              bg=COLORS['warning'], fg=COLORS['text_light']).pack(expand=True)
        
        # 预览内容（由回调函数创建）
        preview_content = preview_content_creator(preview_container)
        
        return preview_container, preview_content
    
    def create_button(self, parent, text, bg_color, command, fg='black', width=None,
                     padx=None, pady=None, side=LEFT, **kwargs):
        """创建统一风格的按钮"""
        default_padx = padx if padx is not None else SPACING['md']
        default_pady = pady if pady is not None else SPACING['xs']
        
        btn = Button(parent, text=text, bg=bg_color, fg=fg, font=FONTS['button'],
                    relief=FLAT, cursor="hand2", padx=default_padx, pady=default_pady,
                    activeforeground=fg, command=command, **kwargs)
        if width:
            btn.config(width=width)
        btn.pack(side=side, padx=SPACING['xs'])
        return btn
    
    def _create_subtitle_config_row(self, parent, label_text, sub_type):
        """创建字幕配置行"""
        row_frame = Frame(parent, bg="white", highlightthickness=1, highlightbackground=COLORS['border_light'])
        row_frame.pack(fill=X, pady=SPACING['xs'])
        
        Label(row_frame, text=label_text, font=FONTS['body'], bg="white",
              fg=COLORS['text_dark'], width=12, anchor=W).pack(side=LEFT, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Input通道输入框
        input_entry = Entry(row_frame, font=FONTS['input'], relief=FLAT,
                           bg='white', fg='black',
                           highlightthickness=1, highlightbackground=COLORS['border'], width=12)
        input_entry.pack(side=LEFT, padx=SPACING['md'], ipady=2)
        
        # Layer输入框
        layer_entry = Entry(row_frame, font=FONTS['input'], relief=FLAT,
                           bg='white', fg='black',
                           highlightthickness=1, highlightbackground=COLORS['border'], width=12)
        layer_entry.pack(side=LEFT, padx=SPACING['md'], ipady=2)
        
        # 延迟时间输入框
        delay_entry = Entry(row_frame, font=FONTS['input'], relief=FLAT,
                           bg='white', fg='black',
                           highlightthickness=1, highlightbackground=COLORS['border'], width=12)
        delay_entry.pack(side=LEFT, padx=SPACING['md'], ipady=2)
        
        # 根据类型设置初始值和存储引用
        if sub_type == "red":
            input_entry.insert(0, self.vmix.red_card_input)
            layer_entry.insert(0, self.vmix.red_card_layer)
            delay_entry.insert(0, str(self.vmix.red_card_delay))
            self.vmix_red_input_entry = input_entry
            self.vmix_red_layer_entry = layer_entry
            self.vmix_red_delay_entry = delay_entry
        elif sub_type == "yellow":
            input_entry.insert(0, self.vmix.yellow_card_input)
            layer_entry.insert(0, self.vmix.yellow_card_layer)
            delay_entry.insert(0, str(self.vmix.yellow_card_delay))
            self.vmix_yellow_input_entry = input_entry
            self.vmix_yellow_layer_entry = layer_entry
            self.vmix_yellow_delay_entry = delay_entry
        elif sub_type == "sub":
            input_entry.insert(0, self.vmix.sub_input)
            layer_entry.insert(0, self.vmix.sub_layer)
            delay_entry.insert(0, str(self.vmix.sub_delay))
            self.vmix_sub_input_entry = input_entry
            self.vmix_sub_layer_entry = layer_entry
            self.vmix_sub_delay_entry = delay_entry
        elif sub_type == "goal":
            input_entry.insert(0, self.vmix.goal_input)
            layer_entry.insert(0, self.vmix.goal_layer)
            delay_entry.insert(0, str(self.vmix.goal_delay))
            self.vmix_goal_input_entry = input_entry
            self.vmix_goal_layer_entry = layer_entry
            self.vmix_goal_delay_entry = delay_entry
    
    def status_bar_connect(self):
        """状态栏连接按钮的处理方法"""
        # 尝试连接
        if self.vmix.connect():
            # 连接成功，更新状态
            self.last_connected_state = True
            self.reconnect_attempt_count = 0
            self.should_auto_reconnect = True  # 重置自动重连标志
            self.has_alerted_disconnect = False  # 重置断开提醒标志
            # 隐藏连接按钮
            if hasattr(self, 'status_vmix_connect_btn'):
                if self.status_vmix_connect_btn.winfo_viewable():
                    self.status_vmix_connect_btn.pack_forget()
            # 更新状态栏
            self.check_vmix_connection()
            # 更新vMix配置页面的状态（如果存在）
            if hasattr(self, 'vmix_status_indicator'):
                self.vmix_status_indicator.config(fg="green")
            if hasattr(self, 'vmix_status_label'):
                self.vmix_status_label.config(text="已连接", fg=COLORS['success'])
        else:
            # 连接失败，确保按钮显示
            self.last_connected_state = False
            # 显示连接按钮
            if hasattr(self, 'status_vmix_connect_btn'):
                if not self.status_vmix_connect_btn.winfo_viewable():
                    self.status_vmix_connect_btn.pack(side=LEFT, padx=(SPACING['sm'], 0))
            # 更新状态栏
            self.check_vmix_connection()
            # 更新vMix配置页面的状态（如果存在）
            if hasattr(self, 'vmix_status_indicator'):
                self.vmix_status_indicator.config(fg="red")
            if hasattr(self, 'vmix_status_label'):
                self.vmix_status_label.config(text="连接失败", fg=COLORS['danger'])
    
    def vmix_connect(self):
        """连接vMix"""
        # 更新配置
        self.vmix.host = self.vmix_ip_entry.get().strip()
        try:
            self.vmix.port = int(self.vmix_port_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.port = 8099
        
        # 尝试连接
        if self.vmix.connect():
            self.vmix_status_indicator.config(fg="green")
            self.vmix_status_label.config(text="已连接", fg=COLORS['success'])
            self.last_connected_state = True
            self.reconnect_attempt_count = 0
            self.should_auto_reconnect = True  # 重置自动重连标志
            self.has_alerted_disconnect = False  # 重置断开提醒标志
            # 更新状态栏
            self.check_vmix_connection()
        else:
            self.vmix_status_indicator.config(fg="red")
            self.vmix_status_label.config(text="连接失败", fg=COLORS['danger'])
            self.last_connected_state = False
            # 更新状态栏
            self.check_vmix_connection()
    
    def vmix_disconnect(self):
        """断开vMix连接"""
        self.vmix.disconnect()
        self.vmix_status_indicator.config(fg="gray")
        self.vmix_status_label.config(text="未连接", fg=COLORS['text_muted'])
        self.last_connected_state = False
        self.reconnect_attempt_count = 0  # 手动断开时重置重连计数
        self.should_auto_reconnect = False  # 手动断开后，不自动重连
        # 显示连接按钮
        if hasattr(self, 'status_vmix_connect_btn'):
            if not self.status_vmix_connect_btn.winfo_viewable():
                self.status_vmix_connect_btn.pack(side=LEFT, padx=(SPACING['sm'], 0))
        # 更新状态栏
        self.check_vmix_connection()
    
    def vmix_save_config(self):
        """保存vMix配置"""
        # 保存红牌配置
        self.vmix.red_card_input = self.vmix_red_input_entry.get().strip()
        self.vmix.red_card_layer = self.vmix_red_layer_entry.get().strip()
        try:
            self.vmix.red_card_delay = float(self.vmix_red_delay_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.red_card_delay = DELAYS['RED_CARD']
        
        # 保存黄牌配置
        self.vmix.yellow_card_input = self.vmix_yellow_input_entry.get().strip()
        self.vmix.yellow_card_layer = self.vmix_yellow_layer_entry.get().strip()
        try:
            self.vmix.yellow_card_delay = float(self.vmix_yellow_delay_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.yellow_card_delay = DELAYS['YELLOW_CARD']
        
        # 保存换人配置
        self.vmix.sub_input = self.vmix_sub_input_entry.get().strip()
        self.vmix.sub_layer = self.vmix_sub_layer_entry.get().strip()
        try:
            self.vmix.sub_delay = float(self.vmix_sub_delay_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.sub_delay = DELAYS['SUB']
        
        # 保存进球配置
        self.vmix.goal_input = self.vmix_goal_input_entry.get().strip()
        self.vmix.goal_layer = self.vmix_goal_layer_entry.get().strip()
        try:
            self.vmix.goal_delay = float(self.vmix_goal_delay_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.goal_delay = DELAYS['GOAL']
        
        # 保存IP和端口
        self.vmix.host = self.vmix_ip_entry.get().strip()
        try:
            self.vmix.port = int(self.vmix_port_entry.get().strip())
        except (ValueError, AttributeError):
            self.vmix.port = 8099
        
        # 持久化保存到文件
        self.vmix.save_config()
        print("✓ vMix配置已保存")
    
    def choose_team_color(self, team_type):
        """打开颜色选择器"""
        if team_type == 'home':
            current_color = self.team_home_color_entry.get()
        else:
            current_color = self.team_away_color_entry.get()
        
        # 打开颜色选择对话框
        color_code = colorchooser.askcolor(title="选择球队颜色", initialcolor=current_color)
        
        if color_code[1]:  # 用户选择了颜色
            hex_color = color_code[1].upper()
            if team_type == 'home':
                self.team_home_color_entry.delete(0, END)
                self.team_home_color_entry.insert(0, hex_color)
                # 根据新背景色自动计算合适的文字颜色
                preview_text_color = get_contrast_text_color(hex_color)
                self.team_home_color_preview.config(bg=hex_color, fg=preview_text_color)
            else:
                self.team_away_color_entry.delete(0, END)
                self.team_away_color_entry.insert(0, hex_color)
                # 根据新背景色自动计算合适的文字颜色
                preview_text_color = get_contrast_text_color(hex_color)
                self.team_away_color_preview.config(bg=hex_color, fg=preview_text_color)
    
    def save_team_settings(self):
        """保存球队设置（保存到统一配置文件）"""
        home_name = self.team_home_name_entry.get().strip()
        away_name = self.team_away_name_entry.get().strip()
        
        if not home_name or not away_name:
            print("✗ 球队名称不能为空")
            return
        
        # 获取新颜色值
        new_home_color = self.team_home_color_entry.get().strip()
        new_away_color = self.team_away_color_entry.get().strip()
        
        # 保存旧颜色（用于更新UI时匹配需要更新的元素）
        self._old_home_color = self.team_home_color
        self._old_away_color = self.team_away_color
        
        # 更新vMix控制器中的球队配置
        self.vmix.team_name_home = home_name
        self.vmix.team_name_away = away_name
        self.vmix.team_home_color = new_home_color
        self.vmix.team_away_color = new_away_color
        
        # 保存到统一配置文件（config.json）
        self.vmix.save_config()
        
        # 更新本地变量（必须在更新UI之前）
        self.team_home_color = new_home_color
        self.team_away_color = new_away_color
        
        # 立即更新全局变量和界面显示
        global teamname_home, teamname_away
        teamname_home = home_name
        teamname_away = away_name
        
        # 更新所有界面上的球队名称和颜色
        self.update_team_names_in_ui()
        
        # 更新scoreboard.csv文件（包含球队名称和颜色）
        self._save_scoreboard()
        
        print(f"✓ 球队设置已保存到配置文件: 主队={home_name} ({new_home_color}), 客队={away_name} ({new_away_color})")
        print("✓ 球队名称已更新到界面")
        print("✓ scoreboard.csv 已更新")
    
    def save_substitutions(self, team_name, player_out, player_in):
        """保存最新一条换人记录到统一的CSV文件
        格式：
        球队名称,换下号码,换下姓名
        球队名称,换上号码,换上姓名
        """
        try:
            # 解析球员信息：号码,姓名
            out_parts = player_out.split(',')
            in_parts = player_in.split(',')
            
            if len(out_parts) == 2 and len(in_parts) == 2:
                content = f"{team_name},{out_parts[0]},{out_parts[1]}\n"
                content += f"{team_name},{in_parts[0]},{in_parts[1]}\n"
                if FileManager.write_csv('substitutions.csv', content):
                    print(f"✓ 已保存最新换人记录到 substitutions.csv")
        except (ValueError, IndexError) as e:
            print(f"保存换人记录失败: {e}")
    
    def update_team_names_in_ui(self):
        """更新界面上所有显示球队名称的地方"""
        # 更新StringVar，这会自动更新所有绑定的Label
        self.home_name_var.set(f"[主队]{teamname_home}")
        self.away_name_var.set(f"[客队]{teamname_away}")
        # 更新计分板的球队名称
        self.scoreboard_home_name_var.set(teamname_home)
        self.scoreboard_away_name_var.set(teamname_away)
        
        # 更新所有主队标签的颜色（兼容不同存储格式）
        old_home_color = getattr(self, '_old_home_color', self.team_home_color)
        for item in self.home_color_labels:
            try:
                if isinstance(item, tuple):
                    # 格式: (frame, label)
                    frame, label = item
                    if frame:
                        try:
                            # 检查背景色是否为球队颜色，如果是则更新
                            # 统一转换为大写进行比较，避免大小写不一致问题
                            if hasattr(frame, 'cget'):
                                bg = frame.cget('bg')
                                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                                if str(bg).upper() == str(old_home_color).upper():
                                    frame.config(bg=self.team_home_color)
                        except (TclError, AttributeError):
                            pass
                    if label:
                        try:
                            # 更新背景色
                            if hasattr(label, 'cget'):
                                bg = label.cget('bg')
                                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                                if str(bg).upper() == str(old_home_color).upper():
                                    label.config(bg=self.team_home_color)
                                    # 根据新背景色自动计算合适的文字颜色
                                    text_color = get_contrast_text_color(self.team_home_color)
                                    label.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
                else:
                    # 单个对象（Frame或Label）
                    if hasattr(item, 'config') and hasattr(item, 'cget'):
                        try:
                            # 更新背景色
                            bg = item.cget('bg')
                            # 统一转换为大写进行比较（颜色值可能有大小写差异）
                            if str(bg).upper() == str(old_home_color).upper():
                                item.config(bg=self.team_home_color)
                                # 如果是Label，根据新背景色自动计算合适的文字颜色
                                if isinstance(item, Label):
                                    text_color = get_contrast_text_color(self.team_home_color)
                                    item.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
            except (TclError, AttributeError, RuntimeError):
                pass  # 忽略错误，继续更新其他元素
        
        # 更新所有客队标签的颜色（兼容不同存储格式）
        old_away_color = getattr(self, '_old_away_color', self.team_away_color)
        for item in self.away_color_labels:
            try:
                if isinstance(item, tuple):
                    # 格式: (frame, label)
                    frame, label = item
                    if frame:
                        try:
                            # 检查背景色是否为球队颜色，如果是则更新
                            # 统一转换为大写进行比较，避免大小写不一致问题
                            if hasattr(frame, 'cget'):
                                bg = frame.cget('bg')
                                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                                if str(bg).upper() == str(old_away_color).upper():
                                    frame.config(bg=self.team_away_color)
                        except (TclError, AttributeError):
                            pass
                    if label:
                        try:
                            # 更新背景色
                            if hasattr(label, 'cget'):
                                bg = label.cget('bg')
                                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                                if str(bg).upper() == str(old_away_color).upper():
                                    label.config(bg=self.team_away_color)
                                    # 根据新背景色自动计算合适的文字颜色
                                    text_color = get_contrast_text_color(self.team_away_color)
                                    label.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
                else:
                    # 单个对象（Frame或Label）
                    if hasattr(item, 'config') and hasattr(item, 'cget'):
                        try:
                            # 更新背景色
                            bg = item.cget('bg')
                            # 统一转换为大写进行比较（颜色值可能有大小写差异）
                            if str(bg).upper() == str(old_away_color).upper():
                                item.config(bg=self.team_away_color)
                                # 如果是Label，根据新背景色自动计算合适的文字颜色
                                if isinstance(item, Label):
                                    text_color = get_contrast_text_color(self.team_away_color)
                                    item.config(fg=text_color)
                        except (TclError, AttributeError):
                            pass
            except (TclError, AttributeError, RuntimeError):
                pass  # 忽略错误，继续更新其他元素
        
        # 更新预览标题的背景和文字颜色
        # 红黄牌预览标题
        if hasattr(self, 'card_preview_header') and hasattr(self, 'card_preview_title_label'):
            try:
                current_bg = self.card_preview_header.cget('bg')
                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                current_bg_upper = str(current_bg).upper()
                old_home_upper = str(old_home_color).upper()
                old_away_upper = str(old_away_color).upper()
                if current_bg_upper == old_home_upper or current_bg_upper == old_away_upper:
                    # 根据当前显示的是哪个队来确定颜色
                    if current_bg_upper == old_home_upper:
                        self.card_preview_header.config(bg=self.team_home_color)
                        text_color = get_contrast_text_color(self.team_home_color)
                    else:
                        self.card_preview_header.config(bg=self.team_away_color)
                        text_color = get_contrast_text_color(self.team_away_color)
                    self.card_preview_title_label.config(bg=self.card_preview_header.cget('bg'), fg=text_color)
            except (TclError, AttributeError):
                pass
        
        # 进球预览标题
        if hasattr(self, 'goal_preview_header') and hasattr(self, 'goal_preview_title_label'):
            try:
                current_bg = self.goal_preview_header.cget('bg')
                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                current_bg_upper = str(current_bg).upper()
                old_home_upper = str(old_home_color).upper()
                old_away_upper = str(old_away_color).upper()
                if current_bg_upper == old_home_upper or current_bg_upper == old_away_upper:
                    if current_bg_upper == old_home_upper:
                        self.goal_preview_header.config(bg=self.team_home_color)
                        text_color = get_contrast_text_color(self.team_home_color)
                    else:
                        self.goal_preview_header.config(bg=self.team_away_color)
                        text_color = get_contrast_text_color(self.team_away_color)
                    self.goal_preview_title_label.config(bg=self.goal_preview_header.cget('bg'), fg=text_color)
            except (TclError, AttributeError):
                pass
        
        # 换人预览标题
        if hasattr(self, 'sub_preview_header') and hasattr(self, 'sub_preview_title_label'):
            try:
                current_bg = self.sub_preview_header.cget('bg')
                # 统一转换为大写进行比较（颜色值可能有大小写差异）
                current_bg_upper = str(current_bg).upper()
                old_home_upper = str(old_home_color).upper()
                old_away_upper = str(old_away_color).upper()
                if current_bg_upper == old_home_upper or current_bg_upper == old_away_upper:
                    if current_bg_upper == old_home_upper:
                        self.sub_preview_header.config(bg=self.team_home_color)
                        text_color = get_contrast_text_color(self.team_home_color)
                    else:
                        self.sub_preview_header.config(bg=self.team_away_color)
                        text_color = get_contrast_text_color(self.team_away_color)
                    self.sub_preview_title_label.config(bg=self.sub_preview_header.cget('bg'), fg=text_color)
            except (TclError, AttributeError):
                pass
        
        # 显示成功提示
        from tkinter import messagebox
        messagebox.showinfo("保存成功", 
                           f"球队设置已保存并立即生效！\n\n"
                           f"主队: {teamname_home} ({self.team_home_color})\n"
                           f"客队: {teamname_away} ({self.team_away_color})")

    def create_status_bar(self):
        """创建底部状态栏显示vMix连接状态（确保层级最高）"""
        status_frame = Frame(self.init_window_name, bg=COLORS['bg_card'],
                           height=35, relief=FLAT, bd=0,
                           highlightthickness=1, highlightbackground=COLORS['border'])
        status_frame.pack(side=BOTTOM, fill=X, padx=SPACING['md'], pady=(0, SPACING['md']))
        status_frame.pack_propagate(False)
        # 提升状态栏到最上层，确保始终可见
        status_frame.lift()
        self.status_frame = status_frame  # 保存引用以便后续操作
        
        # 左侧：vMix连接状态
        left_status = Frame(status_frame, bg=COLORS['bg_card'])
        left_status.pack(side=LEFT, fill=Y, padx=SPACING['md'])
        
        # 连接状态指示器
        self.status_vmix_indicator = Label(left_status, text="●", font=('Arial', 16),
                                          bg=COLORS['bg_card'], fg="gray")
        self.status_vmix_indicator.pack(side=LEFT, padx=(0, SPACING['xs']))
        
        # 连接状态文本
        self.status_vmix_text = Label(left_status, text="vMix: 未连接", font=FONTS['small'],
                                     bg=COLORS['bg_card'], fg=COLORS['text_muted'])
        self.status_vmix_text.pack(side=LEFT, padx=(0, SPACING['md']))
        
        # 连接地址信息
        self.status_vmix_addr = Label(left_status, text="", font=FONTS['small'],
                                     bg=COLORS['bg_card'], fg=COLORS['text_muted'])
        self.status_vmix_addr.pack(side=LEFT)
        
        # 连接按钮（只在未连接时显示）
        self.status_vmix_connect_btn = Button(left_status, text="连接", font=FONTS['small'],
                                             bg=COLORS['success'], fg='white',
                                             relief=FLAT, padx=SPACING['sm'], pady=SPACING['xs'],
                                             cursor="hand2", command=self.status_bar_connect)
        # 初始状态：未连接，显示按钮
        self.status_vmix_connect_btn.pack(side=LEFT, padx=(SPACING['sm'], 0))
        
        # 右侧：版权信息
        right_status = Frame(status_frame, bg=COLORS['bg_card'])
        right_status.pack(side=RIGHT, fill=Y, padx=SPACING['md'])
        
        # 版权信息文本
        copyright_text = "重庆寰网致博体育文化传播有限公司 | 环网直播 | 18523999949"
        copyright_label = Label(right_status, text=copyright_text, font=FONTS['small'],
                               bg=COLORS['bg_card'], fg=COLORS['text_muted'])
        copyright_label.pack(side=RIGHT)
        
        # 初始化状态显示
        self.update_status_bar()
        
        # 启动定期检查连接状态（每3秒检查一次）
        self.check_vmix_connection_periodically()
        
        # 自动连接vMix（延迟执行，确保界面已完全初始化）
        self.init_window_name.after(500, self.auto_connect_vmix)
    
    def auto_connect_vmix(self):
        """自动连接vMix（程序启动时调用）"""
        if self.vmix.connect():
            # 更新状态栏
            if hasattr(self, 'status_vmix_indicator'):
                self.status_vmix_indicator.config(fg="green")
            if hasattr(self, 'status_vmix_text'):
                self.status_vmix_text.config(text="vMix: 已连接", fg=COLORS['success'])
            # 更新vMix配置页面的状态（如果已创建）
            if hasattr(self, 'vmix_status_indicator'):
                self.vmix_status_indicator.config(fg="green")
            if hasattr(self, 'vmix_status_label'):
                self.vmix_status_label.config(text="已连接", fg=COLORS['success'])
            self.last_connected_state = True
            self.is_first_connect_attempt = False
            self.reconnect_attempt_count = 0
            self.should_auto_reconnect = True
            self.has_alerted_disconnect = False  # 重置断开提醒标志
            # 隐藏连接按钮
            if hasattr(self, 'status_vmix_connect_btn'):
                if self.status_vmix_connect_btn.winfo_viewable():
                    self.status_vmix_connect_btn.pack_forget()
            print("✓ 自动连接vMix成功")
        else:
            # 更新状态栏
            if hasattr(self, 'status_vmix_indicator'):
                self.status_vmix_indicator.config(fg="gray")
            if hasattr(self, 'status_vmix_text'):
                self.status_vmix_text.config(text="vMix: 未连接", fg=COLORS['text_muted'])
            # 更新vMix配置页面的状态（如果已创建）
            if hasattr(self, 'vmix_status_indicator'):
                self.vmix_status_indicator.config(fg="red")
            if hasattr(self, 'vmix_status_label'):
                self.vmix_status_label.config(text="连接失败", fg=COLORS['danger'])
            self.last_connected_state = False
            self.is_first_connect_attempt = False
            self.should_auto_reconnect = False  # 首次连接失败后，不自动重连，等待用户手动连接
            
            # 确保显示连接按钮（初始状态已显示，这里确保显示）
            if hasattr(self, 'status_vmix_connect_btn'):
                if not self.status_vmix_connect_btn.winfo_viewable():
                    self.status_vmix_connect_btn.pack(side=LEFT, padx=(SPACING['sm'], 0))
            
            # 首次连接失败时弹窗提醒
            from tkinter import messagebox
            messagebox.showwarning(
                "vMix连接失败",
                f"无法连接到vMix服务器！\n\n"
                f"地址: {self.vmix.host}:{self.vmix.port}\n\n"
                f"请检查：\n"
                f"1. vMix是否正在运行\n"
                f"2. 网络连接是否正常\n"
                f"3. IP地址和端口是否正确\n\n"
                f"请点击状态栏的\"连接\"按钮手动连接。"
            )
            print("✗ 自动连接vMix失败")
    
    def check_vmix_connection_periodically(self):
        """定期检查vMix连接状态"""
        # 检查连接状态
        self.check_vmix_connection()
        
        # 使用常量定义的检查间隔
        self.init_window_name.after(TIMEOUTS['CHECK_INTERVAL'], self.check_vmix_connection_periodically)
    
    def check_vmix_connection(self):
        """检查vMix连接状态（优化：使用轻量级socket状态检查，减少网络负载）"""
        # 更新连接地址显示
        addr_text = f"{self.vmix.host}:{self.vmix.port}"
        self.status_vmix_addr.config(text=addr_text)
        
        if self.vmix.connected and self.vmix.socket:
            # 优化：使用getsockopt检查socket状态，避免发送测试命令减少网络负载
            try:
                # 使用getsockopt检查socket错误状态（轻量级，不发送数据）
                error_code = self.vmix.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if error_code != 0:
                    raise OSError(f"Socket error: {error_code}")
                
                # 连接正常
                self.status_vmix_indicator.config(fg="green")
                self.status_vmix_text.config(text="vMix: 已连接", fg=COLORS['success'])
                # 如果之前未连接，现在已连接，重置重连计数和自动重连标志
                if not self.last_connected_state:
                    self.reconnect_attempt_count = 0
                    self.should_auto_reconnect = True  # 连接成功后，重置自动重连标志
                    self.has_alerted_disconnect = False  # 重置断开提醒标志，下次断开时可以再次提醒
                self.last_connected_state = True
                # 隐藏连接按钮
                if hasattr(self, 'status_vmix_connect_btn'):
                    self.status_vmix_connect_btn.pack_forget()
                return
                
            except (OSError, socket.error, AttributeError) as e:
                # 检查失败，连接已断开
                print(f"✗ vMix连接检查失败: {e}")
                try:
                    self.vmix.socket.close()
                except (OSError, socket.error, AttributeError):
                    pass
                self.vmix.socket = None
                self.vmix.connected = False
        
        # 未连接状态
        if not self.vmix.connected or not self.vmix.socket:
            # 如果之前是连接状态，现在断开了
            if self.last_connected_state and not self.is_first_connect_attempt:
                # 第一次检测到断开，立即弹窗提醒，并停止自动重连（只弹窗一次）
                if not self.has_alerted_disconnect:
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "vMix连接断开",
                        f"检测到vMix连接已断开！\n\n"
                        f"地址: {self.vmix.host}:{self.vmix.port}\n\n"
                        f"可能原因：\n"
                        f"1. vMix程序已关闭\n"
                        f"2. 网络连接中断\n"
                        f"3. 防火墙阻止连接\n\n"
                        f"请点击状态栏的\"连接\"按钮手动重新连接。"
                    )
                    print("✗ 检测到vMix连接断开，已停止自动重连")
                    # 停止自动重连，等待用户手动连接
                    self.should_auto_reconnect = False
                    # 标记已经弹窗提醒过，避免重复弹窗
                    self.has_alerted_disconnect = True
            
            # 更新UI显示为未连接状态
            self.status_vmix_indicator.config(fg="gray")
            self.status_vmix_text.config(text="vMix: 未连接", fg=COLORS['text_muted'])
            
            # 显示连接按钮（如果未显示）
            if hasattr(self, 'status_vmix_connect_btn'):
                # 使用winfo_viewable()检查按钮是否可见，比异常处理更优雅
                if not self.status_vmix_connect_btn.winfo_viewable():
                    self.status_vmix_connect_btn.pack(side=LEFT, padx=(SPACING['sm'], 0))
            
            # 同时更新vMix配置页面的状态显示（如果存在）
            if hasattr(self, 'vmix_status_indicator'):
                self.vmix_status_indicator.config(fg="gray")
            if hasattr(self, 'vmix_status_label'):
                self.vmix_status_label.config(text="未连接", fg=COLORS['text_muted'])
            
            # 更新连接状态标记：只有在已经尝试过重连且重连失败后，才更新标记
            # 如果之前是连接状态，现在断开了，但在本次检查中已经尝试了重连，保持 last_connected_state 不变
            # 这样可以确保下次检查时继续尝试重连
            # 只有当手动断开或首次连接失败时，才设置为 False
            if not (self.last_connected_state and not self.is_first_connect_attempt):
                # 如果之前就不是连接状态（首次连接失败或手动断开），更新标记
                self.last_connected_state = False
    
    def update_status_bar(self):
        """更新状态栏显示"""
        # 初始检查
        self.check_vmix_connection()
    
    def show_panel(self, panel_name):
        """切换右侧显示的面板（确保状态栏始终可见）"""
        # 隐藏当前面板
        if self.current_panel:
            self.current_panel.pack_forget()
        
        # 显示新面板
        panel_map = {
            'player_list': self.frame_player_list,
            'sub': self.frame_sub,
            'cards': self.frame_red_yellow_card,
            'goal': self.frame_goal,
            'vmix': self.frame_vmix_config,
            'team_settings': self.frame_team_settings
        }
        
        if panel_name in panel_map:
            self.current_panel = panel_map[panel_name]
            self.current_panel.pack(fill=BOTH, expand=True)
            # 强制更新显示
            self.right_content.update_idletasks()
            # 确保状态栏始终在最上层可见
            if hasattr(self, 'status_frame'):
                self.status_frame.lift()

    '''换人 - 使用通用方法减少重复代码'''
    def create_sub_card(self, parent_frame, index, player_out, player_in, timestamp, select_callback, delete_callback):
        """通用换人卡片创建方法（优化布局，紧凑美观）"""
        # 使用Grid布局，支持多列显示以减少空间浪费
        # 卡片样式：现代扁平设计，带边框阴影效果
        card = Frame(parent_frame, bg=COLORS['bg_card'], relief=FLAT, bd=1,
                    highlightthickness=1, highlightbackground=COLORS['border'])
        card.grid(row=index // 7, column=index % 7, padx=SPACING['xs'], pady=SPACING['xs'], 
                 sticky="nsew")
        
        # 确保父容器已配置Grid列（如果还没有）
        col = index % 7
        try:
            parent_frame.grid_columnconfigure(col, weight=1, uniform="card_col")
        except (TclError, AttributeError):
            pass
        
        # 卡片内容容器（紧凑布局）
        card_content = Frame(card, bg=COLORS['bg_card'], padx=SPACING['sm'], pady=SPACING['xs'])
        card_content.pack(fill=BOTH, expand=True)
        
        # 顶部选中指示条（初始隐藏，通过高度控制显示）
        selected_indicator = Frame(card_content, bg=COLORS['info'], height=0)
        selected_indicator.pack(fill=X, pady=(0, SPACING['xs']))
        selected_indicator.pack_propagate(False)
        card.selected_indicator = selected_indicator
        
        # 顶部：编号和时间（增大字体）
        top_line = Frame(card_content, bg=COLORS['bg_card'], height=24)
        top_line.pack(fill=X)
        top_line.pack_propagate(False)
        Label(top_line, text=f"#{index+1}", font=('YaHei', 9, 'bold'), 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=LEFT)
        Label(top_line, text=timestamp, font=('YaHei', 8), 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=RIGHT)
        
        # 换下区域（增大字体，使用左侧颜色条）
        out_frame = Frame(card_content, bg=COLORS['bg_card'], height=40)
        out_frame.pack(fill=X, pady=(SPACING['xs']//2, 0))
        out_frame.pack_propagate(False)
        
        # 左侧颜色指示条
        out_indicator = Frame(out_frame, bg="#E53935", width=4)
        out_indicator.pack(side=LEFT, fill=Y, padx=(0, SPACING['xs']))
        out_indicator.pack_propagate(False)
        
        # 换下信息（增大字体）
        out_info = Frame(out_frame, bg=COLORS['bg_card'])
        out_info.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, SPACING['xs']))
        Label(out_info, text="↓ 换下", font=('YaHei', 8, 'bold'), 
              bg=COLORS['bg_card'], fg="#E53935", anchor=W).pack(anchor=W)
        Label(out_info, text=player_out, font=('YaHei', 9), 
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], anchor=W, 
              wraplength=80, justify=LEFT).pack(anchor=W, pady=(2, 0))
        
        # 换上区域（增大字体，使用左侧颜色条）
        in_frame = Frame(card_content, bg=COLORS['bg_card'], height=40)
        in_frame.pack(fill=X, pady=(SPACING['xs']//2, 0))
        in_frame.pack_propagate(False)
        
        # 左侧颜色指示条
        in_indicator = Frame(in_frame, bg="#388E3C", width=4)
        in_indicator.pack(side=LEFT, fill=Y, padx=(0, SPACING['xs']))
        in_indicator.pack_propagate(False)
        
        # 换上信息（增大字体）
        in_info = Frame(in_frame, bg=COLORS['bg_card'])
        in_info.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, SPACING['xs']))
        Label(in_info, text="↑ 换上", font=('YaHei', 8, 'bold'), 
              bg=COLORS['bg_card'], fg="#388E3C", anchor=W).pack(anchor=W)
        Label(in_info, text=player_in, font=('YaHei', 9), 
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], anchor=W, 
              wraplength=80, justify=LEFT).pack(anchor=W, pady=(2, 0))
        
        # 删除按钮（紧凑，小尺寸）
        btn_delete = Button(card_content, text="✕", bg="#DC3545", fg="white", 
                           font=('Arial', 9, 'bold'), relief=FLAT, cursor="hand2", 
                           padx=SPACING['sm'], pady=SPACING['xs']//2, bd=0, 
                           command=delete_callback,
                           activebackground="#C62828", activeforeground="white")
        btn_delete.pack(fill=X, pady=(SPACING['xs'], 0))
        
        card.card_index = index
        # 绑定点击事件（除了删除按钮）
        def bind_click(widget):
            if not isinstance(widget, Button):
                widget.bind("<Button-1>", lambda e: select_callback())
            for child in widget.winfo_children():
                if child != btn_delete:
                    bind_click(child)
        bind_click(card)
    
    def create_sub_card_away(self, index, player_out, player_in, timestamp):
        self.create_sub_card(self.sub_away_cards_frame, index, player_out, player_in, timestamp,
                           lambda: self.select_sub_card_away(index), lambda: self.delete_sub_card_away(index))
    
    def create_sub_card_home(self, index, player_out, player_in, timestamp):
        self.create_sub_card(self.sub_home_cards_frame, index, player_out, player_in, timestamp,
                           lambda: self.select_sub_card_home(index), lambda: self.delete_sub_card_home(index))

    # 根据编号查找球员信息
    def find_player_by_number(self, number, player_list):
        """根据编号查找球员，返回完整信息（编号,姓名）"""
        number = number.strip()
        for player in player_list:
            if player.startswith(number + ","):
                return player
        return None
    
    # 解析输入的编号对
    def parse_sub_input(self, input_text):
        """解析输入的换人编号，返回(换下编号, 换上编号)或None
        支持任意符号（包括空格、逗号、横线等）分隔两个号码
        例如：22 34, 22,34, 22-34, 22/34 等都可以
        """
        input_text = input_text.strip()
        if not input_text:
            return None
        
        # 使用正则表达式提取所有数字
        numbers = re.findall(r'\d+', input_text)
        
        # 如果恰好找到2个数字，返回它们
        if len(numbers) == 2:
            return (numbers[0].strip(), numbers[1].strip())
        
        return None

    def _add_substitution(self, team_type, entry, out_label, in_label, sub_list, player_list, team_name):
        """通用添加换人方法（统一保存到 substitutions.csv）"""
        input_text = entry.get().strip()
        if not input_text:
            return
        
        result = self.parse_sub_input(input_text)
        if result is None:
            out_label.config(text="格式错误！")
            in_label.config(text="应为：22 34 或 22,34")
            return
        
        out_num, in_num = result
        player_out = self.find_player_by_number(out_num, player_list)
        player_in = self.find_player_by_number(in_num, player_list)
        
        if player_out is None or player_in is None:
            out_label.config(text=f"编号 {out_num}" if player_out is None else "?")
            in_label.config(text=f"编号 {in_num}" if player_in is None else "?")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        sub_list.append((player_out, player_in, timestamp))
        
        # 统一保存到 substitutions.csv（不再单独保存主客队文件）
        self.save_substitutions(team_name, player_out, player_in)
        
        # 更新预览标题显示队伍名称和背景颜色
        if hasattr(self, 'sub_preview_title_var'):
            self.sub_preview_title_var.set(f"{team_name} - 换人字幕预览")
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'sub_preview_header'):
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            self.sub_preview_header.config(bg=team_color)
            if hasattr(self, 'sub_preview_title_label'):
                text_color = get_contrast_text_color(team_color)
                self.sub_preview_title_label.config(bg=team_color, fg=text_color)
        
        # 根据team_type调用对应的创建方法
        if team_type == 'away':
            self.create_sub_card_away(len(sub_list) - 1, player_out, player_in, timestamp)
        else:
            self.create_sub_card_home(len(sub_list) - 1, player_out, player_in, timestamp)
        
        out_label.config(text=player_out)
        in_label.config(text=player_in)
        entry.delete(0, END)
        print(f"✓ {'客队' if team_type == 'away' else '主队'}换人 - 换下：{player_out}，换上：{player_in}")
    
    def sub_away_add(self):
        self._add_substitution('away', self.sub_away_entry, self.sub_away_out_label, self.sub_away_in_label,
                              self.sub_away_list, away_list, teamname_away)
    
    def sub_home_add(self):
        self._add_substitution('home', self.sub_home_entry, self.sub_home_out_label, self.sub_home_in_label,
                              self.sub_home_list, home_list, teamname_home)

    def _select_sub_card(self, team_type, index, sub_list, out_label, in_label, cards_frame, team_name):
        """通用选择换人卡片方法（确保同时只能有一个卡片被选中）"""
        player_out, player_in, timestamp = sub_list[index]
        out_label.config(text=player_out)
        in_label.config(text=player_in)
        # 统一保存到 substitutions.csv（不再单独保存主客队文件）
        self.save_substitutions(team_name, player_out, player_in)
        
        # 更新预览标题显示队伍名称和背景颜色
        if hasattr(self, 'sub_preview_title_var'):
            self.sub_preview_title_var.set(f"{team_name} - 换人字幕预览")
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'sub_preview_header'):
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            self.sub_preview_header.config(bg=team_color)
            if hasattr(self, 'sub_preview_title_label'):
                text_color = get_contrast_text_color(team_color)
                self.sub_preview_title_label.config(bg=team_color, fg=text_color)
        
        # 更新选中状态（增强高亮效果，保持文字清晰）
        def update_card_style(card_widget, is_selected):
            try:
                if is_selected:
                    # 使用浅蓝色背景高亮，但足够深以保持文字清晰
                    highlight_bg = "#BBDEFB"  # 浅蓝色背景
                    card_widget.config(bg=highlight_bg, relief=RAISED, bd=3,
                                highlightthickness=4, highlightbackground="#2196F3")  # 深蓝色边框
                    # 显示选中指示条
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=5, bg="#2196F3")  # 深蓝色指示条
                    
                    # 更新卡片内容容器的背景色
                    for child in card_widget.winfo_children():
                        if isinstance(child, Frame):
                            try:
                                child_bg = child.cget('bg')
                                if child_bg == COLORS['bg_card']:
                                    child.config(bg=highlight_bg)
                                # 递归更新子组件背景色（但保留颜色指示条）
                                def update_children_bg(widget):
                                    for c in widget.winfo_children():
                                        if isinstance(c, (Frame, Label)):
                                            try:
                                                c_bg = c.cget('bg')
                                                # 不改变颜色指示条（红色#E53935和绿色#388E3C）和按钮的背景色
                                                if c_bg == COLORS['bg_card'] and c_bg not in ["#E53935", "#388E3C", "#DC3545"]:
                                                    c.config(bg=highlight_bg)
                                                # 颜色指示条保持原色
                                                elif c_bg in ["#E53935", "#388E3C"]:
                                                    pass  # 保持原色
                                                update_children_bg(c)
                                            except (TclError, AttributeError, RuntimeError):
                                                pass
                                update_children_bg(child)
                            except (TclError, AttributeError, RuntimeError):
                                pass
                else:
                    card_widget.config(bg=COLORS['bg_card'], relief=FLAT, bd=1,
                                highlightthickness=1, highlightbackground=COLORS['border'])
                    # 隐藏选中指示条（高度设为0）
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=0)
                    
                    # 恢复所有背景色为默认
                    def restore_bg(widget):
                        for child in widget.winfo_children():
                            if isinstance(child, (Frame, Label)):
                                try:
                                    child_bg = child.cget('bg')
                                    if child_bg == "#BBDEFB":
                                        child.config(bg=COLORS['bg_card'])
                                    restore_bg(child)
                                except (TclError, AttributeError, RuntimeError):
                                    pass
                    restore_bg(card_widget)
            except Exception as e:
                pass
        
        # 先清除另一个队伍的所有选中状态
        if team_type == 'home':
            # 清除客队的所有选中状态
            if hasattr(self, 'sub_away_cards_frame'):
                for card in self.sub_away_cards_frame.winfo_children():
                    update_card_style(card, False)
        else:
            # 清除主队的所有选中状态
            if hasattr(self, 'sub_home_cards_frame'):
                for card in self.sub_home_cards_frame.winfo_children():
                    update_card_style(card, False)
        
        # 更新当前队伍的选中状态
        for card in cards_frame.winfo_children():
            if hasattr(card, 'card_index') and card.card_index == index:
                update_card_style(card, True)
            else:
                update_card_style(card, False)
        print(f"✓ {'客队' if team_type == 'away' else '主队'}切换当前换人到第{index+1}组 - 换下：{player_out}，换上：{player_in}")
    
    def select_sub_card_away(self, index):
        self._select_sub_card('away', index, self.sub_away_list, self.sub_away_out_label, self.sub_away_in_label,
                            self.sub_away_cards_frame, teamname_away)
    
    def select_sub_card_home(self, index):
        self._select_sub_card('home', index, self.sub_home_list, self.sub_home_out_label, self.sub_home_in_label,
                            self.sub_home_cards_frame, teamname_home)
    
    def _clear_sub(self, out_label, in_label, entry, sub_list, cards_frame):
        """通用清空换人方法（统一使用 substitutions.csv）"""
        out_label.config(text="-- --")
        in_label.config(text="-- --")
        entry.delete(0, END)
        sub_list.clear()
        for widget in cards_frame.winfo_children():
            widget.destroy()
        
        # 恢复预览标题和背景颜色为默认值
        if hasattr(self, 'sub_preview_title_var'):
            self.sub_preview_title_var.set("当前换人字幕预览")
        # 恢复预览标题背景颜色和文字颜色为默认警告色
        if hasattr(self, 'sub_preview_header'):
            self.sub_preview_header.config(bg=COLORS['warning'])
            if hasattr(self, 'sub_preview_title_label'):
                text_color = get_contrast_text_color(COLORS['warning'])
                self.sub_preview_title_label.config(bg=COLORS['warning'], fg=text_color)
        
        # 只清空统一的换人记录文件（不再清空单独的主客队文件）
        FileManager.clear_file('substitutions.csv')
    
    def sub_clear_away(self):
        self._clear_sub(self.sub_away_out_label, self.sub_away_in_label, self.sub_away_entry,
                       self.sub_away_list, self.sub_away_cards_frame)
    
    def sub_clear_home(self):
        if hasattr(self, 'sub_preview_team_var'):
            self.sub_preview_team_var.set("当前换人字幕预览")
        self._clear_sub(self.sub_home_out_label, self.sub_home_in_label, self.sub_home_entry,
                       self.sub_home_list, self.sub_home_cards_frame)


    def _delete_sub_card(self, team_type, index, sub_list, cards_frame):
        """通用删除换人卡片方法"""
        if index < len(sub_list):
            del sub_list[index]
            for widget in cards_frame.winfo_children():
                widget.destroy()
            for i, (player_out, player_in, timestamp) in enumerate(sub_list):
                if team_type == 'away':
                    self.create_sub_card_away(i, player_out, player_in, timestamp)
                else:
                    self.create_sub_card_home(i, player_out, player_in, timestamp)
            print(f"✓ 已删除{'客队' if team_type == 'away' else '主队'}第{index+1}个换人记录")
    
    def delete_sub_card_away(self, index):
        self._delete_sub_card('away', index, self.sub_away_list, self.sub_away_cards_frame)
    
    def delete_sub_card_home(self, index):
        self._delete_sub_card('home', index, self.sub_home_list, self.sub_home_cards_frame)

    '''红黄牌 - 使用通用方法优化布局'''
    def create_card_red(self, parent_frame, index, player_info, card_type, timestamp, select_callback, delete_callback):
        """通用红黄牌卡片创建方法（重新设计，现代美观）"""
        # 根据牌类型设置不同的颜色
        if card_type == "红牌":
            card_color = "#E53935"  # 红色
            card_color_light = "#FFCDD2"  # 浅红色背景
            card_text_color = "#C62828"  # 深红色文字
            card_icon = "■"  # 红牌图标
        else:  # 黄牌
            card_color = "#F9A825"  # 黄色
            card_color_light = "#FFF9C4"  # 浅黄色背景
            card_text_color = "#F57F17"  # 深黄色文字
            card_icon = "■"  # 黄牌图标
        
        card_bg = COLORS['bg_card']
        
        # 使用Grid布局，支持多列显示以减少空间浪费
        card = Frame(parent_frame, bg=COLORS['bg_card'], relief=FLAT, bd=1,
                    highlightthickness=2, highlightbackground=COLORS['border'])
        card.grid(row=index // 7, column=index % 7, padx=SPACING['sm'], pady=SPACING['sm'], 
                 sticky="nsew")
        
        # 确保父容器已配置Grid列
        col = index % 7
        try:
            parent_frame.grid_columnconfigure(col, weight=1, uniform="card_col")
        except (TclError, AttributeError):
            pass
        
        # 卡片内容容器（重新设计布局）
        card_content = Frame(card, bg=card_bg)
        card_content.pack(fill=BOTH, expand=True, padx=0, pady=0)
        
        # 顶部选中指示条（初始隐藏，选中时显示）
        selected_indicator = Frame(card_content, bg=COLORS['info'], height=0)
        selected_indicator.pack(fill=X)
        selected_indicator.pack_propagate(False)
        card.selected_indicator = selected_indicator
        
        # === 顶部：牌类型标签区域（使用牌的颜色作为背景） ===
        card_header = Frame(card_content, bg=card_color, height=28)
        card_header.pack(fill=X)
        card_header.pack_propagate(False)
        
        # 左侧：牌类型图标和文字
        header_left = Frame(card_header, bg=card_color)
        header_left.pack(side=LEFT, fill=Y, padx=(SPACING['sm'], 0), pady=SPACING['xs'])
        Label(header_left, text=card_icon, font=('Microsoft YaHei UI', 12, 'bold'), 
              bg=card_color, fg=COLORS['text_light']).pack(side=LEFT, padx=(0, 2))
        Label(header_left, text=card_type, font=('Microsoft YaHei UI', 9, 'bold'), 
              bg=card_color, fg=COLORS['text_light']).pack(side=LEFT)
        
        # 右侧：序号标签（小圆点样式）
        header_right = Frame(card_header, bg=card_color)
        header_right.pack(side=RIGHT, fill=Y, padx=(0, SPACING['sm']), pady=SPACING['xs'])
        Label(header_right, text=f"#{index+1}", font=('Microsoft YaHei UI', 8), 
              bg=card_color, fg=COLORS['text_light'], 
              padx=4, pady=1).pack()
        
        # === 中间：球员信息区域（使用浅色背景突出显示） ===
        player_info_frame = Frame(card_content, bg=card_color_light)
        player_info_frame.pack(fill=BOTH, expand=True, padx=0, pady=0)
        
        # 解析player_info，提取号码和姓名（格式：编号,姓名）
        if ',' in player_info:
            number, name = player_info.split(',', 1)
        else:
            number = player_info
            name = ""
        
        # 球员号码（大号显示）
        number_label = Label(player_info_frame, text=number, 
                            font=('Microsoft YaHei UI', 16, 'bold'),
                            bg=card_color_light, fg=card_text_color)
        number_label.pack(pady=(SPACING['md'], SPACING['xs']))
        
        # 球员姓名（小号显示）
        if name:
            name_label = Label(player_info_frame, text=name,
                              font=('Microsoft YaHei UI', 9),
                              bg=card_color_light, fg=COLORS['text_dark'],
                              wraplength=100)
            name_label.pack(pady=(0, SPACING['md']))
        
        # === 底部：时间和删除按钮区域 ===
        bottom_frame = Frame(card_content, bg=card_bg, height=24)
        bottom_frame.pack(fill=X, side=BOTTOM)
        bottom_frame.pack_propagate(False)
        
        # 左侧：时间
        time_frame = Frame(bottom_frame, bg=card_bg)
        time_frame.pack(side=LEFT, fill=Y, padx=(SPACING['sm'], 0), pady=SPACING['xs'])
        Label(time_frame, text=timestamp, font=('Microsoft YaHei UI', 7),
              bg=card_bg, fg=COLORS['text_muted']).pack()
        
        # 右侧：删除按钮（小图标样式）
        delete_frame = Frame(bottom_frame, bg=card_bg)
        delete_frame.pack(side=RIGHT, fill=Y, padx=(0, SPACING['xs']), pady=2)
        btn_delete = Button(delete_frame, text="✕", bg="#DC3545", fg="white", 
                           font=('Arial', 8, 'bold'), relief=FLAT, cursor="hand2", 
                           padx=4, pady=1, bd=0, width=3, height=1,
                           command=delete_callback,
                           activebackground="#C62828", activeforeground="white")
        btn_delete.pack()
        
        card.card_index = index
        card.card_type = card_type
        
        # 绑定点击事件（除了删除按钮）
        def bind_click(widget):
            if not isinstance(widget, Button):
                widget.bind("<Button-1>", lambda e: select_callback())
            for child in widget.winfo_children():
                if child != btn_delete:
                    bind_click(child)
        bind_click(card)
    
    # 创建主队红黄牌卡片
    def create_card_red_home(self, index, player_info, card_type, timestamp):
        self.create_card_red(self.red_home_cards_frame, index, player_info, card_type, timestamp,
                           lambda: self.select_card_red_home(index), lambda: self.delete_card_red_home(index))

    # 创建客队红黄牌卡片
    def create_card_red_away(self, index, player_info, card_type, timestamp):
        self.create_card_red(self.red_away_cards_frame, index, player_info, card_type, timestamp,
                           lambda: self.select_card_red_away(index), lambda: self.delete_card_red_away(index))

    # 主队红牌
    def red_home_add(self):
        number = self.red_home_entry.get().strip()
        if not number:
            return
        
        player_info = self.find_player_by_number(number, home_list)
        if player_info is None:
            self.red_card_display_label.config(text=f"未找到编号 {number}")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.red_home_list.append((player_info, "红牌", timestamp))
        
        self.create_card_red_home(len(self.red_home_list) - 1, player_info, "红牌", timestamp)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'card_preview_title_var'):
            self.card_preview_title_var.set(teamname_home)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'card_preview_header'):
            self.card_preview_header.config(bg=self.team_home_color)
            if hasattr(self, 'card_preview_title_label'):
                text_color = get_contrast_text_color(self.team_home_color)
                self.card_preview_title_label.config(bg=self.team_home_color, fg=text_color)
        
        # 更新红牌预览，清空黄牌预览
        self.red_card_display_label.config(text=f"{teamname_home}\n{player_info}")
        self.yellow_card_display_label.config(text="")
        
        # 更新按钮类型为红牌
        self.current_card_type = "red_card"
        if hasattr(self, 'card_button'):
            self.card_button.update_subtitle_type("red_card")
        
        # 调整宽度比例：红牌75%，黄牌25%
        self.card_preview_content.grid_columnconfigure(0, weight=3)
        self.card_preview_content.grid_columnconfigure(1, weight=1)
        
        FileManager.write_csv('red_card.csv', f"{teamname_home},{player_info}")
        
        self.red_home_entry.delete(0, END)
        print(f"✓ 主队红牌 - {player_info}")

    # 主队黄牌
    def yellow_home_add(self):
        number = self.red_home_entry.get().strip()
        if not number:
            return
        
        player_info = self.find_player_by_number(number, home_list)
        if player_info is None:
            self.yellow_card_display_label.config(text=f"未找到编号 {number}")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.red_home_list.append((player_info, "黄牌", timestamp))
        
        self.create_card_red_home(len(self.red_home_list) - 1, player_info, "黄牌", timestamp)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'card_preview_title_var'):
            self.card_preview_title_var.set(teamname_home)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'card_preview_header'):
            self.card_preview_header.config(bg=self.team_home_color)
            if hasattr(self, 'card_preview_title_label'):
                text_color = get_contrast_text_color(self.team_home_color)
                self.card_preview_title_label.config(bg=self.team_home_color, fg=text_color)
        
        # 更新黄牌预览，清空红牌预览
        self.yellow_card_display_label.config(text=f"{teamname_home}\n{player_info}")
        self.red_card_display_label.config(text="")
        
        # 更新按钮类型为黄牌
        self.current_card_type = "yellow_card"
        if hasattr(self, 'card_button'):
            self.card_button.update_subtitle_type("yellow_card")
        
        # 调整宽度比例：红牌25%，黄牌75%
        self.card_preview_content.grid_columnconfigure(0, weight=1)
        self.card_preview_content.grid_columnconfigure(1, weight=3)
        
        FileManager.write_csv('yellow_card.csv', f"{teamname_home},{player_info}")
        
        self.red_home_entry.delete(0, END)
        print(f"✓ 主队黄牌 - {player_info}")

    # 客队红牌
    def red_away_add(self):
        number = self.red_away_entry.get().strip()
        if not number:
            return
        
        player_info = self.find_player_by_number(number, away_list)
        if player_info is None:
            self.red_card_display_label.config(text=f"未找到编号 {number}")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.red_away_list.append((player_info, "红牌", timestamp))
        
        self.create_card_red_away(len(self.red_away_list) - 1, player_info, "红牌", timestamp)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'card_preview_title_var'):
            self.card_preview_title_var.set(teamname_away)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'card_preview_header'):
            self.card_preview_header.config(bg=self.team_away_color)
            if hasattr(self, 'card_preview_title_label'):
                text_color = get_contrast_text_color(self.team_away_color)
                self.card_preview_title_label.config(bg=self.team_away_color, fg=text_color)
        
        # 更新红牌预览，清空黄牌预览
        self.red_card_display_label.config(text=f"{teamname_away}\n{player_info}")
        self.yellow_card_display_label.config(text="")
        
        # 更新按钮类型为红牌
        self.current_card_type = "red_card"
        if hasattr(self, 'card_button'):
            self.card_button.update_subtitle_type("red_card")
        
        # 调整宽度比例：红牌75%，黄牌25%
        self.card_preview_content.grid_columnconfigure(0, weight=3)
        self.card_preview_content.grid_columnconfigure(1, weight=1)
        
        FileManager.write_csv('red_card.csv', f"{teamname_away},{player_info}")
        
        self.red_away_entry.delete(0, END)
        print(f"✓ 客队红牌 - {player_info}")

    # 客队黄牌
    def yellow_away_add(self):
        number = self.red_away_entry.get().strip()
        if not number:
            return
        
        player_info = self.find_player_by_number(number, away_list)
        if player_info is None:
            self.yellow_card_display_label.config(text=f"未找到编号 {number}")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.red_away_list.append((player_info, "黄牌", timestamp))
        
        self.create_card_red_away(len(self.red_away_list) - 1, player_info, "黄牌", timestamp)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'card_preview_title_var'):
            self.card_preview_title_var.set(teamname_away)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'card_preview_header'):
            self.card_preview_header.config(bg=self.team_away_color)
            if hasattr(self, 'card_preview_title_label'):
                text_color = get_contrast_text_color(self.team_away_color)
                self.card_preview_title_label.config(bg=self.team_away_color, fg=text_color)
        
        # 更新黄牌预览，清空红牌预览
        self.yellow_card_display_label.config(text=f"{teamname_away}\n{player_info}")
        self.red_card_display_label.config(text="")
        
        # 更新按钮类型为黄牌
        self.current_card_type = "yellow_card"
        if hasattr(self, 'card_button'):
            self.card_button.update_subtitle_type("yellow_card")
        
        # 调整宽度比例：红牌25%，黄牌75%
        self.card_preview_content.grid_columnconfigure(0, weight=1)
        self.card_preview_content.grid_columnconfigure(1, weight=3)
        
        FileManager.write_csv('yellow_card.csv', f"{teamname_away},{player_info}")
        
        self.red_away_entry.delete(0, END)
        print(f"✓ 客队黄牌 - {player_info}")

    def _select_card_red(self, team_type, index, card_list, cards_frame, team_name):
        """通用选择红黄牌卡片方法（确保同时只能有一个卡片被选中）"""
        player_info, card_type, timestamp = card_list[index]
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'card_preview_title_var'):
            self.card_preview_title_var.set(team_name)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'card_preview_header'):
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            self.card_preview_header.config(bg=team_color)
            if hasattr(self, 'card_preview_title_label'):
                text_color = get_contrast_text_color(team_color)
                self.card_preview_title_label.config(bg=team_color, fg=text_color)
        
        if card_type == "红牌":
            # 更新红牌预览，清空黄牌预览
            self.red_card_display_label.config(text=f"{team_name}\n{player_info}")
            self.yellow_card_display_label.config(text="")
            # 更新按钮类型为红牌
            self.current_card_type = "red_card"
            if hasattr(self, 'card_button'):
                self.card_button.update_subtitle_type("red_card")
            # 调整宽度比例：红牌75%，黄牌25%
            self.card_preview_content.grid_columnconfigure(0, weight=3)
            self.card_preview_content.grid_columnconfigure(1, weight=1)
            FileManager.write_csv('red_card.csv', f"{team_name},{player_info}")
        else:
            # 更新黄牌预览，清空红牌预览
            self.yellow_card_display_label.config(text=f"{team_name}\n{player_info}")
            self.red_card_display_label.config(text="")
            # 更新按钮类型为黄牌
            self.current_card_type = "yellow_card"
            if hasattr(self, 'card_button'):
                self.card_button.update_subtitle_type("yellow_card")
            # 调整宽度比例：红牌25%，黄牌75%
            self.card_preview_content.grid_columnconfigure(0, weight=1)
            self.card_preview_content.grid_columnconfigure(1, weight=3)
            FileManager.write_csv('yellow_card.csv', f"{team_name},{player_info}")
        
        # 更新选中状态（增强高亮效果，适配新设计）
        def update_card_style(card_widget, is_selected):
            try:
                if is_selected:
                    # 使用深蓝色边框高亮
                    highlight_border = "#2196F3"  # 深蓝色边框
                    card_widget.config(relief=RAISED, bd=2,
                                highlightthickness=3, highlightbackground=highlight_border)
                    # 显示选中指示条（顶部蓝色条）
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=4, bg=highlight_border)
                else:
                    # 恢复默认样式（与创建时一致）
                    card_widget.config(bg=COLORS['bg_card'], relief=FLAT, bd=1,
                                highlightthickness=2, highlightbackground=COLORS['border'])
                    # 隐藏选中指示条（高度设为0）
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=0, bg=COLORS['info'])
            except Exception as e:
                pass
        
        # 先清除另一个队伍的所有选中状态
        if team_type == 'home':
            # 清除客队的所有选中状态
            if hasattr(self, 'red_away_cards_frame'):
                for card in self.red_away_cards_frame.winfo_children():
                    update_card_style(card, False)
        else:
            # 清除主队的所有选中状态
            if hasattr(self, 'red_home_cards_frame'):
                for card in self.red_home_cards_frame.winfo_children():
                    update_card_style(card, False)
        
        # 更新当前队伍的选中状态
        for card in cards_frame.winfo_children():
            if hasattr(card, 'card_index') and card.card_index == index:
                update_card_style(card, True)
            else:
                update_card_style(card, False)
    
    # 选择主队卡片
    def select_card_red_home(self, index):
        self._select_card_red('home', index, self.red_home_list, self.red_home_cards_frame, teamname_home)

    # 选择客队卡片
    def select_card_red_away(self, index):
        self._select_card_red('away', index, self.red_away_list, self.red_away_cards_frame, teamname_away)

    # 主队清空
    def red_home_clear(self):
        # 清空两个预览区域
        self.red_card_display_label.config(text="")
        self.yellow_card_display_label.config(text="")
        # 恢复宽度比例为各50%
        self.card_preview_content.grid_columnconfigure(0, weight=1)
        self.card_preview_content.grid_columnconfigure(1, weight=1)
        self.red_home_entry.delete(0, END)
        self.red_home_list = []
        
        for widget in self.red_home_cards_frame.winfo_children():
            widget.destroy()
        
        for filename in ['red_card.csv', 'yellow_card.csv']:
            FileManager.clear_file(filename)

    # 客队清空
    def red_away_clear(self):
        # 清空两个预览区域
        self.red_card_display_label.config(text="")
        self.yellow_card_display_label.config(text="")
        # 恢复宽度比例为各50%
        self.card_preview_content.grid_columnconfigure(0, weight=1)
        self.card_preview_content.grid_columnconfigure(1, weight=1)
        self.red_away_entry.delete(0, END)
        self.red_away_list = []
        
        for widget in self.red_away_cards_frame.winfo_children():
            widget.destroy()
        
        for filename in ['red_card.csv', 'yellow_card.csv']:
            FileManager.clear_file(filename)

    '''记分板'''
    def _save_scoreboard(self):
        """保存记分板到CSV"""
        content = f"{teamname_home},{self.scoreHomeVar.get()},{self.team_home_color}\n{teamname_away},{self.scoreAwayVar.get()},{self.team_away_color}\n{self.sessionVar.get()}"
        FileManager.write_csv('scoreboard.csv', content)
    
    def _update_session_button_colors(self, *args):
        """更新场次选择按钮的文字颜色（选中时白色，未选中时深色）"""
        current_value = self.sessionVar.get()
        for radio in getattr(self, 'session_radios', []):
            if radio['value'] == current_value:
                # 选中状态：白色文字
                radio.config(fg=COLORS['text_light'])
            else:
                # 未选中状态：深色文字
                radio.config(fg=COLORS['text_dark'])
    
    def scoreboard_session_switch(self):
        self._save_scoreboard()

    def scoreboard_home_scoreplus(self):
        self.scoreHomeVar.set(self.scoreHomeVar.get() + 1)
        self._save_scoreboard()
    
    def scoreboard_away_scoreplus(self):
        self.scoreAwayVar.set(self.scoreAwayVar.get() + 1)
        self._save_scoreboard()
    
    def scoreboard_home_scoreminus(self):
        self.scoreHomeVar.set(max(0, self.scoreHomeVar.get() - 1))
        self._save_scoreboard()
    
    def scoreboard_away_scoreminus(self):
        self.scoreAwayVar.set(max(0, self.scoreAwayVar.get() - 1))
        self._save_scoreboard()
    
    def scoreboard_score_clear(self):
        self.scoreHomeVar.set(0)
        self.scoreAwayVar.set(0)
        self._save_scoreboard()

    '''进球信息'''
    # 主队进球
    def goal_home_add(self):
        player_num = self.goal_home_entry.get().strip()
        
        if not player_num:
            return
        
        # 查找球员
        player_info = self.find_player_by_number(player_num, home_list)
        
        if player_info is None:
            self.goal_display_label.config(text=f"未找到编号 {player_num} 的球员")
            return
        
        # 获取当前比分
        current_score_home = self.scoreHomeVar.get()
        current_score_away = self.scoreAwayVar.get()
        
        # 添加到列表（包含比分信息）
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.goal_home_list.append((player_info, timestamp, current_score_home, current_score_away))
        
        # 创建卡片
        self.create_goal_card_home(len(self.goal_home_list) - 1, player_info, timestamp, current_score_home, current_score_away)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'goal_preview_title_var'):
            self.goal_preview_title_var.set(teamname_home)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'goal_preview_header'):
            self.goal_preview_header.config(bg=self.team_home_color)
            if hasattr(self, 'goal_preview_title_label'):
                text_color = get_contrast_text_color(self.team_home_color)
                self.goal_preview_title_label.config(bg=self.team_home_color, fg=text_color)
        
        # 更新预览
        self.goal_display_label.config(text=f"{teamname_home}\n{player_info}")
        
        # 保存到CSV（格式：球队名称,号码,姓名）
        parts = player_info.split(',')
        if len(parts) == 2:
            FileManager.write_csv('goal.csv', f"{teamname_home},{parts[0]},{parts[1]}\n")
        
        # 清空输入框
        self.goal_home_entry.delete(0, END)
        
        print(f"✓ 主队进球 - {teamname_home}: {player_info}")
    
    # 客队进球
    def goal_away_add(self):
        player_num = self.goal_away_entry.get().strip()
        
        if not player_num:
            return
        
        # 查找球员
        player_info = self.find_player_by_number(player_num, away_list)
        
        if player_info is None:
            self.goal_display_label.config(text=f"未找到编号 {player_num} 的球员")
            return
        
        # 获取当前比分
        current_score_home = self.scoreHomeVar.get()
        current_score_away = self.scoreAwayVar.get()
        
        # 添加到列表（包含比分信息）
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.goal_away_list.append((player_info, timestamp, current_score_home, current_score_away))
        
        # 创建卡片
        self.create_goal_card_away(len(self.goal_away_list) - 1, player_info, timestamp, current_score_home, current_score_away)
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'goal_preview_title_var'):
            self.goal_preview_title_var.set(teamname_away)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'goal_preview_header'):
            self.goal_preview_header.config(bg=self.team_away_color)
            if hasattr(self, 'goal_preview_title_label'):
                text_color = get_contrast_text_color(self.team_away_color)
                self.goal_preview_title_label.config(bg=self.team_away_color, fg=text_color)
        
        # 更新预览
        self.goal_display_label.config(text=f"{teamname_away}\n{player_info}")
        
        # 保存到CSV（格式：球队名称,号码,姓名）
        parts = player_info.split(',')
        if len(parts) == 2:
            FileManager.write_csv('goal.csv', f"{teamname_away},{parts[0]},{parts[1]}\n")
        
        # 清空输入框
        self.goal_away_entry.delete(0, END)
        
        print(f"✓ 客队进球 - {teamname_away}: {player_info}")
    
    # 创建主队进球卡片
    def create_goal_card(self, parent_frame, index, player_info, timestamp, score_home, score_away, select_callback, delete_callback):
        """通用进球卡片创建方法（优化布局，紧凑美观，显示比分）"""
        # 使用Grid布局，支持多列显示以减少空间浪费
        card = Frame(parent_frame, bg=COLORS['bg_card'], relief=FLAT, bd=1,
                    highlightthickness=1, highlightbackground=COLORS['border'])
        card.grid(row=index // 7, column=index % 7, padx=SPACING['xs'], pady=SPACING['xs'], 
                 sticky="nsew")
        
        # 确保父容器已配置Grid列
        col = index % 7
        try:
            parent_frame.grid_columnconfigure(col, weight=1, uniform="card_col")
        except (TclError, AttributeError):
            pass
        
        # 卡片内容容器（紧凑布局）
        card_content = Frame(card, bg=COLORS['bg_card'], padx=SPACING['sm'], pady=SPACING['xs'])
        card_content.pack(fill=BOTH, expand=True)
        
        # 顶部选中指示条（初始隐藏）
        selected_indicator = Frame(card_content, bg=COLORS['info'], height=0)
        selected_indicator.pack(fill=X, pady=(0, SPACING['xs']))
        selected_indicator.pack_propagate(False)
        card.selected_indicator = selected_indicator
        
        # 顶部：编号和时间（增大字体）
        top_line = Frame(card_content, bg=COLORS['bg_card'], height=24)
        top_line.pack(fill=X)
        top_line.pack_propagate(False)
        Label(top_line, text=f"#{index+1}", font=('YaHei', 9, 'bold'), 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=LEFT)
        Label(top_line, text=timestamp, font=('YaHei', 8), 
              bg=COLORS['bg_card'], fg=COLORS['text_muted']).pack(side=RIGHT)
        
        # 进球信息区域（使用左侧颜色条）
        goal_frame = Frame(card_content, bg=COLORS['bg_card'], height=50)
        goal_frame.pack(fill=X, pady=(SPACING['xs']//2, 0))
        goal_frame.pack_propagate(False)
        
        # 左侧颜色指示条（绿色表示进球）
        goal_indicator = Frame(goal_frame, bg="#4CAF50", width=4)
        goal_indicator.pack(side=LEFT, fill=Y, padx=(0, SPACING['xs']))
        goal_indicator.pack_propagate(False)
        
        # 进球信息（显示比分和球员信息）
        goal_info = Frame(goal_frame, bg=COLORS['bg_card'])
        goal_info.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, SPACING['xs']))
        # 显示比分而不是"进球"
        score_text = f"{score_home}:{score_away}"
        Label(goal_info, text=f"⚽ {score_text}", font=('YaHei', 9, 'bold'), 
              bg=COLORS['bg_card'], fg="#4CAF50", anchor=W).pack(anchor=W)
        Label(goal_info, text=player_info, font=('YaHei', 9), 
              bg=COLORS['bg_card'], fg=COLORS['text_dark'], anchor=W, 
              wraplength=80, justify=LEFT).pack(anchor=W, pady=(2, 0))
        
        # 删除按钮（紧凑，小尺寸）
        btn_delete = Button(card_content, text="✕", bg="#DC3545", fg="white", 
                           font=('Arial', 9, 'bold'), relief=FLAT, cursor="hand2", 
                           padx=SPACING['sm'], pady=SPACING['xs']//2, bd=0, 
                           command=delete_callback,
                           activebackground="#C62828", activeforeground="white")
        btn_delete.pack(fill=X, pady=(SPACING['xs'], 0))
        
        card.card_index = index
        
        # 绑定点击事件（除了删除按钮）
        def bind_click(widget):
            if not isinstance(widget, Button):
                widget.bind("<Button-1>", lambda e: select_callback())
            for child in widget.winfo_children():
                if child != btn_delete:
                    bind_click(child)
        bind_click(card)
    
    def create_goal_card_home(self, index, player_info, timestamp, score_home, score_away):
        self.create_goal_card(self.goal_home_cards_frame, index, player_info, timestamp, score_home, score_away,
                           lambda: self.select_goal_card_home(index), lambda: self.delete_goal_card_home(index))
    
    # 创建客队进球卡片
    def create_goal_card_away(self, index, player_info, timestamp, score_home, score_away):
        self.create_goal_card(self.goal_away_cards_frame, index, player_info, timestamp, score_home, score_away,
                           lambda: self.select_goal_card_away(index), lambda: self.delete_goal_card_away(index))
    
    def _select_goal_card(self, team_type, index, goal_list, cards_frame, team_name):
        """通用选择进球卡片方法（确保同时只能有一个卡片被选中）"""
        # 列表结构：(player_info, timestamp, score_home, score_away)
        if len(goal_list[index]) >= 4:
            player_info, timestamp, score_home, score_away = goal_list[index]
        else:
            # 兼容旧数据格式
            player_info, timestamp = goal_list[index]
            score_home, score_away = 0, 0
        
        # 更新预览标题显示队伍名称
        if hasattr(self, 'goal_preview_title_var'):
            self.goal_preview_title_var.set(team_name)
        # 更新预览标题背景颜色和文字颜色为队伍颜色
        if hasattr(self, 'goal_preview_header'):
            team_color = self.team_home_color if team_type == 'home' else self.team_away_color
            self.goal_preview_header.config(bg=team_color)
            if hasattr(self, 'goal_preview_title_label'):
                text_color = get_contrast_text_color(team_color)
                self.goal_preview_title_label.config(bg=team_color, fg=text_color)
        
        # 更新预览
        self.goal_display_label.config(text=f"{team_name}\n{player_info}")
        
        # 保存到CSV
        parts = player_info.split(',')
        if len(parts) == 2:
            FileManager.write_csv('goal.csv', f"{team_name},{parts[0]},{parts[1]}\n")
        
        # 更新选中状态（增强高亮效果，保持文字清晰）
        def update_card_style(card_widget, is_selected):
            try:
                if is_selected:
                    # 使用浅蓝色背景高亮，但足够深以保持文字清晰
                    highlight_bg = "#BBDEFB"  # 浅蓝色背景
                    card_widget.config(bg=highlight_bg, relief=RAISED, bd=3,
                                highlightthickness=4, highlightbackground="#2196F3")  # 深蓝色边框
                    # 显示选中指示条
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=5, bg="#2196F3")  # 深蓝色指示条
                    
                    # 更新卡片内容容器的背景色
                    for child in card_widget.winfo_children():
                        if isinstance(child, Frame):
                            try:
                                child_bg = child.cget('bg')
                                if child_bg == COLORS['bg_card']:
                                    child.config(bg=highlight_bg)
                                # 递归更新子组件背景色（但保留颜色指示条）
                                def update_children_bg(widget):
                                    for c in widget.winfo_children():
                                        if isinstance(c, (Frame, Label)):
                                            try:
                                                c_bg = c.cget('bg')
                                                # 不改变颜色指示条和按钮的背景色
                                                if c_bg == COLORS['bg_card'] and c_bg not in ["#4CAF50", "#DC3545"]:
                                                    c.config(bg=highlight_bg)
                                                elif c_bg in ["#4CAF50"]:
                                                    pass  # 保持原色
                                                update_children_bg(c)
                                            except (TclError, AttributeError, RuntimeError):
                                                pass
                                update_children_bg(child)
                            except (TclError, AttributeError, RuntimeError):
                                pass
                else:
                    card_widget.config(bg=COLORS['bg_card'], relief=FLAT, bd=1,
                                highlightthickness=1, highlightbackground=COLORS['border'])
                    # 隐藏选中指示条（高度设为0）
                    if hasattr(card_widget, 'selected_indicator'):
                        card_widget.selected_indicator.config(height=0)
                    
                    # 恢复所有背景色为默认
                    def restore_bg(widget):
                        for child in widget.winfo_children():
                            if isinstance(child, (Frame, Label)):
                                try:
                                    child_bg = child.cget('bg')
                                    if child_bg == "#BBDEFB":
                                        child.config(bg=COLORS['bg_card'])
                                    restore_bg(child)
                                except (TclError, AttributeError, RuntimeError):
                                    pass
                    restore_bg(card_widget)
            except Exception as e:
                pass
        
        # 先清除另一个队伍的所有选中状态
        if team_type == 'home':
            # 清除客队的所有选中状态
            if hasattr(self, 'goal_away_cards_frame'):
                for card in self.goal_away_cards_frame.winfo_children():
                    update_card_style(card, False)
        else:
            # 清除主队的所有选中状态
            if hasattr(self, 'goal_home_cards_frame'):
                for card in self.goal_home_cards_frame.winfo_children():
                    update_card_style(card, False)
        
        # 更新当前队伍的选中状态
        for card in cards_frame.winfo_children():
            if hasattr(card, 'card_index') and card.card_index == index:
                update_card_style(card, True)
            else:
                update_card_style(card, False)
    
    # 选择主队进球卡片
    def select_goal_card_home(self, index):
        self._select_goal_card('home', index, self.goal_home_list, self.goal_home_cards_frame, teamname_home)
    
    # 选择客队进球卡片
    def select_goal_card_away(self, index):
        self._select_goal_card('away', index, self.goal_away_list, self.goal_away_cards_frame, teamname_away)
    
    # 清空主队进球
    def goal_home_clear(self):
        self.goal_display_label.config(text="--- 等待输入 ---")
        self.goal_home_entry.delete(0, END)
        self.goal_home_list = []
        
        # 清空所有卡片
        for widget in self.goal_home_cards_frame.winfo_children():
            widget.destroy()
        
        # 清空CSV
        FileManager.clear_file('goal.csv')
    
    # 清空客队进球
    def goal_away_clear(self):
        self.goal_display_label.config(text="--- 等待输入 ---")
        self.goal_away_entry.delete(0, END)
        self.goal_away_list = []
        
        # 清空所有卡片
        for widget in self.goal_away_cards_frame.winfo_children():
            widget.destroy()
        
        # 清空CSV
        FileManager.clear_file('goal.csv')
    
    # 删除主队红黄牌卡片
    def delete_card_red_home(self, index):
        if index < len(self.red_home_list):
            del self.red_home_list[index]
            
            # 重新创建所有卡片
            for widget in self.red_home_cards_frame.winfo_children():
                widget.destroy()
            
            for i, (player_info, card_type, timestamp) in enumerate(self.red_home_list):
                self.create_card_red_home(i, player_info, card_type, timestamp)
            
            print(f"✓ 已删除主队第{index+1}个红黄牌记录")
    
    # 删除客队红黄牌卡片
    def delete_card_red_away(self, index):
        if index < len(self.red_away_list):
            del self.red_away_list[index]
            
            # 重新创建所有卡片
            for widget in self.red_away_cards_frame.winfo_children():
                widget.destroy()
            
            for i, (player_info, card_type, timestamp) in enumerate(self.red_away_list):
                self.create_card_red_away(i, player_info, card_type, timestamp)
            
            print(f"✓ 已删除客队第{index+1}个红黄牌记录")
    
    # 删除主队进球卡片
    def delete_goal_card_home(self, index):
        if index < len(self.goal_home_list):
            del self.goal_home_list[index]
            
            # 重新创建所有卡片
            for widget in self.goal_home_cards_frame.winfo_children():
                widget.destroy()
            
            for i, goal_data in enumerate(self.goal_home_list):
                # 兼容新旧数据格式
                if len(goal_data) >= 4:
                    player_info, timestamp, score_home, score_away = goal_data
                else:
                    player_info, timestamp = goal_data
                    score_home, score_away = 0, 0
                self.create_goal_card_home(i, player_info, timestamp, score_home, score_away)
            
            print(f"✓ 已删除主队第{index+1}个进球记录")
    
    # 删除客队进球卡片
    def delete_goal_card_away(self, index):
        if index < len(self.goal_away_list):
            del self.goal_away_list[index]
            
            # 重新创建所有卡片
            for widget in self.goal_away_cards_frame.winfo_children():
                widget.destroy()
            
            for i, goal_data in enumerate(self.goal_away_list):
                # 兼容新旧数据格式
                if len(goal_data) >= 4:
                    player_info, timestamp, score_home, score_away = goal_data
                else:
                    player_info, timestamp = goal_data
                    score_home, score_away = 0, 0
                self.create_goal_card_away(i, player_info, timestamp, score_home, score_away)
            
            print(f"✓ 已删除客队第{index+1}个进球记录")


def gui_start():
    # 初始化文件（在FileManager类定义之后）
    initialize_files()
    
    init_window = Tk()    #实例化出一个父窗口
    AAA_PORTAL = MY_GUI(init_window)
    # 设置根窗口默认属性
    AAA_PORTAL.set_init_window()
    init_window.mainloop()   #父窗口进入事件循环，可以理解为保持窗口运行，否则界面不展示

if __name__ == "__main__":
    gui_start()