"""GameRadar: fontes de jogos físicos autorizadas, sem scraping (Python stdlib)."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import html, json, os, re, sys, ipaddress
from pathlib import Path
from urllib.parse import urlsplit, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
AGENT = "GameRadar/1.0 (feeds autorizados)"
P = ("switch2","switch","ps5","ps4","ps3","ps2","ps_vita","psp","xbox_series","xbox_one","xbox360","3ds","ds","wiiu","wii","gamecube","gba","gbc","n64","snes","nes","mega_drive")
NS = {"a":"http://www.w3.org/2005/Atom", "g":"http://base.google.com/ns/1.0"}
EXCLUDE = re.compile(r"\b(?:m[ií]dia\s*digital|digital|jogo\s*digital|c[oó]digo\s*digital|conta\s*(?:prim[aá]ria|secund[aá]ria)|gift\s*card|giftcard|dlc\b|season\s+pass|controle\b|joystick|carregador|capinha|pel[ií]cula|skin\b|adesivo|caixa\s*vazia|capa\s*avulsa|headset|acess[oó]rio|console\s*(?:nintendo|ps[45]|playstation|xbox))\b", re.I)

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def read(path, default):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError: return default
def write(path, obj):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); tmp.replace(path)
def valid_url(value):
    try:
        p=urlsplit(str(value))
        if p.scheme!="https" or not p.hostname or p.username or p.password or p.hostname=="localhost" or p.hostname.endswith(".local"): return False
        try:
            if not ipaddress.ip_address(p.hostname).is_global: return False
        except ValueError: pass
        return True
    except ValueError: return False
class Redirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not valid_url(newurl) or urlsplit(newurl).hostname!=urlsplit(req.full_url).hostname: raise ValueError("Redirecionamento inseguro")
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url, token=None):
    if not valid_url(url): raise ValueError("Fonte exige HTTPS público")
    headers={"User-Agent":AGENT,"Accept":"application/json, application/xml, application/rss+xml"}
    if token: headers["Authorization"]="Bearer "+token
    with build_opener(Redirect).open(Request(url,headers=headers),timeout=22) as resp:
        data=resp.read(4*1024*1024+1)
        if len(data)>4*1024*1024: raise ValueError("Feed excede 4MB")
        return data
def clean(value): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(value or "")))).strip()
def money(value):
    if isinstance(value,bool) or value is None: return None
    if isinstance(value,(float,int)): return round(float(value),2) if 0<float(value)<1e8 else None
    m=re.search(r"\d[\d.,]*",str(value))
    if not m: return None
    s=m.group().rstrip(".,")
    if "," in s and "." in s: s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    elif "," in s: s=s.replace(".","").replace(",",".")
    elif s.count(".")>1 or ("." in s and len(s.split(".")[-1])==3): s=s.replace(".","")
    try: return round(float(s),2) if 0<float(s)<1e8 else None
    except ValueError: return None
def platform(title,hint=None):
    pats=(("switch2",r"\b(?:nintendo\s*)?switch\s*2\b|\bns2\b"),("switch",r"\b(?:nintendo\s*)?switch\b"),("ps5",r"\b(?:ps\s*5|playstation\s*5)\b"),("ps4",r"\b(?:ps\s*4|playstation\s*4)\b"),("xbox_series",r"\bxbox\s*(?:series\s*[xs]|sx)\b"),("xbox_one",r"\bxbox\s*one\b"),("xbox360",r"\bxbox\s*360\b"),
          ("ps3",r"\b(?:ps\s*3|playstation\s*3)\b"),("ps2",r"\b(?:ps\s*2|playstation\s*2)\b"),
          ("ps_vita",r"\b(?:ps\s*vita|playstation\s*vita|psvita)\b"),
          ("psp",r"\bpsp\b"),
          ("3ds",r"\b(?:nintendo\s*)?3ds\b"),("ds",r"\bnintendo\s*ds\b"),
          ("wiiu",r"\bwii\s*u\b"),("wii",r"\bwii\b"),
          ("gamecube",r"\b(?:game\s*cube|gamecube)\b"),
          ("gba",r"\b(?:game\s*boy\s*advance|gba)\b"),
          ("gbc",r"\b(?:game\s*boy\s*color|gbc)\b"),
          ("n64",r"\b(?:nintendo\s*64|n64)\b"),("snes",r"\b(?:super\s*nintendo|snes)\b"),
          ("nes",r"\b(?:nintendo\s*entertainment\s*system|nes)\b"),
          ("mega_drive",r"\b(?:mega\s*drive|genesis)\b"))
    return next((k for k,regex in pats if re.search(regex,title,re.I)), hint if hint in P else None)
def condition(raw,title,hint=None):
    v=str(raw or "").lower()
    if v in ("used","usado","seminovo","semi-novo") or re.search(r"\b(usado|seminovo|semi-novo)\b",title,re.I): return "used"
    if v in ("new","novo","lacrado") or re.search(r"\b(novo|lacrado|selado)\b",title,re.I): return "new"
    return hint if hint in ("new","used") else "unknown"
def normalize(source,raw):
    title=clean(raw.get("title"))[:220]
    if not title or EXCLUDE.search(title): return None
    amount=money(raw.get("price")); url=str(raw.get("url") or "").strip()
    plat=platform(title,source.get("platform_hint"))
    if amount is None or plat is None or not valid_url(url) or str(raw.get("currency") or source.get("currency") or "BRL").upper()!="BRL": return None
    image=raw.get("image") if valid_url(raw.get("image") or "") else None
    return {"id":str(source["id"])+":"+str(raw.get("id") or url)[:300], "title":title,
            "platform":plat,"condition":condition(raw.get("condition"),title,source.get("condition_hint")),
            "price":amount,"shipping":money(raw.get("shipping")) if raw.get("shipping") is not None else None,
            "url":url,"image":image,"currency":"BRL","location":clean(raw.get("location"))[:100] or None,
            "source":source.get("name",source["id"]),"source_id":source["id"]}
def xt(e,path):
    item=e.find(path,NS)
    return (item.text or "").strip() if item is not None else ""
def xml_records(data):
    root=ET.fromstring(data)
    entries=root.findall(".//item") or root.findall(".//a:entry",NS)
    result=[]
    for e in entries:
        atom=e.tag.endswith("entry"); url=xt(e,"link")
        if atom:
            link=next((x for x in e.findall("a:link",NS) if x.get("rel","alternate")=="alternate"),None)
            if link is not None: url=link.get("href","")
        amount=xt(e,"g:sale_price") or xt(e,"g:price") or xt(e,"price")
        if not amount:
            match=re.search(r"R\$\s*[\d.,]+",clean(xt(e,"description") or xt(e,"a:summary")))
            amount=match.group() if match else ""
        result.append({"id":xt(e,"a:id" if atom else "guid") or url,"title":xt(e,"a:title" if atom else "title"),
                       "url":url,"price":amount,"image":xt(e,"g:image_link"),"condition":xt(e,"g:condition")})
    return result
def feed(source,offline=None):
    key=source.get("token_env")
    if key and not re.fullmatch(r"[A-Z_][A-Z0-9_]{2,79}",key): raise ValueError("token_env inválido")
    token=os.environ.get(key,"") if key else None
    if key and not token and offline is None: raise ValueError("Secret de fonte ausente")
    data=offline if offline is not None else fetch(source["url"],token)
    fmt=source.get("format","json")
    if fmt in ("rss","atom"): records=xml_records(data)
    elif fmt=="json":
        raw=json.loads(data);records=raw.get("items") if isinstance(raw,dict) else raw
    else: raise ValueError("Formato não suportado")
    if not isinstance(records,list): raise ValueError("Fonte precisa entregar items[]")
    return [o for r in records[:1500] if isinstance(r,dict) if (o:=normalize(source,r))]
def ml_seller(seller,token):
    if not token: raise ValueError("ML_ACCESS_TOKEN não configurado")
    seller=int(seller); src={"id":"ml-"+str(seller),"name":"Mercado Livre"}
    ids=[]
    for off in range(0,500,50):
        data=json.loads(fetch(f"https://api.mercadolibre.com/users/{seller}/items/search?status=active&limit=50&offset={off}",token))
        batch=data.get("results",[]);ids.extend(str(i) for i in batch)
        if len(batch)<50: break
    out=[]
    for off in range(0,len(ids),20):
        obj=json.loads(fetch("https://api.mercadolibre.com/items/bulk?ids="+quote(",".join(ids[off:off+20]),safe=","),token))
        for item in obj:
            body=item.get("body") or {}
            if int(item.get("code",item.get("status_code",0)))!=200 or body.get("status")!="active": continue
            image=(body.get("pictures") or [{}])[0].get("secure_url") or body.get("thumbnail")
            offer=normalize(src,{"id":body.get("id"),"title":body.get("title"),"url":body.get("permalink"),
                                 "price":body.get("price"),"condition":body.get("condition"),"image":image})
            if offer: out.append(offer)
    return out
def ml_items(ids,token):
    """Consulta itens específicos na API oficial do Mercado Livre, mediante token válido.
    Não é busca geral do marketplace; serve para seguir URLs/IDs conhecidos.
    """
    if not token: raise ValueError("ML_ACCESS_TOKEN não configurado")
    valid=[]
    for item in ids:
        value=str(item).upper().strip()
        if not re.fullmatch(r"ML[A-Z]{1,2}[0-9]{5,20}",value): raise ValueError("ID do Mercado Livre inválido: "+value[:30])
        valid.append(value)
    if len(valid)>100: raise ValueError("Limite de 100 itens acompanhados")
    src={"id":"ml-watch","name":"Mercado Livre • Acompanhados"}
    out=[]
    for off in range(0,len(valid),20):
        response=json.loads(fetch("https://api.mercadolibre.com/items/bulk?ids="+quote(",".join(valid[off:off+20]),safe=","),token))
        if not isinstance(response,list): raise ValueError("Resposta de itens inesperada")
        for item in response:
            body=item.get("body") or {}
            if int(item.get("code",item.get("status_code",0)))!=200 or body.get("status")!="active": continue
            image=(body.get("pictures") or [{}])[0].get("secure_url") or body.get("thumbnail")
            offer=normalize(src,{"id":body.get("id"),"title":body.get("title"),"url":body.get("permalink"),
                                 "price":body.get("price"),"condition":body.get("condition"),"image":image})
            if offer:out.append(offer)
    return out

def matches(o,rules):
    if o["platform"] not in rules.get("platforms",P) or o["condition"] not in rules.get("conditions",["new","used"]): return False
    if rules.get("sources") and o["source_id"] not in rules["sources"]: return False
    if rules.get("max_price") is not None and o["price"]>float(rules["max_price"]): return False
    title=o["title"].casefold()
    yes=[str(x).casefold() for x in rules.get("include_keywords",[]) if str(x).strip()]
    no=[str(x).casefold() for x in rules.get("exclude_keywords",[]) if str(x).strip()]
    return (not yes or any(s in title for s in yes)) and not any(s in title for s in no)
def process(state,observed,ok,rules,at=None):
    at=at or now(); records=state.setdefault("records",{}); baseline=set(state.setdefault("initialized_sources",[]));events=[]
    for item in observed:
        old=records.get(item["id"]); p=item["price"]
        if old is None:
            records[item["id"]]=dict(item,first_seen=at,last_seen=at,anchor_price=p,first_price=p,lowest_price=p,price_history=[{"at":at,"price":p}],available=True)
            if item["source_id"] in baseline and rules.get("notify_new",True) and matches(item,rules):
                events.append({"id":item["id"]+":new","type":"new","offer":item})
        else:
            anchor=float(old.get("anchor_price",old["price"]));delta=round(anchor-p,2)
            if (p<float(old["price"]) and rules.get("notify_drop",True) and matches(item,rules)
                and delta>=float(rules.get("min_drop_brl",15))
                and (delta/anchor*100 if anchor else 0)>=float(rules.get("min_drop_percent",10))):
                events.append({"id":item["id"]+f":drop:{p:.2f}","type":"drop","offer":item,"from_price":anchor})
                anchor=p
            elif p>anchor: anchor=p
            history=list(old.get("price_history") or [{"at":old.get("first_seen",at),"price":old.get("first_price",old["price"])}])
            if p!=old["price"]:history.append({"at":at,"price":p})
            records[item["id"]]=dict(item,first_seen=old.get("first_seen",at),last_seen=at,
                  anchor_price=anchor,first_price=old.get("first_price",old["price"]),
                  lowest_price=min(old.get("lowest_price",old["price"]),p),
                  price_history=history[-25:],available=True)
    state["initialized_sources"]=sorted(baseline|set(ok))
    if len(records)>15000: state["records"]=dict(sorted(records.items(),key=lambda x:x[1]["last_seen"],reverse=True)[:15000])
    known=set(state.setdefault("alert_log",[]))|{e["id"] for e in state.setdefault("pending",[])}
    state["pending"].extend(e for e in events if e["id"] not in known)
    state["pending"]=state["pending"][-300:]
    return events
def collect(root=ROOT):
    root=Path(root); sources=read(root/"config/sources.json",{"feeds":[],"mercadolivre_sellers":[]})
    rules=read(root/"config/rules.json",{});state=read(root/"data/state.json",{})
    # Sem fontes cadastradas, não gerar commits de atualização vazios a cada hora.
    if not sources.get("feeds") and not sources.get("mercadolivre_sellers") and not sources.get("mercadolivre_items"):
        empty={"version":1,"updated_at":None,"sources_configured":0,"sources_ok":0,"health":[],"offers":[]}
        if read(root/"data/feed.json",None)!=empty: write(root/"data/feed.json",empty)
        print("GameRadar pronto. Nenhuma fonte autorizada conectada.")
        return 0
    observed=[];ok=[];health=[]
    for s in sources.get("feeds",[]):
        if not s.get("enabled",True): continue
        try:
            items=feed(s);observed.extend(items);ok.append(s["id"])
            health.append({"source":s.get("name",s["id"]),"status":"ok","count":len(items)})
        except Exception as exc:
            health.append({"source":s.get("name",s.get("id")),"status":"error","detail":str(exc)[:130]})
            print("Erro fonte",s.get("id"),exc,file=sys.stderr)
    watched=sources.get("mercadolivre_items",[])
    if watched:
        try:
            items=ml_items(watched,os.getenv("ML_ACCESS_TOKEN",""))
            observed.extend(items);ok.append("ml-watch")
            health.append({"source":"Mercado Livre • Acompanhados","status":"ok","count":len(items)})
        except Exception as exc:
            health.append({"source":"Mercado Livre • Acompanhados","status":"error","detail":str(exc)[:130]})
            print("Erro ML itens:",exc,file=sys.stderr)
    for seller in sources.get("mercadolivre_sellers",[]):
        try:
            items=ml_seller(seller,os.getenv("ML_ACCESS_TOKEN",""));observed.extend(items)
            ok.append("ml-"+str(seller));health.append({"source":"Mercado Livre "+str(seller),"status":"ok","count":len(items)})
        except Exception as exc:
            health.append({"source":"Mercado Livre "+str(seller),"status":"error","detail":str(exc)[:130]})
            print("Erro ML",seller,exc,file=sys.stderr)
    unique={o["id"]:o for o in observed};events=process(state,list(unique.values()),ok,rules)
    # Apenas feeds declarados como snapshots completos permitem identificar indisponíveis.
    # Feeds de novidades/listas parciais não eliminam anúncios que não retornaram nesta coleta.
    full=set(src["id"] for src in sources.get("feeds",[])
             if src.get("enabled",True) and src.get("complete_snapshot",False) and src["id"] in ok)
    if full:
        for old_id, old in state.get("records",{}).items():
            if old.get("source_id") in full and old_id not in unique:
                old["available"]=False
    state["last_check"]=now()
    visible=sorted(state.get("records",{}).values(),key=lambda x:x.get("last_seen",""),reverse=True)[:1500]
    output={"version":1,"updated_at":state["last_check"],"sources_configured":len([s for s in sources.get("feeds",[]) if s.get("enabled",True)])+len(sources.get("mercadolivre_sellers",[]))+(1 if watched else 0),
            "sources_ok":len(ok),"health":health,
            "offers":[{k:v for k,v in o.items() if k!="anchor_price"} for o in visible]}
    write(root/"data/state.json",state);write(root/"data/feed.json",output)
    print(len(unique),"anúncios coletados,",len(events),"eventos,",len(state["pending"]),"alertas pendentes.")
    return 1 if health and not ok else 0
def brl(n): return "R$ "+f"{n:,.2f}".replace(",","_").replace(".",",").replace("_",".")
def ntfy(events,topic):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{16,100}",topic or ""): raise ValueError("NTFY_TOPIC inválido")
    lines=[("NOVO" if e["type"]=="new" else "CAIU")+" • "+e["offer"]["title"][:60]+" • "+brl(e["offer"]["price"]) for e in events[:10]]
    if len(events)>10: lines.append("+"+str(len(events)-10)+" anúncios; abra GameRadar para ver")
    payload=json.dumps({"topic":topic,"title":"🎮 GameRadar • "+str(len(events))+" alertas",
        "message":"\n".join(lines)[:3800],"click":"https://gabriel-liz2003.github.io/GameRadar/"},ensure_ascii=False).encode()
    with urlopen(Request("https://ntfy.sh/",data=payload,headers={"Content-Type":"application/json"},method="POST"),timeout=20) as r:
        if r.status>=300: raise RuntimeError("ntfy HTTP "+str(r.status))
def notify(root=ROOT,topic=None,publisher=ntfy):
    root=Path(root);path=root/"data/state.json";state=read(path,{"pending":[],"alert_log":[]})
    seen=set(state.setdefault("alert_log",[]))
    pending=[e for e in state.setdefault("pending",[]) if e["id"] not in seen]
    if not pending: return 0
    topic=(topic if topic is not None else os.getenv("NTFY_TOPIC","")).strip()
    if topic:
        try: publisher(pending,topic)
        except Exception as exc:
            print("Notificação falhou:",exc,file=sys.stderr);return 2
    state["alert_log"]=(state["alert_log"]+[e["id"] for e in pending])[-16000:]
    state["pending"]=[];write(path,state);return 0
def main():
    args=argparse.ArgumentParser()
    args.add_argument("action",choices=["collect","notify","all"],nargs="?",default="all")
    args.add_argument("--root",default=str(ROOT))
    ns=args.parse_args()
    if ns.action=="collect": return collect(ns.root)
    if ns.action=="notify": return notify(ns.root)
    status=collect(ns.root)
    return notify(ns.root) or status
if __name__=="__main__": sys.exit(main())
