from setuptools import setup, find_packages

#exec (open('pymapmanager/version.py').read())

setup(
    name='pie',
    version=1.0.0,
    description='Raspberry Pi Controlled Experiment (PiE)',
    url='http://github.com/cudmore/pie',
    author='Robert H Cudmore',
    author_email='robert.cudmore@gmail.com',
    license='GNU GPLv3',
    packages = find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "paramiko"
    ]
)
