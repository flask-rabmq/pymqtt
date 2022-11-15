# -*- conding:utf -*-

import logging

from flask import Flask

from pymqtt import Mqtt

logging.basicConfig(format='%(asctime)s %(process)d,%(threadName)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config.setdefault('MQTT_IP', '127.0.0.1')
app.config.setdefault('MQTT_PORT', 1883)
app.config.setdefault('MQTT_USER', 'user')
app.config.setdefault('MQTT_PASSWORD', 'password')

fmqtt = Mqtt()
fmqtt.config_from_obj(app.config)


@app.route('/')
def hello_world():
    content = 'hello world'
    success = fmqtt.publish('hell world', 'topic', qos=2, retain=True)
    success = fmqtt.publish('hell world', 'topic', qos=2)
    return 'send %s success %s' % (content, success)


@fmqtt.subscribe(topic='topic', qos=2)
def flask_rabmq_test(body):
    logger.info("only one arg: %s", body)
    return True


@fmqtt.subscribe(topic='topic', qos=2)
def flask_rabmq_test(body, msg):
    """如果函数有两个参数，第一个参数是消息的payload, 第二个参数是消息的实例"""
    logger.info(body)
    logger.info(msg)
    return True


if __name__ == '__main__':
    fmqtt.run()
    app.run()
