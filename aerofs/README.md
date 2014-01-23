# AeroFS client

# Usage

Build the image

<code>$ fab dodo aerofs_build</code>

Run the container

<code>$ fab dodo aerofs_run</code>

Install AeroFS (needs to be done after build because it needs to run in privileged)

<code>$ fab dodo aerofs aerofs_install</code>

Run aerofs-cli so it syncs files

<code>$ fab dodo aerofs aerofs_runbg</code>

# TODO

- new way of configuring
  - maybe build image, update image with config, then run the aerofs-cli instead of supervisord
