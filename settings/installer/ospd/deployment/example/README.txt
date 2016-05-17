# This folder is meant to contains all the deployment files.
# If you wish to create your own storage templates, please create an empty `storage` folder and place any YAML files in the base of this folder.
# If you wish to create your own network templates, please create an empty `network` folder and place any YAML files in the base of this folder.
# If an instackenv.json file is present, it will be used for the introspection. (unless explicitly provided as a --instackenv-file flag)
# If an undercloud.conf file is present, it will be used for the undercloud installation. (unless explicitly provided as a --undercloud-config flag)
# If an overcloud_deploy.sh script is present, it will be used as the overcloud deployment command (unless explicitly provided as a --overcloud-script flag)
# Any YAML type files found in this folder will be appended to the end of the overcloud deployment command with a '-e' prefix.
