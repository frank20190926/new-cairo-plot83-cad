#!/usr/bin/env python3
"""Render the generated local boards and rebuild the complete review package.

Run after both drawing generators. Uses installed Chrome and Pillow; no service,
logged-in browser, network assets, or additional package installation is needed.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import subprocess
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'exports'
QA = ROOT / '99_临时' / 'orientation-qa'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
BOARDS = {
    'board1-claude': '01-Plot83-NewCairo-All-4-Floor-Plans-A01',
    'board2-claude': '02-Passive-Section-Core-Study-ZeroWaste-A02',
    'board1-codex': '03-Parametric-CAD-Floor-Plans-Set',
    'board2-codex': '04-Solar-Geometry-and-Core-Options',
}
AUDIT = r'''<script>
addEventListener('load',()=>{
  const board=document.querySelector('.board') || document.querySelector('.g') || document.querySelector('body');
  const errors=[];
  const bounds=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};
  for(const e of document.querySelectorAll('main,header,footer,section,.panel,.card,.notes,table')){
    const r=e.getBoundingClientRect();
    if(r.width && r.height && (r.left<-.5||r.top<-.5||r.right>1600.5||r.bottom>1200.5))
      errors.push({element:e.tagName,class:e.className,bounds:bounds(e)});
    if(e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2)
      errors.push({element:e.tagName,class:e.className,overflow:[e.scrollWidth,e.clientWidth,e.scrollHeight,e.clientHeight]});
  }
  document.documentElement.dataset.deliveryAudit=JSON.stringify({viewport:[innerWidth,innerHeight],board:bounds(board),errors,images:[...document.images].map(e=>({src:e.getAttribute('src'),loaded:e.complete&&e.naturalWidth>0}))});
});
</script>'''


def render():
    QA.mkdir(parents=True, exist_ok=True)
    final = ROOT / 'final_boards'
    final.mkdir(exist_ok=True)
    reports = []
    for name, alias in BOARDS.items():
        source = ROOT / (name + '.html')
        text = source.read_text()
        # Resolve local relative assets from the original HTML location.
        text = text.replace('<head>', '<head><base href="' + ROOT.as_uri() + '/">', 1)
        audit = QA / (name + '.html')
        audit.write_text(text.replace('</body>', AUDIT + '</body>'))
        shot = QA / (name + '.png')
        command = [CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
                   '--disable-extensions', '--disable-background-networking',
                   '--hide-scrollbars', '--user-data-dir=' + str(QA / 'chrome-profile'),
                   '--window-size=1600,1287', '--force-device-scale-factor=2',
                   '--virtual-time-budget=1500', '--screenshot=' + str(shot),
                   '--dump-dom', audit.as_uri()]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        match = re.search(r'data-delivery-audit="([^"]+)"', result.stdout)
        if not match:
            raise RuntimeError(name + ': browser audit missing: ' + result.stderr[-1000:])
        report = json.loads(html.unescape(match.group(1)))
        report['board_name'] = name
        assert report['board']['w'] == 1600 and report['board']['h'] == 1200, report
        assert report['viewport'][1] >= 1200, report
        assert not report['errors'], report
        assert all(i['loaded'] for i in report['images']), report
        im = Image.open(shot).convert('RGB').crop((0, 0, 3200, 2400))
        im.save(ROOT / (name + '.jpg'), quality=96, subsampling=0)
        shutil.copyfile(ROOT / (name + '.jpg'), final / (alias + '.jpg'))
        shutil.copyfile(ROOT / (name + '.jpg'), final / (name + '.jpg'))
        preview = im.copy()
        preview.thumbnail((1600, 1200))
        preview.save(QA / (name + '-preview.png'))
        reports.append(report)
        print(name + ': 3200 x 2400; container layout PASS', flush=True)
    (OUT / 'board_layout_check.json').write_text(json.dumps(reports, indent=2) + '\n')


def package():
    files = {'exports/' + f.name: f for f in OUT.iterdir() if f.is_file() and f.suffix != '.zip' and f.name != 'manifest.json'}
    for name in ['build_cad_2800443.py', 'build_claude_boards.py', 'render_delivery.py', 'verify_delivery.py',
                 'ENGINEERING_NOTES.md', 'index.html']:
        files[name] = ROOT / name
    for name in BOARDS:
        for ext in ['.html', '.jpg']:
            files[name + ext] = ROOT / (name + ext)
    for f in (ROOT / 'final_boards').glob('*.jpg'):
        files['final_boards/' + f.name] = f
    files['brief_assets/.png'] = ROOT / 'brief_assets/.png'
    manifest = {name: {'bytes': f.stat().st_size, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
                for name, f in sorted(files.items())}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    package_path = OUT / 'Plot83_NewCairo_CAD_Package.zip'
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, f in files.items():
            z.write(f, name)
        z.write(OUT / 'manifest.json', 'manifest.json')
    with zipfile.ZipFile(package_path) as z:
        assert z.testzip() is None
        for name, entry in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == entry['sha256']
    print(f'Package: {len(files) + 1} files; CRC and all hashes PASS', flush=True)


def audit_web():
    script = r'''<script>addEventListener('load',()=>{
      const tabs=[...document.querySelectorAll('[role=tab]')], results=[];
      for(const tab of tabs){tab.click();results.push(document.querySelectorAll('[role=tabpanel]:not([hidden])').length===1 && !document.getElementById(tab.getAttribute('aria-controls')).hidden);}
      tabs[0].click();tabs[0].dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
      const keyboard=tabs[1].getAttribute('aria-selected')==='true';tabs[0].click();
      const zoom=document.getElementById('zoom');zoom.value=150;zoom.dispatchEvent(new Event('input'));
      const zoomWorks=[...document.querySelectorAll('.plan-canvas .vector')].every(e=>e.style.width==='150%'&&e.style.height==='150%');
      zoom.value=100;zoom.dispatchEvent(new Event('input'));
      const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
      document.documentElement.dataset.webAudit=JSON.stringify({viewport:[innerWidth,innerHeight],documentWidth:document.documentElement.scrollWidth,tabs:results,keyboard,zoom:zoomWorks,duplicateIds:ids.length-new Set(ids).size});
    });</script>'''
    text = (ROOT / 'index.html').read_text().replace('<head>', '<head><base href="' + ROOT.as_uri() + '/">', 1)
    path = QA / 'web-audit.html'
    path.write_text(text.replace('</body>', script + '</body>'))
    reports=[]
    for width in [1440, 500]:
        result=subprocess.run([CHROME,'--headless=new','--no-first-run','--disable-extensions',
            '--disable-background-networking','--hide-scrollbars','--user-data-dir='+str(QA/'chrome-profile'),
            f'--window-size={width},1087','--force-device-scale-factor=1','--virtual-time-budget=1200',
            '--screenshot='+str(QA/f'web-{width}.png'),'--dump-dom',path.as_uri()],capture_output=True,text=True,timeout=60)
        match=re.search(r'data-web-audit="([^"]+)"',result.stdout)
        assert match,'Missing web audit'
        report=json.loads(html.unescape(match.group(1)))
        assert report['viewport'][0]==width,report
        assert len(report['tabs'])==4 and all(report['tabs']),report
        assert report['keyboard'] and report['zoom'] and report['duplicateIds']==0,report
        assert report['documentWidth']==report['viewport'][0],report
        reports.append(report)
    (OUT/'web_validation.json').write_text(json.dumps(reports,indent=2)+'\n')
    print('Web: four tabs, keyboard, zoom, unique SVG IDs and responsive width PASS',flush=True)


if __name__ == '__main__':
    render()
    audit_web()
    package()
