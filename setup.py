from setuptools import find_packages, setup

PACKAGE_NAME = 'perkins'
requirements = open('requirements.txt').read().split('\n')[:-1]

setup(
    name=PACKAGE_NAME,
    version='0.1.5',
    description='Utilidades para extraccion de datos',
    install_requires=requirements,
    url='https://github.com/datos-abiertos-bo/perkins',
    packages=find_packages(),
    python_requires='>=3.6',
)
