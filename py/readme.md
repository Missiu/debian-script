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
sudo wget -O /home/ossfs.py https://raw.githubusercontent.com/Missiu/debian-script/main/py/ossfs.py && pip install termcolor && sudo python3 /home/ossfs.py
```
- 说明：
  - 如果出现：error while loading shared libraries: libcrypto.so.10: cannot open shared object file: No such file or directory,请更换下载的oosfs版本，[oosfs项目地址](https://github.com/aliyun/ossfs/releases)
  - 脚本产生的其他文件可以自定义路径，进行统一，运行完成后脚本自动删除
  - 本脚本针对debian系统，通过Supervisor把ossfs挂载为系统服务，方便管理，其中常用的命令如下： 
    - sudo supervisorctl status
    - sudo supervisorctl start
    - sudo supervisorctl stop
