FROM ubuntu:14.04

RUN apt-get update -q

# requirements
RUN apt-get -qy install libatlas-base-dev gfortran libfreetype6-dev \
    libpng12-dev pandoc libgeos-dev libjpeg-dev libhdf5-dev libncurses5-dev

# SSH
RUN apt-get -qy install openssh-server
RUN mkdir -p /var/run/sshd
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh
RUN chmod 600 /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN sed -i -e "s/session\s*required\s*pam_loginuid.so/#session required pam_loginuid.so/" /etc/pam.d/sshd

# Supervisor
RUN apt-get install -qy curl supervisor
RUN mkdir -p /var/log/supervisor
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# add user
RUN useradd -m %(user)s

# IPython
RUN apt-get -qy install python-pip python-dev python-virtualenv

RUN virtualenv /home/adam/notebookenv

RUN /home/%(user)s/notebookenv/bin/pip install ipython tornado readline \
    pexpect pyzmq pygments pytest mock

RUN /home/%(user)s/notebookenv/bin/pip install \
    numpy scipy

RUN apt-get -qy install pkg-config libsqlite3-dev

RUN ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
RUN ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib
RUN ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib
RUN ln -s /usr/include/freetype2 /usr/local/include/freetype

RUN /home/%(user)s/notebookenv/bin/pip install PIL  \
    --allow-external PIL --allow-unverified PIL

RUN /home/%(user)s/notebookenv/bin/pip install  \
    numexpr matplotlib feedparser \
    tdaemon pysqlite markdown requests cython pandas networkx oauth2

RUN /home/%(user)s/notebookenv/bin/pip install  \
    beautifulsoup4 tables nltk scikit-learn paramiko scikit-image \
    nose nosecolor nose-watch argcomplete boto jinja2

RUN apt-get install libgeos++-dev

RUN /home/%(user)s/notebookenv/bin/pip install basemap \
    --allow-external basemap --allow-unverified basemap


RUN chown -R %(user)s:%(user)s /home/%(user)s/*

CMD ["/usr/bin/supervisord"]
