FROM phusion/baseimage:0.10.1
MAINTAINER dmantis

RUN apt-get update && apt-get upgrade -q -y && \
    apt-get install -y python3 python3-pip redis-server redis-tools && \
    apt-get install -y mongodb libffi-dev libssl-dev python3 python3-dev

RUN pip3 install pyyaml pymongo redis requests bitshares
RUN mkdir /opt/gateway_watcher

# mongodb data dir
RUN mkdir -p /data/db

COPY . /opt/gateway_watcher

WORKDIR /opt/gateway_watcher

EXPOSE 27018:27017

ENTRYPOINT ["/opt/gateway_watcher/entry.sh"]