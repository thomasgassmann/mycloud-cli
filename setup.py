from setuptools import setup
import json


install_requires = []

with open('Pipfile.lock') as fd:
    lock_data = json.load(fd)
    install_requires = [
        package_name + package_data['version']
        for package_name, package_data in lock_data['default'].items()
    ]


setup(
    name='mycloud-cli',
    version='1.2.0',
    license='MIT',
    author='Thomas Gassmann',
    author_email='thomas.gassmann@hotmail.com',
    url='https://github.com/ThomasGassmann/mycloud-cli',
    py_modules=['mycloud'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': ['mycloud=mycloud:main']
    }
)
