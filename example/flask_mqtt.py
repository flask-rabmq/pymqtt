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
    success = fmqtt.publish('hell world', 'topic', qos=2)
    return 'send %s success %s' % (content, success)


@fmqtt.subscribe(topic='topic', qos=2)
def flask_rabmq_test(body):
    logger.info(body)
    return True


if __name__ == '__main__':
    fmqtt.run()
    app.run()
