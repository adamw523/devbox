#!/bin/sh

nohup node server.js -w ~/AeroFS/devshare -a x-www-browser -l 0.0.0.0 ~/AeroFS/devshare > output.log 2> output.log < /dev/null &
sleep 2
