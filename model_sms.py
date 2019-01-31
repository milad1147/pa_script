﻿# -*- coding: utf-8 -*-

__author__ = 'YangLiyuan'

from PA_runtime import *
import clr

try:
    clr.AddReference('System.Data.SQLite')
    clr.AddReference('ScriptUtils')
except:
    pass
del clr

import sqlite3
import shutil
import hashlib
import random
import json

import System.Data.SQLite as SQLite
import PA.InfraLib.ModelsV2.CommonEnum.SMSStatus as SMSStatus
import PA.InfraLib.ModelsV2.Base.Content.TextContent as TextContent
import PA.InfraLib.ModelsV2.Base.Contact as Contact
from ScriptUtils import CASE_NAME, exc, tp, BaseParser, DEBUG


SMS_TYPE_ALL    = 0
SMS_TYPE_INBOX  = 1
SMS_TYPE_SENT   = 2
SMS_TYPE_DRAFT  = 3
SMS_TYPE_OUTBOX = 4
SMS_TYPE_FAILED = 5
SMS_TYPE_QUEUED = 6

SMS_TYPE_TO_FOLDER = (
    None,                      # '',
    Generic.Folders.Inbox,     # '收件箱',
    None,                      # '正在发送',
    Generic.Folders.Sent,      # '草稿箱',
    Generic.Folders.Sent,      # '发件箱',
    Generic.Folders.Sent,      # '发送失败',
    None,                      # '',
)

VERSION_VALUE_DB = 3
VERSION_KEY_DB  = 'db'
VERSION_KEY_APP = 'app'
        
SQL_CREATE_TABLE_SIM_CARDS = '''
    create table if not exists sim_cards(
        sim_id        INTEGER DEFAULT 0,
        number        TEXT,
        sync_enabled  INTEGER DEFAULT 1,
        source        TEXT,
        deleted       INT DEFAULT 0, 
        repeated      INT DEFAULT 0)                                
    '''

SQL_INSERT_TABLE_SIM_CARDS = '''
    insert into sim_cards(
        sim_id,
        number,
        sync_enabled,
        source, deleted, repeated) 
        values(?, ?, ?, ?, ?, ?)
    '''

''' bcp: 
    6.1.9　短信记录信息(WA_MFORENSICS_010700)

    字段说明（短信记录信息）
    0	手机取证采集目标编号	COLLECT_TARGET_ID
    1	本机号码	MSISDN
    2	对方号码	RELATIONSHIP_ACCOUNT
    3	联系人姓名	RELATIONSHIP_NAME
    4	本地动作	LOCAL_ACTION            标示本机是收方还是发方，01接收方、02发送方、99其他
    5	发送时间	MAIL_SEND_TIME
    6	短消息内容	CONTENT
    7	查看状态	MAIL_VIEW_STATUS        0未读，1已读，9其它
    8	存储位置	MAIL_SAVE_FOLDER        01收件箱、02发件箱、03草稿箱、04垃圾箱、99其他
    9	加密状态	PRIVACYCONFIG
    10	删除状态	DELETE_STATUS
    11	删除时间	DELETE_TIME             19700101000000基准
    12	拦截状态	INTERCEPT_STATE
table-sms TYPE
    SMS_TYPE_ALL    = 0
    SMS_TYPE_INBOX  = 1
    SMS_TYPE_SENT   = 2
    SMS_TYPE_DRAFT  = 3
    SMS_TYPE_OUTBOX = 4
    SMS_TYPE_FAILED = 5
    SMS_TYPE_QUEUED = 6    
'''

SQL_CREATE_TABLE_SMS = '''
    create table if not exists sms(
        _id                 TEXT, 
        sim_id              INT,
        sender_phonenumber  TEXT,
        sender_name         TEXT,
        read_status         INT DEFAULT 0,
        type                INT DEFAULT 0,
        suject              TEXT,
        body                TEXT,
        send_time           INT,
        delivered_date      INT,
        is_sender           INT,
        source              TEXT,
        deleted             INT DEFAULT 0, 
        repeated            INT DEFAULT 0,
        recv_phonenumber    TEXT,
        recv_name           TEXT,
        smsc                TEXT
        )
    '''
SQL_INSERT_TABLE_SMS = ''' 
    insert into sms(
        _id, 
        sim_id,
        sender_phonenumber,
        sender_name,
        read_status,
        type,
        suject,
        body,
        send_time,
        delivered_date,
        is_sender,
        source, 
        deleted, 
        repeated,
        recv_phonenumber,
        recv_name,
        smsc
        ) 
        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?, ?)'''

SQL_CREATE_TABLE_VERSION = '''
    create table if not exists version(
        key TEXT primary key,
        version INT)'''

SQL_INSERT_TABLE_VERSION = '''
    insert or REPLACE into version(key, version) values(?, ?)'''


class ModelSMS(object):
    def __init__(self):
        self.db = None
        self.db_cmd = None
        self.db_trans = None

    def db_create(self, db_path):
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                print('error with remove sms db_path:', db_path)
                exc()
        self.db = SQLite.SQLiteConnection('Data Source = {}'.format(db_path))
        self.db.Open()
        self.db_cmd = SQLite.SQLiteCommand(self.db)
        try:
            self.db_trans = self.db.BeginTransaction()
        except:
            exc()
            
        self.db_create_table()
        self.db_commit()

    def db_commit(self):
        if self.db_trans is not None:
            self.db_trans.Commit()
        self.db_trans = self.db.BeginTransaction()

    def db_close(self):
        self.db_trans = None
        if self.db_cmd is not None:
            self.db_cmd.Dispose()
            self.db_cmd = None
        if self.db is not None:
            self.db.Close()
            self.db = None   
            
    def db_create_table(self):
        if self.db_cmd is not None:
            self.db_cmd.CommandText = SQL_CREATE_TABLE_SMS
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_SIM_CARDS
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_VERSION
            self.db_cmd.ExecuteNonQuery()

    def db_insert_table(self, sql, values):
        if self.db_cmd is not None:
            self.db_cmd.CommandText = sql
            self.db_cmd.Parameters.Clear()
            for value in values:
                param = self.db_cmd.CreateParameter()
                param.Value = value
                self.db_cmd.Parameters.Add(param)
            self.db_cmd.ExecuteNonQuery()

    def db_insert_table_sim_cards(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_SIM_CARDS, column.get_values())


    def db_insert_table_sms(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_SMS, column.get_values())


    def db_insert_table_version(self, key, version):
        self.db_insert_table(SQL_INSERT_TABLE_VERSION, (key, version))

    '''
    版本检测分为两部分
    如果中间数据库结构改变，会修改db_version
    如果app增加了新的内容，需要修改app_version
    只有db_version和app_version都没有变化时，才不需要重新解析
    '''
    @staticmethod
    def need_parse(cache_db, app_version):
        if not os.path.exists(cache_db):
            return True
        db = sqlite3.connect(cache_db)
        cursor = db.cursor()
        sql = 'select key, version from version'
        row = None
        db_version_check = False
        app_version_check = False
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
        except Exception as e:
            pass

        while row is not None:
            if row[0] == VERSION_KEY_DB and row[1] == VERSION_VALUE_DB:
                db_version_check = True
            elif row[0] == VERSION_KEY_APP and row[1] == app_version:
                app_version_check = True
            row = cursor.fetchone()

        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()
        return not (db_version_check and app_version_check)

class Column(object):
    def __init__(self):
        self.source   = ''
        self.deleted  = 0
        self.repeated = 0

    def __setattr__(self, name, value):
        if not IsDBNull(value):
            self.__dict__[name] = value

    def get_values(self):
        return (self.source, self.deleted, self.repeated)

class SimCard(Column):
    def __init__(self):
        super(SimCard, self).__init__()
        self.sim_id       = None
        self.number       = None  # 手机号
        self.sync_enabled = None  # 是否同步

    def get_values(self):
        return (
                self.sim_id,
                self.number,
                self.sync_enabled,
            ) + super(SimCard, self).get_values()

class SMS(Column):
    def __init__(self):
        super(SMS, self).__init__()
        self._id                = None  # 消息ID[INT]
        self.sim_id             = None  # SIM 卡 ID[INT]
        self.sender_phonenumber = None  # 发送者手机号码[TEXT]
        self.sender_name        = None  # 发送者姓名[TEXT]
        self.read_status        = None  # 读取状态[INT], 1 已读, 0 未读
        self.type               = None  # 消息类型[INT], SMS_TYPE
        self.suject             = None  # 主题, 一般是彩信 mms 才有[TEXT]
        self.body               = None  # 内容[TEXT]
        self.send_time          = None  # 发送时间[INT]
        self.delivered_date     = None  # 送达时间
        self.is_sender          = None  # 自己是否为发送方[INT]
        self.recv_phonenumber   = None  # 接受者手机号码[TEXT]
        self.recv_name          = None  # 接受者姓名[TEXT]        
        self.smsc               = None  # 短信服务中心号码[TEXT]        

    def get_values(self):
        return (
                self._id, 
                self.sim_id, 
                self.sender_phonenumber, 
                self.sender_name, 
                self.read_status,
                self.type, 
                self.suject,   
                self.body,  
                self.send_time, 
                self.delivered_date, 
                self.is_sender, 
                self.source, 
                self.deleted, 
                self.repeated,
                self.recv_phonenumber,
                self.recv_name,
                self.smsc
            )

class GenerateModel(object):
    def __init__(self, cache_db, cachepath=None):
        self.cache_db = cache_db
        self.cachepath = cachepath

    def get_models(self):
        models = []
        self.db = sqlite3.connect(self.cache_db)
        self.cursor = self.db.cursor()

        models.extend(self._get_sms_models())

        self.cursor.close()
        self.db.close()
        return models

    def _get_sms_models(self):
        models = []
        sql = ''' select * from sms '''

        ''' sms.Body
            sms.Folder
            sms.Delivered
            sms.Read
            sms.TimeStamp
            sms.SourceFile

        table - sms
            0    _id              TEXT, 
            1    sim_id              INT,
            2    sender_phonenumber  TEXT,
            3    sender_name         TEXT,
            4    read_status         INT DEFAULT 0,
            5    type                INT,
            6    suject              TEXT,
            7    body                TEXT,
            8    send_time           INT,
            9    delivered_date      INT,
            10    is_sender           INT,
            11    source              TEXT,
            12    deleted             INT DEFAULT 0, 
            13    repeated            INT DEFAULT 0,

            14    recv_phonenumber  TEXT,
            15    recv_name         TEXT,
            16    smsc               TEXT

            SMS_TYPE_ALL    = 0
            SMS_TYPE_INBOX  = 1
            SMS_TYPE_SENT   = 2
            SMS_TYPE_DRAFT  = 3
            SMS_TYPE_OUTBOX = 4
            SMS_TYPE_FAILED = 5
            SMS_TYPE_QUEUED = 6                        
        '''
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        except:
            exc()
            return 
        while row is not None:
            if canceller.IsCancellationRequested:
                return            
            sms = ModelsV2.Base.SMS()

            if row[7] is not None:
                sms.Content = TextContent(sms)
                sms.Content.Value = row[7]

            if row[5] in range(7):
                if SMS_TYPE_TO_FOLDER[row[5]] is not None:
                    sms.Folder = SMS_TYPE_TO_FOLDER[row[5]]
                
            if row[8] is not None:
                ts = self._get_timestamp(row[8])
                if ts:
                    sms.Time = ts

            if row[9] is not None:
                ts = self._get_timestamp(row[9])
                if ts:
                    sms.DeliveredTime = ts

            # 注意优先级  row[4] read_status, row[5]: type
            sms.Status = SMSStatus.Read if row[4] == 1 else SMSStatus.Unread
            if row[5] in [2, 3, 4]:
                sms.Status = self._convert_sms_type(row[5]) 
                
            # 发件人
            _from = Contact()
            if row[2] is not None:
                _from.PhoneNumbers.Add(row[2])  # sender_phonenumber
            if row[3] is not None:
                _from.RemarkName = row[3]       # sender_name
            sms.FromSet.Add(_from)

            # 收件人
            _to = Contact()
            if row[14] is not None:
                _to.PhoneNumbers.Add(row[14])   # recv_phonenumber
            if row[15] is not None:                                     
                _to.RemarkName = row[15]        # recv_name     
            sms.ToSet.Add(_to)               

            if row[11] is not None:
                sms.SourceFile = self._get_source_file(row[11])

            if row[12] is not None:
                sms.Deleted = self._convert_deleted_status(row[12])
            models.append(sms)
            row = self.cursor.fetchone()
        return models        

    @staticmethod
    def _get_timestamp(timestamp):
        try:
            if len(str(timestamp)) >= 10:
                timestamp = int(str(timestamp)[:10]) + 28800
                ts = TimeStamp.FromUnixTime(timestamp, False)
                if ts.IsValidForSmartphone():
                    return ts
            return False
        except:
            return False

    @staticmethod
    def _convert_deleted_status(deleted):
        if deleted is None:
            return DeletedState.Unknown
        else:
            return DeletedState.Intact if deleted == 0 else DeletedState.Deleted

    def _get_source_file(self, source_file):
        if isinstance(source_file, str):
            return source_file.replace('/', '\\')
        return ''    
    
    @staticmethod
    def _convert_sms_type(sms_type):
        '''
        SMS_TYPE_ALL    = 0
        SMS_TYPE_INBOX  = 1
        SMS_TYPE_SENT   = 2
        SMS_TYPE_DRAFT  = 3
        SMS_TYPE_OUTBOX = 4
        SMS_TYPE_FAILED = 5
        SMS_TYPE_QUEUED = 6 
        '''
        if sms_type in [2,4]:  # 发件箱
            return SMSStatus.Sent
        elif sms_type == 3:    # 草稿箱
            return SMSStatus.Unsent
        # elif sms_type == 1:    # 未读


############################################
######          VMSG DECODEER         ######
############################################

# vmsg format

# BEGIN:VMSG
# VERSION:1.1
# X-IRMS-TYPE:MSG
# X-MESSAGE-TYPE:DELIVER
# X-MESSAGE-STATUS:READ
# X-MESSAGE-SLOT:0
# X-MESSAGE-LOCKED:UNLOCKED
# BEGIN:VCARD
# VERSION:2.1
# TEL:+86138xxxxxxxx
# END:VCARD
# BEGIN:VBODY
# Date:2014/06/29 09:38:53 GMT
# Subject;ENCODING=QUOTED-PRINTABLE;CHARSET=UTF-8:=30=31=32=33=34=35=36
# END:VBODY
# END:VMSG

# csv format
# id: integer number
# tel: phone number
# type: 'RECEIVED' or 'SEND'
# date: 2015-09-06T20:47:01.573Z
# content:
# end tag: ',y,-1'
#
# example:
# 788,10086,RECEIVED,2013-09-06T20:47:01.573Z,示例内容,y,-1


class VMSGDecoder:
    """vmsg format"""
    BEGIN = 'BEGIN'
    END = 'END'

    X_MESSAGE_TYPE = 'X-MESSAGE-TYPE'

    TVMSG = 'VMSG'
    TVCARD = 'VCARD'
    TVBODY = 'VBODY'

    X_BOX = 'X-BOX'
    X_READ = 'X-READ'
    X_SIMID = 'X-SIMID'
    X_LOCKED = 'X-LOCKED'
    X_TYPE = 'X-TYPE'

    INBOX = 'INBOX'
    READ = 'READ'
    UNREAD = 'UNREAD'

    TDELIVER = 'DELIVER'
    TSUBMIT = 'SUBMIT'

    TTEL = 'TEL'
    TDATE = 'Date'
    TSUBJECT = 'Subject'

    def __init__(self):
        pass
            
    def build_from_message(self, fvmsg, fcsv):
        with open(fvmsg, 'r') as f:
            v_l = []  # result
            stack = []
            for line in f:
                line = line.strip()
                if line.startswith(VMSG.BEGIN):
                    self.process_start_tag(line, stack, v_l)
                elif line.startswith(VMSG.END):
                    self.process_end_tag(line, stack, v_l)
                else:
                    self.process_attribute(line, stack, v_l)

        with open(fcsv, 'wb') as fout:
            item_id = 1
            for item in v_l:
                fout.write(json.dumps(item))
                fout.write(',')
                item_id += 1

    def process_start_tag(self, stream, stack, v):
        _tag, _value = self._get_tag(stream)
        #print('process_start_tag:', tag)
        if len(_value) == 0:
            raise ValueError
        #print('pushing:', tag)
        stack.append(_value)
        if _value == VMSG.TVMSG:
            item = {'status': 'y', 'end': '-1'}
            v.append(item)

    def process_end_tag(self, stream, stack, v):
        _tag, _value = self._get_tag(stream)
        #print('process_end_tag:', tag)
        if len(_value) == 0:
            raise ValueError
        if _value != stack[-1]:
            print(_tag, stack[-1])
            raise ValueError
        stack.pop()
        #print('poping:', stream)

        if _tag == VMSG.TVMSG:
            # decode content here
            item = v[-1]
            item['content'] = _value

    def process_attribute(self, stream, stack, v):
        if len(stack) > 0:
            tag = stack[-1]
            if tag == VMSG.TVMSG:
                if stream.startswith(VMSG.X_MESSAGE_TYPE):
                    self.process_message_type(stream, v)
            if tag == VMSG.TVCARD:
                if stream.startswith(VMSG.TTEL):
                    self.process_tel(stream, v)
            elif tag == VMSG.TVBODY:
                if stream.startswith(VMSG.X_BOX):
                    self.process_box(stream, v)
                elif stream.startswith(VMSG.X_READ):
                    pass
                elif stream.startswith(VMSG.X_SIMID):
                    pass
                elif stream.startswith(VMSG.X_LOCKED):
                    pass
                elif stream.startswith(VMSG.X_TYPE):
                    pass
                elif stream.startswith(VMSG.TDATE):
                    self.process_date(stream, v)
                elif stream.startswith(VMSG.TSUBJECT):
                    self.process_subject(stream, v)
                # else:
                #     # continue subject
                #     self.process_continue_subject(stream, v)

    def process_message_type(self, stream, v):
        _type= stream[15:]
        if _type== VMSG.TSUBMIT:
            _type= 'SENT'
        else:
            _type= 'RECEIVED'
        item = v[-1]
        item['type'] = _type

    def process_box(self, stream, v):
        _tag, _value = self._get_tag(stream)
        if _tag == VMSG.INBOX:
            item = v[-1]
            item['box'] = _value

    def process_status(self, stream, v):
        _tag, _value = self._get_tag(stream)
        if _tag == VMSG.X_READ:
            item = v[-1]
            item['status'] = _value

    def process_tel(self, stream, v):
        tel = stream[4:]
        if tel.startswith("+86"):
            tel = tel.replace("+86", "")
        item = v[-1]
        item['tel'] = tel

    def process_date(self, stream, v):
        date = stream[5:24]
        date = date.replace(' ', 'T')
        date = date.replace('/', '-')
        r = '%03d' % (random.randint(0, 999))
        date = date + '.' + r + 'Z'
        item = v[-1]
        item['date'] = date

    def process_subject(self, stream, v):
        s = stream.split(':', 1)
        content = s[-1]
        item = v[-1]
        item['content'] = content.decode('utf8', 'ignore')

    def process_continue_subject(self, stream, v):
        content = stream
        item = v[-1]
        if 'content' in item:
            try:
                item['content'] = item['content'] + content.decode('utf8', 'ignore')
            except Exception as e:
                print(e)

        else:
            item['content'] = content
           
    def decode_subject(self, content):
        #b = bytearray.fromhex(item['content'])
        result = []
        contents = content.split('=')
        for c in contents:
            s = ''
            if len(c) > 2:
                c1 = c[:2]
                c2 = c[2:]
                # try:
                b = bytearray.fromhex(c1)
                s = b.decode(encoding='utf8', errors='ignore')
                s = c1.decode(encoding='utf8', errors='ignore')
                # except:
                result.append(s)
                result.append(c2.decode(encoding='utf8', errors='ignore'))
            elif len(c) == 2:
                try:
                    b = bytearray.fromhex(c)
                    s = b.decode(encoding='utf8', errors='ignore')
                except:
                    s = c.decode(encoding='utf8', errors='ignore')
                result.append(s)
            else:
                s = c.decode(encoding='utf8', errors='ignore')
                result.append(s)

        content = ''.join(result)
        return content

    def _get_tag(self, stream):
        _p = r'(.*?):(.*)'
        res = re.search(_p, stream)
        if res and res.group(1) and res.group(2):
            return (res.group(1), res.group(2))
        else:
            return ('', '')
        