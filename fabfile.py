# coding: utf-8
import os
import re
import ConfigParser
from fabric.api import env, run, sudo, cd, hide
from fabric.contrib.files import upload_template


def e(name="local"):
    print "Setting environment %s" % name
    env.local_app_path = os.path.dirname(os.path.abspath(__file__))
    env.name = name

    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(env.local_app_path, 'deploy', 'environments.ini'))
    config_tuple = config.items(section=env.name)

    for item in config_tuple:
        if isinstance(item[1], str):
            env[item[0]] = item[1].format(**env)
        else:
            env[item[0]] = item[1]

    env.pip = os.path.join(env.project_root, 'venv', 'bin', 'pip')
    env.python = os.path.join(env.project_root, 'venv', 'bin', 'python')


def collect_static():
    run('{python} {manage} collectstatic --noinput'.format(python=env.python,
        manage=os.path.join(env.project_root, 'app', 'manage.py')))


def update_requirements():
    run('{pip} install --upgrade -r {filepath}'.format(pip=env.pip,
        filepath=os.path.join(env.project_root, 'requirements.txt')))


def set_python_paths():
    which_distro()
    # Centos 5 has default python (2.4)
    # Ubuntu 12 and openSUSE 11 default is python 2.7
    if 'centos' in env.distro:
        env.glob_pip = run('which pip-2.7').stdout
        env.glob_python = run('which python2.7').stdout
        env.glob_virtualenv = run(command="which virtualenv-2.7").stdout
    else:
        env.glob_pip = run('which pip').stdout
        env.glob_python = run('which python').stdout
        env.glob_virtualenv = run(command="which virtualenv").stdout


def setup_virtualenv():
    set_python_paths()

    run('{virtualenv} --no-site-packages {dir}'.format(virtualenv=env.glob_virtualenv,
        dir=os.path.join(env.project_root, 'venv')))

    run('{pip} install -r {filepath}'.format(pip=env.pip,
        filepath=os.path.join(env.project_root, 'requirements.txt')))

    # Create PIL symlink in our virtual environment
    run('PIL_PATH=`' + env.glob_python + ' -c "import PIL, os; print os.path.dirname(os.path.abspath(PIL.__file__))"` '
        + '&& ln -s $PIL_PATH {}'.format(os.path.join(env.project_root, 'venv', 'lib', 'python2.7', 'PIL')
    ))

    # Workaround to avoid Unicode error in some python packages
    # which concatenate unicode and plain strings
    # see http://nedbatchelder.com/text/unipain.html
    run('echo \'import sys\nsys.setdefaultencoding("iso-8859-1")\' > %s' %
        os.path.join(env.project_root, 'venv', 'lib', 'python2.7', 'site-packages', 'sitecustomize.py'))


def setup_database():
    # Create DB and set permissions
    run('cd {project_root}/app && {python} manage.py syncdb'.format(python=env.python,
        project_root=env.project_root))
    run('chmod 777 {}'.format(os.path.join(env.project_root, 'dev.db')))
    run('chmod 777 {}'.format(env.project_root))


def setup_servers():
    with cd('/tmp'):
        # see http://wiki.nginx.org/Install
        run('wget http://nginx.org/download/nginx-1.4.1.tar.gz')
        run('./configure')
        run('make')
        sudo('make install')
    sudo('/sbin/chkconfig --add nginx')

    # Install uwsgi with python 2.7 pip
    set_python_paths()
    sudo('{} install uwsgi'.format(env.glob_pip))

    sudo('cp {} /etc/init.d/uwsgi'.format(os.path.join(env.project_root, 'app', 'deploy', 'uwsgi-init')))
    sudo('chmod +x /etc/init.d/uwsgi')
    sudo('/sbin/chkconfig --add uwsgi')
    sudo('/etc/init.d/uwsgi start')
    sudo('/etc/init.d/nginx restart')


def set_local_settings():
    upload_template(filename=os.path.join(env.local_app_path, 'deploy', 'local_settings.py'),
        destination=os.path.join(env.project_root, 'app', 'app', 'local_settings.py'),
        context=env,
        backup=False
    )


def upload_configs():
    # Create uwsgi vassal dir
    sudo('mkdir -p /etc/uwsgi')

    upload_template(filename=os.path.join(env.local_app_path, 'deploy', 'nginx.conf'),
        destination='/etc/nginx/conf.d/{}.conf'.format(env.project_name),
        context=env,
        use_sudo=True,
        backup=False
    )
    upload_template(filename=os.path.join(env.local_app_path, 'deploy', 'uwsgi.ini'),
        destination='/etc/uwsgi/{}.ini'.format(env.project_name),
        context=env,
        use_sudo=True,
        backup=False
    )
    set_local_settings()


def which_distro():
    with hide('output'):
        issue = run('cat /etc/issue').stdout
        p = re.compile('((ubuntu|centos|opensuse)[\s\w]*\d+)', re.IGNORECASE)
    matches = p.findall(issue)

    if matches:
        env.distro = str(matches[0][0]).lower()
    else:
        env.distro = None


def install():
    # TODO: support install task for Ubuntu, add check installed virtualenv and pip
    sudo('yum install -y git')
    run('mkdir -pv {}'.format(env.project_root))
    run('git clone {repo} {dir}'.format(repo=env.git_repo, dir=env.project_root))

    setup_virtualenv()
    upload_configs()
    setup_database()
    setup_servers()
    collect_static()


def deploy():
    env.uwsgi = run(command="which uwsgi").stdout

    with cd(env.project_root):
        run('git pull origin master')
        update_requirements()
        run('cd {project_root}/app && {python} manage.py syncdb'.format(python=env.python,
            project_root=env.project_root))
        #run('find . -name "*.mo" -print -delete')  # Clean old compiled gettext files
        #run('{} manage.py compilemessages'.format(env.python))  # Compile new gettext files
        collect_static()
        sudo('{uwsgi} --reload /tmp/{project}-master.pid'.format(uwsgi=env.uwsgi, project=env.project_name))
