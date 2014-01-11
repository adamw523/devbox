import ConfigParser
import re

from fabric.api import abort, env, get, prompt, run, sudo
from fabric.context_managers import cd, remote_tunnel
from fabric.contrib.files import append, exists, sed, upload_template

#---------------------------
# OpenVPN
#---------------------------

VALID_STATIC_OCTETS = [ [  1,  2], [  5,  6], [  9, 10], [ 13, 14], [ 17, 18],
                        [ 21, 22], [ 25, 26], [ 29, 30], [ 33, 34], [ 37, 38],
                        [ 41, 42], [ 45, 46], [ 49, 50], [ 53, 54], [ 57, 58],
                        [ 61, 62], [ 65, 66], [ 69, 70], [ 73, 74], [ 77, 78],
                        [ 81, 82], [ 85, 86], [ 89, 90], [ 93, 94], [ 97, 98],
                        [101,102], [105,106], [109,110], [113,114], [117,118],
                        [121,122], [125,126], [129,130], [133,134], [137,138],
                        [141,142], [145,146], [149,150], [153,154], [157,158],
                        [161,162], [165,166], [169,170], [173,174], [177,178],
                        [181,182], [185,186], [189,190], [193,194], [197,198],
                        [201,202], [205,206], [209,210], [213,214], [217,218],
                        [221,222], [225,226], [229,230], [233,234], [237,238],
                        [241,242], [245,246], [249,250], [253,254]]

def openvpn_initialize():
    """
    Install OpenVPN on server
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()

    # cannot create tun in docker build yet - https://github.com/dotcloud/docker/issues/2191
    if not exists('/dev/net/tun'):
        run('mkdir /dev/net')
        run('mknod /dev/net/tun c 10 200')

    # install if easy-rsa hasn't been copied over and used yet
    if not exists('/root/easy-rsa/vars'):
        # use openvpns easy-rsa to create keys and configure openvpn
        run('mkdir -p /root/easy-rsa/')

        # copy over easy-rsa tools from oepnvpn examples
        run('cp -r /usr/share/doc/openvpn/examples/easy-rsa/2.0/* /root/easy-rsa/')
        # sudo('chown -R openvpn:openvpn ~openvpn/easy-rsa')
        sed('/root/easy-rsa/whichopensslcnf', 'openssl.cnf', 'openssl-1.0.0.cnf')

        # copy over server.conf file
        upload_template('openvpn/configs/openvpn_server.conf', '/etc/openvpn/server.conf', openvpn_vars)

        # coy over our variables
        upload_template('openvpn/configs/openvpn_vars.sh', '/root/easy-rsa/vars', openvpn_vars)

        with cd('/root/easy-rsa'):
            # create keys
            run('source ./vars; ./clean-all; ./build-dh; ./pkitool --initca; ./pkitool --server server')

            with cd('keys'):
                # genreate the ta key and copy them into /etc/openvpn
                run('openvpn --genkey --secret ta.key')
                run('cp server.crt server.key ca.crt dh1024.pem ta.key /etc/openvpn/')
                run('chmod 400 /etc/openvpn/ta.key')

        # sudo('service openvpn start')

    # open up the firewall
    # sudo('ufw allow 1194/udp')
    # sudo('ufw allow 1194/tcp')
    # sudo('ufw allow from %s/24' % (openvpn_vars['network']))


    # openvpn --cd /etc/openvpn/ --config /etc/openvpn/server.conf --verb 3 

def openvpn_build():
    """
    Build the OpenVPN docker image
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()

    work_dir = docker_vars['work_dir']

    # OpenVPN configuration
    fabtools.require.files.directories([work_dir])
    upload_template('openvpn/configs/openvpn_server.conf', work_dir + 'server.conf', openvpn_vars)

    # SSH configuration
    put ('private/ssh/id_rsa_devbox.pub', work_dir + '/id_rsa.pub')

    # Supervisor
    put('openvpn/supervisord.conf', work_dir)

    # Dockerfile
    put('openvpn/Dockerfile', work_dir)

    # build
    with cd(work_dir):
        # <username / private repo address>/repo_name>:tag
        run('docker build -t %(image)s .' % docker_vars)

def openvpn_run():
    """
    Run the OpenVPN docker container
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()

    # allow SSH traffic to OpenVPN container
    sudo('ufw allow %(public_ssh_port)s' % docker_vars)

    # run the container
    run_cmd = 'docker run -d -privileged -p %(public_ssh_port)s:22 -p 1194:1194/udp -p 443:443 %(image)s ' % docker_vars
    run('ID=$(%s) && echo $ID > /home/deploy/docker/ids/openvpn_container' % run_cmd)

def openvpn_start():
    """
    Start the OpenVPN docker container
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()
        
    # allow SSH traffic to OpenVPN container
    sudo('ufw allow %(public_ssh_port)s' % docker_vars)

    # start the container
    run('docker start `cat /home/deploy/docker/ids/openvpn_container`')

def openvpn_stop():
    """
    Stop the OpenVPN docker container
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()
        
    # stop allowing SSH traffic to OpenVPN container
    sudo('ufw delete allow %(public_ssh_port)s' % docker_vars)

    # kill the container
    run('docker stop `cat /home/deploy/docker/ids/openvpn_container`')

def openvpn():
    """
    Set the environment to the OpenVPN container
    """
    openvpn_vars = _openvpn_config_vars()
    docker_vars = _openvpn_docker_vars()
    # container = _docker_container_id(docker_vars['image'], docker_vars['tag'])

    env.user = 'root'
    env.port = docker_vars['public_ssh_port']
    env.key_filename = 'private/ssh/id_rsa_devbox'

def openvpn_ssh_command():
    """
    Print out a command line to ssh to OpenVPN container
    """
    docker_vars = _openvpn_docker_vars()
    print "ssh -p %s -i private/ssh/id_rsa_devbox root@%s" % (docker_vars['public_ssh_port'], env.host)

def openvpn_create_client():
    """
    Create client keys on server
    """
    hostname = prompt("Host name of the client:")

    # abort if client has been created already
    if exists('/root/easy-rsa/keys/%s.crt' % (hostname), use_sudo=True):
        abort('Certificate for client already exists')

    # creeate client keys
    with cd('/root/easy-rsa/'):
        run('source vars; ./build-key %s' % hostname)

def openvpn_assign_static_ip():
    """
    Assign static IP address for a client
    """
    config = _openvpn_config()

    network = config.get('openvpn', 'network')
    network_pref = re.sub(r'(.*\.)(.+)\b', r'\1', network)
    network_prompt = network_pref + 'x'

    hostname = prompt("Host name of the client:")

    print "Valid IP endings:",
    print ",".join([str(v[0]) for v in VALID_STATIC_OCTETS])
    octet = prompt("Choose an ending octet from the above list (%s) :" % (network_prompt))

    if not exists('/etc/openvpn/ccd'):
        run('mkdir /etc/openvpn/ccd')

    template_vars = {'network_pref': network_pref, 'oct1': octet, 'oct2': str(int(octet) + 1)}
    upload_template('devbox_openvpn/configs/ccd_template', '/etc/openvpn/ccd/%s' % (hostname), template_vars)

def openvpn_download_visc():
    """
    Download OpenVPN configuration files for Viscosity
    """
    hostname = prompt("Host name of the client:")

    if not exists('/root/easy-rsa/keys/%s.crt' % (hostname)):
        abort('Create client keys first with: openvpn_create_client')

    # set up a new directory to create our .visc configruation
    tmp_dir = '/tmp/%s' % (hostname + '.visc')
    if exists(tmp_dir):
        run('rm -fR %s' % (tmp_dir))

    # vars for the configuration file
    client_conf = {
        "visc_name": hostname,
        "server": env.hosts[0]
    }

    # make tmp directory, copy required items into it
    run('mkdir %s' % (tmp_dir))
    run('cp /etc/openvpn/ca.crt %s/ca.crt' % (tmp_dir))
    run('cp /root/easy-rsa/keys/%s.crt %s/cert.crt' % (hostname, tmp_dir))
    run('cp /root/easy-rsa/keys/%s.key %s/key.key' % (hostname, tmp_dir))
    run('cp /etc/openvpn/ta.key %s/ta.key' % (tmp_dir))
    upload_template('devbox_openvpn/configs/client.visc/config.conf', '%s/config.conf' % (tmp_dir), client_conf)
    run('chmod -R a+r %s' % (tmp_dir))

    # download .vsic directory and then delete it from server
    get(tmp_dir, '.')
    run('rm -fR %s' % (tmp_dir))

def openvpn_download_ovpn():
    """
    Download OpenVPN configuration files for OpenVPN
    """
    hostname = prompt("Host name of the client:")

    if not exists('/root/easy-rsa/keys/%s.crt' % (hostname)):
        abort('Create client keys first with: openvpn_create_client')

    # set up a new directory to create our .visc configruation
    tmp_dir = '/tmp/%s' % (hostname + '')
    if exists(tmp_dir):
        run('rm -fR %s' % (tmp_dir))

    # vars for the configuration file
    client_conf = {
        "visc_name": hostname,
        "server": env.hosts[0]
    }

    # make tmp directory, copy required items into it
    run('mkdir %s' % (tmp_dir))
    run('cp /etc/openvpn/ca.crt %s/ca.crt' % (tmp_dir))
    run('cp /root/easy-rsa/keys/%s.crt %s/cert.crt' % (hostname, tmp_dir))
    run('cp /root/easy-rsa/keys/%s.key %s/key.key' % (hostname, tmp_dir))
    run('cp /etc/openvpn/ta.key %s/ta.key' % (tmp_dir))
    upload_template('devbox_openvpn/configs/client.ovpn', '%s/config.ovpn' % (tmp_dir), client_conf)
    run('chmod -R a+r %s' % (tmp_dir))

    # zip up the directory
    with cd('/tmp/'):
        run('zip -r %s.zip %s' % (hostname, hostname))

    # download .vsic directory and then delete it from server
    get('/tmp/%s.zip' % (hostname))
    run('rm -fR %s' % (tmp_dir))
    run('rm /tmp/%s.zip' % (hostname))

def _openvpn_docker_vars():
    return {
        'image': 'adamw523/openvpn',
        'tag': 'latest',
        'public_ssh_port': 6022,
        'work_dir': '/home/deploy/docker/openvpn_work/',
        'openvpn_etc_dir': '/home/deploy/docker/openvpn_volumes/etc_openvpn/'
    }

def _openvpn_config():
    config = ConfigParser.ConfigParser()
    config.read(['private/openvpn.cfg'])
    return config

def _openvpn_config_vars():
    config = _openvpn_config()

    openvpn_vars = {
        "KEY_COUNTRY": config.get('openvpn', 'KEY_COUNTRY'),
        "KEY_PROVINCE": config.get('openvpn', 'KEY_PROVINCE'),
        "KEY_CITY": config.get('openvpn', 'KEY_CITY'),
        "KEY_ORG": config.get('openvpn', 'KEY_ORG'),
        "KEY_EMAIL": config.get('openvpn', 'KEY_EMAIL'),
        "KEY_CN": config.get('openvpn', 'KEY_CN'),
        "KEY_NAME": config.get('openvpn', 'KEY_NAME'),
        "KEY_OU": config.get('openvpn', 'KEY_OU'),
        "network": config.get('openvpn', 'network')
    }

    return openvpn_vars