import { useNavigate } from 'react-router-dom'

export default function RecentlyViewedPage() {
  const navigate = useNavigate()
  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 'none', display: 'flex', alignItems: 'center', gap: '16px', padding: '50px 22px 14px' }}>
        <div onClick={() => navigate(-1)} style={{ cursor: 'pointer' }} aria-label="Back">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M11 18l-6-6 6-6" /></svg>
        </div>
        <div style={{ fontSize: '23px', fontWeight: 600, color: '#fff' }}>Recently viewed</div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 24px 90px', gap: '14px' }}>
        <div style={{ width: '72px', height: '72px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,.05)', border: '1px solid rgba(255,255,255,.08)' }}>
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#ff539d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
        </div>
        <div style={{ fontSize: '20px', fontWeight: 600, color: '#fff' }}>No videos yet</div>
        <div style={{ fontSize: '14px', color: '#9a8f99', maxWidth: '260px' }}>Videos you open will appear here so you can pick up where you left off.</div>
      </div>
    </div>
  )
}
