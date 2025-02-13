# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from unittest import main, TestCase

# Zato
# from zato.common.test import CommandLineServiceInvoker

# ################################################################################################################################
# ################################################################################################################################

class WSXServicesTest(TestCase):

    def test_wsx_services(self) -> 'None':
        # service = 'pubsub1.my-service'
        # invoker = CommandLineServiceInvoker(check_stdout=False)
        # out = invoker.invoke_and_test(service)
        # print(111, out)
        pass

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':
    main()

# ################################################################################################################################
# ################################################################################################################################

'''
# -*- coding: utf-8 -*-

"""
Copyright (C) 2022, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# Zato

from zato.server.service import Service


#tester = FullPathTester(self, False) # type: ignore
#tester.run()

# ################################################################################################################################
# ################################################################################################################################

class MyService(Service):
    """ Tests services that WebSocket clients use.
    """

    def handle(self):

        # stdlib
        from unittest import defaultTestLoader, TestCase, TextTestRunner

        # Zato
        from zato.common.test.config import TestConfig
        from zato.common.test.pubsub import FullPathTester, PubSubTestingClass

        topic_name = TestConfig.pubsub_topic_name_name

        class WSXServicesTestCase(TestCase, PubSubTestingClass):

            def _subscribe(_self, *args, **kwargs): # type: ignore
                service = 'zato.pubsub.pubapi.subscribe'
                response = self.invoke(service, {'topic_name': topic_name})
                return response['sub_key']

            def _unsubscribe(_self, *args, **kwargs): # type: ignore
                service = 'zato.pubsub.pubapi.unsubscribe'
                response = self.invoke(service, {'topic_name': topic_name})
                return response

            def _publish(_self, *args, **kwargs): # type: ignore
                service = 'zato.pubsub.pubapi.publish-message'
                response = self.invoke(service, {'topic_name': topic_name, 'data':'abc123'})
                return response

            def _receive(_self, *args, **kwargs): # type: ignore
                service = 'zato.pubsub.pubapi.get-messages'
                response = self.invoke(service, {'topic_name': topic_name})
                return response

            def test_wsx_services_full_path_subscribe_before_publication(_self):
                tester = FullPathTester(_self, False)
                tester.run()

            def test_wsx_services_full_path_subscribe_after_publication(_self):
                pass

        try:
            suite = defaultTestLoader.loadTestsFromTestCase(WSXServicesTestCase)
            result = TextTestRunner().run(suite)
            result
            topic_name

            self.response.payload = str(result)
        except Exception as e:
            self.logger.warn('QQQ-1 %r', e)

        #sub_key = self._invoke_subscribe()

        """
        pub_service = 'zato.pubsub.pubapi.publish-message'
        topic_name = '/zato/demo/sample'
        data = 'abc123'

        msg = {
            'topic_name': topic_name,
            'data': data,
        }

        response = self.invoke(pub_service, msg)
        self.response.payload = response
        """

# ################################################################################################################################
# ################################################################################################################################

'''
