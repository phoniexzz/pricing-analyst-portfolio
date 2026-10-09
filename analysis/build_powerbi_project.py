"""Build documented PBIP/PBIR/TMDL definitions from a validated snapshot."""
from pathlib import Path
import json, uuid
from powerbi_schema_tools import URLS
from powerbi_measures import MEASURES,MEASURE_TABLE
from powerbi_prepare import ROOT, DISCLAIMERS
P=ROOT/'powerbi';R=P/'Northstar.Report';D=R/'definition';S=P/'Northstar.SemanticModel/definition'
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n' if not isinstance(value,str) else value,encoding='utf-8')
def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'northstar.phase9/'+name))
def field(table,col,measure=False):return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':col}}
def ref(value):return field(MEASURE_TABLE,value,True) if isinstance(value,str) else field(*value)
def lit(value):
 return {'expr':{'Literal':{'Value':('true' if value else 'false') if isinstance(value,bool) else str(value)+'D' if isinstance(value,(int,float)) else "'"+str(value).replace("'","''")+"'"}}}
def filter_def(table,col,values):
 return {'Version':2,'From':[{'Name':'s','Entity':table,'Type':0}],'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':col}}],'Values':[[{'Literal':{'Value':('true' if v else 'false') if isinstance(v,bool) else str(v)+'L' if isinstance(v,int) else "'"+str(v).replace("'","''")+"'"}}] for v in values]}}}]}
def flt(name,table,col,values=None,locked=False,drill=False):
 d={'name':name,'field':field(table,col),'type':'Categorical','howCreated':'Drillthrough' if drill else 'User','isHiddenInViewMode':locked,'isLockedInViewMode':locked}
 if values is not None:d['filter']=filter_def(table,col,values)
 return d
def mflt(name,measure):
 return {'name':name,'field':field(MEASURE_TABLE,measure,True),'type':'Advanced','howCreated':'User','isHiddenInViewMode':True,'isLockedInViewMode':True,'filter':{'Version':2,'From':[{'Name':'m','Entity':MEASURE_TABLE,'Type':0}],'Where':[{'Condition':{'Comparison':{'ComparisonKind':0,'Left':{'Measure':{'Expression':{'SourceRef':{'Source':'m'}},'Property':measure}},'Right':{'Literal':{'Value':'1L'}}}}}]}}
PAGES=[]
def page(name,title,scope,experiment=False,detail=False):
 p={'name':name,'title':title,'scope':scope,'visuals':[],'filters':[],'detail':detail,'experiment':experiment}
 PAGES.append(p);return p
def visual(p,name,kind,title,x,y,w,h,roles=None,filters=None,text=None,action=None):
 v={'name':p['name']+'_'+name,'type':kind,'title':title,'x':x,'y':y,'w':w,'h':h,'roles':roles or {},'filters':filters or [],'text':text,'action':action}
 p['visuals'].append(v);return v
def cards(p,items,y=188):
 n=len(items);w=(1544-16*(n-1))/n
 for j,(title,measure) in enumerate(items):visual(p,'k'+str(j),'card',title,28+j*(w+16),y,w,91,{'Values':[measure]})
def chart(p,name,kind,title,x,y,w,h,**roles):return visual(p,name,kind,title,x,y,w,h,roles)
def table(p,name,title,x,y,w,h,columns,filters=None):return visual(p,name,'tableEx',title,x,y,w,h,{'Values':columns},filters)
def slicer(p,name,title,table,col,x,y,w=245,default=None,sync=False):
 v=visual(p,name,'slicer',title,x,y,w,58,{'Values':[(table,col)]})
 v['default']=default;v['sync']=sync;return v

# Executive: annual historical reporting; portfolio is an independent fixed Base/base saved view.
p=page('p01','Executive Overview','Historical selected window. Snapshot Dec 2025. Conditional portfolio Jan–Dec 2026.')
cards(p,[('Net revenue','Net Revenue'),('Final-month members','Closing Members'),('ARPMM','ARPMM'),('Acquisitions','Acquisitions'),('Monthly opening-base churn','Opening-base Churn')])
for j,measure in enumerate(['Executive Revenue Comparison','Executive Members Comparison','Executive ARPMM Comparison','Executive Acquisition Comparison','Executive Churn Comparison']):
 visual(p,'comparison'+str(j),'card','',28+j*312,281,296,22,{'Values':[measure]})['small_font']=10
chart(p,'revenue','lineChart','Matching-month net revenue',28,305,490,275,Category=[('DimHistoryMonth','month_name')],Y=['Net Revenue','Net Revenue Prior Year'])
chart(p,'members','lineChart','Matching-month closing membership',540,305,490,275,Category=[('DimHistoryMonth','month_name')],Y=['Closing Members','Closing Members Prior Year'])
chart(p,'bridge','waterfallChart','Exact annual revenue bridge (£ net)',1052,305,520,275,Category=[('DimBridge','step')],Y=['Revenue Bridge'])
p['visuals'][-1]['title']='Revenue change: volume + total ARPMM'
p['visuals'][-1]['filters']=[flt('p01_bridge_change','DimBridge','step',['Member volume','Total ARPMM'])]
chart(p,'actions','barChart','Saved conditional action counts',28,608,490,238,Category=[('FactRecommendation','action')],Y=['Recommendation Site Count'])
table(p,'portfolio','Conditional RAISE portfolio. TEST FIRST excluded.',540,608,620,238,['Conditional Raise Sites','Portfolio Increment','Portfolio Member Difference','Portfolio Increment lower','Portfolio Increment upper'])
visual(p,'scope','card','Portfolio uncertainty scope',1180,608,392,100,{'Values':['Portfolio Uncertainty Scope']})
visual(p,'changes','card','Matching-period revenue growth',1180,728,392,118,{'Values':['Net Revenue YoY']})
p['filters'] += [flt('p01_case','DimCase','case',['Base'],True),flt('p01_policy','DimPolicy','variant',['base'],True)]
# Snapshot and source ranks stay immutable.
p=page('p02','Estate Pricing','December 2025 snapshot. All competitors and national-equivalent fields are fictional proxies. Recurring prices include VAT; introductory discounts are separate.')
cards(p,[('Sites in selection','Gyms In Selection'),('Median Standard headline','Median Standard Price'),('Mean competitor recurring gap','Average Competitor Gap'),('Sites with existing caution','Caution Sites')])
chart(p,'gap','scatterChart','December competitor gap versus 2025 monthly churn',28,305,850,345,Category=[('DimGym','gym_id')],X=['Competitor Gap December'],Y=['Headroom Churn 2025'],Series=[('DimGym','segment')],Tooltips=['Saved Estate Rank','Headroom Score','Caution Count'])
chart(p,'band','barChart','Sites by preserved score band',904,305,668,345,Category=[('DimGym','band')],Y=['Gyms In Selection'])
table(p,'sites','Pricing position, service pressure and caution flags',28,678,1544,205,[('DimGym','gym_id'),('DimGym','city'),'Standard Headline December','Competitor Recurring December','Competitor Gap December','Competitor Joining Fee December','Competitor Intro Discount December','Headroom Peak 2025','Caution Count','Headroom Score','Saved Estate Rank','Headroom Band'])
# Behaviour: site measures are weighted; historical policy inference is always saved full 12-pair scope.
p=page('p03','Customer & Member Behaviour','Historical selected window with matching-year comparison. Historical pilot: Oct 2024–Mar 2025 vs Apr–Sep 2025.')
cards(p,[('Qualified conversion','Qualified Conversion'),('Monthly retention','Monthly Retention'),('Acquisition growth','Acquisitions YoY'),('Member growth within period','Period Member Growth'),('Complaints / 1,000 member-months','Complaints per 1000')])
chart(p,'acquisition','lineChart','Monthly acquisition and matching 2024',28,305,750,270,Category=[('DimHistoryMonth','month_name')],Y=['Acquisitions','Acquisitions Prior Year'])
chart(p,'churn','lineChart','Opening-base churn and matching 2024',800,305,772,270,Category=[('DimHistoryMonth','month_name')],Y=['Opening-base Churn','Opening-base Churn Prior Year'])
table(p,'pilot','Saved historical £2 pilot. Equal weights, 12 pairs; local evidence.',28,605,980,248,['Historical Standard Acquisition Effect','Historical Standard Acquisition Effect lower','Historical Standard Acquisition Effect upper','Historical Acquisition Elasticity','Historical Incumbent Churn Effect','Historical Incumbent Churn Effect lower','Historical Incumbent Churn Effect upper','Historical Downgrade Effect','Historical Downgrade Effect lower','Historical Downgrade Effect upper'])
table(p,'q4','Q4 2025 vs Q4 2024 and membership mix',1030,605,542,248,['Q4 Net Revenue Growth','Q4 Acquisitions Growth','Q4 Opening-base Churn Change pp','Q4 Qualified Conversion Change pp','Standard Mix','Off-Peak Mix','Plus Mix','Marketing Spend'])
# Scenario selection controls saved combinations, not the live spreadsheet inputs.
p=page('p04','Pricing Scenarios','Saved Jan–Dec 2026 scenarios. Conditional parameter uncertainty excludes future shocks and transport uncertainty.')
slicer(p,'case','Saved case','DimCase','case',28,184,240,['Base'])
visual(p,'status','card','Saved scenario status',292,184,1280,61,{'Values':['Scenario Selection Status']})
chart(p,'revenue','lineChart','Cumulative incremental net revenue by price option',28,253,752,300,Category=[('DimScenarioMonth','month_name')],Series=[('DimPrice','label')],Y=['Scenario Cumulative Increment'])
chart(p,'members','lineChart','Closing membership by saved price option',800,253,772,300,Category=[('DimScenarioMonth','month_name')],Series=[('DimPrice','label')],Y=['Scenario Monthly Closing'])
table(p,'compare','Saved annual comparisons. December × 12 is seasonal exit run-rate.',28,582,1544,154,[('DimPrice','label'),'Scenario Incremental Revenue','Scenario Increment lower','Scenario Increment upper','Scenario December Members','Scenario Member Impact','Scenario Joins','Scenario Churn','Scenario Downgrade Rate','Scenario Subscription Yield','Scenario ARPMM','Scenario Exit Run-rate'])
table(p,'stress','Site stress results (single gym). Search 0–64; unavailable if no crossing.',28,763,1080,116,[('DimGym','gym_id'),('DimPrice','label'),'Break-even Multiplier','Break-even Member Impact','Break-even Crossings','Teaching Retention Ratio'])
visual(p,'uncertainty','card','Scope of saved ranges',1132,763,440,116,{'Values':['Uncertainty Scope']})
# Recommendations are saved immutable Phase 7 policy decisions.
p=page('p05','Recommendations','Hypothetical 2026 conditional actions. Controlled testing precedes wider implementation. Policy variants are read-only.')
visual(p,'policy','card','Evidence status',28,184,1544,57,{'Values':['Evidence Status']})
p['filters'].append(flt('p05_case','DimCase','case',['Base'],True))
cards(p,[('Base-policy conditional raises','Conditional Raise Sites'),('Base raise-only portfolio uplift','Base Portfolio Increment'),('Base December member difference','Base Portfolio Member Difference'),('Base full-policy lower range','Base Portfolio Increment lower')],y=250)
table(p,'recommendations','80 saved site actions, provisional tests and failed gates',28,371,1544,279,[('DimGym','gym_id'),('DimGym','city'),'Saved Recommendation','Standard Headline December','Recommended Standard Price','Provisional Test Increment','Provisional Test Price','£1 plausible','£1 qualified','£1 failed gates','£2 plausible','£2 qualified','£2 failed gates','Recommendation Explanation'])
table(p,'sensitivity','Five read-only policy variants. Base actions above remain unchanged.',28,677,1040,190,[('DimPolicy','label'),'Saved Policy Raise £1 Sites','Saved Policy Raise £2 Sites','Saved Policy Test Sites','Portfolio Increment','Saved Policy Action'])
visual(p,'policy_scope','card','Portfolio range scope',1092,677,480,190,{'Values':['Portfolio Uncertainty Scope']})
# Experiment: no shared historical/date slicers; saved inference defaults to primary five pairs.
p=page('p06','Experiment & Monitoring','Illustrative £1 experiment. Five first-repricing pairs primary; two repeat pairs exploratory. Simulations are not new evidence.',experiment=True)
p['height']=1350
slicer(p,'simulation','Simulation','DimSimulation','simulation',28,114,295,['Main'])
slicer(p,'checkpoint','Assessment','DimCheckpoint','checkpoint_months',345,114,295,[6])
slicer(p,'population','Saved population','DimPopulation','population',662,114,410,['First repricing'])
visual(p,'window','card','Comparison window',1094,114,478,58,{'Values':['Experiment Window']})
cards(p,[('Saved decision','Experiment Saved Decision'),('Controlled revenue effect','Experiment Revenue Effect'),('Revenue lower bound','Experiment Revenue Effect lower'),('One-sided p-value','Experiment One-sided p'),('Complete pairs','Experiment Complete Pairs')])
chart(p,'revenue','lineChart','Treatment/control revenue. Notice Jan; billing Feb 2026.',28,307,752,190,Category=[('DimExperimentMonth','year_month')],Series=[('DimAssignment','assignment')],Y=['Experiment Profile Revenue'])
chart(p,'members','lineChart','Treatment/control closing members',800,307,772,190,Category=[('DimExperimentMonth','year_month')],Series=[('DimAssignment','assignment')],Y=['Experiment Profile Closing'])
chart(p,'churn_profile','lineChart','Monthly incumbent Standard churn',28,525,752,190,Category=[('DimExperimentMonth','year_month')],Series=[('DimAssignment','assignment')],Y=['Experiment Profile Churn'])
chart(p,'downgrade_profile','lineChart','Monthly incumbent Standard downgrades',800,525,772,190,Category=[('DimExperimentMonth','year_month')],Series=[('DimAssignment','assignment')],Y=['Experiment Profile Downgrade Rate'])
table(p,'pairs','Pair revenue and monthly churn effects (saved)',28,744,590,180,[('FactExperimentPair','pair_id'),'Experiment Pair Revenue Effect',('FactExperimentPair','revenue_difference'),('FactExperimentPair','incumbent_churn_change_pp')],filters=[mflt('pair_population','Experiment Pair In Population')])
table(p,'harms','95% harm upper bounds; monthly changes in pp',640,744,540,180,[('FactExperimentGuardrail','label'),'Guardrail Point Display','Guardrail Upper Display','Guardrail Tolerance Display','Guardrail Upper Pass'])
chart(p,'power','lineChart','Planning power: five pairs',1202,744,370,180,Category=[('FactPower','effect_assumption')],Y=['Planning Power'])
p['visuals'][-1]['filters']=[flt('p06_powerdesign','FactPower','design',['5 first-repricing pairs']),flt('p06_powermethod','FactPower','method',['Exact assignment Monte Carlo'])]
table(p,'monitoring','Checkpoint monitoring and required management responses',28,950,990,216,[('FactExperimentMonitoring','gym_id'),('FactExperimentMonitoring','assignment'),('FactExperimentMonitoring','population_decision'),('FactExperimentMonitoring','capacity_trigger'),('FactExperimentMonitoring','paired_complaints_change'),('FactExperimentMonitoring','required_response')],filters=[mflt('monitor_population','Experiment Monitoring In Population')])
table(p,'assignment','Seven pairs and reserves NF023/NF057',1040,950,532,216,[('FactExperimentDesign','gym_id'),('FactExperimentDesign','pair_id'),('FactExperimentDesign','assignment'),('FactExperimentDesign','population'),('FactExperimentDesign','disposition')],filters=[flt('p06_eligible','FactExperimentDesign','eligible',[True])])
# Hidden detail is a real field-bound drill-through page.
p=page('p07','Gym Detail','Selected gym: 2025 trading, Dec 2025 snapshot and saved £1/£2 qualification evidence.',detail=True)
cards(p,[('Selected site revenue','Net Revenue'),('Closing members','Closing Members'),('December competitor gap','Competitor Gap December'),('Saved score','Headroom Score'),('Saved action','Saved Recommendation')])
chart(p,'trading','lineChart','Monthly net revenue at selected gym',28,305,752,254,Category=[('DimHistoryMonth','month_name')],Y=['Net Revenue','Net Revenue Prior Year'])
table(p,'position','December pricing and relative evidence',804,305,768,254,[('DimGym','gym_id'),('DimGym','city'),'Standard Headline December','Competitor Recurring December','Competitor Gap December','Headroom Band','Saved Estate Rank','Caution Count','Rank Movement Sensitivity'])
table(p,'gates1','£1 qualification evidence (Phase 7 policy)',28,589,752,200,['£1 plausible','£1 qualified','£1 base revenue','£1 downside revenue','£1 downside member impact','£1 revenue lower','£1 failed gates'])
table(p,'gates2','£2 qualification evidence (Phase 7 policy)',800,589,772,200,['£2 plausible','£2 qualified','£2 base revenue','£2 downside revenue','£2 downside member impact','£2 revenue lower','£2 failed gates'])
table(p,'rationale','Commercial rationale',28,810,1544,150,['Recommendation Explanation'])

def model():
 schema=json.loads((P/'model_schema.json').read_text())
 # Native Desktop may create automatic date tables on save. This report uses
 # declared date dimensions, so rebuild removes only these owned auto tables.
 for auto in list((S/'tables').glob('LocalDateTable_*.tmdl'))+list((S/'tables').glob('DateTableTemplate_*.tmdl')):
  assert auto.resolve().is_relative_to((S/'tables').resolve());auto.unlink()
 obsolete=S/'tables/FactScenarioSensitivity.tmdl'
 if obsolete.exists():
  assert obsolete.resolve().is_relative_to(S.resolve());obsolete.unlink()
 write(P/'gym_pricing_dashboard.pbip',{'$schema':URLS['project'],'version':'1.0','artifacts':[{'report':{'path':'Northstar.Report'}}],'settings':{'enableAutoRecovery':True}})
 write(R/'definition.pbir',{'$schema':URLS['reportReference'],'version':'4.0','datasetReference':{'byPath':{'path':'../Northstar.SemanticModel'}}})
 write(P/'Northstar.SemanticModel/definition.pbism',{'$schema':URLS['modelReference'],'version':'4.0','settings':{}})
 write(S/'database.tmdl','database\n\tcompatibilityLevel: 1601\n')
 model='model Model\n\tculture: en-GB\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-GB\n\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n\tannotation PBI_QueryOrder = '+json.dumps(['SourceRoot']+list(schema['tables']))+'\n'
 write(S/'model.tmdl',model)
 path=str((P/'model_data').resolve()).replace('\\','/')
 expression='expression SourceRoot = "'+path+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\tlineageTag: '+uid('SourceRoot')+'\n'
 write(S/'expressions.tmdl',expression)
 queries={}
 for name,meta in schema['tables'].items():
  text=f'table {name}\n\tlineageTag: {uid(name)}\n'
  for col,typ in meta['columns'].items():
   text+=f'\n\tcolumn {col}\n\t\tdataType: {typ}\n\t\tsourceColumn: {col}\n\t\tsummarizeBy: none\n\t\tlineageTag: {uid(name+col)}\n'
   if typ=='dateTime':text+='\t\tformatString: yyyy-MM-dd\n'
   elif typ in ['double','int64']:
    if col.endswith('_pp'):text+='\t\tformatString: 0.00" pp"\n'
    elif col in ['effect_assumption','planning_power','effect_detectable_80pct']:text+='\t\tformatString: 0.0%\n'
    elif any(x in col for x in ['revenue','yield','arpmm','standard_price','competitor_price','joining_fee']) and not any(x in col for x in ['growth','uplift','effect','joining_fee_payers']):text+='\t\tformatString: £#,##0.00\n'
    elif typ=='int64':text+='\t\tformatString: #,##0\n'
   if name.startswith('Fact') and typ!='string':text+='\t\tisHidden\n'
   if col=='month_name' and name.startswith('Dim'):text+='\t\tsortByColumn: month_number\n'
   if col in ['label','step','metric'] and 'sort_order' in meta['columns']:text+='\t\tsortByColumn: sort_order\n'
  types={'string':'type text','int64':'Int64.Type','double':'type number','dateTime':'type date','boolean':'type logical'}
  converted=', '.join('{"'+c+'", '+types[t]+'}' for c,t in meta['columns'].items())
  query=f'let\n    Source = Csv.Document(File.Contents(SourceRoot & "/{name}.csv"), [Delimiter=",", Columns={len(meta["columns"])}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),\n    Typed = Table.TransformColumnTypes(Nulls, {{{converted}}}, "en-GB")\nin\n    Typed'
  text+=f'\n\tpartition {name} = m\n\t\tmode: import\n\t\tsource =\n'+''.join('\t\t\t\t'+l+'\n' for l in query.splitlines())
  write(S/'tables'/f'{name}.tmdl',text);queries[name]=query
 # One measure table, with no physical fact-to-fact relationships.
 t='table '+MEASURE_TABLE+'\n\tlineageTag: '+uid('Measures')+'\n'
 for name,meta in MEASURES.items():
  t+=f"\n\t/// {meta['description']}\n\tmeasure '{name.replace(chr(39),chr(39)*2)}' =\n\t\t\t{meta['dax']}\n\t\tdisplayFolder: {meta['folder']}\n\t\tlineageTag: {uid(name)}\n"
  if meta['format']:t+='\t\tformatString: '+meta['format']+'\n'
 t+='\n\tcolumn Value\n\t\tdataType: int64\n\t\tisHidden\n\t\tsummarizeBy: none\n\t\tsourceColumn: [Value]\n\n\tpartition '+MEASURE_TABLE+' = calculated\n\t\tmode: import\n\t\tsource = {0}\n'
 write(S/'tables'/f'{MEASURE_TABLE}.tmdl',t)
 legacy=S/'tables/Measures.tmdl'
 if legacy.exists():
  assert legacy.resolve().is_relative_to(S.resolve());legacy.unlink()
 relationships=''
 for rel in schema['relationships']:
  relationships+=f"relationship {uid(str(rel))}\n\tfromColumn: {rel['fact']}.{rel['column']}\n\ttoColumn: {rel['dimension']}.{rel['dimension_column']}\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n\n"
 write(S/'relationships.tmdl',relationships)
 write(P/'PowerQuery.m','section Section1;\n// SourceRoot is an editable Power Query parameter.\nshared SourceRoot = "'+path+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true];\n\n'+'\n\n'.join('shared '+n+' =\n'+q+';' for n,q in queries.items()))
 write(P/'Measures.dax','// Documentation mirror; authoritative expressions are in TMDL.\n\n'+'\n\n'.join('['+n+'] =\n'+v['dax'] for n,v in MEASURES.items()))
 write(P/'measure_catalog.json',MEASURES)
 write(P/'.gitignore','**/.pbi/localSettings.json\n**/.pbi/cache.abf\n')

def report():
 version={'visual':'2.4.0','page':'2.1.0','report':'3.0.0'}
 theme={'name':'Northstar','dataColors':['#087F8C','#17324D','#B86200','#7A5195','#B33545','#477499','#477A35'],'background':'#F4F7FA','foreground':'#17324D','tableAccent':'#087F8C','textClasses':{'title':{'fontFace':'Segoe UI','fontSize':13},'label':{'fontFace':'Segoe UI','fontSize':11},'callout':{'fontFace':'Segoe UI','fontSize':24}}}
 write(R/'StaticResources/RegisteredResources/Northstar.json',theme)
 write(D/'report.json',{'$schema':URLS['report'],'themeCollection':{'customTheme':{'name':'Northstar','reportVersionAtImport':version,'type':'RegisteredResources'}},'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'Northstar','path':'Northstar.json','type':'CustomTheme'}]}],'settings':{'useStylableVisualContainerHeader':True}})
 write(D/'version.json',{'$schema':URLS['version'],'version':'2.0.0'})
 write(D/'pages/pages.json',{'$schema':URLS['pages'],'pageOrder':[p['name'] for p in PAGES],'activePageName':'p01'})
 books=[]
 for p in PAGES:
  panel_map={'p01_portfolio':'Executive Portfolio','p03_pilot':'Historical Pilot','p03_q4':'Q4 and Mix','p07_position':'Detail Position','p07_gates1':'Detail Qualification £1','p07_gates2':'Detail Qualification £2'}
  for v in p['visuals']:
   if v['name'] in panel_map:
    v['roles']={'Values':[('DimMetricPanel','metric'),'Metric Panel Saved Value']};v['filters']=[flt(v['name']+'_panel','DimMetricPanel','panel',[panel_map[v['name']]],True)]
  if not p['experiment']:
   for j,(title,col) in enumerate([('Region','region'),('Location type','location_type'),('Headroom segment','segment'),('Gym','gym_id')]):slicer(p,'shared'+str(j),title,'DimGym',col,28+j*390,114,370,sync=not p['detail'])
   if p['name'] in ['p01','p03','p07']:
    # Year selectable; month selection in the date slicer/filter pane is matched to prior year.
    slicer(p,'year','Reporting year','DimHistoryMonth','year',1280,52,290,[2025],sync=not p['detail'])
    slicer(p,'months','Reporting months','DimHistoryMonth','month_name',990,52,270,sync=not p['detail'])
  if p['name']=='p07':p['filters'].append(flt('gym_drill','DimGym','gym_id',drill=True))
  # Every page has normal Power BI navigation, a reset bookmark, visible period and definitions.
  visual(p,'heading','textbox','',28,47,940 if p['name'] in ['p01','p03','p07'] else 1220,51,text='Northstar Fitness  /  '+p['title'])
  bottom=1180 if p['experiment'] else 970 if p['detail'] else 889
  if p['name'] in ['p01','p03','p07']:
   scope=visual(p,'scope_label','card','',28,bottom,1544,33,{'Values':['Historical Reporting Note']});scope['small_font']=9
  else:visual(p,'scope_label','textbox','',28,bottom,1544,33,text=p['scope'])
  stamp=visual(p,'stamp','card','Snapshot ID. Native acceptance is recorded in powerbi/NATIVE_VERIFICATION.md.',28,bottom+137,1544,56,{'Values':['Snapshot Version']})
  stamp['small_font']=9
  p['height']=max(p.get('height',1050),bottom+206)
  definitions='Revenue excludes assumed 20% VAT. Gross recurring prices are separate. Revenue is not profit. Monthly churn uses opening-base exposure; retention is not annual.'
  if p['name']=='p04':definitions='Saved scenarios only. December revenue × 12 is seasonal exit run-rate. +£3 reaches unchanged Plus at 20 gyms. Teaching ratio covers only a uniformly affected group.'
  if p['name']=='p06':definitions='Harm upper bounds: members 3%, Standard acquisition 10%, monthly churn/downgrades +0.25 pp. Primary minimum one-sided p=3.125%; small sample. Repeat intervals unavailable.'
  if p['name']=='p05':definitions='Phase 7 gates: downside member loss ≤5%, positive revenue/lower bound/non-zero sensitivities. These are policy assumptions; TEST FIRST gains are excluded from portfolios.'
  visual(p,'definitions','textbox','',28,bottom+36,1544,35,text=definitions)
  visual(p,'disclaimer','textbox','',28,bottom+77,1544,62,text='\n'.join(DISCLAIMERS))
  for j,target in enumerate(PAGES[:6]):
   nav_label=['Overview','Estate Pricing','Member Behaviour','Scenarios','Recommendations','Experiment & Monitoring'][j]
   if not(p['detail'] and j==0):visual(p,'nav'+str(j),'actionButton',nav_label,28+j*220,7,210,30,action=('PageNavigation',target['name']))
  visual(p,'reset','actionButton','Reset page',1360,7,210,30,action=('Bookmark','reset_'+p['name']))
  if p['detail']:visual(p,'back','actionButton','Back',28,7,160,30,action=('Back',None))
  pdict={'$schema':URLS['page'],'name':p['name'],'displayName':p['title'],'displayOption':'FitToPage','width':1600,'height':p.get('height',1050),'filterConfig':{'filters':p['filters']},'objects':{'background':[{'properties':{'color':{'solid':{'color':lit('#F4F7FA')}},'transparency':lit(0)}}]}}
  if p['detail']:
   pdict.update({'visibility':'HiddenInViewMode','type':'Drillthrough','pageBinding':{'name':'GymDetail','type':'Drillthrough','acceptsFilterContext':'None','parameters':[{'name':'gym','boundFilter':'gym_drill','fieldExpr':field('DimGym','gym_id')} ]}})
  # Prevent source action chart from cross-filtering unrelated historical totals or portfolio rules.
  interactions=[]
  sources=[v for v in p['visuals'] if v['type'] not in ['slicer','textbox','actionButton','card']]
  for a in sources:
   for b in p['visuals']:
    if a!=b and b['type'] not in ['textbox','actionButton']:interactions.append({'source':a['name'],'target':b['name'],'type':'NoFilter'})
  pdict['visualInteractions']=interactions
  expected={v['name'] for v in p['visuals']}
  for stale in (D/f'pages/{p["name"]}/visuals').glob('*/visual.json'):
   if stale.parent.name.startswith(p['name']+'_') and stale.parent.name not in expected:
    assert stale.resolve().is_relative_to((D/'pages').resolve())
    stale.unlink();stale.parent.rmdir()
  defaults={};bookmarkvisuals={}
  for index,v in enumerate(p['visuals']):
   obj={'$schema':URLS['visual'],'name':v['name'],'position':{'x':v['x'],'y':v['y'],'z':index,'width':v['w'],'height':v['h'],'tabOrder':index}}
   vc={'visualType':v['type'],'visualContainerObjects':{'title':[{'properties':{'show':lit(bool(v['title'])),'text':lit(v['title']),'fontSize':lit(12),'fontColor':{'solid':{'color':lit('#17324D')}}}}],'background':[{'properties':{'show':lit(True),'color':{'solid':{'color':lit('#FFFFFF')}},'transparency':lit(0)}}]}}
   if v['roles']:
    query={}
    for role,fields in v['roles'].items():
     query[role]={'projections':[{'field':ref(f),'queryRef':(MEASURE_TABLE+'.'+f if isinstance(f,str) else '.'.join(f)),'nativeQueryRef':('Saved result' if f=='Metric Panel Saved Value' else f) if isinstance(f,str) else f[1].replace('_',' ').title()} for f in fields]}
    vc['query']={'queryState':query}
   if v['text']:
    vc['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':line,'textStyle':{'fontSize':'18pt' if v['name'].endswith('heading') else '9pt','fontFamily':'Segoe UI','color':'#17324D'}}]} for line in v['text'].split('\n')]}}]}
   if v['type']=='card':
    text_measures={'Portfolio Uncertainty Scope','Uncertainty Scope','Scenario Selection Status','Evidence Status','Experiment Window','Saved Recommendation','Experiment Saved Decision'}
    is_text=any(f in text_measures for f in v['roles'].get('Values',[]) if isinstance(f,str))
    vc['objects']={'labels':[{'properties':{'fontSize':lit(12 if is_text else 23),'labelDisplayUnits':lit(1),'color':{'solid':{'color':lit('#17324D')}}}}],'categoryLabels':[{'properties':{'show':lit(False)}}],'wordWrap':[{'properties':{'show':lit(True)}}]}
   if v.get('small_font'):vc['objects']['labels'][0]['properties']['fontSize']=lit(v['small_font'])
   if v['type']=='tableEx':vc['objects']={'columnHeaders':[{'properties':{'wordWrap':lit(True),'fontSize':lit(10)}}],'values':[{'properties':{'wordWrap':lit(True),'fontSize':lit(10)}}],'grid':[{'properties':{'rowPadding':lit(4)}}],'total':[{'properties':{'totals':lit(False)}}]}
   if v['type']=='tableEx' and v['roles']['Values']==[('DimMetricPanel','metric'),'Metric Panel Saved Value']:
    vc['objects']['columnWidth']=[{'selector':{'metadata':'DimMetricPanel.metric'},'properties':{'value':lit(v['w']*.58)}},{'selector':{'metadata':MEASURE_TABLE+'.Metric Panel Saved Value'},'properties':{'value':lit(v['w']*.37)}}]
   if v['name'] in ['p01_actions','p02_gap']:
    table_name,col='FactRecommendation','action'
    colors={'RAISE £2':'#087F8C','RAISE £1':'#477499','TEST FIRST':'#B86200','HOLD PRICE':'#17324D','DEFENSIVE / INVESTIGATE':'#B33545'}
    if v['name']=='p02_gap':
     table_name,col='DimGym','segment';colors={'Investigation priority':'#B33545','Stronger headroom indicators':'#087F8C','Limited headroom indicators':'#17324D','Mixed indicators':'#B86200'}
    vc.setdefault('objects',{})['dataPoint']=[{'selector':{'data':[{'scopeId':{'Comparison':{'ComparisonKind':0,'Left':field(table_name,col),'Right':{'Literal':{'Value':"'"+cat+"'"}}}}}]},'properties':{'fill':{'solid':{'color':lit(color)}}}} for cat,color in colors.items()]
   if v['type']=='slicer':
    vc['objects']={'data':[{'properties':{'mode':lit('Dropdown')}}],'header':[{'properties':{'show':lit(False)}}],'items':[{'properties':{'textSize':lit(10)}}],'selection':[{'properties':{'singleSelect':lit(v.get('default') is not None),'selectAllCheckboxEnabled':lit(False)}}]}
    if v.get('sync'):vc['syncGroup']={'groupName':v['roles']['Values'][0][1],'fieldChanges':True,'filterChanges':True}
    t,c=v['roles']['Values'][0]
    if v.get('default') is not None:
     sel=filter_def(t,c,v['default']);vc['objects']['general']=[{'properties':{'filter':{'filter':sel}}}]
    else:sel=None
    merge=dict(vc['objects'])
    if sel is None:merge['general']=[{'properties':{'filter':{'filter':{'Version':2,'From':[{'Name':'s','Entity':t,'Type':0}],'Where':[]}}}}]
    bookmarkvisuals[v['name']]={'singleVisual':{'objects':{'merge':merge}}}
   if v['action']:
    vc['visualContainerObjects']['title'][0]['properties']['show']=lit(False)
    typ,target=v['action'];props={'show':lit(True),'type':lit(typ)}
    if target:props['navigationSection' if typ=='PageNavigation' else 'bookmark']=lit(target)
    vc['visualContainerObjects']['visualLink']=[{'properties':props}]
    vc['objects']={'text':[{'properties':{'show':lit(True)}},{'selector':{'id':'default'},'properties':{'text':lit(v['title']),'fontSize':lit(9),'fontColor':{'solid':{'color':lit('#FFFFFF')}}}}],'fill':[{'properties':{'show':lit(True)}},{'selector':{'id':'default'},'properties':{'fillColor':{'solid':{'color':lit('#17324D')}},'transparency':lit(0)}}],'outline':[{'properties':{'show':lit(False)}}]}
   if v['filters']:obj['filterConfig']={'filters':v['filters']}
   if v['name'] in ['p06_pairs','p06_monitoring']:
    current=mflt(v['name']+'_current','Experiment Evidence Current')
    current['filter']['Where'][0]['Condition']['Comparison']['Right']['Literal']['Value']='true'
    obj.setdefault('filterConfig',{}).setdefault('filters',[]).append(current)
   obj['visual']=vc;write(D/f'pages/{p["name"]}/visuals/{v["name"]}/visual.json',obj)
  write(D/f'pages/{p["name"]}/page.json',pdict)
  bm={'$schema':URLS['bookmark'],'name':'reset_'+p['name'],'displayName':'Reset '+p['title'],'options':{'applyOnlyToTargetVisuals':True,'targetVisualNames':list(bookmarkvisuals),'suppressDisplay':True,'suppressData':False,'suppressActiveSection':False},'explorationState':{'version':'1.3','activeSection':p['name'],'sections':{p['name']:{'visualContainers':bookmarkvisuals}}}}
  write(D/f'bookmarks/reset_{p["name"]}.bookmark.json',bm);books.append({'name':bm['name']})
 write(D/'bookmarks/bookmarks.json',{'$schema':URLS['bookmarks'],'items':books})
 write(P/'page_specification.json',PAGES)
if __name__=='__main__':
 model();report();print('Built populated PBIP/PBIR/TMDL project:',len(PAGES),'pages;',len(MEASURES),'explicit measures')
