from setuptools import setup, find_packages


def readme():
    """Return the contents of the project README file."""
    with open('README.md') as f:
        return f.read()


def get_requirements():
    """Return a list of package requirements from the requirements.txt file."""
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    name='tempset',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/tempset',
    license='BSD2-Simplified',
    author='Aowabin Rahman; Chris R. Vernon',
    author_email='aowabin.rahman@pnnl.gov; chris.vernon@pnnl.gov',
    description='Generates new temperature set point schedules from base schedules',
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires='>=3.7.*, <4',
    include_package_data=True,
    install_requires=get_requirements()
)