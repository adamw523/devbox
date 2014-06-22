#!/bin/bash
export HOME=/home/%(user)s
export NVM_DIR=/home/%(user)s/.nvm
. /home/%(user)s/.nvm/nvm.sh
nvm use v0.6
/home/%(user)s/cloud9/bin/cloud9.sh -l 0.0.0.0 -w %(directory)s
