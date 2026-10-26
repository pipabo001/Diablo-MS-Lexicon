
# Format    C Type    Python type    Standard size    Notes
# x    pad byte    no value
# c    char    bytes of length 1    1
# b    signed char    integer    1    (1),(3)
# B    unsigned char    integer    1    (3)
# ?    _Bool    bool    1    (1)
# h    short    integer    2    (3)
# H    unsigned short    integer    2    (3)
# i    int    integer    4    (3)
# I    unsigned int    integer    4    (3)
# l    long    integer    4    (3)
# L    unsigned long    integer    4    (3)
# q    long long    integer    8    (2), (3)
# Q    unsigned long long    integer    8    (2), (3)
# n    ssize_t    integer         (4)
# N    size_t    integer         (4)
# e    (7)    float    2    (5)
# f    float    float    4    (5)
# d    double    float    8    (5)
# s    char[]    bytes
# p    char[]    bytes

import struct

class ReadHelper(object):
    def __init__(self, file):
        self.file = file;

    def read_struct(self, fmt):
        return struct.unpack(fmt, self.file.read(struct.calcsize(fmt)));

    def read_int(self):
        return self.read_struct("i")[0];

    def read_uint(self):
        return self.read_struct("I")[0];

    def read_char(self):
         return self.read_struct("b")[0];

    def read_byte(self):
         return self.read_struct("B")[0];

    def read_short(self):
        return self.read_struct("h")[0];

    def read_ushort(self):
        return self.read_struct("H")[0];

    def read_long(self):
        return self.read_struct("l")[0];

    def read_ulong(self):
        return self.read_struct("L")[0];

    def read_longlong(self):
        return self.read_struct("q")[0];

    def read_ulonglong(self):
        return self.read_struct("Q")[0];



class WriteHelper(object):
    def __init__(self, file):
        self.file = file;

    def write_struct(self, fmt, *args):
        return self.file.write(struct.pack(fmt, *args));

    def write_int(self, n):
        return self.write_struct("i", n);

    def write_uint(self, n):
        return self.write_struct("I", n);

    def write_char(self, n):
         return self.write_struct("b", n);

    def write_byte(self, n):
         return self.write_struct("B", n);

    def write_short(self, n):
        return self.write_struct("h", n);

    def write_ushort(self, n):
        return self.write_struct("H", n);

    def write_long(self, n):
        return self.write_struct("l", n);

    def write_ulong(self, n):
        return self.write_struct("L", n);

    def write_longlong(self, n):
        return self.write_struct("q", n);

    def write_ulonglong(self, n):
        return self.write_struct("Q", n);

