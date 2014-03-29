import ConfigParser
import fabtools
import re

from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template

def _oc_server_docker_vars():
    return {
        'image': 'adamw523/owncloud_server',
        'tag': 'latest',
        'work_dir': '/home/deploy/docker/owncloud_server_work/',
        'public_ssh_port': 8022,
        'public_http_port': 8080
    }

def _private_oc_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/owncloud_server.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

def oc_build_self_signed_cert():
    config_vars = _private_oc_config()
    local("mkdir -p private/owncloud")
    local("openssl genrsa -des3 -passout pass:x -out private/owncloud/server.pass.key 2048")
    local("openssl rsa -passin pass:x -in private/owncloud/server.pass.key -out private/owncloud/server.key")
    local("rm private/owncloud/server.pass.key")
    # Create the CSR
    subj = "\"/C=%(country)s/ST=%(state)s/L=%(locality)s/O=%(org_name)s/CN=%(server_address)s\"" % dict(config_vars.items('owncloud'))
    local("openssl req -new -key private/owncloud/server.key -out private/owncloud/server.csr -subj %(subj)s" % {'subj': subj})

    # Sign the CSR
    local("openssl x509 -req -days 365 -in private/owncloud/server.csr -signkey private/owncloud/server.key -out private/owncloud/server.crt")

#writing RSA key
#$ rm server.pass.key
#$ openssl req -new -key server.key -out server.csr
#...
#Country Name (2 letter code) [AU]:US
#State or Province Name (full name) [Some-State]:California
#...
#A challenge password []:
#...


#----------------------------
# Inside ownCloud Server container
#----------------------------


#----------------------------
# On Docker host
#----------------------------

def oc_server_build():
    """
    Build the ownCloud Server image
    """
    docker_vars = _oc_server_docker_vars()
    work_dir = docker_vars['work_dir']

    fabtools.require.files.directories([work_dir])

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('owncloud_server/supervisord.conf', work_dir)

    # Apache config
    put('owncloud_server/configs/001-owncloud.conf', work_dir)

    # Dockerfile
    put('owncloud_server/Dockerfile', work_dir)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        
        run('docker build -t %(image)s .' % docker_vars)

def oc_server_run():
    """
    Run the ownCloud Server docker container from the image
    """
    docker_vars = _oc_server_docker_vars()

    # allow SSH traffic to container
    sudo('ufw allow %(public_ssh_port)s' % docker_vars)

    # run the container
    run_cmd = 'docker run -d -p %(public_ssh_port)s:22 -p %(public_http_port)s:80 %(image)s ' % docker_vars
    run('ID=$(%s) && echo $ID > /home/deploy/docker/ids/owncloud_container' % run_cmd)

def oc_server_start():
    """
    Start the previously run ownCloud Server docker container
    """
    docker_vars = _oc_serer_docker_vars()

    # start the container
    run('docker start `cat /home/deploy/docker/ids/owncloud_server_container`')

def oc_server_stop():
    """
    Stop the ownCloud Server docker container
    """
    docker_vars = _oc_server_docker_vars()

    # kill the container
    run('docker stop `cat /home/deploy/docker/ids/owncloud_container`')

def oc_server():
    """
    Set the environment to the ownCloud Server container
    """
    docker_vars = _oc_server_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def oc_server_ssh_command():
    """
    Print out a command line to ssh to ownCloud Server container
    """
    docker_vars = _oc_server_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

