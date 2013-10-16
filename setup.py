from distutils.core import setup

import os

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py')))

def find_packages(path='.', base=''):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dirpath = os.path.join(path, item)
        if is_package(dirpath):
            if base:
                module_name = '{base}.{item}'.format(base=base, item=item)
            else:
                module_name = item
            packages[module_name] = dirpath
            packages.update(find_packages(dirpath, module_name))
    return packages


packages = find_packages()

setup(name='lhcb',
      version='0.0',
      description='A high-level fitting utility based on RooFit',
      author='Igor Babuschkin',
      author_email='igor@babuschk.in',
      url='',
      package_dir=packages,
      packages=packages.keys(),
      package_data={'': [
          'testdata/*',
      ]},
      scripts=['bin/fit'],
      install_requires=[
          "configobj",
          "rootpy",
          ],
     )
