import os
import subprocess
from urllib.parse import urlparse
from termcolor import colored
import socket
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


# 全局变量
file_path = "/home/supervisord/ossfs"
supervisor_path = '/home/supervisord'
def initialize_globals():
    """初始化全局变量"""
    global file_path
    print_message("========      此脚本使用supervisord管理ossfs进程      ========")
    print_message("======== supervisord默认使用目录为: /home/supervisord ========")

    file_path = get_user_input(
        "请输入ossfs脚本运行中的主目录 (默认为 /home/supervisord/program/ossfs): ", default="/home/supervisord/program/ossfs"
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
    region = get_user_input("请输入oss存储空间所在地域名称 如: oss-cn-hongkong-internal.aliyuncs.com (必填): ", required=True)

    create_directory(local_path)
    run_command(['sudo', 'apt-get', 'install', '-y', 'supervisor'])

    ossfs_scripts = os.path.join(file_path, os.path.basename(local_path))
    create_directory(ossfs_scripts)

    start_ossfs_script = os.path.join(ossfs_scripts, f'start_ossfs_{os.path.basename(local_path)}.sh')

    umount_command = f"sudo umount {local_path}"
    script_content = f"""\
#!/bin/bash
echo "Unmounting {local_path}..."
{umount_command}

echo "Mounting {selected_bucket} to {local_path}..."
ossfs {selected_bucket} {local_path} -ourl={region} -f -o passwd_file={passwd_file} -o allow_other

echo "Finished."
"""
    
    if os.path.exists(start_ossfs_script):
        # 一次打开文件，并使用with语句确保文件正确关闭
        with open(start_ossfs_script, 'r+') as f:  # 使用'r+'模式以便读写
            content = f.read()
            if umount_command in content:
                print_message(f"挂载路径 {local_path} 已在 {start_ossfs_script} 中配置，无需更改。", 'cyan')
            else:
                # 移动文件指针到文件末尾
                f.seek(0, os.SEEK_END)
                f.write(script_content)   
    else:
        with open(start_ossfs_script, 'w') as f:
            f.write(script_content)

    os.chmod(start_ossfs_script, 0o700)
    # supervisord配置
    file_path_ini = os.path.join(ossfs_scripts, f'config_ossfs_{os.path.basename(local_path)}.ini')
    supervisor_conf_path = os.path.join(supervisor_path, 'supervisord.conf')
    create_directory(os.path.join(supervisor_path, 'log'))
    create_directory(os.path.join(supervisor_path, 'run'))
    port =  get_user_input("请输入supervisord port (默认为9001): ",default="9001")
    username = get_user_input("请输入supervisord username (默认为root): ",default="root")
    password = get_user_input("请输入supervisord password (默认为1234): ",default="1234")
    ip = '0.0.0.0' 
    target = '/etc/supervisor/supervisord.conf'
    try:
        if os.path.islink(target) or os.path.exists(target):
            os.remove(target)
        os.symlink(supervisor_conf_path, target)
        print_message(f"已创建软链接: {supervisor_conf_path} -> {target}", 'green')
    except Exception as e:
        print_message(f"创建软链接失败: {e}", 'red')

    supervisor_conf = f"""\
[inet_http_server]    
port={ip}:{port}
username={username}
password={password}

[supervisord]
nodaemon=false
logfile={supervisor_path}/log/supervisord.log
pidfile={supervisor_path}/run/supervisord.pid
nocleanup=true
logfile_backups=10
logfile_maxbytes=50MB
user=root

[supervisorctl]
serverurl=http://{ip}:{port}
"""
    supervisor_ossfs_conf = f"""\
[program:ossfs]
command=bash {start_ossfs_script}
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
logfile={file_path}/log/
logfile_maxbytes=1MB
logfile_backups=10
stdout_logfile={file_path}/log
stdout_logfile_maxbytes=1MB
stdout_logfile_backups=10
stdout_capture_maxbytes=1MB
"""
    supervisor_ossfs_ini = f"""\
[include]
files = {file_path_ini}
"""
    with open(file_path_ini, 'w') as f:
        f.write(supervisor_ossfs_conf)

    # 检查 supervisor_conf_path 文件中是否存在 [include] 部分
    if not os.path.exists(supervisor_conf_path):
        with open(supervisor_conf_path, 'a') as f:
            f.write(supervisor_conf)
            f.write(supervisor_ossfs_ini)    
    else: 
        with open(supervisor_conf_path, 'r') as f:
            content = f.read()
        
        # 检查是否存在 [include] 部分
        if '[include]' in content:
            # 读取原始文件内容
            with open(supervisor_conf_path, 'r') as f:
                original_content = f.readlines()

            # 查找 [include] 部分所在行号
            include_line_index = None
            for i, line in enumerate(original_content):
                if line.strip() == '[include]':
                    include_line_index = i
                    break

            if include_line_index is not None:
                # 在 [include] 部分的下一行追加 files = file_path_ini
                original_content.insert(include_line_index + 1, f"files = {file_path_ini}\n")

                # 写回修改后的内容
                with open(supervisor_conf_path, 'w') as f:
                    f.writelines(original_content)
        else:
            with open(supervisor_conf_path, 'a') as f:
                f.write(supervisor_ossfs_ini)     
        

    try:
        run_command(['sudo','systemctl','start','supervisor'])
        run_command(['sudo','systemctl','restart','supervisor'])
        print_message("====  ossfs启动成功  ====", 'green')
        print_message(f"==== supervisor管理地址: http://{get_ip_address}:{port}  ====", 'green')
    except Exception as e:
        print_message(f"ossfs启动失败: {e}", 'red')
def get_ip_address():
    # 创建一个未连接的套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个外部服务器以获取外网IP（不会真正发送数据）
        s.connect(('8.8.8.8', 1))  # Google Public DNS
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address
def main():

    install_required_packages()
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
