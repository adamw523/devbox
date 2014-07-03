import ConfigParser
import fabtools
import glob
import re

from datetime import datetime
from docker_utils import bridge_ip
from fab_utils import put_if_changed
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm

def _icecoder_docker_vars():
    return {
        'image': 'adamw523/icecoder',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/icecoder_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_icecoder_port': 9999
    }

def _private_icecoder_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/icecoder.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

#----------------------------
# On Docker host
#----------------------------

def _require_icecoder_dirs():
    docker_vars = _icecoder_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def icecoder_build():
    """
    Build the ICEcoder image
    """
    _require_icecoder_dirs()
    docker_vars = _icecoder_docker_vars()
    config_vars = _private_icecoder_config()
    config_vars_dict = dict(config_vars.items('icecoder'))
    work_dir = docker_vars['work_dir']
    template_vars = dict(docker_vars.items() + config_vars_dict.items())

    # Dockerfile
    print template_vars
    upload_template('icecoder/Dockerfile', work_dir, template_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run_cmds = ['docker build',
                '-t %(image)s .']
        run(' '.join(run_cmds) % docker_vars)

def icecoder_run():
    """
    Run the ICEcoder docker container from the image
    """
    _require_icecoder_dirs()
    docker_vars = _icecoder_docker_vars()

    # run the container
    port_options = ['-p %(public_icecoder_port)s:80 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d --volumes-from devshare_host '
    run_cmd = run_cmd + port_options_str + ' %(image)s '
    run_cmd = run_cmd % docker_vars

    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/icecoder_container' %
            (run_cmd, env.user))

def icecoder_start():
    """
    Start the previously run ICEcoder docker container
    """
    _require_icecoder_dirs()
    docker_vars = _icecoder_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/icecoder_container`' %
            env.user)

def icecoder_stop():
    """
    Stop the ICEcoder docker container
    """
    _require_icecoder_dirs()
    docker_vars = _icecoder_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/icecoder_container`' % env.user)



