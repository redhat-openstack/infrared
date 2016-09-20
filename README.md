#Infrared Core

### Introduction
Infrared Core will be a rework of the original project which will be based around a composable
base, for which plugins writen in ansible playbooks / roles add or extend functionality
of the base.

#### Installation


```
git clone https://github.com/rhos-infra/infrared-core.git
cd infrared-core
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# init all the plugins
infrared plugin init-all

# list and check that we have provisioner
infrared plugin list

# try to run provisioner
infrared provisioner virsh [....]
```

