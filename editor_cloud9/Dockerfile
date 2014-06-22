FROM ubuntu:14.04
RUN export http_proxy=%(proxy_url)s; \
    apt-get update -q --fix-missing

## Cloud9
RUN export http_proxy=%(proxy_url)s; \
    apt-get install -qy git nodejs npm curl

RUN ln -s /usr/bin/nodejs /usr/bin/node

# add user
RUN useradd -m %(user)s

# init environment script
ADD my_init.sh /home/%(user)s/my_init.sh
ADD run_cloud9.sh /home/%(user)s/run_cloud9.sh
RUN chown adam:adam /home/%(user)s/*
RUN chmod a+x /home/%(user)s/*.sh

USER %(user)s

# nvm for old versions of node
RUN . /home/%(user)s/my_init.sh; \
    cd $HOME; \
    git config --add http.proxy $http_proxy; \
    git clone git://github.com/creationix/nvm.git ~/.nvm;

RUN . /home/%(user)s/my_init.sh; \
    . /home/%(user)s/.nvm/nvm.sh; \
    NVM_DIR=~/.nvm; \
    nvm install v0.8

# install cloud9
RUN export http_proxy=%(proxy_url)s; \
    export HOME=/home/%(user)s; \
    cd $HOME; \
    mkdir .git; \
    git config --add http.proxy $http_proxy; \
    git clone http://github.com/ajaxorg/cloud9.git; \
    cd cloud9; \
    npm install

CMD ["/home/%(user)s/run_cloud9.sh"]

