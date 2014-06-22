import ConfigParser
import docker_utils
import fabtools
import glob
import re

from datetime import datetime
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm

def _editor_cloud9_docker_vars():
    return {
        'image': 'adamw523/editor_cloud9',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/editor_cloud9_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_c9_port': 3131,
        'proxy_url': 'http://%s:3128' % (docker_utils.bridge_ip())
    }

def _private_editor_cloud9_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/editor_cloud9.cfg'])
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

def _require_editor_cloud9_dirs():
    docker_vars = _editor_cloud9_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def editor_cloud9_build():
    """
    Build the Editor image
    """
    _require_editor_cloud9_dirs()
    docker_vars = _editor_cloud9_docker_vars()
    config_vars = _private_editor_cloud9_config()
    config_vars_dict = dict(config_vars.items('editor'))
    work_dir = docker_vars['work_dir']
    template_vars = dict(docker_vars.items() + config_vars_dict.items())

    # Dockerfile
    upload_template('editor_cloud9/Dockerfile', work_dir, template_vars)
    upload_template('editor_cloud9/my_init.sh', work_dir, template_vars)
    upload_template('editor_cloud9/run_cloud9.sh', work_dir, template_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run_cmds = ['docker build',
                '-t %(image)s .']
        run(' '.join(run_cmds) % docker_vars)

def editor_cloud9_run():
    """
    Run the Editor docker container from the image
    """
    _require_editor_cloud9_dirs()
    docker_vars = _editor_cloud9_docker_vars()

    # run the container
    port_options = ['-p %(public_c9_port)s:3131 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d --volumes-from devshare_host '
    run_cmd = run_cmd + port_options_str + ' -t %(image)s '
    run_cmd = run_cmd % docker_vars

    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/editor_cloud9_container' %
            (run_cmd, env.user))

def editor_cloud9_start():
    """
    Start the previously run Editor docker container
    """
    _require_editor_cloud9_dirs()
    docker_vars = _editor_cloud9_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/editor_cloud9_container`' %
            env.user)

def editor_cloud9_stop():
    """
    Stop the Editor docker container
    """
    _require_editor_cloud9_dirs()
    docker_vars = _editor_cloud9_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/editor_cloud9_container`' % env.user)

def editor_cloud9():
    """
    Set the environment to the Editor container
    """
    docker_vars = _editor_cloud9_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def editor_cloud9_ssh_command():
    """
    Print out a command line to ssh to Editor container
    """
    docker_vars = _editor_cloud9_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

