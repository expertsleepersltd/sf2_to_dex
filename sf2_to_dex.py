from chunk import Chunk
import os, sys, struct
import wave

sf2file = sys.argv[1]

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

class sfSample:
	def __init__(self):
		pass
	def __str__(self):
		return self.name
	def __repr__(self):
		return 'sfSample(name="'+self.name+',start=%d)' % ( self.start )

samples = []

sampleTypes = { 1:'mono', 2:'right', 4:'left', 8:'linked' }

with open(sf2file, 'rb') as F:
	chfile = Chunk( F )
	riff = chfile.getname()
	WAVE = chfile.read(4)
	while 1:
		try:
			chunk = Chunk(chfile, bigendian = 0)
		except EOFError:
			break
		name = chunk.getname()
		print name
		if name == 'LIST':
			listname = chfile.read(4)
			print '\t', listname
		elif name == 'smpl':
			sampleDataStart = chfile.tell() + 8
			print 'sample data starts at', sampleDataStart
			chunk.skip()
		elif name == 'shdr':
			for i in range( ( chunk.chunksize/46 ) - 1 ):
				s = sfSample()
				s.name = chfile.read(20)
				s.start = _read_dword( chfile )
				s.end = _read_dword( chfile )
				s.startLoop = _read_dword( chfile )
				s.endLoop = _read_dword( chfile )
				s.sampleRate = _read_dword( chfile )
				s.pitch = _read_byte( chfile )
				s.correction = _read_byte( chfile )
				s.link = _read_word( chfile )
				s.type = _read_word( chfile )
				samples.append( s )
			chfile.read(46)
		else:
			chunk.skip()

for s in samples:
	typeName = sampleTypes[ s.type & 0x7fff ]
	print '%s %d %d %d %d %d %d %d %d %s' % ( s.name, s.start, s.end, s.startLoop, s.endLoop, s.sampleRate, s.pitch, s.correction, s.link, typeName )

noteNames = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

F = open(sf2file, 'rb')
F2 = open(sf2file, 'rb')

folderName = os.path.basename( sf2file ).split('.')[0]
folderName = "".join(x for x in folderName if x.isalnum() or x ==' ')
print folderName

if not os.path.exists( folderName ):
	os.mkdir( folderName )
os.chdir( folderName )

for s in samples:
	if s.type not in [1,4]:
		continue
	filename = "".join(x for x in s.name if x.isalnum())
	filename += '_'
	filename += noteNames[ s.pitch % 12 ]
	filename += str( ( s.pitch/12 ) - 1 )
	filename += '.wav'
	print filename
	G = wave.open( filename, 'w' )
	G.setsampwidth( 2 )
	G.setframerate( s.sampleRate )
	F.seek( sampleDataStart + 2*s.start )
	frames = s.end-s.start+1
	if s.type == 1:
		G.setnchannels( 1 )
		data = F.read( 2*frames )
		G.writeframesraw( data )
	else:
		G.setnchannels( 2 )
		F2.seek( sampleDataStart + 2*samples[ s.link ].start )
		for i in range(frames):
			data = F.read( 2 )
			G.writeframesraw( data )
			data = F2.read( 2 )
			G.writeframesraw( data )
	G.close()
	loopLength = s.endLoop - s.startLoop
	if loopLength > 1:
		G = open( filename, 'r+b' )
		G.seek( 4 )
		riffSize = _read_dword( G )
		G.seek( 4 )
		_write_dword( G, riffSize+0x76 )
		G.seek( 8+riffSize )
		_write_dword( G, 0x20657563 )		# 'cue '
		_write_dword( G, 0x34 )
		_write_dword( G, 0x2 )				# num cues
		_write_dword( G, 0x1 )				# id
		_write_dword( G, s.startLoop-s.start )		# position
		_write_dword( G, 0x61746164 )		# 'data'
		_write_dword( G, 0x0 )
		_write_dword( G, 0x0 )
		_write_dword( G, s.startLoop-s.start )		# position
		_write_dword( G, 0x2 )				# id
		_write_dword( G, s.endLoop-s.start )		# position
		_write_dword( G, 0x61746164 )		# 'data'
		_write_dword( G, 0x0 )
		_write_dword( G, 0x0 )
		_write_dword( G, s.endLoop-s.start )		# position
		_write_dword( G, 0x5453494C )		# 'LIST'
		_write_dword( G, 0x32 )
		_write_dword( G, 0x6C746461 )		# 'adtl'
		_write_dword( G, 0x6C62616C )		# 'labl'
		_write_dword( G, 0x10 )
		_write_dword( G, 0x1 )				# id
		_write_dword( G, 0x706F6F4C )		# 'Loop'
		_write_dword( G, 0x61745320 )		# ' Sta'
		_write_dword( G, 0x7472 )			# 'rt'
		_write_dword( G, 0x6C62616C )		# 'labl'
		_write_dword( G, 0x0E )
		_write_dword( G, 0x2 )				# id
		_write_dword( G, 0x706F6F4C )		# 'Loop'
		_write_dword( G, 0x646E4520 )		# ' End'
		_write_word( G, 0x0 )
		G.close()


