# from distutils.core import setup

from setuptools import setup

setup(
    name='tripleFingerprint',
    version='0.1',
    packages=['fingerprint'],
    url='',
    license='GPL V3',
    author='Eugeniu Costetchi',
    author_email='costezki.eugen@gmail.com',
    description='generates report of triple dataset fringerprint and eventually '
                'offers a diff to another dataset fingerprint',
    install_requires=['pylatex', 'pandas', 'click'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python ',
      ],
    keywords='RDF application-profile statistics data-fingerprint',
    include_package_data=True,
)
