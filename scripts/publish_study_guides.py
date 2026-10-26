"""发布已在本地完成 Schema 校验的原创辅导课程；不修改 APK 版本。"""
import os,json,base64,hashlib,zipfile,io,urllib.request,urllib.error
from pathlib import Path
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GITHUB_TOKEN']
api='https://api.github.com/repos/'+repo
tag='study-guides-2026-10-26'
root=Path('incoming/study-guides')
manifest=json.loads((root/'ready.json').read_text())
encoded=''.join((root/f'part-{i:02}.txt').read_text().strip() for i in range(manifest['parts']))
raw=base64.b64decode(encoded,validate=True)
assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
assets={}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert z.testzip() is None and set(z.namelist())==set(manifest['assets'])
    for name,digest in manifest['assets'].items():
        assert '/' not in name and '\\' not in name
        data=z.read(name);assert hashlib.sha256(data).hexdigest()==digest
        assets[name]=data
for cid,v in [('mathematical_statistics',2),('engineering_fatigue_fracture',3)]:
    with zipfile.ZipFile(io.BytesIO(assets[f'{cid}-v{v}.zip'])) as z:
        assert set(z.namelist())=={n+'.json' for n in ['course','chapters','knowledge','formulas','questions','glossary']}
        assert json.loads(z.read('course.json'))['courseId']==cid
def request(url,payload=None,method=None,ctype='application/json'):
    data=None if payload is None else payload if isinstance(payload,bytes) else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,method=method or ('GET' if data is None else 'POST'),
       headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'kexi-study-publisher'})
    with urllib.request.urlopen(req,timeout=90) as r:
        text=r.read();return json.loads(text) if text else None
body="""两门课程改为可顺序学习的辅导讲解，保留章节、courseId及原知识点ID。
- 数理统计 v2：95个主题，107条公式，152题（新增95道带解答自测）。
- 工程疲劳与断裂 v3：132个主题，106条公式，206题（新增132道带解答自测）。
- 每个主题补解释、推导或算例、条件与自测；约4.54万/5.59万正文字符（含数学标记，排除图片数据）。
- 附件提供原Schema ZIP、独立Markdown辅导书、来源与导入说明、内容校验报告。
在课习0.4.0及以上的云端课程刷新并更新；也可下载ZIP经课程管理导入。本次无需重装APK。
Schema、ID和引用已校验；新增讲解尚未经外部教师逐条审定，手机端本次未做真机排版验收。
"""
try:release=request(api+'/releases/tags/'+tag)
except urllib.error.HTTPError as e:
    if e.code!=404:raise
    release=request(api+'/releases',dict(tag_name=tag,target_commitish='main',name='课习 · 两门从零学习辅导课程',body=body,draft=True,prerelease=False,make_latest='false'))
existing={a['name']:a for a in release['assets']}
upload=release['upload_url'].split('{')[0]
from urllib.parse import quote
for name,data in assets.items():
    if name in existing:
        assert existing[name]['size']==len(data),'已存在的同名附件尺寸不符，停止避免覆盖'
        assert existing[name].get('digest')=='sha256:'+manifest['assets'][name],'同名附件摘要不符'
        continue
    result=request(upload+'?name='+quote(name),data,ctype='application/octet-stream')
    assert result['size']==len(data)
if release['draft']:
    release=request(api+'/releases/'+str(release['id']),dict(draft=False,make_latest='false'),method='PATCH')
print('已发布',release['html_url'])
