import os
import subprocess
from urllib.parse import urlparse
import re

# 定义全局变量
file_path = "/home/ossfs"

def initialize_globals():
    """初始化全局变量"""
    global file_path
    file_path = input("请输入ossfs脚本运行中的主目录(例如 /home/ossfs)产出的其他文件会存放在这里 默认为 : /home/ossfs").strip()
    if not file_path:
        file_path = "/home/ossfs"
    subprocess.run(['mkdir', '-p', file_path], check=True)

def check_ossfs_installed():
    """检查是否安装了ossfs"""  
    try:
        print("检查是否安装了ossfs...")
        subprocess.run(['ossfs', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("ossfs已安装")
        return True
    except FileNotFoundError:
        print("ossfs未安装")
        return False
    except subprocess.CalledProcessError:
        print("ossfs未安装")
        return False
def install_ossfs():
    """安装指定版本的ossfs"""
    down_path = "https://github.com/aliyun/ossfs/releases/download/v1.91.3/ossfs_1.91.3_ubuntu20.04_amd64.deb"
    # 是否指定版本
    print("默认为下载地址为: "+ down_path)
    
    choice = input("是否指定下载地址？(y/n): ").strip().lower()
    if choice == 'y':
        down_path = input("所有下载地址见: https://github.com/aliyun/ossfs/releases\n请输入下载地址:")
    else:
        print("下载地址为默认")

    file_name = urlparse(down_path).path.split('/')[-1]    
    print("正在安装 ossfs 其版本为: "+file_name+"...")

    # 下载 ossfs 安装包
    subprocess.run(['sudo', 'wget', down_path, '-O', f'/home/{file_name}'], check=True)
    # 更新 apt-get 并安装 gdebi-core
    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'gdebi-core'], check=True)
    # 使用 gdebi 安装 ossfs
    subprocess.run(['sudo', 'gdebi', '-n', f'/home/{file_name}'], check=True)
    subprocess.run(['ossfs', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove('/home/'+file_name)
    print("ossfs 安装完成")

def configure_ossfs():
    """配置ossfs密钥"""
    passwd_file = os.path.join(file_path,'passwd-ossfs')

    if not os.path.exists(passwd_file) or os.path.getsize(passwd_file) == 0:
        print("未发现密钥。")
        print("开始添加密钥。")
        # 确保目录存在
        os.makedirs(file_path, exist_ok=True)
        # 创建文件
        with open(passwd_file, 'w') as f:
            pass  # 创建空文件           
        add_secret_key(passwd_file)
    else:
        choice = input("检测到已存在的密钥文件，是否需要添加新密钥？(y/n) 默认为n: ").strip().lower()
        if choice == 'y':
            add_secret_key(passwd_file)
        else:
            print("已取消添加新密钥。")     

def add_secret_key(passwd_file):
    """添加密钥"""
    with open(passwd_file, 'a') as f:
        while True:
            bucket_name = input("请输入存储空间名称 (BucketName): ").strip()
            access_key_id = input("请输入 AccessKey ID: ").strip()
            access_key_secret = input("请输入 AccessKey Secret: ").strip()

            # 格式化数据
            secret_data = f"{bucket_name}:{access_key_id}:{access_key_secret}"
            
            try:
                f.write(secret_data + '\n')
                print("密钥添加成功。")
            except Exception as e:
                print(f"密钥添加失败：{e}")
            
            choice = input("是否继续添加密钥？(y/n) 默认为n: ").strip().lower()
            if choice == 'y':
                continue
            else:
                break

    # 修改文件权限，确保安全性
    os.chmod(passwd_file, 0o600)
    print(f"密钥已成功添加至 {passwd_file}")

def mount_oss():
    """挂载oss"""
    passwd_file = os.path.join(file_path+'/passwd', 'passwd-ossfs')
    with open(passwd_file, 'r') as f:
        secrets = f.readlines()
    
    if not secrets:
        print("没有可用的密钥，请先配置密钥。")
        return
    
    print("可用的OSS存储空间: ")
    for i, secret in enumerate(secrets, 1):
        bucket = secret.split(':')[0]
        print(f"{i}. {bucket}")

    choice = int(input("请选择需要挂载的OSS存储空间(输入序号): "))
    selected_bucket = secrets[choice - 1].split(':')[0]

    local_path = input("请输入oss挂载到服务器上的路径(如 /home/data):")
    if not local_path:
        local_path = "/home/data"
    region = input("请输入oss存储空间所在地域名称(如 oss-cn-hongkong-internal.aliyuncs.com) 必填!无默认值!: ")

    if not os.path.exists(local_path):
        os.makedirs(local_path, exist_ok=True)
    
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'supervisor'], check=True)

    # 创建脚本文件
    ossfs_scripts =  file_path + "/scripts"
    if not os.path.exists(ossfs_scripts):
        os.makedirs(ossfs_scripts, exist_ok=True)

    start_ossfs_script = os.path.join(ossfs_scripts, 'start_ossfs.sh')
    if not  start_ossfs_script:
        with open(start_ossfs_script, 'w') as f:
            pass  # 创建空文件 

    # 判断路径是否重复
    umount_pattern = f"^sudo umount {re.escape(local_path)}$"
    
    script_content = f"""\
#!/bin/bash
# 卸载
sudo umount {local_path}
# 重新挂载，必须要增加-f参数运行ossfs，让ossfs在前台运行。
exec ossfs {selected_bucket} {local_path} -ourl={region} -f -o passwd_file={passwd_file} -o allow_other
"""
    if os.path.exists(start_ossfs_script):
        with open(start_ossfs_script, 'r') as f:
            content = f.read()
        
        if re.search(umount_pattern, content, re.MULTILINE):
            print(f"{local_path} 已在 {start_ossfs_script} 中配置，无需更改。")
            return
        else:
            with open(start_ossfs_script, 'a') as f:
                f.write(script_content)
            os.chmod(start_ossfs_script, 0o700)

    target = '/etc/supervisor/supervisord.conf'
    supervisor_conf_path = os.path.join(file_path, 'supervisord.conf')

    try:
        if os.path.islink(target) or os.path.exists(target):
            os.remove(target)
        os.symlink(supervisor_conf_path, target)
        print(f"已创建软链接: {supervisor_conf_path} -> {target}")
    except Exception as e:
        print(f"创建软链接失败: {e}")    
        
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
    with open(supervisor_conf_path, 'a') as f:
        f.write(supervisor_conf)
    
    try:
        subprocess.run(['supervisord'], check=True)
        print("ossfs启动成功")
        subprocess.run(['sudo', 'supervisorctl', 'status'], check=True)
    except Exception as e:
        print(f"ossfs启动失败: {e}")
def main():
    initialize_globals()
    if not check_ossfs_installed():
        install_ossfs()
    
    configure_ossfs()
    mount_oss()

    script_path = os.path.abspath(__file__)
    print(f"脚本执行完成，正在删除脚本文件: {script_path}")
    
    try:
        os.remove(script_path)
        print("脚本文件已成功删除，感谢使用。")
    except Exception as e:
        print(f"删除脚本文件失败: {e}")
if __name__ == "__main__":
    main()
