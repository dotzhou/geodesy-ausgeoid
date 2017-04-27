#!/usr/bin/bash

export ssss=$1

echo $ssss

export doy=$2

echo $doy

cd /home/ted/BNC/archive/2017/${doy}

echo $PWD

uncompress ${ssss}*.Z

mkdir /tmp/${ssss}

for i in ${ssss}*d; do crx2rnx $i; done

teqc -R26 ${ssss}*o > /tmp/${ssss}/${ssss}${doy}0.17o

rm ${ssss}*o

compress ${ssss}*d

ln -s /tmp/brdc${doy}0.17g  /tmp/${ssss}/${ssss}${doy}0.17g
ln -s /tmp/brdc${doy}0.17n  /tmp/${ssss}/${ssss}${doy}0.17n

cd /tmp/${ssss}

teqc +G -R -E -C -R26 +qc -plot  ${ssss}${doy}0.17o &

cd /home/ted/BNC/archive/2017/${doy}

