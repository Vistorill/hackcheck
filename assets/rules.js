/* HackCheck – motor de regras de compatibilidade.
   Compartilhado pela landing page e pela dashboard.
   Regras iniciais baseadas na comunidade; confirme sempre no guia Dortania. */
var V=['High Sierra 10.13','Mojave 10.14','Catalina 10.15','Big Sur 11','Monterey 12','Ventura 13','Sonoma 14','Sequoia 15','Tahoe 26'],T=8;
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function R(s,n,m,u){return {s:s,n:n,m:m==null?T:m,u:u!==false&&s!=='bad'}}
function cpuR(n){n=n||'';var m;
if(!n)return R('bad','CPU não detectada.');
if(/Core\(TM\) Ultra|Core Ultra/i.test(n))return R('bad','Core Ultra (Meteor Lake e posteriores) não é suportado.');
if(/Ryzen|Threadripper|EPYC/i.test(n))return R('ok','AMD: exige patches de kernel (AMD Vanilla). Funciona, com ajustes.');
if(/AMD|Athlon|FX-/i.test(n))return R('bad','Linha AMD sem suporte prático.');
if(/Xeon/i.test(n))return R('warn','Xeon: verifique o modelo manualmente.');
if(m=n.match(/i[3579]-(\d{4,5})(\w*)/i)){var d=m[1],g=d.length==5?+d.slice(0,2):+d[0];
if(/^1[0-3]\d{2}$/.test(d)&&/^G\d/i.test(m[2]))return R('warn','Ice/Tiger Lake mobile: suporte experimental.');
if(g<2)return R('bad','Anterior à Sandy Bridge.');
if(g==2)return R('warn','Sandy Bridge: sem AVX2, limite Big Sur.',3);
if(g==3)return R('warn','Ivy Bridge: sem AVX2, limite Monterey.',4);
if(g<=10)return R('ok','Geração '+g+': suportada.');
if(g==11)return R('warn','Rocket Lake: iGPU sem suporte, exige GPU dedicada AMD.');
if(g==12&&/^12[1-6]\d0$/.test(d)&&!/K/i.test(m[2]))return R('warn','Alder Lake sem E-cores: funciona com patches de CPU e GPU dedicada AMD.');
if(g<=14)return R('warn','Geração '+g+': experimental; desative os E-cores e use GPU dedicada AMD.');
return R('bad','Geração não suportada.')}
if(/Pentium|Celeron/i.test(n))return R('warn','Verifique o modelo e a geração manualmente.');
return R('warn','CPU não reconhecida; verifique manualmente.',0,false)}
function gpuR(n){n=n||'';var m;
if(/Microsoft|Basic|Virtual|Remote|Parsec|Meta|Citrix/i.test(n))return null;
if(/Radeon(\(TM\))?\s+(Vega\s*\d+\s+)?Graphics/i.test(n)&&!/RX/i.test(n))return R('bad','iGPU AMD (APU) sem suporte.');
if(m=n.match(/RX\s*(\d{3,4})/i)){var x=+m[1];
if(x>=540&&x<=550)return R('warn','AMD Lexa (RX 540/550): exige spoof e muitas vezes não funciona.');
if(x>=460&&x<=590||x>=5000&&x<=5999)return R('ok','AMD Polaris/Navi 1: suporte nativo.');
if(x>=6400&&x<=6599)return R('bad','AMD Navi 24 (RX 6400/6500): sem suporte.');
if(x>=6600&&x<=6999)return R('ok','AMD RDNA2: suportada (modelos 6600/6700 podem exigir ajustes).');
if(x>=7000)return R('bad','AMD RDNA3 ou mais nova: sem suporte.');
return R('warn','Modelo AMD antigo; verifique.',4)}
if(/Vega\s*(56|64)|Radeon VII/i.test(n))return R('ok','AMD Vega: suporte nativo.');
if(/RTX|GTX\s*16\d\d/i.test(n))return R('bad','NVIDIA Turing ou mais nova: sem suporte.');
if(/GTX\s*7[45]\d/i.test(n))return R('warn','NVIDIA Maxwell (GTX 745/750): só High Sierra (driver Web).',0);
if(m=n.match(/GTX\s*(\d{3,4})|GT\s*(\d{3})/i)){var y=+(m[1]||m[2]);
if(y>=600&&y<800)return R('warn','NVIDIA Kepler: limite Big Sur.',3);
if(y>=900&&y<1100)return R('warn','NVIDIA Maxwell/Pascal: só High Sierra (driver Web).',0);
return R('bad','NVIDIA sem suporte nesta versão.')}
if(m=n.match(/UHD Graphics\s*(\d+)/i))return m[1][0]=='6'?R('ok','Intel UHD 6xx: suportada.'):R('bad','Intel UHD 7xx: sem suporte.');
if(/Iris(\(R\))?\s*Plus/i.test(n))return R('warn','Intel Iris Plus (Ice Lake): suporte experimental.');
if(/Iris(\(R\))?\s*Xe|Arc/i.test(n))return R('bad','Intel Iris Xe/Arc: sem suporte.');
if(/Intel.*UHD Graphics\s*$/i.test(n))return R('warn','Intel UHD sem número (Comet Lake): suportada como UHD 630; confirme a geração da CPU.');
if(m=n.match(/HD Graphics\s*(\d+)/i)){var h=+m[1];
if(h<=3000)return R('warn','Sandy Bridge iGPU: limite Big Sur.',3);
if(h<=5999)return R('warn','iGPU Ivy/Haswell/Broadwell: limite Monterey sem patches.',4);
return R('warn','iGPU Skylake/Kaby Lake: drivers legados (verifique).',6)}
return R('warn','GPU não reconhecida; verifique manualmente.',0,false)}
function netR(n){
if(/bluetooth|virtual|vpn|vmware|hyper-v|tap|loopback|miniport|wan|vethernet/i.test(n))return null;
if(/wi-?fi|wireless|802\.11|wlan/i.test(n)){
if(/Broadcom|BCM|DW1560|Fenvi/i.test(n))return R('ok','Wi-Fi Broadcom: suporte nativo.');
if(/Intel/i.test(n))return R('warn','Wi-Fi Intel: via itlwm; sem AirDrop/Handoff.');
return R('bad','Wi-Fi sem suporte. Troque por Broadcom ou use dongle USB.')}
if(/I21[0-9]|I22[56]|Intel/i.test(n))return R('ok','Ethernet Intel: suportada.');
if(/RTL81|8111|8125|Realtek/i.test(n))return R('ok','Ethernet Realtek: suportada (kext).');
return R('warn','Ethernet não reconhecida; verifique.')}
function audR(n){if(/NVIDIA|AMD High|Display|HDMI|Virtual|Bluetooth|USB/i.test(n))return null;
return /Realtek|ALC/i.test(n)?R('ok','Realtek: suportado via AppleALC.'):R('warn','Codec não confirmado; verifique o layout-id.')}
function dskR(n){return /PM981|PM991|2200S/i.test(n)?R('bad','Modelo conhecido por causar kernel panic no macOS.'):R('ok','Compatível (NVMe/SATA).')}
function analyze(d){var it=[];
function add(c,n,r){if(r)it.push({c:c,n:n,s:r.s,t:r.n,m:r.m,u:r.u})}
add('CPU',d.cpu||'(não detectada)',cpuR(d.cpu));
(d.gpu||[]).forEach(function(x){add('GPU',x,gpuR(x))});
(d.net||[]).forEach(function(x){add('Rede',x,netR(x))});
(d.audio||[]).forEach(function(x){add('Áudio',x,audR(x))});
(d.disk||[]).forEach(function(x){add('Disco',x,dskR(x))});
if(d.ram!=null)add('Memória',d.ram+' GB',+d.ram>=8?R('ok','Memória suficiente.'):R('warn','Recomendado ao menos 8 GB.'));
if(d.laptop)it.push({c:'Tipo',n:'Notebook',s:'warn',t:'Notebooks exigem ajustes extras (trackpad, bateria, tela, Wi-Fi). Desktops são mais simples.',m:T,u:true});
if(d.board)it.push({c:'Placa-mãe',n:d.board,s:'info',t:'Verifique atualização de BIOS e opções (CSM, Secure Boot).',m:T,u:true});
var cpu=it.filter(function(x){return x.c=='CPU'})[0],gp=it.filter(function(x){return x.c=='GPU'&&x.u}),bl=[];
if(!cpu||cpu.s=='bad')bl.push('CPU incompatível.');
if(!gp.length)bl.push('Nenhuma GPU compatível encontrada.');
var mx=Math.min(cpu&&cpu.u?cpu.m:(cpu&&cpu.s=='bad'?-1:T),gp.length?Math.max.apply(null,gp.map(function(x){return x.m})):-1);
var cnt={ok:0,warn:0,bad:0};it.forEach(function(x){if(cnt[x.s]!=null)cnt[x.s]++});
var v=bl.length?'bad':(cnt.warn+cnt.bad?'warn':'ok');
return {it:it,bl:bl,mx:bl.length?-1:mx,cnt:cnt,v:v}}
