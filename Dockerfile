FROM python:3.7-alpine
MAINTAINER blue1616

COPY requirements /tmp/requirements

RUN apk upgrade --no-cache && \
  apk add --no-cache build-base && \
  apk add --no-cache libxml2-dev libxslt-dev && \
  pip3 install -r /tmp/requirements && \
  apk del build-base

COPY ./monolith /opt/monolith

RUN addgroup -g 1000 monolith && \
  adduser -D -u 1000 -G monolith monolith && \
  chown -R monolith:monolith /opt/monolith && \
  chmod +x /opt/monolith/startbot.sh && \
  chmod +x /opt/monolith/startweb.sh

USER monolith
WORKDIR /opt/monolith

CMD ["/opt/monolith/startbot.sh"]
