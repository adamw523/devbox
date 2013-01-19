#!/bin/sh

nohup node server.js -w /vagrant -a x-www-browser -l 0.0.0.0 /vagrant > output.log 2> output.log < /dev/null &
sleep 2
