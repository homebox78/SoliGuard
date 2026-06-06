/* ============================================================
   SoliGuard — App icon (crimson shield), used everywhere
   ============================================================ */

function AppIcon({ size = 48, radius, glow = true }) {
  const r = radius != null ? radius : Math.round(size * 0.23);
  return (
    <div style={{ width: size, height: size, borderRadius: r, position: 'relative', overflow: 'hidden',
      background: 'linear-gradient(152deg, #C7164A 0%, #B0123F 42%, #7E0C30 100%)',
      boxShadow: glow ? `0 ${size * 0.06}px ${size * 0.2}px rgba(150,16,55,.42)` : 'none',
      display: 'grid', placeItems: 'center' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(120% 90% at 28% 16%, rgba(255,255,255,.28), transparent 58%)' }} />
      <div style={{ position: 'absolute', left: '-12%', bottom: '-30%', width: '90%', height: '90%', borderRadius: '50%', background: 'rgba(0,0,0,.10)' }} />
      <Icon name="shieldCheck" size={Math.round(size * 0.56)} stroke={2.1} style={{ color: '#fff', position: 'relative', filter: 'drop-shadow(0 1px 1px rgba(0,0,0,.18))' }} />
    </div>
  );
}

/* installer .exe icon — app icon with a small download badge */
function SetupIcon({ size = 48 }) {
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <AppIcon size={size} />
      <span style={{ position: 'absolute', right: -3, bottom: -3, width: size * 0.42, height: size * 0.42, borderRadius: '50%',
        background: '#fff', display: 'grid', placeItems: 'center', boxShadow: '0 1px 4px rgba(0,0,0,.25)' }}>
        <Icon name="download" size={size * 0.26} stroke={2.6} style={{ color: 'var(--brand)' }} />
      </span>
    </div>
  );
}

/* solideo-style wordmark lockup */
function Wordmark({ light }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <AppIcon size={34} glow={!light} />
      <div>
        <div style={{ fontWeight: 800, fontSize: 16, letterSpacing: '-.02em', color: light ? '#fff' : 'var(--text)' }}>
          솔리<span style={{ color: light ? '#fff' : 'var(--brand)' }}>가드</span>
        </div>
        <div style={{ fontSize: 10.5, color: light ? 'rgba(255,255,255,.7)' : 'var(--text-3)', letterSpacing: '.02em' }}>SoliGuard · solideo</div>
      </div>
    </div>
  );
}

Object.assign(window, { AppIcon, SetupIcon, Wordmark });
