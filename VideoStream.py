class VideoStream:
    def __init__(self, filename) -> None:
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frame = 0

    def next_frame(self):
        data = self.file.read(5)
        if data:
            framelength = int(data)
            data = self.file.read(framelength)
            self.frame += 1
        return data

    def frameNbr(self):
        return self.frame