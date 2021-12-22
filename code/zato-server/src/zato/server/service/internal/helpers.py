# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from dataclasses import dataclass
from io import StringIO
from json import loads
from logging import DEBUG

# Zato
from zato.common.exception import Forbidden
from zato.common.typing_ import intnone, list_, optional
from zato.common.util.open_ import open_rw
from zato.server.service import AsIs, Model, PubSubHook, Service
from zato.server.service.internal.service import Invoke

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.pubsub import PubSubMessage
    from zato.common.typing_ import any_, anytuple

# ################################################################################################################################
# ################################################################################################################################

default_services_allowed = (
    'zato.pubsub.pubapi.publish-message',
    'zato.pubsub.pubapi.subscribe-wsx',
    'zato.pubsub.pubapi.unsubscribe',
    'zato.pubsub.resume-wsx-subscription',
)

# ################################################################################################################################
# ################################################################################################################################

@dataclass(init=False)
class User(Model):
    user_id:      int
    username:     str
    display_name: optional[str]

# ################################################################################################################################
# ################################################################################################################################

@dataclass(init=False)
class UserAccount(Model):
    user:         User
    account_id:   int
    account_type: intnone

# ################################################################################################################################
# ################################################################################################################################

@dataclass
class GetUserRequest(Model):
    username: str

# ################################################################################################################################
# ################################################################################################################################

@dataclass
class GetUserAccountListRequest(Model):
    user_id:    optional[int]
    account_id: int

# ################################################################################################################################
# ################################################################################################################################

@dataclass(init=False)
class GetUserAccountListResponse(Model):
    user_account_list: list_[UserAccount]

# ################################################################################################################################
# ################################################################################################################################

@dataclass(init=False)
class GetUserResponse(Model):
    user:          list_[User]
    parent_user:   list_[optional[User]]
    previous_user: optional[list_[User]]

# ################################################################################################################################
# ################################################################################################################################

class Echo(Service):
    """ Copies request over to response.
    """
    def handle(self) -> 'None':
        self.response.payload = self.request.raw_request

# ################################################################################################################################
# ################################################################################################################################

class InputLogger(Service):
    """ Writes out all input data to server logs.
    """
    def handle(self):
        pass

    def finalize_handle(self) -> 'None': # type: ignore
        self.log_input()

# ################################################################################################################################
# ################################################################################################################################

class PubInputLogger(InputLogger):
    """ Same as InputLogger but has a publicly available name
    """
    name = 'pub.helpers.input-logger'

# ################################################################################################################################
# ################################################################################################################################

class RawRequestLogger(Service):
    """ Writes out self.request.raw_request to server logs.
    """
    name = 'pub.helpers.raw-request-logger'

    def handle(self) -> 'None':
        self.logger.info('Received request: `%s`', self.request.raw_request)

# ################################################################################################################################
# ################################################################################################################################

class IBMMQLogger(Service):
    """ Writes out self.request.raw_request to server logs.
    """
    name = 'pub.helpers.ibm-mq-logger'

    def handle(self) -> 'None':
        template = """
***********************
IBM MQ message received
***********************
MsgId: `{msg_id}`
CorrelId: `{correlation_id}`
Timestamp: `{timestamp}`
PutDate: `{put_date}`
PutTime: `{put_time}`
ReplyTo: `{reply_to}`
MQMD: `{mqmd!r}`
-----------------------
Data: `{data}`
***********************
"""

        mq = self.request.ibm_mq
        na = 'n/a'

        try:
            msg_id = mq.msg_id.decode('ascii')
        except UnicodeDecodeError:
            msg_id = repr(mq.msg_id)

        if mq.correlation_id:
            try:
                correlation_id = mq.correlation_id.decode('ascii')
            except UnicodeDecodeError:
                correlation_id = repr(mq.correlation_id)
        else:
            correlation_id = na

        info = {
            'msg_id': msg_id,
            'correlation_id': correlation_id,
            'timestamp': mq.timestamp,
            'put_date': mq.put_date,
            'put_time': mq.put_time,
            'reply_to': mq.reply_to or na,
            'mqmd': str(mq.mqmd).splitlines(),
            'data': self.request.raw_request,
        }

        msg = template.format(**info)
        msg_out = msg.encode('utf8')

        self.logger.info(msg_out)

# ################################################################################################################################
# ################################################################################################################################

class JSONRawRequestLogger(RawRequestLogger):
    """ Same as RawRequestLogger but returns a JSON response.
    """
    def handle(self) -> 'None':
        super(JSONRawRequestLogger, self).handle()
        self.response.payload = {'status': 'OK'}

# ################################################################################################################################
# ################################################################################################################################

class SIOInputLogger(Service):
    """ Writes out all SIO input parameters to server logs.
    """
    def handle(self) -> 'None':
        self.logger.info('%r', self.request.input)

# ################################################################################################################################
# ################################################################################################################################

class HTMLService(Service):

    def before_handle(self) -> 'None': # type: ignore

        # Configure Django if this service is used - not that we are not doing it
        # globally for the module because the configuration takes some milliseconds
        # the first time around (but later on it is not significant).

        # Django
        import django
        from django.conf import settings

        # Configure Django settings when the module is picked up
        if not settings.configured:
            settings.configure()
            django.setup()

    def set_html_payload(self, ctx:'any_', template:'str') -> 'None':

        # Django
        from django.template import Context, Template

        # Generate HTML and return response
        c = Context(ctx)
        t = Template(template)
        payload = t.render(c).encode('utf-8')

        self.logger.debug('Ctx:[%s]', ctx)
        self.logger.debug('Payload:[%s]', payload)

        if self.logger.isEnabledFor(DEBUG):
            buff = StringIO()
            self.logger.debug(buff.getvalue())
            buff.close()

        self.response.payload = payload
        self.response.content_type = 'text/html; charset=utf-8'

# ################################################################################################################################
# ################################################################################################################################

class TLSLogger(Service):
    """ Logs details of client TLS certificates.
    """
    def handle(self) -> 'None':
        has_tls = False
        for k, v in sorted(self.wsgi_environ.items()):
            if k.startswith('HTTP_X_ZATO_TLS_'):
                has_tls = True
                self.logger.info('%r: %r', k, v)

        if not has_tls:
            self.logger.warning('No HTTP_X_ZATO_TLS_* headers found')

# ################################################################################################################################
# ################################################################################################################################

class WebSocketsGateway(Service):
    """ Dispatches incoming WebSocket requests to target services.
    """
    name = 'helpers.web-sockets-gateway'
    services_allowed = []

    class SimpleIO:
        input_required = 'service',
        input_optional = AsIs('request'),
        output_optional = 'sub_key',
        skip_empty_keys = True

    def handle(self, _default_allowed:'anytuple'=default_services_allowed) -> 'None':

        # Local aliases
        input = self.request.input
        service = input.service

        if service \
           and service not in _default_allowed \
           and service not in self.services_allowed:
                self.logger.warning('Service `%s` is not among %s', service, self.services_allowed) # noqa: E117
                raise Forbidden(self.cid)

        # We need to special-pub/sub subscriptions
        # because they will require calling self.pubsub on behalf of the current WSX connection.
        if service == 'zato.pubsub.pubapi.subscribe-wsx':
            topic_name = input.request['topic_name']
            unsub_on_wsx_close = input.request.get('unsub_on_wsx_close', True)
            sub_key = self.pubsub.subscribe(
                topic_name, use_current_wsx=True, unsub_on_wsx_close=unsub_on_wsx_close, service=self)
            self.response.payload.sub_key = sub_key

        else:
            self.wsgi_environ['zato.orig_channel'] = self.channel
            response = self.invoke(service, self.request.input.request, wsgi_environ=self.wsgi_environ)
            self.response.payload = response

# ################################################################################################################################
# ################################################################################################################################

class WebSocketsPubSubGateway(Service):
    """ Dispatches incoming WebSocket publish/subscribe requests to target services.
    """
    name = 'helpers.web-sockets-pub-sub-gateway'

    class SimpleIO:
        input_required = ('service',)
        input_optional = (AsIs('request'),)

# ################################################################################################################################

    def handle(self) -> 'None':

        # Make sure this is one of allowed services that we are to invoke
        if self.request.input.service not in self.server.fs_server_config.pubsub.wsx_gateway_service_allowed:
            raise Forbidden(self.cid)

        # All good, we can invoke this service
        else:
            self.response.payload = self.invoke(self.request.input.service, self.request.input.request,
                wsgi_environ=self.wsgi_environ)

# ################################################################################################################################
# ################################################################################################################################

class ServiceGateway(Invoke):
    """ Service to invoke other services through.
    """
    name = 'helpers.service-gateway'

# ################################################################################################################################
# ################################################################################################################################

class APISpecHelperUser(Service):
    """ Test support services - User.
    """
    name = 'helpers.api-spec.user'

    class SimpleIO:
        input  = GetUserRequest
        output = GetUserResponse

# ################################################################################################################################

    def handle(self):

        # Our request
        request = self.request.input # type: GetUserRequest

        # Response to produce
        out = GetUserResponse()

        # To be returned in out.user ..
        user1 = User()
        user1.user_id      = 111
        user1.username     = 'username.111'
        user1.display_name = 'display_name.111.' + request.username

        # .. also to be returned in out.user ..
        user2 = User()
        user2.user_id      = 222
        user2.username     = 'username.222'
        user2.display_name = 'display_name.222.' + request.username

        # To be returned as out.parent_user
        # This is an empty list on purpose becaue the field is optional
        parent_user = []

        # To be returned as out.previous_user
        # This is an empty list on purpose becaue the field is optional as well
        previous_user = []

        # Note that user2 is added before user1 - this is on purpose because
        # the test that invokes us will check that this is the specific order, non-ascending,
        # that we are returning the data in, i.e. that nothing attempts to sort it itself
        # before the data is returned to the caller (to the test).
        out.user = [user2, user1]
        out.parent_user = parent_user
        out.previous_user = previous_user

        self.response.payload = out

# ################################################################################################################################
# ################################################################################################################################

class APISpecHelperAccountList(Service):
    """ Test support services - AccountList.
    """
    name = 'helpers.api-spec.account-list'

    class SimpleIO:
        input  = GetUserAccountListRequest
        output = GetUserAccountListResponse

# ################################################################################################################################

    def handle(self):

        # Our request
        request = self.request.input # type: GetUserAccountListRequest

        # Response to produce
        out = GetUserAccountListResponse()

        user1 = User()
        user1.user_id      = 111
        user1.username     = 'username.111'
        user1.display_name = 'display_name.111.{}'.format(request.user_id)

        user2 = User()
        user2.user_id      = 222
        user2.username     = 'username.222'
        user2.display_name = 'display_name.222.{}'.format(request.user_id)

        account1 = UserAccount()
        account1.user = user1
        account1.account_id = 1010 + request.account_id
        account1.account_type = 1111

        account2 = UserAccount()
        account2.user = user2
        account2.account_id = 2020 + request.account_id
        account2.account_type = 2222

        out.user_account_list = [account2, account1]
        self.response.payload = out

# ################################################################################################################################
# ################################################################################################################################

class HelperPubSubTarget(Service):
    """ Test support services - PubSubTarget.
    """
    name = 'helpers.pubsub.target'

    def handle(self):

        # Our request
        msg = self.request.raw_request # type: PubSubMessage

        # Whatever happens next, log what we received
        self.logger.info('I was invoked with %r', msg.to_dict())

        # .. load the inner dict ..
        data = msg.data # type: bytes

        # .. confirm what it was ..
        self.logger.info('Data is %r', data)

        # .. this is where we will save our input data ..
        file_name = data['file_name']

        # .. we will save the message as a JSON one ..
        json_msg = msg.to_json(needs_utf8_decode=True)

        # .. confirm what we will be saving and where ..
        self.logger.info('Saving data to file `%s` -> `%s`', file_name, json_msg)

        # .. and actually save it now.
        f = open_rw(file_name)
        f.write(json_msg)
        f.close()

# ################################################################################################################################
# ################################################################################################################################

class HelperPubSubHook(PubSubHook):
    """ Test support services - PubSubHook.
    """
    name = 'helpers.pubsub.hook'

    def before_publish(self):
        self.logger.info('Helpers before_publish; pub_msg_id:`%s`, data:`%s`',
            self.request.input.ctx.msg.pub_msg_id, self.request.input.ctx.msg.data)

# ################################################################################################################################
# ################################################################################################################################

class HelperPubSubSource(Service):
    """ Test support services - PubSubSource.
    """
    name = 'helpers.pubsub.source'

    class SimpleIO:
        input_required = 'random_data', 'file_name'

    def handle(self):
        self.pubsub.publish(HelperPubSubTarget, data=self.request.raw_request)

# ################################################################################################################################
# ################################################################################################################################
