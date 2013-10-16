from distutils.core import setup

setup(name='wouter',
      version='0.0',
      description='A high-level fitting utility based on RooFit',
      author='Igor Babuschkin',
      author_email='igor@babuschk.in',
      url='',
      packages=['wouter'],
      scripts=['bin/fit'],
      install_requires=[
          "configobj",
          "rootpy",
          ],
     )
