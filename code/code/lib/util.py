#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-02, modification: 0000-00-00"

###########
# imports #
###########
import socket
import traceback


#######
# def #
#######
def rows_to_dict_list(db):
    """
    Make dict Result
    @param      db:     DB object
    @return:            Dictionary Result
    """
    columns = [i[0] for i in db.cursor.description]
    return [dict(zip(columns, row)) for row in db.cursor]


def select_cust_data_class(db, campaign_id):
    """
    Select Stock Item list from CUST_DATA_CLASS
    :param      db:                 DB obejct
    :param      campaign_id:        CAMPAIGN_ID
    :return:                        CUST_DATE list
    """
    try:
        query = """
            SELECT
                CUST_DATA_CLASS_ID,
                COLUMN_KOR
            FROM
                CUST_DATA_CLASS
            WHERE
                CAMPAIGN_ID = %s
                AND USE_YN = 'Y'
        """
        bind = (
            campaign_id,
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def insert_cust_info(db, campaign_id, cust_nm, cust_tel_no, cust_data, target_yn, blacklist_yn, correct_yn):
    """
    Insert CUST_INFO
    :param      db:                 DB object
    :param      campaign_id:        CAMPAIGN_ID
    :param      cust_nm:            CUST_NM
    :param      cust_tel_no:        CUST_TEL_NO
    :param      cust_data:          CUST_DATA
    :param      target_yn:          TARGET_YN
    :param      blacklist_yn:       BLACKLIST_YN
    :param      correct_yn:         CORRECT_YN
    """
    query = str()
    bind = tuple()
    try:
        query = """
            INSERT INTO CUST_INFO
            (
                CAMPAIGN_ID,
                CUST_NM,
                CUST_TEL_NO,
                CUST_DATA,
                TARGET_YN,
                BLACKLIST_YN,
                CORRECT_YN
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s
            )
        """
        bind = (
            campaign_id,
            cust_nm,
            cust_tel_no,
            cust_data,
            target_yn,
            blacklist_yn,
            correct_yn,
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_cust_id(**kwargs):
    """
    Select MAX CUST_ID from CUST_INFO
    :param      kwargs:         Arguments
    :return:                    MAX CUST_ID
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                MAX(CUST_ID)
            FROM
                CUST_INFO
        """
        db.check_alive()
        db.cursor.execute(query)
        results = db.cursor.fetchall()
        if results is bool:
            return False
        if not results:
            return False
        return results[0]['MAX(CUST_ID)']
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def insert_cm_contract(**kwargs):
    """
    Insert CM_CONTRACT
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            INSERT INTO CM_CONTRACT
            (
                CAMPAIGN_ID,
                CUST_ID,
                TEL_NO,
                CUST_OP_ID,
                PROD_ID,
                CALL_TRY_COUNT,
                LAST_CALL_ID,
                IS_INBOUND,
                TASK_SEQ,
                USE_YN
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """
        bind = (
            kwargs.get('campaign_id'),
            kwargs.get('cust_id'),
            kwargs.get('tel_no'),
            kwargs.get('cust_op_id'),
            kwargs.get('prod_id'),
            kwargs.get('call_try_count'),
            kwargs.get('last_call_id'),
            kwargs.get('is_inbound'),
            kwargs.get('task_seq'),
            kwargs.get('use_yn'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def insert_auto_call_condition(**kwargs):
    """
    Insert AUTO_CALL_CONDITION
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            INSERT INTO AUTO_CALL_CONDITION
            (
                START_DTM,
                END_DTM,
                DISPATCH_TIME,
                OB_CALL_STATUS,
                CALL_TRY_ACCOUNT,
                CREATE_DTM,
                CREATOR,
                CAMPAIGN_ID,
                PROGRESS_STATUS,
                ACTIVE_STATUS,
                USE_YN,
                WEEK_DAY,
                CD_DESC,
                CD_NAME
            )
            VALUES (
                %s, %s, %s, %s, %s,
                DATE_FORMAT(NOW(), '%%Y-%%m-%%d %%H:%%i:%%s'), %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        bind = (
            kwargs.get('start_dtm'),
            kwargs.get('end_dtm'),
            kwargs.get('dispatch_time'),
            kwargs.get('ob_call_status'),
            kwargs.get('call_try_count'),
            kwargs.get('creator'),
            kwargs.get('campaign_id'),
            kwargs.get('progress_status'),
            kwargs.get('active_status'),
            kwargs.get('use_yn'),
            kwargs.get('week_day'),
            kwargs.get('cd_desc'),
            kwargs.get('cd_name')
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_auto_call_condition_id(db):
    """
    Select MAX ID from AUTO_CALL_CONDITION
    :param      db:         DB object
    :return:                MAX CUST_ID
    """
    try:
        query = """
            SELECT
                MAX(ID)
            FROM
                AUTO_CALL_CONDITION
        """
        db.check_alive()
        db.cursor.execute(query)
        results = db.cursor.fetchall()
        if results is bool:
            return False
        if not results:
            return False
        return results[0]['MAX(ID)']
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def insert_auto_call_condition_custom(**kwargs):
    """
    Insert AUTO_CALL_CONDITION_CUSTOM
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            INSERT INTO AUTO_CALL_CONDITION_CUSTOM
            (
                CUST_DATA_CLASS_ID,
                AUTO_CALL_CONDITION_ID,
                DATA_VALUE,
                USE_YN
            )
            VALUES (
                %s, %s, %s, %s
            )
        """
        bind = (
            kwargs.get('cust_data_class_id'),
            kwargs.get('auto_data_condition_id'),
            kwargs.get('data_value'),
            kwargs.get('use_yn')
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def update_cm_contract(**kwargs):
    """
    UPDATE CM_CONTRACT
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                CALL_TRY_COUNT = %s,
                TASK_SEQ = %s,
                TASK_SEQ_NM = %s,
                SUCCESS_CD = %s,
                SUCCESS_NM = %s,
                CUST_REACT = %s,
                REC_FILE_NM = %s,
                REC_PTH = %s,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('call_try_count'),
            kwargs.get('task_seq'),
            kwargs.get('task_seq_nm'),
            kwargs.get('success_cd'),
            kwargs.get('success_nm'),
            kwargs.get('cust_react'),
            kwargs.get('rec_file_nm'),
            kwargs.get('rec_path'),
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_call_history(**kwargs):
    """
    Select DIAL_RESULT of CALL_HISTORY
    :param      kwargs:         Argument
    :return:                    Result
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                DIAL_RESULT,
                DIAL_RESULT_DETAIL,
                DURATION,
                DATE_FORMAT(START_TIME, '%%Y%%m%%d%%H%%i%%s') AS START_TIME,
                DATE_FORMAT(END_TIME, '%%Y%%m%%d%%H%%i%%s') AS END_TIME,
                SIP_USER
            FROM
                CALL_HISTORY
            WHERE
                CALL_ID = %s
        """
        bind = (
            kwargs.get('call_id'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def update_call_history(**kwargs):
    """
    UPDATE CALL_HISTORY
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CALL_HISTORY
            SET
                DIAL_RESULT_DETAIL = %s,
                UPDATED_DTM = NOW()
            WHERE
                CALL_ID = %s
        """
        bind = (
            kwargs.get('dial_result_detail'),
            kwargs.get('call_id'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_cust_info(**kwargs):
    """
    Select CUST_INFO
    :param      kwargs:         Arguments
    :return:                    CUST_DATA
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                CUST_NM,
                CUST_DATA,
                CUST_TEL_NO
            FROM
                CUST_INFO
            WHERE
                CUST_ID = %s
        """
        bind = (
            kwargs.get('cust_id'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results[0]
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def select_cust_id_in_cm_contract(**kwargs):
    """
    Select CUST_ID from CM_CONTRACT
    :param      kwargs:         Arguments
    :return:                    CUST_ID
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                CUST_ID
            FROM
                CM_CONTRACT
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return False
        if not results:
            return False
        return results[0]['CUST_ID']
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def select_rec_info(**kwargs):
    """
    Select CUST_ID from CM_CONTRACT
    :param      kwargs:         Arguments
    :return:                    CUST_ID
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                REC_PTH, 
                REC_FILE_NM,
                TASK_SEQ,
                SUCCESS_CD,
                CUST_REACT,
                IS_INBOUND
            FROM
                CM_CONTRACT
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return False
        if not results:
            return False
        return results[0]
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def update_cm_contract_conv_data(**kwargs):
    """
    UPDATE CM_CONTRACT OF CONV_DATA
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    target_dict = kwargs.get('target_dict')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                REC_ID = %s,
                REC_CONV_PTH = %s,
                REC_CONV_FILE_NM = %s,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            target_dict['REC_ID'],
            target_dict['REC_CONV_PTH'],
            target_dict['REC_CONV_FILE_NM'],
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_cm_stt_rslt_detail(**kwargs):
    """
    Select data from CM_STT_RSLT_DETAIL
    :param      kwargs:         Arguments
    :return:                    CM_STT_RSLT_DETAIL Data
    """
    db = kwargs.get('db')
    try:
        query = """
            SELECT
                SENTENCE_ID, 
                SPEAKER_CODE,
                START_TIME,
                END_TIME,
                SENTENCE
            FROM
                CM_STT_RSLT_DETAIL
            WHERE
                CALL_ID = %s
            ORDER BY
                SENTENCE_ID
        """
        bind = (
            kwargs.get('call_id'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def select_stt_results_existed(db, rec_id, record_file_name):
    """
    Check STT results existed from STTARECRSTINF(STT녹취결과정보)
    @param      db:                     DB object
    @param      rec_id:                 REC_ID(녹취ID)
    @param      record_file_name:       RECORD_FILE_NAME(녹취파일명)
    """
    try:
        query = """
            SELECT
                REC_ID
            FROM
                DBSTTS.dbo.STTARECRSTINF WITH(NOLOCK)
            WHERE
                REC_ID = %s
                AND RECORD_FILE_NAME = %s
                AND STMT_NO = '1'
        """
        bind = (
            rec_id,
            record_file_name
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        result = rows_to_dict_list(db)
        if result is bool:
            return False
        if not result:
            return False
        return True
    except Exception:
        raise Exception(traceback.format_exc())


def delete_stt_results(db, rec_id, record_file_name):
    """
    Delete STT results from STTARECRSTINF(STT녹취결과정보)
    @param      db:                     DB object
    @param      rec_id:                 REC_ID(녹취ID)
    @param      record_file_name:       RECORD_FILE_NAME(녹취파일명)
    """
    try:
        query = """
            DELETE FROM
                DBSTTS.dbo.STTARECRSTINF
            WHERE
                REC_ID = %s
                AND RECORD_FILE_NAME = %s
        """
        bind = (
            rec_id,
            record_file_name
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise Exception(traceback.format_exc())


def insert_stt_result(db, bind_list):
    """
    Insert STT result STTARECRSTINF(STT녹취결과정보)
    @param      db:             DB object
    @param      bind_list:      Bind list
    """
    try:
        query = """
            INSERT INTO DBSTTS.dbo.STTARECRSTINF
            (
                REC_ID,
                RECORD_FILE_NAME,
                STMT_NO,
                SPK_DIV_CD,
                STMT_ST_TM,
                STMT_END_TM,
                STMT,
                CRTPE_ID,
                CRTPE_DTM,
                MDFPE_ID,
                MDFPE_DTM
            )
            VALUES
            (
              %s, %s, %s, %s, %s, 
              %s, %s, %s, %s, %s, %s
            )
        """
        db.check_alive()
        db.cursor.executemany(query, bind_list)
        db.conn.commit()
    except Exception:
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def update_cm_contract_rec_tran(**kwargs):
    """
    UPDATE CM_CONTRACT OF CONV_DATA
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                REC_TRAN_YN = %s,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('rec_tran_yn'),
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def update_cm_contract_rec_tran(**kwargs):
    """
    UPDATE CM_CONTRACT OF CONV_DATA
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                REC_TRAN_YN = %s,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('rec_tran_yn'),
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def select_rec_tran_n(**kwargs):
    """
    SELECT CM_CONTRACT data
    :param      kwargs:         Arguments
    """
    db = kwargs.get('db')
    query = str()
    try:
        query = """
            SELECT
                A.CONTRACT_NO,
                A.REC_FILE_NM,
                DATE_FORMAT(B.START_TIME, '%Y%m%d%H%i%s') AS START_TIME,
                A.REC_CONV_FILE_NM,
                A.REC_CONV_PTH,
                DATE_FORMAT(B.END_TIME, '%Y%m%d%H%i%s') AS END_TIME,
                A.IS_INBOUND,
                A.CAMPAIGN_ID,
                C.CUST_DATA,
                B.DURATION,
                B.SIP_USER,
                A.REC_ID,
                C.CUST_NM,
                C.CUST_TEL_NO,
                C.CUST_ID
            FROM
                CM_CONTRACT A,
                CALL_HISTORY B,
                CUST_INFO C
            WHERE
                A.REC_TRAN_YN = 'N'
                AND B.START_TIME >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                AND A.LAST_CALL_ID = B.CALL_ID
                AND A.CUST_ID = C.CUST_ID
            ORDER BY
                B.START_TIME
        """
        db.check_alive()
        db.cursor.execute(query)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        print(query)
        raise Exception(traceback.format_exc())


def select_dial_result_detail_null(**kwargs):
    """
    SELECT CM_CONTRACT data
    :param      kwargs:         Arguments
    """
    db = kwargs.get('db')
    query = str()
    try:
        query = """
            SELECT
                B.CUST_ID,
                A.CALL_ID,
                B.CAMPAIGN_ID,
                B.CONTRACT_NO,
                DATE_FORMAT(A.START_TIME, '%Y%m%d%H%i%s') AS START_TIME,
                A.DIAL_RESULT,
                A.DURATION,
                DATE_FORMAT(A.END_TIME, '%Y%m%d%H%i%s') AS END_TIME
            FROM
                CALL_HISTORY A,
                CM_CONTRACT B
            WHERE
                A.DIAL_RESULT_DETAIL IS NULL
                AND A.END_TIME < DATE_ADD(NOW(), INTERVAL {0} MINUTE)
                AND A.CALL_ID = B.LAST_CALL_ID
        """.format(kwargs.get('interval'))
        db.check_alive()
        db.cursor.execute(query)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        print(query)
        raise Exception(traceback.format_exc())


def select_contract_no(**kwargs):
    """
    SELECT CM_CONTRACT data
    :param      kwargs:         Arguments
    """
    db = kwargs.get('db')
    query = str()
    bind = tuple()
    try:
        query = """
            SELECT
                B.CONTRACT_NO,
                B.CALL_TRY_COUNT
            FROM
                CUST_INFO A,
                CM_CONTRACT B
            WHERE
                A.CUST_TEL_NO = %s
                AND JSON_UNQUOTE(JSON_EXTRACT(A.CUST_DATA, '$."8"')) LIKE '%%{0}%%'
                AND A.CUST_ID = B.CUST_ID
        """.format(kwargs.get('call_time'))
        bind = (
            kwargs.get('cust_tel_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
        results = db.cursor.fetchall()
        if results is bool:
            return list()
        if not results:
            return list()
        return results
    except Exception:
        print(query)
        print(bind)
        raise Exception(traceback.format_exc())


def update_call_try_count(**kwargs):
    """
    UPDATE CM_CONTRACT with CALL_TRY_COUNT
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                CALL_TRY_COUNT = -1,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def update_cm_contract_for_masking(**kwargs):
    """
    UPDATE CM_CONTRACT for masking
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CM_CONTRACT
            SET
                TEL_NO = %s,
                UPDATED_DTM = NOW()
            WHERE
                CONTRACT_NO = %s
        """
        bind = (
            kwargs.get('cust_tel_no'),
            kwargs.get('contract_no'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)


def update_cust_info_for_masking(**kwargs):
    """
    UPDATE CUST_INFO for masking
    :param      kwargs:         Arguments
    """
    query = str()
    bind = tuple()
    db = kwargs.get('db')
    try:
        query = """
            UPDATE
                CUST_INFO
            SET
                CUST_TEL_NO = %s,
                CUST_NM = %s
            WHERE
                CUST_ID = %s
        """
        bind = (
            kwargs.get('tel_no'),
            kwargs.get('cust_nm'),
            kwargs.get('cust_id'),
        )
        db.check_alive()
        db.cursor.execute(query, bind)
    except Exception:
        print(query)
        print(bind)
        exc_info = traceback.format_exc()
        db.conn.rollback()
        raise Exception(exc_info)
