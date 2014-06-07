import ConfigParser
import fabtools
import glob
import re

from datetime import datetime
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm

def _editor_docker_vars():
    return {
        'image': 'adamw523/editor',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/editor_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ssh_port': 8025
    }

def _private_editor_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/editor.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

#----------------------------
# Inside Editor container
#----------------------------

#----------------------------
# On Docker host
#----------------------------

def _require_editor_dirs():
    docker_vars = _editor_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def editor_build():
    """
    Build the Editor image
    """
    _require_editor_dirs()
    docker_vars = _editor_docker_vars()
    config_vars = _private_editor_config()
    config_vars_dict = dict(config_vars.items('editor'))
    work_dir = docker_vars['work_dir']

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('editor/supervisord.conf', work_dir)

    # Dockerfile
    upload_template('editor/Dockerfile', work_dir, docker_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def editor_run():
    """
    Run the Editor docker container from the image
    """
    _require_editor_dirs()
    docker_vars = _editor_docker_vars()

    # run the container
    port_options = ['-p %(public_ssh_port)s:22 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d --volumes-from devshare_host '
    run_cmd = run_cmd + port_options_str + ' %(image)s '
    run_cmd = run_cmd % docker_vars

    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/editor_container' %
            (run_cmd, env.user))

def editor_start():
    """
    Start the previously run Editor docker container
    """
    _require_editor_dirs()
    docker_vars = _editor_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/editor_container`' %
            env.user)

def editor_stop():
    """
    Stop the Editor docker container
    """
    _require_editor_dirs()
    docker_vars = _editor_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/editor_container`' % env.user)

def editor():
    """
    Set the environment to the Editor container
    """
    docker_vars = _editor_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def editor_ssh_command():
    """
    Print out a command line to ssh to Editor container
    """
    docker_vars = _editor_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

