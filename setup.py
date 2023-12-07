import re

from setuptools import setup


PACKAGE_NAME = 'ringr'


with open('requirements.txt', 'r') as f:
    requires = f.read().split()


def read_file(path):
    with open(path) as f:
        return f.read()


def get_version():
    content = read_file(f'{PACKAGE_NAME}/__init__.py')
    regex = r'^__version__ = [\'"]([^\'"]+)[\'"]'
    match = re.search(regex, content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError('Unable to find __version__')


setup(
    name=PACKAGE_NAME,
    version=get_version(),
    description='Sound event detection system',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Alberto Alcolea',
    author_email='albertoalcolea@gmail.com',
    url='https://github.com/albertoalcolea/ringr',
    project_urls={
        'Source': 'https://github.com/albertoalcolea/ringr'
    },
    license='MIT',
    keywords=[
        'ringr',
        'ring',
        'sound',
        'sound detection',
        'audio',
        'audio detection',
        'frequency analyzer',
        'peak detection',
        'home assistant',
    ],
    packages=[PACKAGE_NAME],
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'ringr = ringr.__main__:main',
        ]
    },
    extras_require={
        'dev': [
            'flake8>=4.0.1',
            'twine>=4.0.0',
        ]
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
    ],
)
