#!/bin/bash

WORKDIR=$(pwd)

cd $WORKDIR
rm -rf micronucleus
git clone https://github.com/micronucleus/micronucleus.git 
cd micronucleus && git checkout 80419704f68bf0783c5de63a6a4b9d89b45235c7
cd commandline && make

cd $WORKDIR
rm -rf I2C-Tiny-USB
git clone https://github.com/harbaum/I2C-Tiny-USB.git
cd I2C-Tiny-USB/digispark && sed -i "s/#define I2C_IS_AN_OPEN_COLLECTOR_BUS/\/\/#define I2C_IS_AN_OPEN_COLLECTOR_BUS/" main.c
make hex

sudo $WORKDIR/micronucleus/commandline/micronucleus --run --dump-progress --type intel-hex main.hex
