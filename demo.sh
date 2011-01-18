#!/bin/bash

# This script will try and run a demo of a project, here qGitFilterBranch.
# It will try not to mess with your installed system thanks to virtualenv.
# It requires internet access, the first time at least.
# This script is quite ugly, I know. (C) Feth Arezki feth>at<tuttu.info 2011
# Licence? GPLv3 for a start: http://www.gnu.org/licenses/gpl.html

# # Customization

#Command to fetch project
fetchcmd="git clone https://github.com/mike-perdide/qGitFilterBranch.git"
#Command to build project. Escape variables.
buildcmd="make -C qGitFilterBranch/qGitFilterBranch/"
#Command to run project. Escape variables.
runcmd="PYTHONPATH=\$mydir/qGitFilterBranch/ \$mydir/bin/python qGitFilterBranch/qGitFilterBranch/run.py"
#Pypi deps for the project
pypideps=gitpython

# # end of customization


# # This script's dependencies
missing=0

if [ x`which virtualenv` == "x" ] ; then
    missing=1
    echo "Missing virtualenv. On debian and ubuntu, look for a package named 'python-virtualenv'"
fi
if [ x`which git` == "x" ] ; then
    missing=1
    echo "Missing git. On most systems, look for a package named 'git'"
fi

if [ $missing == 1 ] ; then
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
read -p "Choice? (defaults to 'keep')>" -i "K" answer
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
        echo "A script named $launcher was created for your convenience. It will help you start qGitFilterBranch"
    ;;
esac
}

err(){
echo "Command returned non 0 status: $?: $cmd."
gc
}

trap err ERR
trap gc EXIT

echo "Invoking virtualenv on $mydir"
cmd="virtualenv $mydir > /dev/null"
eval $cmd
cd $mydir
echo "Activating virtualenv"
cmd="source ./bin/activate > /dev/null"
eval $cmd
depslog=$mydir/deps.log
echo "Fetching Pipy deps. Logs in $depslog"
cmd="easy_install $pypideps > $depslog"
eval $cmd
fetchlog=$mydir/fetch.log
echo "Fetching project. Logs in $fetchlog"
cmd="$fetchcmd > $fetchlog"
eval $cmd
buildlog=$mydir/build.log
echo "Building project. Logs in $buildlog"
cmd="$buildcmd > $buildlog"
eval $cmd
cmd=$runcmd
eval $cmd

