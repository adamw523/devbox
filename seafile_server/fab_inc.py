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

def _sf_server_docker_vars():
    return {
        'image': 'adamw523/seafile_server',
        'tag': 'latest',
        'work_dir': '/home/%s/docker/seafile_server_work/' % env.user,
        'ids_dir': '/home/%s/docker/ids/' % env.user,
        'public_ssh_port': 8022,
        'public_http_port': 8000,
        'public_ccnet_port': 10001,
        'public_data_port': 12001,
        'public_https_port': 8443,
        'seafile_version': '3.1.3',
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

#----------------------------
# Inside Seafile Server container
#----------------------------

def sf_server_configure():
    """Start the configuration of Seafile. Run through this step manually"""

    docker_vars = _sf_server_docker_vars()

    sf_stop()
    with cd('/seafile/seafile-server-%(seafile_version)s' % docker_vars):
        run('./setup-seafile.sh')

def sf_start():
    """Start Seafile Server"""

    docker_vars = _sf_server_docker_vars()
    run('supervisorctl start seafile')

def sf_stop():
    """Stop Seafile Server"""
    docker_vars = _sf_server_docker_vars()

    run('supervisorctl stop seafile')

def sf_server_backup():
    """Create a backup on Seafile server"""
    sf_stop()

    fabtools.require.files.directories(['/backup/data', '/backup/databases'])
    # backup databases
    run('sqlite3 /seafile/ccnet/GroupMgr/groupmgr.db .dump > /backup/databases/groupmgr.db.bak.`date +"%Y-%m-%d-%H-%M-%S"`')
    run('sqlite3 /seafile/ccnet/PeerMgr/usermgr.db .dump > /backup/databases/usermgr.db.bak.`date +"%Y-%m-%d-%H-%M-%S"`')
    run('sqlite3 /seafile/seafile-data/seafile.db .dump > /backup/databases/seafile.db.bak.`date +"%Y-%m-%d-%H-%M-%S"`')
    run('sqlite3 /seafile/seahub.db .dump > /backup/databases/seahub.db.bak.`date +"%Y-%m-%d-%H-%M-%S"`')

    # backup library data
    run('rsync -az /seafile /backup/data')

    sf_start()

def _make_old_copy(files):
    """"Copy given file or file paths with .old extension"""
    if type(files) == 'str':
        files = [files]

    for file_ in files:
        if(exists(file_)):
            run('mv %(file)s %(file)s.old' % {'file': file_})

def sf_server_restore():
    """Restore seafile from latest backup in /backup/"""
    docker_vars = _sf_server_docker_vars()

    sf_stop()

    fabtools.require.files.directories(['/backup/data', '/backup/databases'])

    # restore library data
    run('rsync -az /backup/data/seafile/* /seafile/')

    # fix permissions / executable flags
    with cd('/seafile/seafile-server-%(seafile_version)s' % docker_vars):
        run('chmod +x *.sh')
        with cd('seafile/bin'):
            run('chmod +x *')

    # add latest link
    run('ln -s /seafile/seafile-server%(seafile_version)s /seafile/seafile-server-latest' % docker_vars)

    # restore databases
    with cd('/seafile'):
        _make_old_copy(['ccnet/PeerMgr/usermgr.db', 'ccnet/GroupMgr/groupmgr.db',
                        'seafile-data/seafile.db', 'seahub.db'])

        run('sqlite3 ccnet/PeerMgr/usermgr.db < %s' % _latest_file('/backup/databases/usermgr.db.bak*'))
        run('sqlite3 ccnet/GroupMgr/groupmgr.db < %s' % _latest_file('/backup/databases/groupmgr.db.bak*'))
        run('sqlite3 seafile-data/seafile.db < %s' % _latest_file('/backup/databases/seafile.db.bak*'))
        run('sqlite3 seahub.db < %s ' % _latest_file('/backup/databases/seahub.db.bak*'))


    sf_start()

def sf_download_backup():
    """Downlaod a tgz file with the contents of /backup"""
    run('tar -czf /backup.tgz /backup')
    get('/backup.tgz', 'backups/seafile-backup.tgz')

def sf_upload_backup():
    """Uploadt the tgz backup file"""
    put('backups/seafile-backup.tgz', '/backup.tgz')
    with cd('/'):
        run('tar -xzf backup.tgz')

def sf_backup_to_s3():
    """Sync backup to S3"""
    private_config = _private_sf_config()
    print private_config.get('seafile', 'backup_bucket')
    cmd = "boto-rsync -a\"%(s3_access_key)s\" -s\"%(s3_secret_key)s\" --delete /backup s3://%(backup_bucket)s/seafile_server"
    cmd = cmd % dict(private_config.items('seafile'))
    run(cmd)

def sf_get_backup_from_s3():
    """Get backup from S3"""
    private_config = _private_sf_config()

    if exists('/backup') and not confirm('Overwrite existing /backup directory?', default=False):
        return

    cmd = "boto-rsync -a\"%(s3_access_key)s\" -s\"%(s3_secret_key)s\" --delete s3://%(backup_bucket)s/seafile_server /backup"
    cmd = cmd % dict(private_config.items('seafile'))
    run(cmd)

def _latest_file(search):
    """Returns newest file matching given search path"""
    files = (run('ls -1 %s' % search, quiet=True)).splitlines()
    date_strs = [file_[file_.rfind('.')+1:] for file_ in files]
    dates = [datetime.strptime(date_str, '%Y-%m-%d-%H-%M-%S') for date_str in date_strs]
    max_index = dates.index(max(dates))
    return files[max_index]

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
    config_vars = _sf_ssl_proxy_private_config()
    config_vars_dict = dict(config_vars.items('seafile'))
    work_dir = docker_vars['work_dir']

    # nginx/ssl configuration
    upload_template('seafile_ssl_proxy/nginx_default.conf', work_dir, config_vars_dict)
    put('private/seafile_ssl_proxy/server.key', work_dir)
    put('private/seafile_ssl_proxy/server.crt', work_dir)

    # SSH configuration
    put('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('seafile_server/supervisord.conf', work_dir)

    # Seafile
    put('seafile_server/seafile_run.sh', work_dir)

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
                '-p %(public_http_port)s:8000 ' % docker_vars,
                '-p %(public_https_port)s:8443 ' % docker_vars,
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
    docker_vars = _sf_server_docker_vars()

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

