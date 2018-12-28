from setuptools import setup, find_packages
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
    version='1.2.3',
    license='MIT',
    author='Thomas Gassmann',
    author_email='thomas.gassmann@hotmail.com',
    url='https://github.com/ThomasGassmann/mycloud-cli',
    install_requires=install_requires,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['mycloud=mycloud.__main__:main']
    }
)
