import subprocess

def server():
    cmd =['python', 'manage.py', 'runserver_plus']
    subprocess.run(cmd)

def migrate():
    cmd =['python', 'manage.py', 'migrate']
    subprocess.run(cmd)

def shell():
    cmd =['python', 'manage.py', 'shell_plus']
    subprocess.run(cmd)
