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

def _ipython_docker_vars():
    return {
        'image': 'adamw523/ipython',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/ipython_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ipython_port': 8888,
        'public_ssh_port': 8025,
        'proxy_url': 'http://%s:3128' % (bridge_ip())
    }

def _private_ipython_config():
    # get config file
    config = ConfigParser.ConfigParser()
    config.read(['private/ipython.cfg'])
    return config

#----------------------------
# Local commands
#----------------------------

#----------------------------
# Inside IPython container
#----------------------------

#----------------------------
# On Docker host
#----------------------------

def _require_ipython_dirs():
    docker_vars = _ipython_docker_vars()
    work_dir = docker_vars['work_dir']
    ids_dir = docker_vars['ids_dir']
    fabtools.require.files.directories([work_dir, ids_dir])

def ipython_build():
    """
    Build the IPython image
    """
    _require_ipython_dirs()
    docker_vars = _ipython_docker_vars()
    config_vars = _private_ipython_config()
    config_vars_dict = dict(config_vars.items('ipython'))
    work_dir = docker_vars['work_dir']
    template_vars = dict(docker_vars.items() + config_vars_dict.items())

    # SSH configuration
    put_if_changed('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')
    put_if_changed(template_vars['ssh_public_key'], work_dir + '/authorized_keys')

    # Supervisor
    upload_template('ipython/supervisord.conf', work_dir, template_vars)

    # Dockerfile
    upload_template('ipython/Dockerfile', work_dir, template_vars)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run_cmds = ['docker build',
                '-t %(image)s .']
        run(' '.join(run_cmds) % docker_vars)

def ipython_run():
    """
    Run the IPython docker container from the image
    """
    _require_ipython_dirs()
    docker_vars = _ipython_docker_vars()

    # run the container
    port_options = ['-p %(public_ssh_port)s:22 ' % docker_vars,
                    '-p %(public_ipython_port)s:8888 ' % docker_vars]
    port_options_str = ' '.join(port_options)

    run_cmd = 'docker run -i -d --volumes-from devshare_host '
    run_cmd = run_cmd + port_options_str + ' %(image)s '
    run_cmd = run_cmd % docker_vars

    run('ID=$(%s) && echo $ID > /home/%s/docker/ids/ipython_container' %
            (run_cmd, env.user))

def ipython_start():
    """
    Start the previously run IPython docker container
    """
    _require_ipython_dirs()
    docker_vars = _ipython_docker_vars()

    # start the container
    run('docker start `cat /home/%s/docker/ids/ipython_container`' %
            env.user)

def ipython_stop():
    """
    Stop the IPython docker container
    """
    _require_ipython_dirs()
    docker_vars = _ipython_docker_vars()

    # kill the container
    run('docker stop `cat /home/%s/docker/ids/ipython_container`' % env.user)

def ipython():
    """
    Set the environment to the IPython container
    """
    docker_vars = _ipython_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def ipython_ssh_command():
    """
    Print out a command line to ssh to IPython container
    """
    docker_vars = _ipython_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

