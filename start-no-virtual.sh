#!/usr/bin/env bash

kill `cat eve.pid`
gunicorn application:app -p eve.pid -b 0.0.0.0:8000 -D