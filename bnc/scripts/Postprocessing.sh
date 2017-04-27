#!/usr/bin/bash

export path=$1
export uppercase=${path##*/}
export filename=`echo $uppercase | tr [:upper:] [:lower:]`
mv $1 /home/ted/BNC/convert/$filename

