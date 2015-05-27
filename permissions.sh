#!/bin/bash
if [ -z "$1" ]; then
  export EDITOR=$0 && sudo -E visudo
else
  echo "thunder ALL=NOPASSWD: /sbin/halt, /sbin/reboot, /sbin/poweroff" >> $1
fi
