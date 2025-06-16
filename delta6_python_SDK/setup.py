from setuptools import setup, find_packages

setup(
    name="delta6",
    version="1.1",
    packages=find_packages(),
    install_requires=[
        'pyserial', 
        'apscheduler',
        'scipy',
        'numpy',
        'pygame',
        'platformio'
    ],
    author="Yue Feng",
    author_email="ttopeor@gmail.com",
    description="An affordable 6-dof force sensor",
    url="https://github.com/ttopeor/Delta6_Doc",
)
