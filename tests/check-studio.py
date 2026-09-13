#!/usr/bin/env python3
"""Integration check of the real control plane, streams, and live cutoff."""
from pathlib import Path
import base64
import json
import math
import os
import socket
import struct
import time
import urllib.request
import urllib.error
import urllib.parse
import sys

root=Path(__file__).resolve().parents[1]
(root/'.work').mkdir(exist_ok=True)
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:18080'
document_path=Path(sys.argv[2]) if len(sys.argv)>2 else root/'examples/studio/reference.gr4s'
def api(path,body=None,method=None):
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,
                               headers={'Content-Type':'application/json'},method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            data=response.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'{req.get_method()} {path}: HTTP {error.code}: {error.read().decode()}') from error

class WebSocketSnapshots:
    def __init__(self,path):
        target=urllib.parse.urlsplit(path if '://' in path else base+path)
        host=target.hostname or '127.0.0.1'
        port=target.port or (443 if target.scheme in ('https','wss') else 80)
        request_path=target.path or '/'
        if target.query: request_path+='?'+target.query
        key=base64.b64encode(os.urandom(16)).decode()
        self.connection=socket.create_connection((host,port),timeout=10)
        request=(f'GET {request_path} HTTP/1.1\r\nHost: {host}:{port}\r\n'
                 'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                 f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
        self.connection.sendall(request.encode())
        self.stream=self.connection.makefile('rb')
        status=self.stream.readline().decode().strip()
        assert ' 101 ' in status,status
        while self.stream.readline() not in (b'\r\n',b'\n',b''):
            pass

    def read(self):
        message=bytearray()
        binary=False
        while True:
            header=self.stream.read(2)
            assert len(header)==2,'websocket closed before a snapshot arrived'
            opcode=header[0]&0x0f
            final=bool(header[0]&0x80)
            length=header[1]&0x7f
            masked=bool(header[1]&0x80)
            if length==126: length=int.from_bytes(self.stream.read(2),'big')
            elif length==127: length=int.from_bytes(self.stream.read(8),'big')
            mask=self.stream.read(4) if masked else b''
            payload=self.stream.read(length)
            assert len(payload)==length,'truncated websocket frame'
            if masked: payload=bytes(value^mask[index%4] for index,value in enumerate(payload))
            if opcode in (0,1,2):
                if opcode in (1,2): binary=opcode==2
                message.extend(payload)
                if final:
                    if not binary: return json.loads(message)
                    # StudioPowerSpectrumSink uses this binary WebSocket
                    # header; its HTTP snapshots use dataset JSON instead.
                    assert len(message)>=44,'truncated spectrum header'
                    magic,version,flags,bins,center,span,sequence,timestamp=struct.unpack_from('<IHHIddQd',message)
                    assert (magic,version,flags)==(0x53505753,1,0),'unknown spectrum format'
                    assert len(message)==44+4*bins,'truncated spectrum data'
                    return {'bins':bins,'center_hz':center,'span_hz':span,
                            'sequence':sequence,'timestamp':timestamp,
                            'power':list(struct.unpack_from(f'<{bins}f',message,44))}
            if opcode==9: self.send_control(10,payload)
            if opcode==8: raise RuntimeError('websocket closed before a snapshot arrived')

    def send_control(self,opcode,payload):
        mask=os.urandom(4)
        masked=bytes(value^mask[index%4] for index,value in enumerate(payload))
        self.connection.sendall(bytes((0x80|opcode,0x80|len(payload)))+mask+masked)

    def close(self):
        try: self.send_control(8,(1000).to_bytes(2,'big'))
        except OSError: pass
        try: self.connection.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        self.stream.close()
        self.connection.close()

doc=json.loads(document_path.read_text())
output_window_size=int(next(node for node in doc['graph']['nodes'] if node['id']=='Output')['parameters']['window_size']['value'])
catalog=api('/blocks')
ids={b['id'] for b in catalog}
catalog_by_id={b['id']:b for b in catalog}
def parameter_value(node,key,value):
    # .gr4s editor literals may be strings. The runtime YAML needs numbers
    # for numeric settings, just as Studio's catalog-aware exporter emits.
    metadata=next((p for p in catalog_by_id[node['blockType']]['parameters'] if p['name']==key),{})
    kind=metadata.get('type','').lower()
    if key=='ui_constraints' and isinstance(value,str):
        value=json.loads(value) if value.strip() else {}
    elif kind in ('float','double','float32','float64'):
        value=float(value)
    elif kind in ('int','uint','int8','uint8','int16','uint16','int32','uint32','int64','uint64','size_t'):
        value=int(value)
    return json.dumps(value)
lines=['metadata:', '  name: workshop-verified', 'blocks:']
for node in doc['graph']['nodes']:
    assert node['blockType'] in ids,node['blockType']
    # Match Studio's exporter: the runtime instance name is the node ID, not
    # the default reflected class name stored in the editor's parameters.
    params={k:v['value'] for k,v in node['parameters'].items() if k!='name'}
    if node['blockType'].startswith('gr::studio::'):
        params.pop('endpoint',None) # Managed stream routes come from the session.
    if node['id']=='File': params['file_name']=str(root/'assets/demo-data/two-tone.f32')
    if 'StudioSeriesSink' in node['blockType']: params['payload_format']='series-window-json-v1'
    if 'StudioPowerSpectrumSink' in node['blockType']: params['payload_format']='dataset-xy-json-v1'
    lines+=['  - id: '+json.dumps(node['blockType']),'    parameters:','      name: '+node['id']]
    lines+=['      '+k+': '+parameter_value(node,k,v) for k,v in params.items()]
lines+=['connections:']
for edge in doc['graph']['edges']:
    a,b=edge['source'],edge['target']
    lines+=['  - '+json.dumps([a['nodeId'],a['portId'],b['nodeId'],b['portId']])]
grc='\n'.join(lines)+'\n'
(root/'.work/reference.grc').write_text(grc)
create_request={'name':'intro-workshop-check','grc':grc}
if doc['metadata'].get('schedulerId'): create_request['scheduler_id']=doc['metadata']['schedulerId']
session=api('/sessions',create_request)
print('Created',session,flush=True)
sid=session['id']
websocket_streams={}
try:
    result=api(f'/sessions/{sid}/start',{})
    print('Started',result,flush=True)
    assert result['state']=='running',result
    time.sleep(1)
    state=api(f'/sessions/{sid}')
    assert len(state['streams'])==4,state['streams']
    for stream in state['streams']:
        if stream['transport']=='websocket':
            websocket_streams[stream['id']]=WebSocketSnapshots(stream['path'])
            snapshot=websocket_streams[stream['id']].read()
        else:
            snapshot=api(stream['path'])
        (root/f'.work/snapshot-{stream["id"]}.json').write_text(json.dumps(snapshot,indent=2))
        print('Snapshot',stream['id'],str(snapshot)[:400],flush=True)
        if 'bins' in snapshot:
            assert snapshot['bins'] in (512,513),snapshot['bins']
            assert 4000<snapshot['span_hz']<=4096,snapshot['span_hz']
            assert all(math.isfinite(value) for value in snapshot['power'])
    # Runtime unique names are reflected in session block descriptors/settings errors if needed.
    print('Settings',api(f'/sessions/{sid}/blocks/Lowpass/settings'),flush=True)
    print('Live cutoff',api(f'/sessions/{sid}/blocks/Lowpass/settings',{'f_low':3072.0}),flush=True)
    time.sleep(.5)
    effective=api(f'/sessions/{sid}/blocks/Lowpass/settings')['settings']['f_low']
    assert effective==3072.0,effective
    output_stream=next(s for s in state['streams'] if s['id']=='Output')
    before=json.loads((root/'.work/snapshot-Output.json').read_text())
    def tone(snapshot):
        values=snapshot['data'][0]
        assert len(values)==output_window_size and all(math.isfinite(value) for value in values)
        real=sum(value*math.cos(2*math.pi*2048*n/8192) for n,value in enumerate(values))
        imag=sum(value*math.sin(2*math.pi*2048*n/8192) for n,value in enumerate(values))
        return 2/len(values)*math.hypot(real,imag)
    if output_stream['transport']=='websocket':
        for _ in range(30):
            after=websocket_streams[output_stream['id']].read()
            if tone(after)>0.25: break
    else:
        after=api(output_stream['path'])
    assert tone(before)<0.02,(tone(before),tone(after))
    assert tone(after)>0.25,(tone(before),tone(after))
    print('PASS: Studio live cutoff=3072; 2048 Hz amplitude',tone(before),'->',tone(after),flush=True)
finally:
    for websocket_stream in websocket_streams.values(): websocket_stream.close()
    api(f'/sessions/{sid}',method='DELETE')
