FROM ubuntu:trusty
RUN apt-get update -q
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
RUN apt-get install -qy python2.7 python-setuptools python-simplejson python-imaging sqlite3
EXPOSE 8082
EXPOSE 10001
EXPOSE 12001
RUN mkdir -p /seafile/downloads
RUN cd /seafile/downloads && wget http://adamw523.s3.amazonaws.com/seafile/seafile-server_3.0.3_x86-64.tar.gz
RUN cd /seafile && tar -xzf downloads/seafile-ser*

CMD ["/usr/bin/supervisord"]
