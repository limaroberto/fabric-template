### Fabric deploy skeleton for django projects

Supposed server setup for django is uwsgi with nginx (as proxy and static files server)
Target systems are Centos 5 and 6 (remote); Ubuntu 12 and OpenSUSE 11 (local) for now.

Assuming all systems have python 2.7 installed and it has pip and virtualenv packages.
I used some django 1.4 - specific paths (e.g for settings.py and wsgi.py). You may need to correct it accordingly
to your project

Multiple environments are supported, you can adopt config file to your needs, ex. good to have dev, stage and prod environments.

#### Commands

* install - makes installation on the remote server
* deploy - deploys the application

#### Examples
```bash
fab e:environment_name deploy
```
where **environment_name** - environment configuration, defined in environments.ini