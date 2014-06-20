from fabric.utils import abort
from fabric.api import settings
from fabric.operations import open_shell
from fabric.colors import green as _green
from fabric.colors import yellow as _yellow
from fabric.colors import red as _red
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
# from fabric import context_managers
from fabtools import require
import fabtools

from aerofs.fab_inc import *
from editor_cloud9.fab_inc import *
from editor_vim.fab_inc import *
from local_proxy.fab_inc import *
from openvpn.fab_inc import *
from owncloud_server.fab_inc import *
from seafile_server.fab_inc import *
from seafile_ssl_proxy.fab_inc import *
from seafile_sync.fab_inc import *

import ConfigParser
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

def dodo():
	"""
	Select DigitalOcean environment
	"""

	# get config file
	config = ConfigParser.ConfigParser()
	config.read(['private/dodo.cfg'])

	# set values from config
	env.hosts = [config.get('dodo', 'host')]
	env.user = config.get('dodo', 'user')

def minee_base():
    """
    Select minee environment
    """

    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/minee.cfg'])

    # set values from config
    env.hosts = [config.get('minee_base', 'host')]
    env.user = config.get('minee_base', 'user')
    env.port = config.get('minee_base', 'port')

def minee_docker():
	"""
	Select minee docker host environment
	"""

	# get config file
	config = ConfigParser.ConfigParser()
	config.read(['private/minee.cfg'])

	# set values from config
	env.hosts = [config.get('dockerhost', 'host')]
	env.user = config.get('dockerhost', 'user')
	env.port = config.get('dockerhost', 'port')

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

def _work_dir():
    if not exists('~/work'):
        run('mkdir ~/work')

def _scripts_dir():
    if not exists('~/scripts'):
        run('mkdir ~/scripts')

def c9_install():
    """
    Insatll Could9 IDE and dependencies
    """
    print(_green("Cloud9 IDE"))
    install_devtools()
    nodejs_install()
    fabtools.require.deb.packages(['npm', 'libxml2', 'libxml2-dev'])
    sudo('npm install -g sm')
    sudo('npm install qs mime formidable q n-util wrench detective')
    _work_dir()
    with cd('~/work'):
        if not exists('cloud9'):
            run('git clone https://github.com/ajaxorg/cloud9.git cloud9')
        with cd('cloud9'):
            run('git checkout v2.0.93')
            sudo('sm install')

def c9_start():
    _scripts_dir()
    put('scripts/run_cloud9.sh', '~/scripts/run_cloud9.sh')
    with cd('~/work/cloud9'):
        run('sh ~/scripts/run_cloud9.sh')

def c9_kill():
    with cd('~/work/cloud9'):
        run('killall node')

def nodejs_install():
    """
    Install nodejs
    """
    with settings(warn_only=True):
        if not run('which node'):
            with cd('/tmp'):
                if not exists('node'):
                    sudo('git clone https://github.com/joyent/node.git')
                with cd('node'):
                    sudo('git checkout v0.8.18') #Try checking nodejs.org for what the stable version is
                    sudo('./configure')
                    sudo('make')
                    sudo('make install')

#---------------------------
# Yeoman
#---------------------------
def yeoman_install():
    nodejs_install()
    sudo('gem install --no-ri --no-rdoc compass')
    fabtools.require.deb.packages(['libjpeg-turbo-progs', 'optipng'])

    if not run('which phantomjs', warn_only=True):
        if not exists('phantomjs-1.8.1-linux-i686'):
            run('wget http://phantomjs.googlecode.com/files/phantomjs-1.8.1-linux-i686.tar.bz2')
            run('tar xjf phantom*')
            if not exists('/usr/local/bin/phantomjs'):
                sudo('ln -s /home/vagrant/phantomjs-1.8.1-linux-i686/bin/phantomjs /usr/local/bin/phantomjs')

    sudo('npm install -g yeoman')


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
    fabtools.require.deb.packages(['python-pip', 'python-dev', 'libncurses5', 'libncurses5-dev'])
    sudo('pip install ipython virtualenv')

def ipython_notebook_install():
    ipython_install()

    fabtools.require.deb.packages(['libatlas-base-dev', 'gfortran', 'python-scipy', 
        'libfreetype6', 'libfreetype6-dev', 'libpng12-dev', 'python-opencv', 'pandoc',
        'libgeos-dev', 'libjpeg-dev', 'libhdf5-dev'])

    if not exists('notebookenv'):
        run('virtualenv notebookenv')

    # install iPython notebook requirements in our virtualenv
    run('/home/%s/notebookenv/bin/pip install ipython tornado readline nose pexpect pyzmq pygments pytest mock' % env.user)
    run('/home/%s/notebookenv/bin/pip install numpy' % env.user)
    run('/home/%s/notebookenv/bin/pip install scipy matplotlib feedparser nose tdaemon' % env.user)
    run('/home/%s/notebookenv/bin/pip install pysqlite PIL markdown requests numexpr cython' % env.user)
    run('/home/%s/notebookenv/bin/pip install pandas networkx oauth2 beautifulsoup4 tables nltk' % env.user)
    run('/home/%s/notebookenv/bin/pip install scikit-learn paramiko' % env.user)
    run('/home/%s/notebookenv/bin/pip install scikit-image' % env.user)
    run('/home/%s/notebookenv/bin/pip install nosecolor nose-watch argcomplete' % env.user)
    run('/home/%s/notebookenv/bin/pip install boto' % env.user)

    # link the OpenCV module into our virtualenv
    if not exists('/home/%s/notebookenv/lib/python2.7/site-packages/cv2.so' % env.user):
        run('ln -s /usr/lib/pyshared/python2.7/cv2.so /home/%s/notebookenv/lib/python2.7/site-packages/' % env.user)

    # configuraiton for notbook server
    if not exists('~/.ipython'):
        run('mkdir ~/.ipython')
    put('configs/profile_nbserver', '~/.ipython/')

    # nbconvert
    docutils = run('/home/%s/notebookenv/bin/pip freeze |grep docutils' % env.user, warn_only=True)
    if not docutils:
        with cd('/tmp'):
            run('curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz')
            run('/home/%s/notebookenv/bin/pip install docutils.tgz' % env.user)

    run('mkdir -p ~/tools')
    if not exists('~/tools/nbconvert'):
        with cd('~/tools'):
            run('git clone git@github.com:adamw523/nbconvert.git ~/tools/nbconvert')

def ipython_notebook_run():
    with cd('~/AeroFS/devshare/notebooks'):
        _runbg('/home/%s/notebookenv/bin/ipython notebook --profile nbserver --pylab inline > output.log ' % env.user)

#---------------------------
# GIS libraries for Notebook
#---------------------------
def notebook_gis_install():
    # install basemap
    with settings(warn_only=True):
        basemap = run('/home/%s/notebookenv/bin/pip freeze |grep basemap' % env.user)

    if not basemap:
        if not exists('/usr/lib/libgeos.so'):
            sudo('ln -s /usr/lib/libgeos_c.so /usr/lib/libgeos.so')

        with cd('/tmp/'):
            run('wget http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.6/basemap-1.0.6.tar.gz')
            run('tar -xzf basemap-1.0.6.tar.gz')
            with cd('basemap-1.0.6'):
                run('/home/%s/notebookenv/bin/python setup.py install' % env.user)
            run('rm -fR basemap-1.0.6')

    # install shapefile library
    with settings(warn_only=True):
        shapefile = run('/home/%s/notebookenv/bin/pip freeze |grep shapefile' % env.user)

    if not shapefile:
        with cd('/tmp/'):
            run('git clone https://github.com/adamw523/pyshp.git')
            with cd('pyshp'):
                run('/home/%s/notebookenv/bin/python setup.py install' % env.user)
            run('rm -fR pyshp')

#---------------------------
# Ruby / Rails Env
#---------------------------
def ruby_install():
    fabtools.require.deb.packages(['ruby', 'ruby-dev'])
    rbenv_install()
    bundler_install()

def rbenv_install():
    if not exists('~/.rbenv'):
        run('git clone git://github.com/sstephenson/rbenv.git ~/.rbenv')
    if not exists('~/.rbenv/plugins/ruby-build'):
        run('git clone git://github.com/sstephenson/ruby-build.git ~/.rbenv/plugins/ruby-build')

    append('~/.profile', '\nexport PATH="$HOME/.rbenv/bin:$PATH"');
    append('~/.profile', '\neval "$(rbenv init -)"')

def bundler_install():
    sudo('gem install bundler')

#---------------------------
# VIM
#---------------------------
def vim_copy_config():
    put('configs/vimrc.after', '/home/%s/.vimrc.after' % env.user)

def vim_janus_install():
    fabtools.require.deb.packages(['rake', 'git', 'curl', 'ctags', 'vim'])
    run('curl -Lo- https://bit.ly/janus-bootstrap | bash')
    vim_copy_config()

#---------------------------
# tmux
#---------------------------
def tmux_copy_config():
    put('configs/tmux.conf', '/home/%s/.tmux.conf' % env.user)

#---------------------------
# AWS
#---------------------------
def aws_install_boto():
    sudo('pip install boto boto-rsync')

def aws_copy_creds():
    put('private/boto.cfg', '/etc/boto.cfg', use_sudo=True)

def aws_copy_MailStore():
    run('python /vagrant/scripts/upload_MailStore.py')

#----------------------------
# Docker
#----------------------------
def docker_install():
    update_system(force=False)
    sudo("sh -c 'wget -qO- https://get.docker.io/gpg | apt-key add -'")
    append('/etc/apt/sources.list.d/docker.list', 'deb http://get.docker.io/ubuntu docker main', use_sudo=True)
    #update_system()
    fabtools.require.deb.packages(['lxc-docker'])
    fabtools.user.modify('deploy', extra_groups=['docker'])

    # have Docker listen on TCP as well as the socket
    # sed('/etc/init/docker.conf', 'DOCKER_OPTS=', 'DOCKER_OPTS="-H tcp://0.0.0.0:4243 -H unix:///var/run/docker.sock"', use_sudo=True)

    # create docker directories
    fabtools.require.files.directories(['/home/deploy/docker/ids'])

    # defalt ufw to allow NATed ports
    sed('/etc/default/ufw', 'DEFAULT_FORWARD_POLICY="DROP"', 'DEFAULT_FORWARD_POLICY="ACCEPT"', use_sudo=True)
    sudo('ufw reload')

def docker_port_maps(container, port):
    pass

#---------------------------
# OpenVPN Client
#---------------------------
def configure_openvpn_client(zip_path=None):
    """
    Configure devbox as OpenVPN client
    """
    if not zip_path:
        abort("Please provide a path to zip config ovpn file. eg: configure_openvpn_client:adam.zip")

    fabtools.require.deb.packages(['openvpn'])
    run('mkdir -p /tmp/client.ovpn')
    put(zip_path, '/tmp/client.ovpn/client.ovpn.zip')
    with cd('/tmp/client.ovpn'):
        run('unzip client.ovpn.zip')
        dirname = run("dirname `find . -name 'cert.crt' | head -n1`")
        sudo("cp %(dn)s/key.key %(dn)s/ca.crt %(dn)s/ta.key %(dn)s/cert.crt /etc/openvpn/" % {'dn': dirname})
        sudo("cp %(dn)s/config.ovpn /etc/openvpn/client.conf" % {'dn': dirname})

    sudo('service openvpn restart')
    run('rm -fR /tmp/client.ovpn')


#---------------------------
# System Level
#---------------------------

def create_swapfile():
    sudo('swapoff -a')
    sudo('fallocate -l 1024M /swapfile')
    sudo('chmod 600 /swapfile')
    sudo('mkswap /swapfile')
    sudo('swapon /swapfile')


def install_devtools():
    """
    Install development tools
    """
    fabtools.require.deb.packages(['build-essential', 'screen', 'tmux', 'libsqlite3-dev', 
        'git', 'git-svn', 'subversion', 'swig', 'libjpeg-turbo8-dev', 'libjpeg8-dev',
        'mercurial', 'sqlite3', 'bash-completion', 'libssl-dev'])

    with settings(warn_only=True):
        quantal64 = run('uname -a |grep quantal64')
        libs = ['libfreetype.so', 'libpng.so', 'libz.so', 'libjpeg.so']
        if quantal64:
            # hack to fix Python PIL
            for lib in libs:
                sudo('if [ ! -L /usr/lib/%s ]; then ln -s /usr/lib/x86_64-linux-gnu/%s /usr/lib; fi' % (lib, lib))
        else:
            for lib in libs:
                sudo('if [ ! -L /usr/lib/%s ]; then ln -s /usr/lib/i386-linux-gnu/%s /usr/lib; fi' % (lib, lib))


    # SSH config
    put('private/ssh/id_rsa_devbox', '/home/%s/.ssh/id_rsa' % env.user, mode=0600)
    put('private/ssh/id_rsa_devbox.pub', '/home/%s/.ssh/id_rsa.pub' % env.user, mode=0600)
    run('chmod 700 ~/.ssh')

    # github config
    run('git config --global user.name "Adam Wisniewski"')
    run('git config --global user.email "adamw@tbcn.ca"')

    # python
    fabtools.require.deb.packages(['python-pip', 'libssl-dev', 'python-dev'])
    sudo('pip install hyde feedparser fabric dodo virtualenvwrapper fabtools')

    # M2Crypto pip not installing on Ubuntu 13.10 .. fix might be below, if package needed
    # http://blog.rectalogic.com/2013/11/installing-m2crypto-in-python.html
    # DEB_HOST_MULTIARCH=x86_64-linux-gnu pip install "git+git://anonscm.debian.org/collab-maint/m2crypto.git@debian/0.21.1-3#egg=M2Crypto"

    setup_bash()

def setup_bash():
    put('configs/bashrc.after', '/home/%s/.bashrc.after' % env.user)
    append('/home/%s/.bashrc' % env.user, "\n. ~/.bashrc.after")

def lock_down_firewall():
    """
    Install Uncomplicated Firewall and lock down everything except for SSH
    """
    fabtools.require.deb.packages(['ufw'])
    sudo('ufw default deny')
    sudo('ufw enable')
    sudo('ufw allow ssh')

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

def shell():
    open_shell()

