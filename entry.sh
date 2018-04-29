#!/usr/bin/env bash

redis-server &
mongod --fork --logpath /var/log/mongod.log
python3 app.py