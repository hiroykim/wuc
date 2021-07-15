#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
from importlib import \
  reload  # In Python 2.x, this was a builtin, but in 3.x, it's in the importlib module.

reload(sys)
# sys.setdefaultencoding('utf-8') # the default on Python 3 is UTF-8 already

__EXE_PATH__ = os.path.realpath(sys.argv[0])
__BIN_PATH__ = os.path.dirname(__EXE_PATH__)
__LIB_PATH__ = os.path.realpath(__BIN_PATH__ + '/../lib/python')
# sys.path.append(__LIB_PATH__)
__ONE_DAY_IN_SECONDS__ = 60 * 60 * 24

__MAUM_ROOT_LIB_PATH__ = os.path.join(os.getenv('MAUM_ROOT'), 'lib/python')
sys.path.append(__MAUM_ROOT_LIB_PATH__)
sys.path.append(os.path.realpath(sys.argv[0] + '/../voice_bot'))

# Basic lib import
from concurrent import futures
from datetime import date, timedelta, datetime
import argparse
import grpc
import time
import socketio

import logging
import logging.handlers

# pb import
from google.protobuf import empty_pb2
from google.protobuf import struct_pb2 as struct
from maum.m2u.da.v3 import talk_pb2
from maum.m2u.da.v3 import talk_pb2_grpc
from maum.m2u.da import provider_pb2
from maum.m2u.facade import userattr_pb2, types_pb2

from voice_bot.ai_da_lib.maumsds import MaumSds
from voice_bot.ai_da_lib.dbconnector import DbConnector
from voice_bot.ai_da_lib import logger
from voice_bot.config.config import DaConfig
from voice_bot.config.config import HCallMysqlConfig
from voice_bot.config.config import HCallMysqlConfigDev
from voice_bot.config.config import SimpleBotMaumSdsConfig
from voice_bot.config.config import SimpleBotMaumSDSConfigLocal
from voice_bot.config.config import SimpleSocketConfig

from voice_bot.ai_check_info.check_lib.common import Common
# 메리츠화재 IMPORT
sys.path.append('/srv/maum/code')
sys.path.append('/appl/maum')
import da
from cfg import config
common = Common()


def init_meta(intent='', msg_code=''):
  res_meta = struct.Struct()
  res_meta['tts_tempo'] = DaConfig.tts_tempo
  # res_meta['intent'] = intent
  # res_meta['msg_code'] = msg_code
  res_meta['delimiter'] = '|'
  return res_meta


class DAMainServer(talk_pb2_grpc.DialogAgentProviderServicer):
  # state = provider_pb2.DIAG_STATE_IDLE
  init_param = provider_pb2.InitParameter()
  # session_update 담길 session_update_entity
  session_update_entity = {}
  logger = logging.getLogger('SUMMER_SIMPLE_BOT')
  sds_host = 5 # default host

  def __init__(self):
    self.state = provider_pb2.DIAG_STATE_IDLE
    if not os.path.exists(DaConfig.log_dir_path):
      os.makedirs(DaConfig.log_dir_path)
    self.logger = logger.get_timed_rotating_logger(
        logger_name=DaConfig.logger_name,
        log_dir_path=DaConfig.log_dir_path,
        log_file_name=DaConfig.log_file_name,
        backup_count=DaConfig.log_backup_count,
        log_level=DaConfig.log_level
    )
    self.logger.setLevel(logging.DEBUG)
    self.logger.info('===================== CONFIG START =====================')
    self.logger.info('[__EXE_PATH__] {0}'.format(__EXE_PATH__))
    self.logger.info('[__BIN_PATH__] {0}'.format(__BIN_PATH__))
    self.logger.info('[__LIB_PATH__] {0}'.format(__LIB_PATH__))
    # self.logger.info(
    #   '[__ONE_DAY_IN_SECONDS__] {0}'.format(__ONE_DAY_IN_SECONDS__))
    self.logger.info('[log.file.name] {}/{}'.format(DaConfig.log_dir_path,
                                                    DaConfig.log_file_name))
    self.logger.info('=====================  CONFIG END  =====================')
    self.socket_url = '{0}:{1}'.format(SimpleSocketConfig.host,
                                  SimpleSocketConfig.port)
    self.sio = socketio.Client(ssl_verify=False)
    self.logger.info('self.socket_url {0}'.format(self.socket_url))
    self.sio.connect(self.socket_url)
    # session_id dict
    self.session_id_dict = dict()
    # DB session dict
    self.db_session_dict = dict()


  def IsReady(self, empty, context):
    self.logger.debug('>>>>>> IsReady called')
    status = provider_pb2.DialogAgentStatus()
    status.state = self.state
    return status

  def Init(self, init_param, context):
    self.logger.debug('>>>>>> Init called')
    self.state = provider_pb2.DIAG_STATE_INITIALIZING

    # direct method
    self.state = provider_pb2.DIAG_STATE_RUNNING
    # copy all
    self.init_param.CopyFrom(init_param)
    # self.db_conn = DbConnector(HCallMysqlConfigDev)
    self.db_conn = DbConnector(HCallMysqlConfig)

    # PROVIDER
    provider = provider_pb2.DialogAgentProviderParam()
    provider.name = 'DA'
    provider.description = 'Hi, DA dialog agent'
    provider.version = '0.1'
    provider.single_turn = True
    provider.agent_kind = provider_pb2.AGENT_SDS
    provider.require_user_privacy = True
    self.logger.debug('[Init] end')
    return provider

  def Terminate(self, empty, context):
    self.logger.debug('>>>>>> Terminate called')
    # do nothing
    self.state = provider_pb2.DIAG_STATE_TERMINATED
    return empty_pb2.Empty()

  def GetUserAttributes(self, request, context):
    self.logger.debug('>>>>>> GetUserAttributes called')
    result = userattr_pb2.UserAttributeList()
    attrs = []

    # UserAttribute의 name은 DialogAgentProviderParam의 user_privacy_attributes에
    # 정의한 이름과 일치해야 한다.
    # 이 속성은 사용자의 기본 DB 외에 정의된 속성 외에 추가적으로 필요한
    # 속성을 정의하는 것입니다.
    # Sample 예제

    lang = userattr_pb2.UserAttribute()
    lang.name = 'lang'
    lang.title = '기본 언어 설정'
    lang.type = types_pb2.DATA_TYPE_STRING
    lang.desc = '기본으로 사용할 언어를 지정해주세요.'
    attrs.append(lang)

    result.attrs.extend(attrs)
    return result

  def GetRuntimeParameters(self, empty, context):
    self.logger.debug('>>>>>> GetRuntimeParameters called')
    result = provider_pb2.RuntimeParameterList()
    params = []
    # Sample 예제

    db_host = provider_pb2.RuntimeParameter()
    db_host.name = 'db_host'
    db_host.type = types_pb2.DATA_TYPE_STRING
    db_host.desc = 'Database Host'
    db_host.default_value = ' '
    db_host.required = True
    params.append(db_host)

    db_pwd = provider_pb2.RuntimeParameter()
    db_pwd.name = 'db_pwd'
    db_pwd.type = types_pb2.DATA_TYPE_AUTH
    db_pwd.desc = 'Database Password'
    db_pwd.default_value = ' '
    db_pwd.required = True
    params.append(db_pwd)

    return result

  def GetProviderParameter(self, empty, context):
    self.logger.debug('>>>>>> GetProviderParameter called')
    provider = provider_pb2.DialogAgentProviderParam()
    provider.name = 'DA'
    provider.description = 'Hi, DA dialog agent'
    provider.version = '0.1'
    provider.single_turn = True
    provider.agent_kind = provider_pb2.AGENT_SDS
    provider.require_user_privacy = True
    return provider

  def OpenSession(self, request, context):
    self.logger.debug('>>>>>> OpenSession called')
    # self.logger.debug(request)
    result = talk_pb2.TalkResponse()

    session_id = request.session.id
    simplebot_id = request.utter.meta.fields.get('simplebot.id')
    simplebot_id = simplebot_id.string_value if simplebot_id is not None else None
    contract_no = request.utter.meta.fields.get('contract_no')
    contract_no = contract_no.string_value if contract_no is not None else None
    campaign_id = request.utter.meta.fields.get('campaign_id')
    campaign_id = campaign_id.string_value if campaign_id is not None else None

    # sds = MaumSds(SimpleBotMaumSDSConfigLocal, self.logger)
    sds = MaumSds(SimpleBotMaumSdsConfig, self.logger)

    # 심플봇 테스트 케이스
    simplebot_id, host, entity_list = self.get_simplebot_cust_info(simplebot_id, contract_no)

    # 실 음성봇 테스트 케이스
    if host is None and campaign_id is not None:
      host = self.get_sds_host(campaign_id)
      entity_list = self.get_cust_info(campaign_id, contract_no)

    # M2U test-chat 케이스 : test용 host
    if host is None: host = self.sds_host

    self.logger.debug('[OpenSession] SESSION ID: {}'.format(str(session_id)))
    self.logger.debug('[OpenSession] CONTRACT NO: {}'.format(contract_no))
    self.logger.debug('[OpenSession] SIMPLEBOT ID: {}'.format(simplebot_id))
    self.logger.debug('[OpenSession] MAUM-SDS HOST: {}'.format(host))

    if entity_list is None: entity_list = []
    entity_list.append({'entityName': 'INPUT', 'entityValue': 'aaa'})

    sds.host = host
    # answer = '안녕하세요 Maum-sds 연동된 음성봇 개발 챗봇입니다. '\
    #          '테스트용 maum-sds 에서 받아온 결과로 답변을 드리겠습니다.'
    answer, _i, res_content = sds.call_maum_sds('처음으로', session_id, sds.TYPE_INTENT, entity_list)

    res_meta = struct.Struct()
    result.response.meta.CopyFrom(res_meta)
    result.response.speech.utter = answer

    # session 정보 ,session data 10k
    result.response.session_update.id = session_id
    res_context = struct.Struct()
    res_context['session_data'] = str(self.session_update_entity)
    result.response.session_update.context.CopyFrom(res_context)
    # session id 제거
    # session id dict 생성.
    self.session_id_dict[session_id] = datetime.now()
    # DB 연결

    self.logger.debug('DB Connect [Session id: {0}]'.format(session_id))
    self.db_session_dict[session_id] = da.connect_db(self.logger, 'MYSQL', config.MYConfig)
    for session_id, create_time in self.session_id_dict.items():
      if (datetime.now() - create_time).seconds > 7200:
        self.logger.debug('Delete session id dict [session_id: {0}]'.format(session_id))
        del self.session_id_dict[session_id]
        if session_id in self.db_session_dict:
          try:
            self.db_session_dict[session_id].disconnect()
          except Exception:
            self.logger.debug('DB already disconnect [session_id: {0}]'.format(session_id))
          self.logger.debug('Delete DB session dict [session_id: {0}]'.format(session_id))
          del self.db_session_dict[session_id]
    return result

  def OpenSkill(self, request, context):
    self.logger.debug('>>>>>> OpenSkill called')
    # self.logger.debug('[OpenSkill] Open request: {}'.format(str(request)))
    result = talk_pb2.TalkResponse()
    return result

  def CloseSkill(self, request, context):
    self.logger.debug('>>>>>> CloseSkill called')
    self.logger.debug(request)
    self.logger.debug('=====================')
    self.logger.debug(context)
    result = talk_pb2.CloseSkillResponse()
    return result

  def Event(self, req, context):
    self.logger.debug('>>>>>>  Event called')
    # req = talk_pb2.EventRequest()
    answer = 'DA-maum-sds 에서는 Event를 지원하지 않고 있습니다.'
    event_res = talk_pb2.TalkResponse()
    event_res.response.speech.utter = answer
    event_res.response.close_skill = True
    return event_res

  def Talk(self, req, context):

    self.logger.debug('>>>>>> Talk called')
    self.logger.info('Talk request : {}'.format(req))
    mysql_db = self.db_session_dict[req.session.id]
    ##########################################################################
    ### req에서 utter, contract_no 등 가져오기
    ##########################################################################
    talk_res = talk_pb2.TalkResponse()
    sds = MaumSds(SimpleBotMaumSdsConfig, self.logger)

    campaign_id = None
    pre_intent = None
    is_tts = None
    call_id = None
    contract_no = None
    simplebot_id = None
    checked_voicemail = None
    intent_repeat_cnt = None


    today = date.today()
    month_after = today.replace(day=1) + timedelta(days=1)
    month = str(month_after.month)
    res_meta = init_meta()
    utter = req.utter.utter
    max_turn = None
    task_over_max = None
    current_utter = None

    if req.session.context.fields.get('pre_intent') is not None:
      pre_intent = str(req.session.context.fields['pre_intent'].string_value)
    if req.utter.meta.fields.get('contract_no') is not None:
      contract_no = str(req.utter.meta.fields['contract_no'].string_value)
    if req.utter.meta.fields.get('doing_tts') is not None:
      is_tts = str(req.utter.meta.fields['doing_tts'].string_value)
    if req.utter.meta.fields.get('call_id') is not None:
      call_id = str(req.utter.meta.fields['call_id'].string_value)
    if req.utter.meta.fields.get('simplebot.id') is not None:
      simplebot_id = str(req.utter.meta.fields['simplebot.id'].string_value)
    if req.utter.meta.fields.get('campaign_id') is not None:
      campaign_id = str(req.utter.meta.fields['campaign_id'].string_value)
    if req.session.context.fields.get('checked_voicemail') is not None:
      checked_voicemail = str(req.session.context.fields['checked_voicemail'].string_value)
    if req.session.context.fields.get('intent_repeat_cnt') is not None:
      intent_repeat_cnt = str(req.session.context.fields['intent_repeat_cnt'].string_value)
    if req.utter.meta.fields.get('current_utter') is not None:
      current_utter = str(req.utter.meta.fields['current_utter'].string_value)

    self.logger.debug('[Talk] campaign_id : {}'.format(campaign_id))
    self.logger.debug('[Talk] is_tts : {}'.format(is_tts))
    self.logger.debug('[Talk] call_id : {}'.format(call_id))
    self.logger.debug('[Talk] contract_no : {}'.format(contract_no))
    self.logger.debug('[Talk] simplebot_id : {}'.format(simplebot_id))
    self.logger.debug('[Talk] pre_intent : {}'.format(pre_intent))
    self.logger.debug('[Talk] intent_repeat_cnt : {}'.format(intent_repeat_cnt))
    self.logger.debug('[Talk] utter : {}'.format(utter))
    self.logger.debug('[Talk] checked_voicemail : {}'.format(checked_voicemail))


    ##########################################################################
    ### 고객 정보, sds host 정보 가져오기
    ##########################################################################
    if campaign_id is None or campaign_id == '':
      campaign_id = 1
      contract_no = 2

    # 현재는 entity를 매번 보내야 하는 구조.
    # host도 추후에는 session에 담도록 처리하기.
    # 심플봇 테스트 케이스
    simplebot_id, host, entity_list = self.get_simplebot_cust_info(simplebot_id, contract_no)

    if entity_list is None: entity_list = []
    self.logger.info('host: {0}, campaign_id: {1}'.format(host, campaign_id))
    # 실 음성봇 테스트 케이스
    if host is None and campaign_id is not None:
      host = self.get_sds_host(campaign_id)
      entity_list = entity_list + self.get_cust_info(campaign_id, contract_no)
    elif host is not None and campaign_id is not None:  # 고객데이터 읽어서 maum-sds로 넘겨주기
      entity_list = entity_list + self.get_cust_info(campaign_id, contract_no)

    # M2U test-chat 케이스 : test용 host
    if host is None: host = self.sds_host

    sds.host = host

    ##########################################################################
    ### utter 예외 처리(음성사서함, #rec_, 상담원, 묵음..)
    ##########################################################################

    # 고객 utter 모니터링 전달
    # self.send_monitor_socket(host, utter, 'user')

    ## 음성사서함 정규식에 해당되는 발화가들어오면, 통화종료
    # if len(re.findall(r".*(음성\s*사서함|삐\s*소리|음성\s*녹음|연락\s*번호).*", str(utter))) > 0:
    # ## 기존에 음성사서함 체크하던 정규식
    # #if len(re.findall(
    #     #r".*((연락|호출)(\s*)번호|번호를(\s*)남기시려면|뇌출혈|핸드폰|안녕하세요|음성|다시(\s*)연락드릴(\s*)십일|환급금은(\s*)일>반|냄길께년|(번호(\s*)남(기|겨|겼)).*(환급금은(\s*)일반)|해파리).*",
    #     #str(utter))) > 0:
    #   self.logger.debug('[Talk] 자동응답 메세지 인식됨 -> 대화 종료 / contract_no: {}, utter: {}'.format(str(contract_no), str(utter)))
    #
    #   session_data = struct.Struct()
    #   session_data['checked_voicemail'] = 'Y'
    #   talk_res.response.session_update.context.CopyFrom(session_data)
    #
    #   res_meta['status'] = str('complete')
    #   res_meta['ai_call_err_msg'] = str('음성사서함')
    #   talk_res.response.close_skill = True
    #   talk_res.response.meta.CopyFrom(res_meta)
    #   return talk_res

    # TTS 도중에 들어오는 STT 무시하는 로직 ,
#    if is_tts == 'Y':
#      talk_res = make_empty_talk_res(pre_intent)
#      self.logger.debug(
#          '[{}]doing tts, ignore utter: {}'.format(req.session.id,
#                                                   utter))
#      return talk_res
    if current_utter is not None:
      # if current_utter.split('-')[1] == '1':
      if current_utter.split('-')[1] == '1' or len(current_utter.split('-')[1]) > 2:
        talk_res = make_empty_talk_res(pre_intent)
        self.logger.debug('[{0}]current utter, ignore utter: {1}'.format(current_utter, utter))
        return talk_res
    res_meta['tts'] = 'stop'

    # pre_intent is None: 아직 첫 발화가 나가지 않음
    if contract_no is None and utter != '시작' :#and pre_intent is None:
      talk_res = make_empty_talk_res(pre_intent)
      self.logger.debug(
          '[{}]doing tts, ignore utter: {}'.format(req.session.id,
                                                   utter))
      return talk_res


    # #res_start 무시
    if utter == '#rec_start':
      talk_res = make_empty_talk_res(pre_intent)
      return talk_res
    # utter가 두번이상에 걸쳐 들어온 경우 DA에서 무시하는 로직.
    try:
      self.session_id_dict.pop(req.session.id)
    except Exception:
      talk_res = make_empty_talk_res(pre_intent)
      self.logger.debug('[{0}] utter twice input, ignore utter: {1}'.format(req.session.id, utter))
      return talk_res

    # #res_stop 시 통화 종료
    if utter == '#rec_stop':
      da.rec_stop_da(
        req=req,
        db=mysql_db
      )
      talk_res.response.close_skill = True
      #self.logger.debug('>>talk response: {}'.format(talk_res))
      talk_res.response.meta.CopyFrom(res_meta)
      # 음성사서함 메세지 인식된 경우 dial_result = 700으로 업데이트
      # if checked_voicemail == 'Y':
      #   sql = "UPDATE CALL_HISTORY SET DIAL_RESULT=%s WHERE CONTRACT_NO=%s ORDER BY CALL_ID DESC LIMIT 1;"
      #   self.logger.debug("update call_history.dial_result sql: {}".format(sql))
      #   self.db_conn.update_query_with_params(sql, ('700', str(contract_no)))
      # DB 연결
      self.logger.debug('DB Connect [Session id: {0}]'.format(req.session.id))
      self.db_session_dict[req.session.id].disconnect()
      del self.db_session_dict[req.session.id]
      return talk_res

    # openSession에서 contract_no가 안넘어와서 임시적으로 '시작'으로 처리..
    sds_type = sds.TYPE_UTTER
    if utter == '시작':
      self.logger.info('[Talk] CM이 "시작" 보냄 -> 처음으로')
      utter = '처음으로'
      sds_type = sds.TYPE_INTENT

    ##########################################################################
    ### maum SDS 통신
    ##########################################################################

    # 전처리
    utter = preprocess_utter(utter)

    ####self.send_monitor_socket(host, ori_utter, 'user')

    # self.logger.debug(
    #     '[Talk]{}: utter(전처리 후) = {}, pre_intent={}, contract_no={}'
    #       .format(req.session.id, utter, pre_intent, contract_no))

    if entity_list is None: entity_list = []
    entity_list.append({'entityName': 'INPUT', 'entityValue': 'aaa'})
    # 메리츠화재DA호출(pre_sds_da)
    da_output_dict = dict()
    if str(host) == '5':
      utter, da_output_dict = da.pre_sds_da(
        req=req,
        db=mysql_db,
        utter=utter,
        da_output_dict=da_output_dict
      )
    # MAUM_SDS 통신
    answer, intent, res_content = sds.call_maum_sds(utter, req.session.id, sds_type, entity_list)
    if intent == '' and utter != '...' and is_tts == 'Y':
      talk_res = make_empty_talk_res(pre_intent)
      self.logger.debug(
          '[{}]doing tts, ignore utter: {}'.format(req.session.id,
                                                   utter))
      self.session_id_dict[req.session.id] = datetime.now()
      return talk_res


    self.logger.debug('>> res_content: {0}'.format(res_content))
    # 메리츠화재DA호출(after_sds_da)
    if str(host) == '5':
      while True:
        utter, da_output_dict, answer, sds_repeat = da.after_sds_da(
          req=req,
          answer=answer,
          da_output_dict=da_output_dict,
          db=mysql_db,
          res_content=res_content,
          utter=utter
        )
        if not sds_repeat:
          break
        # MAUM_SDS 통신
        answer, intent, res_content = sds.call_maum_sds(utter, req.session.id, sds_type, entity_list)


    # answer post-processing
    answer = common.convert_script(answer, 1)
    answer = answer.replace('\n', '')
    # answer = answer.decode("utf-8").encode("utf-8")

    ##########################################################################
    ###  CALL 기타 처리 (doing_tts, dtmf ..)
    ##########################################################################

    # max turn check
    if pre_intent == intent:
      intent_repeat_cnt = int(intent_repeat_cnt) + 1
    else:
      intent_repeat_cnt = 0

    res_meta['intent_repeat_cnt'] = intent_repeat_cnt

    call_task_info = self.get_call_task_info(simplebot_id, intent)
    # todo: task_info 없으면 예외처리
    # dtmf 설정
    self.handle_call_meta(call_task_info, res_meta)
    self.logger.debug('>> after handle_call_meta: {}'.format(res_meta))

    if self.check_max_turn(res_meta):
      self.logger.debug('check_max_turn is true')
      self.logger.debug(req)
      # 반복회수 초과시 다음 task로 maum-sds 호출
      next_task = str(res_meta['task_over_max']).replace("\n", "")
      answer, intent, res_content = sds.call_maum_sds(next_task, req.session.id, sds.TYPE_INTENT, entity_list)
      # SDS 재처리 후 max turn 재확인
      if pre_intent == intent:
        intent_repeat_cnt = int(intent_repeat_cnt) + 1
      else:
        intent_repeat_cnt = 0
      res_meta['intent_repeat_cnt'] = intent_repeat_cnt
      # dtmf 재설정
      call_task_info = self.get_call_task_info(simplebot_id, intent)
      # todo: task_info 없으면 예외처리
      self.handle_call_meta(call_task_info, res_meta)

      # 메리츠화재DA호출
      if str(host) == '5':
        while True:
          utter, da_output_dict, answer, sds_repeat = da.after_sds_da(
            req=req,
            answer=answer,
            da_output_dict=da_output_dict,
            db=mysql_db,
            res_content=res_content,
            utter=utter
          )
          if not sds_repeat:
            break
          # MAUM_SDS 통신
          answer, intent, res_content = sds.call_maum_sds(utter, req.session.id, sds_type, entity_list)

    # 시스템 utter 모니터링 전달
    #self.send_monitor_socket(host, answer, 'bot', intent)

    ####################################
    ### 구기자 SCENARIO_RESULT insert
    ####################################
    if (host == 441 or host == '441' or host == 587 or host == '587') and '종료' in intent:
      sql = "UPDATE CALL_HISTORY SET SCENARIO_RESULT=%s WHERE CONTRACT_NO=%s ORDER BY CALL_ID DESC LIMIT 1;"
      if len(re.findall(r".*(네|예|맞아|맞습니다).*", str(utter))) > 0:
        self.db_conn.update_query_with_params(sql, ('Y', str(contract_no)))
      else:
        self.db_conn.update_query_with_params(sql, ('N', str(contract_no)))

    ####################################
    ### 직방 상담원 연결
    ####################################
    if (host == 619 or host == '619' or host == 620 or host == '620') and intent == '상담사연결':
      res_meta['status'] = 'complete'
      res_meta['transfer'] = '01066351157'  # 근재 번호(임시)
      talk_res.response.close_skill = True

    # 통화 종료 처리
    # if intent == '' or intent == '종료' or intent == '바쁨' or intent == '콜백' or '종료' in intent:
    dest_intent = str()
    src_intent = str()
    if 'meta' in res_content:
      if 'intentRel' in res_content['meta']:
        if 'destIntent' in res_content['meta']['intentRel']:
          dest_intent = res_content['meta']['intentRel']['destIntent']
        if 'srcIntent' in res_content['meta']['intentRel']:
          src_intent = res_content['meta']['intentRel']['srcIntent']
    # if 'setMemory' in res_content:
    #   if 'intent' in res_content['setMemory']:
    #     intent = res_content['setMemory']['intent']['intent']
    if intent == '최대반복초과종결':
      dest_intent = intent

    # 종결 체크
    if dest_intent.endswith('종결'):
      res_meta['status'] = 'complete'
      talk_res.response.close_skill = True
      self.logger.debug('talk complete: {}'.format(intent))

    #if (talk_res.response.close_skill) :
    #  if ('transfer' in res_meta):
    #    self.send_monitor_socket(host, ">>>>> 상담사 연결 -> " + res_meta['transfer'], 'system', '')
    #  else:
    #    self.send_monitor_socket(host, ">>>>> 통화 종료", 'system', '')


    ##########################################################################
    #  response 구성
    ##########################################################################

    # session_data set
    session_data = struct.Struct()
    session_data['pre_intent'] = intent
    session_data['intent_repeat_cnt'] = str(intent_repeat_cnt)
    # 메리츠화재 session_data 저장
    if str(host) == '5':
        session_data = da.set_session_data(req, intent, session_data, da_output_dict)
        if intent == '종료':
            res_meta['status'] = 'complete'
            talk_res.response.close_skill = True
            self.logger.debug('talk complete: {}'.format(intent))

    talk_res.response.session_update.context.CopyFrom(session_data)
    res_meta['sds.intent'] = intent
    if res_meta['tts'] == 'stop' and utter != '처음으로':
      answer = '네, {0}'.format(answer)
    talk_res.response.meta.CopyFrom(res_meta)
    talk_res.response.speech.utter = answer
    self.session_id_dict[req.session.id] = datetime.now()
    return talk_res

  def check_max_turn(self, meta):
    res = False
    if 'max_turn' in meta:
      max_turn = int(meta['max_turn'])
      intent_repeat_cnt = int(meta['intent_repeat_cnt'])

      if 0 < max_turn < intent_repeat_cnt:
        res = True

    return res

  def handle_call_meta(self, call_task_info, meta):
    if call_task_info:
      simplebot_id = call_task_info['SIMPLEBOT_ID']
      task = call_task_info['TASK']
      accept_idx = call_task_info['ACCEPT_STT_STC_IDX']
      max_turn = call_task_info['MAX_TURN']
      task_over_max = call_task_info['TASK_OVER_MAX']
      dtmf = call_task_info['DTMF']
      intent_repeat_cnt = int(meta['intent_repeat_cnt'])

      if accept_idx:
        accept_idx = int(accept_idx.split(',')[0]) + 1

      if dtmf and intent_repeat_cnt <= int(max_turn):
        dtmf = dtmf.split(',')[int(meta['intent_repeat_cnt'])]

      meta['utter_no'] = accept_idx
      meta['extra'] = get_dtmf_meta(dtmf)
      meta['max_turn'] = max_turn
      meta['task_over_max'] = task_over_max
      self.logger.debug("dtmf: {0}".format(meta['extra']))
      self.logger.debug("dtmf: {0}".format(get_dtmf_meta(dtmf)))
      self.logger.debug("dtmf: {0}".format(dtmf))
    else:
      self.logger.debug('No call_task_meta data.')

  def get_simplebot_cust_info(self, simplebot_id, contract_no):

    sql = None
    # chatbot
    simplebot_id = 2
    self.logger.debug(simplebot_id)
    self.logger.debug(contract_no)

    if simplebot_id is not None:
      sql = "SELECT ID, HOST, TEST_CUST_DATA FROM SIMPLEBOT WHERE ID =" + str(simplebot_id) + ";"
    # voicebot
    elif contract_no is not None:
      sql = "SELECT b.ID, b.HOST, b.TEST_CUST_DATA FROM CM_CAMPAIGN a, SIMPLEBOT b, CM_CONTRACT c "\
      "WHERE a.SIMPLEBOT_ID = b.ID AND a.CAMPAIGN_ID = c.CAMPAIGN_ID AND c.CONTRACT_NO ="+ str(contract_no) + ";"

    try:
      result = self.db_conn.select_one(sql)
      self.logger.debug('get_simplebot_cust_info sql : {}'.format(sql))
      self.logger.debug('get_simplebot_cust_info : {}'.format(result))
    except Exception as e:
      self.logger.error(e)

    if result is None:
      return None, None, None

    else:
      simplebot_id, host, cust_info_list = result
      # cust_info_list = cust_info_list[0]
      if cust_info_list is None or cust_info_list == '':
        self.logger.debug('simplebot test: no cust data')
        cust_info_list = {}
      else:
        cust_info_list = json.loads(cust_info_list)

    # 후처리
    entity_list = []
    for entity_name in cust_info_list:
      entity_val = cust_info_list[entity_name]
      entity_set = {'entityName': entity_name, 'entityValue': entity_val}
      entity_list.append(entity_set)

    return simplebot_id, host, entity_list

  # 운영용 get_cust_info
  def get_cust_info(self, campaignid, contract_no):
    self.logger.debug('get_cust_info() contract_no : {}'.format(contract_no))
    cust_info_list = None
    try:
      sql = "SELECT CDC.COLUMN_KOR," \
            " JSON_EXTRACT(CI.CUST_DATA, CONCAT('$.\"', CDC.CUST_DATA_CLASS_ID, '\"'))" \
           " FROM CUST_INFO CI" \
           " LEFT JOIN CM_CONTRACT CC" \
           " ON CI.CUST_ID = CC.CUST_ID" \
           " LEFT JOIN CUST_DATA_CLASS CDC" \
           " ON CI.CAMPAIGN_ID = CDC.CAMPAIGN_ID" \
           " WHERE CC.USE_YN = 'Y'" \
           " AND CDC.USE_YN = 'Y'" \
           " AND CC.IS_INBOUND = 'N'" \
            " AND CDC.CAMPAIGN_ID = " + str(campaignid) + \
           " AND CC.CONTRACT_NO = " + str(contract_no) + ";"

      self.logger.debug('get_cust_info sql : {}'.format(sql))
      cust_info_list = self.db_conn.select_all(sql)
      self.logger.debug('cust_info : {}'.format(cust_info_list))
    except Exception as e:
      self.logger.error(e)

    if cust_info_list is None:
      return list()
    # 후처리
    entity_list = []
    for cust_info in cust_info_list:
      entity_name = cust_info[0]
      entity_val = cust_info[1]
      if entity_val is None:
        continue

      # if entity_name != "계약자명":
      #   continue
      # print(entity_val)
      entity_val = entity_val.replace('\"', '')
      entity_set = {'entityName': entity_name, 'entityValue': entity_val}
      entity_list.append(entity_set)

    return entity_list

  def get_sds_host(self, campaignid):
    host = None
    self.logger.debug('get_sds_host() campaignid : {}'.format(campaignid))

    try:
      sql = "SELECT S.HOST FROM CM_CAMPAIGN CC " \
            "JOIN SIMPLEBOT S on S.ID = CC.SIMPLEBOT_ID " \
            "WHERE CAMPAIGN_ID = " + str(campaignid) + ";"

      self.logger.debug('get_sds_host sql : {}'.format(sql))
      host = self.db_conn.select_one(sql)[0]
      self.logger.debug('get_sds_host : {}'.format(host))
    except Exception as e:
      self.logger.error(e)
    return host

  def get_call_task_info(self, simplebot_id, intent):
    self.logger.debug('get_call_task_info() intent : {}'.format(intent))
    call_task_info = {}
    try:
      sql = "SELECT * FROM SPB_CALL_TASK_META" \
            " WHERE SIMPLEBOT_ID='" + str(simplebot_id) +"'"\
            " AND TASK='" + str(intent) + "';"

      self.logger.debug('get_call_task_info sql : {}'.format(sql))
      call_task_info = self.db_conn.select_one_dict(sql)
      self.logger.debug('call_task_info : {}'.format(call_task_info))
    except Exception as e:
      self.logger.error(e)
    return call_task_info

  def send_monitor_socket(self, host, msg, user='bot', intent=''):
    self.logger.debug('[send_monitor_socket] ')
    result = {'status': 'failed', 'message': ''}

    try:
      if self.sio.connected == False:
        self.logger.debug('sio is not connected, bye!')
        result['message'] = 'socket is not connected!'
        # return result

      self.logger.debug('socket url :: {}'.format(self.socket_url))
      if self.socket_url == '':
        result['message'] = 'connect url failed'
        return result
      if '' in (host, msg, user):
        result['message'] = 'check param'
        return result

      data = dict()
      data['type'] = 'join'
      data['room'] = str(host)
      data['intent'] = intent
      self.logger.debug(json.dumps(data))
      # self.sio.emit('connection', json.dumps(data))
      self.logger.debug('[send_socket] connect, room: {}'.format(host))

      data['type'] = str(user)
      data['message'] = str(msg)

      # self.sio.emit('sendMsg', json.dumps(data))
      self.logger.debug('=================================')
      self.logger.debug(json.dumps(data))
      self.logger.debug('=================================')
      # sio.send('sendMsg', json.dumps(data), room=str(sio_host))
      self.logger.debug('[send_socket] emit ')
      # sio.disconnect()
      # print('[send_socket] disconnect ')
      result['status'] = 'success'
    except Exception as e:
      result['message'] = 'exception :: ' + str(e)
      # return result
    finally:
      self.logger.debug(result)
      return result


def get_dtmf_meta(dtmf):
  dtmf_meta = ''
  if dtmf == '0':
    dtmf_meta = 'dtmf_off'
  elif dtmf == '1':
    dtmf_meta = 'dtmf_on'
  elif dtmf == '2':
    dtmf_meta = 'both'
  return dtmf_meta


def make_empty_talk_res(pre_intent):
  talk_res = talk_pb2.TalkResponse()
  talk_res.response.speech.utter = ''
  res_meta = update_meta(pre_intent)
  talk_res.response.meta.CopyFrom(res_meta)
  return talk_res


def update_meta(intent='', msg_code=''):
  res_meta = struct.Struct()
  res_meta['tts_tempo'] = DaConfig.tts_tempo
  res_meta['intent'] = intent
  res_meta['msg_code'] = msg_code
  res_meta['delimiter'] = '|'
  return res_meta


def preprocess_utter(utter):
  if utter == '네 이거' or utter == '네 이번':
    utter = '네이버'
  if utter == '이만' or utter == '이마':
    utter = '이마음'
  if "<br" in utter:
    utter = utter.replace("<br>", "")
    utter = utter.replace("<br/>", "")

  str(utter).replace("\n", "")

  return utter


def serve():
  parser = argparse.ArgumentParser(description='DAMainServer DA')
  parser.add_argument('-p', '--port',
                      nargs='?',
                      dest='port',
                      required=True,
                      type=int,
                      help='port to access server')
  args = parser.parse_args()

  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

  talk_pb2_grpc.add_DialogAgentProviderServicer_to_server(
      DAMainServer(), server)
  listen = '[::]' + ':' + str(args.port)
  server.add_insecure_port(listen)
  server.start()

  try:
    while True:
      time.sleep(__ONE_DAY_IN_SECONDS__)
  except KeyboardInterrupt:
    server.stop(0)


if __name__ == '__main__':
  serve()
