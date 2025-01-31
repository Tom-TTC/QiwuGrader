# -*- coding:utf-8 -*-
import requests
import json
from qiwugrader.model.basic_request import BasicRequest

from qiwugrader.grader.compatible import encode_str

__author__ = 'Feliciano'


class SingleDialogue(BasicRequest):

    DEFAULT_REPLY = u'我不知道。'
    RESULT_NONE_REPLY = u'我也没有得到答案。'
    ERROR_REPLY = u'好的。。'
    REQUEST_TIMEOUT = u'服务器连接超时'

    def __init__(self, service_config):
        super(SingleDialogue, self).__init__()

        server_config = service_config.get_config('server')

        self.protocol = server_config['protocol']
        self.host = server_config['host']
        self.port = server_config['port']
        self.endpoint = server_config['api']
        self.method = server_config.get('method', 'POST')

        request_config = service_config.get_config('request')

        self.payload = request_config['payload']
        self.threshold = request_config.get('threshold', None)
        self.answer_key = request_config.get('answer', 'reply')
        self.data_key = request_config.get('data', None)
        self.type = request_config.get('type', 'application/json')

        self.timeout = request_config.get('timeout', 5)

        self.url = self.to_uri()

    def chat(self, data, max_wait=None):
        if self.threshold and self.threshold > 1:
            return SingleDialogue.DEFAULT_REPLY

        payload = encode_str(self.payload % data)
        headers = {}

        if self.method == "POST":
            headers['content-type'] = self.type

        result = None
        try:
            if self.method == 'GET':
                r = requests.get(self.url, params=payload, headers=headers, timeout=max_wait or self.timeout)
            else:
                r = requests.post(self.url, data=payload, headers=headers, timeout=max_wait or self.timeout)
            result = r.json()
        except requests.exceptions.Timeout as e:
            self.logger.info(e.message)
            self.logger.error("request timeout {0} {1}:{2}".format(self.method, self.host, self.port))
            return SingleDialogue.REQUEST_TIMEOUT
        except ValueError:
            self.logger.info("error decoding: " + r.text)
            self.logger.error("request value error {0} {1}:{2}".format(self.method, self.host, self.port))
        except requests.exceptions.RequestException as e:
            self.logger.info(e.message)
            self.logger.error("request error {0} {1}:{2}".format(self.method, self.host, self.port))
        except Exception as e:
            self.logger.error("request exception {0} {1}:{2}".format(self.method, self.host, self.port))
            self.logger.exception(e)
            return SingleDialogue.ERROR_REPLY
        if result and self.answer_key in result:
            if not self.threshold:
                if self.data_key:
                    attach_data = None
                    if self.data_key == '.':
                        attach_data = result
                    elif self.data_key in result:
                        attach_data = result[self.data_key]
                    if attach_data:
                        return result[self.answer_key] + json.dumps(attach_data, ensure_ascii=False)
                return result[self.answer_key]
            else:
                if 'probability' in result and result['probability'] > self.threshold:
                    cut = result['reply'].find(' ( ')
                    if cut > -1:
                        return result[self.answer_key][:cut]
                    return result[self.answer_key]
        elif result is None:
            return SingleDialogue.RESULT_NONE_REPLY
        return SingleDialogue.DEFAULT_REPLY
