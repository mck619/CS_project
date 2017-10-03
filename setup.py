from setuptools import setup, find_packages

setup(name='cspython',
      version='0.1.0',
      description='python data analysis tools',
      author=['Michael Kakehashi','John Kleeman'],
      author_email='mckakehashi@gmail.com',
      packages=find_packages(), install_requires=['pandas', 'jupyter']
      )
