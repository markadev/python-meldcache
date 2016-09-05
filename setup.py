from setuptools import find_packages, setup


setup(
    name = 'meldcache',
    description = 'Memcached client that melds multiple memcached servers ' +
                  'into one elastic cache cluster.',
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
