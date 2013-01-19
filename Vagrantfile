Vagrant::Config.run do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  # config.vm.box = "precise"

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  # config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  # Boot with a GUI so you can see the screen. (Default is headless)
  # config.vm.boot_mode = :gui

  # Assign this VM to a host-only network IP, allowing you to access it
  # via the IP. Host-only networks can talk to the host machine as well as
  # any other machines on the same network, but cannot be accessed (through this
  # network interface) by any external networks.
  # config.vm.network :hostonly, "192.168.33.10"

  # Assign this VM to a bridged network, allowing you to connect directly to a
  # network using the host's network device. This makes the VM appear as another
  # physical device on your network.
  # config.vm.network :bridged

  # Forward a port from the guest to the host, which allows for outside
  # computers to access the VM, whereas host only networking does not.
  # config.vm.forward_port 3000, 8030
  # config.vm.forward_port 5432, 4432

  # Share an additional folder to the guest VM. The first argument is
  # an identifier, the second is the path on the guest to mount the
  # folder, and the third is the path on the host to the actual folder.
  # config.vm.share_folder "v-data", "/vagrant_data", "../data"
  # config.vm.share_folder "backup_data", "/vagrant_backup_data", "backup_data", :extra => 'dmode=777'

  config.vm.define :devbox do |devbox|
    devbox.vm.box = "quantal32"
    devbox.vm.network :bridged
    #devbox.vm.box_url = "https://github.com/downloads/roderik/VagrantQuantal64Box/quantal64.box"
    devbox.vm.share_folder "data", "/data", "/Users/adam/work_local/devbox"
    devbox.vm.customize ["modifyvm", :id,
                           "--cpus", 4]
    devbox.ssh.forward_x11 = true
    devbox.vm.forward_port 3131, 3131
    devbox.vm.forward_port 8888, 8888
  end

end
