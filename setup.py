from setuptools import setup

setup(name='synfony',
      version='0.1',
      packages=['common',],
      package_dir={'common': 'synfony/common/',},
      install_requires=['flake8',
                        'pygame',
                        'pytest'],
      python_requires='~=3.10')
