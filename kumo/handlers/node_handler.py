# Copyright (c) 2021 Ichiro ITS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import rclpy
from rclpy.logging import get_logger
from rosidl_runtime_py.utilities import get_message

from kumo.handlers.base_handler import BaseHandler
from kumo.handlers.publisher_handler import PublisherHandler
from kumo.handlers.subscription_handler import SubscriptionHandler
from kumo.message import Message, MessageType


class NodeHandler(BaseHandler):

    def __init__(self, name: str):
        super().__init__()

        self.node = rclpy.create_node(name)

        self.logger = get_logger('node_handler')

    def destroy(self) -> bool:
        if super().destroy():
            self.logger.warn('Destroying node %s...' % self.id)
            self.node.destroy_node()

    async def process(self) -> None:
        try:
            rclpy.spin_once(self.node, timeout_sec=0.01)

        except Exception as e:
            self.logger.error('Failed to spin node %s! %s' % (id, e))

        await super().process()

    async def handle_message(self, message: Message) -> None:

        if message.type == MessageType.DESTROY_NODE:
            try:
                return self.handle_destroy_node(message)

            except Exception as e:
                self.logger.error('Failed to destroy node %s! %s' % (self.id, str(e)))
                self.send_error_respond(message, e)

        elif message.type == MessageType.CREATE_PUBLISHER:
            try:
                return self.handle_create_publisher(message)

            except Exception as e:
                self.logger.error('Failed to create a publisher! %s' % str(e))
                self.send_error_respond(message, e)

        elif message.type == MessageType.CREATE_SUBSCRIPTION:
            try:
                return self.handle_create_subscription(message)

            except Exception as e:
                self.logger.error('Failed to create a subscription! %s' % str(e))
                self.send_error_respond(message, e)

        await super().handle_message(message)

    def handle_destroy_node(self, message: Message) -> None:
        if message.content.get('node_id') == self.id:
            self.destroy()
            self.send_respond(message, {'node_id': self.id})

    def handle_create_publisher(self, message: Message) -> None:
        if message.content.get('node_id') == self.id:
            publisher = PublisherHandler(
                self.node, get_message(message.content.get('message_type')),
                message.content.get('topic_name'))

            self.attach(publisher)

            self.logger.info('Publisher %s created!' % publisher.id)
            self.send_respond(message, {'publisher_id': publisher.id})

    def handle_create_subscription(self, message: Message) -> None:
        if message.content.get('node_id') == self.id:
            subscription = SubscriptionHandler(
                self.node, get_message(message.content.get('message_type')),
                message.content.get('topic_name'))

            self.attach(subscription)

            self.logger.info('Subscription %s created!' % subscription.id)
            self.send_respond(message, {'subscription_id': subscription.id})
