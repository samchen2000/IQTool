# 快速开始
## 7. VNC远程桌面
1. 安装VNC服务
```
sudo apt install x11vnc
```

2. 创建连接密码
```
x11vnc -storepasswd
```
***使用 cat用户 创建VNC连接密码，密码默认保存在/home/cat/.vnc/passwd文件中***

3. 进行连接测试
```
export DISPLAY=:0
x11vnc -auth guess -once -loop -noxdamage -repeat -rfbauth /home/cat/.vnc/passwd -rfbport 5900 -shared
```
