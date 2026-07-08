import * as React from 'react'
import { useTranslation } from 'react-i18next'
import * as NoxxVM from '@/shared/noxx/useNoxx'

export default function TermsPage() {
  const { t } = useTranslation()
  const { showTerms, backProfile, termsSections } = NoxxVM.useNoxx()
  return (
    <>
{(showTerms) && (<>
    <div data-screen-label="Terms" style={{"position": "absolute", "inset": "0", "display": "flex", "flexDirection": "column"}}>
      <div style={{"flex": "none", "display": "flex", "alignItems": "center", "gap": "16px", "padding": "16px 22px 14px"}}><div onClick={backProfile} style={{"cursor": "pointer"}}><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg></div><div style={{"fontSize": "23px", "fontWeight": "600", "color": "#fff"}}>{t('termsPageTitle')}</div></div>
      <div style={{"flex": "1", "overflowY": "auto", "padding": "14px 24px 40px"}}>
        {(termsSections||[]).map((t, _k0: number) => (<React.Fragment key={_k0}>
          <div style={{"marginBottom": "26px"}}><div style={{"fontSize": "18px", "fontWeight": "600", "color": "#fff", "marginBottom": "8px"}}>{t.head}</div><div style={{"fontSize": "15px", "lineHeight": "1.6", "color": "#9a9098", "textWrap": "pretty"}}>{t.body}</div></div>
        </React.Fragment>))}
        <div style={{"fontSize": "13.5px", "color": "#6a616b", "marginTop": "10px"}}>{t('termsLastUpdated')}</div>
      </div>
    </div>
    </>)}
    </>
  )
}
