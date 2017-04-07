# from distutils.core import setup

from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='tripleFingerprint',
    version='0.2',
    packages=find_packages(),
    url='https://github.com/costezki/RDF-fingerprint-diff',
    license='GPL V3',
    author='Eugeniu Costetchi',
    author_email='costezki.eugen@gmail.com',
    description='generates report representing the fingerprint of a RDF dataset'
                'and eventually '
                'offers a diff to another fingerprint',
    install_requires=['pylatex', 'pandas', 'click'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python ',
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
      ],
    keywords='RDF application-profile statistics data-fingerprint',
    include_package_data=True,
    long_description=readme(),
    entry_points="""
        [console_scripts]
        fingerprint=fingerprint.triple_profiler:cli
    """
)
