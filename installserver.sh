#!/bin/bash 

expected_args=1
if [ $# -ne $expected_args ]
then
	echo "syntax : install.sh <install absolute path>"
	exit 1
else
    echo "installing"
    rsync -a ./mysite $1/
    sed "s,%%templatedir%%,$1,g; s,%%dbfile%%,$1,g; s,%%staticpath%%,$1,g;" ./mysite/settings.py > $1/mysite/settings.py
    sed "s,%%webroot%%,$1,g" ./wsgi_handler.py > $1/wsgi_handler.py
fi

