"""Build a self-contained, offline HTML demonstration from batch results."""
from __future__ import annotations

import json
from pathlib import Path


def build_dashboard(index: dict, destination: Path):
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IC EconGym 15个产业经济任务演示</title>
<style>
:root{--bg:#f5f7f8;--panel:#fff;--ink:#1d2b32;--muted:#60717c;--line:#dce4e8;--accent:#126d77;--accent2:#b65439}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"Microsoft YaHei",system-ui,sans-serif}
header{padding:24px 32px;background:#12343b;color:#fff}header h1{margin:0;font-size:24px;font-weight:650}header p{margin:8px 0 0;color:#c9dcdf;font-size:13px}
main{max-width:1480px;margin:auto;padding:24px;display:grid;grid-template-columns:290px minmax(0,1fr);gap:18px}
aside,.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 10px #102a3010}
aside{padding:15px;align-self:start;max-height:calc(100vh - 120px);overflow:auto;position:sticky;top:18px}
.aside-title{font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.04em;margin:2px 5px 12px}
.task{width:100%;display:block;text-align:left;border:0;background:transparent;border-radius:8px;padding:10px 11px;cursor:pointer;color:var(--ink);font-size:13px;line-height:1.35}
.task:hover{background:#ecf4f4}.task.active{background:#dceff0;color:#075a64;font-weight:700}
.tag{font-size:10px;color:var(--muted);display:block;margin-top:3px}
.content{min-width:0}.panel{padding:22px;margin-bottom:18px}.panel h2{margin:0 0 8px;font-size:21px}.question{color:var(--muted);line-height:1.7;font-size:14px;margin:0}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:16px 0 8px}select{border:1px solid #bacbd0;border-radius:7px;background:#fff;padding:8px 10px;color:var(--ink)}
.plot{height:350px;width:100%;border:1px solid var(--line);border-radius:8px;background:#fff;overflow:hidden}.plot svg{display:block;width:100%;height:100%}
.legend{display:flex;flex-wrap:wrap;gap:9px;margin-top:12px}.legend span{font-size:12px;padding:5px 8px;border-radius:20px;background:#f0f4f5}
.swatch{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px 7px;text-align:right;border-bottom:1px solid var(--line)}th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:650;background:#f7fafb}
.scroll{overflow:auto}.note{font-size:12px;line-height:1.6;color:#635a48;background:#fff8e8;padding:11px 13px;border-radius:8px;border:1px solid #eee0b5;margin:13px 0 0}
footer{color:var(--muted);font-size:11px;margin-top:10px}
@media(max-width:800px){main{grid-template-columns:1fr;padding:12px}aside{max-height:none;position:static}header{padding:20px}.panel{padding:15px}}
</style></head><body>
<header><h1>IC EconGym　13部门产业经济实验</h1><p>赋能 × 风险 × 治理｜15个任务｜统一投入产出约束环境</p></header>
<main><aside><div class="aside-title">选择任务</div><div id="task-list"></div></aside>
<div class="content"><section class="panel"><h2 id="task-title"></h2><p class="question" id="task-question"></p><div class="note">图表来自给定结构和参数下的机制仿真。2020年投入产出核算是数据锚点；AI、行为、冲击及政策系数为演示情景，不表示现实政策因果效应。金额原始单位为万元，图表中的大额金额换算为亿元。</div></section>
<section class="panel"><div class="controls"><label for="metric">指标</label><select id="metric"></select><span id="run-info" class="tag"></span></div><div class="plot" id="plot"></div><div class="legend" id="legend"></div></section>
<section class="panel"><h2 style="font-size:17px">期末情景对照</h2><div class="scroll"><table id="summary"></table></div><footer>同一任务的情景使用相同随机种子。完整逐期与部门结果见 runs 目录；财政成本为累计支出。</footer></section></div></main>
<script type="application/json" id="payload">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('payload').textContent);
const metrics={output:'总产出',value_added:'固定价格增加值',shortage:'总订单短缺',final_shortage:'当期最终需求短缺',final_fill_rate:'当期最终需求履约率（0—1）',service_rate:'总订单服务率',price_index:'价格指数',edge_health_mean:'平均边健康',ai_effective_mean:'平均有效AI',technology_mean:'平均技术状态',coordination_rate:'协同参与率',qualification_mean:'平均认证状态',government_inventory_spend:'当期库存支持',government_qualification_spend:'当期认证支持',government_edge_repair_spend:'当期边修复支持',supplier_hhi:'合成供给集中度',congestion_cumulative:'累计拥堵损失',fiscal_cost_cumulative:'累计财政成本',welfare:'设定权重下福利'};
const defaults={ic_e1:'ai_effective_mean',ic_e2:'shortage',ic_e3:'technology_mean',ic_e4:'shortage',ic_e5:'shortage',ic_r1:'price_index',ic_r2:'edge_health_mean',ic_r3:'shortage',ic_r4:'shortage',ic_r5:'shortage',ic_g1:'ai_effective_mean',ic_g2:'ai_effective_mean',ic_g3:'coordination_rate',ic_g4:'government_inventory_spend',ic_g5:'ai_effective_mean'};
const colors=['#126d77','#b65439','#9069a6','#bc9223','#3e78ab','#619c4b','#cf6678','#69747a','#44a799'];
const taskList=document.getElementById('task-list'),metricSelect=document.getElementById('metric');
let current=0;
const monetary=new Set(['output','value_added','shortage','final_shortage','congestion_cumulative','fiscal_cost_cumulative','welfare','government_inventory_spend','government_qualification_spend','government_edge_repair_spend']);
function n(x,key){if(!Number.isFinite(x))return '—';let a=Math.abs(x);return monetary.has(key)&&a>=1e4?(x/1e4).toFixed(2)+'亿元':a>=100?x.toFixed(1):x.toFixed(3)}
function menu(){taskList.innerHTML='';data.tasks.forEach((task,i)=>{let b=document.createElement('button');b.className='task'+(i===current?' active':'');b.innerHTML=task.id.toUpperCase()+'　'+task.name+'<span class="tag">'+task.variants.length+'个情景</span>';b.onclick=()=>{current=i;metricSelect.value=defaults[task.id]||'output';render()};taskList.appendChild(b)})}
function draw(task,key){const w=900,h=340,pad={l:90,r:25,t:20,b:43};const series=task.variants.map(v=>task.series[v].map(r=>Number(r[key])));const values=series.flat().filter(Number.isFinite);let lo=Math.min(...values),hi=Math.max(...values);if(!Number.isFinite(lo)||!Number.isFinite(hi)){lo=0;hi=1}if(lo===hi){lo-=Math.abs(lo)*.05+1;hi+=Math.abs(hi)*.05+1}else{let d=(hi-lo)*.07;lo-=d;hi+=d}const x=i=>pad.l+i*(w-pad.l-pad.r)/Math.max(data.periods-1,1),y=v=>h-pad.b-(v-lo)*(h-pad.t-pad.b)/(hi-lo);let svg='<svg viewBox="0 0 '+w+' '+h+'" preserveAspectRatio="none">';for(let k=0;k<5;k++){let yy=pad.t+k*(h-pad.t-pad.b)/4;let val=hi-k*(hi-lo)/4;svg+='<line x1="'+pad.l+'" y1="'+yy+'" x2="'+(w-pad.r)+'" y2="'+yy+'" stroke="#e6edef"/><text x="'+(pad.l-8)+'" y="'+(yy+4)+'" text-anchor="end" font-size="11" fill="#60717c">'+n(val,key)+'</text>'}svg+='<line x1="'+pad.l+'" y1="'+(h-pad.b)+'" x2="'+(w-pad.r)+'" y2="'+(h-pad.b)+'" stroke="#aebfc5"/>';[0,.25,.5,.75,1].forEach(f=>{let xx=x(f*(data.periods-1));svg+='<text x="'+xx+'" y="'+(h-13)+'" text-anchor="middle" font-size="11" fill="#60717c">'+Math.round(f*(data.periods-1))+'</text>'});series.forEach((arr,j)=>{let points=arr.map((v,i)=>x(i)+','+y(v)).join(' ');svg+='<polyline fill="none" stroke="'+colors[j%colors.length]+'" stroke-width="2.5" points="'+points+'"/>'});svg+='</svg>';document.getElementById('plot').innerHTML=svg;document.getElementById('legend').innerHTML=task.variants.map((v,j)=>'<span><i class="swatch" style="background:'+colors[j%colors.length]+'"></i>'+v+'</span>').join('')}
function table(task){const keys=['output','value_added','final_shortage','final_fill_rate','shortage','service_rate','price_index','supplier_hhi','fiscal_cost_cumulative'];let html='<tr><th>情景</th>'+keys.map(k=>'<th>'+metrics[k]+'</th>').join('')+'</tr>';task.variants.forEach(v=>{let r=task.series[v].at(-1);html+='<tr><td>'+v+'</td>'+keys.map(k=>'<td>'+n(Number(r[k]),k)+'</td>').join('')+'</tr>'});document.getElementById('summary').innerHTML=html}
function render(){menu();const task=data.tasks[current];document.getElementById('task-title').textContent=task.id.toUpperCase()+'　'+task.name;document.getElementById('task-question').textContent=task.question;document.getElementById('run-info').textContent=data.periods+'期｜随机种子 '+data.seeds.join(', ')+'｜进口配置 '+data.import_case;let previous=metricSelect.value;metricSelect.innerHTML=Object.entries(metrics).map(([k,v])=>'<option value="'+k+'">'+v+'</option>').join('');metricSelect.value=previous&&metrics[previous]?previous:(defaults[task.id]||'output');draw(task,metricSelect.value);table(task)}
metricSelect.addEventListener('change',()=>draw(data.tasks[current],metricSelect.value));render();
</script></body></html>'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page.replace("__DATA__", payload), encoding="utf-8")
