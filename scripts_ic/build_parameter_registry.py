from pathlib import Path
import ast,json,csv
from copy import deepcopy
import yaml
from scripts_ic.upgrade_common import ROOT,write_csv

def main():
    tree=ast.parse((ROOT/'ic_extension/model_v3.py').read_text(encoding='utf-8'));params={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
            name=node.args[0].value
            if len(node.args)>1:
                try:value=ast.literal_eval(node.args[1])
                except (ValueError,TypeError):value=ast.unparse(node.args[1])
                params.setdefault(name,[]).append({'value':value,'line':node.lineno})
    rows=[]
    configuration_names={'seed','periods','task_id','name','modules','import_case','policy','channels','shock','demand_shock','rationing_rule','engine_version'}
    for name,items in sorted(params.items()):
        if name in configuration_names:kind='configuration_or_structure_assumption'
        elif name in ['ai_initial','absorption']:kind='proxy_informed_initialization_or_scenario'
        elif name in ['welfare_weights','value_added','technology','resilience','shortage','fiscal_cost','concentration','price_volatility']:kind='normative_objective_weight_or_observation_field'
        else:kind='scenario_parameter_not_IO_estimated'
        rows.append({'parameter':name,'defaults':json.dumps([v['value'] for v in items],ensure_ascii=False),'code_lines':'|'.join(str(v['line']) for v in items),'evidence_status':kind,'empirically_estimated_in_national_model':False,'notes':'SMIC physical-unit capacity coefficient is estimated in a separate case and is not substituted into the national value-based coefficient' if 'capital' in name or 'capacity_lag'==name else ''})
    # Hard-coded rules are exposed rather than hidden by config enumeration.
    for name,value,meaning in [('government_ai_conversion',.1,'public AI expenditure conversion'),('government_rd_conversion',.05,'public R&D conversion'),('qualification_conversion',.2,'qualification support'),('price_feedback_gain',.05,'shortage-price feedback'),('holding_cost',.1,'finished inventory cost'),('shortage_cost',.2,'sector reward shortage penalty'),('edge_pressure_to_health',.05,'pressure-health mapping')]:
        rows.append({'parameter':name,'defaults':str(value),'code_lines':'hardcoded rule in model_v3.py','evidence_status':'scenario_rule_coefficient_not_IO_estimated','empirically_estimated_in_national_model':False,'notes':meaning})
    write_csv(ROOT/'calibration/dynamic_parameter_registry.csv',rows)
    with (ROOT/'ic_extension/data/sector_labels.csv').open(encoding='utf-8-sig') as f:sectors=list(csv.DictReader(f))[:13]
    mapping=[]
    for s in sectors:
        mapping.append({'sector_id':s['sector_index_1based'],'model_label':s['io_label'],'parent_sector':s['parent_42_sector'],'split_share':s['split_share_within_parent'],'origin':'existing executable 2020 workbook','method_from_attachment':'revenue separation coefficient; same transformation on row and column','numerator_source':'industrial/statistical/economic census yearbooks as listed in supplied manuscript','denominator_source':'same-scope parent-sector revenue from stated yearbooks','edition_years':'2019/2021 industrial; supplied manuscript states 2023 economic census; supplementary 2018 census and 2019/2021 statistical yearbooks','original_table_page_and_cell':'not supplied; cannot authenticate each numeric split','2020_missing_rule':'2018/2023 linear interpolation where applied; individual affected sectors not identified in attachment','scope_warning':'attachment includes information-service chip and application sectors not represented as decision agents in this 13-sector version'})
    write_csv(ROOT/'calibration/sector_split_registry.csv',mapping)
    inventory=[{'source':'National IO workbook','file':'remake-2020年投入产出表与指标.xlsx','year':'2020','role':'executed accounting matrix','status':'processed workbook, official download URL not supplied'}, {'source':'Supplied IO manuscript','file':'打印-返修2.1-基于投入产出表的中国集成电路全产业链结构与关联效应研究(1).docx','year':'2018/2020/2023 discussed','role':'classification and separation-method evidence','status':'unpublished supplied manuscript; scope differs from executable 13 sectors'}, {'source':'Supplied AI workbook','file':'AI渗透综合指标.xlsx','year':'2023/2024/unspecified','role':'four separate measured proxies','status':'functional aggregation, not AI coefficient identification'}, {'source':'SMIC official earnings releases','file':'external_validation/source_manifest.json','year':'2020Q1-2025Q4','role':'independent physical capacity case','status':'downloaded, hashes and page-level values retained'}]
    write_csv(ROOT/'calibration/data_source_registry.csv',inventory)
    # Preserve every configured leaf, including task overrides and normative weights.
    configured=[]
    def flatten(value,prefix):
        if isinstance(value,dict):
            for key,child in value.items():yield from flatten(child,prefix+'.'+str(key) if prefix else str(key))
        elif isinstance(value,list):
            for index,child in enumerate(value,1):yield from flatten(child,prefix+f'[{index}]')
        else:yield prefix,value
    for task in [f'ic_{g}{n}' for g in ['e','r','g'] for n in range(1,6)]:
        path=ROOT/'cfg_ic'/f'{task}.yaml'
        base=yaml.safe_load(path.read_text(encoding='utf-8'));variants=base.pop('variants',{})
        for arm,overrides in [('base',{})]+list(variants.items()):
            cfg=deepcopy(base)
            for key,value in overrides.items():
                if isinstance(value,dict) and isinstance(cfg.get(key),dict):cfg[key].update(value)
                else:cfg[key]=value
            for name,value in flatten(cfg,''):
                configured.append({'task':task,'arm':arm,'key_path':name,'configured_value':json.dumps(value,ensure_ascii=False),'source':str(path.relative_to(ROOT)),'evidence':'task configuration; not behavior identified from IO'})
    write_csv(ROOT/'calibration/task_parameter_registry.csv',configured)
    role_path=ROOT/'ic_extension/data/sector_roles.yaml'
    role_values=[{'key_path':name,'value':json.dumps(value,ensure_ascii=False),'source':str(role_path.relative_to(ROOT)),'evidence':'role configuration; H label is a mechanism locator'} for name,value in flatten(yaml.safe_load(role_path.read_text(encoding='utf-8')),'')]
    write_csv(ROOT/'calibration/sector_role_registry.csv',role_values)
    source=(ROOT/'ic_extension/model_v3.py').read_text(encoding='utf-8')
    literals=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)) and not isinstance(node.value,bool):
            literals.append({'line':node.lineno,'value':node.value,'code':source.splitlines()[node.lineno-1].strip(),'identity':'numeric code literal; may be dimension, bound, numerical constant or scenario coefficient, not automatically an economic parameter'})
    write_csv(ROOT/'calibration/code_literal_inventory.csv',sorted(literals,key=lambda r:r['line']))
    print(json.dumps({'dynamic_parameters':len(rows),'split_rows':len(mapping),'sources':len(inventory)}))

if __name__=='__main__':main()
