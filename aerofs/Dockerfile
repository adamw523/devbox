FROM ubuntu:precise
RUN echo deb http://archive.ubuntu.com/ubuntu/ precise main universe > /etc/apt/sources.list.d/precise.list
RUN apt-get update -q
RUN apt-get install -qy curl iputils-ping openssh-server supervisor

# SSH
RUN mkdir -p /var/run/sshd
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh
RUN chmod 600 /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh

# Supervisor
RUN mkdir -p /var/log/supervisor
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# AeroFS
VOLUME /root
VOLUME /AeroFS

#ADD aerofs-installer.deb /tmp/aerofs-installer.deb

# needs to run privileged for jdk install (which requires fuse)
# RUN apt-get install -qy openjdk-7-jre openjdk-7-jdk default-jre sharutils dtach

#RUN dpkg --install /aerofs-installer.deb

CMD ["/usr/bin/supervisord"]