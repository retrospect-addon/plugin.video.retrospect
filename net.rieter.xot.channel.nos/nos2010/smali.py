import time
import datetime
import md5
# import hashlib as md5
# import sys


# http://pallergabor.uw.hu/androidblog/dalvik_opcodes.html
# http://code.google.com/p/smali/wiki/TypesMethodsAndFields
def GetStream(p1, p2, p3):
    b = [53, 36, 1, 64, 115]
    c = [98, 119, 98, 108, 97, 98, 115]
    d = [46, 46, 42, 76, 106]
    e = [105, 64, 104, 62, 73, 9, -89]
    # e = [105, 64, 104, 62, 73, 9, 167]

    v0 = v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = 0

    v0 = len(d)             # : 122
    v4 = [0] * v0           # : 124
    v0 = 0x1                # : 126

    if not p3 == v0:        # : 128
        # :cond_0
        v0 = 2              # : 338
        if not p3 == v0:    # : 340
            # :cond_1
            # p3 == 3
            v0 = "h264_sb"  # : 347
        else:
            # p3 == 2
            v0 = "h264_std" # : 342
    else: # p3 == 1
        v0 = "h264_bb"      # : 130

    # :goto_0
    v3 = 0                  # : 133
    v2 = 11                 # : 135
    v1 = 7                  # : 137

    # :goto_1
    v5 = len(v4)            # : 140
    while v3 < v5:          # : 142
        # cond_2
        v5 = d              # : 352
        v5 = v5[v3]         # : 354
        v5 = v5 ^ v2        # : 356
        v6 = -v1            # : 358
        v5 += v6            # : 360
        # v5 = chr(v5)        # : 362 -> we should probably not do chr() here
        v4[v3] = v5         # : 364
        v3 = v3 + 0x1       # : 366
        v2 = v2 + 0x3       # : 368
        v1 = v1 - 0x2       # : 370

        # goto :goto_1      # : 372
        v5 = len(v4)        # : 140
        pass

    v1 = "%08x"             # : 144
    v2 = 1                  # : 146
    v2 = [None] * v2          # : 148
    v3 = 0                  # : 150
    v5 = p1                 # : 152/154
    v2[v3] = v5             # : 156
    v5 = "%08x" % tuple(v2) # : 158 / 160
    v1 = e                  # : 162
    v1 = len(v1)            # : 164
    v6 = [''] * v1          # : 166

    v1 = 0x0                # : 168
    v3 = 0x32               # : 170
    v2 = -0x3               # : 172

    # :goto_2               # : 174
    v7 = len(v6)            # : 175
    while v1 < v7:          # : 177
        # cond_3
        v7 = e              # : 375
        v7 = v7[v1]         # : 377
        v7 = v7 ^ v3        # : 379
        v8 = -v2            # : 381
        v7 += v8            # : 383
        # v7 = chr(v7)        # : 385 -> we should probably not do chr() here
        v6[v1] = v7         # : 387
        v1 += 0x1           # : 389
        v3 += 0x5           # : 391
        v2 += 0x3           # : 393

        # : goto_2          # : 395
        v7 = len(v6)        # : 175

    v1 = 0x0                # : 179

    # :goto_3               # : 181
    v2 = len(v4)            # : 182
    while v1 < v2:          # : 184
        # :cond_4
        v2 = v4[v1]         # : 398
        v3 = b              # : 400
        v3 = v3[v1]         # : 402
        v2 = v2 ^ v3        # : 404
        # v2 = chr(v2)        # : 406 -> we should probably not do chr() here
        v4[v1] = v2         # : 408
        v1 += 0x1           # : 410

        # : goto_3           # : 412
        v2 = len(v4)        # : 182

    v1 = 0x0                # : 186

    # :goto_4               # : 188
    v2 = len(v6)            # : 189
    while v1 < v2:          # : 191
        # :cond_5
        v2 = v6[v1]         # : 415
        v3 = c              # : 417
        v3 = v3[v1]         # : 419
        v2 = v2 ^ v3        # : 421
        # v2 = chr(v2)        # : 423 -> we should probably not do chr() here
        v6[v1] = v2         # : 425
        v1 += 0x1           # : 427

        # goto_4            # : 429
        v2 = len(v6)        # : 189

    v1 = len(v6)            # : 193
    v1 = v1 - 0x1           # : 195
    v2 = len(v4)            # : 197
    v3 = v2 - 0x1           # : 199
    v2 = v6[v1]             # : 201
    v2 = v2 ^ -0x3          # : 203 -> -0x3 will that work?
    # v2 = chr(v2)            # : 205 -> we should probably not do chr() here
    v6[v1] = v2             # : 207
    v2 = v1 - 0x1           # : 209
    v1 = -0x6               # : 211

    # :goto_5
    while v2 >= 0:          # : 214
        # :cond_6
        v7 = v6[v2]         # : 432
        v8 = v2 + 0x1       # : 434
        v8 = v6[v8]         # : 436
        v8 += v1            # : 438
        v7 = v7 ^ v8        # : 440
        # v7 = chr(v7)        # : 442 -> we should probably not do chr() here
        v6[v2] = v7         # : 444
        v2 -= 0x1          # : 446
        v1 += 0x2           # : 448
        # goto_5            # : 450

    v1 = v4[v3]             # : 216
    v2 = 0x0                # : 218
    v2 = v6[v2]             # : 220
    v2 += 0x8               # : 222
    v1 = v1 ^ v2            # : 224
    # v1 = chr(v1)            # : 226 -> we should probably not do chr() here
    v4[v3] = v1             # : 228
    v2 = v3 - 0x1           # : 230
    v1 = 0x4                # : 232

    # :goto_6
    while v2 >= 0:          # : 234
        # cond_7
        v3 = v4[v2]         # : 453
        v7 = v2 + 0x1       # : 455
        v7 = v4[v7]         # : 457
        v7 += v1            # : 459
        v3 = v3 ^ v7        # : 461
        # v3 = chr(v3)        # : 463 -> we should probably not do chr() here
        v4[v2] = v3         # : 465
        v2 -= 0x1           # : 467
        v1 -= 0x4           # : 469
        # goto_6            # : 471

    v1 = "%5$s%7$s%1$s%2$s%3$s%4$s%6$s"  # : 237
    v2 = 0x7                # : 239
    v2 = [None] * v2        # : 241

    v3 = 0x0                # : 243
    v7 = "video"            # : 245
    v2[v3] = v7             # : 247

    v3 = 0x1                # : 249
    v7 = "icougmobiel"      # : 251
    v2[v3] = v7             # : 253

    v3 = 0x2                # : 255
    v2[v3] = v0             # : 257

    v3 = 0x3                # : 259
    v2[v3] = p2             # : 261

    v3 = 0x4                # : 263
    v7 = ""                 # : 265
    v7 = reduce(lambda x, y: "%s%s" % (x, chr(y)), v4, "")  # : 267
    v2[v3] = v7             # : 269

    v3 = 0x5                # : 271
    v2[v3] = v5             # : 273

    v3 = 0x6                # : 275
    v4 = ""                 # : 277
    v4 = reduce(lambda x, y: "%s%s" % (x, chr(y)), v6, "")  # : 279
    v2[v3] = v4             # : 281

    v1 = "".join((v2[4], v2[6], v2[0], v2[1], v2[2], v2[3], v2[5]))  # : 283/285
    hashTool = md5.md5()
    hashTool.update(v1)
    v1 = hashTool.hexdigest()
    return "%s/%s/%s/%s?type=http" % (v0, v1, v5, p2)


def GetPythonStream(timeStamp, episodeId, quality):
    # init arrays
    b = [53, 36, 1, 64, 115]
    c = [98, 119, 98, 108, 97, 98, 115]
    d = [46, 46, 42, 76, 106]
    e = [105, 64, 104, 62, 73, 9, -89]

    # determine the quality
    if quality == 1:
        videoType = "h264_bb"
    elif quality == 2:
        videoType = "h264_std"
    else:
        videoType = "h264_sb"

    # fill hashOne with initial values base on D
    hashOne = [0] * len(d)
    x = 0x0
    y = 0xb  # 11
    z = 0x7
    while x < len(hashOne):
        # cond_2
        hashOne[x] = (d[x] ^ y) - z
        x = x + 1
        y = y + 3
        z = z - 2

    # generate a hexed timestamp
    hexTime = "%08x" % (timeStamp,)

    # fill hashTwo with initial values based on E
    hashTwo = [0] * len(e)
    x = 0x0
    y = 0x32
    z = -0x3
    while x < len(hashTwo):
        # cond_3
        hashTwo[x] = (e[x] ^ y) - z
        x += 0x1
        y += 0x5
        z += 0x3

    # now we shuffle hashOne using B
    x = 0
    while x < len(hashOne):
        # cond_4
        hashOne[x] = hashOne[x] ^ b[x]
        x += 0x1

    # then shuffle hashTwo using C
    x = 0x0
    while x < len(hashTwo):
        # cond_5
        hashTwo[x] = hashTwo[x] ^ c[x]
        x += 0x1

    # then shuffle hashTwo with itself
    x = len(hashTwo) - 0x1
    hashTwo[x] = hashTwo[x] ^ -0x3
    y = x - 0x1
    z = -0x6
    while y >= 0:
        # cond_6
        hashTwo[y] = hashTwo[y] ^ (hashTwo[y + 0x1] + z)
        y -= 0x1
        z += 0x2

    # then shuffle hashOne with itself
    x = len(hashOne) - 0x1
    hashOne[x] = hashOne[x] ^ (hashTwo[0x0] + 0x8)
    y = x - 0x1
    z = 0x4
    while y >= 0:
        # cond_7
        hashOne[y] = hashOne[y] ^ (hashOne[y + 0x1] + z)
        y -= 0x1
        z -= 0x4

    hashTuple = (reduce(lambda x, y: "%s%s" % (x, chr(y)), hashOne, "")
                 , reduce(lambda x, y: "%s%s" % (x, chr(y)), hashTwo, "")
                 , "video"
                 , "icougmobiel"
                 , videoType
                 , episodeId
                 , hexTime)

    toHash = "".join(hashTuple)

    hashTool = md5.md5()
    hashTool.update(toHash)
    hashValue = hashTool.hexdigest()
    return "http://odi.omroep.nl/video/icougmobiel/%s/%s/%s/%s?type=http" % (videoType, hashValue, hexTime, episodeId)

# sys.exit()
# reload(sys)
# sys.setdefaultencoding("utf-8")
# print sys.getdefaultencoding()

timeStamp = time.mktime(datetime.datetime.now().timetuple())
print int(timeStamp)
# print "http://odi.omroep.nl/video/icougmobiel/h264_std/d9b7ba484e4a121647d53aa6266ca59f"
print "http://odi.omroep.nl/video/icougmobiel/%s" % (GetStream(1360362944, "VPWON_1188106", 2),)
print GetPythonStream(1360362944, "VPWON_1188106", 2)
print "http://odi.omroep.nl/video/icougmobiel/h264_std/77661f2c019abd1c49358ec532ceeba8/51157dc0/VPWON_1188106?type=http"

print GetPythonStream(timeStamp, "NPS_1220263", 2)

"""
public static final String a = v.class.getSimpleName();
  private static final char[] b = { 53, 36, 1, 64, 115 };
  private static final char[] c = { 98, 119, 98, 108, 97, 98, 115 };
  private static final char[] d = { 46, 46, 42, 76, 106 };
  private static final char[] e = { 105, 64, 104, 62, 73, 9, -89 };

  public static String a(long paramLong, String paramString, int paramInt)
  {
    char[] arrayOfChar1 = new char[d.length];
    String str1;
    int i;
    int j;
    int k;
    label28: String str2;
    char[] arrayOfChar2;
    int m;
    int n;
    int i1;
    label78: int i2;
    label89: int i3;
    label100: int i6;
    int i7;
    label146: int i8;
    if (paramInt == 1)
    {
      str1 = "h264_bb";
      i = 0;
      j = 11;
      k = 7;
      if (i < arrayOfChar1.length)
        break label320;
      Object[] arrayOfObject1 = new Object[1];
      arrayOfObject1[0] = Long.valueOf(paramLong);
      str2 = String.format("%08x", arrayOfObject1);
      arrayOfChar2 = new char[e.length];
      m = 0;
      n = 50;
      i1 = -3;
      if (m < arrayOfChar2.length)
        break label351;
      i2 = 0;
      if (i2 < arrayOfChar1.length)
        break label382;
      i3 = 0;
      if (i3 < arrayOfChar2.length)
        break label406;
      int i4 = -1 + arrayOfChar2.length;
      int i5 = -1 + arrayOfChar1.length;
      arrayOfChar2[i4] = ((char)(0xFFFFFFFD ^ arrayOfChar2[i4]));
      i6 = i4 - 1;
      i7 = -6;
      if (i6 >= 0)
        break label430;
      arrayOfChar1[i5] = ((char)(arrayOfChar1[i5] ^ '\b' + arrayOfChar2[0]));
      i8 = i5 - 1;
    }
    for (int i9 = 4; ; i9 -= 4)
    {
      if (i8 < 0)
      {
        Object[] arrayOfObject2 = new Object[7];
        arrayOfObject2[0] = "video";
        arrayOfObject2[1] = "icougmobiel";
        arrayOfObject2[2] = str1;
        arrayOfObject2[3] = paramString;
        arrayOfObject2[4] = new String(arrayOfChar1);
        arrayOfObject2[5] = str2;
        arrayOfObject2[6] = new String(arrayOfChar2);
        return String.format("http://%s/%s/%s/%s/%s/%s/%s?type=http", new Object[] { "odi.omroep.nl", "video", "icougmobiel", str1, aa.b(String.format("%5$s%7$s%1$s%2$s%3$s%4$s%6$s", arrayOfObject2)), str2, paramString });
        if (paramInt == 2)
        {
          str1 = "h264_std";
          break;
        }
        str1 = "h264_sb";
        break;
        label320: arrayOfChar1[i] = ((char)((j ^ d[i]) + -k));
        i++;
        j += 3;
        k -= 2;
        break label28;
        label351: arrayOfChar2[m] = ((char)((n ^ e[m]) + -i1));
        m++;
        n += 5;
        i1 += 3;
        break label78;
        label382: arrayOfChar1[i2] = ((char)(arrayOfChar1[i2] ^ b[i2]));
        i2++;
        break label89;
        label406: arrayOfChar2[i3] = ((char)(arrayOfChar2[i3] ^ c[i3]));
        i3++;
        break label100;
        label430: arrayOfChar2[i6] = ((char)(arrayOfChar2[i6] ^ i7 + arrayOfChar2[(i6 + 1)]));
        i6--;
        i7 += 2;
        break label146;
      }
      arrayOfChar1[i8] = ((char)(arrayOfChar1[i8] ^ i9 + arrayOfChar1[(i8 + 1)]));
      i8--;
    }
  }
  """
