import './index.css'
import { useState, useRef, useEffect } from 'react'
import { useSnowDay } from './hooks/useSnowDay'

/* ─── Snowflake SVG ──────────────────────────────── */
function Snowflake({ size = 16, opacity = 0.6, style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      style={{ opacity, flexShrink: 0, ...style }}
      aria-hidden="true">
      <line x1="12" y1="2" x2="12" y2="22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="19.07" y1="4.93" x2="4.93" y2="19.07" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="12" cy="2"  r="1.5" fill="currentColor"/>
      <circle cx="12" cy="22" r="1.5" fill="currentColor"/>
      <circle cx="2"  cy="12" r="1.5" fill="currentColor"/>
      <circle cx="22" cy="12" r="1.5" fill="currentColor"/>
    </svg>
  )
}

function SnowParticles() {
  return (
    <div className="snow-particles" aria-hidden="true">
      {Array.from({ length: 18 }).map((_, i) => (
        <div key={i} className="particle" style={{
          left: `${Math.random() * 100}%`,
          animationDelay: `${Math.random() * 8}s`,
          animationDuration: `${6 + Math.random() * 8}s`,
          fontSize: `${8 + Math.random() * 10}px`,
          opacity: 0.08 + Math.random() * 0.15,
        }}>❄</div>
      ))}
    </div>
  )
}

function ProbRing({ value, size = 140 }) {
  const r = 48
  const circ = 2 * Math.PI * r
  const dash = (value / 100) * circ
  const color = value >= 70 ? '#60a5fa' : value >= 40 ? '#818cf8' : '#475569'
  return (
    <div className="prob-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 120 120" aria-hidden="true">
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8"/>
        <circle cx="60" cy="60" r={r} fill="none"
          stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dasharray 1s ease, stroke 0.5s ease' }}
        />
      </svg>
      <div className="prob-ring__inner">
        <span className="prob-ring__number" style={{ color }}>{value}</span>
        <span className="prob-ring__pct">%</span>
      </div>
    </div>
  )
}

function WeatherPill({ icon, label, value }) {
  return (
    <div className="weather-pill">
      <span className="weather-pill__icon">{icon}</span>
      <div>
        <div className="weather-pill__label">{label}</div>
        <div className="weather-pill__value">{value}</div>
      </div>
    </div>
  )
}

function DayCard({ day, label, country }) {
  if (!day || !day.date) return null
  const prob = day.probability || 0
  const high = prob >= 70
  const med  = prob >= 40 && prob < 70
  const dateLabel = new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long', month: 'short', day: 'numeric'
  })
  return (
    <div className={`day-card ${high ? 'day-card--high' : med ? 'day-card--med' : 'day-card--low'}`}>
      <div className="day-card__header">
        <div>
          <div className="day-card__tag">{label}</div>
          <div className="day-card__date">{dateLabel}</div>
        </div>
        <ProbRing value={prob} size={110} />
      </div>
      <div className="day-card__label">{day.label}</div>
      <div className="day-card__pills">
        <WeatherPill icon="🌨" label="Snowfall"
          value={country === 'US' ? `${day.snow_amount ?? 0}" inches` : `${day.snow_amount ?? 0} cm`} />
        <WeatherPill icon="🌡" label="Temperature"
          value={`${day.temperature ?? '--'}${day.unit_temp ?? '°F'}`} />
        <WeatherPill icon="💨" label="Wind"
          value={day.breakdown?.wind_score > 0 ? 'Strong winds' : 'Calm'} />
        <WeatherPill icon="📋" label="Forecast" value={day.short_forecast || 'N/A'} />
      </div>
    </div>
  )
}

function CalculatorForm({ onSubmit, loading }) {
  const [zip, setZip]           = useState('')
  const [snowDays, setSnowDays] = useState('0')
  const [school, setSchool]     = useState('public')
  const inputRef                = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!zip.trim()) return
    onSubmit({ zipCode: zip.trim(), snowDaysThisYear: snowDays, schoolType: school })
  }

  return (
    <form className="calc-form" onSubmit={handleSubmit} noValidate>
      <div className="calc-form__row">
        <div className="field">
          <label className="field__label" htmlFor="zip">ZIP or Postal Code</label>
          <div className="field__hint">US: 10001 &nbsp;·&nbsp; Canada: K1A 0A6</div>
          <input
            ref={inputRef} id="zip" className="field__input" type="text"
            value={zip} onChange={e => setZip(e.target.value)}
            placeholder="e.g. 10001 or K1A0A6" maxLength={7}
            autoComplete="postal-code" inputMode="text" required
            aria-label="Enter your ZIP or postal code"
          />
        </div>
        <div className="field field--sm">
          <label className="field__label" htmlFor="snowdays">Snow Days This Year</label>
          <div className="field__hint">Already used</div>
          <input
            id="snowdays" className="field__input" type="number"
            value={snowDays} onChange={e => setSnowDays(e.target.value)}
            min="0" max="20" inputMode="numeric"
            aria-label="Snow days already used this school year"
          />
        </div>
      </div>
      <div className="field">
        <label className="field__label" htmlFor="school">Type of School</label>
        <div className="field__hint">Affects how likely a closure is called</div>
        <select id="school" className="field__select" value={school}
          onChange={e => setSchool(e.target.value)} aria-label="Select school type">
          <option value="public">Public</option>
          <option value="urban_public">Urban Public</option>
          <option value="rural_public">Rural Public</option>
          <option value="private">Private / Prep</option>
          <option value="boarding">Boarding School</option>
        </select>
      </div>
      <button type="submit"
        className={`calc-btn ${loading ? 'calc-btn--loading' : ''}`}
        disabled={loading || !zip.trim()}
        aria-label="Calculate snow day probability">
        {loading
          ? <><span className="spinner" aria-hidden="true" /> Checking weather…</>
          : <><Snowflake size={18} opacity={1} /> Calculate</>
        }
      </button>
    </form>
  )
}

export default function App() {
  const { data, loading, error, predict } = useSnowDay()
  const resultsRef = useRef(null)

  useEffect(() => {
    if (data && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
  }, [data])

  return (
    <div className="app">
      <SnowParticles />

      <header className="header">
        <div className="header__logo">
          <Snowflake size={22} opacity={1} style={{ color: 'var(--blue)' }} />
        </div>
        <nav className="header__nav" aria-label="Site navigation">
          <a href="#how" className="nav-link">How it works</a>
          <a href="#faq" className="nav-link">FAQ</a>
        </nav>
      </header>

      <main className="main">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero__eyebrow">
            <Snowflake size={13} opacity={1} />
            <span>US &amp; Canada</span>
          </div>
          <h1 id="hero-title" className="hero__title">
            Snow Day<br />
            <span className="hero__title--accent">Calculator</span>
          </h1>
          <p className="hero__sub">
            Weather-powered prediction for US &amp; Canadian schools.<br className="br-md" />
            Updated daily using Weather.gov &amp; Environment Canada.
          </p>
        </section>

        <section className="card-wrap" aria-label="Snow day calculator">
          <div className="card">
            <div className="card__header">
              <h2 className="card__title">Get Your Prediction</h2>
              <div className="card__badge">Free · No sign-up</div>
            </div>
            <CalculatorForm onSubmit={predict} loading={loading} />
            {error && (
              <div className="alert alert--error" role="alert" aria-live="polite">
                <span>⚠</span> {error}
              </div>
            )}
          </div>
        </section>

        {data && (
          <section ref={resultsRef} className="results" aria-live="polite" aria-label="Prediction results">
            <div className="results__location">
              <Snowflake size={14} opacity={0.7} style={{ color: 'var(--blue)' }} />
              <span>{data.city}{data.region ? `, ${data.region}` : ''}</span>
              <span className="results__country">{data.country}</span>
            </div>
            <div className="results__grid">
              <DayCard day={data.tomorrow}  label="Tomorrow"           country={data.country} />
              <DayCard day={data.day_after} label="Day After Tomorrow" country={data.country} />
            </div>
            <p className="results__source">
              Data from {data.country === 'US' ? 'Weather.gov' : 'Environment Canada'} ·
              Predictions updated at noon daily
            </p>
          </section>
        )}

        <section id="how" className="info-section" aria-labelledby="how-title">
          <h2 id="how-title" className="section-title">How It Works</h2>
          <div className="steps">
            {[
              { n: '01', title: 'Enter Location',  desc: 'Type your US ZIP or Canadian postal code.' },
              { n: '02', title: 'Live Weather',     desc: 'We fetch the latest forecast from official government APIs.' },
              { n: '03', title: 'Smart Prediction', desc: 'Snow amount, temperature, wind, and your school type are all factored in.' },
              { n: '04', title: 'Instant Result',   desc: 'Get a probability score for the next two school days.' },
            ].map(s => (
              <div key={s.n} className="step">
                <div className="step__num">{s.n}</div>
                <div>
                  <div className="step__title">{s.title}</div>
                  <div className="step__desc">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section id="faq" className="info-section" aria-labelledby="faq-title">
          <h2 id="faq-title" className="section-title">FAQ</h2>
          <div className="faqs">
            {[
              { q: 'Is this free?',             a: 'Yes — completely free. No account needed.' },
              { q: 'Does it work for Canada?',  a: 'Yes! Enter your postal code (e.g. K1A 0A6). We support all provinces.' },
              { q: 'How accurate is it?',       a: 'We use official government weather data. The prediction also accounts for school type and days already used this year.' },
              { q: 'When does it update?',      a: 'Forecasts refresh every day at noon, matching when most school boards decide closures.' },
            ].map((f, i) => (
              <details key={i} className="faq">
                <summary className="faq__q">{f.q}</summary>
                <p className="faq__a">{f.a}</p>
              </details>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="footer__snow">
          <Snowflake size={16} opacity={0.4} style={{ color: 'var(--blue)' }} />
        </div>
        <p>Snow Day Calculator &copy; {new Date().getFullYear()}</p>
        <p className="footer__sub">Data from Weather.gov &amp; Environment Canada · Not affiliated with any school board</p>
      </footer>

      <style>{appStyles}</style>
    </div>
  )
}

const appStyles = `
.snow-particles { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.particle { position: absolute; top: -20px; color: #fff; animation: fall linear infinite; will-change: transform; }
@keyframes fall { to { transform: translateY(110vh) rotate(360deg); } }
.app { position: relative; min-height: 100vh; display: flex; flex-direction: column; }
.header { position: sticky; top: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(1rem, 5vw, 3rem); height: 60px; background: rgba(10,15,30,0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border-bottom: 1px solid var(--border); }
.header__logo { color: var(--blue); display: flex; align-items: center; }
.header__nav { display: flex; gap: 1.5rem; }
.nav-link { color: var(--text-2); font-size: 0.875rem; text-decoration: none; transition: color var(--t-fast); }
.nav-link:hover { color: var(--text-1); }
.main { flex: 1; width: 100%; max-width: 900px; margin: 0 auto; padding: clamp(2rem, 6vw, 4rem) clamp(1rem, 5vw, 2rem); display: flex; flex-direction: column; gap: clamp(2.5rem, 6vw, 4rem); position: relative; z-index: 1; }
.hero { text-align: center; }
.hero__eyebrow { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--blue); font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 1rem; }
.hero__title { font-family: var(--font-display); font-size: clamp(2.8rem, 8vw, 6rem); font-weight: 800; line-height: 1.0; color: var(--text-1); letter-spacing: -0.02em; margin-bottom: 1.25rem; }
.hero__title--accent { background: linear-gradient(135deg, var(--blue), var(--cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero__sub { color: var(--text-2); font-size: clamp(0.95rem, 2.5vw, 1.1rem); line-height: 1.7; max-width: 520px; margin: 0 auto; }
.br-md { display: none; }
@media (min-width: 600px) { .br-md { display: block; } }
.card-wrap { width: 100%; }
.card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: clamp(1.5rem, 4vw, 2.5rem); box-shadow: var(--shadow-md), var(--shadow-glow); }
.card__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.75rem; flex-wrap: wrap; gap: 0.5rem; }
.card__title { font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: var(--text-1); }
.card__badge { font-size: 0.75rem; padding: 0.3rem 0.8rem; background: rgba(96,165,250,0.1); color: var(--blue); border: 1px solid rgba(96,165,250,0.2); border-radius: var(--r-full); }
.calc-form { display: flex; flex-direction: column; gap: 1.25rem; }
.calc-form__row { display: grid; grid-template-columns: 1fr; gap: 1.25rem; }
@media (min-width: 520px) { .calc-form__row { grid-template-columns: 1fr 160px; } }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field__label { font-size: 0.85rem; font-weight: 500; color: var(--text-1); }
.field__hint { font-size: 0.75rem; color: var(--text-3); }
.field__input, .field__select { background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: var(--r-md); padding: 0.75rem 1rem; color: var(--text-1); font-size: 1rem; transition: border-color var(--t-fast), box-shadow var(--t-fast); width: 100%; height: 50px; }
.field__input:focus, .field__select:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px rgba(96,165,250,0.15); }
.field__select { -webkit-appearance: none; appearance: none; cursor: pointer; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238b9fc4' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 1rem center; padding-right: 2.5rem; }
.field__select option { background: #1e293b; }
.calc-btn { display: flex; align-items: center; justify-content: center; gap: 0.6rem; background: linear-gradient(135deg, var(--blue-dark), #2563eb); color: #fff; border: none; border-radius: var(--r-md); padding: 0.9rem 2rem; font-size: 1rem; font-weight: 500; cursor: pointer; transition: transform var(--t-fast), box-shadow var(--t-fast), opacity var(--t-fast); box-shadow: 0 4px 20px rgba(37,99,235,0.4); height: 52px; width: 100%; }
.calc-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(37,99,235,0.5); }
.calc-btn:active:not(:disabled) { transform: translateY(0); }
.calc-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.calc-btn--loading { opacity: 0.8; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.alert { display: flex; align-items: flex-start; gap: 0.6rem; padding: 0.875rem 1rem; border-radius: var(--r-md); font-size: 0.9rem; margin-top: 0.5rem; }
.alert--error { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.25); color: #fca5a5; }
.results { display: flex; flex-direction: column; gap: 1.25rem; scroll-margin-top: 80px; }
.results__location { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: var(--text-2); }
.results__country { margin-left: 0.25rem; font-size: 0.75rem; padding: 0.2rem 0.6rem; background: rgba(96,165,250,0.1); color: var(--blue); border-radius: var(--r-full); font-weight: 500; }
.results__grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 640px) { .results__grid { grid-template-columns: 1fr 1fr; } }
.results__source { font-size: 0.75rem; color: var(--text-3); text-align: center; }
.day-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 1.5rem; transition: transform var(--t-mid), box-shadow var(--t-mid); animation: slideUp 0.4s ease both; }
.day-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.day-card--high { border-color: rgba(96,165,250,0.25); box-shadow: 0 0 30px rgba(96,165,250,0.08); }
.day-card--med { border-color: rgba(129,140,248,0.2); }
.day-card--low { border-color: var(--border); }
@keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
.day-card__header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1rem; }
.day-card__tag { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--blue); margin-bottom: 0.3rem; }
.day-card__date { font-size: 0.95rem; font-weight: 500; color: var(--text-1); }
.day-card__label { font-size: 0.9rem; color: var(--text-2); margin-bottom: 1.25rem; }
.prob-ring { position: relative; flex-shrink: 0; }
.prob-ring__inner { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 1px; }
.prob-ring__number { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; line-height: 1; }
.prob-ring__pct { font-size: 0.75rem; font-weight: 600; color: var(--text-2); align-self: flex-end; margin-bottom: 4px; }
.day-card__pills { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.weather-pill { display: flex; align-items: center; gap: 0.6rem; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: var(--r-sm); padding: 0.6rem 0.75rem; }
.weather-pill__icon { font-size: 1.1rem; flex-shrink: 0; }
.weather-pill__label { font-size: 0.68rem; color: var(--text-3); line-height: 1; margin-bottom: 0.15rem; }
.weather-pill__value { font-size: 0.82rem; color: var(--text-1); font-weight: 500; line-height: 1; }
.info-section { display: flex; flex-direction: column; gap: 1.5rem; }
.section-title { font-family: var(--font-display); font-size: clamp(1.4rem, 4vw, 2rem); font-weight: 800; color: var(--text-1); letter-spacing: -0.01em; }
.steps { display: flex; flex-direction: column; gap: 1rem; }
.step { display: flex; align-items: flex-start; gap: 1.25rem; padding: 1.25rem; border-radius: var(--r-md); background: var(--bg-card); border: 1px solid var(--border); }
.step__num { font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: rgba(96,165,250,0.25); line-height: 1; flex-shrink: 0; width: 2rem; }
.step__title { font-weight: 500; color: var(--text-1); margin-bottom: 0.25rem; }
.step__desc { font-size: 0.875rem; color: var(--text-2); }
@media (min-width: 640px) { .steps { display: grid; grid-template-columns: 1fr 1fr; } }
.faqs { display: flex; flex-direction: column; gap: 0.75rem; }
.faq { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); overflow: hidden; }
.faq__q { padding: 1rem 1.25rem; cursor: pointer; font-weight: 500; color: var(--text-1); font-size: 0.95rem; list-style: none; display: flex; align-items: center; justify-content: space-between; transition: background var(--t-fast); }
.faq__q:hover { background: rgba(255,255,255,0.02); }
.faq__q::after { content: '+'; color: var(--blue); font-size: 1.2rem; }
details[open] .faq__q::after { content: '−'; }
.faq__a { padding: 0.75rem 1.25rem 1rem; color: var(--text-2); font-size: 0.875rem; line-height: 1.7; border-top: 1px solid var(--border); }
.footer { text-align: center; padding: 2.5rem 1.5rem; border-top: 1px solid var(--border); color: var(--text-3); font-size: 0.8rem; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; position: relative; z-index: 1; }
.footer__snow { margin-bottom: 0.25rem; }
.footer__sub { font-size: 0.73rem; }
@media (min-width: 768px) and (max-width: 1024px) { .main { max-width: 700px; } .hero__title { font-size: clamp(3rem, 7vw, 5rem); } }
@media (min-width: 1024px) { .hero__sub { font-size: 1.1rem; } .card { padding: 2.5rem; } }
@media (prefers-reduced-motion: reduce) { .particle, .spinner { animation: none; } .day-card { animation: none; } * { transition-duration: 0.01ms !important; } }
`
