#!/bin/env python3

from dataclasses import dataclass
import zlib, lzma, bz2
import sys
import os

def error(string):
    print(f"error: {string}")
    sys.exit(1)

comp_methods = ["none", "zlib", "lzma", "bz2"]
def_comp = 1

arr_to_indices = lambda a: {i: k for k, i in zip(range(len(a)), a)}

def print_usage(program):
    print(f"usage: {program} <operation> <file> [args]")
    print( "  operations:")
    print( "    tape    (t) - pack files into tape with given compression")
    print(f"                  (recursively if -r specified) (def compression is {comp_methods[def_comp]})")
    print( "      args: [files] [-r] [-c=compression]")
    print(f"      compression methods: {', '.join(comp_methods)}")
    print( "    extract (e) - unpack files from tape to dst (cwd if unspecified)")
    print( "      args: [dst]")
    print( "    list    (l) - list files in tape")
    print( "      args: none")

def parse_args(args):
    program = args.pop(0)
    if len(args) == 0:
        print_usage(program)
        error("expected operation")
    
    operation = args.pop(0)
    
    if len(args) == 0:
        print_usage(program)
        error("tape operation expects output file")
    
    file = args.pop(0)

    if operation in ("tape", "t"):
        files = []
        compression = def_comp
        do_args = True
        recursively = False
        for i in args:
            if i == "--":
                do_args = False
                continue

            if i == "-r" and do_args:
                recursively = True
                continue
            
            if i.startswith("-c=") and do_args:
                compression = i[3:]
                if compression not in comp_methods:
                    error(f"'{compression}' is not supported compression method (supported: {', '.join(comp_methods)})")
                compression = arr_to_indices(comp_methods)[compression]
                continue

            files.append(i)

        if len(files) == 0:
            error("no files specified")

        return 1, file, [files, recursively, compression]
    elif operation in ("extract", "e"):
        if len(args) == 0: dst = "."
        else:
            dst = args.pop(0)
            if not os.path.isdir(dst):
                error("no such directory")

        return 2, file, [dst]
    elif operation in ("list", "l"):
        return 3, file, []
    else:
        error(f"unknown operation {operation}")

# huge hack, for fixing absolute paths
prefixes = []

def parse_files(files, recursively, path="", prefix=None, first_run=True):
    global prefixes
    ret = []
    if first_run:
        for k, i in enumerate(files):
            #if not i.startswith("/"):
            #    prefixes.append("")
            #    continue
            if "/" not in i:
                prefixes.append("")
                continue

            if i.endswith("/"):
                prefixes.append(i.rsplit("/", 2)[0] + "/")
                files[k] = i.rsplit("/", 2)[1] + "/"
            else:
                prefixes.append(i.rsplit("/", 1)[0] + "/")
                files[k] = i.rsplit("/", 1)[1]

    for k, i in enumerate(files):
        imagpath = path + i
        if prefix is None: realpath = prefixes[k] + path + i
        else: realpath = prefix + path + i
        if os.path.isfile(realpath):
            ret.append((prefixes[k] if prefix is None else prefix, imagpath))
        elif os.path.isdir(realpath):
            ret.append((prefixes[k] if prefix is None else prefix, path + (i if i.endswith("/") else i + "/")))
            if recursively:
                ret += parse_files(os.listdir(realpath), True, path + (i if i.endswith("/") else i + "/"), prefixes[k] if prefix is None else prefix, False)
        else:
            error(f"file {i} does not exist")
    return ret

fmt_ver_maj = 2
fmt_ver_min = 0

def serialize(files, compression):
    file = b"TAPE"
    file += fmt_ver_maj.to_bytes()
    file += fmt_ver_min.to_bytes()
    # data
    data = bytes()
    file_pointers = {}
    for prefix, filename in files:
        if not filename.endswith("/"):
            pointer = [len(data)]
            data += open(prefix + filename, "rb").read()
            pointer.append(len(data) - pointer[0])
            file_pointers[filename] = pointer

    # file structure
    file += len(files).to_bytes(4)
    for _, i in files:
        file += int(i.endswith("/")).to_bytes()
        file += len(i).to_bytes(4)
        file += i.encode()
        if not i.endswith("/"):
            file += file_pointers[i][0].to_bytes(8)
            file += file_pointers[i][1].to_bytes(8)

    # data
    if compression == 1:
        data = zlib.compress(data)
    elif compression == 2:
        data = lzma.compress(data)
    elif compression == 3:
        data = bz2.compress(data)
    
    file += len(data).to_bytes(8)
    file += compression.to_bytes()
    file += data

    return file

def CHECK_TAPE_FILE(f):
    if f.read(4) != b"TAPE":
        error("isn't a tapefile")
    ver_maj = int.from_bytes(f.read(1))
    ver_min = int.from_bytes(f.read(1))
    if ver_maj != fmt_ver_maj:
        error(f"major format versions dont match ({fmt_ver_maj}.{fmt_ver_min} <> {ver_maj}.{ver_min})")
    return ver_maj, ver_min

if __name__ == "__main__":
    print(f"taper, binary version {fmt_ver_maj}.{fmt_ver_min}")
    op, file, args = parse_args(sys.argv)

    # taping
    if op == 1:
        tape = serialize(parse_files(args[0], args[1]), args[2])
        open(file, "wb").write(tape)
        print(f"wrote {len(tape)} bytes")
    
    # extracting
    elif op == 2:
        file_paths = {}
        dst = args[0]
        with open(file, "rb") as f:
            CHECK_TAPE_FILE(f)
            files = int.from_bytes(f.read(4))
            for i in range(files):
                is_dir = bool(int.from_bytes(f.read(1)))
                name_length = int.from_bytes(f.read(4))
                name = f.read(name_length).decode()
                if not is_dir:
                    ptr = int.from_bytes(f.read(8))
                    size = int.from_bytes(f.read(8))

                if is_dir:
                    file_paths[name] = None
                else:
                    file_paths[name] = [ptr, size]

            data_length = int.from_bytes(f.read(8))
            data_compression = int.from_bytes(f.read(1))
            data = f.read(data_length)

            if data_compression == 1:
                data = zlib.decompress(data)
            elif data_compression == 2:
                data = lzma.decompress(data)
            elif data_compression == 3:
                data = bz2.decompress(data)

            for k, v in file_paths.items():
                print(k)
                if v == None:
                    os.mkdir(os.path.join(dst, k))
                else:
                    file = open(os.path.join(dst, k), "wb")
                    file.write(data[v[0]:v[0]+v[1]])
                    file.close()

    # listing
    elif op == 3:
        with open(file, "rb") as f:
            ver_maj, ver_min = CHECK_TAPE_FILE(f)
            print(f"binary version {ver_maj}.{ver_min}")
            files = int.from_bytes(f.read(4))
            full_size = 0
            for i in range(files):
                is_dir = bool(int.from_bytes(f.read(1)))
                name_length = int.from_bytes(f.read(4))
                name = f.read(name_length).decode()
                if not is_dir:
                    ptr = int.from_bytes(f.read(8))
                    size = int.from_bytes(f.read(8))
                    full_size += size

                if is_dir:
                    print(f"directory\t{name}")
                else:
                    print(f"{size} bytes\t{name}")

            data_length = int.from_bytes(f.read(8))
            data_compression = int.from_bytes(f.read(1))

            print(f"data section length: {data_length} bytes ({full_size} bytes uncompressed)")
            print(f"compressing method: {comp_methods[data_compression]} {full_size/data_length:0.2f}x")

# thats all folks!

