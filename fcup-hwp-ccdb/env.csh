set sourced=($_)
set d=`/usr/bin/readlink -f $sourced[2]`
set d=`/usr/bin/dirname $d`
setenv PYTHONPATH ${d}:${PYTHONPATH}
setenv PATH ${d}:${PATH}
