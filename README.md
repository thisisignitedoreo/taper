
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

---

_good for distributing malware and pirated games /s_

