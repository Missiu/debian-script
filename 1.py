import os
import subprocess
from urllib.parse import urlparse
import re
from termcolor import colored

def print_success(message):
    """打印绿色的成功信息"""
    print(colored(message, 'green'))

def print_error(message):
    """打印红色的错误信息"""
    print(colored(message, 'red'))

def print_warning(message):
    """打印黄色的提示信息"""
    print(colored(message, 'yellow'))

def get_user_input(prompt, default=None, required=False):
    """
    获取用户输入并显示为青色
    :param prompt: 提示信息
    :param default: 默认值（可选）
    :param required: 是否必填（可选）
    :return: 用户输入或默认值
    """
    while True:
        user_input = input(colored(prompt, 'cyan')).strip()
        if not user_input and default is not None:
            return default
        if required and not user_input:
            print_warning("该项为必填项，请输入有效值。")
        else:
            return user_input

def run_command(command_list, check=True, capture_output=False):
    """运行系统命令的封装函数"""
    try:
        result = subprocess.run(
            command_list,
            check=check,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL
        )
        return result.stdout.decode('utf-8').strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print_error(f"命令执行失败：{' '.join(command_list)}，错误：{e}")
        raise

def initialize_globals():
    """初始化全局变量"""
    file_path = get_user_input("请输入ossfs脚本运行中的主目录(例如 /home/ossfs)，默认为 /home/ossfs: ", "/home/ossfs")
    subprocess.run(['mkdir', '-p', file_path], check=True)
    return file_path

def check_ossfs_installed():
    """检查是否安装了ossfs"""
    print_warning("检查是否安装了ossfs...")
    try:
        run_command(['ossfs', '--version'])
        print_success("ossfs已安装")
        return True
    except subprocess.CalledProcessError:
        print_error("ossfs未安装")
        return False

def install_ossfs():
    """安装指定版本的ossfs"""
    default_down_path = "https://github.com/aliyun/ossfs/releases/download/v1.91.3/ossfs_1.91.3_ubuntu20.04_amd64.deb"
    down_path = get_user_input(f"是否指定下载地址？(默认为 {default_down_path}) (y/n): ", default="n").lower()
    
    if down_path == 'y':
        down_path = get_user_input("请输入下载地址: ", required=True)
    else:
        down_path = default_down_path
    
    file_name = urlparse(down_path).path.split('/')[-1]
    print_warning(f"正在安装 ossfs，其版本为: {file_name}...")
    
    run_command(['sudo', 'wget', down_path, '-O', f'/home/{file_name}'])
    run_command(['sudo', 'apt-get', 'update'])
    run_command(['sudo', 'apt-get', 'install', '-y', 'gdebi-core'])
    run_command(['sudo', 'gdebi', '-n', f'/home/{file_name}'])
    run_command(['ossfs', '--version'])
    
    os.remove(f'/home/{file_name}')
    print_success("ossfs 安装完成")

def configure_ossfs(file_path):
    """配置ossfs密钥"""
    passwd_file = os.path.join(file_path, 'passwd', 'passwd-ossfs')

    if not os.path.exists(passwd_file) or os.path.getsize(passwd_file) == 0:
        print_warning("未发现密钥。开始添加密钥。")
        os.makedirs(os.path.join(file_path, 'passwd'), exist_ok=True)
        add_secret_key(passwd_file)
    else:
        choice = get_user_input("检测到已存在的密钥文件，是否需要添加新密钥？(y/n) 默认为 n: ", default="n").lower()
        if choice == 'y':
            add_secret_key(passwd_file)
        else:
            print_warning("已取消添加新密钥。")     

def add_secret_key(passwd_file):
    """添加密钥"""
    with open(passwd_file, 'a') as f:
        while True:
            bucket_name = get_user_input("请输入存储空间名称 (BucketName): ", required=True)
            access_key_id = get_user_input("请输入 AccessKey ID: ", required=True)
            access_key_secret = get_user_input("请输入 AccessKey Secret: ", required=True)

            secret_data = f"{bucket_name}:{access_key_id}:{access_key_secret}"
            try:
                f.write(secret_data + '\n')
                print_success("密钥添加成功。")
            except Exception as e:
                print_error(f"密钥添加失败：{e}")

            choice = get_user_input("是否继续添加密钥？(y/n) 默认为 n: ", default="n").lower()
            if choice != 'y':
                break

    os.chmod(passwd_file, 0o600)
    print_success(f"密钥已成功添加至 {passwd_file}")

def mount_oss(file_path):
    """挂载oss"""
    passwd_file = os.path.join(file_path, 'passwd', 'passwd-ossfs')
    with open(passwd_file, 'r') as f:
        secrets = f.readlines()

    if not secrets:
        print_error("没有可用的密钥，请先配置密钥。")
        return
    
    print_warning("可用的OSS存储空间: ")
    for i, secret in enumerate(secrets, 1):
        bucket = secret.split(':')[0]
        print_warning(f"{i}. {bucket}")

    choice = int(get_user_input("请选择需要挂载的OSS存储空间(输入序号): ", required=True))
    selected_bucket = secrets[choice - 1].split(':')[0]

    local_path = get_user_input("请输入oss挂载到服务器上的路径(如 /home/data)，默认为 /home/data: ", "/home/data")
    region = get_user_input("请输入oss存储空间所在地域名称(如 oss-cn-hongkong-internal.aliyuncs.com) 必填，无默认值!: ", required=True)

    os.makedirs(local_path, exist_ok=True)
    run_command(['sudo', 'apt-get', 'install', '-y', 'supervisor'])

    ossfs_scripts = os.path.join(file_path, "scripts")
    os.makedirs(ossfs_scripts, exist_ok=True)

    start_ossfs_script = os.path.join(ossfs_scripts, 'start_ossfs.sh')
    umount_pattern = f"^sudo umount {re.escape(local_path)}$"
    script_content = f"""\
#!/bin/bash
sudo umount {local_path}
exec ossfs {selected_bucket} {local_path} -ourl={region} -f -o passwd_file={passwd_file} -o allow_other
"""

    if os.path.exists(start_ossfs_script):
        with open(start_ossfs_script, 'r') as f:
            content = f.read()
        
        if not re.search(umount_pattern, content, re.MULTILINE):
            with open(start_ossfs_script, 'a') as f:
                f.write(script_content)
    else:
        with open(start_ossfs_script, 'w') as f:
            f.write(script_content)
    os.chmod(start_ossfs_script, 0o700)

    supervisor_conf_path = os.path.join(file_path, 'supervisord', 'supervisord.conf')
    os.makedirs(os.path.join(file_path, 'log'), exist_ok=True)

    try:
        target = '/etc/supervisor/supervisord.conf'
        if os.path.islink(target) or os.path.exists(target):
            os.remove(target)
        os.symlink(supervisor_conf_path, target)
        print_success(f"已创建软链接: {supervisor_conf_path} -> {target}")
    except Exception as e:
        print_error(f"创建软链接失败: {e}")

    supervisor_conf = f"""\
[supervisord]
nodaemon=true
logfile={file_path}/log/supervisord.log
pidfile={file_path}/run/supervisord.pid
user=root    
[program:ossfs]
command=bash {start_ossfs_script}
autostart=true
autorestart=true
logfile={file_path}/log/ossfs.log
logfile_maxbytes=1MB
logfile_backups=10
"""
    with open(supervisor_conf_path, 'w') as f:
        f.write(supervisor_conf)

    try:
        run_command(['supervisord'])
        print_success("ossfs启动成功")
        run_command(['sudo', 'supervisorctl', 'status'])
    except Exception as e:
        print_error(f"ossfs启动失败: {e}")

def main():
    file_path = initialize_globals()
    if not check_ossfs_installed():
        install_ossfs()
    
    configure_ossfs(file_path)
    mount_oss(file_path)

    script_path = os.path.abspath(__file__)
    print_warning(f"脚本执行完成，正在删除脚本文件: {script_path}")
    
    try:
        os.remove(script_path)
        print_success("脚本文件已成功删除，感谢使用。")
    except Exception as e:
        print_error(f"删除脚本文件失败: {e}")

if __name__ == "__main__":
    main()
