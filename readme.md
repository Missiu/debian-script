

# debian/ubantu常用脚本

主要存放一些在使用服务器时可能需要用到的脚本

完全的新系统需要：sudo apt-get install wget -y

包含：ossfs一键安装脚本、acme一键申请泛域名名证书、一键解决服务器无法登录问题

### 文件目录说明
```
filetree 
├── README.md
├── py # 存放python类型脚本
│ 	├── py1.py # 脚本
│ 	└── readme.md # 脚本说明
└── sh # 存放shell类型脚本
 	├── sh1.sh # 脚本
	└── readme.md # 脚本说明
```

# py脚本说明

## ossfs

- 作用：主要作用于oss存储自动挂到服务器
- 概述：
  - 安装ossfs：
  - ossfs配置：
  - 挂载oss
    - 使用Supervisor启动ossfs
    - Supervisor是用Python开发的一套通用的进程管理程序，能将一个普通的命令行进程变为后台daemon，并监控进程状态。异常退出时能自动重启。
- 运行：
```sh
sudo wget -O /home/ossfs.py https://raw.githubusercontent.com/Missiu/debian-script/main/py/ossfs.py && pip install termcolor && sudo chmod 700 /home/ossfs.py && sudo python3 /home/ossfs.py
```
- 说明：
  - 如果出现：error while loading shared libraries: libcrypto.so.10: cannot open shared object file: No such file or directory,请更换下载的oosfs版本，[oosfs项目地址](https://github.com/aliyun/ossfs/releases)
  - 脚本产生的其他文件可以自定义路径，进行统一，运行完成后脚本自动删除
  - 本脚本针对debian系统，通过Supervisor把ossfs挂载为系统服务，方便管理，其中常用的命令如下：
    - sudo systemctl start supervisor
    - sudo systemctl status supervisor
    - sudo systemctl stop supervisor
  - 目录说明
    - supervisord.conf 配置supervisord服务的配置文件，具体配置参考supervisord官网
    - 在program中有受supervisord管理的项目，其中ossfs每个挂载的目录都被设置为了进程
    - 每个ossfs每个挂载的目录名称都为挂载路径的尾部，比如 /mnt/oss/test/ 为test 其中有执行脚本已经服务配置文件
  - 创建了软连接 /etc/supervisor/supervisord.conf  

---
 
## acme
- 作用：自动安装并且通过cdn申请泛域名证书，并且可以自行选择安装证书的目录
- 概述：
  - 检查acme需要的环境，比如git，是否已经安装acme
  - 如果没安装则安装acme，并且让用户输入--home和--config-home安装目录，创建软连接，让可执行文件随时可执行
  - DNS-API验证让用户先确认需要使用哪些商家的cdn
  - 再根据选择让用户角色的kye和Secret
  - 注册账号
  - 解析域名，安装完成
  - 选择是否部署到nginx上
  - 如果部署到nginx则使用acme的命令把证书安装到用户输入的nginx的目录
- 运行：
```sh
sudo wget -O /home/acme.py https://raw.githubusercontent.com/Missiu/debian-script/main/py/acme.py && pip install termcolor && sudo chmod 700 /home/acme.py && sudo python3 /home/acme.py
```
- 说明：目前只支持debian系统的阿里云cdn泛域名申请
- 创建了软连接 /usr/local/bin/acme.sh


# sh脚本说明

## sshd_config

- 作用：主要作用于轻量云服务器链接不上的情况
- 概述：自动修改sshd_config文件，把PasswordAuthentication参数设置为yes
- 运行：
```sh
sudo wget -P /home -N --no-check-certificate "https://raw.githubusercontent.com/Missiu/debian-script/main/sh/update_sshd_config.sh" && sudo chmod 700 /home/update_sshd_config.sh && sudo /home/update_sshd_config.sh
```
- 说明：
  - -P /home: 指定下载文件保存的目录为/home
  - -N: 忽略证书验证。
  - --no-check-certificate: 忽略证书验证。
  - wget: 用于下载文件。
  - chmod 700: 设置文件权限为700。



