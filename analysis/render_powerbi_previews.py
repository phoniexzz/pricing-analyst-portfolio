"""Render clearly labelled design previews from the saved snapshot and page spec.

These illustrate the intended composition; they do not emulate Power BI or prove
native DAX, interaction or visual rendering behaviour.
"""
import sys,json,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/.workbook_previews/python_packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter,PercentFormatter
import numpy as np,pandas as pd
from powerbi_measures import MEASURES,METRIC_PANELS
P=ROOT/'powerbi';OUT=ROOT/'images';OUT.mkdir(exist_ok=True)
NAVY='#17324D';TEAL='#087F8C';AMBER='#B86200';RED='#B33545';BLUE='#477499'
plt.rcParams.update({'font.family':'Segoe UI','font.size':10,'axes.labelcolor':NAVY,'text.color':NAVY,'axes.edgecolor':'#D5DEE8','xtick.color':'#52667A','ytick.color':'#52667A'})
def load(n):return pd.read_csv(P/'model_data'/f'{n}.csv')
H=load('FactHistory');G=load('DimGym');REC=load('FactRecommendation');HEAD=load('FactHeadroom');ANN=load('FactScenarioAnnual');SM=load('FactScenarioMonthly');EST=load('FactScenarioEstate');PORT=load('FactPortfolio');HP=load('FactHistoricalEstimate');EX=load('FactExperimentEstimate');EP=load('FactExperimentPath');GOV=load('FactExperimentGovernance');DES=load('FactExperimentDesign');MON=load('FactExperimentMonitoring');POWER=load('FactPower');PAIR=load('FactExperimentPair');GUARD=load('FactExperimentGuardrail')
SINGLE=REC[REC.action=='RAISE £2'].iloc[0].gym_id
def fmt(value,measure=None):
 if value is None or pd.isna(value):return '—'
 if isinstance(value,(bool,np.bool_)):return 'Yes' if value else 'No'
 if isinstance(value,str):return value
 f=MEASURES.get(measure,{}).get('format','')
 if '%' in f:return f'{value:.2%}'
 if 'pp' in f:return f'{value:.2f} pp'
 if '£' in f:return f'£{value:,.2f}' if '0.00' in f else f'£{value:,.0f}'
 if '#,##0'==f:return f'{value:,.0f}'
 if f=='0.0000':return f'{value:.4f}'
 if f=='0.0':return f'{value:.1f}'
 return f'{value:,.2f}'
def hist_metrics(gym=None):
 d=H if gym is None else H[H.gym_id==gym];d25=d[d.month.str.startswith('2025')];d24=d[d.month.str.startswith('2024')]
 result={}
 for year,t in [(2025,d25),(2024,d24)]:
  rev=t.monthly_revenue.sum();ex=t.average_members.sum();opening=t.opening_members.sum();joins=t.new_members.sum()
  vv={'Net Revenue':rev,'Closing Members':t[t.month=='%s-12-01'%year].closing_members.sum(),'ARPMM':rev/ex,'Acquisitions':joins,'Opening-base Churn':t.opening_base_cancellations.sum()/opening,'Qualified Conversion':joins/t.qualified_prospects.sum(),'Average Members':ex/12,'Average Member Months':ex}
  vv['Monthly Retention']=1-vv['Opening-base Churn']
  for k,v in vv.items():result[k+(' Prior Year' if year==2024 else '')]=v
 for k in ['Net Revenue','Closing Members','Average Members','Acquisitions','ARPMM']:result[k+' YoY']=result[k]/result[k+' Prior Year']-1
 result['Period Member Growth']=result['Closing Members']/d25[d25.month=='2025-01-01'].opening_members.sum()-1
 result['Complaints per 1000']=d25.pricing_complaints.sum()/d25.average_members.sum()*1000
 result['Marketing Spend']=d25.marketing_spend.sum()
 result['Opening-base Churn Change pp']=(result['Opening-base Churn']-result['Opening-base Churn Prior Year'])*100
 result['Conditional Raise Sites']=REC[REC.action.str.startswith('RAISE')].shape[0] if gym is None else int(REC.set_index('gym_id').loc[gym,'action'].startswith('RAISE'))
 for k,col in [('Standard Mix','average_standard_members'),('Off-Peak Mix','average_offpeak_members'),('Plus Mix','average_premium_members')]:result[k]=d25[col].sum()/d25.average_members.sum()
 for name,col in [('Net Revenue','monthly_revenue'),('Acquisitions','new_members')]:
  a=d25[d25.month>='2025-10-01'][col].sum();b=d24[d24.month>='2024-10-01'][col].sum();result['Q4 '+name+' Growth']=a/b-1
 for name,num,den in [('Opening-base Churn','opening_base_cancellations','opening_members'),('Qualified Conversion','new_members','qualified_prospects')]:
  a=d25[d25.month>='2025-10-01'];b=d24[d24.month>='2024-10-01'];result['Q4 '+name+' Change pp']=(a[num].sum()/a[den].sum()-b[num].sum()/b[den].sum())*100
 return result
def metric(name,gym=None):
 h=hist_metrics(gym)
 if name in h:return h[name]
 if name.startswith('Executive ') and name.endswith(' Comparison'):
  underlying={'Revenue':'Net Revenue YoY','Members':'Closing Members YoY','ARPMM':'ARPMM YoY','Acquisition':'Acquisitions YoY','Churn':'Opening-base Churn Change pp'}[name[10:-11]]
  return 'vs 2024: '+(f'{h[underlying]:+.2f} pp' if 'pp' in underlying else f'{h[underlying]:+.2%}')
 if name.startswith('Base Portfolio '):return metric(name.replace('Base Portfolio','Portfolio'),gym)
 if name=='Evidence Status':return 'CURRENT saved evidence. Base actions and named portfolio; five read-only sensitivities below.'
 if name=='Historical Reporting Note':return 'Historical window: Jan–Dec 2025. Prior-year comparison uses the same months. Pricing snapshot: Dec 2025. Conditional portfolio: Jan–Dec 2026.'
 if name=='Gyms In Selection':return 80 if gym is None else 1
 if name=='Median Standard Price':return G.current_standard_price.median()
 if name=='Average Competitor Gap':return G.competitor_price_gap.mean()
 if name=='Caution Sites':return (G.caution_flag_count>0).sum()
 if name=='Portfolio Uncertainty Scope':return 'Saved full-policy range; provisional tests excluded.'
 if name=='Uncertainty Scope':return 'Saved full-estate conditional range. Regional ranges are unavailable.'
 if name=='Scenario Selection Status':return 'Saved Base case. No forecasts are rerun. £3 is an analytical comparison.'
 if name=='Snapshot Stamp':return 'Validated reporting snapshot. Phase 9 build-ready; native verification pending.'
 if name=='Experiment Window':return 'Jul–Dec 2025 vs Jan–Jun 2026. Main; First repricing.'
 if name=='Experiment Saved Decision':return 'EXTEND TEST'
 if name=='Experiment Complete Pairs':return 5
 if name=='Experiment One-sided p':return float(EX[(EX.simulation=='Main')&(EX.population=='First repricing')&(EX.checkpoint_months==6)&(EX.metric=='revenue_effect')].iloc[0].p_value_one_sided)
 if name.startswith('Experiment ') and ('Effect' in name or 'Harm' in name):
  mapping={'Experiment Revenue Effect':'revenue_effect','Experiment Member Harm':'member_harm','Experiment Acquisition Harm':'standard_acquisition_harm','Experiment Churn Harm':'incumbent_churn_change_pp','Experiment Downgrade Harm':'incumbent_downgrade_change_pp'}
  end='lower' if name.endswith(' lower') else 'upper' if name.endswith(' upper') else 'estimate';base=name.removesuffix(' lower').removesuffix(' upper')
  if base in mapping:return EX[(EX.simulation=='Main')&(EX.population=='First repricing')&(EX.checkpoint_months==6)&(EX.metric==mapping[base])].iloc[0][end]
 if name.startswith('Historical '):
  mapping={'Historical Standard Acquisition Effect':'controlled_acquisition_response','Historical Acquisition Elasticity':'acquisition_elasticity','Historical Incumbent Churn Effect':'incumbent_churn_response_pp','Historical Downgrade Effect':'incumbent_downgrade_response_pp'}
  end='ci_lower' if name.endswith(' lower') else 'ci_upper' if name.endswith(' upper') else 'estimate';base=name.removesuffix(' lower').removesuffix(' upper')
  if base in mapping:return HP[(HP.estimator=='paired_equal')&(HP.window=='primary_6m')&(HP.group=='All assigned pairs')&(HP.metric==mapping[base])].iloc[0][end]
 port=PORT[(PORT.variant=='base')&(PORT.case=='Base')].iloc[0]
 pm={'Portfolio Increment':'incremental_revenue','Portfolio Member Difference':'member_difference','Portfolio Increment lower':'incremental_revenue_lower','Portfolio Increment upper':'incremental_revenue_upper','Portfolio Churn':'churn_rate','Portfolio Conversion':'conversion_rate'}
 if name in pm:return port[pm[name]]
 if gym:
  gr=G.set_index('gym_id').loc[gym];rr=REC.set_index('gym_id').loc[gym];hr=HEAD.set_index('gym_id').loc[gym]
  fields={'Standard Headline December':gr.current_standard_price,'Competitor Recurring December':gr.local_competitor_avg_price,'Competitor Gap December':gr.competitor_price_gap,'Headroom Score':gr.score,'Saved Estate Rank':gr['rank'],'Headroom Band':gr.band,'Caution Count':gr.caution_flag_count,'Rank Movement Sensitivity':hr.max_absolute_rank_movement,'Saved Recommendation':rr.action,'Recommendation Explanation':rr.explanation}
  if name in fields:return fields[name]
  if name.startswith('£1 ') or name.startswith('£2 '):
   val=rr[('plus1_' if name.startswith('£1 ') else 'plus2_')+name[3:].replace(' ','_')]
   return 'None' if name.endswith('failed gates') and pd.isna(val) else val
 return None
def panel(fig,v,Ht):
 rect=[v['x']/1600,1-(v['y']+v['h'])/Ht,v['w']/1600,v['h']/Ht]
 ax=fig.add_axes(rect);ax.set_facecolor('white');ax.set_xticks([]);ax.set_yticks([])
 for sp in ax.spines.values():sp.set_visible(False)
 if v['title']:ax.text(.018,.97,v['title'],transform=ax.transAxes,va='top',fontsize=10.3,fontweight='bold',clip_on=True)
 return ax,rect
def mini_chart(fig,v,Ht):
 ax,rect=panel(fig,v,Ht)
 chart=fig.add_axes([rect[0]+.044,rect[1]+.041,rect[2]-.064,rect[3]-.084])
 chart.set_facecolor('white');chart.spines[['top','right']].set_visible(False);chart.grid(axis='y',color='#E6ECF2',linewidth=.7);chart.set_axisbelow(True);chart.tick_params(labelsize=8)
 return chart
def draw_table(ax,headers,rows,maxcols=7,maxrows=7):
 # Native tables retain all fields and scrolling. Preview shows readable leading columns.
 headers=headers[:maxcols];rows=[r[:maxcols] for r in rows[:maxrows]]
 if not rows:rows=[['—']*len(headers)]
 labels=['\n'.join(textwrap.wrap(str(x),22)) for x in headers]
 table=ax.table(cellText=rows,colLabels=labels,cellLoc='left',colLoc='left',bbox=[.015,.035,.97,.76])
 table.auto_set_font_size(False);table.set_fontsize(8)
 for (r,c),cell in table.get_celld().items():
  cell.set_linewidth(.4);cell.set_edgecolor('#E0E7EF');cell.set_facecolor('#EAF1F6' if r==0 else 'white');cell.set_text_props(color=NAVY,weight='bold' if r==0 else 'normal')
  text=cell.get_text().get_text()
  if c==0 and len(headers)==4 and r>0:cell.get_text().set_text('\n'.join(textwrap.wrap(text,18)))
  limit=max(24,int(ax.get_window_extent().width*.97/len(headers)/4.8))
  if r>0 and not(c==0 and len(headers)==4) and len(text)>limit:cell.get_text().set_text(text[:limit-1]+'…')
def table_data(v,gym):
 name=v['name'];headers=[];rows=[]
 if name in ['p01_portfolio','p03_q4','p03_pilot','p07_gates1','p07_gates2','p07_position']:
  panel={'p01_portfolio':'Executive Portfolio','p03_pilot':'Historical Pilot','p03_q4':'Q4 and Mix','p07_position':'Detail Position','p07_gates1':'Detail Qualification £1','p07_gates2':'Detail Qualification £2'}[name]
  for f in METRIC_PANELS[panel]:rows.append([f,fmt(metric(f,gym),f)])
  return ['Metric','Saved result'],rows
 if name=='p02_sites':
  d=G.sort_values('rank').head(6);return ['Gym','City','Standard','Competitor','Gap','Score','Rank'],[[x.gym_id,x.city,f'£{x.current_standard_price:.2f}',f'£{x.local_competitor_avg_price:.2f}',f'£{x.competitor_price_gap:.2f}',f'{x.score:.1f}',str(x['rank'])] for _,x in d.iterrows()]
 if name=='p04_compare':
  d=EST[EST.case=='Base'].sort_values('price_increment');return ['Increase','Net uplift','95% lower','95% upper','December members','Member impact','Exit run-rate'],[[f'£{x.price_increment:.0f}',f'£{x.incremental_revenue:,.0f}',f'£{x.incremental_revenue_lower:,.0f}',f'£{x.incremental_revenue_upper:,.0f}',f'{x.month12_members:,.0f}',f'{x.member_impact:.2%}',f'£{x.annualised_exit_run_rate:,.0f}'] for _,x in d.iterrows()]
 if name=='p04_stress':
  d=ANN[(ANN.gym_id==SINGLE)&(ANN.case=='Base')&(ANN.price_increment>0)]
  return ['Example site','Increase','Multiplier','Member impact','Crossings','Teaching ratio'],[[x.gym_id,f'£{x.price_increment:.0f}',fmt(x.break_even_response_multiplier),f'{x.break_even_member_impact:.2%}' if pd.notna(x.break_even_member_impact) else '—',fmt(x.break_even_crossings),f'{x.teaching_break_even_retention:.2%}'] for _,x in d.iterrows()]
 if name=='p05_recommendations':
  d=pd.concat([REC[REC.action=='RAISE £2'],REC[REC.action=='RAISE £1'].head(2),REC[REC.action=='TEST FIRST'].head(2),REC[REC.action=='HOLD PRICE'].head(1),REC[REC.action=='DEFENSIVE / INVESTIGATE'].head(1)])
  return ['Gym','City','Saved action','Current','Proposed','Provisional test','£1 qualified'],[[x.gym_id,x.city,x.action,f'£{x.current_standard_price:.2f}',f'£{x.proposed_standard_price:.2f}',f'£{x.provisional_test_increment:.0f}' if pd.notna(x.provisional_test_increment) else '—',fmt(x.plus1_qualified)] for _,x in d.iterrows()]
 if name=='p05_sensitivity':
  sens=load('FactPolicyRecommendation');labels=load('DimPolicy').set_index('variant').label
  return ['Saved variant','Raise £1','Raise £2','TEST FIRST','Base raise portfolio'],[[labels[v],str((sens[sens.variant==v].action=='RAISE £1').sum()),str((sens[sens.variant==v].action=='RAISE £2').sum()),str((sens[sens.variant==v].action=='TEST FIRST').sum()),f'£{PORT[(PORT.variant==v)&(PORT.case=="Base")].iloc[0].incremental_revenue:,.0f}'] for v in sens.variant.unique()]
 if name=='p06_pairs':
  d=PAIR[(PAIR.simulation=='Main')&(PAIR.population=='First repricing')&(PAIR.checkpoint_months==6)]
  return ['Pair','Revenue effect','GBP difference','Churn change pp'],[[x.pair_id,f'{np.exp(x.revenue_log)-1:.2%}',f'£{x.revenue_difference:,.0f}',f'{x.incumbent_churn_change_pp:.2f} pp'] for _,x in d.iterrows()]
 if name=='p06_harms':
  d=GUARD[(GUARD.simulation=='Main')&(GUARD.population=='First repricing')&(GUARD.checkpoint_months==6)]
  def f(v,pp):return f'{v:.2f} pp' if pp else f'{v:.2%}'
  return ['Controlled harm','Point','95% upper','Limit'],[[x.label,f(x.estimate,'_pp' in x.metric),f(x.upper,'_pp' in x.metric),f(x.tolerance,'_pp' in x.metric)] for _,x in d.iterrows()]
 if name=='p06_monitoring':
  d=MON[(MON.simulation=='Main')&(MON.population=='First repricing')&(MON.checkpoint_months==6)].head(6)
  return ['Gym','Assignment','Saved decision','Service pressure','Response'],[[x.gym_id,x.assignment,x.population_decision,fmt(x.capacity_trigger),x.required_response] for _,x in d.iterrows()]
 if name=='p06_assignment':
  d=DES[DES.eligible].sort_values(['pair_id','gym_id'],na_position='last');pairs=d[d.pair_id.notna()].drop_duplicates('pair_id');res=d[d.assignment.isna()]
  rows=[[x.pair_id,x.gym_id,x.population] for _,x in pairs.iterrows()]+[['Reserve',x.gym_id,'Unmatched'] for _,x in res.iterrows()]
  return ['Pair / reserve','Example member','Population'],rows
 if name=='p07_rationale':return ['Selected site recommendation rationale'],[[REC.set_index('gym_id').loc[gym,'explanation']]]
 return ['Saved evidence'],[['Select a site for detail']]
def render():
 pages=json.loads((P/'page_specification.json').read_text(encoding='utf-8'));review=[]
 for p in pages:
  Ht=p.get('height',1050)+48
  fig=plt.figure(figsize=(16,Ht/100),dpi=100,facecolor='#F4F7FA')
  fig.text(.018,1-.018,'DESIGN PREVIEW — NOT A NATIVE POWER BI SCREENSHOT',color=RED,fontsize=12,fontweight='bold')
  # Leave an explicit top label beyond the report canvas.
  offset=48
  gym=SINGLE if p['detail'] else None
  for original in p['visuals']:
   v={**original,'y':original['y']+offset}
   if v['type']=='textbox':
    ax,rect=panel(fig,v,Ht);ax.set_facecolor('#F4F7FA');ax.text(.01,.87,v['text'],transform=ax.transAxes,va='top',fontsize=20 if v['name'].endswith('heading') else 9,wrap=True,clip_on=True);continue
   if v['type']=='actionButton':
    ax,rect=panel(fig,{**v,'title':''},Ht);ax.set_facecolor(NAVY if p['title']==v['title'] else '#E6EDF4');ax.text(.5,.5,v['title'],ha='center',va='center',transform=ax.transAxes,fontsize=9,color='white' if p['title']==v['title'] else NAVY);continue
   if v['type']=='slicer':
    ax,rect=panel(fig,v,Ht);f=v['roles']['Values'][0][1];default={'case':'Base','variant':'Base policy','simulation':'Main','checkpoint_months':'Six-month primary','population':'First repricing','year':'2025','month_name':'All months','gym_id':gym or 'All gyms','region':'All regions','location_type':'All location types','segment':'All saved segments'}[f];ax.text(.02,.27,str(default),transform=ax.transAxes,fontsize=12,clip_on=True);ax.plot([.95,.965,.98],[.36,.26,.36],color=NAVY,transform=ax.transAxes);continue
   if v['type']=='card':
    ax,rect=panel(fig,v,Ht);name=v['roles']['Values'][0];value=fmt(metric(name,gym),name)
    size=v.get('small_font',23) if len(value)<30 else 11
    ax.text(.035,.38,'\n'.join(textwrap.wrap(value,max(26,int(v['w']/7)))),transform=ax.transAxes,fontsize=size,fontweight='bold' if size>14 else 'normal',va='center',clip_on=True);continue
   if v['type']=='tableEx':
    ax,rect=panel(fig,v,Ht);headers,rows=table_data(v,gym)
    if v['name']=='p07_rationale':ax.text(.018,.58,'\n'.join(textwrap.wrap(rows[0][0],210)),transform=ax.transAxes,fontsize=9,va='center')
    else:draw_table(ax,headers,rows,maxrows=10 if v['name']=='p03_pilot' else 8 if v['name']=='p03_q4' else 9 if v['name']=='p06_assignment' else 7)
    continue
   ax=mini_chart(fig,v,Ht);name=v['name']
   if name in ['p01_revenue','p01_members','p03_acquisition','p03_churn','p07_trading']:
    d=H if gym is None else H[H.gym_id==gym];col='monthly_revenue' if name in ['p01_revenue','p07_trading'] else 'closing_members' if name=='p01_members' else 'new_members' if name=='p03_acquisition' else 'opening_base_cancellations'
    for year,color in [(2024,BLUE),(2025,TEAL)]:
     q=d[d.month.str.startswith(str(year))].groupby('month')[col].sum();vals=q.values
     if name=='p03_churn':vals=vals/d[d.month.str.startswith(str(year))].groupby('month').opening_members.sum().values
     ax.plot(range(1,13),vals,label=str(year),color=color,lw=2)
    ax.set_xticks([1,3,6,9,12],['Jan','Mar','Jun','Sep','Dec']);ax.legend(loc='best',fontsize=8,frameon=False)
    if name=='p03_churn':ax.yaxis.set_major_formatter(PercentFormatter(1))
    elif col=='monthly_revenue':ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'£{x/1e6:.1f}m' if gym is None else f'£{x/1e3:.0f}k'))
    else:ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1000:.0f}k'))
   elif name=='p01_bridge':
    h=hist_metrics();vol=(h['Average Member Months']-h['Average Member Months Prior Year'])*h['ARPMM Prior Year'];yld=h['Average Member Months']*(h['ARPMM']-h['ARPMM Prior Year']);total=vol+yld
    ax.bar([0,1,2],[vol,yld,total],bottom=[0,vol,0],color=[RED,TEAL,NAVY],width=.55);ax.axhline(0,color=NAVY,lw=.8);ax.set_xticks([0,1,2],['Volume','Total ARPMM','Revenue change']);ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'£{x/1e6:.1f}m'))
   elif name=='p01_actions':
    counts=REC.action.value_counts().reindex(['RAISE £2','RAISE £1','TEST FIRST','HOLD PRICE','DEFENSIVE / INVESTIGATE']);ax.barh(range(5),counts,color=[TEAL,BLUE,AMBER,NAVY,RED]);ax.set_yticks(range(5),['RAISE £2','RAISE £1','TEST FIRST','HOLD','INVESTIGATE']);ax.invert_yaxis()
    for i,n in enumerate(counts):ax.text(n+.4,i,str(n),va='center',fontsize=9)
    ax.set_xlim(0,44)
   elif name=='p02_gap':
    colors={'Investigation priority':RED,'Stronger headroom indicators':TEAL,'Limited headroom indicators':NAVY,'Mixed indicators':AMBER}
    for seg,d in HEAD.groupby('segment'):ax.scatter(d.competitor_gap_dec2025,d.churn_rate_2025,c=colors[seg],s=23,label=seg,alpha=.8)
    ax.axvline(0,color='#98A8BA',ls='--');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Competitor minus Northstar (£ gross)',fontsize=9);ax.set_ylabel('Monthly churn',fontsize=9);ax.legend(fontsize=7,frameon=False,loc='best')
   elif name=='p02_band':
    vals=HEAD.band.value_counts().reindex(['High','Medium','Low']);ax.bar(['High','Medium','Low'],vals,color=[TEAL,BLUE,AMBER]);ax.set_ylabel('Gyms',fontsize=9)
   elif name in ['p04_revenue','p04_members']:
    col='cumulative_incremental_revenue' if name=='p04_revenue' else 'closing_members'
    for price,color in zip([0,1,2,3],[NAVY,BLUE,TEAL,AMBER]):
     d=SM[(SM.case=='Base')&(SM.price_increment==price)].groupby('month')[col].sum();ax.plot(range(1,13),d.values,color=color,label='No increase' if price==0 else f'+£{price}',lw=2)
    ax.set_xticks([1,3,6,9,12],['Jan','Mar','Jun','Sep','Dec']);ax.legend(fontsize=8,frameon=False)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_,money=name=='p04_revenue':f'£{x/1e6:.1f}m' if money else f'{x/1e3:.0f}k'))
   elif name.startswith('p06_') and name!='p06_power':
    history=load('FactExperimentHistory');history=history[(history.population=='First repricing')&(history.month>='2025-07-01')]
    d=pd.concat([history,EP[(EP.simulation=='Main')&(EP.population=='First repricing')&(EP.month<='2026-06-01')]],ignore_index=True)
    for arm,color in [('Treatment',TEAL),('Control',BLUE)]:
     x=d[d.assignment==arm].groupby('month');col='monthly_revenue' if name=='p06_revenue' else 'closing_members' if name=='p06_members' else 'incumbent_standard_cancellations' if name=='p06_churn_profile' else 'incumbent_standard_downgrades';val=x[col].sum()
     if name in ['p06_churn_profile','p06_downgrade_profile']:val=val/x.incumbent_standard_opening.sum()
     ax.plot(range(1,13),val.values,label=arm,color=color,lw=2)
    ax.set_xticks([1,3,6,7,8,12],['Jul 25','Sep','Dec','Jan 26','Feb','Jun']);ax.axvline(7,color=AMBER,ls='--',alpha=.7);ax.axvline(8,color=AMBER,ls=':',alpha=.7);ax.legend(fontsize=8,frameon=False)
    if name in ['p06_churn_profile','p06_downgrade_profile']:ax.yaxis.set_major_formatter(PercentFormatter(1))
    elif name=='p06_revenue':ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'£{x/1000:.0f}k'))
    else:ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1000:.0f}k'))
   elif name=='p06_power':
    d=POWER[(POWER.design=='5 first-repricing pairs')&(POWER.method=='Exact assignment Monte Carlo')].sort_values('effect_assumption');ax.plot(d.effect_assumption,d.planning_power,color=TEAL,marker='o',lw=2);ax.axhline(.8,color=AMBER,ls='--');ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0));ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0));ax.set_ylim(0,1)
  filename=('powerbi_'+p['name']+'_'+p['title'].lower().replace(' & ','_').replace(' ','_')+'.png')
  fig.savefig(OUT/filename,dpi=100,facecolor=fig.get_facecolor());plt.close(fig)
  review.append({'page':p['title'],'file':'images/'+filename,'native_screenshot':False,'source':'Validated saved reporting snapshot','preview_scope':'Default report selection; hidden detail uses '+SINGLE if p['detail'] else 'Default report selection','table_preview':'Leading rows/columns shown; native tables retain scrolling and all fields'})
 (ROOT/'analysis/powerbi_preview_manifest.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
 print('Rendered six main design previews and hidden drill-through layout, labelled non-native.')
if __name__=='__main__':render()
