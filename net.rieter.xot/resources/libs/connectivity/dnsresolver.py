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

    def get_host(self, url):
        start = url.index("//")
        start += 2
        end = url.find("/", start)
        if end > 0:
            return url[start:end]
        else:
            return url[start:]

    def resolve_address(self, address, types=(1,)):
        s = socket.socket(type=socket.SOCK_DGRAM)
        q = self.__create_request(address)
        s.settimeout(10.0)
        s.sendto(q, (self.__server, 53))
        r = s.recvfrom(1024)
        if types is None:
            return self.__parse_response(r[0])
        else:
            return filter(lambda (x, y): x in types, self.__parse_response(r[0]))

    def __create_request(self, address):
        # noinspection PyListCreation
        q = []
        q.append("\x00\x01")  # sequence
        q.append("\x01\x00")  # standard request
        q.append("\x00\x01")  # questions
        q.append("\x00\x00")  # answer RRS
        q.append("\x00\x00")  # authority RRS
        q.append("\x00\x00")  # additional RRS

        # queryParts = ("alphabet", "rieter", "net")
        address_parts = address.split(".")
        for p in address_parts:
            q.append(chr(len(p)))
            q.append(p)
        q.append("\x00")
        q.append("\x00\x01")  # Type: A
        q.append("\x00\x01")  # Class: IN
        return "".join(q)

    # noinspection PyUnusedLocal
    def __parse_response(self, response):
        results = []
        reader = DnsResolver.__ByteStringReader(response)
        transaction_id = reader.read_integer()
        flags = reader.read_integer()
        questions = reader.read_integer()
        answers = reader.read_integer()
        authority = reader.read_integer()
        additional = reader.read_integer()
        while True:
            length = reader.read_integer(1)
            if length == 0:
                break
            address_part = reader.read_string(length)
            # print addressPart
            continue
        dns_type = reader.read_integer()
        direction = reader.read_integer()

        for i in range(0, answers):
            name = reader.read_full_string()
            # print "Name: %s" % (name,)

            answer_type = reader.read_integer()
            direction = reader.read_integer()
            ttl = reader.read_integer(4)
            length = reader.read_integer()
            address = []
            if answer_type == 1:
                for s in range(0, length):
                    address.append(str(reader.read_integer(1)))
                address = ".".join(address)
            elif answer_type == 5:
                address = reader.read_full_string()
            else:
                raise Exception("wrong type: %s" % (answer_type, ))

            # print ip
            #print ip
            results.append((answer_type, address))
        return results

    class __ByteStringReader:
        def __init__(self, byte_string):
            self.__byteString = byte_string
            self.__pointer = 0
            self.__resumePoint = 0
            # print "Input: %r" % (byteString, )

        def read_integer(self, length=2):
            val = self.read_string(length)
            val = self.__byte_to_int(val)
            # print val
            return val

        def read_full_string(self):
            value = ""
            while True:
                length = self.read_integer(1)
                if length == 0:
                    break
                elif length == 192:  # \xC0
                    # pointer found
                    new_pointer = self.read_integer(1)
                    old_pointer = self.__pointer
                    self.__pointer = new_pointer
                    value += self.read_full_string()
                    self.__pointer = old_pointer
                    break
                value += self.read_string(length)
                value += "."
                continue
            return value.strip('.')

        def read_string(self, length):
            # print "from: %s to %s" % (self.__pointer, self.__pointer + length)
            val = self.__byteString[self.__pointer:self.__pointer + length]
            #print "Value %r" % (val, )
            self.__pointer += length
            return val

        def __byte_to_int(self, byte_string):
            return int(byte_string.encode('hex'), 16)
