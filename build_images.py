import json, pathlib, io, hashlib, concurrent.futures
import requests
from PIL import Image, ImageOps
root=pathlib.Path("public")
root.mkdir(exist_ok=True)
out=root/"images"
out.mkdir(exist_ok=True)
data=json.loads(pathlib.Path("spirits.json").read_text(encoding="utf-8"))
spirits=[s for m in data for s in m["spirits"]]
def fetch(s):
    if not s["image"]: return str(s["id"]), {"error":"No verified reference"}
    url=s["image"]
    try:
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://wiki.biligame.com/sky/" if s["source"]=="BWiki" else "https://www.18183.com/"},timeout=25)
        r.raise_for_status()
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert("RGB")
        if min(im.size)<100: raise ValueError("Image too small")
        im.thumbnail((1400,1000))
        path=out/f'{s["id"]}.webp'
        im.save(path,"WEBP",quality=84,method=4)
        return str(s["id"]),{"path":f'images/{s["id"]}.webp',"source":s["source"],"sha256":hashlib.sha256(r.content).hexdigest(),"bytes":path.stat().st_size}
    except Exception as e:
        return str(s["id"]),{"error":str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    result=dict(pool.map(fetch,spirits))
(out/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
for filename in ("index.html","spirits.json"):
    (root/filename).write_bytes(pathlib.Path(filename).read_bytes())
print("Images downloaded:",sum("path" in v for v in result.values()),"/",len(result))
for k,v in result.items():
    if "error" in v: print(k,v["error"])
