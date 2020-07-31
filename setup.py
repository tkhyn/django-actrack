"""
django-actrack
An activity tracker and notifier for django
(c) 2014-2020 Thomas Khyn
MIT License (see LICENSE.txt)
"""

from setuptools import setup, find_packages
import os


# imports __version__ variable
exec(open('actrack/version.py').read())
dev_status = __version_info__[3]

if dev_status == 'alpha' and not __version_info__[4]:
    dev_status = 'pre'

DEV_STATUS = {'pre': '2 - Pre-Alpha',
              'alpha': '3 - Alpha',
              'beta': '4 - Beta',
              'rc': '4 - Beta',
              'final': '5 - Production/Stable'}

# setup function parameters
setup(
    name='django-actrack',
    version=__version__,
    description='An activity tracker for Django',
    long_description=open(os.path.join('README.rst')).read(),
    author='Thomas Khyn',
    author_email='thomas@ksytek.com',
    url='https://github.com/tkhyn/django-actrack',
    keywords=[],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: %s' % DEV_STATUS[dev_status],
        'Framework :: Django',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
    ],
    packages=find_packages(exclude=('tests',)),
    install_requires=(
        'django>=1.11',
        'django-gm2m>=0.6',
        'jsonfield',
    ),
)
