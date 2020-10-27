from zlib import adler32
import gzip, glob
from py3 import to_bytes, PY3

def part(nparts, path):
        if nparts <= 1: return 0
        if PY3:    path = to_bytes(path)
        return adler32(path) % nparts
        
class _Partition(object):
    
    def __init__(self, f):
        self.F = f
        
    def __iter__(self):
        return self
        
    def __next__(self):
        l = self.F.readline()
        if not l:
            raise StopIteration
        return l.strip()
        
class PartitionedList(object):
    
    def __init__(self, mode, filenames, compressed=False):
        #
        # mode: "r" or "w"
        #
        self.Mode = mode
        self.FileNames = filenames
        self.Files = []
        self.NParts = len(filenames)
        self.Compressed = compressed
        
        if mode == "w":
            self.Files = [open(fn, "wt") if not compressed else gzip.open(fn, "w") for fn in self.FileNames]
        else:
            self.Files = [open(fn, "rt") if not fn.endswith(".gz") else gzip.open(fn, "r") for fn in self.FileNames]
            
    @staticmethod
    def open(prefix=None, files=None):
        # open existing set
        if files is None:
            files = sorted(glob.glob(f"{prefix}.*"))
        return PartitionedList("r", files)
        
    @staticmethod
    def create(nparts, prefix, compressed=False):
        # create new set
        gz = ".gz" if compressed else ""
        files = ["%s.%05d%s" % (prefix, i, gz) for i in range(nparts)]
        return PartitionedList("w", files, compressed)
        
    def add(self, item):
        if self.Mode != "w":    raise ValueError("The list is not open for writing")
        item = item.strip()
        i = part(self.NParts, item)
        item = item+"\n"
        if self.Compressed: item = to_bytes(item)
        self.Files[i].write(item)
        
    def files(self):
        return self.Files
        
    def items(self):
        assert self.Mode == "r"
        for f in self.Files:
            l = f.readline()
            while l:
                yield l.strip()
                l = f.readline()
                
    def __iter__(self):
        return self.items()

    def close(self):
        [f.close() for f in self.Files]

    def __del__(self):
        self.close()

if __name__ == "__main__":
    import sys, glob
    prefix = sys.argv[1]
    lst = PartitionedList.open(prefix=prefix)
    
    for i, part in enumerate(lst.partitions()):
        print(f"----- part {i} -----")
        files = list(part)
        for f in files:
            print(f)
        