from setuptools import setup, find_packages
import json


install_requires = []

with open('README.md', 'r') as fh:
    long_description = fh.read()

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
    long_description=long_description,
    description='myCloud Command Line Interface',
    long_description_content_type='text/markdown',
    author_email='thomas.gassmann@hotmail.com',
    url='https://github.com/thomasgassmann/mycloud-cli',
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['mycloud=mycloud.__main__:main']
    },
    keywords='swisscom cloud cli mycloud',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ]
)
