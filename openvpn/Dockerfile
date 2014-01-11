FROM ubuntu:precise
RUN echo deb http://archive.ubuntu.com/ubuntu/ precise main universe > /etc/apt/sources.list.d/precise.list
RUN apt-get update -q
RUN apt-get install -qy openvpn iptables curl iputils-ping openssh-server supervisor libssl-dev zip less

# SSH
RUN mkdir -p /var/run/sshd
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh
RUN chmod 600 /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh

# Supervisor
RUN mkdir -p /var/log/supervisor
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# OpenVPN
VOLUME /etc/openvpn
VOLUME /root/easy-rsa

CMD ["/usr/bin/supervisord"]