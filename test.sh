#!/bin/bash

set -e

flake8

python -m unittest discover tests

