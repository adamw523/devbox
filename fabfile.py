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
from icecoder.fab_inc import *
from ipython.fab_inc import *
from openvpn.fab_inc import *
from seafile_server.fab_inc import *
from seafile_ssl_proxy.fab_inc import *
from seafile_sync.fab_inc import *

import ConfigParser
import json
import os.path
import sys

env.project_name = 'devbox'

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
	env.private_ip = config.get('dodo', 'private_ip')

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

def docker_ports():
    data = json.loads(run('docker ps -q | xargs docker inspect', quiet=True))
    ports = data[0]['NetworkSettings']['Ports']

    for host_data in data:
        # print host_data
        ports = host_data['NetworkSettings']['Ports']
        print host_data['Config']['Hostname'], "-", \
                host_data['NetworkSettings']['IPAddress'], "-", \
                host_data['Config']['Image']
        for port in ports:
            if ports[port]:
                print "\t", ports[port][0]['HostPort'], '\t=>', port

        print

def docker_install_host_tools():
    fabtools.require.deb.packages(['tmux'])
    put('editor_vim/tmux.conf', '/home/%s/.tmux.conf' % (env.user))

def docker_install_host_networking():
    fabtools.require.deb.packages(['vlan'])

    sudo('ifconfig eth0:0 %s up' % (env.private_ip))
    # TODO: virtual NIC needs to survive a reboot

#---------------------------
# OpenVPN Client
#---------------------------
def openvpn_connect():
    """
    Connect to devbox over OpenVPN
    """

    # install requirements
    fabtools.require.deb.packages(['openvpn'])
    if not exists('openvpn'):
        run('mkdir openvpn')

    # open firewall
    sudo('ufw allow 1194/udp')
    sudo('ufw allow 1194/tcp')

    # might need sudo('echo 1 > /proc/sys/net/ipv4/ip_forward')


    # generate key
    run('openvpn --genkey --secret openvpn/static.key')

    # create remote configuration
    server_conf = [
    'dev tun',
    'ifconfig 10.8.30.1 10.8.30.2',
    'secret static.key',
    'comp-lzo',
    'user nobody',
    'group nogroup',
    'daemon'
    ]

    append('openvpn/server.conf', server_conf)

    # kill if already running
    with settings(warn_only=True):
        running = run('pgrep -u nobody openvpn')
        if running:
            sudo('killall openvpn')

    # start remote process
    with cd('openvpn'):
        sudo('openvpn server.conf')

    # configure local process
    get('openvpn/static.key', '/tmp/%s.key' % (env.host))
    local('rm -f /tmp/%s.conf' % (env.host))
    local('echo "remote %s" >> /tmp/%s.conf ' % (env.host, env.host))
    local('echo "dev tun" >> /tmp/%s.conf ' % (env.host))
    local('echo "ifconfig 10.8.30.2 10.8.30.1" >> /tmp/%s.conf ' % (env.host))
    local('echo "secret /tmp/%s.key" >> /tmp/%s.conf ' % (env.host, env.host))
    local('echo "comp-lzo" >> /tmp/%s.conf ' % (env.host))
    local('echo "route %s 255.255.255.255" >> /tmp/%s.conf ' % (env.private_ip, env.host))

    local('sudo /usr/local/sbin/openvpn /tmp/%s.conf' % (env.host))


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

