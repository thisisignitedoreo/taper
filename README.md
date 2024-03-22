
# taper
very simple file archiver

## overview
to create an archive (a tape):
```console
$ python main.py t file.tape file1 file2 dir1 -r
```

to list archive contents:
```console
$ python main.py l file.tape
```

to extract a tape:
```console
$ python main.py e file.tape some_directory
```

for further information run program without any arguments

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
	FileStructure files;
	u64 dataLength;
	char data[dataLength];
} TapeFile;

```

---

_good for distributing malware and pirated games /s_

