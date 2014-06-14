FROM ubuntu:trusty
RUN apt-get update -q --fix-missing
RUN apt-get install -qy curl iputils-ping openssh-server supervisor

# SSH
RUN mkdir -p /var/run/sshd
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh
RUN chmod 600 /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN sed -i -e "s/session\s*required\s*pam_loginuid.so/#session required pam_loginuid.so/" /etc/pam.d/sshd
EXPOSE 8022

# Supervisor
RUN mkdir -p /var/log/supervisor
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Users SSH
RUN useradd -m %(user)s -s /bin/bash
ADD authorized_keys /tmp/home/%(user)s/.ssh/authorized_keys
RUN chmod 700 /tmp/home/%(user)s/.ssh
RUN chmod 600 /tmp/home/%(user)s/.ssh/*
RUN chown -R adam:adam /tmp/home/%(user)s
# below is a weird hack that prevents 'permission denied' errors
RUN shopt -s dotglob; mv /tmp/home/%(user)s/* /home/%(user)s/ 

# vim

CMD ["/usr/bin/supervisord"]
