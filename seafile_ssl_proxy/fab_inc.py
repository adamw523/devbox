import ConfigParser
import fabtools
import glob
import re

from datetime import datetime
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm

def _sf_ssl_proxy_docker_vars():
    return {
        'image': 'adamw523/seafile_ssl_proxy',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/seafile_ssl_proxy_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ssh_port': 8023,
        'public_https_port': 8443,
        'seafile_version': '3.0.3',
        'seafile_arch': 'x86-64'
    }

def _sf_ssl_proxy_private_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/seafile_ssl_proxy.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

def sf_build_self_signed_cert():
    config_vars = _sf_ssl_proxy_private_config()
    local("mkdir -p private/seafile_ssl_proxy")
    local("openssl genrsa -des3 -passout pass:x -out private/seafile_ssl_proxy/server.pass.key 2048")
    local("openssl rsa -passin pass:x -in private/seafile_ssl_proxy/server.pass.key -out private/seafile_ssl_proxy/server.key")
    local("rm private/seafile_ssl_proxy/server.pass.key")

    # Create the CSR
    subj = "\"/C=%(country)s/ST=%(state)s/L=%(locality)s/O=%(org_name)s/CN=%(server_address)s\"" % dict(config_vars.items('seafile'))
    local("openssl req -new -key private/seafile_ssl_proxy/server.key -out private/seafile_ssl_proxy/server.csr -subj %(subj)s" % {'subj': subj})

    # Sign the CSR
    local("openssl x509 -req -days 365 -in private/seafile_ssl_proxy/server.csr -signkey private/seafile_ssl_proxy/server.key -out private/seafile_ssl_proxy/server.crt")


#----------------------------
# Inside Nginx SSL Proxy container
#----------------------------

def sf_server_configure():
    """Start the configuration of Seafile. Run through this step manually"""

    docker_vars = _sf_ssl_proxy_docker_vars()
    with cd('/seafile/seafile-server-%(seafile_version)s' % docker_vars):
        run('./setup-seafile.sh')

#----------------------------
# On Docker host
#----------------------------

def _require_ssl_proxy_dirs():
    docker_vars = _sf_ssl_proxy_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def sf_ssl_proxy_build():
    """
    Build the Nginx Seafile Server SSL Proxy image
    """
    _require_ssl_proxy_dirs()
    docker_vars = _sf_ssl_proxy_docker_vars()
    config_vars = _sf_ssl_proxy_private_config()
    config_vars_dict = dict(config_vars.items('seafile'))
    work_dir = docker_vars['work_dir']

    # nginx/ssl configuration
    upload_template('private/seafile_ssl_proxy/default.conf', work_dir, dict(config_vars_dict.items() + {'docker_host': env.host}.items()))
    put('private/seafile_ssl_proxy/server.key', work_dir)
    put('private/seafile_ssl_proxy/server.crt', work_dir)

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('seafile_ssl_proxy/supervisord.conf', work_dir)

    # Dockerfile
    upload_template('seafile_ssl_proxy/Dockerfile', work_dir + '/', docker_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def sf_ssl_proxy_run():
    """
    Run the Seafile SSL Proxy docker container from the image
    """
    _require_ssl_proxy_dirs()
    docker_vars = _sf_ssl_proxy_docker_vars()

    # run the container
    port_options = ['-p %(public_ssh_port)s:22 ' % docker_vars,
                '-p %(public_https_port)s:8443 ' % docker_vars
            ]

    port_options_str = ' '.join(port_options)
    run_cmd = 'docker run -i -d ' + port_options_str + ' %(image)s ' % docker_vars
    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/seafile_ssl_proxy_container' %
            (run_cmd, env.user))

def sf_ssl_proxy_start():
    """
    Start the previously run Seafile SSL Proxy docker container
    """
    _require_ssl_proxy_dirs()
    docker_vars = _sf_ssl_proxy_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/seafile_ssl_proxy_container`' %
            env.user)

def sf_ssl_proxy_stop():
    """
    Stop the Seafile SSL Proxy docker container
    """
    _require_ssl_proxy_dirs()
    docker_vars = _sf_ssl_proxy_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/seafile_ssl_proxy_container`' % env.user)

def sf_ssl_proxy():
    """
    Set the environment to the Seafile SSL Proxy container
    """
    docker_vars = _sf_ssl_proxy_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def sf_ssl_proxy_ssh_command():
    """
    Print out a command line to ssh to Seafile SSL Proxy container
    """
    docker_vars = _sf_ssl_proxy_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

