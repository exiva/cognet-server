#!/usr/local/bin/bash
pushd .
rm -f *.pyc *~
cd ..
tar --exclude='package-cognetd.sh*' --exclude=config.py --exclude='*~' --exclude=CVS -zcf cognetd2-`date '+%Y%m%d'`.tar.gz cognetd2
popd
