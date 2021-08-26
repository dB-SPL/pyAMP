import PySimpleGUI as sg
import pickle
import pyfldigi
import crcmod
import base64
import lzma
from time import gmtime, strftime
from datetime import datetime
from os import __file__, getcwd
from os import path
from os import mkdir
from os import stat

fldigi = pyfldigi.client.Client()
rxdata = b''
requested_blocks = []

script_dir = getcwd()

fileListUpdated = False

def save_config(config_dict):
	with open('config','wb') as f:
		pickle.dump(config_dict,f)
		print('Saved configuration file.')
		fileListUpdated = True

def create_config():
	mycall = input("My Callsign:")
	info = ' ' + input("Additional info to display such as QTH or group name:")
	version = 'pyAMP 0.0.1 pre-alpha'
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
except FileNotFoundError:
	print('No config file found.  Starting config...')
	config = create_config()
	save_config(config)
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
		crc = str(hex(crc16(data.encode()))).upper()[-4:]
	
	if type(data) == bytes:
		crc = str(hex(crc16(data))).upper()[-4:]
	
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
					if 'data' in files[file_name]['hash'][file_hash]:
						if blk_num in files[file_name]['hash'][file_hash]['data']:
							files[file_name]['data'][data_format][blk_num] = files[file_name]['hash'][file_hash]['data'].pop(blk_num)
					elif blk_num in existing_data:
						files[file_name]['data'][data_format][blk_num] = existing_data[blk_num]
					else:
						files[file_name]['data'][data_format][blk_num] = b''
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
							if 'data' in files[file_name]['hash'][file_hash]:
								if blk_num in files[file_name]['hash'][file_hash]['data']:
									files[file_name]['data'][data_format][blk_num] = files[file_name]['hash'][file_hash]['data'].pop(blk_num)
							elif blk_num in existing_data:
								files[file_name]['data'][data_format][blk_num] = existing_data[blk_num]
							else:
								files[file_name]['data'][data_format][blk_num] = b''
		if hash_found == True: fileListUpdated = True
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

def check_file_complete(file_name, file_hash):
	blocks = {}
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
		write_msg_to_file(file_data, file_name, compressed)

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
			else:
				if 'data' not in files[file_name]['hash'][file_hash]:
					files[file_name]['hash'][file_hash]['data'] = {}
				files[file_name]['hash'][file_hash]['data'][block_num] = block
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
		for file_name in files:
			if 'hash' in files[file_name] and file_name != 'unknown':
				for file_hash in files[file_name]['hash']:
					if 'format' in files[file_name]['hash'][file_hash] and 'size' in files[file_name]['hash'][file_hash]:
						check_file_complete(file_name, file_hash)
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
			line_len = int(line_len)
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
	new_rx_bytes = fldigi.text.get_rx_data()
	if new_rx_bytes != b'':
		rx_bytes = b''.join([rx_bytes, new_rx_bytes])
		rx_bytes = process_rx(rx_bytes)
	return rx_bytes

def update_file_list(files_dict):
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
           [sg.Button('Save',size=(8,1)),sg.Button('Remove',size=(8,1),key='rRemove'),sg.Button('Report',size=(8,1))],
           [sg.Text('Nbr Bytes', size=(8,1)),sg.Input('',key='rBytes',size=(8,1),readonly=True),sg.Text('Nbr Blks', size=(8,1)), sg.Input('',key='rBlocks',size=(8,1),readonly=True, use_readonly_for_disable=False), sg.Text('Blk Size', size=(7,1)), sg.Input('',key='rBlockSize',size=(8,1),readonly=True, use_readonly_for_disable=False)],
           [sg.Text('Missing', size=(10,1)), sg.Input('',key=('rMissing'),readonly=True)],
           [sg.Text('Data')],
           [sg.Multiline('', key='rData', size=(55,4), autoscroll=False, disabled=True)],
           [sg.Button('Relay',size=(8,1)),sg.Button('Fetch', size=(8,1)),sg.Input('',key='rRelayMissing', size=(30,1))],
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
tabgrp = [[sg.TabGroup([[sg.Tab('Receive', layout1), sg.Tab('Transmit', layout2), sg.Tab('Config', layout3)]], key='tabs', enable_events=True)]]  
        
#Define Window
window =sg.Window(config['version'],tabgrp, icon="pyamp.png")

def update_rTabFromListBox(hash_file_name): 
	file_name = file_hash = date_time_string = desc = call_info = num_bytes = num_blocks = block_size = missing_blocks = ''
	if hash_file_name != '':
		hash_file_name = hash_file_name.split(' ')
		file_hash = hash_file_name[0]
		file_name = hash_file_name[1]
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
					if data_format in files[file_name]:
						for blk in files[file_name]['data'][data_format]:
							if files[file_name]['data'][data_format][blk] == b'':
								missing_blocks.append(blk)
				missing_blocks = str(missing_blocks)[1:][:-1]
	window['rFile'].update(value=file_name)
	window['rDateTime'].update(value=date_time_string)
	window['rDesc'].update(value=desc)
	window['rCallInfo'].update(value=call_info)
	window['rBytes'].update(value=num_bytes)
	window['rBlocks'].update(value=num_blocks)
	window['rBlockSize'].update(value=block_size)
	window['rMissing'].update(value=missing_blocks)
	window['rData'].update(print_msg(file_name))

def print_msg(file_name):
	print_str = ''
	rx_dir_exists = path.isdir('RX')
	if rx_dir_exists == True:
		file_path = path.join('RX', file_name)
		try: 
			with open(file_path, 'rb') as f:
				print_bytes = f.read()
				print_str = print_bytes.decode('cp1252')
		except: 
			pass
	return print_str

def onTimeout(rx_bytes):
	files_str = str(files)
	rxdata = process_rx(rx_bytes)
	if files_str != str(files):
		fileList = update_file_list(files)
		window['rFileList'].update(values)

#Read  values entered by user
while True:
	event,values=window.read(timeout=1000)
	if event != '__TIMEOUT__':
		print('event:', event)
	#	print('values:', values)
	#access all the values and if selected add them to a string
	if event == 'rRemove':
		#if fileList != []
		remove_file = values['rFileList'][0].split(' ')
		remove_file = remove_file[1]
		files.pop(remove_file)
		fileList = update_file_list(files)
		window['rFileList'].update(values)
		update_rTabFromListBox('')
		save_files(files)
	if event == '__TIMEOUT__':
		onTimeout (rxdata)
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
		config['mycall'] = values['cCallsign']
		config['info'] = values['cInfo']
		save_config(config)
		window['cSaveText'].update(value='Configuration saved')
	if event == sg.WIN_CLOSED or event == 'Exit':
		break
window.close()
