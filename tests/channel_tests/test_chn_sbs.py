# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import binascii
import os
import pyaes
import json
import random

from tests.channel_tests.channeltest import ChannelTest
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


class TestSbsSeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestSbsSeChannel, self).__init__(methodName, "channel.se.sbs", "dplayse")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_decryption_with_parameters(self):
        # Input
        ct = "iPYoP0sU67vM5q7Esk8gwzkqC+FmRN89GFb3IuAbx3dIxWrOmpKLqls9EK30VDJZsW1zX71QkPFn/76eMCUVLLANcgaqO00ZNV2AkPcKk9uBIILK52no7WWad4QAwcsyuO0fn/OGuEVuLikvlIL1SGrqdkNt9L43a+vFrawKQn+P+qHhR8VHhXR+I6sFZqQWYo5Ex082X6qbRl5jJfq7Xh4OmFCy4gHIfo66IPR+mm3iDmRzlV8BY+5bdGOXRMp/L3mxulZzglLV8d6dSPYfzo7l2B5DOCCNAStuaWM5+AuCiB3cDpJtwH0DivtpEcmSCKZTPvEkXtpl3hdtPsfQSYP3K+4kqxMfV25PiT2HQC+Bxvt6jHzcBUhfq9ytYVD9erdCWOmqrBXa7jmpw4RKtjWk291gf/djhk4oRq+TKnA9gKaor5L1WKt4MUTkNh1Wok8vwab9s5Y1ZxEa0jFyzjQmqto7xqCkSGlcS45KAHrK/L3U0RN5QJy/K1KofWXVfbZKV20fEZl9n5Z+b4nmsPNcrtiZxqeSuXU3Vy2QkDt/RUDo3jpwEVQJvabyO0pkQS6099IVlNEC/GENgjSig0fzoTtaTcyCx3XdYRNW1+zngpxfLrT8C4NF4EZtiFPLYrV381KMytVun4CQZNJ4AyN+rbfp+osevrATtxh/wOn2OFd4whB7uBG+GdZvpJKeUk3Nx7KiDCvClEHE5zTZt5Qo5ZnDGSzYgUn+L/P+BB8IoIs1DNXAeAMvlrA5llJLOjDBo6V/IGvZGh69hjs2giXGD++DO2jvOwqw2vIlb3RAh3+qJVRNwmOtjDfxbH3HTjTsZDKAU/Yalt9EW4OK0+WPA/AYrGg3sZMEiGuuojGHEoM2XbE6fFPRvvJE5AMAG9+ncD8GtlQsPlLX7XjaW/zpE7MvLf0UGw20DUcxsJVYCBT/932gEBo2D3lmYGP2t4TQ/O743LuioYGkpAxFoyIjqRmd7sUy0tM28T8SzfWoTmFlOJC4bpHkZ19xFqGfCnWIgYxgywfv5xV+lFHjWJRn3F/JocWwCo9SZ2d5w+or1C4m6vjapGMqaJXJUKF8RlrdJbwfXvk7NEgkdS7c8ncmV5Kwxm2Wlc/Hgud+0mX79bcLFuqa8oF9xSk6SE5quzbu7BN4YVxD8sbC/LcM7gV4sWNct2SVVNeILJAwn1IlgHUe+Wx84t3wGrGTAc5ew2gF/xAuzgNYDV4SQEgfZjSEexvmcBc0VFiN9IxhVIZ9S7WgTHdWF6eES7gy3lgKsImzYrROWqcd3Pquo8oce3VrHdKG/2Dy450/YEvhZYBOFe2CxCj2UIAJk538ZmQtoXo33NrtVmJRvKYnnOs9vKQkYmQNo3yk3SXRQupN/wgH3HTVNqVaPKCJfTy1zqgz/rtO1bVXdp4GwfAvrnnAzPTF9dphxPt85K9/Ukc4/Y+mGIesmds8Be+9vbXCHCBRPs1mlVK8X/t5nJD+ED/eXkTxEJ04M/tFBTQnUeZT7U7Bfx4Lx3R5iYRiALh1xWovvEiYw7ts//idNUgHqB6YHKPY/2L4yx3xk6UvOpWW4d3VdDuoe+U6kaECreeymfuorsPoAdKvHpTE27TEF24APibGJJ6jfGcRIO97h4VPrTC/YugKgXYWEd5Hk7GDQyacg8spayIUtkzt8P/wEKVwbGA9xnUOepl21U4MMlc/saCbFQA/tDdGvlESzc0BMBSJQefbkzQSIZj30jjwpr/meFsPwLLyqp8FRepw48Gz70IXtw7Oltxt3OtI8IQfO2X259qppzeoNa5mYdvMW+67kg=="
        encrypted_bytes = binascii.a2b_base64(ct)
        iv_hex = "e55f5ec7b09f9a41d4bbb9cdedd107f0"
        salt_hex = "693397a9c958b990"
        salt_bytes = binascii.unhexlify(salt_hex)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"

        # Expected result
        unencrypted = '[{"key":"api_type","value":"js"},{"key":"p","value":1},{"key":"f","value":"91bc57b20229990a496a7ac3d14d4fcb"},{"key":"n","value":"MTU4OTA2MTk1MQ=="},{"key":"wh","value":"dd865a948064df918ad0bf458955392d|5d76839801bc5904a4f12f1731a7b6d1"},{"key":"fe","value":["DNT:1","L:en-NL","D:24","PR:1","S:1920,1080","AS:1920,1040","TO:-120","SS:true","LS:true","IDB:true","B:false","ODB:true","CPUC:unknown","PK:Win32","CFP:-1424337346","FR:false","FOS:false","FB:false","JSF:Arial,Arial Black,Arial Narrow,Book Antiqua,Bookman Old Style,Calibri,Cambria,Cambria Math,Century,Century Gothic,Century Schoolbook,Comic Sans MS,Consolas,Courier,Courier New,Garamond,Georgia,Helvetica,Impact,Lucida Bright,Lucida Calligraphy,Lucida Console,Lucida Fax,Lucida Handwriting,Lucida Sans,Lucida Sans Typewriter,Lucida Sans Unicode,Microsoft Sans Serif,Monotype Corsiva,MS Gothic,MS PGothic,MS Reference Sans Serif,MS Sans Serif,MS Serif,Palatino Linotype,Segoe Print,Segoe Script,Segoe UI,Segoe UI Light,Segoe UI Semibold,Segoe UI Symbol,Tahoma,Times,Times New Roman,Trebuchet MS,Verdana,Wingdings,Wingdings 2,Wingdings 3","P:Chrome PDF Plugin,Chrome PDF Viewer,Native Client","T:1,false,false","H:12","SWF:false"]},{"key":"ife_hash","value":"05351185b52593d76ae5d04d963fe5a5"},{"key":"cs","value":1},{"key":"jsbd","value":"{\\"HL\\":10,\\"NCE\\":true,\\"DMTO\\":1,\\"DOTO\\":1}"}]'
        key_hex = "621f73987518e3b1ff250fe19cb4778f33ef2425936e25d6da0ad3f5891a74a1"
        timestamp_expected = 1589047200

        # Do the work
        timestamp = 1589061893
        timestamp = timestamp - (timestamp % (60*60*6))
        self.assertEqual(timestamp_expected, timestamp)

        key_str = "{}{}".format(user_agent, timestamp)
        key_iv = self.__evp_kdf(
            key_str.encode(), salt_bytes, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5")

        result_key = binascii.hexlify(key_iv["key"]).decode()
        result_iv = binascii.hexlify(key_iv["iv"]).decode()
        self.assertEqual(key_hex, result_key)
        self.assertEqual(iv_hex, result_iv)

        # We can use PyAES in Feed mode
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key_iv["key"], key_iv["iv"]))
        back = decrypter.feed(encrypted_bytes)
        # Again, make a final call to flush any remaining bytes and strip padding
        back += decrypter.feed()

        self.assertEqual(unencrypted, back.decode())

    def test_decryption_with_iv_and_key(self):
        ct = "x1O45dImsNmb1fu51XWe1AAYZxerA5//iSdqY7++6cUy/6PzvGMGxrlm7/soyJw9VcZNbwfpayq+TR+rCT7uDmRqmqw86mEdEo32xX90H+h6w1xRkUQjQX9tTWbhTqiDresxmXRX6zbZ+PhJWZjghXX5QTcYR9LNhjPt3urrpZykR8+LJRx7IC6NXpaNavAjExedZoFmCgsxkSxcgeAToYRzF4HoCQK3QvU8uuZyfV3SbsZutHkrACaeXLtLm3XAAvjeKTxBwHZP8x2F1+OeGb23ZX7pdQskpMT85bZwMUqEhwk/w/zDr5ANQWu7R4cV3msrLBzAw+5jgn88ukVH/1njW5PMamYgmgSzWYjDKpHbGOfe13G0lO3+q4B2Sih9/CJxNCLmV7QMfD/Rx7RTsrbP1knUSnrUVh7q0N77To9wvwaAiSEq6BecWhvU9x5N/ymoPXLxsdhI9PvUgtEvNp2wPyJHgaxS2yszX79FQITJyoT++E1q8pmDslNwjv5YTOZ8uW33b/N2CZ0cS5qFu3zgLQJDJPNbQ6UCks0VLeWDLocUUQHlqe/ywkHIvY3k3E2jubcUFaIA0MgqWavk0ukHyxSTVjvgtjbL+86ktjCMBLs17Uq9EEiP/kPtXYb3EecYfEAH8A9JIXRZuHF0OoeEyfm90dOeHO4rhYClIfUcTmipxrO5JiO8g+/xWxztXd9DLlK3GFKTBO69gzs0u2166X9iN2XOnZMbZjJPDIcpgY99rtVN9i64iK/hcScd/XaEnkg3Z1vdylylDm58A/YhexOGC18txApzEWoSDNa7bGeMQXc1yd9mftBjNqIst4Bxrft90p66G86g5uOcSxMcQYAxTUu4qKMjAtqtU3Yc+YAJ0R5WfI5tcIdDV4GuAupdS1Yfmx6IwpPIfVVxwp1Q3dQKEBPEe0RbFU0jtD8CY7khjRdkmRb2wdNnyrNtM9dFw43miYfOdEDXJ5AvwK+EEMjMD/xFkoiijgZVBbmLgpFQ9C8M86frdBoCetXIR7qJFTxgM6Wz7Tolo1YIJ1Vu/vWxjiJQMSz7nMjj53DZv8cO0vj1fUlQjKvK/bUr4eX7ndijV5GKvuYzYhnPSpwuggTDYNBwlR5KT/k/NiWfzqW9i74gldTKeQxydRzKqV4Q+UUqovkEEbCxvwHSTa5q0Zd++dngXCajbqBpFtYWAgXwRSaP/Rfp+l5jkl6XioqdoTJDTaiPWDfUtJN/PDRR4SV7XeH4l1mE53aikIGFIZ354stt/2zpXL+kaX/qFILczeLjZG1+Fc4jzopnl6r+cOlMffvrv4MbAC97/DQ//nC4Ax33oH4HfSI6RVqHW+6R4R6XzAVkv4zB9aMo2DlmUvYA3rNNfdR37Zahj9aMicew+kiUuGmJwW0ywma+498FIfndJwDmegVIuG8X0TH6Rba9eHtONqSCJUv58ZrTtr7CcB3o7CRRfLjMzsv1Se9pggK1gsAVrgI8sXNKLLaiHTaXmmLeqFdtIKQgeMan1SPpWQZuGf4nSc511WnGinZqvFlsSWpGyvbpi12AbpHCf6O6mAdNhXzGZyTXMryf0PFGPSnGFl9qlW3zolMYQqEGBVVaCjbtTcf/uRwgS91C74iWyvLZJUQspMqkvnuDhw/nhJ1zdcszbGzX4vkRxCJfRbvHYIc4Uaho1lmP/QOBskigpyZgqXBNxscYDnQwXistaq0VRaPXR/ZsIiAelzXvnqlJzZD66Di6tHX5jcK9NO0po0lEowXfp5TPER5Nh4L5kO+Prb1aHrEpo91bmly4V/CnSxqrJSEKZr5FcQ=="
        unencrypted = '[{"key":"api_type","value":"js"},{"key":"p","value":1},{"key":"f","value":"91bc57b20229990a496a7ac3d14d4fcb"},{"key":"n","value":"MTU4ODcxMjc2NQ=="},{"key":"wh","value":"dd865a948064df918ad0bf458955392d|5d76839801bc5904a4f12f1731a7b6d1"},{"key":"fe","value":["DNT:1","L:en-NL","D:24","PR:1","S:1920,1080","AS:1920,1040","TO:-120","SS:true","LS:true","IDB:true","B:false","ODB:true","CPUC:unknown","PK:Win32","CFP:-1424337346","FR:false","FOS:false","FB:false","JSF:Arial,Arial Black,Arial Narrow,Book Antiqua,Bookman Old Style,Calibri,Cambria,Cambria Math,Century,Century Gothic,Century Schoolbook,Comic Sans MS,Consolas,Courier,Courier New,Garamond,Georgia,Helvetica,Impact,Lucida Bright,Lucida Calligraphy,Lucida Console,Lucida Fax,Lucida Handwriting,Lucida Sans,Lucida Sans Typewriter,Lucida Sans Unicode,Microsoft Sans Serif,Monotype Corsiva,MS Gothic,MS PGothic,MS Reference Sans Serif,MS Sans Serif,MS Serif,Palatino Linotype,Segoe Print,Segoe Script,Segoe UI,Segoe UI Light,Segoe UI Semibold,Segoe UI Symbol,Tahoma,Times,Times New Roman,Trebuchet MS,Verdana,Wingdings,Wingdings 2,Wingdings 3","P:Chrome PDF Plugin,Chrome PDF Viewer,Native Client","T:1,false,false","H:12","SWF:false"]},{"key":"ife_hash","value":"05351185b52593d76ae5d04d963fe5a5"},{"key":"cs","value":1},{"key":"jsbd","value":"{\\"HL\\":31,\\"NCE\\":true,\\"DMTO\\":1,\\"DOTO\\":1}"}]'
        encrypted_bytes = binascii.a2b_base64(ct)

        iv = "a8e6b1bea40a4275c288d1aa06220df3"
        iv = binascii.unhexlify(iv)

        key = "2e27e3c8a19b810cc62ca3728e70c0fa4cbe12db3d4ee84d87f98fb0138ba74a"
        key = binascii.unhexlify(key)

        # We can use PyAES in Feed mode
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        back = decrypter.feed(encrypted_bytes)
        # Again, make a final call to flush any remaining bytes and strip padding
        back += decrypter.feed()

        self.assertEqual(unencrypted, back.decode())

    def test_encryption_with_iv_and_key(self):
        ct = "x1O45dImsNmb1fu51XWe1AAYZxerA5//iSdqY7++6cUy/6PzvGMGxrlm7/soyJw9VcZNbwfpayq+TR+rCT7uDmRqmqw86mEdEo32xX90H+h6w1xRkUQjQX9tTWbhTqiDresxmXRX6zbZ+PhJWZjghXX5QTcYR9LNhjPt3urrpZykR8+LJRx7IC6NXpaNavAjExedZoFmCgsxkSxcgeAToYRzF4HoCQK3QvU8uuZyfV3SbsZutHkrACaeXLtLm3XAAvjeKTxBwHZP8x2F1+OeGb23ZX7pdQskpMT85bZwMUqEhwk/w/zDr5ANQWu7R4cV3msrLBzAw+5jgn88ukVH/1njW5PMamYgmgSzWYjDKpHbGOfe13G0lO3+q4B2Sih9/CJxNCLmV7QMfD/Rx7RTsrbP1knUSnrUVh7q0N77To9wvwaAiSEq6BecWhvU9x5N/ymoPXLxsdhI9PvUgtEvNp2wPyJHgaxS2yszX79FQITJyoT++E1q8pmDslNwjv5YTOZ8uW33b/N2CZ0cS5qFu3zgLQJDJPNbQ6UCks0VLeWDLocUUQHlqe/ywkHIvY3k3E2jubcUFaIA0MgqWavk0ukHyxSTVjvgtjbL+86ktjCMBLs17Uq9EEiP/kPtXYb3EecYfEAH8A9JIXRZuHF0OoeEyfm90dOeHO4rhYClIfUcTmipxrO5JiO8g+/xWxztXd9DLlK3GFKTBO69gzs0u2166X9iN2XOnZMbZjJPDIcpgY99rtVN9i64iK/hcScd/XaEnkg3Z1vdylylDm58A/YhexOGC18txApzEWoSDNa7bGeMQXc1yd9mftBjNqIst4Bxrft90p66G86g5uOcSxMcQYAxTUu4qKMjAtqtU3Yc+YAJ0R5WfI5tcIdDV4GuAupdS1Yfmx6IwpPIfVVxwp1Q3dQKEBPEe0RbFU0jtD8CY7khjRdkmRb2wdNnyrNtM9dFw43miYfOdEDXJ5AvwK+EEMjMD/xFkoiijgZVBbmLgpFQ9C8M86frdBoCetXIR7qJFTxgM6Wz7Tolo1YIJ1Vu/vWxjiJQMSz7nMjj53DZv8cO0vj1fUlQjKvK/bUr4eX7ndijV5GKvuYzYhnPSpwuggTDYNBwlR5KT/k/NiWfzqW9i74gldTKeQxydRzKqV4Q+UUqovkEEbCxvwHSTa5q0Zd++dngXCajbqBpFtYWAgXwRSaP/Rfp+l5jkl6XioqdoTJDTaiPWDfUtJN/PDRR4SV7XeH4l1mE53aikIGFIZ354stt/2zpXL+kaX/qFILczeLjZG1+Fc4jzopnl6r+cOlMffvrv4MbAC97/DQ//nC4Ax33oH4HfSI6RVqHW+6R4R6XzAVkv4zB9aMo2DlmUvYA3rNNfdR37Zahj9aMicew+kiUuGmJwW0ywma+498FIfndJwDmegVIuG8X0TH6Rba9eHtONqSCJUv58ZrTtr7CcB3o7CRRfLjMzsv1Se9pggK1gsAVrgI8sXNKLLaiHTaXmmLeqFdtIKQgeMan1SPpWQZuGf4nSc511WnGinZqvFlsSWpGyvbpi12AbpHCf6O6mAdNhXzGZyTXMryf0PFGPSnGFl9qlW3zolMYQqEGBVVaCjbtTcf/uRwgS91C74iWyvLZJUQspMqkvnuDhw/nhJ1zdcszbGzX4vkRxCJfRbvHYIc4Uaho1lmP/QOBskigpyZgqXBNxscYDnQwXistaq0VRaPXR/ZsIiAelzXvnqlJzZD66Di6tHX5jcK9NO0po0lEowXfp5TPER5Nh4L5kO+Prb1aHrEpo91bmly4V/CnSxqrJSEKZr5FcQ=="
        ct_bytes = binascii.a2b_base64(ct)
        ct = binascii.b2a_base64(ct_bytes)
        unencrypted = b'[{"key":"api_type","value":"js"},{"key":"p","value":1},{"key":"f","value":"91bc57b20229990a496a7ac3d14d4fcb"},{"key":"n","value":"MTU4ODcxMjc2NQ=="},{"key":"wh","value":"dd865a948064df918ad0bf458955392d|5d76839801bc5904a4f12f1731a7b6d1"},{"key":"fe","value":["DNT:1","L:en-NL","D:24","PR:1","S:1920,1080","AS:1920,1040","TO:-120","SS:true","LS:true","IDB:true","B:false","ODB:true","CPUC:unknown","PK:Win32","CFP:-1424337346","FR:false","FOS:false","FB:false","JSF:Arial,Arial Black,Arial Narrow,Book Antiqua,Bookman Old Style,Calibri,Cambria,Cambria Math,Century,Century Gothic,Century Schoolbook,Comic Sans MS,Consolas,Courier,Courier New,Garamond,Georgia,Helvetica,Impact,Lucida Bright,Lucida Calligraphy,Lucida Console,Lucida Fax,Lucida Handwriting,Lucida Sans,Lucida Sans Typewriter,Lucida Sans Unicode,Microsoft Sans Serif,Monotype Corsiva,MS Gothic,MS PGothic,MS Reference Sans Serif,MS Sans Serif,MS Serif,Palatino Linotype,Segoe Print,Segoe Script,Segoe UI,Segoe UI Light,Segoe UI Semibold,Segoe UI Symbol,Tahoma,Times,Times New Roman,Trebuchet MS,Verdana,Wingdings,Wingdings 2,Wingdings 3","P:Chrome PDF Plugin,Chrome PDF Viewer,Native Client","T:1,false,false","H:12","SWF:false"]},{"key":"ife_hash","value":"05351185b52593d76ae5d04d963fe5a5"},{"key":"cs","value":1},{"key":"jsbd","value":"{\\"HL\\":31,\\"NCE\\":true,\\"DMTO\\":1,\\"DOTO\\":1}"}]'

        iv = "a8e6b1bea40a4275c288d1aa06220df3"
        iv = binascii.unhexlify(iv)

        key = "2e27e3c8a19b810cc62ca3728e70c0fa4cbe12db3d4ee84d87f98fb0138ba74a"
        key = binascii.unhexlify(key)

        # We can use PyAES in Feed mode
        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        encrypted = encrypter.feed(unencrypted)
        # Again, make a final call to flush any remaining bytes and strip padding
        encrypted += encrypter.feed()
        encrypted_b64 = binascii.b2a_base64(encrypted)
        self.assertEqual(ct, encrypted_b64)

    def test_key_data(self):
        password = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.361588701600"
        salt = "d48fc95c3be6f837"
        salt_bytes = binascii.unhexlify(salt)
        iv = "330891851a4617eb5644a577d0860c11"
        key = "19520dc1c574c58f2b142da0260c7c538c2ffd6ef174c6b913537ffb63319edc"

        key_iv = self.__evp_kdf(
            password.encode(), salt_bytes, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5")
        result_key = binascii.hexlify(key_iv["key"]).decode()
        result_iv = binascii.hexlify(key_iv["iv"]).decode()

        self.assertEqual(len(iv), len(result_iv))
        self.assertEqual(iv, result_iv)
        self.assertEqual(len(key), len(result_key))
        self.assertEqual(key, result_key)

    def test_murmurhash_special(self):
        expected = "05351185b52593d76ae5d04d963fe5a5"
        murmur = "0xd79325b585113505a5e53f964dd0e56aL"

        result = self.__transform_murmur(murmur)
        self.assertEqual(expected, result)

    def test_login(self):
        import time

        user_agent = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
        device_id = "91bc57b20229990a496a7ac3d14d4fcb"
        window_id = "{}|{}".format(
            binascii.hexlify(os.urandom(16)).decode(), binascii.hexlify(os.urandom(16)).decode())

        now = int(time.time())
        b64_now = binascii.b2a_base64(str(now).encode()).decode().strip()

        # region Browser properties seem optional
        # fe = [
        #     "DNT:1",
        #     "L:en-NL",
        #     "D:24",
        #     "PR:1",
        #     "S:1920,1080",
        #     "AS:1920,1040",
        #     "TO:-120",
        #     "SS:true",
        #     "LS:true",
        #     "IDB:true",
        #     "B:false",
        #     "ODB:true",
        #     "CPUC:unknown",
        #     "PK:Win32",
        #     "CFP:-1424337346",
        #     "FR:false",
        #     "FOS:false",
        #     "FB:false",
        #     "JSF:Arial,Arial Black,Arial Narrow,Book Antiqua,Bookman Old Style,Calibri,Cambria,Cambria Math,Century,Century Gothic,Century Schoolbook,Comic Sans MS,Consolas,Courier,Courier New,Garamond,Georgia,Helvetica,Impact,Lucida Bright,Lucida Calligraphy,Lucida Console,Lucida Fax,Lucida Handwriting,Lucida Sans,Lucida Sans Typewriter,Lucida Sans Unicode,Microsoft Sans Serif,Monotype Corsiva,MS Gothic,MS PGothic,MS Reference Sans Serif,MS Sans Serif,MS Serif,Palatino Linotype,Segoe Print,Segoe Script,Segoe UI,Segoe UI Light,Segoe UI Semibold,Segoe UI Symbol,Tahoma,Times,Times New Roman,Trebuchet MS,Verdana,Wingdings,Wingdings 2,Wingdings 3",
        #     "P:Chrome PDF Plugin,Chrome PDF Viewer,Native Client",
        #     "T:1,false,false",
        #     "H:12",
        #     "SWF:false"
        # ]
        # fs_murmur_value = ", ".join(fe)
        # # Murmur (x64 128-bit) from fs_murmur_value via https://asecuritysite.com/encryption/mur
        # fs_murmur = "0xfa204e6c7927d156f9b50d837b6cb295L"
        # fs_murmur_hash = self.__transform_murmur(fs_murmur)
        #endregion

        data = [
            {"key": "api_type", "value": "js"},
            {"key": "p", "value": 1},                       # constant
            {"key": "f", "value": device_id},               # browser instance ID
            {"key": "n", "value": b64_now},                 # base64 encoding of time.now()
            {"key": "wh", "value": window_id},              # WindowHandle ID
            # {"key": "fe", "value": fe},                     # browser properties
            # {"key": "ife_hash", "value": fs_murmur_hash},   # hash of browser properties
            {"key": "cs", "value": 1},                      # canvas supported 0/1
            {"key": "jsbd", "value": "{\"HL\":41,\"NCE\":true,\"DMTO\":1,\"DOTO\":1}"}
        ]
        data_value = json.dumps(data)

        stamp = now - (now % (60*60*6))
        password = "{}{}".format(user_agent, stamp)

        salt_bytes = os.urandom(8)
        key_iv = self.__evp_kdf(password.encode(), salt_bytes, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5")
        key = key_iv["key"]
        iv = key_iv["iv"]

        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        encrypted = encrypter.feed(data_value)
        # Again, make a final call to flush any remaining bytes and strip padding
        encrypted += encrypter.feed()

        salt_hex = binascii.hexlify(salt_bytes)
        iv_hex = binascii.hexlify(iv)
        encrypted_b64 = binascii.b2a_base64(encrypted)
        bda = {
            "ct": encrypted_b64.decode(),
            "iv": iv_hex.decode(),
            "s": salt_hex.decode()
        }
        bda_str = json.dumps(bda)
        bda_base64 = binascii.b2a_base64(bda_str.encode())

        req_dict = {
            "bda": bda_base64.decode(),
            "public_key": "FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            "site": "https://client-api.arkoselabs.com",
            "userbrowser": user_agent,
            "simulate_rate_limit": "0   ",
            "simulated": "0",
            "rnd": "{}".format(random.random())
        }

        req_data = ""
        for k, v in req_dict.items():
            print(k, v)
            req_data = "{}{}={}&".format(req_data, k, HtmlEntityHelper.url_encode(v))
        req_data = req_data.rstrip("&")

        import requests
        s = requests.sessions.session()
        arkrose_json = s.post(
            url="https://client-api.arkoselabs.com/fc/gt2/public_key/FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            data=req_data,
            headers={"user-agent": user_agent}
        ).json()
        print(arkrose_json)
        arkose_token = arkrose_json["token"]
        self.assertTrue("rid=" in arkose_token, "Invalid Arkose Token")

        data = s.get("https://disco-api.dplay.se/token?realm=dplayse&deviceId={}&shortlived=true".format(device_id))
        api_json = data.json()
        api_token = api_json["data"]["attributes"]["token"]
        print(api_token)

        dplay_username = os. environ['DPLAY_USERNAME']
        dplay_password = os. environ['DPLAY_PASSWORD']
        creds = {"credentials": {"username": dplay_username, "password": dplay_password}}
        res = s.post(
            url="https://disco-api.dplay.se/login",
            json=creds,
            headers={
                "x-disco-arkose-token": arkose_token,
                "Origin": "https://auth.dplay.se",
                "x-disco-client": "WEB:10:AUTH_DPLAY_V1:2.4.1",  # is not specified a captcha is required
                # "Sec-Fetch-Site": "same-site",
                # "Sec-Fetch-Mode": "cors",
                # "Sec-Fetch-Dest": "empty",
                "Referer": "https://auth.dplay.se/login",
                "User-Agent": user_agent
            }
        )
        print(res.json())
        self.assertLessEqual(res.status_code, 399)

        me = s.get("https://disco-api.dplay.se/users/me")
        print(me.json())
        self.assertLessEqual(me.status_code, 399)

    def __transform_murmur(self, murmur):
        murmur = murmur.rstrip("L")
        if murmur.startswith("0x"):
            murmur = murmur[2:]
        n = 2
        pairs = [murmur[i:i+n] for i in range(0, len(murmur), n)]

        return pairs[7] + pairs[6] + pairs[5] + pairs[4] + pairs[3] + pairs[2] + pairs[1] + pairs[0] + \
            pairs[15] + pairs[14] + pairs[13] + pairs[12] + pairs[11] + pairs[10] + pairs[9] + pairs[8]

    def __evp_kdf(self, passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
        """
        https://gist.github.com/adrianlzt/d5c9657e205b57f687f528a5ac59fe0e

        https://github.com/Shani-08/ShaniXBMCWork2/blob/master/plugin.video.serialzone/jscrypto.py

        :param byte passwd:
        :param byte salt:
        :param int key_size:
        :param int iv_size:
        :param int iterations:
        :param str hash_algorithm:

        :return:

        """

        import hashlib

        target_key_size = key_size + iv_size
        derived_bytes = b""
        number_of_derived_words = 0
        block = None
        hasher = hashlib.new(hash_algorithm)

        while number_of_derived_words < target_key_size:
            if block is not None:
                hasher.update(block)

            hasher.update(passwd)
            hasher.update(salt)
            block = hasher.digest()

            hasher = hashlib.new(hash_algorithm)

            for _ in range(1, iterations):
                hasher.update(block)
                block = hasher.digest()
                hasher = hashlib.new(hash_algorithm)

            derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

            number_of_derived_words += len(block)/4

        return {
            "key": derived_bytes[0: key_size * 4],
            "iv": derived_bytes[key_size * 4:]
        }
