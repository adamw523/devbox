import ConfigParser
import fabtools
import re

from fabric.api import abort, env, get, prompt, put, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template

def _aerofs_docker_vars():
    return {
        'image': 'adamw523/aerofs',
        'tag': 'latest',
        'work_dir': '/home/deploy/docker/aerofs_work/',
        'public_ssh_port': 7022
    }

#----------------------------
# Inside AeroFS container
#----------------------------

def _runbg(cmd, sockname="dtach"):
    return run('dtach -n `mktemp -u /tmp/%s.XXXX` %s'  % (sockname,cmd))

def aerofs_install():
    fabtools.require.deb.packages(['openjdk-7-jre', 'openjdk-7-jdk', 'default-jre', 
                                    'sharutils', 'dtach'])

    # install aerofs
    run('wget --no-check-certificate http://dsy5cjk52fz4a.cloudfront.net/aerofs-installer.deb')
    run('dpkg -i aerofs-installer.deb')

def aerofs_run_once():
    run('aerofs-cli')

def aerofs_runbg():
    _runbg('aerofs-cli')

#----------------------------
# On Docker host
#----------------------------

def aerofs_build():
    """
    Build the AeroFS docker image
    """
    docker_vars = _aerofs_docker_vars()
    work_dir = docker_vars['work_dir']

    fabtools.require.files.directories([work_dir])

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('aerofs/supervisord.conf', work_dir)

    # Dockerfile
    put('aerofs/Dockerfile', work_dir)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        
        run('docker build -t %(image)s .' % docker_vars)

def aerofs_run():
    """
    Run the AeroFS docker container from the image
    """
    docker_vars = _aerofs_docker_vars()

    # allow SSH traffic to AeroFS container
    sudo('ufw allow %(public_ssh_port)s' % docker_vars)

    # run the container
    run_cmd = 'docker run -d -privileged -p %(public_ssh_port)s:22 %(image)s ' % docker_vars
    run('ID=$(%s) && echo $ID > /home/deploy/docker/ids/aerofs_container' % run_cmd)

def aerofs_start():
    """
    Start the previously run AeroFS docker container
    """
    docker_vars = _aerofs_docker_vars()

    # start the container
    run('docker start `cat /home/deploy/docker/ids/aerofs_container`')

def aerofs_stop():
    """
    Stop the AeroFS docker container
    """
    docker_vars = _aerofs_docker_vars()

    # kill the container
    run('docker stop `cat /home/deploy/docker/ids/aerofs_container`')

def aerofs():
    """
    Set the environment to the AeroFS container
    """
    docker_vars = _aerofs_docker_vars()

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def aerofs_ssh_command():
    """
    Print out a command line to ssh to AeroFS container
    """
    docker_vars = _aerofs_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

