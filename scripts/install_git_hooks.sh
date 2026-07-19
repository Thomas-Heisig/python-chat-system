#!/usr/bin/env sh

set -eu

git config core.hooksPath .githooks
echo "Git hooks activated: core.hooksPath=.githooks"
