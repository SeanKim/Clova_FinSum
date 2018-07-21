from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from data import User
import pandas as pd
from News_reader import Clova_News
import time
from socketserver import ThreadingMixIn

class ClovaServer(BaseHTTPRequestHandler):
    def set_header(self):
        self.send_response(200, "OK")
        self.send_header('Content-type', 'application/json;charset-UTF-8')
        self.end_headers()

    def do_main(self):
        # do_main 함수는 json request 내 name과 똑같은 이름의 내부 함수를 실행하므로
        # 원하는 동작을 일으킬 함수는 그에 해당하는 intent와 똑같은 이름으로 정해줘야 함
        try:
            self.set_response(*getattr(self, self.body['request']['intent']['name'])())
            self.do_response()
        except AttributeError as e:
            print(str(e))
            #try:
            if self.body['request']['type'] == 'LaunchRequest':
                self.set_response('SimpleSpeech', '무엇을 도와드릴까요?', False, None, True, '도움말을 듣고 싶으시면 \"도움말 들려줘라고 말해 주세요.\"')
                self.do_response()
            #except:
             #   self.set_response('SimpleSpeech', '다시 한 번 말씀해 주세요', False, None)
              #  self.do_response()


        del self.speech_body, self.speech_type, self.shouldEndSession, self.sessionAttributes, self.user,\
            self.do_reprompt, self.reprompt_msg

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.set_header()
        post_data = self.rfile.read(content_length)
        self.body = json.loads(post_data.decode('utf-8'))
        # user_id로 저장된 정보를 불러옵니다.
        self.user = User(self.body['context']['System']['user']['userId'])
        self.do_main()
        print("response done")

    def set_response(self, *args):
        base_value = ['SimpleSpeech', '', True, None, False, '']
        args =list(args)
        base_ix = (len(base_value)-len(args))
        args = args + base_value[-base_ix:] if base_ix != 0 else args
        self.speech_type = args[0]
        self.speech_body = args[1]
        self.shouldEndSession = args[2]
        self.sessionAttributes = args[3]
        self.do_reprompt = args[4]
        self.reprompt_msg = args[5]

    def do_response(self):
        response_body = {'version': "", "sessionAttributes": self.sessionAttributes,
                         "response":
                             {'outputSpeech':
                                  {"type":
                                       self.speech_type,
                                   "values":
                                       None},
                              'directives': None,
                              'shouldEndSession': self.shouldEndSession}}

        if self.do_reprompt:
            response_body['response']['reprompt'] = {
                                                  "outputSpeech" : {
                                                    "type" : "SimpleSpeech",
                                                    "values" : {
                                                      "type" : "PlainText",
                                                      "lang" : "ko",
                                                      "value" : self.reprompt_msg
                                                    }
                                                  }
                                                }

        if self.speech_type == 'SimpleSpeech':
            response_body['response']['outputSpeech']['values'] = {"lang": 'ko', 'type': 'PlainText',
                                                               'value': self.speech_body}
        elif self.speech_type == 'SpeechList':
            response_body['response']['outputSpeech']['values'] = \
                [{'type': 'PlainText', 'lang':'ko', 'value':v} for v in self.speech_body]

        self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))

    def no_symbol(self, symbol, sessionAttributes=None):
        if symbol == None:
            return 'SimpleSpeech', '해당하는 종목이 없습니다. 코스피 혹은 코스닥시장에 상장 된 종목만 가능합니다. 다시 말씀해 주세요.', False, sessionAttributes
        else:
            simmilars = []
            [simmilars.append(key) if symbol in key else None for key in symbol_dict.keys()]
            if len(simmilars) == 0:
                return 'SimpleSpeech', '해당하는 종목이 없습니다. 코스피 혹은 코스닥시장에 상장 된 종목만 가능합니다. 다시 말씀해 주세요.', False, sessionAttributes
            else:
                return 'SimpleSpeech', symbol + '이 들어가는 종목은 ' +', '.join(simmilars) + '이 있습니다. 이 중 하나를 말씀해 주세요.', False, sessionAttributes

    def addFavorite(self):
        try:
            symbol = self.body['request']['intent']['slots']['symbol']['value']
            symbol_code = symbol_dict[symbol]
        except (KeyError, TypeError) as e:
            symbol = None if 'symbol' not in locals() else symbol
            return self.no_symbol(symbol, sessionAttributes={'name':'addFavorite'})
        self.user.data = self.user.data.append(pd.Series([symbol_code]))
        self.user.save_data()
        return 'SimpleSpeech', symbol + '가 관심종목에 추가되었습니다. 계속 추가를 원하시면 종목 이름을 말씀해 주세요.', False, {'name':'addFavorite'}

    def ing(self):
        try:
            if self.body['session']['sessionAttributes'] == None:
                pass
            #도움말 띄우기 미구현
        except KeyError:
            self.set_response(*getattr(self, self.body['session']['sessionAttributes']['name'])())


    def recentNews(self):
        # 3문장으로 요약하도록 해 두었음, 결과가 적절하지 않을 시 수정 요망
        try:
            symbol = self.body['request']['intent']['slots']['symbol']['value']
            symbol = symbol_dict[symcbol]
        except (KeyError, TypeError) as e:
            symbol = None if 'symbol' not in locals() else symbol
            return self.no_symbol(symbol)
        news_list = chrome.recent_news(symbol)
        if type(news_list) != pd.DataFrame:
            return 'SimpleSpeech', '24시간 내에 관련 종목 뉴스가 없어요', True, None
        summaries = chrome.summary_all(news_list)
        speech_list = [[v['title'], v['summary'], '다음 뉴스입니다.'] for i,v in summaries.iterrows()]
        speech_text = []
        # Speech List이므로 딕셔너리의 리스트를 할당
        # https://developers.naver.com/console/clova/guide/CEK/References/CEK_API.md#CustomExtSpeechInfoObject
        for ll in speech_list:
            speech_text += ll
        return 'SpeechList', ['뉴스를 요약해 드릴게요'] + speech_text[:-1], True, None


def run(handler_class=ClovaServer, port=80):\
    #threading
    class server_class(ThreadingMixIn, HTTPServer):
        pass
    global chrome
    global symbol_dict
    symbol_dict = pd.read_csv('symbols.csv', index_col='Name', dtype=str).to_dict()['Code']
    chrome = Clova_News()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    # httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile='certificate.pem',
    #                               keyfile='key.pem', ssl_version=ssl.PROTOCOL_TLSv1)
    print("Server Started")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


run()