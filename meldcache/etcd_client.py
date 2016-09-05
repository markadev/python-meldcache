from __future__ import unicode_literals

import etcd
import json
import threading
import time
from urlparse import urlparse

from .client import ClusteredClient


class EtcdClient(ClusteredClient):
    def __init__(self, url):
        super(EtcdClient, self).__init__()

        parsed_url = urlparse(url)
        if parsed_url.scheme == 'etcd':
            self.etcd_https = False
        elif parsed_url.scheme == 'etcds':
            self.etcd_https = True
        else:
            raise RuntimeError("Invalid etcd URL: '{}'".format(url))
        self.etcd_host = parsed_url.hostname
        self.etcd_port = parsed_url.port
        self.etcd_basedir = parsed_url.path.rstrip('/') + '/'
        self.etcd_poll_timeout = 5
        self.etcd_client = None

        # Start the member discovery thread
        self.stopped = False
        self.discovery_thread = threading.Thread(target=self._discover_members)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()

    def shutdown(self, wait=False):
        super(EtcdClient, self).__init__()

        self.stopped = True
        if wait:
            self.discovery_thread.join()

    def _discover_members(self):
        self.logger.info("Starting cache cluster membership discovery (etcd)")

        watch_index = None
        while not self.stopped:
            try:
                if self.etcd_client is None:
                    # We still need to connect to etcd! :O
                    self.etcd_client = self._etcd_connect()

                if watch_index is None:
                    # Perform the initial member discovery and enough
                    # info to start polling with etcd watches
                    watch_index, members = self._read_initial_members()
                    self.logger.info("Synchronized. Initial members are %s",
                        members.keys())

                # Wait for a change and then process it
                watch_index, change = self._poll_for_change(watch_index)
                if change is not None:
                    # TODO
                    # action can be 'set' 'expire' 'delete' OTHERS?
                    pass
            except etcd.EtcdException:
                self.logger.warn("Synchronization with etcd lost. Will retry.")
                # Trigger initial discovery again
                watch_index = None

                # Wait some time before retrying
                time.sleep(30)
        self.etcd_client = None

    def _etcd_connect(self):
        kwargs = {}
        if self.etcd_port is not None:
            kwargs['port'] = self.etcd_port
        if self.etcd_https:
            kwargs['protocol'] = 'https'
        return etcd.Client(host=self.etcd_host, allow_reconnect=True, **kwargs)

    def _read_initial_members(self):
        """
        List the contents of the etcd directory to fetch the current
        members as well as to get the watch index for change polling.
        :returns: a tuple of (watch_index, member_dict)
        """
        members = {}
        try:
            dir_result = self.etcd_client.get(self.etcd_basedir)
            # Start watch at X-Etcd-Index + 1
            watch_index = dir_result.etcd_index + 1

            base_len = len(self.etcd_basedir)
            for c in dir_result.children:
                if c.dir:
                    continue
                member_name = c.key[base_len:]
                try:
                    member_config = json.loads(c.value)
                    members[member_name] = member_config
                except ValueError:
                    # Gracefully ignore this member
                    self.logger.warn("The value for etcd key '%s' is not " +
                        "valid JSON", c.key)
        except etcd.EtcdKeyNotFound:
            # There are no members registered yet. That's perfectly OK.
            watch_index = 0
        return watch_index, members

    def _poll_for_change(self, watch_index):
        try:
            change = self.etcd_client.watch(self.etcd_basedir,
                index=watch_index,
                recursive=True,
                timeout=self.etcd_poll_timeout)
            watch_index = change.modifiedIndex + 1
        except etcd.EtcdWatchTimedOut:
            change = None
            # Continue on...
        return watch_index, change


# vim:set ts=4 sw=4 expandtab:
