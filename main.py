import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Queue, Process, cpu_count, Array
from socketserver import ThreadingMixIn
from config import *
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
        elif self.body['request']['intent']['name'] == 'Clova.GuideIntent':
            self.set_response(*self.Help())
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

    def Help(self):
        return 'SpeechList', ['금융비서는 관심종목 관리, 맞춤 금융 뉴스 진행, 종목 요약, 종목 뉴스 요약, 시장요약,  종목추천, 급변종목 최근뉴스 등에 대해 알려드릴 수 있어요.'] +\
                    ['미래에셋대우를 관심종목에 추가해줘, 미래에셋대우를 관심종목에서 제거해줘, 관심종목 알려줘라고 말해서 관심종목을 관리 하실 수 있고,'] + \
                   ['금융뉴스 진행해줘라고 말씀하시면 관심종목에 등록 된 종목들을 기반으로 뉴스를 진행해 드려요.'] + \
                    ['그 외에도 코스닥 시장 요약해줘'] + ['네이버 종목 요약해줘'] + ['삼성전자 뉴스 요약해줘'] +\
                    ['추천 종목 알려줘'] + ['가장 많이 떨어진 종목 알려줘와 같은 기능이 있어요.'] +\
                  ['자세한 사용방법을 알고 싶으시면 클로바 확장 서비스 관리, 금융비서에 들어가 보세요.'], False

    def stockSummary(self):
        try:
            name = self.body['request']['intent']['slots']['symbol']['value']
            code = symbol_dict[name]
        except (KeyError, TypeError) as e:
            code = None if 'code' not in locals() else code
            return self.no_symbol(code)

        in_queue.put(['stock_summary', [code, name], self.ix])
        _, out = out_queues[self.ix].get()
        if type(out[2][0]) == int or type(out[2][0]) == float:
            n = ['없어요']
        else:
            n = []
            print(len(out[2][0]))
            for i in range(len(out[2][0])):
                n += [out[2][0][i]]
            n += ['가 있어요'] + ['자세한 뉴스 내용을 알고 싶으면. {} 뉴스 요약해줘 라고 말해주세요'.format(name)]
        msg = ['{}의 현재 주가는 {}으로 전날 대비 등락률 {}를 기록하고 있어요.'.format(name, out[0][0], out[0][2]).replace('-', '마이너스')] +\
              ['{} 기준 수급은 기관 {}주 외국인 {}주에요.'.format(out[1][0], out[1][1], out[1][2]).replace('-', '마이너스')]+ \
              ['최근 3일간의 뉴스는'] + n
        return 'SpeechList', msg, False

    def marketSummary(self):
        market = self.body['request']['intent']['slots']['market']['value']
        in_queue.put(['market_summary', [market,], self.ix])
        out = out_queues[self.ix].get()
        msg = []

        if out[1].find("+") != -1:
            sign = "플러스"
        else:
            sign = "마이너스"

        msg += ['{} 시장을 요약해드릴게요.'.format(market)] + ['현재 지수는 {}이고 전날 대비 {}, 수치로는 {} {}만큼 변화했어요'.format(out[0], out[1].split(' ')[1], sign, out[1].split(' ')[0])] +\
                ['수급현황은 개인: {}, 외국인: {}, 기관: {}을 기록하고 있어요'.format(out[4], out[5], out[6]).replace('-', '마이너스')]
        return 'SpeechList', msg

    def Rise(self):
        in_queue.put(['rise_fall', ['rise'], self.ix])
        msg = self.__rise_fall('오른')
        return 'SpeechList', msg

    def Fall(self):
        in_queue.put(['rise_fall', ['fall'], self.ix])
        msg = self.__rise_fall('떨어진')
        return 'SpeechList', msg

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

        msg = ['코스피 중에서 가장 많이 {} 세 주식은 {}입니다. '.format(direction, ', '.join(valid_names))]
        #todo 뉴스리스트 한번에 넣고 코드별로 정리하게 하기
        for name, code in zip(valid_names, valid_list):
            in_queue.put(['stock_summary', [code, name], self.ix])
            _, out = out_queues[self.ix].get()
            if type(out[2][0]) == int or type(out[2][0]) == float:
                pass
            else:
                n = ['{}과 관련 된 최근 뉴스는 '.format(name)]
                print(len(out[2][0]))
                for i in range(len(out[2][0])):
                    n += [out[2][0][i]]
                msg += n
        msg += ['가 있어요.'] + ['자세한 뉴스 내용을 알고 싶으면. 종목이름과 함께 종목명 뉴스 요약해줘라고 말해주세요'.format(name)]
        return msg

    def stockRecommend(self):
        in_queue.put(['recommend', [1, ], self.ix])
        recommend = out_queues[self.ix].get()
        code_to_symbol = {v: k for k, v in symbol_dict.items()}
        if len(recommend) -- 0:
            return 'SimpleSpeech', '오늘의 증권사 신규 추천 종목이 없어요. 내일을 기다려봐요.'
        else:
            symbol_recommend = []
            for stock in recommend:
                try:
                    symbol_recommend.append(code_to_symbol[stock])
                except:
                    pass
            if len(symbol_recommend) == 0:
                return 'SimpleSpeech', '오늘의 증권사 신규 추천 종목이 없어요. 내일을 기다려봐요.'
            else:
                return 'SimpleSpeech', '오늘의 증권사 신규 추천 종목은 {}가 있어요.'.format(', '.join(symbol_recommend))

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
        in_queue.put(['recent_news', [symbol, NEWS_RECENT_DAY, MAX_NEWS_SUMMARY], self.ix])
        news_list = out_queues[self.ix].get()
        if type(news_list) != pd.DataFrame:
            return 'SimpleSpeech', '24시간 내에 관련 종목 뉴스가 없어요', True, None
        for kk, news in news_list.iterrows():
            in_queue.put(['do_summary', [news, SUMMARY_SENTENCES], self.ix])
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
