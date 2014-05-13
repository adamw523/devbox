import ConfigParser
import fabtools
import re

from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template

def _sf_server_docker_vars():
    return {
        'image': 'adamw523/seafile_server',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/seafile_server_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ssh_port': 8022,
        'public_http_port': 8082,
        'public_ccnet_port': 10001,
        'public_data_port': 12001,
        'public_https_port': 8443,
        'seafile_version': '3.0.3',
        'seafile_arch': 'x86-64'
    }

def _private_sf_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/seafile_server.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

def sf_build_self_signed_cert():
    config_vars = _private_oc_config()
    local("mkdir -p private/seafile")
    local("openssl genrsa -des3 -passout pass:x -out private/seafile/server.pass.key 2048")
    local("openssl rsa -passin pass:x -in private/seafile/server.pass.key -out private/seafile/server.key")
    local("rm private/seafile/server.pass.key")
    # Create the CSR
    subj = "\"/C=%(country)s/ST=%(state)s/L=%(locality)s/O=%(org_name)s/CN=%(server_address)s\"" % dict(config_vars.items('seafile'))
    local("openssl req -new -key private/seafile/server.key -out private/seafile/server.csr -subj %(subj)s" % {'subj': subj})

    # Sign the CSR
    local("openssl x509 -req -days 365 -in private/seafile/server.csr -signkey private/seafile/server.key -out private/seafile/server.crt")


#----------------------------
# Inside Seafile Server container
#----------------------------

def sf_configure():
    """Starts the configuration of Seafile. Run through this step manually"""

    docker_vars = _sf_server_docker_vars()
    with cd('/seafile/seafile-server-%(seafile_version)s' % docker_vars):
        run('./setup-seafile.sh')


#----------------------------
# On Docker host
#----------------------------

def _require_server_dirs():
    docker_vars = _sf_server_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def sf_server_build():
    """
    Build the Seafile Server image
    """
    _require_server_dirs()
    docker_vars = _sf_server_docker_vars()
    work_dir = docker_vars['work_dir']

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('seafile_server/supervisord.conf', work_dir)

    # Dockerfile
    upload_template('seafile_server/Dockerfile', work_dir + '/', docker_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def sf_server_run():
    """
    Run the Seafile Server docker container from the image
    """
    _require_server_dirs()
    docker_vars = _sf_server_docker_vars()

    # run the container
    port_options = ['-p %(public_ssh_port)s:22 ' % docker_vars,
                '-p %(public_http_port)s:8082 ' % docker_vars,
                '-p %(public_ccnet_port)s:10001 ' % docker_vars,
                '-p %(public_data_port)s:12001 ' % docker_vars
            ]

    port_options_str = ' '.join(port_options)
    run_cmd = 'docker run -i -d ' + port_options_str + ' %(image)s ' % docker_vars
    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/seafile_server_container' %
            (run_cmd, env.user))

def sf_server_start():
    """
    Start the previously run Seafile Server docker container
    """
    _require_server_dirs()
    docker_vars = _oc_server_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/seafile_server_container`' %
            env.user)

def sf_server_stop():
    """
    Stop the Seafile Server docker container
    """
    _require_server_dirs()
    docker_vars = _sf_server_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/seafile_server_container`' % env.user)

def sf_server():
    """
    Set the environment to the Seafile Server container
    """
    docker_vars = _sf_server_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def sf_server_ssh_command():
    """
    Print out a command line to ssh to Seafile Server container
    """
    docker_vars = _sf_server_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

