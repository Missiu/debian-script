import os
import subprocess
from termcolor import colored
import sys

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
        print_message(f"目录已创建: {path}", 'green')
    else:
        print_message(f"目录已存在: {path}", 'yellow')

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

def check_command(cmd):
    """检查系统中是否存在指定命令。"""
    result = subprocess.run(['which', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def check_environment():
    """检查是否安装了必要的命令。"""
    required_commands = ['git', 'curl', 'wget', 'openssl']
    missing = [cmd for cmd in required_commands if not check_command(cmd)]
    if missing:
        print_message(f"缺少以下命令：{', '.join(missing)}", 'red')
        # 安装依赖
        run_command(['sudo', 'apt-get', 'update'])
        run_command(['sudo', 'apt-get', 'install', '-y', 'git', 'curl', 'wget', 'openssl'])
        check_environment()
    print_message("环境检查通过。", 'green')

def install_acme(home_dir, config_home, email,istall_dir):
    """安装acme.sh并指定安装目录和配置。"""
    acme_path = os.path.join(home_dir, "acme.sh")
    if check_command('acme.sh'):
        print_message("acme.sh 已经安装。", 'yellow')
        return
    os.chdir(istall_dir)
    run_command(['git', 'clone','--depth','1','https://github.com/acmesh-official/acme.sh.git'])
    os.chdir('acme.sh')
    install_command = [
        './acme.sh','--install',
        '--home', home_dir,
        '--config-home',config_home,
        '--accountemail',email,
        '--nocron'
    ]
    result = run_command(install_command,check=True, silent=False)
    # result = run_command(install_command, check=True, silent=False)
    if result.returncode != 0:
        print_message("acme.sh 安装失败", 'red')
        sys.exit(1)
    # 删除临时目录
    os.remove(istall_dir)
        
    # 创建软连接
    # 创建符号链接，指向 /usr/local/bin
    symlink_path = "/usr/local/bin/acme.sh"
    if os.path.islink(symlink_path):
        os.remove(symlink_path)  # 删除现有的符号链接
    elif os.path.exists(symlink_path):
        print_message(f"{symlink_path} 已存在，跳过符号链接创建。", 'yellow')
    else:
        os.symlink(acme_path, symlink_path)
        print_message(f"创建符号链接 {symlink_path} -> {acme_path}", 'green')

def configure_dns_api():
    """根据用户输入配置 acme.sh 的 DNS API 验证。"""
    cdns = {
        "阿里云": ("dns_ali", "Ali"),
        "Cloudflare": ("dns_cf", "CF"),
        # 可以添加其他 DNS 提供商
    }

    print_message("请选择一个 DNS 提供商用于 API 验证：", 'cyan')
    for idx, provider in enumerate(cdns.keys(), 1):
        print_message(f"{idx}. {provider}", 'cyan')

    try:
        choice = int(get_user_input("请输入 DNS 提供商的编号：", required=True))
        if choice < 1 or choice > len(cdns):
            raise ValueError("无效的编号")
        provider_key = list(cdns.keys())[choice - 1]
    except (ValueError, IndexError):
        print_message("请输入有效的提供商编号。", 'red')
        return None

    # 设置 API 环境变量前缀
    dns_api, api_env_prefix = cdns[provider_key]

    # 获取 API Key 和 Secret
    key = get_user_input(f"请输入 {provider_key} 的 API Key：", required=True)
    secret = get_user_input(f"请输入 {provider_key} 的 API Secret：", required=True)

    # 设置环境变量
    os.environ[f"{api_env_prefix}_Key"] = key
    os.environ[f"{api_env_prefix}_Secret"] = secret

    print_message(f"{provider_key} 的 DNS API 验证已配置。", 'green')
    return dns_api


def register_account(email,home_dir):
    """使用acme.sh注册一个新账户。"""
    os.chdir(home_dir)
    command = ['acme.sh', '--register-account', '-m' ,email]
    result = run_command(command, check=True, silent=False)
    if result.returncode != 0:
        print_message("账户注册失败。", 'red')
        sys.exit(1)
    print_message("账户注册成功。", 'green')

def issue_certificate(domain, dns_provider,home_dir):
    """为指定域名签发证书。"""
    os.chdir(home_dir)
    command = ['acme.sh', '--issue', '-d', domain, '-d', f'*.{domain}', '--dns', dns_provider]
    result = run_command(command, check=True, silent=False)
    if result.returncode != 0:
        print_message(f"为域名 {domain} 签发证书失败", 'red')
        sys.exit(1)
    print_message(f"证书已为域名 {domain} 签发。", 'green')

def deploy_certificate(domain, nginx_cert_dir):
    """将签发的证书部署到Nginx。"""
    key_file = os.path.join(nginx_cert_dir, f"{domain}.key")
    cert_file = os.path.join(nginx_cert_dir, f"{domain}.cer")
    get_user_input = get_user_input("请输入您服务器上nginx重启的命令，默认为(service nginx force-reload)", required=False,default="service nginx force-reload")
    print_message(f"常见的命令有：service nginx force-reload，systemctl reload nginx，nginx -s reload","cyan")
    print_message(f"docker中命令有：docker exec -it nginx nginx -s reload","cyan")
    deploy_command = [
        'acme.sh', '--install-cert', '-d', domain, 
        '--key-file', key_file, 
        '--fullchain-file', cert_file, 
        '--reloadcmd', get_user_input
    ]
    result = run_command(deploy_command, check=True, silent=False)
    if result.returncode != 0:
        print_message("证书部署到 Nginx 失败", 'red')
        sys.exit(1)
    print_message(f"证书已成功部署到 Nginx，路径为 {nginx_cert_dir}", 'green')

def main():
    # 环境检查
    check_environment()

    # 输入安装目录和配置
    home_dir = get_user_input("请输入acme.sh的安装目录 默认/home/acme：", required=False,default="/home/acme")
    # config_home = get_user_input("请输入acme.sh的配置目录 (--config-home)：", required=False,default=f"{home_dir}/cert")
    # cert_home = get_user_input("请输入证书存放目录 (--cert-home)：", required=False,default="/home/acme/conf")
    email = get_user_input("请输入用于注册的邮箱：", required=True)
    config_home = f'{home_dir}/data'
    # 创建目录
    create_directory(home_dir)
    create_directory(config_home)
    istall_dir = '/home/tmp_acme'
    create_directory(istall_dir)

    # 安装acme.sh
    install_acme(home_dir, config_home, email,istall_dir)

    # 配置DNS-API
    dns_provider = configure_dns_api()

    # # 注册账户
    register_account(email,home_dir)

    # 解析域名并签发证书
    domain = get_user_input("请输入要签发证书的域名：如 exp.com: ", required=True)
    issue_certificate(domain, dns_provider,home_dir)

    # 部署到Nginx
    deploy_nginx = get_user_input("是否将证书部署到Nginx？(y/n)：", default="n").lower()
    if deploy_nginx == "y":
        nginx_cert_dir = get_user_input("请输入Nginx证书存放目录：", required=True)
        create_directory(nginx_cert_dir)
        deploy_certificate(domain, nginx_cert_dir)

    script_path = os.path.abspath(__file__)
    print_message(f"脚本执行完成，正在删除脚本文件: {script_path}", 'green')
    try:
        os.remove(script_path)
        print_message("脚本文件已成功删除，感谢使用。", 'green')
    except Exception as e:
        print_message(f"删除脚本文件失败: {e}", 'red')
        
if __name__ == "__main__":
    main()
