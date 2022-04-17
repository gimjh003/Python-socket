# 메시지 식별 번호
REQ_FILE_SEND = 0x01 # 파일 전송 요청
REP_FILE_SEND = 0x02 # 파일 전송 요청에 대한 응답
FILE_SEND_DATA = 0x03 # 파일 전송 데이터
FILE_SEND_RES = 0x04 # 파일 수신 결과

# 메시지 분할 여부
NOT_FRAGMENTED = 0x00 # 미분할
FRAGMENTED = 0x01 # 분할

# 분할된 메시지의 마지막인지의 여부
NOT_LASTMSG = 0x00 # 마지막 메시지가 아님
LASTMSG = 0x01 # 마지막 메시지임

# 파일 전송 승인 여부 
ACCEPTED = 0x00 # 승인
DENIED = 0x01 # 거절

# 파일 전송 성공 여부
FAIL = 0x00 # 실패
SUCCESS = 0x01 # 성공

# 데이터 변환 기본형
class ISerializable:
    def GetBytes(self):
        pass

    def GetSize():
        pass

class Message(ISerializable):
    def __init__(self):
        self.Header = ISerializable()
        self.Body = ISerializable()
    
    def GetBytes(self):
        buffer = bytes(self.GetSize())
        header = self.Header.GetBytes()
        body = self.Body.GetBytes()

        return header+body
    
    def GetSize(self):
        return self.Header.GetSize() + self.Body.GetSize()