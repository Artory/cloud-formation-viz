from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cfviz',
    version='0.1.0',
    description='Python Distribution Utilities',
    author='Ben Butler-Cole, Jakub Valenta',
    author_email='ben@bridesmere.com, jakub.valenta@artory.com',
    url='https://github.com/Artory/cloud-formation-viz',

    packages=find_packages(),

    install_requires=[
        'click',
        'PyYAML',
    ],

    zip_safe=True,

    entry_points={
        'console_scripts': [
            'cfviz=cloud_formation_viz.cfviz:cli',
        ],
    },

    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
    ],
)
