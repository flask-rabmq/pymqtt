# pymqtt

pymqtt is a mqtt python client library extension meant to facilitate the integration of a MQTT client into your web application. Basically it is a thin wrapper around the paho-mqtt package to simplify MQTT integration in a python application. MQTT is a machine-to-machine (M2M)/”Internet of Things” (IoT) protocol which is designed as a lightweight publish/subscribe messaging transport. It comes very handy when trying to connect multiple IoT devices with each other or monitor and control these devices from one or multiple clients.


## Installing

Install and update using `pip`:

```
$ pip install -U pymqtt
```


## A Simple Example

```python
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
```