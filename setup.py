from setuptools import setup

version = {}
with open('metronomiconic/version.py') as f:
    exec(f.read(), version)

setup(
    name='metronomiconic',
    version=version['__version__'],
    packages=['metronomiconic'],
    url='http://github.com/trueneu/metronomiconic',
    download_url='https://github.com/trueneu/metronomiconic/archive/v{vers}.zip'.format(vers=version['__version__']),
    license='MIT',
    author='trueneu',
    author_email='true.neu@gmail.com',
    description="The music learner's metronome with double/half tempo feature",
    platforms='Posix; MacOS X',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia',
    ],
    install_requires=[
        'soundfile',
        'pysoundcard',
        'numpy',
        'urwid',
    ],
    long_description=open("README.rst").read(),
    entry_points={
        'console_scripts': [
              'metronomiconic = metronomiconic.main:main'
        ],
    },

)
