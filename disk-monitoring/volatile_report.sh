#!/bin/bash
cd `dirname $0`
export PYTHONPATH=/group/clas12/packages/mysql-connector/8.0.17/lib
rm -f index.html cache.html
./volatile_html.py >& index.html
scp index.html clas12@jlabl5:~/clasweb/clas12offline/disk/volatile
./cache_html.py >& cache.html
scp cache.html clas12@jlabl5:~/clasweb/clas12offline/disk/cache/index.html

