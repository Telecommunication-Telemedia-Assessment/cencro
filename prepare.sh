#!/bin/bash
git submodule init && git submodule update

cd vmaf
make -j 12


