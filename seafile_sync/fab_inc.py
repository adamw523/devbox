import ConfigParser
import fabtools
import glob
import re

from datetime import datetime
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm
from seafile_ssl_proxy.fab_inc import _sf_ssl_proxy_private_config

def _sf_sync_docker_vars():
    return {
        'image': 'adamw523/seafile_sync',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/seafile_sync_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ssh_port': 8024,
        'seafile_version': '3.0.3',
        'seafile_arch': 'x86-64'
    }

def _private_sf_sync_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/seafile_sync.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

#----------------------------
# Inside Seafile Sync container
#----------------------------

#----------------------------
# On Docker host
#----------------------------

def _require_sf_sync_dirs():
    docker_vars = _sf_sync_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def sf_sync_build():
    """
    Build the Seafile Sync image
    """
    _require_sf_sync_dirs()
    docker_vars = _sf_sync_docker_vars()
    config_vars = _private_sf_sync_config()
    config_vars_dict = dict(config_vars.items('seafile'))
    work_dir = docker_vars['work_dir']
    template_vars = dict(docker_vars.items() + config_vars_dict.items())

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    upload_template('seafile_sync/supervisord.conf', work_dir, template_vars)

    # Dockerfile
    upload_template('seafile_sync/Dockerfile', work_dir, template_vars)
    upload_template('seafile_sync/seafile_cli_run.sh', work_dir, config_vars_dict)
    upload_template('seafile_sync/fix_permissions.sh', work_dir, config_vars_dict)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def sf_sync_run():
    """
    Run the Seafile Sync docker container from the image
    """
    _require_sf_sync_dirs()
    docker_vars = _sf_sync_docker_vars()
    id_path = '/home/%s/docker/ids/seafile_sync_container' % (env.user)

    # remove old container if exists
    if exists(id_path):
        run('docker rm `cat %s`' % (id_path))

    # run the container
    port_options = ['-p %(public_ssh_port)s:22 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d --name devshare_host '
    run_cmd = run_cmd + port_options_str + ' %(image)s '
    run_cmd = run_cmd % docker_vars
    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/seafile_sync_container' %
            (run_cmd, env.user))

def sf_sync_start():
    """
    Start the previously run Seafile Sync docker container
    """
    _require_sf_sync_dirs()
    docker_vars = _sf_sync_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/seafile_sync_container`' %
            env.user)

def sf_sync_stop():
    """
    Stop the Seafile Sync docker container
    """
    _require_sf_sync_dirs()
    docker_vars = _sf_sync_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/seafile_sync_container`' % env.user)

def sf_sync():
    """
    Set the environment to the Seafile Sync container
    """
    docker_vars = _sf_sync_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def sf_sync_ssh_command():
    """
    Print out a command line to ssh to Seafile Sync container
    """
    docker_vars = _sf_sync_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

