# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import unittest
from libcloud.utils.py3 import httplib

from libcloud.common.types import InvalidCredsError
from libcloud.common.dimensiondata import DimensionDataAPIException
from libcloud.compute.drivers.dimensiondata import DimensionDataNodeDriver as DimensionData
from libcloud.compute.base import Node, NodeAuthPassword, NodeLocation

from libcloud.test import MockHttp
from libcloud.test.compute import TestCaseMixin
from libcloud.test.file_fixtures import ComputeFileFixtures

from libcloud.test.secrets import DIMENSIONDATA_PARAMS


class DimensionDataTests(unittest.TestCase, TestCaseMixin):

    def setUp(self):
        DimensionData.connectionCls.conn_classes = (None, DimensionDataMockHttp)
        DimensionDataMockHttp.type = None
        self.driver = DimensionData(*DIMENSIONDATA_PARAMS)

    def test_invalid_region(self):
        try:
            self.driver = DimensionData(*DIMENSIONDATA_PARAMS, region='blah')
        except ValueError:
            pass

    def test_invalid_creds(self):
        DimensionDataMockHttp.type = 'UNAUTHORIZED'
        try:
            self.driver.list_nodes()
            self.assertTrue(
                False)  # Above command should have thrown an InvalidCredsException
        except InvalidCredsError:
            pass

    def test_list_locations_response(self):
        DimensionDataMockHttp.type = None
        ret = self.driver.list_locations()
        self.assertEqual(len(ret), 5)
        first_node = ret[0]
        self.assertEqual(first_node.id, 'NA3')
        self.assertEqual(first_node.name, 'US - West')
        self.assertEqual(first_node.country, 'US')

    def test_list_nodes_response(self):
        DimensionDataMockHttp.type = None
        ret = self.driver.list_nodes()
        self.assertEqual(len(ret), 3)

    def test_list_sizes_response(self):
        DimensionDataMockHttp.type = None
        ret = self.driver.list_sizes()
        self.assertEqual(len(ret), 1)
        size = ret[0]
        self.assertEqual(size.name, 'default')

    def test_reboot_node_response(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = node.reboot()
        self.assertTrue(ret is True)

    def test_reboot_node_response_INPROGRESS(self):
        DimensionDataMockHttp.type = 'INPROGRESS'
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        try:
            node.reboot()
            self.assertTrue(
                False)  # above command should have thrown DimensionDataAPIException
        except DimensionDataAPIException:
            pass

    def test_destroy_node_response(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = node.destroy()
        self.assertTrue(ret is True)

    def test_destroy_node_response_RESOURCE_BUSY(self):
        DimensionDataMockHttp.type = 'INPROGRESS'
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        try:
            node.destroy()
            self.assertTrue(
                False)  # above command should have thrown DimensionDataAPIException
        except DimensionDataAPIException:
            pass

    def test_create_node_response(self):
        rootPw = NodeAuthPassword('pass123')
        image = self.driver.list_images()[0]
        network = self.driver.ex_list_networks()[0]
        node = self.driver.create_node(name='test2', image=image, auth=rootPw,
                                       ex_description='test2 node', ex_network=network,
                                       ex_is_started=False)
        self.assertEqual(node.id, 'e75ead52-692f-4314-8725-c8a4f4d13a87')
        self.assertEqual(node.extra['status'].action, 'DEPLOY_SERVER')

    def test_create_node_response_network_domain(self):
        rootPw = NodeAuthPassword('pass123')
        location = self.driver.ex_get_location_by_id('NA9')
        image = self.driver.list_images(location=location)[0]
        network_domain = self.driver.ex_list_network_domains(location=location)[0]
        vlan = self.driver.ex_list_vlans(location=location)[0]
        node = self.driver.create_node(name='test2', image=image, auth=rootPw,
                                       ex_description='test2 node',
                                       ex_network_domain=network_domain,
                                       ex_vlan=vlan,
                                       ex_is_started=False)
        self.assertEqual(node.id, 'e75ead52-692f-4314-8725-c8a4f4d13a87')
        self.assertEqual(node.extra['status'].action, 'DEPLOY_SERVER')

    def test_create_node_no_network(self):
        rootPw = NodeAuthPassword('pass123')
        image = self.driver.list_images()[0]
        try:
            self.driver.create_node(name='test2', image=image, auth=rootPw,
                                    ex_description='test2 node', ex_network=None,
                                    ex_isStarted=False)
        except ValueError:
            pass

    def test_ex_shutdown_graceful(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = self.driver.ex_shutdown_graceful(node)
        self.assertTrue(ret is True)

    def test_ex_shutdown_graceful_INPROGRESS(self):
        DimensionDataMockHttp.type = 'INPROGRESS'
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        try:
            self.driver.ex_shutdown_graceful(node)
            self.assertTrue(
                False)  # above command should have thrown DimensionDataAPIException
        except DimensionDataAPIException:
            pass

    def test_ex_start_node(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = self.driver.ex_start_node(node)
        self.assertTrue(ret is True)

    def test_ex_start_node_INPROGRESS(self):
        DimensionDataMockHttp.type = 'INPROGRESS'
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        try:
            self.driver.ex_start_node(node)
            self.assertTrue(
                False)  # above command should have thrown DimensionDataAPIException
        except DimensionDataAPIException:
            pass

    def test_ex_power_off(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = self.driver.ex_power_off(node)
        self.assertTrue(ret is True)

    def test_ex_power_off_INPROGRESS(self):
        DimensionDataMockHttp.type = 'INPROGRESS'
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        try:
            self.driver.ex_power_off(node)
            self.assertTrue(
                False)  # above command should have thrown DimensionDataAPIException
        except DimensionDataAPIException:
            pass

    def test_ex_reset(self):
        node = Node(id='11', name=None, state=None,
                    public_ips=None, private_ips=None, driver=self.driver)
        ret = self.driver.ex_reset(node)
        self.assertTrue(ret is True)

    def test_list_networks(self):
        nets = self.driver.list_networks()
        self.assertEqual(nets[0].name, 'test-net1')
        self.assertTrue(isinstance(nets[0].location, NodeLocation))

    def test_create_network_domain(self):
        location = self.driver.ex_get_location_by_id('NA9')
        net = self.driver.ex_create_network_domain(location=location,
                                                   name='test',
                                                   description='test')
        self.assertEqual(net.name, 'test')
        self.assertTrue(net.id, 'f14a871f-9a25-470c-aef8-51e13202e1aa')

    def test_get_network_domain(self):
        location = self.driver.ex_get_location_by_id('NA9')
        net = self.driver.ex_get_network_domain('8cdfd607-f429-4df6-9352-162cfc0891be')
        self.assertEqual(net.id, '8cdfd607-f429-4df6-9352-162cfc0891be')
        self.assertEqual(net.description, 'test2')
        self.assertEqual(net.name, 'test')

    def test_update_network_domain(self):
        location = self.driver.ex_get_location_by_id('NA9')
        net = self.driver.ex_get_network_domain('8cdfd607-f429-4df6-9352-162cfc0891be')
        net.name = 'new name'
        net2 = self.driver.ex_update_network_domain(net)
        self.assertEqual(net2.name, 'new name')

    def test_delete_network_domain(self):
        location = self.driver.ex_get_location_by_id('NA9')
        net = self.driver.ex_get_network_domain('8cdfd607-f429-4df6-9352-162cfc0891be')
        result = self.driver.ex_delete_network_domain(net)
        self.assertTrue(result)

    def test_ex_list_networks(self):
        nets = self.driver.ex_list_networks()
        self.assertEqual(nets[0].name, 'test-net1')
        self.assertTrue(isinstance(nets[0].location, NodeLocation))

    def test_ex_list_network_domains(self):
        nets = self.driver.ex_list_network_domains()
        self.assertEqual(nets[0].name, 'Aurora')
        self.assertTrue(isinstance(nets[0].location, NodeLocation))

    def test_ex_list_vlans(self):
        vlans = self.driver.ex_list_vlans()
        self.assertEqual(vlans[0].name, "Primary")


class DimensionDataMockHttp(MockHttp):

    fixtures = ComputeFileFixtures('dimensiondata')

    def _oec_0_9_myaccount_UNAUTHORIZED(self, method, url, body, headers):
        return (httplib.UNAUTHORIZED, "", {}, httplib.responses[httplib.UNAUTHORIZED])

    def _oec_0_9_myaccount(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_myaccount.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_myaccount_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_myaccount.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_base_image(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_base_image.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_base_imageWithDiskSpeed(self, method, url, body, headers):
        body = self.fixtures.load('oec_0_9_base_imageWithDiskSpeed.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deployed(self, method, url, body, headers):
        body = self.fixtures.load(
            'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deployed.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_pendingDeploy(self, method, url, body, headers):
        body = self.fixtures.load(
            'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_pendingDeploy.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_datacenter(self, method, url, body, headers):
        body = self.fixtures.load(
            'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11(self, method, url, body, headers):
        body = None
        action = url.split('?')[-1]

        if action == 'restart':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_restart.xml')
        elif action == 'shutdown':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_shutdown.xml')
        elif action == 'delete':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_delete.xml')
        elif action == 'start':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_start.xml')
        elif action == 'poweroff':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_poweroff.xml')

        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_INPROGRESS(self, method, url, body, headers):
        body = None
        action = url.split('?')[-1]

        if action == 'restart':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_restart_INPROGRESS.xml')
        elif action == 'shutdown':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_shutdown_INPROGRESS.xml')
        elif action == 'delete':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_delete_INPROGRESS.xml')
        elif action == 'start':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_start_INPROGRESS.xml')
        elif action == 'poweroff':
            body = self.fixtures.load(
                'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_11_poweroff_INPROGRESS.xml')

        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server(self, method, url, body, headers):
        body = self.fixtures.load(
            '_oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkWithLocation(self, method, url, body, headers):
        body = self.fixtures.load(
            'oec_0_9_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_networkWithLocation.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deleteServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deleteServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deleteServer_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deleteServer_RESOURCEBUSY.xml')
        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_rebootServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_rebootServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_rebootServer_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_rebootServer_RESOURCEBUSY.xml')
        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_server(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_server.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_infrastructure_datacenter(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_infrastructure_datacenter.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_startServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_startServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_startServer_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_startServer_INPROGRESS.xml')
        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_shutdownServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_shutdownServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_shutdownServer_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_shutdownServer_INPROGRESS.xml')
        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_resetServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_resetServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_powerOffServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_powerOffServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_powerOffServer_INPROGRESS(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_powerOffServer_INPROGRESS.xml')
        return (httplib.BAD_REQUEST, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_networkDomain(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_networkDomain.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_vlan(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_vlan.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deployServer(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_deployServer.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_server_e75ead52_692f_4314_8725_c8a4f4d13a87(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_server_server_e75ead52_692f_4314_8725_c8a4f4d13a87.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_deployNetworkDomain(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_deployNetworkDomain.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_networkDomain_8cdfd607_f429_4df6_9352_162cfc0891be(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_networkDomain_8cdfd607_f429_4df6_9352_162cfc0891be.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_editNetworkDomain(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_editNetworkDomain.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_deleteNetworkDomain(self, method, url, body, headers):
        body = self.fixtures.load(
            'caas_2_0_8a8f6abc_2745_4d8a_9cbc_8dabe5a7d0e4_network_deleteNetworkDomain.xml')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
