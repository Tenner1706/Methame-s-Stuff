#!/bin/bash

read -p "This will restart your PC in the end, proceed? [Y/N] " ans
case "$ans" in
    [Yy]*) ;;
    *) echo "Aborted."; exit 1 ;;
esac

paru -S --needed python-evdev python-selenium chromedriver wl-clipboard
sudo usermod -aG input "$USER"

reboot
