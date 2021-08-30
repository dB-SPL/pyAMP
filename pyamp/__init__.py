__version__ = 'pyAMP 0.0.4 preview'

import PySimpleGUI as sg
import pickle
import pyfldigi
import crcmod
import base64
import lzma
from time import gmtime, strftime
from datetime import datetime
from os import __file__, getcwd, path, mkdir, stat

fldigi = pyfldigi.Client()
rxdata = b''
rx_counter = int(0)
requested_blocks = []

script_dir = getcwd()

fileListUpdated = False

pyamp_icon = b'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'

def save_config(config_dict):
	with open('config','wb') as f:
		pickle.dump(config_dict,f)
		print('Saved configuration file.')
		fileListUpdated = True

def create_config():
	global __version__
	mycall = ''
	info = ''
	version = __version__
	config_dict = {'mycall': mycall, 'info': info, 'version': version}
	return config_dict

def update_config(config_dict):
	mycall = input("Current Callsign: " + config_dict['mycall'] + "\nNew Callsign:")
	info = ' ' + input("Current info: " + config_dict['info'] + '\nAdditional info to display such as QTH or group name:')
	new_config = {'mycall': mycall, 'info': info}
	save_config(new_config)
	return new_config

try:
	with open('config','rb') as f:
		config = pickle.load(f)
	config_exists = True
except FileNotFoundError:
	print('No config file found.  Starting config...')
	config_exists = False
	config = create_config()
	save_config(config)
	

def save_files(files_dict):
	with open('files','wb') as f:
		pickle.dump(files_dict,f)
		
try:
	with open('files','rb') as f:
		files = pickle.load(f)
except FileNotFoundError:
	print('List of received files not found.  Starting a new list...')
	files = {'unknown': {'hash': {}}}
	save_files(files)
	print('Saved new file list.')

def checksum(data):
	crc16 = crcmod.mkCrcFun(0x18005, 0xffff, True)
	
	if type(data) == str:
		crc = '{0:0{1}X}'.format(crc16(data.encode()),4)

	if type(data) == bytes:
		crc = '{0:0{1}X}'.format(crc16(data),4)
	return crc        

def k2sToBase64(file_path):
	with open(file_path, 'rb') as file:
		k2s = file.read()
	uncompressed_size = len(k2s)
	compressed_data = lzma.compress(k2s,format=lzma.FORMAT_RAW,filters=[{'id': lzma.FILTER_LZMA2}])[6:][:-1]
	bin = b''.join([b'\x01LZMA',len(k2s).to_bytes(4, byteorder="big"),b']\x00\x00\x00\x04',compressed_data])
	return base64.b64encode(bin).decode()

def base64ToFlamp(file_hash,block_size,b64str):
	b64str = '[b64:start]' + b64str + '\n[b64:end]'
	data_array = [b64str[i:i+block_size] for i in range(0, len(b64str), block_size)]
	block_array = []
	for i in range(0, len(data_array)):
		block_number = str(i + 1)
		block_contents = '{' + file_hash + ':' + block_number + '}' + data_array[i]
		block_array.append('<DATA ' + str(len(block_contents)) + ' ' + checksum(block_contents) + '>' + block_contents)
	return block_array

def makePreamble(file_hash, date_time_filename, msg_size, num_of_blocks, block_size, id=config['mycall'] + config['info'], prog=config['version']):
	prog_contents = '{' + file_hash + '}' + prog
	file_contents = '{' + file_hash + '}' + date_time_filename
	id_contents = '{' + file_hash + '}' + id
	size_contents = '{' + file_hash + '}' + str(msg_size) + ' ' + str(num_of_blocks) + ' ' + str(block_size) 
	pre_prog = '<PROG ' + str(len(prog_contents)) + ' ' + checksum(prog_contents) + '>' + prog_contents
	pre_file = '<FILE ' + str(len(file_contents)) + ' ' + checksum(file_contents) + '>' + file_contents
	pre_id = '<ID ' + str(len(id_contents)) + ' ' + checksum(id_contents) + '>' + id_contents
	pre_size = '<SIZE ' + str(len(size_contents)) + ' ' + checksum(size_contents) + '>' + size_contents
	preamble = pre_prog + '\n' + pre_file + '\n' + pre_id + '\n' + pre_size + '\n'
	return preamble

def fileToFlamp(file_path,relay=False,block_size=64,compress='auto',file_hash='auto',base_conversion='base64'):
	if compress in ['auto', 'true', 'True', True]:
		comp = "1"
	else:
		 comp = "0"
	if file_hash == 'auto':
		date_time_string = datetime.fromtimestamp(stat(file_path).st_mtime).strftime('%Y%m%d%H%M%S')
		date_time_filename = date_time_string + ':' + path.basename(file_path)
		file_hash = checksum(date_time_filename + comp + base_conversion + str(block_size))
	with open(file_path, 'rb') as file:
		k2s = file.read()
	if comp == "1":
		uncompressed_size = len(k2s)
		compressed_data = lzma.compress(k2s,format=lzma.FORMAT_RAW,filters=[{'id': lzma.FILTER_LZMA2}])[6:][:-1]
		b64 = base64.b64encode(b''.join([b'\x01LZMA',len(k2s).to_bytes(4, byteorder="big"),b']\x00\x00\x00\x04',compressed_data])).decode()
		msg = '[b64:start]' + b64 + '[b64:end]'
	else:
		msg = k2s.decode('cp1252')
	data_array = [msg[i:i+block_size] for i in range(0, len(msg), block_size)]
	block_array = []
	if relay == False:
		block_array.append(makePreamble(file_hash, date_time_filename, len(msg), int(len(data_array)), block_size, config['mycall']))
	else:
		block_array.append('FLAMP RELAY\n')
	for i in range(0, len(data_array)):
		block_number = str(i + 1)
		block_contents = '{' + file_hash + ':' + block_number + '}' + data_array[i]
		block_array.append('<DATA ' + str(len(block_contents)) + ' ' + checksum(block_contents) + '>' + block_contents + '\n')
	return block_array

def parse_block(string):
	string_split = string.split('{')
	hash_split = string_split[1].split(':')
	num_block = hash_split[1].split('}')
	return [hash_split[0], num_block[0], num_block[1]]



def add_proto_block(keyword, file_hash, block):
	global files
	print('Adding ' + keyword + ' block')
	hash_found = False
	if keyword == 'PROG':
		for file_name in files:
			if file_hash in files[file_name]['hash']:
				files[file_name]['hash'][file_hash]['prog'] = block
				hash_found =  True
		if hash_found == False:
			if 'unknown' not in files:
				files['unknown'] = {}
			if 'hash' not in files['unknown']:
				files['unknown']['hash'] = {}
			if file_hash not in files['unknown']['hash']:
				files['unknown']['hash'][file_hash] = {}
			files['unknown']['hash'][file_hash]['prog'] = block
	if keyword == 'ID':
		for file_name in files:
			if file_hash in files[file_name]['hash']:
				files[file_name]['hash'][file_hash]['id'] = block
				hash_found =  True
		if hash_found == False:
			if 'unknown' not in files:
				files['unknown'] = {}
			if 'hash' not in files['unknown']:
				files['unknown']['hash'] = {}
			if file_hash not in files['unknown']['hash']:
				files['unknown']['hash'][file_hash] = {}
			files['unknown']['hash'][file_hash]['id'] = block
	if keyword == 'DESC':
		for file_name in files:
			if file_hash in files[file_name]['hash']:
				files[file_name]['hash'][file_hash]['desc'] = block
				hash_found =  True
		if hash_found == False:
			if 'unknown' not in files:
				files['unknown'] = {}
			if 'hash' not in files['unknown']:
				files['unknown']['hash'] = {}
			if file_hash not in files['unknown']['hash']:
				files['unknown']['hash'][file_hash] = {}
			files['unknown']['hash'][file_hash]['desc'] = block
	if keyword == 'FILE':
		block_content = block.split(':')
		date_time_string = str(block_content[0])
		file_name = str(block_content[1])
		if file_name in files:
			if file_hash not in files[file_name]['hash']:
				files[file_name]['hash'][file_hash] = {}
			files[file_name]['hash'][file_hash]['date_time'] = date_time_string
		if file_name not in files:
			files[file_name] = {}
			files[file_name]['hash'] = {}
			files[file_name]['hash'][file_hash] = {}
			if file_hash in files['unknown']['hash']:
				files[file_name]['hash'][file_hash] = files['unknown']['hash'].pop(file_hash)
			files[file_name]['hash'][file_hash]['date_time'] = date_time_string
		if 'size' in files[file_name]['hash'][file_hash]:
			size = files[file_name]['hash'][file_hash]['size']
			size_content = size.split(' ')
			file_size = size_content[0]
			num_blocks = int(size_content[1])
			block_size = size_content[2]
			hash_string = date_time_string + ':' + file_name + '1' + 'base64' + '64'
			if file_hash == checksum(hash_string):
				files[file_name]['hash'][file_hash]['format'] ='1base6464'
				if 'data' not in files[file_name]:
					files[file_name]['data'] = {}
				existing_data = {}
				data_format = size + ' ' + '1base6464'
				if data_format in files[file_name]['data']:
					existing_data = files[file_name]['data'].pop(data_format)	
				files[file_name]['data'][data_format] = {}
				for blk_num in range(1,num_blocks + 1):
					files[file_name]['data'][data_format][blk_num] = b''
					if blk_num in existing_data:
						files[file_name]['data'][data_format][blk_num] = existing_data[blk_num]
					elif 'data' in files[file_name]['hash'][file_hash]:
						if blk_num in files[file_name]['hash'][file_hash]['data']:
							files[file_name]['data'][data_format][blk_num] = files[file_name]['hash'][file_hash]['data'].pop(blk_num)
			check_file_complete(file_name, file_hash)			
	if keyword == 'SIZE':
		hash_found = False
		block_content = block.split(' ')
		for file_name in files:
			if file_hash in files[file_name]['hash']:
				files[file_name]['hash'][file_hash]['size'] = block
				hash_found = True
				if 'date_time' in files[file_name]['hash'][file_hash]:
					date_time_string = files[file_name]['hash'][file_hash]['date_time']
					file_size = block_content[0]
					num_blocks = int(block_content[1])
					block_size = block_content[2]
					hash_string = date_time_string + ':' + file_name + '1' + 'base64' + '64'
					if file_hash == checksum(hash_string):
						files[file_name]['hash'][file_hash]['format'] ='1base6464'
						if 'data' not in files[file_name]:
							files[file_name]['data'] = {}
						existing_data = {}
						data_format = block + ' ' + '1base6464'
						if data_format in files[file_name]['data']:
							existing_data = files[file_name]['data'].pop(data_format)	
						files[file_name]['data'][data_format] = {}
						for blk_num in range(1,num_blocks + 1):
							files[file_name]['data'][data_format][blk_num] = b''
							#if blk_num in existing_data:
							#	files[file_name]['data'][data_format][blk_num] = existing_data[blk_num]
							if 'data' in files[file_name]['hash'][file_hash]:
								if blk_num in files[file_name]['hash'][file_hash]['data']:
									files[file_name]['data'][data_format][blk_num] = files[file_name]['hash'][file_hash]['data'].pop(blk_num)							
		if hash_found == True:
			fileListUpdated = True
			check_file_complete(file_name, file_hash)
		if hash_found == False:
			if 'unknown' not in files:
				files['unknown'] = {}
			if 'hash' not in files['unknown']:
				files['unknown']['hash'] = {}
			if file_hash not in files['unknown']['hash']:
				files['unknown']['hash'][file_hash] = {}
			files['unknown']['hash'][file_hash]['size'] = block

def write_msg_to_file(data_bytes, file_name, compressed=True):
	print('decoding :' + file_name)
	base_encoding = 'none'
	for i in ['b64', 'b128', 'b256']:
		if i.encode() in data_bytes:
			base_encoding = i
			start = '[' + i + ':start]'
			end = '[' + i + ':end]'
			start_pos = data_bytes.find(start.encode())
			data_bytes = data_bytes[start_pos + len(start):]
			end_pos = data_bytes.find(end.encode())
			data_bytes = data_bytes[:end_pos]
	if base_encoding == 'b64':
		data_bytes = base64.b64decode(data_bytes)
	if compressed == True and b'\x01LZMA' in data_bytes:
		data_bytes = data_bytes[5:]
		comp_len = int.from_bytes(data_bytes[:4], "big")
		data_bytes = data_bytes[9:]
		k2s = lzma.decompress(b''.join([b'\x5d\x00\x00\x80\x00',comp_len.to_bytes(8, "little"),data_bytes]))
		rx_dir_exists = path.isdir('RX')
		if rx_dir_exists == False: mkdir('RX')
		file_path = path.join('RX', file_name)
		with open(file_path, 'wb') as f:
			f.write(k2s)
			f.close()
		print('saved file to: ' + file_path)
		return k2s

def write_save_as(rx_file_name, save_path):
	global files
	if 'complete' in files[rx_file_name] and save_path != '()':
		k2s = files[rx_file_name]['complete']
		with open(save_path, 'wb') as f:
			f.write(k2s)
			f.close()
			print('Wrote ' + rx_file_name + ' to ' + save_path)

def check_file_complete(file_name, file_hash):
	blocks = {}
	if file_name not in files:
		return
	if file_hash not in files[file_name]['hash']:
		return
	if 'size' in files[file_name]['hash'][file_hash] and 'format' in files[file_name]['hash'][file_hash] and 'data' in files[file_name]:
		print('processing ' + file_name)
		size = files[file_name]['hash'][file_hash]['size']
		print('size block: ' + size)
		file_format = files[file_name]['hash'][file_hash]['format']
		print('file_format block: ' + file_format)
		if file_format[0] == '1':
			compressed = True
		else:
			compressed = False
		print('compressed: ' + str(compressed))
		data_format = size + ' ' + file_format
		blocks = files[file_name]['data'][data_format]
	elif 'size' in files[file_name]['hash'][file_hash] and 'format' in files[file_name]['hash'][file_hash] and 'data' in files[file_name]['hash'][file_hash]:
		blocks = files[file_name]['hash'][file_hash]['data']
	size_content = size.split(' ')
	num_blks = size_content[1]
	num_blks = int(num_blks)
	num_missing = num_blks
	print('received ' + str(len(blocks)) + ' out of ' + str(num_blks))
	if len(blocks) == num_blks:
		missing_blocks = []
		for blk in blocks:
			if blocks[blk] == b'':
				missing_blocks.append(blk)
		num_missing = len(missing_blocks)
		print('missing blocks: ' + str(num_missing))
	if num_missing == 0:
		file_data = b''
		for blk in blocks:
			file_data = b''.join([file_data, blocks[blk]])
		complete_msg = write_msg_to_file(file_data, file_name, compressed)
		if isinstance(complete_msg, bytes):
			files[file_name]['complete'] = complete_msg
				

def add_data_block(file_hash, block_num, block):
	print('Adding DATA block')
	print('file_hash: ' + file_hash)
	print('block_num: ' + str(block_num))
	print('block: ' + block.decode())
	hash_found = False
	block_num = int(block_num)
	for file_name in files:
		if file_hash in files[file_name]['hash']:
			if 'format' in files[file_name]['hash'][file_hash]:
				file_format = files[file_name]['hash'][file_hash]['format']
				if 'size' in files[file_name]['hash'][file_hash]:
					size = files[file_name]['hash'][file_hash]['size']
					data_format = size + ' ' + file_format
					if 'data' not in files[file_name]:
						files[file_name]['data'] = {}
					if data_format not in files[file_name]['data']:
						files[file_name]['data'][data_format] = {}
						num_blks = size.split(' ')
						num_blks = int(num_blks[1])
						for blk in range (1, num_blks + 1):
							files[file_name]['data'][data_format][blk] = b''
				files[file_name]['data'][data_format][block_num] = block
				check_file_complete(file_name, file_hash)
			else:
				if 'data' not in files[file_name]['hash'][file_hash]:
					files[file_name]['hash'][file_hash]['data'] = {}
				files[file_name]['hash'][file_hash]['data'][block_num] = block
				check_file_complete(file_name, file_hash)
			hash_found = True
			fileListUpdated = True
	if hash_found == False:
		if 'unknown' not in files:
			files['unknown'] = {}
		if 'hash' not in files['unknown']:
			files['unknown']['hash'] = {}
		if file_hash not in files['unknown']['hash']:
			files['unknown']['hash'][file_hash] = {}
		if 'data' not in files['unknown']['hash'][file_hash]:
			files['unknown']['hash'][file_hash]['data'] = {}
		files['unknown']['hash'][file_hash]['data'][block_num] = block

def remove_block_from_rx(rx_bytes, start_pos, end_pos):
	new_rx_bytes = b''.join([rx_bytes[:start_pos], rx_bytes[end_pos:]])
	return new_rx_bytes

def process_rx(rx_bytes):
	start_files = str(files)
	more_data = True
	while more_data == True:
		block = search_rx_for_block(rx_bytes)
		if block == None:
			more_data = False
		elif block == -1:
			more_data = False
		else:
			start_pos = block[0]
			print(start_pos)
			end_pos = block[1]
			print(end_pos)
			new_rx_bytes = remove_block_from_rx(rx_bytes, start_pos, end_pos)
			rx_bytes = new_rx_bytes
	if start_files != str(files):
		save_files(files)
		print('Saved updated blocks to file.')
		#for file_name in files:
		#	if 'hash' in files[file_name] and file_name != 'unknown':
		#		for file_hash in files[file_name]['hash']:
		#			if 'format' in files[file_name]['hash'][file_hash] and 'size' in files[file_name]['hash'][file_hash]:
		#				check_file_complete(file_name, file_hash)
	return rx_bytes

def search_missing_block_report(rx_bytes, file_hash, start_search=0):
	start_pos = rx_bytes.find('<MISSING '.encode(),start_search)
	if start_pos != -1:
		pos = start_pos + 9
		chunk = rx_bytes[pos:][:100]
		pos = chunk.find(' '.encode())
		line_len = int(chunk[:pos].decode())
		pos = pos + 1
		check = chunk[pos:][:4].decode()
		pos = chunk.find('{'.encode())
		block = chunk[pos:][:line_len]
		chunk = chunk[pos:][:line_len]
		if check == checksum(block):
			request_hash = chunk[1:][:4].decode()
			if request_hash == file_hash:
				request_blocks = chunk[6:].decode().split(' ')
				request_blocks.pop(request_blocks.index(''))
				blk_list = []
				for blk in request_blocks:
					blk_list.append(int(blk))
				end_pos = end_pos = rx_bytes.find(block, start_pos) + len(block)
				return [start_pos, end_pos, blk_list]
		else:
				return [start_pos, 'checksum_error']
	else:
		return -1

def fetch_missing_blocks(rx_bytes, file_hash):
	start_search = 0
	more_data = True
	while more_data == True:
		request_blocks = search_missing_block_report(rx_bytes, file_hash, start_search)
		if request_blocks == -1:
			more_data = False
		elif request_blocks[1] == 'checksum_error':
			start_search = request_blocks[0]+9
		else:
			start_pos = int(request_blocks[0])
			end_pos = int(request_blocks[1])
			for blk in request_blocks[2]:
				if blk not in requested_blocks:
					requested_blocks.append(blk)
			new_rx_bytes = remove_block_from_rx(rx_bytes, start_pos, end_pos)
			rx_bytes = new_rx_bytes
	return rx_bytes

def search_rx_for_block(rx_bytes, add_block=True):
	start_pos = -1
	for search_keyword in ['<PROG ','<ID ','<FILE ','<SIZE ','<DESC ','<DATA ', '<CNTL ']:
		start_pos = rx_bytes.find(search_keyword.encode())
		if start_pos != -1:
			pos = start_pos + 1
			chunk = rx_bytes[pos:][:256]
			pos = chunk.find(' '.encode())
			keyword = chunk[:pos].decode()
			chunk = chunk[pos + 1:]
			pos = chunk.find(' '.encode())
			line_len = chunk[:pos].decode()
			if line_len == '':
				start_pos = -1
				break
			if line_len.isdecimal():
				line_len = int(line_len)
			else:
				return [start_pos, start_pos + 3, 'checksum_error', '', '']
			chunk = chunk[pos + 1:]
			check = chunk[:4].decode()
			chunk = chunk[5:][:line_len]
			if len(chunk) != line_len:
				start_pos = -1
				break
			if checksum(chunk) == check:
				file_hash = chunk[1:][:4].decode()
				chunk = chunk[5:]
				if keyword == 'DATA':
					chunk = chunk[1:]
					pos = chunk.find('}'.encode())
					block_num = chunk[:pos].decode()
					block_num = int(block_num)
					chunk = chunk[pos:]
				block = chunk[1:]
				end_pos = rx_bytes.find(block, start_pos) + len(block)
				if keyword == 'DATA':
					if add_block == True:
						add_data_block(file_hash, block_num, block)
					return [start_pos, end_pos, keyword, file_hash, block_num, block]
				else:
					if add_block == True:
						add_proto_block(keyword, file_hash, block.decode())
					return [start_pos, end_pos, keyword, file_hash, block.decode()]
			else:
				#add_proto_block(start_pos, start_pos +3, 'checksum_error', '', '')
				return [start_pos, start_pos + 3, 'checksum_error', '', '']
	if start_pos == None:
		return -1
	elif start_pos == -1:
		return -1
	
def check_for_rx(rx_bytes):
	global fldigi
	new_rx_bytes = fldigi.text.get_rx_data()
	if new_rx_bytes != b'':
		if len(rx_bytes) + len(new_rx_bytes) > 4096:
			rx_len = 4096 - len(new_rx_bytes)
			rx_bytes = rx_bytes[-rx_len:]
		rx_bytes = b''.join([rx_bytes, new_rx_bytes])
		rx_bytes = process_rx(rx_bytes)
	return rx_bytes

def update_file_list(files_dict):
	global files
	files_dict = files
	fileList = []
	for file_name in files_dict:
		if 'hash' in files_dict[file_name]:
			for file_hash in files_dict[file_name]['hash']:
				percent_complete = ''
				if 'size' in files_dict[file_name]['hash'][file_hash]:
					size = files_dict[file_name]['hash'][file_hash]['size']
					num_blks = size.split(' ')
					num_blks = num_blks[1]
					if 'format' in files[file_name]['hash'][file_hash]:
						file_format = files[file_name]['hash'][file_hash]['format']
						data_format = size + ' ' + file_format
						missing_blocks = []
						if 'data' in files[file_name]:
							if data_format in files[file_name]['data']:
								for blk in files[file_name]['data'][data_format]:
									if files[file_name]['data'][data_format][blk] == b'':
										missing_blocks.append(blk)
								num_missing = len(missing_blocks)
								percent_complete = str(round((int(num_blks) - num_missing) / int(num_blks) * 100)) + '%'
								fileList.append(file_hash + ' ' + file_name + ' ' + percent_complete)
					else:

						fileList.append(file_hash + ' ' + file_name + ' waiting for preamble...')
				else:
					fileList.append(file_hash + ' waiting for preamble...')
	return fileList

fileList = []
fileList = update_file_list(files)

#define layout
layout1 = [[sg.Text('File', size=(10,1)),sg.Input('',key='rFile',readonly=True)],
           [sg.Text('Date Time', size=(10,1)),sg.Input('',key='rDateTime',readonly=True)],
           [sg.Text('Description', size=(10,1)),sg.Input('',key='rDesc',readonly=True)],
           [sg.Text('Call/Info', size=(10,1)),sg.Input('',key='rCallInfo',readonly=True)],
           [sg.Button('Save As',size=(8,1),key='rSave', disabled=True),sg.Button('Remove',size=(8,1),key='rRemove', disabled=True),sg.Button('Report',key='rReport', size=(8,1), disabled=True)],
           [sg.Text('Nbr Bytes', size=(8,1)),sg.Input('',key='rBytes',size=(8,1),readonly=True),sg.Text('Nbr Blks', size=(8,1)), sg.Input('',key='rBlocks',size=(8,1),readonly=True, use_readonly_for_disable=False), sg.Text('Blk Size', size=(7,1)), sg.Input('',key='rBlockSize',size=(8,1),readonly=True, use_readonly_for_disable=False)],
           [sg.Text('Missing', size=(10,1)), sg.Input('',key=('rMissing'),readonly=True)],
           [sg.Text('Data')],
           [sg.Multiline('', key='rData', size=(55,4), autoscroll=False, disabled=True)],
           [sg.Button('Relay',size=(8,1), key='rRelay', disabled=True),sg.Button('Fetch', size=(8,1), key='rFetch', disabled=True),sg.Input('',key='rRelayMissing', size=(30,1))],
           [sg.Text('Receive Queue')],
           [sg.Listbox(values=fileList, key='rFileList', size=(55, 5), enable_events=True,select_mode='LISTBOX_SELECT_MODE_SINGLE')]]
layout2=[[sg.Text('Send To', size=(10,1)),sg.Input('QST',key='tSendTo')],
           [sg.Text('File', size=(10,1)),sg.Input('',key='tFile')],
           [sg.Text('Description', size=(10,1)),sg.Input('',key='tDisc')],
           [sg.Text('Blk Size', size=(7,1)),sg.Input('64',key='tBlockSize',size=(4,1)),sg.Text('Xmt Rpt', size=(7,1)), sg.Input('1',key='tXmtRpt',size=(3,1)), sg.Text('Hdr Rpt', size=(7,1)), sg.Input('1',key='tHdrRpt',size=(3,1)), sg.Text('Nbr Blks',size=(7,1)), sg.Input('',key='tNbrBlocks',size=(4,1))],
           [sg.Checkbox('Compress', default=True),sg.Checkbox('Transmit Unproto', default=False),sg.Input('',key='tBytes',size=(20,1))],
           [sg.Text('Blocks', size=(10,1)),sg.Input('',key='tBlocks')],
           [sg.Button('Transmit',key='tXmit',size=(8,1)),sg.Button('Transmit All',key='tXmitAll',size=(8,1)),sg.Button('Remove',key='tRemove',size=(8,1)),sg.Button('Add',key='tAdd',size=(8,1))],
           [sg.Text('Transmit Queue')],
           [sg.Listbox(values=[], key='tFileList', size=(55, 10), enable_events=True)]]
layout3= [[sg.Text('Callsign', size=(10,1)),sg.Input(config['mycall'],key='cCallsign')],
           [sg.Text('Info', size=(10,1)),sg.Input(config['info'],key='cInfo')],
           [sg.Button('Save',key='cSave'),sg.Text('',key='cSaveText')]]

#Define Layout with Tabs         
tabgrp = [[sg.TabGroup([[sg.Tab('Receive', layout1, key='receive'), sg.Tab('Transmit', layout2, key='transmit'), sg.Tab('Config', layout3, key='config')]], key='tabs', enable_events=True)]]  
        
#Define Window
window = sg.Window(__version__,tabgrp, icon=pyamp_icon)

def update_rTabFromListBox(hash_file_name): 
	global window
	global files
	file_name = file_hash = date_time_string = desc = call_info = num_bytes = num_blocks = block_size = missing_blocks = missing_blocks_str = ''
	file_percent = '0'
	rRemoveDisabled = True
	if hash_file_name != '':
		rRemoveDisabled = False
		hash_file_name = hash_file_name.split(' ')
		file_hash = hash_file_name[0]
		file_name = hash_file_name[1]
		if len(hash_file_name) == 3:
			file_percent = hash_file_name[2]
		if file_name == 'waiting':
			file_name = 'unknown'
		if file_name in files:
			if 'date_time' in files[file_name]['hash'][file_hash]:
				date_time_string = files[file_name]['hash'][file_hash]['date_time']
			else:
				window['rDateTime'].update(value='unknown')
			if 'desc' in files[file_name]['hash'][file_hash]:
				desc = files[file_name]['hash'][file_hash]['desc']
			if 'id' in files[file_name]['hash'][file_hash]:
				call_info = files[file_name]['hash'][file_hash]['id']
			if 'size' in files[file_name]['hash'][file_hash]:
				size_str = files[file_name]['hash'][file_hash]['size']
				size = size_str.split(' ')
				num_bytes = size[0]
				num_blocks = size[1]
				block_size = size[2]
			if 'format' in files[file_name]['hash'][file_hash]:
				missing_blocks = []
				file_format = files[file_name]['hash'][file_hash]['format']
				data_format = size_str + ' ' + file_format
				if 'data' in files[file_name]:
					if data_format in files[file_name]['data']:
						for blk in files[file_name]['data'][data_format]:
							if files[file_name]['data'][data_format][blk] == b'':
								missing_blocks.append(blk)
				missing_blocks_str = ' '.join(map(str, missing_blocks))
	window['rFile'].update(value=file_name)
	window['rDateTime'].update(value=date_time_string)
	window['rDesc'].update(value=desc)
	window['rCallInfo'].update(value=call_info)
	if file_percent == '100%':
		window['rSave'].update(disabled=False)
	else:
		window['rSave'].update(disabled=True)
	window ['rRemove']. update (disabled=rRemoveDisabled)
	window['rBytes'].update(value=num_bytes)
	window['rBlocks'].update(value=num_blocks)
	window['rBlockSize'].update(value=block_size)
	window['rMissing'].update(value=missing_blocks_str)
	window['rData'].update(print_msg(file_name))

def print_msg(file_name):
	global files
	print_str = ''
	if file_name != '':
		if 'complete' in files[file_name]:
			print_bytes = files[file_name]['complete']
			print_str = print_bytes.decode('cp1252')
	return print_str

def onTimeout(rx_bytes):
	global files
	global fileList
	files_str = str(files)
	rx_bytes = check_for_rx(rx_bytes)
	rx_bytes = process_rx(rx_bytes)
	if files_str != str(files):
		fileList = update_file_list(files)
		window['rFileList'].update(values=fileList)
		update_file_list(fileList)
	return rx_bytes

#Read  values entered by user
while True:
	event,values=window.read(timeout=1000)
	if config_exists == False:
		window['config'].select()
		window['cSaveText'].update(value='Please enter Callsign and Info.')
	if event != '__TIMEOUT__':
		print('event:', event)
	#	print('values:', values)
	#access all the values and if selected add them to a string
	if event == 'rRemove':
		#if fileList != []
		remove_file = values['rFileList'][0].split(' ')
		remove_hash = remove_file[0]
		remove_file = remove_file[1]
		files[remove_file]['hash'].pop(remove_hash)
		if len(files[remove_file]['hash']) == 0:
			files.pop(remove_file)
		fileList = update_file_list(files)
		window['rFileList'].update(values=fileList)
		update_rTabFromListBox('')
		save_files(files)
	if event == '__TIMEOUT__':
		rxdata = onTimeout(rxdata)
		#rxdata = process_rx(rxdata)
		#fileList = update_file_list(files)
	if event == 'rSave':
		rSaveFilePath = sg.popup_get_file('', no_window=True, save_as=True, default_path=values['rFile'])
		write_save_as(values['rFile'], rSaveFilePath)
	if event == 'rFileList':
		if fileList != []:
			#print(values ['rFileList'])		
			rHashFileName = values['rFileList'][0]
			update_rTabFromListBox(values['rFileList'][0])
	if event == 'tabs' and values['tabs'] == 'Config':
		window['cCallsign'].update(value=config['mycall'])
		window['cInfo'].update(value=config['info'])
	if event == 'tabs' and values['tabs'] != 'Config':
		window['cSaveText'].update(value='')
	if event == 'cSave':
		if values['cCallsign'] != '':
			config['mycall'] = values['cCallsign']
			config['info'] = values['cInfo']
			save_config(config)
			config_exists = True
			window['cSaveText'].update(value='Configuration saved')
	if event == sg.WIN_CLOSED or event == 'Exit':
		break
window.close()
