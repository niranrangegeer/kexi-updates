"""从已发布的GitHub Releases生成目录，运行于GitHub Actions。"""
import os,json,re,hashlib,base64,urllib.request,zipfile,io
repo=os.environ['GITHUB_REPOSITORY']
token=os.environ['GITHUB_TOKEN']
api='https://api.github.com/repos/'+repo
def request(path,payload=None):
    raw=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(api+path,data=raw,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'kexi-catalog'},method='GET' if raw is None else 'PUT')
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def download(asset,limit):
    assert 0<asset['size']<=limit,'附件大小非法'
    url=asset['browser_download_url']
    assert url.startswith('https://github.com/'+repo+'/releases/download/')
    with urllib.request.urlopen(url,timeout=90) as r:data=r.read(limit+1)
    assert len(data)==asset['size']<=limit
    return data
releases=[]
for page in range(1,11):
    batch=request('/releases?per_page=100&page='+str(page))
    releases.extend(r for r in batch if not r['draft'] and not r['prerelease'])
    if len(batch)<100:break
courses={};app=None
for release in releases:
    assets=release['assets']
    for a in assets:
        m=re.fullmatch(r'([A-Za-z0-9_-]+)-v([1-9][0-9]*)\.zip',a['name'])
        if not m:continue
        cid,version=m[1],int(m[2])
        if cid in courses and courses[cid]['version']>=version:continue
        data=download(a,30*1024*1024)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert sum(x.file_size for x in z.infolist())<=30*1024*1024
            assert all(not x.filename.startswith('/') and '..' not in x.filename and '\\' not in x.filename for x in z.infolist())
            manifest=json.loads(z.read('course.json'))
            assert manifest['courseId']==cid
            for key in ['chaptersFile','knowledgeFile','formulasFile','questionsFile']:
                assert re.fullmatch(r'[A-Za-z0-9_-]+\.json',manifest[key])
                assert isinstance(json.loads(z.read(manifest[key])),list)
        courses[cid]=dict(courseId=cid,name=manifest['courseName'],version=version,url=a['browser_download_url'],
            sha256=hashlib.sha256(data).hexdigest(),size=len(data),description=manifest['description'])
    meta=next((a for a in assets if a['name']=='app-release.json'),None)
    if meta:
        desc=json.loads(download(meta,65536))
        version=int(desc['versionCode'])
        if app is not None and app['versionCode']>=version:continue
        apk=next(a for a in assets if a['name']==desc['file'])
        assert apk['name'].endswith('.apk')
        data=download(apk,150*1024*1024)
        app=dict(versionCode=version,versionName=desc['versionName'],url=apk['browser_download_url'],
            sha256=hashlib.sha256(data).hexdigest(),size=len(data),notes=desc.get('notes',''))
catalog=dict(courses=sorted(courses.values(),key=lambda c:c['courseId']),app=app)
try:old=request('/contents/catalog.json?ref=main')
except urllib.error.HTTPError as e:
    if e.code!=404:raise
    old=None
raw=(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n').encode()
if old and base64.b64decode(old['content'])==raw:
    print('目录无需更新')
else:
    body=dict(message='更新课程与APK版本目录',branch='main',content=base64.b64encode(raw).decode())
    if old:body['sha']=old['sha']
    request('/contents/catalog.json',body)
    print('目录已更新：',len(courses),'门课程')
