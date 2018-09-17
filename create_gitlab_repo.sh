#!/bin/bash

TOKEN='!!!!!!!!!!!!!!!!!!!!!!!11PUT YOUR GITLAB TOKEN HERE!!!!!!!!!!!!!!!'
PLUGIN_DIR='infrared-plugins'

function print_output {
echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++
echo $1
echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++
}

function cleanup {
	print_output "Cleaning up things before execution"
	if [ -d "$PLUGIN_DIR" ]; then
		rm -rfv "$PLUGIN_DIR"
	fi
	mkdir "$PLUGIN_DIR"
}

function clone_master {
	print_output "Cloning master. Plugin name $1"
	pushd $PLUGIN_DIR
	rm -rfv $1
	git clone https://github.com/redhat-openstack/infrared.git $1
	popd
}

function filter_plugin {
	print_output "Filtering plugin $1"
	pushd $PLUGIN_DIR/$1
	git filter-branch --prune-empty --subdirectory-filter plugins/$1
	popd
}

function create_plugin_files {
	pushd $PLUGIN_DIR
	print_output "Creating plugin files $1"
	module_name=${1/-/_}
	mv $1 tmp_$module_name
	mkdir $1
	mv tmp_$module_name $1/$module_name
	mv $1/$module_name/.git $1/.git
        print_output "Creating setup.py $1"
        cat <<EOM> $1/setup.py
import os
from setuptools import setup, find_packages

setup(
    include_package_data=True,
    setup_requires=['pbr'],
    pbr=True
    )
EOM

        print_output "Creating setup.cfg $1"
        cat <<EOM> $1/setup.cfg
[metadata]
name = infrared-$1
summary = $1 plugin for InfraRed
description-file =
    README.rst
author = Red Hat OpenStack Infrastructure Team
author-email = rhos-infrared-dev@redhat.com 
home-page = https://gitlab.cee.redhat.com/ovorobio/infrared-$1/
classifier =
  License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
  Development Status :: 5 - Production/Stable
  Intended Audience :: Developers
  Intended Audience :: System Administrators
  Intended Audience :: Information Technology
  Topic :: Software Development :: Testing
  Topic :: Utilities

[files]
packages = 
    $module_name

[entry_points]
infrared.plugins=
        $1=$module_name:$module_name
EOM

        print_output "Creating MANIFEST.in $1"
        cat <<EOM> $1/MANIFEST.in
global-include *.yml *.j2 *.spec *.py *.rst
include requirements*.txt
EOM
        print_output "Creating __init__.py $1"
        cat <<EOM> $1/$module_name/__init__.py
import os
import infrared

class $module_name:

     def __init__(self):
         print "$1 plugin"
EOM
	echo $1 > $1/README.rst
	popd
}

function remove_gitlab_repo {
	print_output "Removing old gitlab project $1"
	curl --header "PRIVATE-TOKEN: ${TOKEN}" -X DELETE "https://gitlab.cee.redhat.com/api/v3/projects/ovorobio%2F$1"; echo
}

function create_gitlab_repo {
	print_output "Create new github repo $1"
	repo_id='null'
	while [ "$repo_id" == "null" ]; do 
	  repo_id=$(curl --header "PRIVATE-TOKEN: ${TOKEN}" -X POST "https://gitlab.cee.redhat.com/api/v3/projects?name=${1}&public=true&issues_enabled=true"|jq '.id')
	  if [ "$repo_id" == "null" ]
	  then
	    sleep 15
          fi
	done
}

function push_plugin {
	print_output "Add files and create a repo"
	pushd $PLUGIN_DIR/$1
	git remote set-url origin git@gitlab.cee.redhat.com:ovorobio/${1}.git
	git fetch
	git add .
	git commit -m "Initial commit to the separated repo"
	git push -u origin master
	popd
}

function create_git_tag {
	print_output "Creating tag with version"
	pushd $PLUGIN_DIR/$1
	git tag $TAG
	popd
}

function upload_to_pypi {
	print_output "Uploading $i to pypi"
	pushd $PLUGIN_DIR/$1
	rm -rfv  dist/
	python setup.py bdist_wheel
	twine upload dist/*
	popd
}

while [ "$1" != "" ]; do
	PARAM=`echo $1 | awk -F= '{print $1}'`
	VALUE=`echo $1 | awk -F= '{print $2}'`
	case $PARAM in
		--file)
		    	FILE=$VALUE
			;;
		--tag)
			TAG=$VALUE
			;;
		*)
			;;
	esac
	shift
done

cleanup

for i in $(cat $FILE); do
	clone_master $i
	filter_plugin $i
	create_plugin_files $i
	remove_gitlab_repo $i
	create_gitlab_repo $i
	push_plugin $i
	create_git_tag $i
	#upload_to_pypi $i
done
