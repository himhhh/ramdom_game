import random
import os
import requests
import json
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

# 定义配置文件路径
config_file = 'config.json'

def save_config(config):
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def get_steam_library_folders(steam_install_path):
    library_folders_file = os.path.join(steam_install_path, 'steamapps', 'libraryfolders.vdf')
    
    if not os.path.exists(library_folders_file):
        messagebox.showerror("错误", "找不到 libraryfolders.vdf 文件")
        return []

    library_folders = [os.path.join(steam_install_path, 'steamapps')]
    with open(library_folders_file, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            if '\"path\"' in line:
                path = line.split('"')[3]
                library_folders.append(os.path.join(path, 'steamapps'))
    return library_folders

def get_installed_games_info(library_folders):
    installed_games = []
    for folder in library_folders:
        acf_files = glob.glob(os.path.join(folder, 'appmanifest_*.acf'))
        for acf_file in acf_files:
            game_info = {}
            with open(acf_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    if '"appid"' in line:
                        game_info['appid'] = int(line.split('"')[3])
                    elif '"name"' in line:
                        game_info['name'] = line.split('"')[3]
                        break
            if 'appid' in game_info and 'name' in game_info:
                installed_games.append(game_info)
    return installed_games


def fetch_game_data(url, retries=3):
    for _ in range(retries):
        response = requests.get(url)
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                messagebox.showerror("错误", "无法解析 JSON 响应")
                return None
        elif response.status_code == 502:
            continue
        else:
            messagebox.showerror("错误", f"请求失败，状态码：{response.status_code}")
            return None
    messagebox.showerror("错误", "请求失败，服务器无响应")
    return None

def show_message(game_name):
    def close_messagebox():
        if message_window.winfo_exists():
            message_window.destroy()

    message_window = tk.Toplevel()
    message_window.title("此弹窗将在2s后关闭...")
    message_window.attributes('-topmost', True)
    
    # 创建一个Frame来居中显示消息标签
    frame = tk.Frame(message_window, padx=10, pady=10)
    frame.pack(expand=True, fill=tk.BOTH)
    
    # 创建一个标签来显示消息，并设置居中对齐
    message_label = tk.Label(frame, text=f"{game_name} 即将启动，祝你玩的开心！", anchor='center')
    message_label.pack(expand=True)

    # 更新窗口大小以适应标签内容
    message_window.update_idletasks()
    window_width = message_label.winfo_reqwidth() + 40
    window_height = message_label.winfo_reqheight() + 40
    screen_width = message_window.winfo_screenwidth()
    screen_height = message_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    message_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # 设置关闭消息框
    message_window.after(2000, close_messagebox)
    message_window.bell()  # 触发提示音

def start_random_game():
    steam_api_key = api_key_entry.get()
    steam_user_id = user_id_entry.get()
    steam_install_path = steam_path_entry.get()
    include_uninstalled = include_uninstalled_var.get()
    enable_blessing = enable_blessing_var.get()

    if not steam_install_path:
        messagebox.showerror("错误", "请填写 Steam 安装目录")
        return

    if include_uninstalled and (not steam_api_key or not steam_user_id):
        messagebox.showerror("错误", "请填写 Steam API Key 和 用户 ID")
        return

    config = {
        'api_key': steam_api_key,
        'user_id': steam_user_id,
        'steam_path': steam_install_path,
        'include_uninstalled': include_uninstalled,
        'include_installed_only': include_installed_only_var.get(),
        'enable_blessing': enable_blessing
    }
    save_config(config)

    steam_library_folders = get_steam_library_folders(steam_install_path)
    if not steam_library_folders:
        return

    owned_games = []

    if include_uninstalled:
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steam_user_id}&include_appinfo=true&format=json"
        data = fetch_game_data(url)

        if data and 'response' in data and 'games' in data['response']:
            owned_games = data['response']['games']

    # 获取所有安装游戏的信息，包括那些不在账户中的游戏
    installed_games = get_installed_games_info(steam_library_folders)
    
    if include_uninstalled:
        # 结合已拥有的游戏和安装的游戏
        for game in installed_games:
            if not any(game['appid'] == owned_game['appid'] for owned_game in owned_games):
                owned_games.append(game)

    if not include_uninstalled or not owned_games:
        owned_games = installed_games

    # 输出所有备选游戏
    if owned_games:
        game_names = [game.get('name', f"游戏 {game['appid']}") for game in owned_games]
        #print("备选游戏列表：")
        #for name in game_names:
            #print(name)

        random_game = random.choice(owned_games)
        app_id = random_game['appid']
        game_name = random_game.get('name', f"游戏 {app_id}")

        if enable_blessing:
            show_message(game_name)

        os.system(f'start steam://run/{app_id}')
    else:
        messagebox.showinfo("提示", "没有找到符合条件的游戏。")


def browse_steam_path():
    folder_selected = filedialog.askdirectory()
    steam_path_entry.delete(0, tk.END)
    steam_path_entry.insert(0, folder_selected)

def open_steam_api_help(event=None):
    webbrowser.open('https://steamcommunity.com/dev/apikey')

def open_steam_user_id_help(event=None):
    webbrowser.open('https://steamidfinder.com/')

def show_example_path(event=None):
    messagebox.showinfo("示例", "C:/Program Files/Steam（请根据实际情况配置）")

# 创建主窗口
root = tk.Tk()
root.title("随机启动 Steam 游戏")

# 使窗口大小自适应
root.columnconfigure(1, weight=1)
root.rowconfigure(4, weight=1)

# 创建并放置标签和输入框
tk.Label(root, text="Steam API Key:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
api_key_entry = ttk.Entry(root, show='*')
api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)

# 添加超链接
api_key_help = tk.Label(root, text="获取地址", fg="blue", cursor="hand2")
api_key_help.grid(row=0, column=2, padx=10, pady=10, sticky=tk.W)
api_key_help.bind("<Button-1>", open_steam_api_help)

tk.Label(root, text="Steam 用户 ID:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
user_id_entry = ttk.Entry(root, show='*')
user_id_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)

# 添加超链接
user_id_help = tk.Label(root, text="获取地址", fg="blue", cursor="hand2")
user_id_help.grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
user_id_help.bind("<Button-1>", open_steam_user_id_help)

tk.Label(root, text="Steam 安装目录:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
steam_path_entry = ttk.Entry(root)
steam_path_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.EW)

# 浏览按钮和示例链接
steam_path_frame = tk.Frame(root)
steam_path_frame.grid(row=2, column=2, padx=5, pady=10, sticky=tk.W)
browse_button = tk.Button(steam_path_frame, text="浏览", command=browse_steam_path)
browse_button.pack(side=tk.LEFT, padx=5)
example_path_help = tk.Label(steam_path_frame, text="?", fg="blue", cursor="hand2")
example_path_help.pack(side=tk.LEFT, padx=5)
example_path_help.bind("<Button-1>", show_example_path)

include_uninstalled_var = tk.BooleanVar()
include_uninstalled_check = ttk.Checkbutton(root, text="启用随机任意游戏（含未安装）", variable=include_uninstalled_var)
include_uninstalled_check.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

include_installed_only_var = tk.BooleanVar()
include_installed_only_check = ttk.Checkbutton(root, text="启用仅随机已安装游戏", variable=include_installed_only_var)
include_installed_only_check.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

# 绑定复选框互斥
def on_include_uninstalled_check():
    if include_uninstalled_var.get():
        include_installed_only_var.set(False)

def on_include_installed_only_check():
    if include_installed_only_var.get():
        include_uninstalled_var.set(False)

include_uninstalled_check.config(command=on_include_uninstalled_check)
include_installed_only_check.config(command=on_include_installed_only_check)

enable_blessing_var = tk.BooleanVar()
enable_blessing_check = ttk.Checkbutton(root, text="启用祝福消息", variable=enable_blessing_var)
enable_blessing_check.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

# 创建并放置按钮
start_button = tk.Button(root, text="启动随机游戏", command=start_random_game)
start_button.grid(row=6, column=1, pady=20)

# 加载配置
config = load_config()
if config:
    api_key_entry.insert(0, config.get('api_key', ''))
    user_id_entry.insert(0, config.get('user_id', ''))
    steam_path_entry.insert(0, config.get('steam_path', ''))
    include_uninstalled_var.set(config.get('include_uninstalled', False))
    include_installed_only_var.set(config.get('include_installed_only', False))
    enable_blessing_var.set(config.get('enable_blessing', False))
else:
    enable_blessing_var.set(True)
    include_installed_only_var.set(True)
# 运行主循环
root.mainloop()



