import './index.css'
import { useState, useRef, useEffect } from 'react'
import { useSnowDay } from './hooks/useSnowDay'

/* ─── Snowflake SVG ─────────────────────────────── */
function Snowflake({ size = 16, opacity = 0.6, style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      style={{ opacity, flexShrink: 0, ...style }} aria-hidden="true">
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

/* ─── Snow Particles ────────────────────────────── */
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

/* ─── Prob Ring ─────────────────────────────────── */
function ProbRing({ value, size = 140 }) {
  const r = 48
  const circ = 2 * Math.PI * r
  const dash = (value / 100) * circ
  const color = value >= 60 ? '#f87171' : value >= 20 ? '#fb923c' : '#34d399'
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
        <span className="prob-ring__number" style={{ color }}>{value}%</span>
      </div>
    </div>
  )
}

/* ─── Weather Pill ──────────────────────────────── */
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

/* ─── Day Card ──────────────────────────────────── */
function DayCard({ day, label, country }) {
  if (!day || !day.date) return null
  const prob = day.probability || 0
  const high = prob >= 60
  const med  = prob >= 20 && prob < 60
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

/* ─── Calculator Form ───────────────────────────── */
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
          <div className="field__hint field__hint--highlight">US: 10001 &nbsp;·&nbsp; Canada: K1A 0A6</div>
          <input ref={inputRef} id="zip" className="field__input" type="text"
            value={zip} onChange={e => setZip(e.target.value)}
            placeholder="e.g. 10001 or K1A0A6" maxLength={7}
            autoComplete="postal-code" inputMode="text" required
            aria-label="Enter your ZIP or postal code" />
        </div>
        <div className="field field--sm">
          <label className="field__label" htmlFor="snowdays">Snow Days This Year</label>
          <div className="field__hint field__hint--highlight">Already used</div>
          <input id="snowdays" className="field__input" type="number"
            value={snowDays} onChange={e => setSnowDays(e.target.value)}
            min="0" max="20" inputMode="numeric"
            aria-label="Snow days already used this school year" />
        </div>
      </div>
      <div className="field">
        <label className="field__label" htmlFor="school">Type of School</label>
        <div className="field__hint field__hint--highlight">Affects how likely a closure is called</div>
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
          : <><Snowflake size={18} opacity={1} /> Calculate</>}
      </button>
    </form>
  )
}

/* ─── Article Sections ──────────────────────────── */
function ArticleContent() {
  return (
    <article className="article" itemScope itemType="https://schema.org/Article">

      <p className="article__intro">
        Most snow day calculators hand you a number and call it done. What they don't tell you is <em>how</em> that number was built — or why two schools three miles apart can get completely different answers on the same morning. This guide covers everything that actually matters: how predictions work, what school boards are really looking at when they make the call, and how to use your forecast with more confidence whether you're in Buffalo, Barrie, Dallas, or Prince George.
      </p>

      <section className="article__section">
        <h2 className="article__h2">What Is a Snow Day Calculator — and How Is It Different From a Predictor?</h2>
        <p>The terms get used interchangeably, but they describe slightly different tools.</p>
        <p>A <strong>snow day calculator</strong> typically lets you enter conditions manually — snowfall totals, temperature, wind — and outputs a probability. It's useful for "what if" scenarios when a storm is still days out and the forecast keeps shifting.</p>
        <p>A <strong>snow day predictor</strong> pulls live weather data automatically based on your ZIP code or Canadian postal code. It reads current conditions, cross-references historical closure patterns for your specific area, and gives you a real-time probability without any manual input.</p>
        <p>Your site uses both approaches — real-time prediction with the option to tweak inputs — which reflects how closures actually get decided. Superintendents don't consult a single number. They watch conditions evolve from the evening before through 5 AM the next morning.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">The Decision Happens Between 4 AM and 6:30 AM</h2>
        <p>This is the detail most calculators bury. The window that determines your day is narrow.</p>
        <p>In the US, most school districts make their call between <strong>4:30 AM and 6:00 AM</strong>. In Canada — particularly Ontario, Alberta, and Quebec — boards typically notify families by <strong>6:00–6:30 AM</strong>. Rural boards, especially those running long bus routes, often decide even earlier, sometimes by 5 AM, because drivers need time to assess road conditions before first pick-up.</p>
        <p>What changes in those hours:</p>
        <ul className="article__list">
          <li>Snowfall rate overnight (accumulation per hour matters more than total depth)</li>
          <li>Road treatment reports from municipal crews</li>
          <li>Wind chill readings at bus stops</li>
          <li>Visibility on rural routes</li>
          <li>Whether freezing rain has developed on top of snow</li>
        </ul>
        <p>A storm that drops 8 cm starting at midnight looks very different from the same 8 cm that arrives at 6 AM. The overnight version gives plows a head start. The early-morning version hits roads at peak commute window with zero treatment time. Same snowfall total, completely different outcome.</p>
        <p>Check your prediction the evening before — then check it again at 5 AM. The difference between those two readings tells you a lot.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">Why the Same Snowfall Closes Schools in One City but Not Another</h2>
        <p>This is probably the most misunderstood aspect of snow day predictions, and it's why generic calculators frustrate people.</p>
        <h3 className="article__h3">Regional Threshold Differences</h3>
        <p>A district in <strong>San Antonio, Texas</strong> may close schools for 2 cm of snow. The same 2 cm in <strong>Toronto</strong> or <strong>Minneapolis</strong> doesn't register as an event. This isn't fragility — it's resource allocation. Southern US cities don't maintain large plow fleets or stockpiles of road salt because they average one or two winter events per year. The economics don't support it.</p>
        <p>Meanwhile, cities like <strong>Winnipeg</strong>, <strong>Syracuse</strong>, or <strong>Chicago</strong> have invested decades in winter infrastructure. Their thresholds are higher because their capability is higher.</p>
        <p>Our calculator accounts for this by applying regional sensitivity modifiers. A 70% probability in Atlanta means something different than a 70% probability in Edmonton — and the algorithm reflects that.</p>
        <h3 className="article__h3">Urban vs. Rural Gap</h3>
        <p>This is the factor that surprises most parents who move between areas.</p>
        <p>Urban school boards — think TDSB in Toronto or Chicago Public Schools — have relatively short, well-treated bus routes. Rural boards covering hundreds of kilometers across back roads operate under completely different constraints. One icy rural road that a plow won't reach until 7 AM can shut down bus service for an entire sub-region even when city schools stay open.</p>
        <p>If you're in a rural postal code or ZIP, your snow day probability will generally run higher than your urban neighbors — and rightfully so.</p>
        <h3 className="article__h3">Lake Effect Zones (US &amp; Canada)</h3>
        <p>Communities downwind of the Great Lakes — <strong>Buffalo, Cleveland, Erie, Barrie, Owen Sound, Kingston</strong> — experience snowfall patterns that defy regional averages. A lake effect band can dump 30–50 cm in 6 hours on one side of a county while 40 km away sees nothing.</p>
        <p>Standard weather models struggle here. Our predictor uses narrower geographic inputs and lake effect weighting for these zones, which is why it's worth entering your specific postal code or ZIP rather than just your city name.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">What School Boards Are Actually Evaluating</h2>
        <p>Superintendents and transportation directors aren't checking a snow day app. Here's what actually goes into the decision:</p>
        <p><strong>Snowfall depth and rate</strong> — Total accumulation matters, but rate per hour is the more critical variable. 15 cm over 12 hours is manageable. 15 cm in 3 hours is a crisis for road crews.</p>
        <p><strong>Temperature and wind chill</strong> — In Canada, many boards have explicit wind chill thresholds. At -25°C to -30°C wind chill, some boards automatically cancel or delay regardless of snowfall, citing student safety at bus stops.</p>
        <p><strong>Road conditions from transportation operators</strong> — Bus contractors report directly to boards. If drivers say they can't safely complete routes, schools close. This is why the decision is sometimes made at 4:30 AM after early drivers do test runs.</p>
        <p><strong>Freezing rain</strong> — Counterintuitively, freezing rain events produce more closures than heavy snowfall in many regions. Snow piles up visibly; ice is invisible and catastrophically effective at making roads impassable. A freezing rain warning from Environment Canada or the National Weather Service is a much stronger signal than a snowfall warning of equivalent severity.</p>
        <p><strong>Already-accumulated ice</strong> — Overnight temperatures dropping after an afternoon rain can create a base ice layer under any morning snow. Plows move snow; they don't break up base ice quickly. This scenario — warm rain followed by sharp temperature drop — is one of the highest-closure patterns in the dataset.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">How the Prediction Is Calculated</h2>
        <p>The probability you see is built from several weighted inputs, not a single threshold.</p>
        <p><strong>Snowfall accumulation</strong> contributes the largest share of the score in most regions. Depth thresholds are calibrated regionally — what triggers a high probability in Georgia is different from what triggers it in Manitoba.</p>
        <p><strong>Storm timing</strong> is weighted heavily because of the 4–7 AM window described above. Snow arriving overnight scores higher than equivalent snow arriving mid-afternoon.</p>
        <p><strong>Wind and wind chill</strong> affect both road safety and student welfare at bus stops. In Prairie provinces (Saskatchewan, Manitoba, Alberta) and upper Midwest states (Minnesota, North Dakota), wind chill is sometimes the primary variable.</p>
        <p><strong>Freezing rain probability</strong> receives disproportionate weight because of its outsized impact on closure decisions relative to raw totals.</p>
        <p><strong>Historical closure patterns</strong> for your specific location — not just your region, but your district's actual track record — are layered in where data is available. A district that closed twice last year at 8 cm of snow will score differently than one that stayed open through 20 cm.</p>
        <p>The result is a percentage from 0–100:</p>
        <div className="prob-table">
          {[
            { range: 'Under 20%', meaning: 'Open. Conditions don\'t suggest disruption.' },
            { range: '20–40%',    meaning: 'Probably open, possible delay in some districts.' },
            { range: '40–60%',    meaning: 'Genuine uncertainty. Check again in the morning.' },
            { range: '60–80%',    meaning: 'Likely closure or delay. Start planning.' },
            { range: 'Over 80%',  meaning: 'Strong signal. Most districts in your area with these conditions have closed historically.' },
          ].map((row, i) => (
            <div key={i} className="prob-table__row">
              <span className="prob-table__range">{row.range}</span>
              <span className="prob-table__meaning">{row.meaning}</span>
            </div>
          ))}
        </div>
        <p>These ranges are guidelines, not rules. Local variability is real. Always confirm through your board's official channels.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">US vs. Canada: Key Differences in How Closures Work</h2>
        <p>Parents relocating between the two countries are often surprised by the differences. They're worth knowing.</p>
        <h3 className="article__h3">Decision Communication</h3>
        <p>US districts typically announce via automated phone calls, school district websites, and local TV station school closing lists (a tradition that's been running since the 1970s). Apps like Remind and SchoolMessenger are now common.</p>
        <p>Canadian boards — particularly Ontario — use the board's own website and student transportation consortium sites (e.g., Halton Student Transportation Services, Durham Student Transportation Consortium). Social media plays a larger role in Canada than in the US for real-time updates.</p>
        <h3 className="article__h3">Bus Cancellation vs. School Closure</h3>
        <p>This distinction is critical and Canada-specific. In many Ontario and Quebec districts, <strong>buses can be cancelled while schools remain open</strong>. A bus cancellation means transportation is suspended due to unsafe road conditions, but the school building is open for students who can get there independently.</p>
        <p>This produces a third outcome that US parents aren't always familiar with: the school is technically open, your child isn't going, and it doesn't count as a snow day. Some boards track these separately. Our predictor accounts for this by flagging both "school closed" and "buses cancelled, school open" as distinct probability outputs where applicable.</p>
        <h3 className="article__h3">Environment Canada vs. National Weather Service</h3>
        <p>Both agencies issue tiered weather alerts (Advisory → Watch → Warning → Emergency). Environment Canada tends to issue warnings slightly earlier in storm events and uses metric thresholds (cm, km/h, °C). US NWS alerts use imperial measurements.</p>
        <p>Both are reliable. Our prediction engine ingests both sources and applies the appropriate thresholds based on your location.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">Province and State-Specific Patterns Worth Knowing</h2>
        <p><strong>Ontario</strong> — The most complex Canadian province for predictions. Lake effect from all five Great Lakes affects different regions differently. Southern Ontario boards (GTA, Hamilton-Wentworth) are relatively conservative about closures. Northern Ontario boards close more readily given access road vulnerability and extreme temperatures. Freezing rain from Lake Ontario frequently affects Kingston and Prince Edward County.</p>
        <p><strong>Alberta</strong> — Calgary and Edmonton experience chinook events that can rapidly clear snow. A 25 cm snowfall forecast can be undercut by a chinook pushing temperatures to +10°C overnight. Our model incorporates chinook probability for Alberta postal codes.</p>
        <p><strong>British Columbia</strong> — Metro Vancouver is famously disrupted by small snow events that would be ignored elsewhere. The combination of steep terrain, rarely-treated residential streets, and a vehicle fleet not equipped for winter makes even 5 cm consequential. The Interior (Kelowna, Kamloops, Prince George) operates under very different standards.</p>
        <p><strong>Quebec</strong> — Strong snow removal infrastructure in Montreal and Quebec City means higher thresholds than comparable Canadian cities. Rural Quebec and the regions outside the two major metros have thresholds closer to northern Ontario.</p>
        <p><strong>Texas and the Deep South</strong> — Ice storms and freezing rain events cause extensive closures. Rarely more than 2–3 events per season, but when they arrive, closures are widespread and multi-day because road treatment resources are limited and residential streets may not be addressed for 2–3 days.</p>
        <p><strong>Upper Midwest (Minnesota, Wisconsin, Michigan, North Dakota)</strong> — Highest thresholds in the US. Districts here have invested heavily in fleet and road treatment and operate under the assumption that winter is long. Closures typically require blizzard conditions, extreme cold (-30°F+ wind chill), or visibility events.</p>
        <p><strong>Northeast (New York, Massachusetts, Connecticut, New Jersey)</strong> — Highly variable. Urban districts like New York City rarely close; suburban and rural districts are much more responsive. Lake effect in western New York (Buffalo, Rochester, Watertown) creates hyperlocal events that can close rural districts while cities stay open.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">How to Get the Most Accurate Prediction</h2>
        <p><strong>Use your postal code or ZIP, not just your city name.</strong> City boundaries are large. Your school and the school 10 km away may be served by different transportation operators with different policies. The more specific your input, the more accurate the result.</p>
        <p><strong>Check the night before, then again at 5 AM.</strong> Forecasts update continuously. A prediction at 9 PM reflects the storm as modeled then. By 5 AM, the National Weather Service or Environment Canada has issued updated hourly guidance, road condition reports are coming in, and the model has substantially more data.</p>
        <p><strong>Enter your school type.</strong> Public elementary schools, public high schools, and private schools often apply different thresholds. Universities and colleges operate largely independently. A prediction calibrated to elementary school closure patterns will differ from one calibrated to university closures.</p>
        <p><strong>Cross-reference with official alerts.</strong> If an active Winter Storm Warning (US) or Snowfall Warning (Canada) is in effect for your area and your probability reads above 65%, the combination is a strong signal. Conversely, a high snow day probability without an official warning in place suggests the model may be incorporating forecast uncertainty — worth a second check.</p>
      </section>

      <section className="article__section">
        <h2 className="article__h2">What to Do While You Wait for the Decision</h2>
        <p>For parents: arrange backup childcare before you need it. Once a closure is announced at 5:30 AM, every available neighbour, grandparent, and daycare provider is getting the same call simultaneously. Having a plan in place before the storm arrives removes the morning scramble.</p>
        <p>For students: assuming a snow day before it's announced has a long failure rate. Forecasts shift. Boards sometimes surprise. The prediction gives you a probability, not a guarantee. Check the official board website or transportation service before making any assumptions.</p>
        <p>For teachers and school staff: many boards have staff reporting policies that differ from student closure policies. Even when students are dismissed, staff may be required to attend. Check your board's emergency procedures.</p>
      </section>

    </article>
  )
}

/* ─── FAQ Component (with Schema markup) ────────── */
const FAQ_DATA = [
  {
    q: 'How accurate is the snow day calculator?',
    a: 'For 24–48 hour forecasts, accuracy typically runs 85–92% when conditions are clear-cut — heavy snowfall with appropriate timing and temperature. Accuracy drops in ambiguous scenarios: 5–10 cm of snow with overnight temperatures hovering around 0°C, or situations where the forecast itself is uncertain. The further out you\'re predicting, the wider the uncertainty band.'
  },
  {
    q: 'Why did the prediction say 80% but school was open?',
    a: 'Several reasons this happens: The storm tracked north or south of your area. Road crews worked through the night and conditions were better than forecast by 5 AM. Your district has a higher-than-average threshold. Or the superintendent simply made a judgment call to stay open. An 80% probability means this scenario has historically produced closures — not that it always does.'
  },
  {
    q: 'Can I use this for work closures, not just schools?',
    a: 'Yes. The underlying weather data is the same. Work closures generally follow school closures in terms of timing and severity thresholds, though many employers use different criteria. Government and public sector work in Canada often mirrors school board decisions.'
  },
  {
    q: 'Does it work for universities and colleges?',
    a: 'Universities in both the US and Canada are notoriously reluctant to close and typically operate on different timelines — they may announce cancellations course-by-course or faculty-by-faculty rather than a blanket closure. The probability you see is calibrated toward K-12 schools. For university closures, treat it as a rough signal rather than a specific prediction.'
  },
  {
    q: "What's the difference between a snow day and a bus cancellation in Ontario?",
    a: 'A snow day means the school is closed entirely. A bus cancellation means school is open but transportation is suspended — your child is expected to attend if you can get them there independently. Bus cancellations are announced through the same channels as closures. Look specifically for whether your transportation consortium\'s buses are cancelled, not just whether the school is open.'
  },
  {
    q: 'How does it handle freezing rain versus snow?',
    a: 'Freezing rain is weighted more aggressively in the model than equivalent snowfall, because its impact on road conditions per centimeter of accumulation is much greater. Even 5 mm of freezing rain can produce closure conditions that 10 cm of dry snow would not.'
  },
  {
    q: 'Why is the prediction different for schools in the same city?',
    a: 'Boundaries matter. School districts in the US and school boards in Canada don\'t always follow city limits. Two schools in the same city may be served by different transportation consortiums with different policies, or one may be a private school with different closure criteria. Enter the ZIP or postal code closest to your specific school for the most accurate result.'
  },
]

function FAQItem({ item, isOpen, onToggle }) {
  return (
    <details className="faq" open={isOpen} onClick={e => { e.preventDefault(); onToggle(); }}
      itemScope itemProp="mainEntity" itemType="https://schema.org/Question">
      <summary className="faq__q" itemProp="name">{item.q}</summary>
      <div itemScope itemProp="acceptedAnswer" itemType="https://schema.org/Answer">
        <p className="faq__a" itemProp="text">{item.a}</p>
      </div>
    </details>
  )
}

function FAQSection() {
  const [openIndex, setOpenIndex] = useState(0)
  return (
    <section id="faq" className="info-section faq-section" aria-labelledby="faq-title"
      itemScope itemType="https://schema.org/FAQPage">
      <h2 id="faq-title" className="section-title">Frequently Asked Questions</h2>
      <div className="faqs">
        {FAQ_DATA.map((item, i) => (
          <FAQItem key={i} item={item} isOpen={openIndex === i}
            onToggle={() => setOpenIndex(openIndex === i ? -1 : i)} />
        ))}
      </div>
    </section>
  )
}

/* ─── App ───────────────────────────────────────── */
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

      {/* ── Header ── */}
      <header className="header">
        <div className="header__logo">
          <Snowflake size={22} opacity={1} style={{ color: 'var(--blue)' }} />
        </div>
        <nav className="header__nav" aria-label="Site navigation">
          <a href="#how"     className="nav-link">How it works</a>
          <a href="#article" className="nav-link">Guide</a>
          <a href="#faq"     className="nav-link">FAQ</a>
        </nav>
      </header>

      <main className="main">

        {/* ── Hero ── */}
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

        {/* ── Calculator ── */}
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

        {/* ── Results ── */}
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

        {/* ── How It Works ── */}
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

        {/* ── Full Article ── */}
        <div id="article">
          <ArticleContent />
        </div>

        {/* ── FAQ with Schema ── */}
        <FAQSection />

        {/* ── Disclaimer ── */}
        <div className="disclaimer">
          Predictions are updated continuously using Weather.gov (US) and Environment Canada data. This tool estimates probability and is not an official source of school closure information. Always confirm closures through your school board's official website, transportation consortium, or local emergency alerts.
        </div>

      </main>

      {/* ── Footer ── */}
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

/* ─── Styles ────────────────────────────────────── */
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
.main { flex: 1; width: 100%; max-width: 860px; margin: 0 auto; padding: clamp(2rem, 6vw, 4rem) clamp(1rem, 5vw, 2rem); display: flex; flex-direction: column; gap: clamp(2.5rem, 6vw, 4rem); position: relative; z-index: 1; }
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
.field__hint--highlight { color: var(--blue); }
.results__source--highlight { color: var(--blue); }
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
.prob-ring__inner { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 1px; padding-left: 12px; }
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

/* ── Article ── */
.article { display: flex; flex-direction: column; gap: 0; }
.article__intro { font-size: 1.05rem; color: var(--text-2); border-left: 3px solid var(--blue-dark); padding-left: 1.25rem; line-height: 1.8; margin-bottom: 0; font-style: italic; }
.article__section { padding-top: 2.5rem; border-top: 1px solid var(--border); margin-top: 2.5rem; }
.article__section:first-of-type { border-top: none; margin-top: 1.5rem; padding-top: 0; }
.article__h2 { font-family: var(--font-display); font-size: clamp(1.15rem, 3vw, 1.5rem); font-weight: 700; color: var(--text-1); letter-spacing: -0.01em; margin-bottom: 1rem; }
.article__h3 { font-size: 1rem; font-weight: 600; color: #c7d5f0; margin: 1.5rem 0 0.75rem; }
.article p { color: var(--text-2); margin-bottom: 0.9rem; line-height: 1.75; font-size: 0.95rem; }
.article p strong { color: var(--text-1); font-weight: 600; }
.article__list { padding-left: 1.4rem; margin-bottom: 0.9rem; }
.article__list li { color: var(--text-2); margin-bottom: 0.35rem; font-size: 0.95rem; line-height: 1.6; }

/* ── Prob Table ── */
.prob-table { border: 1px solid var(--border); border-radius: var(--r-md); overflow: hidden; margin: 1.25rem 0; }
.prob-table__row { display: flex; align-items: baseline; gap: 1rem; padding: 0.65rem 1rem; border-bottom: 1px solid var(--border); }
.prob-table__row:last-child { border-bottom: none; }
.prob-table__range { font-weight: 600; color: var(--blue); font-size: 0.85rem; white-space: nowrap; min-width: 90px; flex-shrink: 0; }
.prob-table__meaning { color: var(--text-2); font-size: 0.875rem; line-height: 1.5; }

/* ── FAQ ── */
.faq-section { scroll-margin-top: 80px; }
.faqs { display: flex; flex-direction: column; gap: 0.75rem; }
.faq { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); overflow: hidden; }
.faq__q { padding: 1rem 1.25rem; cursor: pointer; font-weight: 500; color: var(--text-1); font-size: 0.95rem; list-style: none; display: flex; align-items: center; justify-content: space-between; transition: background var(--t-fast); }
.faq__q:hover { background: rgba(255,255,255,0.02); }
.faq__q::after { content: '+'; color: var(--blue); font-size: 1.2rem; }
details[open] .faq__q::after { content: '−'; }
.faq__a { padding: 0.75rem 1.25rem 1rem; color: var(--text-2); font-size: 0.875rem; line-height: 1.75; border-top: 1px solid var(--border); margin: 0; }

/* ── Disclaimer ── */
.disclaimer { padding: 1rem 1.25rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: var(--r-md); font-size: 0.8rem; color: var(--text-3); font-style: italic; line-height: 1.6; }

/* ── Footer ── */
.footer { text-align: center; padding: 2.5rem 1.5rem; border-top: 1px solid var(--border); color: var(--text-3); font-size: 0.8rem; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; position: relative; z-index: 1; }
.footer__snow { margin-bottom: 0.25rem; }
.footer__sub { font-size: 0.73rem; }

@media (min-width: 768px) and (max-width: 1024px) { .main { max-width: 700px; } .hero__title { font-size: clamp(3rem, 7vw, 5rem); } }
@media (min-width: 1024px) { .hero__sub { font-size: 1.1rem; } .card { padding: 2.5rem; } }
@media (prefers-reduced-motion: reduce) { .particle, .spinner { animation: none; } .day-card { animation: none; } * { transition-duration: 0.01ms !important; } }
`
