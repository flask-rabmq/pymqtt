# -*- coding:utf8 -*-
import traceback
import sys
import time
import logging
import datetime
import importlib
from functools import update_wrapper
from paho.mqtt.client import Client


# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

logger = logging.getLogger(__name__)


def setup_method(f):
    def wrapper_func(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return update_wrapper(wrapper_func, f)


class Mqtt(object):

    def __del__(self):
        logger.info('stop loop')
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

    def __init__(self, ip=None, port=None, user=None, password=None, client_id=None):
        self.mqtt_ip = ip
        self.mqtt_port = port
        self.mqtt_user = user
        self.mqtt_password = password
        self.mqtt_client_id = client_id
        self.connect_status = False
        self.mqtt_client = False
        self.subscribe_callback = {}
        self.publish_mid = {}
        self.subscribe_status = False
        self.current_subscribe_topic = None
        self.fist_connect = None

    def run(self):
        self.mqtt_ip = self.mqtt_ip or self.config.get('MQTT_IP') or '127.0.0.1'
        self.mqtt_port = self.mqtt_port or self.config.get('MQTT_PORT') or 1883
        self.mqtt_user = self.mqtt_user or self.config.get('MQTT_USER')
        self.mqtt_password = self.mqtt_password or self.config.get('MQTT_PASSWORD')
        self.mqtt_client_id = self.mqtt_client_id or self.config.get('MQTT_CLIENT_ID')
        self.mqtt_client = self.mqtt_client or Client(self.mqtt_client_id)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_publish = self.on_publish
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_client.on_message = self.on_message
        self.connect()
        self.start_subscribe()

    def config_from_obj(self, obj):
        if is_py3 and isinstance(obj, str):
            mod = importlib.import_module(obj)
            self.config = mod.__dict__
        elif is_py2 and isinstance(obj, (str, eval('unicode'))):
            mod = importlib.import_module(obj)
            self.config = mod.__dict__
        elif isinstance(obj, dict):
            self.config = obj
        else:
            self.config = obj.__dict__

    def start_subscribe(self):
        for topic in self.subscribe_callback:
            self.subscribe_status = False
            self.current_subscribe_topic = topic
            if self.subscribe_callback[topic].get('is_share'):
                share_topic = '$queue/%s' % topic
            else:
                share_topic = None
            _, mid = self.mqtt_client.subscribe(topic=share_topic or topic, qos=self.subscribe_callback[topic].get('qos'))
            while not self.subscribe_status and self.fist_connect is None:
                self.mqtt_client.subscribe(topic=share_topic or topic, qos=self.subscribe_callback[topic].get('qos'))
                time.sleep(0.1)

    def subscribe(self, topic, qos=0, is_share=True):
        def decorator(f):
            self.add_subscribe_rule(f, topic, qos, is_share=is_share)
            return f
        return decorator

    @setup_method
    def add_subscribe_rule(self, func, topic, qos, is_share=True):
        self.subscribe_callback[topic] = {'func': func, 'qos': qos, 'is_share': is_share}

    def on_connect(self, client, userdata, flags, rc):
        logger.info('connect success')
        self.connect_status = True
        if self.fist_connect is False:
            self.start_subscribe()

    def on_publish(self, client, userdata, mid):
        logger.info('publish mid: ' + str(mid) + ' success')
        self.publish_mid.get(mid) and self.publish_mid[mid].update({'status': True})

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logger.info('subscribe %s success mid: %s' % (self.current_subscribe_topic, mid))
        self.subscribe_status = True
        self.fist_connect = False

    def on_disconnect(self, client, userdata, rc):
        logger.info('mqtt(%s:%s) disconnect' % (self.mqtt_ip, self.mqtt_port))
        logger.info('mqtt(%s:%s) reconnect' % (self.mqtt_ip, self.mqtt_port))

    def on_message(self, client, userdata, msg):
        logger.info("Received message, topic: %s,payload: %s" % (msg.topic, str(msg.payload)))
        topic = msg.topic
        content = msg.payload
        func = self.subscribe_callback.get(topic).get('func')
        if func:
            try:
                result = func(content)
            except Exception as E:
                logger.error(traceback.format_exc())
                result = None
        else:
            result = None
        logger.info('handler result: %s' % result)

    def connect(self):
        if not self.mqtt_client:
            raise Exception('请初始化')
        self.mqtt_client.connect(self.mqtt_ip, self.mqtt_port, keepalive=2)
        if self.mqtt_user and self.mqtt_password:
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        # 启动
        self.mqtt_client.loop_start()
        while not self.connect_status:
            logger.info('mqtt(%s:%s) connecting' % (self.mqtt_ip, self.mqtt_port))
            time.sleep(0.1)

    def clean_publish_mid(self):
        mids = [x for x in self.publish_mid.keys()]
        for mid in mids:
            if self.publish_mid.get(mid, {}).get('expire') < datetime.datetime.now():
                self.publish_mid.pop(mid, None)

    def publish(self, content, topic, qos=0):
        _, mid = self.mqtt_client.publish(topic=topic, qos=qos, payload=content)
        self.publish_mid[mid] = {'status': False, 'expire': datetime.datetime.now() + datetime.timedelta(seconds=5)}
        while self.publish_mid.get(mid) and self.publish_mid.get(mid)['status'] is False:
            self.clean_publish_mid()
            time.sleep(0.1)
        return mid in self.publish_mid

