import http.server, ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from news2 import Clova_News
from data import summary_all
import os

class ClovaServer(BaseHTTPRequestHandler):
    def set_header(self):
        self.send_response(200, "OK")
        self.send_header('Content-type', 'application/json;charset-UTF-8')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        body = json.loads(post_data.decode('utf-8'))

        ## user_id로 저장된 정보를 불러옵니다.


        self.set_header()
        if body['request']['intent']['name'] == 'recentnews':
            symbol = body['request']['intent']['slots']['Symbol']['value']
            #회사명을 코드로 바꾸는 함수 필요
            symbol = '000880'
            news_list = chrome.recent_news(symbol)
            summaries = summary_all(news_list)
            summaries['speech_text'] = summaries['title'] + '\n' + summaries['summary']
            speech_text = '\n\n'.join(summaries['speech_text'])
            response_body = {'version':"", "sessionAttributes": None,
                             "response":
                                 {'outputSpeech':
                                      {"type":
                                           "SimpleSpeech",
                                       "values":
                                           {"lang":'ko', 'type':'PlainText', 'value':speech_text}},
                                  'directives':None, 'shouldEndSession':True}}
            self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))
        else:
            self.wfile.write('해당되는 항목이 없음'.encode('utf-8'))
def run(server_class=HTTPServer, handler_class=ClovaServer, port=80):
    global chrome
    chrome = Clova_News()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    #httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile='certificate.pem',
    #                               keyfile='key.pem', ssl_version=ssl.PROTOCOL_TLSv1)
    print("Server Started")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

run()