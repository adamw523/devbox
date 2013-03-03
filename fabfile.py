import ConfigParser
from fabric.utils import abort
from fabric.api import *
from fabric.operations import *
from fabric.colors import green as _green
from fabric.colors import yellow as _yellow
from fabric.colors import red as _red
from fabric.contrib.files import *
from fabtools import require
import fabtools
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
    fabtools.require.deb.packages(['npm', 'libxml2', 'libxml2-dev'])
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
        'libgeos-dev'])

    if not exists('notebookenv'):
        run('virtualenv notebookenv')

    # install iPython notebook requirements in our virtualenv
    run('/home/%s/notebookenv/bin/pip install ipython tornado readline nose pexpect pyzmq pygments' % env.user)
    run('/home/%s/notebookenv/bin/pip install numpy' % env.user)
    run('/home/%s/notebookenv/bin/pip install scipy matplotlib feedparser nose tdaemon' % env.user)
    run('/home/%s/notebookenv/bin/pip install pysqlite PIL markdown requests' % env.user)

    # install basemap
    basemap = run('/home/%s/notebookenv/bin/pip freeze |grep basemap' % env.user)
    if not basemap:
        if not exists('/usr/lib/libgeos.so'):
            sudo('ln -s /usr/lib/libgeos_c.so /usr/lib/libgeos.so')

        with cd('/tmp/'):
            # run('wget http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.6/basemap-1.0.6.tar.gz')
            # run('tar -xzf basemap-1.0.6.tar.gz')
            with cd('basemap-1.0.6'):
                run('/home/%s/notebookenv/bin/python setup.py install' % env.user)

    # link the OpenCV module into our virtualenv
    if not exists('/home/%s/notebookenv/lib/python2.7/site-packages/cv2.so' % env.user):
        run('ln -s /usr/lib/pyshared/python2.7/cv2.so /home/%s/notebookenv/lib/python2.7/site-packages/' % env.user)

    # configuraiton for notbook server
    if not exists('~/.ipython'):
        run('mkdir ~/.ipython')
    put('configs/profile_nbserver', '~/.ipython/')

    # make a directory to put our notbooks in
    if not exists('/data/notebooks'):
        run('mkdir /data/notebooks')

    # nbconvert
    docutils = run('/home/%s/notebookenv/bin/pip freeze |grep docutils' % env.user)
    if not docutils:
        with cd('/tmp'):
            run('curl http://docutils.svn.sourceforge.net/viewvc/docutils/trunk/docutils/?view=tar > docutils.tgz')
            run('/home/%s/notebookenv/bin/pip install docutils.tgz' % env.user)

    run('mkdir -p ~/tools')
    if not exists('~/tools/nbconvert'):
        with cd('~/tools'):
            run('git clone git@github.com:adamw523/nbconvert.git ~/tools/nbconvert')

def ipython_notebook_run():
    with cd('~//data/notebooks'):
        run('/home/%s/notebookenv/bin/ipython notebook --profile nbserver --pylab inline > output.log ')

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
    fabtools.require.deb.packages(['openjdk-7-jre', 'openjdk-7-jdk', 'default-jre', 
        'sharutils', 'dtach'])
    put('lib/aerofs-installer.deb', '/tmp/')
    sudo('dpkg -i /tmp/aerofs-installer.deb')

def aerofs_run_once():
    run('aerofs-cli')

def aerofs_run():
    _runbg('aerofs-cli')

#---------------------------
# VPN
#---------------------------
def openvpn_install():
    """
    Install OpenVPN on server
    """
    require.user('openvpn')

    fabtools.require.deb.packages(['openvpn', 'openvswitch-brcompat'])
    openvpn_vars = {
        "KEY_COUNTRY": "CA",
        "KEY_PROVINCE": "ON",
        "KEY_CITY": "Toronto",
        "KEY_ORG": "TouchBase Consulting",
        "KEY_EMAIL": "adam@tbcn.ca",
        "KEY_CN": "changeme",
        "KEY_NAME": "changeme",
        "KEY_OU": "changeme",
        "network": '10.2.3.0'
    }

    # install if easy-rsa hasn't been copied over and used yet
    if not exists('/home/openvpn/easy-rsa'):
        # use openvpns easy-rsa to create keys and configure openvpn
        sudo('mkdir ~openvpn/easy-rsa/', user='openvpn')
        
        # copy over easy-rsa tools from oepnvpn examples
        sudo('cp -r /usr/share/doc/openvpn/examples/easy-rsa/2.0/* ~openvpn/easy-rsa/', user='openvpn')
        sudo('chown -R openvpn:openvpn ~openvpn/easy-rsa')

        # copy over server.conf file
        upload_template('configs/openvpn_server.conf', '/etc/openvpn/server.conf', openvpn_vars, use_sudo=True)

        # coy over our variables
        upload_template('configs/openvpn_vars.sh', '/home/openvpn/easy-rsa/vars', openvpn_vars, use_sudo=True)

        with cd('~openvpn/easy-rsa'):
            # create keys
            sudo('source ./vars; ./clean-all; ./build-dh; ./pkitool --initca; ./pkitool --server server', user='openvpn')
            
            with cd('keys'):
                # genreate the ta key and copy them into /etc/openvpn
                sudo('openvpn --genkey --secret ta.key', user='openvpn')
                sudo('cp server.crt server.key ca.crt dh1024.pem ta.key /etc/openvpn/')
                sudo('chmod 400 /etc/openvpn/ta.key')

        sudo('service openvpn start')

    # open up the firewall
    sudo('ufw allow 1194/udp')
    sudo('ufw allow 1194/tcp')
    sudo('ufw allow from %s/24' % (openvpn_vars['network']))

def openvpn_create_client():
    """
    Create client keys on server
    """
    hostname = prompt("Host name of the client:")

    # abort if client has been created already
    if exists('/home/openvpn/easy-rsa/keys/%s.crt' % (hostname), use_sudo=True):
        abort('Certificate for client already exists')

    # creeate client keys
    with cd('~openvpn/easy-rsa/'):
        sudo('source vars; ./build-key %s' % hostname, user='openvpn')

def openvpn_download_visc():
    """
    Download OpenVPN configuration files for Viscosity
    """
    hostname = prompt("Host name of the client:")

    if not exists('/home/openvpn/easy-rsa/keys/%s.crt' % (hostname), use_sudo=True):
        abort('Create client keys first with: openvpn_create_client')

    # set up a new directory to create our .visc configruation
    tmp_dir = '/tmp/%s' % (hostname + '.visc')
    if exists(tmp_dir):
        sudo('rm -fR %s' % (tmp_dir))
    
    # vars for the configuration file
    client_conf = {
        "visc_name": hostname,
        "server": env.hosts[0]
    }

    # make tmp directory, copy required items into it
    sudo('mkdir %s' % (tmp_dir))
    sudo('cp /etc/openvpn/ca.crt %s/ca.crt' % (tmp_dir))
    # sudo('cp /etc/openvpn/server.crt %s/server.crt' % (tmp_dir))
    sudo('cp ~openvpn/easy-rsa/keys/%s.crt %s/cert.crt' % (hostname, tmp_dir))
    sudo('cp ~openvpn/easy-rsa/keys/%s.key %s/key.key' % (hostname, tmp_dir))
    sudo('cp /etc/openvpn/ta.key %s/ta.key' % (tmp_dir))
    upload_template('configs/client.visc/config.conf', '%s/config.conf' % (tmp_dir), client_conf, use_sudo=True)
    sudo('chmod -R a+r %s' % (tmp_dir))

    # download .vsic directory and then delete it from server
    get(tmp_dir, '.')
    sudo('rm -fR %s' % (tmp_dir))

#---------------------------
# System Level
#---------------------------
def install_devtools():
    """
    Install development tools
    """
    fabtools.require.deb.packages(['build-essential', 'screen', 'tmux', 'libsqlite3-dev', 
        'git', 'git-svn', 'subversion', 'swig', 'libjpeg-turbo8-dev', 'libjpeg8-dev'])

    quantal64 = run('uname -a |grep quantal64', warn_only=True)
    if quantal64:
        # hack to fix Python PIL
        libs = ['libfreetype.so', 'libpng.so', 'libz.so', 'libjpeg.so']
        for lib in libs:
            sudo('if [ ! -L /usr/lib/%s ]; then ln -s /usr/lib/x86_64-linux-gnu/%s /usr/lib; fi' % (lib, lib), warn_only=True)

    # SSH config
    put('private/ssh/id_rsa_devbox', '/home/%s/.ssh/id_rsa' % env.user, mode=0600)
    put('private/ssh/id_rsa_devbox.pub', '/home/%s/.ssh/id_rsa.pub' % env.user, mode=0600)
    run('chmod 700 ~/.ssh')

    # github config
    run('git config --global user.name "Adam Wisniewski"')
    run('git config --global user.email "adamw@tbcn.ca"')

    # python
    fabtools.require.deb.packages(['python-pip', 'libssl-dev', 'python-dev']) 
    sudo('pip install hyde feedparser fabric dodo M2Crypto virtualenvwrapper')

    setup_bash()

def setup_bash():
    put('configs/bashrc.after', '/home/%s/.bashrc.after' % env.user)
    append('/home/%s/.bashrc' % env.user, "\n. .bashrc.after")

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

