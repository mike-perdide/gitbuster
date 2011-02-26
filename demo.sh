#!/bin/sh

# This script will try and run a demo of a project, here gitbuster.
# It will try not to mess with your installed system thanks to virtualenv.
# It requires internet access, the first time at least.
# This script is quite ugly, I know. (C) Feth Arezki feth>at<tuttu.info 2011
# Licence? GPLv3 for a start: http://www.gnu.org/licenses/gpl.html

# # Customization

#Command to fetch project
fetchcmd="git clone https://github.com/mike-perdide/gitbuster.git"
#Command to build project. Escape variables.
buildcmd="make -C gitbuster/gitbuster/"
#Command to run project. Escape variables.
runcmd="PYTHONPATH=\$mydir/gitbuster/ \$mydir/bin/python gitbuster/gitbuster/gitbuster"
#Pypi deps for the project
pypideps=gitpython

# # end of customization


# # This script's dependencies

missing=0

#virtualenv for the sandbox
if [ x`which virtualenv` = "x" ] ; then
    missing=1
    echo "Missing virtualenv. On debian and ubuntu, look for a package named 'python-virtualenv'"
fi
#git for fetching and using gitbuster
if [ x`which git` = "x" ] ; then
    missing=1
    echo "Missing git. On most systems, look for a package named 'git'"
fi
#make for pypi
if [ x`which make` = "x" ] ; then
    missing=1
    echo "Missing make. On most systems, look for a package named 'make'"
fi
#gcc for pypi
if [ x`which gcc` = "x" ] ; then
    missing=1
    echo "Missing gcc. On most systems, look for a package named 'gcc'"
fi
#pyuic4 for gitbuster
if [ x`which pyuic4` = "x" ] ; then
    missing=1
    echo "Missing pyuic4. On debian/ubuntu systems, look for a package named 'pyqt4-dev-tools'"
fi

if [ $missing = 1 ] ; then
    exit 1
fi

# # End of this script's dependencies

set -e

mydir=`mktemp -d`
echo "Working in $mydir"

gc(){
echo "Deactivating virtualenv"
deactivate 2> /dev/null
echo "Now you can"
echo " * [Dd] delete $mydir and forget about this project"
echo " * [Kk] keep $mydir, maybe copy it into a more persistent place. There will be a launcher script in it for your convenience"
read -p "Choice? (defaults to 'keep')>" answer
case "$answer" in
    d | D)
        rm -fr $mydir
        echo "$mydir cleaned"
    ;;
    *)
        echo "Keeping $mydir"
        launcher=$mydir/launcher.sh
        cat > $launcher << EOF
#!/bin/bash
mydir=\`dirname \$0\`
cd \$mydir
source \$mydir/bin/activate
eval $runcmd
deactivate 2> /dev/null
EOF
        chmod +x $launcher
        echo "A script named $launcher was created for your convenience. It will help you start gitbuster"
    ;;
esac
exit
}

checkcmd(){
if [ "$?" != 0 ] ; then
    echo "Command returned non 0 status: $?: $cmd."
    gc
fi
}

runandcheck(){
    echo $1
    eval $2
    checkcmd
}

trap gc EXIT

depslog=$mydir/deps.log
fetchlog=$mydir/fetch.log
buildlog=$mydir/build.log

runandcheck "Invoking virtualenv on $mydir" "virtualenv $mydir > /dev/null"
runandcheck "Moving to $mydir" "cd $mydir"
runandcheck "Activating virtualenv" ". ./bin/activate > /dev/null"
runandcheck "Fetching Pipy deps. Logs in $depslog" "easy_install $pypideps > $depslog"
runandcheck "Fetching project. Logs in $fetchlog" "$fetchcmd > $fetchlog"
runandcheck "Building project. Logs in $buildlog" "$buildcmd > $buildlog"
runandcheck "Starting gitbuster" "$runcmd"

