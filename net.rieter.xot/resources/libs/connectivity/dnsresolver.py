# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import socket


class DnsResolver:
    def __init__(self, server):
        self.__server = server

    def GetHost(self, url):
        start = url.index("//")
        start += 2
        end = url.find("/", start)
        if end > 0:
            return url[start:end]
        else:
            return url[start:]

    def ResolveAddress(self, address, types=(1, )):
        s = socket.socket(type=socket.SOCK_DGRAM)
        q = self.__CreateRequest(address)
        s.settimeout(10.0)
        s.sendto(q, (self.__server, 53))
        r = s.recvfrom(1024)
        if types is None:
            return self.__ParseResponse(r[0])
        else:
            return filter(lambda (x, y): x in types, self.__ParseResponse(r[0]))

    def __CreateRequest(self, address):
        # noinspection PyListCreation
        q = []
        q.append("\x00\x01")  # sequence
        q.append("\x01\x00")  # standard request
        q.append("\x00\x01")  # questions
        q.append("\x00\x00")  # answer RRS
        q.append("\x00\x00")  # authority RRS
        q.append("\x00\x00")  # additional RRS

        # queryParts = ("alphabet", "rieter", "net")
        addressParts = address.split(".")
        for p in addressParts:
            q.append(chr(len(p)))
            q.append(p)
        q.append("\x00")
        q.append("\x00\x01")  # Type: A
        q.append("\x00\x01")  # Class: IN
        return "".join(q)

    # noinspection PyUnusedLocal
    def __ParseResponse(self, response):
        results = []
        reader = DnsResolver.__ByteStringReader(response)
        transactionId = reader.ReadInteger()
        flags = reader.ReadInteger()
        questions = reader.ReadInteger()
        answers = reader.ReadInteger()
        authority = reader.ReadInteger()
        additional = reader.ReadInteger()
        while True:
            length = reader.ReadInteger(1)
            if length == 0:
                break
            addressPart = reader.ReadString(length)
            # print addressPart
            continue
        dnsType = reader.ReadInteger()
        direction = reader.ReadInteger()

        for i in range(0, answers):
            name = reader.ReadFullString()
            # print "Name: %s" % (name,)

            answerType = reader.ReadInteger()
            direction = reader.ReadInteger()
            ttl = reader.ReadInteger(4)
            length = reader.ReadInteger()
            address = []
            if answerType == 1:
                for s in range(0, length):
                    address.append(str(reader.ReadInteger(1)))
                address = ".".join(address)
            elif answerType == 5:
                address = reader.ReadFullString()
            else:
                raise Exception("wrong type: %s" % (answerType, ))

            # print ip
            #print ip
            results.append((answerType, address))
        return results

    class __ByteStringReader:
        def __init__(self, byteString):
            self.__byteString = byteString
            self.__pointer = 0
            self.__resumePoint = 0
            # print "Input: %r" % (byteString, )

        def ReadInteger(self, length=2):
            val = self.ReadString(length)
            val = self.__ByteToInt(val)
            # print val
            return val

        def ReadFullString(self):
            value = ""
            while True:
                length = self.ReadInteger(1)
                if length == 0:
                    break
                elif length == 192:  # \xC0
                    # pointer found
                    newPointer = self.ReadInteger(1)
                    oldPointer = self.__pointer
                    self.__pointer = newPointer
                    value += self.ReadFullString()
                    self.__pointer = oldPointer
                    break
                value += self.ReadString(length)
                value += "."
                continue
            return value.strip('.')

        def ReadString(self, length):
            # print "from: %s to %s" % (self.__pointer, self.__pointer + length)
            val = self.__byteString[self.__pointer:self.__pointer + length]
            #print "Value %r" % (val, )
            self.__pointer += length
            return val

        def __ByteToInt(self, byteString):
            return int(byteString.encode('hex'), 16)
