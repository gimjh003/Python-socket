import os
import re
import sys
import socket
import socketserver
import struct

import message
from message import Message

from message_header import Header
from message_body import BodyRequest
from message_body import BodyResponse
from message_body import BodyData
from message_body import BodyResult

from message_util import MessageUtil

CHUNK_SIZE = 4096
upload_dir = ''

class FileReceiveHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("클라이언트 접속 : {0}".format(self.client_address[0]))
        client = self.request # client socket
        reqMsg = MessageUtil.receive(client)
        if reqMsg.Header.MSGTYPE != message.REQ_FILE_SEND:
            client.close()
            return

        reqBody = BodyRequest(None)

        print("파일 업로드 요청이 왔습니다. 수락하시겠습니까? yes/no")
        answer = sys.stdin.readline()
        
        rspMsg = Message()
        rspMsg.Body = BodyResponse(None)
        rspMsg.Body.MSGID = reqMsg.Header.MSGID
        rspMsg.Body.RESPONSE = message.ACCEPTED

        rspMsg.Header = Header(None)

        msgId = 0
        rspMsg.Header.MSGID = msgId
        msgId = msgId + 1
        rspMsg.Header.MSGTYPE = message.REP_FILE_SEND
        rspMsg.Header.BODYLEN = rspMsg.Body.GetSize()
        rspMsg.Header.FRAGMENTED = message.NOT_FRAGMENTED
        rspMsg.Header.LASTMSG = message.LASTMSG
        rspMsg.Header.SEQ = 0

        if answer.strip() != "yes":
            rspMsg.Body = BodyResponse(None)
            rspMsg.Body.MSGID = reqMsg.Header.MSGID
            rspMsg.Body.RESPONSE = message.DENIED

            MessageUtil.send(client, rspMsg)
            client.close()
            return
        else:
            MessageUtil.send(client, rspMsg)
            print("파일 전송을 시작합니다...")

            fileSize = reqMsg.Body.FILESIZE
            fileName = reqMsg.Body.FILENAME
            recvFileSize = 0
            with open(upload_dir + "\\" + fileName, 'wb') as file:
                dataMsgId = -1
                prevSeq = 0

                while True:
                    reqMsg = MessageUtil.receive(client)
                    if reqMsg == None: # 버퍼에 아무것도 없음. 전송 완료 (헤더)
                        break
                    print("#", end="")
                    
                    if reqMsg.Header.MSGTYPE != message.FILE_SEND_DATA:
                        break

                    if dataMsgId == -1:
                        dataMsgId = reqMsg.Header.MSGID
                    elif dataMsgId != reqMsg.Header.MSGID:
                        break

                    if prevSeq != reqMsg.Header.SEQ: # 순서 어긋나면 전송 중단
                        print("{0}, {1}".format(prevSeq, reqMsg.Header.SEQ))
                        break

                    prevSeq += 1

                    recvFileSize += reqMsg.GetSize()
                    file.write(reqMsg.Body.GetBytes()) # 메시지를 받아 서버에서 생성한 파일에 기록
                    
                    if reqMsg.Header.LASTMSG == message.LASTMSG: # 마지막 메시지면 반복문을 빠져나옴
                           break

                file.close()

                print()
                print("파일 크기 : {0} bytes".format(fileSize))
                print("수신 파일 크기 : {0} bytes".format(recvFileSize))

                rstMsg = Message()
                rstMsg.Body = BodyResult(None)
                rstMsg.Body.MSGID = reqMsg.Header.MSGID
                rstMsg.Body.RESULT = message.SUCCESS

                rstMsg.Header = Header(None)
                rstMsg.Header.MSGID = msgId
                msgId += 1
                rstMsg.Header.MSGTYPE = message.FILE_SEND_RES
                rstMsg.Header.BODYLEN = rstMsg.Body.GetSize()
                rstMsg.Header.FRAGMENTED = message.NOT_FRAGMENTED
                rstMsg.Header.LASTMSG = message.LASTMSG
                rstMsg.Header.SEQ = 0

                if fileSize == recvFileSize: # 전송 요청에 있었던 파일 크기와 받은 파일 크기를 비교해서 같으면 성공으로 메시지를 보냄
                    MessageUtil.send(client, rstMsg)
                else: # 파일 크기에 이상이 있다면 실패 메시지를 보냄
                    rstMsg.Body = BodyResult(None)
                    rstMsg.Body.MSGID = reqMsg.Header.MSGID
                    rstMsg.Body.RESULT = message.FAIL
                    MessageUtil.send(client, rstMsg)
                
            print("파일 전송을 마쳤습니다.")
            client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법 : {0} <Directory>".format(sys.argv[0]))
        sys.exit(0)
    upload_dir = sys.argv[1]
    if os.path.isdir(upload_dir) == False:
        os.mkdir(upload_dir)

    bindPort = 5425
    server = None
    try:
        server = socketserver.TCPServer(('', bindPort), FileReceiveHandler)
        print("파일 업로드 서버 시작...")
        server.serve_forever()
    except Exception as err:
        print(err)
    
    print("서버를 종료합니다.")