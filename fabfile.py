from fabric.api import *
from fabric.operations import *
from fabric.colors import green as _green
from fabric.colors import yellow as _yellow
from fabric.colors import red as _red
from fabric.contrib.files import *
import os.path
import sys

env.project_name = 'devbox'

def _set_vagrant_env():
	pass

def _runbg(cmd, sockname="dtach"):
    return run('dtach -n `mktemp -u /tmp/%s.XXXX` %s'  % (sockname,cmd))

#---------------------------
# Environemnts
#---------------------------

def vagrant():
    """
    Select vagrant-managed VM for commands
    """
    env.settings = 'vagrant'

    # get vagrant ssh setup
    vagrant_config = _get_vagrant_config()
    env.key_filename = vagrant_config['IdentityFile']
    env.hosts = ['%s:%s' % (vagrant_config['HostName'], vagrant_config['Port'])]
    env.user = vagrant_config['User']
    env.disable_known_hosts = True

    _set_vagrant_env()

#---------------------------
# Cloud9 IDE
#---------------------------

def c9_install():
    """
    Insatll Could9 IDE and dependencies
    """
    print(_green("Cloud9 IDE"))
    install_devtools()
    nodejs_install()
    sudo('apt-get -y install npm libxml2 libxml2-dev')
    sudo('npm install -g sm')
    sudo('npm install qs mime formidable q n-util wrench detective')
    with cd('/data_local'):
        if not exists('cloud9'):
            run('git clone https://github.com/ajaxorg/cloud9.git cloud9')
        with cd('cloud9'):
            run('git checkout v2.0.86')
            sudo('sm install')

def c9_start():
    with cd('/data_local/cloud9'):
        run('sh /vagrant/scripts/run_cloud9.sh')

def c9_kill():
    with cd('/data_local/cloud9'):
        run('killall node')

def nodejs_install():
    """
    Install nodejs
    """
    if not run('which node', warn_only=True):
        with cd('/tmp'):
            if not exists('node'):
                sudo('git clone https://github.com/joyent/node.git')
            with cd('node'):
                sudo('git checkout v0.6.18') #Try checking nodejs.org for what the stable version is
                sudo('./configure')
                sudo('make')
                sudo('make install')

#---------------------------
# Gmail Backup
#---------------------------
def gmailbackup_install():
    with cd('/data'):
        if not exists('gmailbackup'):
            run('mkdir gmailbackup')
            run('wget http://gmailbackup.googlecode.com/files/gmailbackup-20100324_0051.tgz')
            run('tar -xzf gmailbackup-20100324_0051.tgz')
        else:
            print(_red('Already installed'))

#---------------------------
# IPython
#---------------------------
def ipython_install():
    sudo('apt-get -y install python-pip python-dev libncurses5 libncurses5-dev')
    sudo('pip install ipython virtualenv')

def ipython_notebook_install():
    sudo('apt-get -y install libatlas-base-dev gfortran python-scipy libfreetype6 libfreetype6-dev libpng12-dev')
    sudo('apt-get -y install python-opencv pandoc')
    #sudo('apt-get -y install python-mpltoolkits.basemap')
    #sudo('apt-get -y install python-mpltoolkits.basemap-data')
    sudo('apt-get -y install libgeos-dev')

    if not exists('notebookenv'):
        run('virtualenv notebookenv')

    # install iPython notebook requirements in our virtualenv
    run('/home/vagrant/notebookenv/bin/pip install ipython tornado readline nose pexpect pyzmq pygments')
    run('/home/vagrant/notebookenv/bin/pip install numpy')
    run('/home/vagrant/notebookenv/bin/pip install scipy')
    run('/home/vagrant/notebookenv/bin/pip install matplotlib')
    run('/home/vagrant/notebookenv/bin/pip install feedparser')
    run('/home/vagrant/notebookenv/bin/pip install nose')
    run('/home/vagrant/notebookenv/bin/pip install pysqlite')
    run('/home/vagrant/notebookenv/bin/pip install PIL')
    run('/home/vagrant/notebookenv/bin/pip install markdown')

    # install basemap
    basemap = run('/home/vagrant/notebookenv/bin/pip freeze |grep basemap')
    if not basemap:
        if not exists('/usr/lib/libgeos.so'):
            sudo('ln -s /usr/lib/libgeos_c.so /usr/lib/libgeos.so')

        with cd('/tmp/'):
            # run('wget http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.6/basemap-1.0.6.tar.gz')
            # run('tar -xzf basemap-1.0.6.tar.gz')
            with cd('basemap-1.0.6'):
                run('/home/vagrant/notebookenv/bin/python setup.py install')


    # link the OpenCV module into our virtualenv
    if not exists('/home/vagrant/notebookenv/lib/python2.7/site-packages/cv2.so'):
        run('ln -s /usr/lib/pyshared/python2.7/cv2.so /home/vagrant/notebookenv/lib/python2.7/site-packages/')

    # configuraiton for notbook server
    if not exists('~/.ipython'):
        run('mkdir ~/.ipython')
    put('configs/profile_nbserver', '~/.ipython/')

    # make a directory to put our notbooks in
    if not exists('/data/notebooks'):
        run('mkdir /data/notebooks')

    # nbconvert
    docutils = run('/home/vagrant/notebookenv/bin/pip freeze |grep docutils')
    if not docutils:
        with cd('/tmp'):
            run('curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz')
            run('/home/vagrant/notebookenv/bin/pip install docutils.tgz')

    run('mkdir -p ~/tools')
    if not exists('~/tools/nbconvert'):
        with cd('~/tools'):
            run('git clone git@github.com:adamw523/nbconvert.git ~/tools/nbconvert')

def ipython_notebook_run():
    with cd('/data/notebooks'):
        run('/home/vagrant/notebookenv/bin/ipython notebook --profile nbserver --pylab inline > output.log ')

#---------------------------
# Ruby / Rails Env
#---------------------------
def rbenv_install():
    run('git clone git://github.com/sstephenson/rbenv.git ~/.rbenv')
    append('~/.profile', '\nexport PATH="$HOME/.rbenv/bin:$PATH"');
    append('~/.profile', '\neval "$(rbenv init -)"')
    run('git clone git://github.com/sstephenson/ruby-build.git ~/.rbenv/plugins/ruby-build')

#---------------------------
# VIM
#---------------------------
def vim_janus_install():
    sudo('apt-get install -y rake git curl ctags')
    run('curl -Lo- https://bit.ly/janus-bootstrap | bash')

def vim_copy_config():
    put('configs/vimrc.after', '/home/vagrant/.vimrc.after')

#---------------------------
# AWS
#---------------------------
def aws_install_boto():
    sudo('pip install boto')

def aws_copy_creds():
    put('private/boto.cfg', '/etc/boto.cfg', use_sudo=True)

def aws_copy_MailStore():
    run('python /vagrant/scripts/upload_MailStore.py')

#----------------------------
# AeroFS
#----------------------------
def aerofs_install():
    sudo('apt-get install -y openjdk-7-jre openjdk-7-jdk default-jre sharutils dtach')
    sudo('dpkg -i /vagrant/lib/aerofs-installer.deb')

def aerofs_run_once():
    run('aerofs-cli')

def aerofs_run():
    _runbg('aerofs-cli')

#---------------------------
# System Level
#---------------------------
def install_devtools():
    """
    Install development tools
    """
    sudo('apt-get -y install git build-essential screen tmux libsqlite3-dev')
    if not exists('/data_local'):
        sudo('mkdir /data_local')
        sudo('chown -R vagrant:vagrant /data_local')

    sudo('apt-get install -y libjpeg-turbo8-dev libjpeg8-dev')

    quantal64 = run('uname -a |grep quantal64', warn_only=True)
    if quantal64:
        # hack to fix Python PIL
        libs = ['libfreetype.so', 'libpng.so', 'libz.so', 'libjpeg.so']
        for lib in libs:
            sudo('if [ ! -L /usr/lib/%s ]; then ln -s /usr/lib/x86_64-linux-gnu/%s /usr/lib; fi' % (lib, lib), warn_only=True)

    # SSH config
    put('private/ssh/id_rsa*', '/home/vagrant/.ssh/', mode=0600)
    run('chmod 700 ~/.ssh')

    # github config
    run('git config --global user.name "Adam Wisniewski"')
    run('git config --global user.email "adamw@tbcn.ca"')

    # python
    sudo('pip install hyde')

def setup_bash():
    put('configs/bashrc.after', '/home/vagrant/.bashrc.after')
    append('/home/vagrant/.bashrc', "\n. .bashrc.after")

def update_system(force=True):
    """
    Update apt-get sources, only if force=True OR last update was over a week ago
    """
    print(_green("Updating apt if needed"))

    mfile = run('find /tmp/ -name fab_apt_update -mtime -7  -print')
    if force or len(mfile) is 0:
        sudo('apt-get update')
        run('touch /tmp/fab_apt_update')

def set_timezone():
    """
    Set the timezone to America/Toronto
    """
    print(_green("Setting timezone"))

    sudo('echo "America/Toronto" | sudo tee /etc/timezone')
    sudo('sudo dpkg-reconfigure tzdata --frontend noninteractive tzdata')

def vagrant_remount():
    """Remount the vagrant partition"""
    sudo("mount /vagrant -o remount")
    sudo("mount /data -o remount")

def _get_vagrant_config():
    """
    Parses vagrant configuration and returns it as dict of ssh parameters
    and their values
    """
    result = local('vagrant ssh-config', capture=True)
    conf = {}
    for line in iter(result.splitlines()):
        parts = line.split()
        conf[parts[0]] = ' '.join(parts[1:])

    return conf

