import ConfigParser
import fabtools
import glob
import re

from datetime import datetime
from fabric.api import abort, env, get, local, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template
from fabric.contrib.console import confirm

def _local_proxy_docker_vars():
    return {
        'image': 'adamw523/local_proxy',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/local_roxy_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user
    }

#----------------------------
# Local commands
#----------------------------

#----------------------------
# Inside Editor container
#----------------------------

#----------------------------
# On Docker host
#----------------------------

def _require_local_proxy_dirs():
    docker_vars = _local_proxy_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def local_proxy_build():
    """
    Build the Local Proxy image
    """
    docker_vars = _local_proxy_docker_vars()
    _require_local_proxy_dirs()
    work_dir = docker_vars['work_dir']

    # Dockerfile
    upload_template('local_proxy/Dockerfile', work_dir)

    # Squid config
    put('local_proxy/squid.conf', work_dir)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def local_proxy_run():
    """
    Run the Local Proxy docker container from the image
    """
    _require_local_proxy_dirs()
    docker_vars = _local_proxy_docker_vars()

    # run the container
    port_options = ['-p 3128:3128 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d '
    run_cmd = run_cmd + port_options_str + ' %(image)s '
    run_cmd = run_cmd % docker_vars

    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/local_proxy_container' %
            (run_cmd, env.user))

def local_proxy_start():
    """
    Start the previously run container
    """
    _require_local_proxy_dirs()

    # start the container
    run('docker start `cat /home/%s/docker/ids/local_proxy_container`' %
            env.user)

def local_proxy_stop():
    """
    Stop the docker container
    """
    _require_local_proxy_dirs()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/local_proxy_container`' % env.user)
