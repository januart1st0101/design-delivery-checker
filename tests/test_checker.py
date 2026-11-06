import base64,copy,shutil,hashlib,importlib.util,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from make_fixtures import build,gltf,glb,png,put
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def rules(r):return {i['rule_id'] for i in r['issues']}
def hashes(p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and not f.is_symlink()}
class CheckerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=build(Path(self.tmp.name)/'fixtures')
 def scan(self,n='normal3d',**kw):return m.scan(self.root/n,**kw)
 def altered(self,change):
  d,b=gltf();change(d);r=self.root/'altered';put(r,'x.gltf',json.dumps(d));put(r,'triangle.bin',b);put(r,'貼圖.png',png());return m.scan(r)
 def test_normal_3d(self):
  r=self.scan();self.assertEqual(r['overview']['counts']['ERROR'],0);self.assertEqual(r['overview']['counts']['WARNING'],0)
  self.assertEqual([f['statistics']['decoded_positions'] for f in r['files'] if f['format']=='GLB'],[3,3])
 def test_missing_gltf_glb_obj(self):
  r=self.scan('missing');self.assertIn('REF_MISSING',rules(r));self.assertGreaterEqual(sum(i['rule_id']=='REF_MISSING' for i in r['issues']),3)
 def test_single_no_material_and_groups(self):
  r=self.scan('normal3d/no-material.obj');self.assertEqual(r['overview']['counts']['ERROR'],0);self.assertNotIn('OBJ_MATERIAL_UNRESOLVED',rules(r))
 def test_single_gltf(self):self.assertEqual(self.scan('normal3d/三角形.gltf')['overview']['counts']['ERROR'],0)
 def test_embedded_no_external_missing(self):self.assertNotIn('REF_MISSING',rules(self.scan('normal3d/embedded.glb')))
 def test_buffer_view_image(self):self.assertNotIn('REF_MISSING',rules(self.scan('normal3d/view-image.glb')))
 def test_external_data_buffer(self):
  d,b=gltf();d['buffers'][0]['uri']='data:application/octet-stream;base64,'+base64.b64encode(b).decode();put(self.root,'normal3d/data.gltf',json.dumps(d));self.assertEqual(self.scan('normal3d/data.gltf')['overview']['counts']['ERROR'],0)
 def test_image_case(self):
  (self.root/'normal3d/貼圖.png').rename(self.root/'normal3d/貼圖.PNG');self.assertIn('PATH_CASE',rules(self.scan()))
 def test_buffer_range(self):self.assertIn('VIEW_RANGE',rules(self.altered(lambda d:d['bufferViews'][0].update(byteLength=999))))
 def test_accessor_range(self):self.assertIn('ACCESSOR_RANGE',rules(self.altered(lambda d:d['accessors'][0].update(count=999))))
 def test_material_index(self):self.assertIn('GLTF_INDEX',rules(self.altered(lambda d:d['meshes'][0]['primitives'][0].update(material=8))))
 def test_texture_index(self):self.assertIn('GLTF_INDEX',rules(self.altered(lambda d:d['textures'][0].update(source=8))))
 def test_node_cycle(self):self.assertIn('NODE_CYCLE',rules(self.altered(lambda d:d['nodes'][1].update(children=[0]))))
 def test_duplicate_names_legal(self):
  r=self.altered(lambda d:d['nodes'][1].update(name='群組'));self.assertNotIn('ERROR',[i['severity'] for i in r['issues']])
 def test_out_of_range_geometry_index(self):
  f=self.root/'normal3d/triangle.bin';f.write_bytes(f.read_bytes()[:-2]+struct.pack('<H',9));self.assertIn('GEOMETRY_INDEX',rules(self.scan('normal3d/三角形.gltf')))
 def test_sparse_geometry_index(self):
  d,b=gltf();d['accessors'][1].pop('bufferView');d['accessors'][1]['sparse']={'count':1,'indices':{'bufferView':2,'componentType':5121},'values':{'bufferView':3}}
  d['bufferViews'] += [{'buffer':0,'byteOffset':42,'byteLength':1},{'buffer':0,'byteOffset':44,'byteLength':2}]
  b+=b'\x02\0'+struct.pack('<H',9);d['buffers'][0]['byteLength']=len(b)
  r=self.root/'sparse';put(r,'s.gltf',json.dumps(d));put(r,'triangle.bin',b);put(r,'貼圖.png',png());self.assertIn('GEOMETRY_INDEX',rules(m.scan(r)))
 def test_compression_not_claimed_decoded(self):
  r=self.altered(lambda d:d['meshes'][0]['primitives'][0].update(extensions={'KHR_draco_mesh_compression':{'bufferView':0,'attributes':{'POSITION':0}}}))
  self.assertIn('COMPRESSED_GEOMETRY',rules(r));self.assertEqual(next(f for f in r['files'] if f['format']=='glTF')['statistics']['decoded_positions'],0)
 def test_unsupported_version(self):self.assertIn('GLTF_VERSION',rules(self.altered(lambda d:d['asset'].update(version='1.0'))))
 def test_bad_glb(self):
  f=self.root/'bad.glb';f.write_bytes(b'glTF'+b'\0'*8);self.assertTrue(self.scan('bad.glb')['not_checked'] or self.scan('bad.glb')['overview']['counts']['ERROR'])
 def test_bad_json(self):
  put(self.root,'bad.gltf','{');self.assertIn('PARSE_INVALID',rules(self.scan('bad.gltf')))
 def test_obj_bad_index(self):
  put(self.root,'bad.obj','v 0 0 0\nf 1 2 3\n');self.assertIn('OBJ_INDEX',rules(self.scan('bad.obj')))
 def test_mtl_options_quoted_name(self):self.assertNotIn('REF_MISSING',rules(self.scan('normal3d/model.obj')))
 def test_mtl_unknown_option_not_false_missing(self):
  put(self.root,'x.mtl','newmtl x\nmap_Kd -unknown x y\n');r=self.scan('x.mtl');self.assertIn('MTL_OPTION',rules(r));self.assertNotIn('REF_MISSING',rules(r))
 def test_unity_normal_builtin(self):
  r=self.scan('unity-normal');self.assertEqual(r['overview']['counts']['ERROR'],0);self.assertIn('UNITY_BUILTIN',rules(r))
 def test_unity_missing_and_duplicate(self):
  rs=rules(self.scan('unity-issues'));self.assertTrue({'UNITY_DUP_GUID','UNITY_MATERIAL_GUID_MISSING','UNITY_SHADER_GUID_MISSING','UNITY_TEXTURE_GUID_MISSING','UNITY_META_MISSING'}<=rs)
 def test_package_unresolved_not_missing(self):
  put(self.root,'unity-issues/Packages/manifest.json','{"dependencies":{"com.example.unknown":"1.0.0"}}');r=self.scan('unity-issues');self.assertIn('UNITY_PACKAGE_GUID',rules(r));self.assertNotIn('UNITY_SHADER_GUID_MISSING',rules(r))
 def test_unity_single_without_index_not_false_missing(self):
  r=self.scan('unity-normal/Assets/Scene.unity');self.assertIn('UNITY_PACKAGE_GUID',rules(r));self.assertNotIn('UNITY_MATERIAL_GUID_MISSING',rules(r))
 def test_imported_fileid_not_checked(self):
  put(self.root,'unity-normal/Assets/Photo.png',png());put(self.root,'unity-normal/Assets/Photo.png.meta','guid: '+'2'*32+'\n')
  f=self.root/'unity-normal/Assets/Scene.unity';f.write_text(f.read_text()+'  m_Texture: {fileID: 2800000, guid: '+'2'*32+', type: 3}\n');self.assertIn('UNITY_IMPORTED_FILEID',rules(self.scan('unity-normal')))
 def test_local_fileid(self):
  f=self.root/'unity-normal/Assets/Scene.unity';f.write_text(f.read_text()+'  m_Local: {fileID: 999}\n');self.assertIn('UNITY_LOCAL_FILEID_MISSING',rules(self.scan('unity-normal')))
 def test_unity_binary(self):
  put(self.root,'unity-normal/Assets/Binary.unity',b'\0\x01unity');self.assertIn('UNITY_BINARY',rules(self.scan('unity-normal')))
 def test_separate_unity_projects_not_duplicate_guid(self):
  twins=self.root/'twins';shutil.copytree(self.root/'unity-normal',twins/'one');shutil.copytree(self.root/'unity-normal',twins/'two');self.assertNotIn('UNITY_DUP_GUID',rules(m.scan(twins)))
 def test_real_psd_psb_classification_only(self):
  r=self.scan('unverified');self.assertEqual(r['overview']['counts']['ERROR'],0);self.assertIn('NATIVE_PARSER_UNAVAILABLE',rules(r));self.assertIn('FONT_STATUS_UNKNOWN',rules(r));self.assertTrue(all('未支援' in f['coverage'] for f in r['files'] if f['format']=='PSD/PSB'))
 def test_mixed_batch(self):
  r=m.scan(self.root);self.assertTrue({'GLB','OBJ','Unity text','PSD/PSB'}<={f['format'] for f in r['files']})
 def test_readonly_hash(self):
  before=hashes(self.root);r=m.scan(self.root);self.assertEqual(hashes(self.root),before);self.assertTrue(all(x['unchanged'] for x in r['integrity']))
 def test_relative_report_schema(self):
  r=m.scan(self.root);self.assertNotIn(str(self.root),json.dumps(r));self.assertNotIn(str(self.root.parent),m.markdown(r))
  self.assertEqual(set(r['overview']['counts']),{'ERROR','WARNING','INFO','NOT_CHECKED'})
  for i in r['issues']:self.assertEqual(set(i),{'severity','rule_id','file','reference','evidence','impact','suggestion'})
 def test_escape_and_remote_no_read(self):
  r=self.altered(lambda d:d['images'][0].update(uri='../secret.png'));self.assertIn('PATH_ESCAPE',rules(r))
  r=self.altered(lambda d:d['images'][0].update(uri='https://user:secret@example.test/tex.png?token=secret'));self.assertIn('PATH_REMOTE',rules(r));self.assertNotIn('token=',json.dumps(r));self.assertNotIn('user:secret',json.dumps(r))
 def test_absolute_redaction(self):
  r=self.altered(lambda d:d['images'][0].update(uri='/private/person/tex.png'));self.assertIn('PATH_ABSOLUTE',rules(r));self.assertNotIn('/private/person',json.dumps(r))
 def test_symlink_outside(self):
  outside=Path(self.tmp.name)/'secret';outside.write_text('secret')
  link=self.root/'normal3d/貼圖.png';link.unlink();link.symlink_to(outside)
  r=self.scan('normal3d/三角形.gltf');self.assertIn('REF_BLOCKED',rules(r));self.assertFalse(any('secret' in str(x) for x in r['integrity']))
 def test_limits(self):
  self.assertIn('READ_LIMIT',rules(self.scan(max_bytes=20)))
  self.assertIn('SCAN_LIMIT',rules(self.scan(max_files=1)))
  self.assertIn('READ_LIMIT',rules(self.scan(total_bytes=20)))
 def test_large_accessor(self):self.assertIn('READ_LIMIT',rules(self.altered(lambda d:d['accessors'][0].update(count=1000001))))
 def test_cli_help(self):self.assertEqual(subprocess.run([sys.executable,str(ROOT/'scripts/check.py'),'--help'],capture_output=True).returncode,0)
 def test_cli_output_outside_and_no_overwrite(self):
  out=Path(self.tmp.name)/'report';cmd=[sys.executable,str(ROOT/'scripts/check.py'),str(self.root/'normal3d'),'--output',str(out)]
  self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
  self.assertEqual(subprocess.run(cmd[:-1]+[str(self.root/'normal3d/report')],capture_output=True).returncode,2)
 def test_magic_detection_without_suffix(self):
  source=self.root/'normal3d/embedded.glb';target=self.root/'normal3d/no-extension';target.write_bytes(source.read_bytes());r=self.scan('normal3d/no-extension');self.assertEqual(r['files'][0]['format'],'GLB')
 def test_unknown_single_format_not_passed(self):
  put(self.root,'unknown.dat','ordinary data');self.assertIn('FORMAT_UNSUPPORTED',rules(self.scan('unknown.dat')))
 def test_encoded_absolute_redaction(self):
  r=self.altered(lambda d:d['images'][0].update(uri='%2Fprivate%2Fperson%2Ftex.png'));self.assertIn('PATH_ABSOLUTE',rules(r));self.assertNotIn('person',json.dumps(r))
 def test_fifo_not_opened_as_regular_asset(self):
  if not hasattr(os,'mkfifo'):self.skipTest('POSIX-only')
  os.mkfifo(self.root/'pipe.obj');r=self.scan('pipe.obj');self.assertIn('HEADER_UNREADABLE',rules(r))
 def test_incomplete_meta_index_not_false_missing(self):
  r=self.scan('unity-normal',total_bytes=100);self.assertNotIn('UNITY_MATERIAL_GUID_MISSING',rules(r))
 def test_invalid_nested_gltf_keeps_report(self):
  for change in [lambda d:d.update(meshes=[{'primitives':[7]}]),lambda d:d.update(materials=[{'pbrMetallicRoughness':[]}])]:
   with self.subTest(change=change):self.assertIn('PARSE_INVALID',rules(self.altered(change)))
 def test_invalid_manifest_keeps_report(self):
  for value in ['[]','{"dependencies":[]}']:
   put(self.root,'unity-normal/Packages/manifest.json',value);self.assertIn('UNITY_MANIFEST_UNREADABLE',rules(self.scan('unity-normal')))
 def test_obj_folder_not_skipped(self):
  container=self.root/'delivery';shutil.copytree(self.root/'normal3d',container/'obj');r=m.scan(container);self.assertIn('OBJ',{f['format'] for f in r['files']})
 def test_unity_cache_only_at_project_root(self):
  put(self.root,'delivery/Library/file.obj','v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n');self.assertIn('OBJ',{f['format'] for f in self.scan('delivery')['files']})
 def test_matrix_column_padding(self):
  for size in (22,23):
   d={'asset':{'version':'2.0'},'buffers':[{'uri':'m.bin','byteLength':size}],'bufferViews':[{'buffer':0,'byteLength':size}],'accessors':[{'bufferView':0,'componentType':5121,'type':'MAT3','count':2}]}
   put(self.root,'matrix/m.gltf',json.dumps(d));put(self.root,'matrix/m.bin',bytes(size));r=self.scan('matrix')
   self.assertEqual('ACCESSOR_RANGE' in rules(r),size==22)
 def test_primitive_budget(self):
  self.assertIn('READ_LIMIT',rules(self.altered(lambda d:d['meshes'][0].update(primitives=d['meshes'][0]['primitives']*10001))))
 def test_markdown_not_active_images(self):
  r=self.altered(lambda d:d['images'][0].update(uri='![x](remote.png)'));self.assertIn('!\\[x\\]',m.markdown(r))
 def test_missing_geometry_not_counted_as_decoded_triangles(self):
  (self.root/'normal3d/triangle.bin').unlink();r=self.scan('normal3d/三角形.gltf');stats=next(f for f in r['files'] if f['format']=='glTF')['statistics'];self.assertEqual(stats['decoded_positions'],0);self.assertEqual(stats['triangles_uncompressed'],0)
 def test_total_decode_work_limit(self):
  d,b=gltf();count=700000;b=bytes(count*12)+struct.pack('<3H',0,1,2)
  d['buffers'][0]['byteLength']=len(b);d['bufferViews'][0]['byteLength']=count*12;d['bufferViews'][1]['byteOffset']=count*12;d['accessors'][0].update(count=count,max=[0,0,0])
  put(self.root,'decode/a.gltf',json.dumps(d));put(self.root,'decode/triangle.bin',b);put(self.root,'decode/貼圖.png',png());self.assertIn('READ_LIMIT',rules(self.scan('decode')))
 def test_invalid_index_accessor_not_counted(self):
  r=self.altered(lambda d:d['meshes'][0]['primitives'][0].update(indices=999));self.assertIn('GLTF_INDEX',rules(r));self.assertEqual(next(f for f in r['files'] if f['format']=='glTF')['statistics']['triangles_uncompressed'],0)
if __name__=='__main__':unittest.main(verbosity=2)
