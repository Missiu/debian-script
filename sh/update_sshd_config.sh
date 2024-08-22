#!/bin/bash

# 定义配置文件路径
CONFIG_FILE="/etc/ssh/sshd_config"
# 定义要查找的参数名称
PARAM_NAME="PasswordAuthentication"
# 定义备份文件路径
BACKUP_FILE="${CONFIG_FILE}.bak"

# 检查是否具有root权限
if [ "$(id -u)" -ne 0 ]; then
    echo "请以root用户或使用sudo权限运行此脚本。"
    exit 1
fi

# 备份配置文件
cp $CONFIG_FILE $BACKUP_FILE

# 检查参数是否存在且已配置为no
grep -q "^${PARAM_NAME} no" $CONFIG_FILE

if [ $? -eq 0 ]; then
    echo "${PARAM_NAME}当前配置为no，正在修改为yes..."

    # 修改配置文件
    sed -i "s/^${PARAM_NAME} no/${PARAM_NAME} yes/" $CONFIG_FILE

    # 重启SSHD服务
    systemctl restart sshd.service

    # 检查服务是否成功重启
    if [ $? -eq 0 ]; then
        echo "SSHD服务已成功重启，${PARAM_NAME}配置已生效。"
        # 删除备份文件
        rm -f $BACKUP_FILE
    else
        echo "SSHD服务重启失败，正在恢复备份文件..."
        # 恢复备份文件
        cp $BACKUP_FILE $CONFIG_FILE
        systemctl restart sshd.service
        if [ $? -eq 0 ]; then
            echo "已成功恢复配置文件，并重启SSHD服务。"
        else
            echo "恢复后重启SSHD服务失败，请手动检查配置。"
        fi
        # 删除备份文件
        rm -f $BACKUP_FILE
    fi
else
    echo "${PARAM_NAME}已配置为yes或不存在，无需修改。"
    # 删除备份文件
    rm -f $BACKUP_FILE
fi
