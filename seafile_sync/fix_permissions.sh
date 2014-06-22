#!/bin/bash

chown -R %(user)s:%(user)s %(sync_path)s
chmod a+w -R %(sync_path)s
