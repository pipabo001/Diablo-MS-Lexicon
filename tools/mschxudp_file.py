from io import SEEK_SET
from io import SEEK_CUR
from file_helper import ReadHelper, WriteHelper

# win10 1703
#           proto8                   unknown_X   version
# 00000000  6d 73 63 68 78 75 64 70  02 00 60 00 01 00 00 00  |mschxudp..`.....|
#           phrase_offset_start
#                       phrase_start phrase_end  phrase_count
# 00000010  40 00 00 00 48 00 00 00  98 00 00 00 02 00 00 00  |@...H...........|
#           timestamp
# 00000020  49 4e 06 59 00 00 00 00  00 00 00 00 00 00 00 00  |IN.Y............|
# 00000030  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
#                                                      candidate2
#           phrase_offsets[]         magic_X     phrase_offset2
# 00000040  00 00 00 00 24 00 00 00  10 00 10 00 18 00 06 06  |....$...........|
#           phrase_unknown8_X        pinyin
# 00000050  00 00 00 00 96 0a 99 20  61 00 61 00 61 00 00 00  |....... a.a.a...|
#           phrase                               magic_X
# 00000060  61 00 61 00 61 00 61 00  61 00 00 00 10 00 10 00  |a.a.a.a.a.......|
#                       phrase_unknown8_X
#                 candidate2
#           offset2                        pinyin
# 00000070  1a 00 07 06 00 00 00 00  a6 0a 99 20 62 00 62 00  |........... b.b.|
#                             phrase
# 00000080  62 00 62 00 00 00 62 00  62 00 62 00 62 00 62 00  |b.b...b.b.b.b.b.|
# 00000090  62 00 62 00 62 00 00 00                           |b.b.b...|
# 00000098


# win10 1607
#           proto8                   version     phrase_offset_start
# 00000000  6d 73 63 68 78 75 64 70  01 00 00 00 40 00 00 00  |mschxudp....@...|
#          phrase_start phrase_end   phrase_count unknown_X
# 00000010  48 00 00 00 7e 00 00 00  02 00 00 00 00 00 00 00  |H...~...........|
#           timestamp
# 00000020  29 b8 cc 58 00 00 00 00  00 00 00 00 00 00 00 00  |)..X............|
# 00000030  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
#                                                      candidate2
#           phrase_offsets[]         magic       offset2
# 00000040  00 00 00 00 1c 00 00 00  08 00 08 00 10 00 01 06  |................|
#           pinyin                   phrase
# 00000050  61 00 61 00 61 00 00 00  61 00 61 00 61 00 61 00  |a.a.a...a.a.a.a.|
#                                                pinyin
#                                          candidate2
#                       magic        offset2
# 00000060  61 00 00 00 08 00 08 00  10 00 05 06 62 00 62 00  |a...........b.b.|
#                       phrase
# 00000070  62 00 00 00 62 00 62 00  62 00 62 00 00 00        |b...b.b.b.b...|
# 0000007e


class MschxudpFile(object):
    '''
    classdocs
    '''


    def __init__(self, file_name):
        '''
        Constructor
        '''
        self.open(file_name);

    def open(self, file_name):
        self.file_name = file_name;
        with open(self.file_name, "rb") as file:
            fi = ReadHelper(file);
            self.proto = str(file.read(8));

            (self.unknown, self.version,
             self.phrase_offset_start, self.phrase_start, self.phrase_end,
             self.phrase_count, self.timestamp) = fi.read_struct('IIIIIII');

            if (self.phrase_offset_start == 0x00000040
                ) and (self.phrase_offset_start + 4 * self.phrase_count == self.phrase_start):
                self.win10 = "1703";
                self.phrase_magic = 0x00100010;
            elif (self.version == 0x40) and (self.version + 4 * self.phrase_end == self.phrase_offset_start):
                self.win10 = "1607";
                self.phrase_magic = 0x00080008;
                (self.version,
                 self.phrase_offset_start, self.phrase_start, self.phrase_end,
                 self.phrase_count, self.unknown, self.timestamp
                 ) = (self.unknown, self.version,
                 self.phrase_offset_start, self.phrase_start, self.phrase_end,
                 self.phrase_count, self.timestamp
                 )
                assert (self.phrase_offset_start == 0x00000040) and (
                    self.phrase_offset_start + 4 * self.phrase_count == self.phrase_start)
            else:
                from datetime import datetime;
                print("ERROR unknown version (%X %X %X %X %X %X %X)"
                     % (self.unknown, self.version,
                     self.phrase_offset_start, self.phrase_start, self.phrase_end,
                     self.phrase_count, self.timestamp));
                raise;

            self.timestamp_e = file.read(self.phrase_offset_start - file.tell());
            self.phrase_offsets = [];
            for i in range(self.phrase_count):
                offset = fi.read_uint();
                self.phrase_offsets.append(offset);
            self.phrase_offsets.append(self.phrase_end - self.phrase_start);

            self.phrases = [];
            for i in range(self.phrase_count):
                phrase_magic = fi.read_uint();
                if phrase_magic != self.phrase_magic:
                    print("ERROR phrase_magic: 0x%X != 0x%X, file(%s)offset(0x%X)"
                          % (phrase_magic, self.phrase_magic, self.file_name, file.tell()));
                    raise;
                offset = fi.read_ushort();
                candidate = fi.read_byte();
                candidate2 = fi.read_byte();

                if self.phrase_magic == 0x00100010:
                    phrase_unknown = fi.read_ulonglong();
                    pinyin = file.read(offset - 0x0010).decode('utf-16')[:-1];
                elif self.phrase_magic == 0x00080008:
                    pinyin = file.read(offset - 0x0008).decode('utf-16')[:-1];

                phrase_len = self.phrase_offsets[i + 1] - self.phrase_offsets[i] - offset;
                phrase = file.read(phrase_len).decode('utf-16')[:-1];

                if self.phrase_magic == 0x00100010:
                    self.phrases.append((offset, candidate, candidate2,
                                         phrase_unknown, pinyin, phrase));
                elif self.phrase_magic == 0x00080008:
                    self.phrases.append((offset, candidate, candidate2,
                                         pinyin, phrase));
                else:
                    print("ERROR unknown version");

    def dump(self):
        print('proto:', self.proto);
        print('unknown: \t0x%08X' % self.unknown);
        print('version: \t0x%08X' % self.version);
        print('phrase_offset_start: 0x%08X' % self.phrase_offset_start);
        print('phrase_start: \t0x%08X' % self.phrase_start);
        print('phrase_end: \t0x%08X' % self.phrase_end);
        print('phrase_count: \t0x%08X' % self.phrase_count);
        print('phrase_magic: \t0x%08X' % self.phrase_magic);

        from datetime import datetime;
        print('timestamp:', datetime.fromtimestamp(self.timestamp));
        # print('timestamp_e:', self.timestamp_e);

        if self.phrase_magic == 0x00100010:
            for i in range(self.phrase_count):
                (offset, candidate, candidate2, phrase_unknown, pinyin, phrase) = self.phrases[i];
                print(i, pinyin, "===", phrase, "@@@", (candidate, candidate2, "0x%X" % phrase_unknown));
        elif self.phrase_magic == 0x00080008:
            for i in range(self.phrase_count):
                (offset, candidate, candidate2, pinyin, phrase) = self.phrases[i];
                print(i, pinyin, "===", phrase, "@@@", (candidate, candidate2));
        else:
            print("ERROR unknown version");


class MschxudpFileBuilder(object):
    '''
    classdocs
    '''


    def __init__(self, win10='1703', phrase_magic=0x00100010):
        '''
        Constructor
        '''
        self.phrases = [];
        self.proto = b'mschxudp'
        self.version = 1;
        self.phrase_offset_start = 0x00000040;
        if win10 == '1703' or phrase_magic == 0x00100010:
            self.unknown = 0x00600002;
            self.phrase_magic = 0x00100010;
        elif win10 == '1607' or phrase_magic == 0x00080008:
            self.unknown = 0x00000000;
            self.phrase_magic = 0x00080008;
        else:
            print("ERROR unsurport version");
            raise

    def add_phrase(self, candidate, pinyin, phrase, *phrase_unknown):
        if(len(phrase_unknown) == 0) and self.phrase_magic == 0x00100010:
            phrase_unknown = 0x20990A9600000000;
        self.phrases.append((candidate, pinyin, phrase, phrase_unknown));

    def save(self, file_name):
        with open(file_name, 'wb') as file:
            fi = WriteHelper(file)

            phrase_count = len(self.phrases);
            phrase_start = self.phrase_offset_start + phrase_count * 4;

            file.seek(phrase_start, SEEK_SET);

            phrase_offsets = [];
            phrase_offset = 0;
            for i in self.phrases:
                # i : (candidate[2], pinyin, phrase, *phrase_unknown)
                phrase_offsets.append(phrase_offset);

                pinyin_utf16 = (i[1] + '\0').encode('utf-16-le');
                phrase_utf16 = (i[2] + '\0').encode('utf-16-le');
                if self.phrase_magic == 0x00100010:
                    offset = 0x0010 + len(pinyin_utf16);
                    fi.write_struct('IHBBQ', self.phrase_magic, offset, i[0][0], i[0][1], i[3]);
                elif self.phrase_magic == 0x00080008:
                    offset = 0x0008 + len(pinyin_utf16);
                    fi.write_struct('IHBB', self.phrase_magic, offset, i[0][0], i[0][1]);
                file.write(pinyin_utf16)
                file.write(phrase_utf16);

                phrase_offset += offset + len(phrase_utf16);

            phrase_end = phrase_start + phrase_offset

            from datetime import datetime;
            timestamp = int(datetime.now().timestamp());


            file.seek(0, SEEK_SET);
            file.write(self.proto);
            assert file.tell() == 8

            if self.phrase_magic == 0x00100010:
                fi.write_struct('IIIIIII', self.unknown, self.version,
                 self.phrase_offset_start, phrase_start, phrase_end,
                 phrase_count, timestamp);
            elif self.phrase_magic == 0x00080008:
                fi.write_struct('IIIIIII', self.version,
                 self.phrase_offset_start, phrase_start, phrase_end,
                 phrase_count, self.unknown, timestamp);
            assert file.tell() == 0x24

            file.seek(self.phrase_offset_start, SEEK_SET);
            for i in phrase_offsets:
                fi.write_int(i);
