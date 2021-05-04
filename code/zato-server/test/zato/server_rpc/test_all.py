# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from contextlib import closing
from unittest import main, TestCase

# Zato
from zato.common.ext.dataclasses import dataclass
from zato.common.odb.model import Base, HTTPBasicAuth, Cluster, Server as ServerModel
from zato.common.odb.api import ODBManager, SQLConnectionPool
from zato.server.connection.server.rpc.api import ConfigCtx, ServerRPC
from zato.server.connection.server.rpc.config import CredentialsConfig, ODBConfigSource, RemoteServerInvocationCtx
from zato.server.connection.server.rpc.invoker import LocalServerInvoker, RemoteServerInvoker, \
     ServerInvoker

# ################################################################################################################################
# ################################################################################################################################

class TestConfig:
    cluster_name = 'rpc_test_cluster'
    server1_name = 'server1'
    server2_name = 'server2'
    server3_name = 'server3'
    api_credentials_password = 'api_credentials_password'
    server1_preferred_address = 'https://abc1'
    server2_preferred_address = 'https://abc2'
    server3_preferred_address = 'https://abc3'
    crypto_use_tls = True

# ################################################################################################################################
# ################################################################################################################################

class TestCluster:
    def __init__(self, name):
        # type: (str) -> None
        self.name = name

# ################################################################################################################################
# ################################################################################################################################

class TestParallelServer:
    def __init__(self, cluster, odb, server_name):
        # type: (TestCluster, ODBManager, str) -> None
        self.cluster = cluster
        self.odb = odb
        self.name = server_name

# ################################################################################################################################
# ################################################################################################################################

class BaseTestServerInvoker:

    @dataclass
    class InvocationEntry:
        args: tuple
        kwargs: dict

# ################################################################################################################################
# ################################################################################################################################

class TestLocalServerInvoker(LocalServerInvoker, BaseTestServerInvoker):

    def __init__(self, *args, **kwargs):

        # Initialise our base class
        super().__init__(*args, **kwargs)

        # An entry is added each time self.invoke is called
        self.invocation_history = []

    def invoke(self, *args, **kwargs):
        self.invocation_history.append(self.InvocationEntry(args, kwargs))

# ################################################################################################################################
# ################################################################################################################################

class TestRemoteServerInvoker(RemoteServerInvoker, BaseTestServerInvoker):

    def __init__(self, *args, **kwargs):

        # Initialise our base class
        super().__init__(*args, **kwargs)

        # An entry is added each time self.invoke is called
        self.invocation_history = []

    def invoke(self, *args, **kwargs):
        self.invocation_history.append(self.InvocationEntry(args, kwargs))

# ################################################################################################################################
# ################################################################################################################################

class ServerRPCTestCase(TestCase):

    def setUp(self):

        # Prepare in-memory ODB configuration ..
        odb_name = 'ServerRPCTestCase'
        odb_config = {
            'engine': 'sqlite',
            'is_active': True,
            'fs_sql_config': {},
            'echo': True,
        }

        # .. set up ODB ..
        odb_pool = SQLConnectionPool(odb_name, odb_config, odb_config)
        self.odb = ODBManager()
        self.odb.init_session(odb_name, odb_config, odb_pool)

        # .. create SQL schema ..
        Base.metadata.create_all(self.odb.pool.engine)

        with closing(self.odb.session()) as session:

            cluster = Cluster()
            cluster.name = TestConfig.cluster_name
            cluster.odb_type = 'sqlite'
            cluster.broker_host = 'localhost-test-broker-host'
            cluster.broker_port = 123456
            cluster.lb_host = 'localhost-test-lb-host'
            cluster.lb_port = 1234561
            cluster.lb_agent_port = 1234562

            server1 = ServerModel()
            server1.cluster = cluster
            server1.name = TestConfig.server1_name
            server1.token = 'abc1'
            server1.preferred_address = TestConfig.server1_preferred_address
            server1.crypto_use_tls = TestConfig.crypto_use_tls

            server2 = ServerModel()
            server2.cluster = cluster
            server2.name = TestConfig.server2_name
            server2.token = 'abc2'
            server2.preferred_address = TestConfig.server2_preferred_address
            server2.crypto_use_tls = TestConfig.crypto_use_tls

            server3 = ServerModel()
            server3.cluster = cluster
            server3.name = TestConfig.server3_name
            server3.token = 'abc3'
            server3.preferred_address = TestConfig.server3_preferred_address
            server3.crypto_use_tls = TestConfig.crypto_use_tls

            api_credentials = HTTPBasicAuth()
            api_credentials.cluster = cluster
            api_credentials.is_active = True
            api_credentials.name = CredentialsConfig.sec_def_name
            api_credentials.username = CredentialsConfig.api_user
            api_credentials.realm = CredentialsConfig.sec_def_name
            api_credentials.password = TestConfig.api_credentials_password

            session.add(cluster)
            session.add(server1)
            session.add(server2)
            session.add(server3)
            session.add(api_credentials)

            session.commit()

# ################################################################################################################################

    def get_server_rpc(self, odb, local_server_invoker_class=None, remote_server_invoker_class=None):

        cluster = TestCluster(TestConfig.cluster_name)
        parallel_server = TestParallelServer(cluster, odb, TestConfig.server1_name)

        config_source = ODBConfigSource(parallel_server.odb, cluster.name, parallel_server.name)
        config_ctx = ConfigCtx(
            config_source,
            parallel_server,
            local_server_invoker_class=local_server_invoker_class,
            remote_server_invoker_class=remote_server_invoker_class,
        )

        return ServerRPC(config_ctx)

# ################################################################################################################################

    def get_local_server_invoker(self, local_server_invoker_class=LocalServerInvoker):
        rpc = self.get_server_rpc(None, local_server_invoker_class=local_server_invoker_class)
        return rpc[TestConfig.server1_name]

# ################################################################################################################################

    def get_remote_server_invoker(self, server_name, remote_server_invoker_class=RemoteServerInvoker):

        rpc = self.get_server_rpc(self.odb, remote_server_invoker_class=remote_server_invoker_class)
        return rpc[TestConfig.server2_name]

# ################################################################################################################################

    def test_get_item_local_server(self):

        invoker = self.get_local_server_invoker()

        self.assertIsInstance(invoker, ServerInvoker)
        self.assertIsInstance(invoker, LocalServerInvoker)

# ################################################################################################################################

    def test_get_item_remote_server(self):

        invoker = self.get_remote_server_invoker(TestConfig.server2_name)

        self.assertIsInstance(invoker, ServerInvoker)
        self.assertIsInstance(invoker, RemoteServerInvoker)

# ################################################################################################################################

    def test_invoke_local_server(self):

        invoker = self.get_local_server_invoker(
            local_server_invoker_class=TestLocalServerInvoker) # type: TestLocalServerInvoker

        args1 = (1, 2, 3, 4)
        kwargs1 = {'a1':'a2', 'b1':'b2'}

        args2 = (5, 6, 7, 8)
        kwargs2 = {'a3':'a4', 'b3':'b4'}

        invoker.invoke(*args1, **kwargs1)
        invoker.invoke(*args2, **kwargs2)

        history1 = invoker.invocation_history[0] # type: TestLocalServerInvoker.InvocationEntry
        history2 = invoker.invocation_history[1] # type: TestLocalServerInvoker.InvocationEntry

        self.assertTupleEqual(history1.args, args1)
        self.assertDictEqual(history1.kwargs, kwargs1)

        self.assertTupleEqual(history2.args, args2)
        self.assertDictEqual(history2.kwargs, kwargs2)

# ################################################################################################################################

    def test_invoke_remote_server(self):

        invoker = self.get_remote_server_invoker(
            TestConfig.server2_name, remote_server_invoker_class=TestRemoteServerInvoker) # type: TestRemoteServerInvoker

        args1 = (1, 2, 3, 4)
        kwargs1 = {'a1':'a2', 'b1':'b2'}

        args2 = (5, 6, 7, 8)
        kwargs2 = {'a3':'a4', 'b3':'b4'}

        invoker.invoke(*args1, **kwargs1)
        invoker.invoke(*args2, **kwargs2)

        history1 = invoker.invocation_history[0] # type: TestRemoteServerInvoker.InvocationEntry
        history2 = invoker.invocation_history[1] # type: TestRemoteServerInvoker.InvocationEntry

        self.assertTupleEqual(history1.args, args1)
        self.assertDictEqual(history1.kwargs, kwargs1)

        self.assertTupleEqual(history2.args, args2)
        self.assertDictEqual(history2.kwargs, kwargs2)

# ################################################################################################################################

    def test_remote_server_invocation_ctx_is_populated(self):
        """ Confirms that remote server's invocation_ctx contains remote address and API credentials.
        """
        invoker = self.get_remote_server_invoker(
            TestConfig.server2_name, remote_server_invoker_class=TestRemoteServerInvoker) # type: TestRemoteServerInvoker

        ctx = invoker.invocation_ctx

        self.assertEqual(ctx.address, TestConfig.server2_preferred_address)
        self.assertEqual(ctx.cluster_name, TestConfig.cluster_name)
        self.assertEqual(ctx.server_name, TestConfig.server2_name)
        self.assertEqual(ctx.username, CredentialsConfig.api_user)
        self.assertEqual(ctx.password, TestConfig.api_credentials_password)
        self.assertIs(ctx.crypto_use_tls, TestConfig.crypto_use_tls)

# ################################################################################################################################

    def test_populate_servers(self):
        pass

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':
    main()

# ################################################################################################################################
