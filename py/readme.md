


## ossfs

- 作用：主要作用于oss存储自动挂到服务器
- 概述：
  - 安装ossfs：
  - ossfs配置：
  - 挂载oss
    - 使用Supervisor启动ossfs
    - Supervisor是用Python开发的一套通用的进程管理程序，能将一个普通的命令行进程变为后台daemon，并监控进程状态。异常退出时能自动重启。
- 运行：sudo wget -P /home -N --no-check-certificate "https://raw.githubusercontent.com/Missiu/debian-script/main/py/ossfs.py" && sudo chmod 700 /home/ossfs.py && sudo python3 /home/ossfs.py
- 说明：
  - 如果出现：error while loading shared libraries: libcrypto.so.10: cannot open shared object file: No such file or directory,请更换下载的oosfs版本，[oosfs项目地址](https://github.com/aliyun/ossfs/releases)
  - -P /home: 指定下载文件保存的目录为/home
  - -N: 忽略证书验证。
  - --no-check-certificate: 忽略证书验证。
  - wget: 用于下载文件。
  - chmod 700: 设置文件权限为700。