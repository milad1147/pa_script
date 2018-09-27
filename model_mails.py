# -*- coding: utf-8 -*-

from PA_runtime import *
import clr
clr.AddReference('System.Core')
clr.AddReference('System.Xml.Linq')
clr.AddReference('System.Data.SQLite')
del clr

from System.IO import MemoryStream
from System.Text import Encoding
from System.Xml.Linq import *
from System.Linq import Enumerable
from System.Xml.XPath import Extensions as XPathExtensions
import System.Data.SQLite as SQLite

import os
import sqlite3
import traceback

SQL_CREATE_TABLE_MAILS = '''
    create table if not exists mails(
        mailId INTEGER,
        accountId INTEGER,
        subject TEXT,
        abstract TEXT,
        fromEmail TEXT, 
        receiveUtc INTEGER,
        size INTEGER,
        tos TEXT,
        cc TEXT,
        bcc TEXT,
        ip TEXT,
        isForward INTEGER,
        isRead INTEGER,
        isRecalled INTEGER,
        sendStatus INTEGER,
        account_email TEXT,
        alias TEXT,
        mail_folder TEXT,
        content TEXT,
        downloadUtc TEXT,
        downloadSize TEXT,
        attachName TEXT,
        exchangeField TEXT,
        attachDir TEXT,
        attach_object TEXT,
        folderId INTEGER,
        attachId INTEGER,
        source TEXT,
        deleted INT,
        repeated INT
    )'''

SQL_INSERT_TABLE_MAILS = '''
    insert into mails(mailId, accountId, subject, abstract, fromEmail, receiveUtc, size, tos, cc, bcc, ip, isForward, isRead, isRecalled, sendStatus, account_email, alias,
    mail_folder, content, downloadUtc, downloadSize, attachName, exchangeField, attachDir, attach_object, folderId, attachId, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

SQL_CREATE_TABLE_ACCOUNT = '''
    create table if not exists accounts(
        accountId INTEGER,
        alias TEXT,
        accountEmail TEXT,
        loginDate REAL,
        accountImage BLOB,
        accountSign BLOB,
        password TEXT,
        source TEXT,
        deleted INT,
        repeated INT
    )'''

SQL_INSERT_TABLE_ACCOUNT = '''
    insert into accounts(accountId, alias, accountEmail, loginDate, accountImage, accountSign, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?, ?, ?)'''


SQL_CREATE_TABLE_CONTACT = '''
    create table if not exists contact(
        contactName TEXT,
        contactBirthday TEXT,
        contactDepartment TEXT,
        contactFamilyAddress TEXT,
        contactMark TEXT,
        contactMobile TEXT,
        contactTelephone TEXT,
        contactEmail TEXT,
        contactNick TEXT,
        groupName TEXT,
        alias TEXT,
        accountEmail TEXT,
        accountId INTEGER,
        contactId INTEGER,
        source TEXT,
        deleted INT,
        repeated INT
    )'''

SQL_INSERT_TABLE_CONTACT = '''
    insert into contact(contactName, contactBirthday, contactDepartment, contactFamilyAddress, contactMark,
    contactMobile, contactTelephone, contactEmail, contactNick, groupName, alias, accountEmail, accountId, contactId, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

SQL_CREATE_TABLE_MAIL_FOLDER = '''
    create table if not exists mail_folder(
        folderType TEXT,
        folderName TEXT,
        accountNick TEXT,
        accountEmail,TEXT,
        source TEXT,
        deleted INT,
        repeated INT
    )'''

SQL_INSERT_TABLE_MAIL_FOLDER = '''
    insert into mail_folder(folderType, folderName, accountNick, accountEmail, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?)'''

SQL_CREATE_TABLE_ATTACH = '''
    create table if not exists attach(
        accountNick TEXT,
        accountEmail TEXT,
        subject TEXT,
        downloadUtc TEXT,
        downloadSize TEXT,
        fromEmail TEXT,
        fromNick TEXT,
        mailUtc REAL,
        attachName TEXT,
        exchangeField TEXT,
        attachType TEXT,
        attachDir TEXT,
        emailFolder TEXT,
        mailId INT,
        source TEXT,
        deleted INT,
        repeated INT
    )'''

SQL_INSERT_TABLE_ATTACH = '''
    insert into attach(accountNick, accountEmail, subject, downloadUtc, downloadSize,
    fromEmail, fromNick, mailUtc, attachName, exchangeField, attachType, attachDir, emailFolder, mailId, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

SQL_CREATE_TABLE_TODO = '''
    create table if not exists todo(
        content TEXT,
        createdTime INTEGER,
        reminderTime INTEGER,
        isdone INTEGER,
        isdeleted INTEGER,
        source TEXT,
        deleted INT, 
        repeated INT
    )'''

SQL_INSERT_TABLE_TODO = '''
    insert into todo(content, createdTime, reminderTime, isdone, source, deleted, repeated)
        values(?, ?, ?, ?, ?, ?, ?)'''


SQL_CREATE_TABLE_SEARCH = ''''''

SQL_INSERT_TABLE_SEARCH = ''''''


class MM(object):
    def __init__(self):
        self.db = None
        self.db_cmd = None
        self.db_trans = None
        
    def db_create(self, db_path):
        if os.path.exists(db_path):
            os.remove(db_path)
        self.db = SQLite.SQLiteConnection('Data Source = {}'.format(db_path))
        self.db.Open()
        self.db_cmd = SQLite.SQLiteCommand(self.db)
        self.db_trans = self.db.BeginTransaction()

        self.db_create_table()
        self.db_commit()

    def db_commit(self):
        if self.db_cmd is not None:        
            if self.db_trans is not None:
                self.db_trans.Commit()
            self.db_trans = self.db.BeginTransaction()

    def db_update(self, SQL, values=None):
        if self.db_cmd is not None:
            self.db_cmd.CommandText = SQL
            self.db_cmd.Parameters.Clear()            
            for v in values:
                param = self.db_cmd.CreateParameter()
                param.Value = v
                self.db_cmd.Parameters.Add(param)     
            try:
                self.db_cmd.ExecuteNonQuery()
            except:
                traceback.print_exc()

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
            self.db_cmd.CommandText = SQL_CREATE_TABLE_ACCOUNT
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_ATTACH
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_CONTACT
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_MAIL_FOLDER
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_MAILS
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_SEARCH
            self.db_cmd.ExecuteNonQuery()
            self.db_cmd.CommandText = SQL_CREATE_TABLE_TODO
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

    def db_insert_table_mails(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_MAILS, column.get_values())
        
    
    def db_insert_table_account(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_ACCOUNT, column.get_values())

    def db_insert_table_contact(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_CONTACT, column.get_values())

    def db_insert_table_mail_folder(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_MAIL_FOLDER, column.get_values())

    def db_insert_table_attach(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_ATTACH, column.get_values())

    def db_insert_table_todo(self, column):
        self.db_insert_table(SQL_INSERT_TABLE_TODO, column.get_values())

    def db_insert_table_search(self, column):
        pass


class Column(object):
    def __init__(self):
        self.source = ''
        self.deleted = 0
        self.repeated = 0

    def __setattr__(self, name, value):
        if IsDBNull(value):
            self.__dict__[name] = None
        else:
            if isinstance(value, str):
                value = re.compile('[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f]').sub(' ', value)                 
            self.__dict__[name] = value

    def get_values(self):
        return (self.source, self.deleted, self.repeated)


class Mails(Column):
    def __init__(self):
        super(Mails, self).__init__()
        self.mailId = None
        self.accountId = None
        self.subject = None
        self.abstract = None
        self.fromEmail = None
        self.receiveUtc = None
        self.size = None
        self.tos = None
        self.cc = None
        self.bcc = None
        self.ip = None
        self.isForward = None
        self.isRead = None
        self.isRecalled = None
        self.sendStatus = None
        self.account_email = None
        self.alias = None
        self.mail_folder = None
        self.content = None
        self.downloadUtc = None
        self.downloadSize = None
        self.attachName = None
        self.exchangeField = None
        self.attachDir = None
        self.attach_object = None
        self.folderId = None
        self.attachId = None

    def get_values(self):
        return (self.mailId, self.accountId, self.subject, self.abstract, 
        self.fromEmail, self.receiveUtc,self.size,
        self.tos, self.cc, self.bcc, self.ip,self.isForward,
        self.isRead,self.isRecalled,self.sendStatus,self.account_email,self.alias,
        self.mail_folder, self.content, self.downloadUtc, 
        self.downloadSize, self.attachName, self.exchangeField, self.attachDir, self.attach_object, self.folderId, self.attachId) + super(Mails, self).get_values()
   

class Accounts(Column):
    def __init__(self):
        super(Accounts, self).__init__()
        self.accountId = None
        self.alias = None
        self.accountEmail = None
        self.loginDate = None
        self.accountImage = None
        self.accountSign = None

    def get_values(self):
        return (self.accountId, self.alias, self.accountEmail, self.loginDate,
        self.accountImage, self.accountSign) + super(Accounts,self).get_values()



class Contact(Column):
    def __init__(self):
        super(Contact, self).__init__()
        self.contactName = None
        self.contactBirthday = None
        self.contactDepartment = None
        self.contactFamilyAddress = None
        self.contactMark = None
        self.contactMobile = None
        self.contactTelephone = None
        self.contactEmail = None
        self.contactNick = None
        self.groupName = None
        self.alias = None
        self.accountEmail = None
        self.accountId = None
        self.contactId = None

    def get_values(self):
        return(self.contactName, self.contactBirthday, self.contactDepartment,
        self.contactFamilyAddress, self.contactMark, self.contactMobile, self.contactTelephone,
        self.contactEmail,self.contactNick, self.groupName, self.alias, self.accountEmail, self.accountId, self.contactId) + super(Contact, self).get_values()



class MailFolder(Column):
    def __init__(self):
        super(MailFolder, self).__init__()
        self.folderTtpe = None
        self.folderName = None
        self.accountNick = None
        self.accountEmail = None

    def get_values(self):
        return (self.folderTtpe, self.folderName, self.accountNick, self.accountEmail) + super(MailFolder, self).get_values()


class Attach(Column):
    def __init__(self):
        super(Attach, self).__init__()
        self.accountNick = None
        self.acocuntEmail = None
        self.subject = None
        self.downloadUtc = None
        self.downloadSize = None
        self.fromEmail = None
        self.fromNick = None
        self.mailUtc = None
        self.attachName = None
        self.exchangeField = None
        self.attachType = None
        self.attachDir = None
        self.emailFolder = None
        self.mailId = None

    def get_values(self):
        return (self.accountNick, self.acocuntEmail, self.subject, self.downloadUtc,
        self.downloadSize, self.fromEmail, self.fromNick, self.mailUtc,
        self.attachName, self.exchangeField, self.attachType, self.attachDir, self.emailFolder,
        self.mailId) + super(Attach, self).get_values()


class Todo(Column):
    def __init__(self):
        super(Todo, self).__init__()
        self.content = None
        self.createdTime = None
        self.reminderTime = None
        self.isdone = None

    def get_values(self):
        return (self.content,
                self.createdTime,
                self.reminderTime,
                self.isdone) + super(Todo, self).get_values()


class Search(Column):
    pass


class Generate(object):
    def __init__(self, db_cache):
        self.db_cache = db_cache
        
    def get_models(self):
        models = []
        self.db = sqlite3.connect(self.db_cache)
        self.cursor = self.db.cursor()
        models.extend(self._get_mails_models())
        models.extend(self._get_accounts_models())
        models.extend(self._get_contact_models())
        models.extend(self._get_mail_folder_models())
        models.extend(self._get_attach_models())
        models.extend(self._get_search_models())
        self.cursor.close()
        self.db.close()
        return models

    def _get_mails_models(self):
        models = []
        sql = '''select a.*, accounts.accountEmail, accounts.loginDate from (
            select mailId,subject,abstract,fromEmail,receiveUtc,size,tos,cc,bcc,ip,isForward,
            isRead,isRecalled,sendStatus,account_email,alias,mail_folder,content,group_concat(downloadUtc) as downloadUtc,
            group_concat(downloadSize) as downloadSize,group_concat(attachName) as attachName,group_concat(attachDir) as attachDir,source,repeated,deleted,accountId
            from mails group by mailId) as a left join accounts on a.accountId = accounts.accountId
            '''
        row = None
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        except Exception as e:
            print(e)
        while row is not None:
            canceller.ThrowIfCancellationRequested()
            email = Generic.Email()
            if row[22] not in [None, '']:
                email.SourceFile.Value = self._get_source_file(row[22])
            if row[24] is not None:
                email.Deleted = self._convert_deleted_status(row[24])
            if row[16] is not None:
                email.Folder.Value = row[16]
                if row[16] == '已发送':
                    email.Status.Value = MessageStatus.Sent
                elif row[16] == '收件箱':
                    email.Status.Value = MessageStatus.Unsent
                else:
                    if row[11] is not None:
                        email.Status.Value = MessageStatus.Unread if row[11] == 0 else MessageStatus.Read
            else:
                email.Folder.Value = '已删除'
            if row[1] is not None:
                email.Subject.Value = row[1]
            if row[17] is not None:
                email.Body.Value = row[17]
            if row[4] is not None:
                email.TimeStamp.Value = TimeStamp.FromUnixTime(row[4], False) if len(str(row[4])) == 10 else TimeStamp.FromUnixTime(int(str(row[4])[0:10:1]), False) if len(str(row[4]))>10 else TimeStamp.FromUnixTime(0, False)
            if row[3] is not None:
                party = Generic.Party()
                party.Identifier.Value = row[3]
                if row[9] is not None:
                    party.IPAddresses.Add(str(row[9]))
                    if row[4] is not None:                
                        party.DatePlayed.Value = TimeStamp.FromUnixTime(row[4], False) if len(str(row[4])) == 10 else TimeStamp.FromUnixTime(int(str(row[4])[0:10:1]), False) if len(str(row[4]))>10 else TimeStamp.FromUnixTime(0, False)
                email.From.Value = party
            if row[6] is not None:
                tos = row[6].split(' ')
                for t in range(len(tos)-1):
                    if t%2 == 0:
                        party = Generic.Party()
                        party.Identifier.Value = tos[t]
                        party.Name.Value = tos[t+1]
                        if row[4] is not None:
                            party.DatePlayed.Value = TimeStamp.FromUnixTime(row[4], False) if len(str(row[4])) == 10 else TimeStamp.FromUnixTime(int(str(row[4])[0:10:1]), False) if len(str(row[4]))>10 else TimeStamp.FromUnixTime(0, False)
                        email.To.Add(party)
            if row[7] is not None:
                cc = row[7].split(' ')
                for c in range(len(cc)-1):
                    if c%2 == 0:
                        party = Generic.Party()
                        party.Identifier.Value = cc[c]
                        party.Name.Value = cc[c+1]
                        if row[4] is not None:
                            party.DatePlayed.Value = TimeStamp.FromUnixTime(row[4], False) if len(str(row[4])) == 10 else TimeStamp.FromUnixTime(int(str(row[4])[0:10:1]), False) if len(str(row[4]))>10 else TimeStamp.FromUnixTime(0, False)
                        email.Cc.Add(party)
            if row[8] is not None:
                bcc = row[8].split(' ')
                for b in range(len(bcc)-1):
                    if b%2 == 0:
                        party = Generic.Party()
                        party.Identifier.Value = bcc[b]
                        party.Name.Value = tos[t+1]
                        if row[4] is not None:
                            party.DatePlayed.Value = TimeStamp.FromUnixTime(row[4], False) if len(str(row[4])) == 10 else TimeStamp.FromUnixTime(int(str(row[4])[0:10:1]), False) if len(str(row[4]))>10 else TimeStamp.FromUnixTime(0, False)
                        email.Bcc.Add(party)
            if row[18] is not None:
                try:
                    for a in range(len(row[18].split(','))):
                        attachment = Generic.Attachment()
                        if row[20] is not None:
                            attachment.Filename.Value = row[20].split(',')[a]
                        if row[21] is not None:
                            attachment.URL.Value = row[21].split(',')[a]
                        if row[18] is not None:
                            attachment.DownloadTime.Value = TimeStamp.FromUnixTime(int(float(row[18].split(',')[a])),False)
                        if row[19] is not None:
                            attachment.Size.Value = int(row[19].split(',')[a])
                        email.Attachments.Add(attachment)
                except Exception as e:
                    pass
            if row[2] is not None:
                email.Abstract.Value = row[2]
            if row[5] is not None:
                email.Size.Value = row[5]
            if row[12] is not None:
                email.IsRecall.Value = row[12]
            user = Common.User()
            if row[15] is not None:
                user.Name.Value = row[15]
            if row[26] is not None:
                user.Username.Value = row[26]
            if row[27] is not None:
                user.LastLoginTime.Value = TimeStamp.FromUnixTime(row[27], False) if len(str(row[27])) == 10 else TimeStamp.FromUnixTime(int(str(row[27])[0:10:1]), False) if len(str(row[27]))>10 else TimeStamp.FromUnixTime(0, False)
            if row[14] is not None:
                user.Email.Value = row[14]
            if row[25] is not None:
                user.ID.Value = str(row[25])
                email.OwnerUserID.Value = str(row[25])
            email.OwnerUser.Value = user
            if row[25] is not None:
                email.Account.Value = str(row[26])
            models.append(email)
            row = self.cursor.fetchone()
        return models

    def _get_accounts_models(self):
        models = []
        sql = '''
            select * from accounts where deleted = 0
        ''' 
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            while row is not None:
                canceller.ThrowIfCancellationRequested()
                user = Common.User()
                if row[1] is not None:
                    user.Name.Value = row[1]
                if row[2] is not None:
                    user.Email.Value = row[2]
                if row[3] is not None:
                    user.LastLoginTime.Value = TimeStamp.FromUnixTime(row[3], False) if len(str(row[3])) == 10 else TimeStamp.FromUnixTime(int(str(row[3])[0:10:1]), False) if len(str(row[3]))>10 else TimeStamp.FromUnixTime(0, False)
                if row[0] is not None:
                    user.ID.Value = str(row[0])
                if row[8] is not None:
                    user.Deleted = DeletedState.Intact if row[8] == 0 else DeletedState.Deleted
                models.append(user)
                row = self.cursor.fetchone()
        except:
            pass
        return models

    def _get_contact_models(self):
        models = []
        sql = ''' select * from contact '''
        row = None
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
        except Exception as e:
            print(e)
        while row is not None:
            canceller.ThrowIfCancellationRequested()
            friend = Common.Friend()
            if row[-3] not in [None, '']:
                friend.SourceFile.Value = self._get_source_file(row[-3])
            if row[-2] is not None:
                friend.Deleted = self._convert_deleted_status(row[-2])
            if row[12] is not None:
                friend.OwnerUserID.Value = str(row[12])
            if row[0] is not None:
                friend.FullName.Value = row[0]
            if row[2] is not None:
                friend.CompanyName.Value = row[2]
            addr = Contacts.StreetAddress()
            if row[3] is not None:
                addr.FullName.Value = row[3]
                friend.LivingAddresses.Add(addr)
            if row[4] is not None:
                friend.Remarks.Value = row[4]
            if row[5] is not None:
                friend.PhoneNumber.Value = row[5]
            if row[7] is not None:
                friend.Email.Value = row[7]
            if row[8] is not None:
                friend.Name.Value = row[8]
            models.append(friend)
            row = self.cursor.fetchone()
        return models

    def _get_mail_folder_models(self):
        models = []
        return models

    def _get_attach_models(self):
        models = []
        return models

    def _get_search_models(self):
        models = []
        return models

    @staticmethod
    def _convert_deleted_status(deleted):
        if deleted is None:
            return DeletedState.Unknown
        else:
            return DeletedState.Intact if deleted == 0 else DeletedState.Deleted

    def _get_source_file(self, source_file):
        if isinstance(source_file, str):
            return source_file.replace('/', '\\')
        return source_file

    def _get_timestamp(self, timestamp):
        """  """
        try:
            if isinstance(timestamp, (long, float, str)) and len(str(timestamp)) > 10:
                timestamp = int(str(timestamp)[:10])
            if isinstance(timestamp, int) and len(str(timestamp)) == 10:
                ts = TimeStamp.FromUnixTime(timestamp, False)
                if not ts.IsValidForSmartphone():
                    ts = None
                return ts
        except:
            return None



