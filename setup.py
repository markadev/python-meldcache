from setuptools import find_packages, setup


setup(
    name = 'python-meldcache',
    description = 'Memcached client that melds multiple memcached servers ' +
                  'into one elastic cache cluster.',
    author = 'Mark Aikens',
    author_email = 'markadev@primeletters.net',
    license = 'MIT',

    packages = find_packages(),
    install_requires = [
        'pymemcache',
        'python-etcd',
        'uhashring',
    ],

    use_scm_version = True,
    setup_requires = ['setuptools_scm'],
)

# vim:set ts=4 sw=4 expandtab:
