import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Queue, Process, cpu_count, Array
from socketserver import ThreadingMixIn

import pandas as pd

from Browser import Clova_News
from data import User
from collections import defaultdict

class ClovaServer(BaseHTTPRequestHandler):
    def set_header(self):
        self.send_response(200, "OK")
        self.send_header('Content-type', 'application/json;charset-UTF-8')
        self.end_headers()

    def do_main(self):
        self.user = None
        self.ix = self.reserving_queue()
        # do_main 함수는 json request 내 name과 똑같은 이름의 내부 함수를 실행하므로
        # 원하는 동작을 일으킬 함수는 그에 해당하는 intent와 똑같은 이름으로 정해줘야 함
        # try:
        if self.body['request']['type'] == 'LaunchRequest':
            self.set_response(
            *('SimpleSpeech', '무엇을 도와드릴까요?', False, None, True, '도움말을 듣고 싶으시면 \"도움말 들려줘라고 말해 주세요.\"'))
            self.do_response()
        else:
            self.set_response(*getattr(self, self.body['request']['intent']['name'])())
            self.do_response()
        # except (AttributeError, TypeError) as e:
        #     try:
        #         if self.body['request']['type'] == 'LaunchRequest':
        #             self.set_response(
        #                 *('SimpleSpeech', '무엇을 도와드릴까요?', False, None, True, '도움말을 듣고 싶으시면 \"도움말 들려줘라고 말해 주세요.\"'))
        #             self.do_response()
        #         else:
        #             self.set_response(*('SimpleSpeech', '다시 한 번 말씀해 주세요', False, None))
        #             self.do_response()
        #     except:
        #         self.set_response(*('SimpleSpeech', '다시 한 번 말씀해 주세요', False, None))
        #         self.do_response()

        del self.speech_body, self.speech_type, self.shouldEndSession, self.sessionAttributes, \
            self.do_reprompt, self.reprompt_msg
        flags[self.ix] = 0

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.set_header()
        post_data = self.rfile.read(content_length)
        self.body = json.loads(post_data.decode('utf-8'))
        self.do_main()
        print("response done")

    def set_response(self, *args):
        base_value = ['SimpleSpeech', '', True, None, False, '']
        args = list(args)
        base_ix = (len(base_value) - len(args))
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
                "outputSpeech": {
                    "type": "SimpleSpeech",
                    "values": {
                        "type": "PlainText",
                        "lang": "ko",
                        "value": self.reprompt_msg
                    }
                }
            }

        if self.speech_type == 'SimpleSpeech':
            response_body['response']['outputSpeech']['values'] = {"lang": 'ko', 'type': 'PlainText',
                                                                   'value': self.speech_body}
        elif self.speech_type == 'SpeechList':
            response_body['response']['outputSpeech']['values'] = \
                [{'type': 'PlainText', 'lang': 'ko', 'value': v} for v in self.speech_body]

        self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))

    def reserving_queue(self):
        ix = None
        while ix == None:
            for i, v in enumerate(flags):
                if v == 0:
                    flags[i] = 1
                    ix = i
                    break
        return ix

    def no_symbol(self, symbol, sessionAttributes=None):
        if symbol == None:
            return 'SimpleSpeech', '해당하는 종목이 없습니다. 코스피 혹은 코스닥시장에 상장 된 종목만 가능합니다. 다시 말씀해 주세요.', False, sessionAttributes
        else:
            simmilars = []
            [simmilars.append(key) if symbol in key else None for key in symbol_dict.keys()]
            if len(simmilars) == 0:
                return 'SimpleSpeech', '해당하는 종목이 없습니다. 코스피 혹은 코스닥시장에 상장 된 종목만 가능합니다. 다시 말씀해 주세요.', False, sessionAttributes
            else:
                return 'SimpleSpeech', symbol + '이 들어가는 종목은 ' + ', '.join(
                    simmilars) + '이 있습니다. 이 중 하나를 말씀해 주세요.', False, sessionAttributes

    def Rise(self):
        in_queue.put(['rise_fall', ['rise'], self.ix])
        msg = self.__rise_fall('오른')
        return 'SimpleSpeech', msg

    def Fall(self):
        in_queue.put(['rise_fall', ['fall'], self.ix])
        msg = self.__rise_fall('떨어진')
        return 'SimpleSpeech', msg

    def __rise_fall(self, direction):
        name_list = out_queues[self.ix].get()
        valid_list = []
        valid_names = []
        i = 0
        for name in name_list[0]:
            try:
                valid_list.append(symbol_dict[name])
                valid_names.append(name)
                i += 1
                if i == 3:
                    break
            except:
                pass

        msg = '코스피 중에서 가장 많이 {} 세 주식은 {}입니다. '.format(direction, ', '.join(valid_names))
        #todo 뉴스리스트 한번에 넣고 코드별로 정리하게 하기
        for n, code in enumerate(valid_list):
            in_queue.put(['recent_news', [code, 1], self.ix])
            news_list = out_queues[self.ix].get()
            if type(news_list) != pd.DataFrame:
                pass
            else:
                word_df = None
                for ii, news in news_list.iterrows():
                    in_queue.put(['count_words', [news], self.ix])
                kk = 0
                while kk < len(news_list):
                    if type(word_df) != pd.DataFrame:
                        word_df = out_queues[self.ix].get()
                        kk += 1
                    else:
                        word_df = word_df + out_queues[self.ix].get()
                        kk += 1
                msg += '{}와 관련되어 가장 언급이 많이 된 단어 다섯가지는 {},'.format(valid_names[n], ', '.join(
                    list(word_df.sort_values('count', ascending=False).index[:5].values)))
        msg += '입니다'
        return msg

    def stockRecommend(self):
        in_queue.put(['recommend', [None], self.ix])
        recommend = out_queues[self.ix].get()
        code_to_symbol = {v: k for k, v in symbol_dict.items()}

        symbol_recommend = []
        for stock in recommend:
            try:
                symbol_recommend.append(code_to_symbol[stock])
            except:
                pass
            if len(symbol_recommend) == 5:
                break
        return 'SimpleSpeech', '최근 한달간 애널리스트가 가장 많이 추천한 종목은 {} 입니다'.format(', '.join(symbol_recommend))

    def morningNews(self):
        pass
        # 전날 상승종목 하락종목 워드클라우드
        # 전날 장 요약, 수급 요약
        # 관심종목 별 뉴스

    def currentFavorite(self):
        self.user = User(self.body['context']['System']['user']['userId'])
        code_to_symbol = {v: k for k, v in symbol_dict.items()}
        cfs = ', '.join([code_to_symbol[symbol] for symbol in self.user.data['symbol']])
        print(self.user.data)
        return 'SimpleSpeech', '현재 관심종목은 {}입니다'.format(cfs), True, None

    def removeFavorite(self):
        self.user = User(self.body['context']['System']['user']['userId'])
        try:
            symbol = self.body['request']['intent']['slots']['symbol']['value']
            symbol_code = symbol_dict[symbol]
        except (KeyError, TypeError) as e:
            symbol = None if 'symbol' not in locals() else symbol
            return self.no_symbol(symbol, sessionAttributes={'name': 'addFavorite'})
        self.user.data = self.user.data.loc[self.user.data['symbol'] != symbol_code, :].dropna()
        self.user.save_data()
        return 'SimpleSpeech', symbol + '를 관심종목에서 제거하였습니다. 계속 제거를 원하시면 종목 이름을 말씀해 주세요.', False, {'name': 'removeFavorite'}

    def addFavorite(self):
        self.user = User(self.body['context']['System']['user']['userId'])
        try:
            symbol = self.body['request']['intent']['slots']['symbol']['value']
            symbol_code = symbol_dict[symbol]
        except (KeyError, TypeError) as e:
            symbol = None if 'symbol' not in locals() else symbol
            return self.no_symbol(symbol, sessionAttributes={'name': 'addFavorite'})
        if symbol_code in self.user.data['symbol'].values:
            return 'SimpleSpeech', '이미 추가 되어 있는 종목입니다. 계속 추가를 원하시면 종목 이름을 말씀해 주세요.', False, {'name':'addFavorite'}
        else:
            self.user.data = self.user.data.append(pd.DataFrame([symbol_code], columns=['symbol']))
            print(self.user.data)
            self.user.save_data()
            return 'SimpleSpeech', symbol + '가 관심종목에 추가되었습니다. 계속 추가를 원하시면 종목 이름을 말씀해 주세요.', False, {'name': 'addFavorite'}

    def ing(self):
        try:
            if self.body['session']['sessionAttributes'] == None:
                pass
            # 도움말 띄우기 미구현
        except KeyError:
            # durltj dpfjskaus eocjgoidehla
            self.set_response(*getattr(self, self.body['session']['sessionAttributes']['name'])())

    def recentNews(self):
        # 3문장으로 요약하도록 해 두었음, 결과가 적절하지 않을 시 수정 요망
        try:
            symbol = self.body['request']['intent']['slots']['symbol']['value']
            symbol = symbol_dict[symbol]
        except (KeyError, TypeError) as e:
            symbol = None if 'symbol' not in locals() else symbol
            return self.no_symbol(symbol)
        in_queue.put(['recent_news', [symbol, 1], self.ix])
        news_list = out_queues[self.ix].get()
        if type(news_list) != pd.DataFrame:
            return 'SimpleSpeech', '24시간 내에 관련 종목 뉴스가 없어요', True, None
        for kk, news in news_list.iterrows():
            in_queue.put(['do_summary', [news, ], self.ix])
        summaries = pd.DataFrame(columns=['title', 'summary'])
        while len(summaries) < len(news_list):
            summaries = summaries.append(out_queues[self.ix].get())
        speech_list = [[v['title'], v['summary'], '다음 뉴스입니다.'] for i, v in summaries.iterrows()]
        speech_text = []
        # Speech List이므로 딕셔너리의 리스트를 할당
        # https://developers.naver.com/console/clova/guide/CEK/References/CEK_API.md#CustomExtSpeechInfoObject
        for ll in speech_list:
            speech_text += ll
        return 'SpeechList', ['뉴스를 요약해 드릴게요'] + speech_text[:-1], True, None


def set_env(n_processes=cpu_count()):
    global in_queue, out_queues, flags, chromes, symbol_dict
    in_queue = Queue()
    out_queues = [Queue() for i in range(n_processes)]
    flags = Array('i', n_processes)
    print('{}개의 셀레니움을 시작 중입니다.'.format(n_processes))
    chromes = [Process(target=Clova_News, args=(in_queue, out_queues, i)) for i in range(n_processes)]
    [c.start() for c in chromes]
    symbol_dict = pd.read_csv('symbols.csv', index_col='Name', dtype=str).to_dict()['Code']


class server_class(ThreadingMixIn, HTTPServer):
    pass


def run(handler_class=ClovaServer, port=80): \
        # threading
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


if __name__ == '__main__':
    print('because of low processing power, number of processes is set as 2.')
    set_env(2)
    run()
