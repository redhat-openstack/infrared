List builds
-----------

The List Builds plugin is used to list all the available puddles (builds) for the
given OSP version.

Usage::

    $ ir list-builds --version 12

This will produce output in ansible style.

Alternatively you can have a clean raw output by saving builds to the file and printing them::

    $ ir list-builds --version 12 --file-output builds.txt &> /dev/null &&  cat builds.txt

Output::

    2017-08-16.1 # 16-Aug-2017 05:48
    latest # 16-Aug-2017 05:48
    latest_containers # 16-Aug-2017 05:48
    passed_phase1 # 16-Aug-2017 05:48
    ......
