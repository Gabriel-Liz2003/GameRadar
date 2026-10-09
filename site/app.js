"use strict";
const PLATFORMS={switch2:"Switch 2",switch:"Switch",ps5:"PS5",ps4:"PS4",xbox_series:"Xbox Series",xbox_one:"Xbox One"};
const EXAMPLES=[
{id:"demo-1",title:"Pokémon Legends: Z-A Nintendo Switch 2 lacrado — exemplo",platform:"switch2",condition:"new",price:289.90,source:"LOJA FICTÍCIA",source_id:"demo",url:"https://example.com",image:null,location:"Brasil",first_seen:new Date().toISOString()},
{id:"demo-2",title:"Zelda Tears of the Kingdom Nintendo Switch usado — exemplo",platform:"switch",condition:"used",price:189.90,source:"CLASSIFICADO FICTÍCIO",source_id:"demo",url:"https://example.com",image:null,location:"Santa Catarina",first_seen:new Date().toISOString()},
{id:"demo-3",title:"Astro Bot PS5 novo — exemplo",platform:"ps5",condition:"new",price:149.90,source:"LOJA FICTÍCIA",source_id:"demo",url:"https://example.com",image:null,location:"São Paulo",first_seen:new Date().toISOString()}
];
const q=s=>document.querySelector(s);
const values={platforms:Object.keys(PLATFORMS),search:"",location:"",source:"",maxPrice:"",newCheck:true,usedCheck:true,unknownCheck:false,sort:"recent",onlyFavorites:false};
function stored(key,def){try{return JSON.parse(localStorage.getItem(key))||def}catch{return def}}
let filters={...values,...stored("gr-filter-v1",{})};
if(!Array.isArray(filters.platforms))filters.platforms=Object.keys(PLATFORMS);
let favorites=stored("gr-favorites-v1",[]);
if(!Array.isArray(favorites))favorites=[];
let feed={offers:[],sources_ok:0,sources_configured:0,health:[],updated_at:null};
let demo=false,limit=36;
const brl=n=>new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"}).format(Number(n)||0);
function persist(){try{localStorage.setItem("gr-filter-v1",JSON.stringify(filters));localStorage.setItem("gr-favorites-v1",JSON.stringify(favorites))}catch{}}
function dateAgo(s){
 if(!s)return "Sem data";
 const h=Math.floor((Date.now()-new Date(s).getTime())/3600000);
 if(!Number.isFinite(h)||h<0)return "Recente";
 if(h<1)return "Há pouco";if(h<24)return h+"h atrás";
 return Math.floor(h/24)+"d atrás";
}
function modal(title,body,code){
 q("#modalTitle").textContent=title;q("#modalText").textContent=body;
 q("#modalCode").hidden=!code;q("#copy").hidden=!code;q("#modalCode").textContent=code||"";
 q("#modal").showModal();
}
function init(){
 q("#platforms").replaceChildren(...Object.entries(PLATFORMS).map(([id,name])=>{
  const b=document.createElement("button");b.className="chip";b.textContent=name;b.dataset.id=id;
  b.onclick=()=>{filters.platforms=filters.platforms.includes(id)?filters.platforms.filter(x=>x!==id):[...filters.platforms,id];persist();sync();render()};return b;
 }));
 for(const [el,key] of [["#search","search"],["#location","location"],["#maxPrice","maxPrice"]]){
  q(el).oninput=e=>{filters[key]=e.target.value;limit=36;persist();render()};
 }
 for(const [el,key] of [["#source","source"],["#sort","sort"]]){
  q(el).onchange=e=>{filters[key]=e.target.value;limit=36;persist();render()};
 }
 for(const [el,key] of [["#newCheck","newCheck"],["#usedCheck","usedCheck"],["#unknownCheck","unknownCheck"],["#onlyFavorites","onlyFavorites"]]){
  q(el).onchange=e=>{filters[key]=e.target.checked;limit=36;persist();render()};
 }
 q("#reset").onclick=()=>{filters={...values,platforms:Object.keys(PLATFORMS)};limit=36;persist();sync();render()};
 q("#reload").onclick=()=>load(true);
 q("#more").onclick=()=>{limit+=36;render()};
 q("#showDemo").onclick=()=>{demo=!demo;render()};
 q("#toggleDemo").onclick=()=>{demo=!demo;render()};
 q("#about").onclick=()=>modal("Como funciona","O GameRadar coleta anúncios de fontes JSON/RSS oficialmente disponibilizadas ou inventários de vendedores que autorizaram o aplicativo do Mercado Livre.\n\nA primeira coleta registra os anúncios sem avisar sobre todos eles. Nas verificações seguintes, detecta anúncios novos e quedas de preço. O GitHub Actions salva os resultados e usa o ntfy para alertar.\n\nO painel não pesquisa todos os anúncios da Amazon, Shopee, OLX ou Mercado Livre sem credenciais e permissão.");
 q("#notifications").onclick=()=>modal("Ativar notificações no Android","1. Instale o aplicativo ntfy no Android.\n2. Gere um tópico longo e aleatório com Python: import secrets; print('gameradar-'+secrets.token_urlsafe(24)).\n3. Inscreva-se nesse tópico no ntfy.\n4. No GitHub, configure o secret NTFY_TOPIC com o tópico criado.\n5. Edite config/rules.json para filtros de alertas. O primeiro scan da fonte é silencioso.\n\nNão compartilhe o tópico: qualquer pessoa que descubra um tópico público pode lê-lo.");
 q("#rules").onclick=()=>{
   const cfg={platforms:filters.platforms,conditions:[...(filters.newCheck?["new"]:[]),...(filters.usedCheck?["used"]:[]),...(filters.unknownCheck?["unknown"]:[])],
   sources:filters.source?[filters.source]:[],max_price:filters.maxPrice?Number(filters.maxPrice):null,
   include_keywords:filters.search?[filters.search]:[],exclude_keywords:["somente caixa","sem jogo"],
   notify_new:true,notify_drop:true,min_drop_percent:10,min_drop_brl:15};
   modal("Exportar regras de alertas","Copie o JSON abaixo e substitua o conteúdo de config/rules.json no repositório. Isso controla os avisos no celular. Os filtros do site não atualizam o GitHub automaticamente.",JSON.stringify(cfg,null,2));
 };
 q("#close").onclick=()=>q("#modal").close();q("#ok").onclick=()=>q("#modal").close();
 q("#modal").onclick=e=>{if(e.target===q("#modal"))q("#modal").close()};
 q("#copy").onclick=async()=>{try{await navigator.clipboard.writeText(q("#modalCode").textContent);q("#copy").textContent="Copiado ✓"}catch{q("#copy").textContent="Selecione o JSON para copiar"}};
 sync();load();
 if("serviceWorker" in navigator && location.protocol==="https:"){window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}))}
}
function sync(){
 for(const [el,key] of [["#search","search"],["#location","location"],["#maxPrice","maxPrice"],["#sort","sort"]])q(el).value=filters[key];
 for(const [el,key] of [["#newCheck","newCheck"],["#usedCheck","usedCheck"],["#unknownCheck","unknownCheck"],["#onlyFavorites","onlyFavorites"]])q(el).checked=filters[key];
 document.querySelectorAll(".chip").forEach(b=>{const on=filters.platforms.includes(b.dataset.id);b.classList.toggle("active",on);b.setAttribute("aria-pressed",String(on))});
 q("#source").value=filters.source;
}
async function load(manual=false){
 q("#feedStatus").textContent="Carregando...";
 try{
  const result=await fetch("./data/feed.json?v="+Date.now(),{cache:"no-store"});
  if(!result.ok)throw Error("HTTP "+result.status);
  const value=await result.json();
  if(!Array.isArray(value.offers))throw Error("Formato inválido");
  feed=value;
  q("#notice").className="notice";
 }catch(err){
  feed={offers:[],sources_ok:0,sources_configured:0,health:[],updated_at:null};
  q("#notice").textContent="Não foi possível carregar o feed. Para abrir localmente, execute um servidor HTTP; não use file://. Erro: "+err.message;
  q("#notice").className="notice show error";
 }
 const ids=[...new Set(feed.offers.map(o=>o.source_id).filter(Boolean))];
 const select=q("#source");select.replaceChildren();
 const opt=document.createElement("option");opt.value="";opt.textContent="Todas as fontes";select.append(opt);
 for(const id of ids){
  const el=document.createElement("option");el.value=id;
  el.textContent=(feed.offers.find(o=>o.source_id===id)||{}).source||id;select.append(el);
 }
 if(!ids.includes(filters.source))filters.source="";
 sync();render();
 if(manual&&feed.updated_at)q("#feedStatus").textContent="Feed consultado";
}
function card(item){
 const article=document.createElement("article");article.className="card";
 const picture=document.createElement("div");picture.className="picture";
 const tag=document.createElement("span");tag.className="tag "+(item.condition==="used"?"used":item.condition!=="new"?"unknown":"");tag.textContent=item.condition==="new"?"NOVO":item.condition==="used"?"USADO":"NÃO INFORMADO";picture.append(tag);
 const fav=document.createElement("button");fav.className="favorite";fav.setAttribute("aria-label","Favoritar anúncio");fav.textContent=favorites.includes(item.id)?"★":"☆";fav.classList.toggle("active",favorites.includes(item.id));
 fav.onclick=()=>{favorites=favorites.includes(item.id)?favorites.filter(x=>x!==item.id):[...favorites,item.id];persist();render()};picture.append(fav);
 if(item.image&&String(item.image).startsWith("https://")){
  const img=document.createElement("img");img.src=item.image;img.alt="Imagem do anúncio";img.loading="lazy";img.referrerPolicy="no-referrer";
  img.onerror=()=>{img.remove();const mark=document.createElement("div");mark.className="placeholder";mark.textContent="🎮";picture.append(mark)};picture.append(img);
 }else{const mark=document.createElement("div");mark.className="placeholder";mark.textContent="🎮";picture.append(mark)}
 const body=document.createElement("div");body.className="card-body";
 const plat=document.createElement("div");plat.className="platform-label";plat.textContent=PLATFORMS[item.platform]||item.platform;
 const h=document.createElement("h3");h.textContent=item.title;
 const seller=document.createElement("div");seller.className="seller";seller.textContent=(item.source||"Fonte")+(item.location?" · "+item.location:"");
 const priceEl=document.createElement("div");priceEl.className="price";priceEl.textContent=brl(item.price);
 const shipping=document.createElement("div");shipping.className="shipping";shipping.textContent=item.shipping!=null?"Frete: "+brl(item.shipping):"Frete a consultar";
 const bottom=document.createElement("div");bottom.className="card-bottom";
 const tm=document.createElement("span");tm.className="date";tm.textContent=dateAgo(item.first_seen||item.last_seen);
 const link=document.createElement("a");link.className="deal-link";link.textContent=demo?"Somente exemplo ↗":"Ver anúncio ↗";
 if(!demo && /^https:\/\//.test(item.url||"")){link.href=item.url;link.target="_blank";link.rel="noopener noreferrer"}
 else{link.href="#";link.onclick=e=>{e.preventDefault();modal("Exemplo fictício","Este anúncio aparece apenas para demonstrar a interface. Não existe oferta real associada.")}};
 bottom.append(tm,link);body.append(plat,h,seller,priceEl,shipping,bottom);article.append(picture,body);return article;
}
function render(){
 const offers=demo?EXAMPLES:(feed.offers||[]);
 q("#allCount").textContent=offers.length;
 q("#lowest").textContent=offers.length?brl(Math.min(...offers.map(o=>o.price))):"—";
 q("#sourcesOk").textContent=demo?"—":String(feed.sources_ok||0);
 q("#lastUpdate").textContent=demo?"Dados fictícios":feed.updated_at?"Atualizado "+dateAgo(feed.updated_at):"Aguardando coleta";
 q("#feedStatus").textContent=demo?"Modo exemplo":feed.sources_ok?"Fontes online":feed.sources_configured?"Fontes com falha":"Sem fontes conectadas";
 q("#feedStatus").classList.toggle("ok",!demo&&feed.sources_ok>0);
 if(demo){q("#notice").textContent="MODO DEMONSTRAÇÃO: anúncios e preços fictícios. Volte aos dados reais usando o botão abaixo.";q("#notice").className="notice show"}
 else if(!feed.sources_configured){q("#notice").textContent="O monitor está pronto, mas ainda não há uma fonte autorizada conectada. Configure config/sources.json no GitHub. Os anúncios exibidos serão reais somente depois disso.";q("#notice").className="notice show"}
 else if(!feed.sources_ok){q("#notice").textContent="Nenhuma fonte respondeu com sucesso. Confira os logs do workflow no GitHub.";q("#notice").className="notice show error"}
 else if(feed.health&&feed.health.some(h=>h.status==="error")){q("#notice").textContent="Algumas fontes estão indisponíveis, mas você pode consultar os anúncios coletados anteriormente.";q("#notice").className="notice show error"}
 else{q("#notice").className="notice"}
 let visible=offers.filter(o=>filters.platforms.includes(o.platform))
  .filter(o=>filters[o.condition==="new"?"newCheck":o.condition==="used"?"usedCheck":"unknownCheck"])
  .filter(o=>!filters.maxPrice || Number(o.price)<=Number(filters.maxPrice))
  .filter(o=>!filters.source || o.source_id===filters.source)
  .filter(o=>!filters.search || (o.title||"").toLocaleLowerCase("pt-BR").includes(filters.search.toLocaleLowerCase("pt-BR")))
  .filter(o=>!filters.location || (o.location||"").toLocaleLowerCase("pt-BR").includes(filters.location.toLocaleLowerCase("pt-BR")))
  .filter(o=>!filters.onlyFavorites || favorites.includes(o.id));
 if(filters.sort==="low")visible.sort((a,b)=>a.price-b.price);
 else if(filters.sort==="high")visible.sort((a,b)=>b.price-a.price);
 else if(filters.sort==="name")visible.sort((a,b)=>a.title.localeCompare(b.title,"pt-BR"));
 else visible.sort((a,b)=>new Date(b.first_seen||b.last_seen)-new Date(a.first_seen||a.last_seen));
 q("#resultCount").textContent="("+visible.length+")";
 q("#resultLabel").textContent=visible.length+" "+(visible.length===1?"resultado":"resultados");
 q("#cards").replaceChildren(...visible.slice(0,limit).map(card));
 q("#more").hidden=visible.length<=limit;
 q("#empty").hidden=visible.length>0;
 q("#emptyTitle").textContent=offers.length?"Nenhum jogo com esses filtros":"Seu radar está vazio";
 q("#emptyText").textContent=offers.length?"Experimente limpar os filtros ou mudar a plataforma.":"Conecte fontes de mídia física autorizadas para receber anúncios reais. É possível ver um exemplo visual.";
 q("#showDemo").textContent=demo?"Voltar aos dados reais":"Ver exemplo visual ↗";
 q("#toggleDemo").textContent=demo?"← Dados reais":"Ver exemplo";
}
init();
