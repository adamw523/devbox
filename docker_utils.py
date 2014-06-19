from fabric.api import run

def bridge_ip():
    ip = run("ifconfig docker0 |grep 'inet addr' |awk -F: '{print $2}' |awk '{print $1}'")
    return ip
