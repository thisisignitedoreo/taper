
# taper
dead simple file archiver made just out of curiosity

## overview
to get detailed help:
```console
$ python main.py
```

## file format
.tape file is binary file with following structure:
```c

typedef struct {
    u8 isDir;
    u32 nameLength;
    char name[nameLength];
    // if !isDir
    u64 dataPtr;
    u64 size;
    // endif
} File;

typedef struct {
    u32 files;
    File data[files];
} FileStructure;

typedef struct {
    char magic[4]; // = "TAPE"
    u8 versionMajor;
    u8 versionMinor;
    // 2.0
    FileStructure files;
    bool isEncrypted; // if 1 file is encrypted and has 8 bytes of salt at the start
    char salt[8]; // ascii string of salt, used to check if password is correct
                  // compare it with decrypted first 8 bytes of data section
                  // mismatch means password isn't correct
                  // in theory smth could go wrong but i would not count on it
                  // contains no security-sensetive information
                  // if isEncrypted is false is not present
                  // but, 8 bytes of salt are still in the data section, just ignore it
    u64 dataLength;
    u8 compressionMethod;
    // compression method:
    // 0: none (uncompressed)
    // 1: zlib
    // 2: lzma (xz)
    // 3: bzip2
    char data[dataLength];
} TapeFile;

```

few important words about password protection:

- it is probably not that secure
- it is probably shit
- it does not encrypt file structure

so how it works:

data section is xored with the password by the following algorithm

- you take sha256 of the password
- you xor all bytes of data section with next byte of hash, looping over it

example:
sha256 of password is `1d2a003d` (not a real hash, but it is not really relevent here)

```
data   | 0x25 0x56 0x76 0x25 0x56 0x76 0x25 0x56 0x76
hash   | 0x1d 0x2a 0x00 0x3d 0x1d 0x2a 0x00 0x3d 0x1d
       |     note start over ^
       | xor operation
result | 0x38 0x7c 0x76 0x25 0x2e 0x45 0x41 0x4b 0x5c
```

apply same algorithm to decrypt it ( `xor(xor(a, b), b) == a` =^) )

---

_good for distributing malware and pirated games /s_

