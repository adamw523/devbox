FROM ubuntu:trusty
RUN apt-get install -qy curl iputils-ping openssh-server supervisor
RUN apt-get update -q --fix-missing

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
RUN useradd -m adam
RUN apt-get install -qy python2.7 python-simplejson python-pip
RUN mkdir -p /seafile/downloads
RUN chown -R adam:adam /seafile

USER adam
RUN cd /seafile/downloads && wget http://adamw523.s3.amazonaws.com/seafile/seafile-cli_%(seafile_version)s_%(seafile_arch)s.tar.gz
RUN cd /seafile && tar -xzf downloads/seafile-cli*
RUN mkdir /home/adam/.seafile-client
ADD seafile_cli_run.sh /home/adam/seafile_cli_run.sh
USER root
RUN chmod +x /home/adam/seafile_cli_run.sh
RUN chown adam:adam /home/adam/seafile_cli_run.sh

# Sync
VOLUME %(sync_path)s
RUN mkdir %(sync_path)s
RUN chown adam:adam %(sync_path)s

CMD ["/usr/bin/supervisord"]
