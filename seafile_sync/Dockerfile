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

# Seafile
RUN useradd -m %(user)s
RUN apt-get install -qy python2.7 python-simplejson python-pip
RUN mkdir -p /seafile/downloads
RUN chown -R %(user)s:%(user)s /seafile

USER %(user)s
RUN cd /seafile/downloads && wget http://adamw523.s3.amazonaws.com/seafile/seafile-cli_%(seafile_version)s_%(seafile_arch)s.tar.gz
RUN cd /seafile && tar -xzf downloads/seafile-cli*
RUN mkdir /home/%(user)s/.seafile-client
ADD seafile_cli_run.sh /home/%(user)s/seafile_cli_run.sh
ADD fix_permissions.sh /root/fix_permissions.sh
USER root
RUN chmod +x /home/%(user)s/seafile_cli_run.sh
RUN chmod +x /root/fix_permissions.sh
RUN chown %(user)s:%(user)s /home/%(user)s/seafile_cli_run.sh

# Sync
USER root
VOLUME %(sync_path)s

CMD ["/usr/bin/supervisord"]
# CMD ["/bin/sh", "-c", "while true; do echo hello world; sleep 1; done"]
