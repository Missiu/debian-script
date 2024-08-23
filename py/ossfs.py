import os
import subprocess
from urllib.parse import urlparse
from termcolor import colored

def print_message(message, color='green'):
    """打印彩色信息"""
    print(colored(message, color))

def get_user_input(prompt, default=None, required=False):
    """获取用户输入并显示为青色"""
    while True:
        user_input = input(colored(prompt, 'cyan')).strip()
        if user_input:
            return user_input
        if default is not None:
            return default
        if required:
            print_message("该项为必填项，请输入有效值。", 'yellow')

def create_directory(path):
    """创建目录"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def run_command(command, check=True, silent=False):
    """运行系统命令"""
    try:
        result = subprocess.run(command, check=check, 
                                stdout=subprocess.DEVNULL if silent else None, 
                                stderr=subprocess.DEVNULL if silent else None)
        return result
    except subprocess.CalledProcessError as e:
        print_message(f"命令执行失败: {e}", 'red')
        raise

def install_required_packages():
    """安装必要的软件包"""
    print_message("检查并安装必要的依赖包...", 'cyan')
    run_command(['sudo', 'apt-get', 'update'])
    run_command(['sudo', 'apt-get', 'install', '-y', 'wget', 'python3-pip', 'gdebi-core', 'supervisor'])

    try:
        import termcolor
        print_message("termcolor 已安装", 'green')
    except ImportError:
        print_message("安装 termcolor...", 'cyan')
        run_command(['pip3', 'install', 'termcolor'])

def download_script(script_url, dest_path):
    """下载并设置脚本权限"""
    print_message(f"从 {script_url} 下载脚本...", 'cyan')
    run_command(['sudo', 'wget', '-P', os.path.dirname(dest_path), '-N', '--no-check-certificate', script_url])
    run_command(['sudo', 'chmod', '700', dest_path])
    print_message(f"脚本已下载并设置权限: {dest_path}", 'green')

# 全局变量
file_path = "/home/ossfs"

def initialize_globals():
    """初始化全局变量"""
    global file_path
    file_path = get_user_input(
        "请输入ossfs脚本运行中的主目录 (默认为 /home/ossfs): ", default="/home/ossfs"
    )
    create_directory(file_path)

def check_ossfs_installed():
    """检查是否安装了ossfs"""  
    print_message("检查是否安装了ossfs...", 'cyan')
    try:
        run_command(['ossfs', '--version'], silent=True)
        print_message("ossfs已安装", 'green')
        return True
    except Exception:
        print_message("ossfs未安装", 'yellow')
        return False

def install_ossfs():
    """安装指定版本的ossfs"""
    down_path = get_user_input(
        "是否指定下载地址？(默认为: https://github.com/aliyun/ossfs/releases/download/v1.91.3/ossfs_1.91.3_ubuntu20.04_amd64.deb) (y/n): ",
        default="https://github.com/aliyun/ossfs/releases/download/v1.91.3/ossfs_1.91.3_ubuntu20.04_amd64.deb"
    )

    file_name = urlparse(down_path).path.split('/')[-1]
    file_full_path = os.path.join("/home", file_name)

    print_message(f"正在安装 ossfs, 版本为: {file_name}...", 'cyan')
    run_command(['sudo', 'wget', down_path, '-O', file_full_path])
    run_command(['sudo', 'gdebi', '-n', file_full_path])
    os.remove(file_full_path)
    print_message("ossfs 安装完成", 'green')

def configure_ossfs():
    """配置ossfs密钥"""
    passwd_dir = os.path.join(file_path, 'passwd')
    create_directory(passwd_dir)
    passwd_file = os.path.join(passwd_dir, 'passwd-ossfs')

    if not os.path.exists(passwd_file) or os.path.getsize(passwd_file) == 0:
        print_message("未发现密钥，开始添加密钥。", 'red')
        add_secret_key(passwd_file)
    else:
        choice = get_user_input("检测到已存在的密钥文件，是否需要添加新密钥？(y/n): ", default="n")
        if choice.lower() == 'y':
            add_secret_key(passwd_file)

def add_secret_key(passwd_file):
    """添加密钥"""
    with open(passwd_file, 'a') as f:
        while True:
            bucket_name = get_user_input("请输入存储空间名称 (BucketName): ", required=True)
            access_key_id = get_user_input("请输入 AccessKey ID: ", required=True)
            access_key_secret = get_user_input("请输入 AccessKey Secret: ", required=True)

            secret_data = f"{bucket_name}:{access_key_id}:{access_key_secret}"
            f.write(secret_data + '\n')
            print_message("密钥添加成功。", 'green')

            choice = get_user_input("是否继续添加密钥？(y/n): ", default="n")
            if choice.lower() != 'y':
                break

    os.chmod(passwd_file, 0o600)
    print_message(f"密钥已成功添加至 {passwd_file}", 'green')

def mount_oss():
    """挂载oss"""
    passwd_file = os.path.join(file_path, 'passwd', 'passwd-ossfs')
    with open(passwd_file, 'r') as f:
        secrets = f.readlines()

    if not secrets:
        print_message("没有可用的密钥，请先配置密钥。", 'yellow')
        return

    print_message("可用的OSS存储空间: ", 'cyan')
    for i, secret in enumerate(secrets, 1):
        print(f"{i}. {secret.split(':')[0]}")

    choice = int(get_user_input("请选择需要挂载的OSS存储空间(输入序号): ", required=True))
    selected_bucket = secrets[choice - 1].split(':')[0]

    local_path = get_user_input("请输入oss挂载到服务器上的路径 (默认为 /home/data): ", default="/home/data")
    region = get_user_input("请输入oss存储空间所在地域名称 (必填): ", required=True)

    create_directory(local_path)
    run_command(['sudo', 'apt-get', 'install', '-y', 'supervisor'])

    ossfs_scripts = os.path.join(file_path, "scripts")
    create_directory(ossfs_scripts)

    start_ossfs_script = os.path.join(ossfs_scripts, 'start_ossfs.sh')
    umount_command = f"sudo umount {local_path}"

    if os.path.exists(start_ossfs_script):
        with open(start_ossfs_script, 'r') as f:
            if umount_command in f.read():
                print_message(f"{local_path} 已在 {start_ossfs_script} 中配置，无需更改。", 'cyan')
                return

    script_content = f"""\
#!/bin/bash
echo "Unmounting {local_path}..."
{umount_command}

echo "Mounting {selected_bucket} to {local_path}..."
ossfs {selected_bucket} {local_path} -ourl={region} -f -o passwd_file={passwd_file} -o allow_other

echo "Finished."
"""
    with open(start_ossfs_script, 'a') as f:
        f.write(script_content)
    os.chmod(start_ossfs_script, 0o700)

    supervisor_conf_path = os.path.join(file_path, 'supervisord', 'supervisord.conf')
    create_directory(os.path.join(file_path, 'supervisord'))
    create_directory(os.path.join(file_path, 'log'))
    create_directory(os.path.join(file_path, 'run'))

    target = '/etc/supervisor/supervisord.conf'
    try:
        if os.path.islink(target) or os.path.exists(target):
            os.remove(target)
        os.symlink(supervisor_conf_path, target)
        print_message(f"已创建软链接: {supervisor_conf_path} -> {target}", 'green')
    except Exception as e:
        print_message(f"创建软链接失败: {e}", 'red')

    supervisor_conf = f"""\
[supervisord]
nodaemon=true
logfile={file_path}/log/supervisord.log
pidfile=/var/run/supervisord.pid
user=root

[program:ossfs]
command=bash {start_ossfs_script}
autostart=true
autorestart=true
logfile={file_path}/log/ossfs.log
logfile_maxbytes=1MB
logfile_backups=10
"""
    with open(supervisor_conf_path, 'a') as f:
        f.write(supervisor_conf)

    try:
        run_command(['supervisord'])
        print_message("ossfs启动成功", 'green')
    except Exception as e:
        print_message(f"ossfs启动失败: {e}", 'red')

def main():
    script_url = "https://raw.githubusercontent.com/Missiu/debian-script/main/py/ossfs.py"
    script_dest = "/home/ossfs.py"

    install_required_packages()
    download_script(script_url, script_dest)
    
    initialize_globals()
    if not check_ossfs_installed():
        install_ossfs()

    configure_ossfs()
    mount_oss()

    script_path = os.path.abspath(__file__)
    print_message(f"脚本执行完成，正在删除脚本文件: {script_path}", 'green')
    try:
        os.remove(script_path)
        print_message("脚本文件已成功删除，感谢使用。", 'green')
    except Exception as e:
        print_message(f"删除脚本文件失败: {e}", 'red')

if __name__ == "__main__":
    main()
