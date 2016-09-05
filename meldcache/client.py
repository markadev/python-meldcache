from __future__ import unicode_literals

import logging
import time
from uhashring import HashRing


class ClusteredClient(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._hash_ring = HashRing([], compat=False, replicas=1)
        self._graylisted_servers = {}

    def shutdown(self):
        """
        Cleanly shuts down the client, terminating any background activity
        """
        pass

    def get(self, key):
        return self._routed_call(key, lambda client : client.get(key))

    def set(self, key, value, ttl=None):
        # TODO pass in ttl
        return self._routed_call(key, lambda client : client.set(key, value))

    def _routed_call(self, key, func):
        keep_retrying = True
        while keep_retrying:
            # Retrieve the node that the key currently maps to
            node = self._hash_ring.get(key)
            if node is None:
                # No (alive) nodes in the cluster
                break
            client = node['instance']

            if client.sock is None:
                # The client is not connected. Do not attempt retries on
                # failure if the operation doesn't work with a clean slate
                keep_retrying = False

            # Try the operation
            try:
                func(client)
            except Exception:
                # We expect that the client is disconnected now or there is
                # one less busted connection in the connection pool
                if not keep_retrying:
                    self._graylist_node(node)

                    # We changed the ring configuration so keep retrying
                    # because we'll get routed to another server.
                    keep_retrying = True
        return None

    def _graylist_node(self, node):
        """
        Adds the node to our graylist.

        The graylist is where unresponsive nodes go until they are either
        removed from the cluster configuration or are brought back online.

        Requests are not normally sent to nodes on the graylist.
        """
        nodename = node['nodename']
        if nodename not in self._graylisted_servers:
            node_cfg = {
                'hostname': node['hostname'],
                'port': node['port'],
                'weight': node['weight'],
                'graylisted_time': time.time(),
            }
            self._graylisted_servers.put(nodename, node_cfg)
            self._hash_ring.remove_node(nodename)

    # Called when a new node is discovered
    def _cfg_add_node(self, nodename, hostname, port, weight=1):
        """Adds a node to the cluster configuration."""

        # Remove it from the graylist so we try to use it right away
        if nodename in self._graylisted_servers:
            del self._graylisted_servers[nodename]

        if nodename not in self._hash_ring.conf:
            self.logger.info("Discovered new memcached instance '%s'",
                nodename)
            self._hash_ring.add_node(nodename,
                conf={'hostname': hostname, 'port': port, 'weight': weight})

    def _cfg_remove_node(self, nodename):
        """Removes a node from the cluster configuration."""

        if nodename in self._graylisted_servers:
            del self._graylisted_servers[nodename]
        elif nodename in self._hash_ring.conf:
            self._hash_ring.remove_node(nodename)


# vim:set ts=4 sw=4 expandtab:
