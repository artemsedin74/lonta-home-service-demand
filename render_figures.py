"""Standalone source-backed research figures, with population/window/uncertainty notes."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


def render(data,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=data['categories']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    blue,dark='#355ce4','#202433'
    foot='Lonta Research • 2023 AHS, DataLumos V2 archival copy • US occupied owner homes\nProjects in preceding 24 months at the 2023 interview. Historical reported work; not current prices, revenue or ad-attributed sales.'
    names=[]
    def save(fig,ax,name,note):
        ax.set_axisbelow(True);ax.grid(axis='x',color='#e4e7ef',linewidth=.7)
        fig.subplots_adjust(left=.31,right=.96,top=.82,bottom=.24)
        fig.text(.035,.055,foot+'\n'+note,fontsize=8.3,color='#50596a',va='bottom')
        fig.savefig(out/(name+'.png'),dpi=180)
        p=out/(name+'.svg');fig.savefig(p)
        p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
        names.append(name);plt.close(fig)

    ordered=sorted(rows,key=lambda r:r['frequency_per1000']['estimate'])
    fig,ax=plt.subplots(figsize=(11,7))
    x=np.array([r['frequency_per1000']['estimate'] for r in ordered]);y=np.arange(len(rows))
    e=np.array([[r['frequency_per1000']['estimate']-r['frequency_per1000']['lower'] for r in ordered],
                [r['frequency_per1000']['upper']-r['frequency_per1000']['estimate'] for r in ordered]])
    ax.barh(y,x,color=blue,height=.55);ax.errorbar(x,y,xerr=e,fmt='none',color=dark,capsize=3,lw=1.1)
    ax.set_yticks(y,[r['label'] for r in ordered]);ax.set_xlim(0,float((x+e[1]).max())*1.23)
    ax.set_xlabel('Homes with ≥1 professional-category project per 1,000 owner homes')
    ax.set_title('How often was each project category reported?',loc='left',pad=26,fontweight='bold')
    for i,r in enumerate(ordered):ax.text(r['frequency_per1000']['upper']+1,i,f"{r['frequency_per1000']['estimate']:.1f}",va='center',fontsize=10)
    save(fig,ax,'01-project-frequency','Bounds: pointwise 90% Fay BRR normal intervals. All owner homes, including no-project homes. Categories overlap.\nProfessional = most work outside household; not verified paid invoices.')

    fig,ax=plt.subplots(figsize=(11,7))
    for key,label,marker,color,offset in [('professional_project_share_pct','Share of projects','o',blue,-.13),
                                         ('professional_spending_share_pct','Share of reported spending','s',dark,.13)]:
        x=[r[key]['estimate'] for r in rows];y=np.arange(len(rows))+offset
        e=np.array([[r[key]['estimate']-r[key]['lower'] for r in rows],[r[key]['upper']-r[key]['estimate'] for r in rows]])
        ax.errorbar(x,y,xerr=e,fmt=marker,color=color,capsize=2,label=label,lw=1,markersize=5)
    ax.set_yticks(np.arange(len(rows)),[r['label'] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,105)
    ax.set_xlabel('Professional-category share (%) • distinct count and spending denominators')
    ax.set_title('A project share is not a spending share',loc='left',pad=28,fontweight='bold')
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,frameon=False,fontsize=9)
    save(fig,ax,'02-project-spending-shares','Bounds: pointwise 90% Fay BRR normal intervals. Professional = most work outside household; not verified paid invoices.')

    fig,ax=plt.subplots(figsize=(11,7))
    for i,r in enumerate(rows):
        ax.plot([r['q1_cost']['estimate'],r['q3_cost']['estimate']],[i,i],color=blue,lw=4,solid_capstyle='butt')
        ax.plot(r['median_cost']['estimate'],i,'o',color=dark,markersize=6)
        ax.text(r['q3_cost']['estimate']+150,i,f"median ${r['median_cost']['estimate']:,.0f}",va='center',fontsize=9)
    ax.set_yticks(np.arange(len(rows)),[r['label'] for r in rows]);ax.invert_yaxis()
    ax.set_xlim(0,max(r['q3_cost']['estimate'] for r in rows)*1.37)
    ax.xaxis.set_major_formatter(StrMethodFormatter('${x:,.0f}'))
    ax.set_xlabel('Nominal reported cost • line=weighted 25th–75th percentiles; dot=median')
    ax.set_title('Reported costs of professional-category projects',loc='left',pad=25,fontweight='bold')
    save(fig,ax,'03-cost-distributions','Scope: professional-category projects; most work outside household, not verified paid invoices.\nSpans describe distribution spread, not confidence intervals. Known zero included; unknown costs excluded. Different job scopes.')

    fig,ax=plt.subplots(figsize=(11,7))
    for group,label,marker,color,offset in [('pre_1980','Pre-1980','o',dark,-.2),('1980_1999','1980–1999','s',blue,0),
                                          ('2000_or_later','2000+','^','#a8791e',.2)]:
        for i,r in enumerate(rows):
            v=next(v for v in data['vintage'] if v['code']==r['code'] and v['vintage']==group)
            if v['suppressed']:
                continue
            ax.errorbar(v['estimate'],i+offset,xerr=[[v['estimate']-v['lower']],[v['upper']-v['estimate']]],
                        fmt=marker,color=color,capsize=2,lw=1,markersize=4,label=label if i==0 else None)
    ax.set_yticks(np.arange(len(rows)),[r['label'] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,105)
    ax.set_xlabel('Homes with ≥1 professional-category project per 1,000 homes in each vintage group')
    ax.set_title('The home-age pattern differs by service',loc='left',pad=30,fontweight='bold')
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=3,frameon=False,fontsize=9)
    save(fig,ax,'04-home-vintage','Raw descriptive rates; pointwise 90% Fay BRR intervals. Septic 2000+ suppressed below 30 events. Equipment stock not controlled.\nProfessional = most work outside household; not verified paid invoices.')
    return names
