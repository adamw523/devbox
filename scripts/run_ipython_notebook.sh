#!/bin/bash

# source /home/vagrant/notebookenv/bin/activate
cd /data/notebooks
# nohup ipython notebook --profile nbserver > output.log 2> output.log < /dev/null 
nohup /home/vagrant/notebookenv/bin/ipython notebook --profile nbserver &> output.log &
