## sshd_config

- 作用：主要作用于轻量云服务器链接不上的情况
- 概述：自动修改sshd_config文件，把PasswordAuthentication参数设置为yes
- 运行：sudo wget -P /home -N --no-check-certificate "https://raw.githubusercontent.com/Missiu/debian-script/main/sh/update_sshd_config.sh" && sudo chmod 700 /home/update_sshd_config.sh && sudo /home/update_sshd_config.sh
- 说明：
  - -P /home: 指定下载文件保存的目录为/home
  - -N: 忽略证书验证。
  - --no-check-certificate: 忽略证书验证。
  - wget: 用于下载文件。
  - chmod 700: 设置文件权限为700。
