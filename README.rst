================
 Document Title
================

Trying it out
=============

Commands::

    docker run --name memcached-01 -d -P memcached
    docker run --name memcached-02 -d -P memcached
    docker run --name memcached-03 -d -P memcached

    memcached-registrar --public-addr=127.0.0.1 --public-port=32770 --internal-port=32770 --registry=etcd://localhost/services/memcached-01/members
    memcached-registrar --public-addr=127.0.0.1 --public-port=32771 --internal-port=32771 --registry=etcd://localhost/services/memcached-01/members
    memcached-registrar --public-addr=127.0.0.1 --public-port=32772 --internal-port=32772 --registry=etcd://localhost/services/memcached-01/members

    etcdctl ls /services/memcached-01/members
