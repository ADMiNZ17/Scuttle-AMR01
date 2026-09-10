#!/bin/bash

echo "Setting up scuttle required udev rules"
cp udev/* /etc/udev/rules.d/
udevadm control --reload-rules && udevadm trigger

