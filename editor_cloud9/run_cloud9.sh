#!/bin/sh
export HOME=/home/%(user)s
export NVM_DIR=/home/%(user)s/.nvm
. /home/%(user)s/.nvm/nvm.sh
nvm use 0.8
node /home/%(user)s/cloud9/server.js -l 0.0.0.0 -w %(directory)s
