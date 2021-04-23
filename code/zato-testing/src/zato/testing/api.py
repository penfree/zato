# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# ################################################################################################################################
# ################################################################################################################################

class ParallelServer:
    def __init__(self):
        self.api = PublicAPI()

# ################################################################################################################################
# ################################################################################################################################

class _ChannelImpl:
    def __init__(self, name):

        self.name = name

    def invoke(self, request):
        pass

# ################################################################################################################################
# ################################################################################################################################

class Channel:
    def get(self, name):
        pass

    def invoke(self, name, request):
        pass

# ################################################################################################################################
# ################################################################################################################################

class ChannelREST(Channel):
    pass

# ################################################################################################################################
# ################################################################################################################################

class ChannelAPI:
    def __init__(self):
        self.rest = ChannelREST()

# ################################################################################################################################
# ################################################################################################################################

class PublicAPI:
    def __init__(self):
        self.channel = ChannelAPI()

# ################################################################################################################################
# ################################################################################################################################

class ZatoTestCase:

    def __init__(self):
        pass

    def test_create_customer(self):
        server = ParallelServer()

# ################################################################################################################################
# ################################################################################################################################
