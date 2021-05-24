"""
	Original version:
	 	Copyright (c) 2020 Expert Sleepers Ltd. MIT License.

	Python 3 modifications:
	 	Copyright (c) 2021 Robin Parmar. MIT License. <robin@robinparmar.com>
"""

### LIBRARIES
import os, sys, struct
from chunk import Chunk
import wave

### GLOBAL VARIABLES
# retrieve command line argument
sf2file = sys.argv[1]

# a list of sfSample instances
sfSamples = []

# offset
sampleDataStart = 0;

### HELPER FUNCTIONS
def _read_dword( F ):
	return struct.unpack('<i', F.read(4))[0]
def _read_word( F ):
	return struct.unpack('<h', F.read(2))[0]
def _read_byte( F ):
	return struct.unpack('<b', F.read(1))[0]

def _write_dword( F, v ):
	F.write( struct.pack('<i', v) )
def _write_word( F, v ):
	F.write( struct.pack('<h', v) )

### SAMPLE CLASS
class sfSample:
	def __init__(self, f):
		self.name = f.read(20)
		self.start = _read_dword(f)
		self.end = _read_dword(f)
		self.startLoop = _read_dword(f)
		self.endLoop = _read_dword(f)
		self.sampleRate = _read_dword(f)
		self.pitch = _read_byte(f)
		self.correction = _read_byte(f)
		self.link = _read_word(f)
		self.type = _read_word(f)
	def __str__(self):
		return self.name
	def __repr__(self):
		return 'sfSample(name="%s",start=%d)' % (self.name, self.start)

# remove illegal characters from a binary sequence
def cleanse(seq):
	return "".join(x for x in seq.decode("utf-8", "replace") if x.isalnum())

# read the soundFont to populate sample list
def readSoundfont():
	print("\nReading soundfont: ", sf2file)

	with open(sf2file, 'rb') as F:
		chfile = Chunk(F)
		riff = chfile.getname()
		temp = chfile.read(4)

		while True:
			try:
				chunk = Chunk(chfile, bigendian=0)
			except EOFError:
				break

			name = chunk.getname()
			if name == b'LIST':
				listname = chfile.read(4)
			elif name == b'smpl':
				sampleDataStart = chfile.tell() + 8
				chunk.skip()
			elif name == b'shdr':
				for i in range( int(chunk.chunksize/46) - 1 ):
					s = sfSample(chfile)
					sfSamples.append(s)
				chfile.read(46)
			else:
				chunk.skip()

# create folder to store all output WAVs
def newFolder():
	fdn = os.path.basename(sf2file).split('.')[0]
	fdn = "".join(x for x in fdn if x.isalnum() or x ==' ')
	if not os.path.exists(fdn):
		os.mkdir(fdn)

	print("Writing to folder: ", fdn)
	return fdn

# write out individual WAV files from the soundfont
def writeWaves(folderName):
	noteNames = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

	F = open(sf2file, 'rb')
	F2 = open(sf2file, 'rb')

	# iterate through all sfSample instances
	for s in sfSamples:
		if s.type not in [1, 4]:
			continue

		filename = "{}_{}{}.wav".format( cleanse(s.name), noteNames[s.pitch % 12], int((s.pitch/12)-1) )
		print("\t", filename)

		filename = os.path.join(folderName, filename)
		with wave.open(filename, 'w') as G:
			G.setsampwidth(2)
			G.setframerate(s.sampleRate)
			F.seek(sampleDataStart + 2*s.start)
			frames = s.end-s.start+1

			if s.type == 1:
				G.setnchannels(1)
				data = F.read(2*frames)
				G.writeframesraw(data)
			else:
				G.setnchannels(2)
				F2.seek( sampleDataStart + 2*sfSamples[ s.link ].start )
				for i in range(frames):
					data = F.read(2)
					G.writeframesraw(data)
					data = F2.read(2)
					G.writeframesraw(data)

		loopLength = s.endLoop - s.startLoop

		if loopLength > 1:
			with open(filename, 'r+b') as G:
				G.seek( 4 )
				riffSize = _read_dword( G )

				G.seek( 4 )
				_write_dword( G, riffSize+0x76 )

				G.seek( 8+riffSize )
				_write_dword( G, 0x20657563 )				# 'cue '
				_write_dword( G, 0x34 )
				_write_dword( G, 0x2 )						# num cues
				_write_dword( G, 0x1 )						# id
				_write_dword( G, s.startLoop-s.start )		# position
				_write_dword( G, 0x61746164 )				# 'data'
				_write_dword( G, 0x0 )
				_write_dword( G, 0x0 )
				_write_dword( G, s.startLoop-s.start )		# position
				_write_dword( G, 0x2 )						# id
				_write_dword( G, s.endLoop-s.start )		# position
				_write_dword( G, 0x61746164 )				# 'data'
				_write_dword( G, 0x0 )
				_write_dword( G, 0x0 )
				_write_dword( G, s.endLoop-s.start )		# position
				_write_dword( G, 0x5453494C )				# 'LIST'
				_write_dword( G, 0x32 )
				_write_dword( G, 0x6C746461 )				# 'adtl'
				_write_dword( G, 0x6C62616C )				# 'labl'
				_write_dword( G, 0x10 )
				_write_dword( G, 0x1 )						# id
				_write_dword( G, 0x706F6F4C )				# 'Loop'
				_write_dword( G, 0x61745320 )				# ' Sta'
				_write_dword( G, 0x7472 )					# 'rt'
				_write_dword( G, 0x6C62616C )				# 'labl'
				_write_dword( G, 0x0E )
				_write_dword( G, 0x2 )						# id
				_write_dword( G, 0x706F6F4C )				# 'Loop'
				_write_dword( G, 0x646E4520 )				# ' End'
				_write_word( G, 0x0 )

# master flow
def main():
	readSoundfont()
	folderName = newFolder()
	writeWaves(folderName)

main()
