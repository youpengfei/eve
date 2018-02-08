#!/usr/bin/env bash

source eve-env/bin/activate


gunicorn application:app -p eve.pid -b 0.0.0.0:8000 -D