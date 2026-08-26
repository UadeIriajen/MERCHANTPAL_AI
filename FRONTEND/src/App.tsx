import { useEffect, useMemo, useState } from 'react';
import { Link, Route, Switch, useLocation, useParams } from 'wouter';
import {
  ArrowLeft, ArrowRight, BarChart3, Bell, Bot, Check, ChevronRight, CircleHelp, Download,
  Clock3, CreditCard, DollarSign, Edit3, FileText, Filter, Home as HomeIcon,
  Info, Lightbulb, LogOut, Menu, Mic, MoreHorizontal, Package, Plus, Receipt,
  Search, Settings, ShoppingBag, Sparkles, Trash2, TrendingUp, UserRound, Users,
  WifiOff, X, Zap,
} from 'lucide-react';
import { ErrorBoundary } from '@/components/error-boundary';
import { defaultProducts, defaultTransactions, readLocal, writeLocal, type MockProduct, type MockTransaction, type MockUser } from '@/lib/mock-services';

const naira = (amount: number) => `₦${amount.toLocaleString('en-NG')}`;
const initialProducts = defaultProducts;
const initialTransactions = defaultTransactions;
type Product = MockProduct;
type Transaction = MockTransaction;
const read = readLocal;
const write = writeLocal;
const fallbackUser: MockUser = { name: 'Amina', business: 'Amina’s Kitchen', identifier: 'demo@merchantpal.app' };
const getCurrentUser = () => read<MockUser>('mp-user', fallbackUser);
const initials = (name: string) => name.trim().split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();

function BrandLogo({ small = false }: { small?: boolean }) {
  return <img className={`brand-logo ${small ? 'brand-logo-small' : ''}`} src="/merchantpal-logo.jpg" alt="MerchantPal" />;
}

function Button({ children, onClick, variant = 'primary', className = '', type = 'button', disabled = false }: { children: React.ReactNode; onClick?: () => void; variant?: 'primary' | 'outline' | 'ghost' | 'danger'; className?: string; type?: 'button' | 'submit'; disabled?: boolean }) {
  return <button type={type} onClick={onClick} disabled={disabled} className={`mp-button mp-${variant} pressable ${className}`}>{children}</button>;
}

function IconButton({ children, label, onClick, className = '' }: { children: React.ReactNode; label: string; onClick?: () => void; className?: string }) {
  return <button aria-label={label} data-testid={`button-${label.toLowerCase().replaceAll(' ', '-')}`} onClick={onClick} className={`icon-button pressable ${className}`}>{children}</button>;
}

function AppHeader({ title = 'MerchantPal', back, action }: { title?: string; back?: string; action?: React.ReactNode }) {
  return <header className="app-header safe-top">
    {back ? <Link href={back} className="icon-button" data-testid="link-back"><ArrowLeft size={21} /></Link> : <div className="brand-lockup"><BrandLogo small /></div>}
    {back && <strong className="header-title">{title}</strong>}
    {action || (!back && <Link href="/notifications" className="icon-button" data-testid="link-notifications"><Bell size={20} /><span className="notification-dot" /></Link>)}
  </header>;
}

const navItems = [
  { href: '/', label: 'Home', icon: HomeIcon },
  { href: '/assistant', label: 'Assistant', icon: Bot },
  { href: '/inventory', label: 'Inventory', icon: Package },
  { href: '/transactions', label: 'Transactions', icon: Receipt },
  { href: '/profile', label: 'Profile', icon: UserRound },
];
function BottomNav() {
  const [location] = useLocation();
  return <nav className="bottom-nav safe-bottom" aria-label="Primary navigation">
    {navItems.map(({ href, label, icon: Icon }) => {
      const active = href === '/' ? location === '/' : location.startsWith(href);
      return <Link href={href} key={href} className={`bottom-item ${active ? 'active' : ''}`} data-testid={`link-nav-${label.toLowerCase()}`}>
        <span className="nav-icon"><Icon size={19} strokeWidth={active ? 2.5 : 1.8} /></span><span>{label}</span>
      </Link>;
    })}
  </nav>;
}

function Shell({ children }: { children: React.ReactNode }) {
  const [offline, setOffline] = useState(!navigator.onLine);
  useEffect(() => {
    const goOffline = () => setOffline(true); const goOnline = () => setOffline(false);
    window.addEventListener('offline', goOffline); window.addEventListener('online', goOnline);
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => undefined);
    return () => { window.removeEventListener('offline', goOffline); window.removeEventListener('online', goOnline); };
  }, []);
  return <div className="app-shell"><div className="app-frame">
    {offline && <div className="offline-strip"><WifiOff size={14} /> Working offline · your changes stay on this device</div>}
    {children}<BottomNav />
  </div></div>;
}

function PublicFrame({ children, title, back = '/welcome' }: { children: React.ReactNode; title?: string; back?: string }) {
  return <div className="app-shell"><div className="app-frame public-frame">
    {title ? <AppHeader title={title} back={back} /> : null}<main className="public-main">{children}</main>
  </div></div>;
}

function Welcome() {
  return <PublicFrame><main className="welcome-main">
    <div className="welcome-brand"><BrandLogo /></div>
    <div className="welcome-copy"><span className="eyebrow">A clearer way to trade</span><h1>Your business,<br /><em>understood.</em></h1><p>Keep track of sales, stock and the small details that keep your business moving.</p></div>
    <div className="welcome-art" aria-hidden="true"><div className="art-ring ring-one" /><div className="art-ring ring-two" /><div className="art-card"><TrendingUp size={26} /><span>₦48,000</span><small>Today's sales</small></div><div className="art-dots" /></div>
    <div className="welcome-actions"><Link href="/signup" className="mp-button mp-primary" data-testid="link-get-started">Get started <ArrowRight size={18} /></Link><Link href="/login" className="mp-button mp-outline" data-testid="link-login">I already have an account</Link></div>
    <p className="welcome-foot">Made by the MerchantPal team · Works offline</p>
  </main></PublicFrame>;
}

function Login({ signup = false }: { signup?: boolean }) {
  const [, navigate] = useLocation();
  const [form, setForm] = useState({ name: '', identifier: '', password: '' });
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (signup) {
      write('mp-pending-user', { name: form.name || 'New merchant', identifier: form.identifier, business: '' });
      navigate('/setup');
      return;
    }
    const accounts = read<MockUser[]>('mp-accounts', []);
    const existing = accounts.find(account => account.identifier === form.identifier);
    write('mp-user', existing || { name: form.identifier.split('@')[0] || 'Merchant', business: 'My business', identifier: form.identifier, isNew: !existing });
    navigate('/');
  };
  return <PublicFrame title={signup ? 'Create account' : 'Welcome back'} back="/welcome">
    <div className="auth-layout"><div className="auth-intro"><BrandLogo small /><span className="eyebrow">{signup ? 'Start small. Grow steady.' : 'Good to see you again.'}</span><h1>{signup ? 'Make room for what matters.' : 'Your numbers,<br />in one place.'}</h1><p>{signup ? 'Set up your private business companion in less than a minute.' : 'Pick up right where you left off.'}</p></div>
      <form className="form-stack" onSubmit={submit}>
        {signup && <label>Full name<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Amina Yusuf" required data-testid="input-name" /></label>}
        <label>Phone or email<input value={form.identifier} onChange={e => setForm({ ...form, identifier: e.target.value })} placeholder="Enter phone or email" required data-testid="input-identifier" /></label>
        <label>Password<input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder={signup ? 'Create a password' : 'Enter your password'} required data-testid="input-password" /></label>
        {!signup && <Link className="form-link align-right" href="/login">Forgot password?</Link>}
        <Button type="submit" className="full-width">{signup ? 'Create my account' : 'Log in'} <ArrowRight size={17} /></Button>
        <div className="form-divider"><span>or</span></div>
        <Button variant="outline" onClick={() => {
          if (signup) write('mp-pending-user', { name: form.name || 'Demo merchant', identifier: form.identifier || 'demo@merchantpal.app', business: '' });
          else write('mp-user', read('mp-user', { name: 'Amina', business: 'Amina’s Kitchen', identifier: 'demo@merchantpal.app' }));
          navigate(signup ? '/setup' : '/');
        }} className="full-width">Demo account is here (till backend is ready)</Button>
      </form>
      <p className="auth-switch">{signup ? 'Already have an account?' : "Don't have an account?"} <Link href={signup ? '/login' : '/signup'} data-testid="link-auth-switch">{signup ? 'Log in' : 'Create account'}</Link></p>
    </div>
  </PublicFrame>;
}

function Setup() {
  const [, navigate] = useLocation();
  const pending = read<MockUser>('mp-pending-user', { name: 'Amina', business: 'Amina’s Kitchen', identifier: 'demo@merchantpal.app' });
  const [business, setBusiness] = useState(pending.business || '');
  const [offer, setOffer] = useState('food');
  const [description, setDescription] = useState('');
  return <PublicFrame title="Business setup" back="/signup"><div className="setup-page"><div className="stepper"><span className="step-active">1</span><i /><span>2</span><i /><span>3</span></div><span className="eyebrow">A little about your business</span><h1>Let’s get you set up.</h1><p className="muted">This helps MerchantPal give you more useful summaries. You can change it later.</p><div className="form-stack"><label>Business name<input value={business} onChange={e => setBusiness(e.target.value)} placeholder="e.g. Amina’s Kitchen" data-testid="input-business-name" /></label><label>What do you offer?<select value={offer} onChange={e => setOffer(e.target.value)}><option value="food">Food and drinks</option><option value="retail">Retail products</option><option value="services">Services</option><option value="other">Something else</option></select></label><label>Tell us a little more <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="What do you offer, and what would you like MerchantPal to help you track?" rows={4} /></label><label>Currency<select defaultValue="ngn"><option value="ngn">Nigerian Naira (₦)</option><option value="usd">US Dollar ($)</option></select></label><Button onClick={() => { const user = { ...pending, name: pending.name || 'Merchant', business: business || 'My business', category: offer, description, isNew: !read<MockUser[]>('mp-accounts', []).some(account => account.identifier === pending.identifier) }; write('mp-user', user); write('mp-accounts', [...read<MockUser[]>('mp-accounts', []).filter(account => account.identifier !== user.identifier), user]); write('mp-pending-user', null); navigate('/'); }} className="full-width">Finish setup <ArrowRight size={17} /></Button></div></div></PublicFrame>;
}

function StatCard({ label, value, trend, tone = '' }: { label: string; value: string; trend?: string; tone?: string }) {
  return <div className={`stat-card ${tone}`}><span className="label muted">{label}</span><strong>{value}</strong>{trend && <span className="stat-trend"><TrendingUp size={14} />{trend}</span>}</div>;
}

function Dashboard() {
  const user = getCurrentUser();
  const fresh = Boolean(user.isNew);
  return <Shell><AppHeader /><main className="screen-content fade-in"><div className="greeting"><span className="eyebrow">Tuesday, 24 June 2025</span><h1>Good morning, {user.name}</h1><p>Here’s how your business is doing today.</p></div>
    <Link href="/assistant/voice" className="talk-card pressable" data-testid="link-talk-assistant"><div className="talk-icon"><Sparkles size={23} /></div><div><span className="label">YOUR BUSINESS COMPANION</span><h2>Talk to MerchantPal</h2><p>Tell me what happened today.</p></div><ArrowRight size={20} /></Link>
    <section className="section-block"><div className="section-heading"><h2>Today at a glance</h2><Link href="/analytics">See analytics</Link></div><div className="stats-grid"><StatCard label="TODAY'S SALES" value={fresh ? '₦0' : '₦48,000'} trend={fresh ? undefined : '+12.4%'} /><StatCard label="TODAY'S PROFIT" value={fresh ? '₦0' : '₦16,850'} trend={fresh ? undefined : '+8.1%'} tone="mint" /></div></section>
    <section className="section-block"><div className="section-heading"><h2>Business health</h2><Link href="/insights">View insights</Link></div><div className="health-grid"><Link href="/analytics" className="health-card"><span className="health-icon expense"><DollarSign size={15} /></span><span className="label muted">EXPENSES</span><strong>{fresh ? '₦0' : '₦9,450'}</strong><small>this week</small></Link><Link href="/analytics" className="health-card"><span className="health-icon profit"><TrendingUp size={15} /></span><span className="label muted">NET PROFIT</span><strong>{fresh ? '₦0' : '₦72,850'}</strong><small>this week</small></Link><Link href="/insights" className="health-card health-insight"><span className="health-icon insight"><Lightbulb size={15} /></span><span className="label muted">INSIGHT</span><strong>{fresh ? 'Start tracking' : 'Fridays are strongest'}</strong><small>tap to learn more</small></Link></div></section>
    <section className="section-block"><div className="section-heading"><h2>Inventory</h2><Link href="/inventory">View all</Link></div><div className="stock-card"><div className="stock-header"><div className="stock-symbol"><Package size={18} /></div><div><strong>4 products</strong><p>₦245,000 total value</p></div><span className="stock-warning">2 low stock</span></div><div className="stock-row"><span>Jollof Rice</span><div className="progress"><i style={{ width: '72%' }} /></div><b>18</b></div><div className="stock-row"><span>Grilled Chicken</span><div className="progress warning"><i style={{ width: '28%' }} /></div><b>7</b></div></div></section>
    <section className="section-block"><div className="section-heading"><h2>Recent sales</h2><Link href="/transactions">See all</Link></div><TransactionRow transaction={initialTransactions[0]} /><TransactionRow transaction={initialTransactions[1]} /></section>
  </main></Shell>;
}

function Assistant() {
  const user = getCurrentUser();
  const [messages, setMessages] = useState<{ from: 'user' | 'bot'; text: string }[]>([{ from: 'bot', text: `Hi ${user.name.split(' ')[0]}. Tell me about a sale, an expense, or anything on your mind.` }]);
  const [input, setInput] = useState('');
  const send = () => { if (!input.trim()) return; const value = input.trim(); setInput(''); setMessages(m => [...m, { from: 'user', text: value }, { from: 'bot', text: value.toLowerCase().includes('sale') ? 'Got it. I’ve drafted a sale for ₦12,000. Take a look and confirm when you’re ready.' : 'I’m following. I can help you record sales, check stock, or understand your numbers.' }]); };
  return <Shell><AppHeader title="Assistant" action={<IconButton label="assistant-help"><CircleHelp size={20} /></IconButton>} /><main className="assistant-page">
    <div className="assistant-hero"><div className="assistant-orb"><Sparkles size={28} /></div><span className="eyebrow">MERCHANTPAL AI</span><h1>Your business,<br />in plain language.</h1><p>Ask a question or tell me what happened.</p></div>
    <div className="chat-list">{messages.map((message, i) => <div key={`${message.from}-${i}`} className={`chat-row ${message.from}`}><div className="chat-bubble">{message.text}</div></div>)}</div>
    {messages.length > 2 && <div className="sale-draft surface-card rise-in"><div className="sale-draft-head"><span className="icon-tile mint"><Receipt size={17} /></span><div><span className="label muted">DRAFT SALE</span><strong>Jollof Rice + Chicken</strong></div><span className="sale-status">Review</span></div><div className="sale-total"><span>Total</span><strong>₦12,000</strong></div><div className="sale-draft-actions"><Button variant="outline" onClick={() => setMessages(m => m.slice(0, -1))}>Edit</Button><Button onClick={() => setMessages(m => [...m, { from: 'bot', text: 'Sale recorded. Your inventory has been updated.' }])}>Confirm sale <Check size={16} /></Button></div></div>}
    <div className="assistant-composer"><Link href="/assistant/voice" className="voice-mini" aria-label="start voice recording" data-testid="link-voice-recording"><Mic size={19} /></Link><input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder="Ask MerchantPal anything…" data-testid="input-assistant" /><IconButton label="send-message" onClick={send}><ArrowRight size={19} /></IconButton></div>
  </main></Shell>;
}

function VoiceRecording() {
  const [, navigate] = useLocation(); const [recording, setRecording] = useState(true); const bars = [22, 35, 52, 30, 67, 42, 76, 43, 58, 29, 51, 38, 70, 31, 48, 24, 59, 36, 45, 28];
  return <Shell><AppHeader title="Talk to MerchantPal" back="/assistant" /><main className="voice-page"><div className="voice-copy"><span className="eyebrow">VOICE NOTE</span><h1>{recording ? 'I’m listening.' : 'Ready when you are.'}</h1><p>{recording ? 'Tell me what happened in your business today.' : 'Tap the microphone to start again.'}</p></div><div className={`waveform ${recording ? 'recording' : ''}`}>{bars.map((height, i) => <i key={i} style={{ height: `${recording ? height : 8}px`, animationDelay: `${i * 40}ms` }} />)}</div><div className="voice-timer">{recording ? '00:18' : '00:00'}</div><button className={`record-button ${recording ? 'record-pulse' : ''}`} onClick={() => setRecording(!recording)} aria-label={recording ? 'stop recording' : 'start recording'}><span>{recording ? <div className="stop-square" /> : <Mic size={32} />}</span></button><div className="voice-actions"><Button variant="ghost" onClick={() => navigate('/assistant')}>Cancel</Button>{recording ? <Button onClick={() => navigate('/assistant/clarify')}>Stop & review</Button> : null}</div></main></Shell>;
}

function Clarify() {
  const [, navigate] = useLocation(); const [choice, setChoice] = useState('sale');
  return <Shell><AppHeader title="Review note" back="/assistant/voice" /><main className="screen-content clarify-page"><span className="eyebrow">I HEARD</span><h1>“Sold two plates of jollof and a chicken to Kunle for twelve thousand.”</h1><div className="clarify-note"><Sparkles size={17} /><span>I’ve turned that into a sale. Is this right?</span></div><div className="clarify-card surface-card"><div className="sale-draft-head"><span className="icon-tile mint"><Receipt size={17} /></span><div><span className="label muted">SALE</span><strong>Jollof Rice + Chicken</strong></div></div><div className="clarify-line"><span>Customer</span><b>Kunle</b></div><div className="clarify-line"><span>Quantity</span><b>2 plates + 1 piece</b></div><div className="clarify-line"><span>Total</span><b className="money">₦12,000</b></div></div><h3>What should I do with this?</h3><div className="choice-list">{[['sale', 'Record as a sale', 'Updates your sales and inventory'], ['note', 'Save as a note', 'Keep it for later']].map(([key, label, sub]) => <button key={key} className={`choice ${choice === key ? 'selected' : ''}`} onClick={() => setChoice(key)}><span className="radio">{choice === key && <i />}</span><span><b>{label}</b><small>{sub}</small></span></button>)}</div><Button className="full-width" onClick={() => navigate('/transactions/t1/confirm')}>{choice === 'sale' ? 'Confirm sale' : 'Save note'} <Check size={17} /></Button></main></Shell>;
}

function Inventory() {
  const [, navigate] = useLocation(); const [products, setProducts] = useState<Product[]>(() => read('mp-products', initialProducts)); const [search, setSearch] = useState(''); const [lowOnly, setLowOnly] = useState(false);
  useEffect(() => write('mp-products', products), [products]);
  const visible = products.filter(p => (p.name.toLowerCase().includes(search.toLowerCase()) || p.category.toLowerCase().includes(search.toLowerCase())) && (!lowOnly || p.stock < 10));
  const remove = (id: string) => { if (window.confirm('Remove this product from inventory?')) setProducts(ps => ps.filter(p => p.id !== id)); };
  return <Shell><AppHeader /><main className="screen-content fade-in"><div className="page-heading"><div><span className="eyebrow">YOUR CATALOG</span><h1>Inventory</h1></div><IconButton label="add-product" onClick={() => navigate('/inventory/add')}><Plus size={21} /></IconButton></div><div className="search-box"><Search size={18} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products…" data-testid="input-search-products" /></div><div className="inventory-summary surface-card"><div><span className="label muted">INVENTORY VALUE</span><strong>₦245,000</strong><span className="stat-trend"><TrendingUp size={13} /> +5% from last week</span></div><div className="summary-side"><b>{products.length}</b><span>products</span></div></div><div className="section-heading inventory-list-heading"><h2>Product list</h2><Button variant="ghost" onClick={() => setLowOnly(!lowOnly)}><Filter size={15} /> {lowOnly ? 'All products' : 'Low stock'}</Button></div>{visible.length ? <div className="product-list">{visible.map(product => <div className="product-card surface-card" key={product.id} data-testid={`card-product-${product.id}`}><div className="product-icon"><ShoppingBag size={18} /></div><div className="product-info"><strong>{product.name}</strong><span>{product.category} · {naira(product.price)} / {product.unit}</span><div className="product-stock"><div className={`progress ${product.stock < 10 ? 'warning' : ''}`}><i style={{ width: `${Math.min(product.stock / 36 * 100, 100)}%` }} /></div><small className={product.stock < 10 ? 'warn-text' : ''}>{product.stock} in stock</small></div></div><div className="product-actions"><IconButton label={`edit-${product.id}`} onClick={() => navigate(`/inventory/${product.id}`)}><Edit3 size={16} /></IconButton><IconButton label={`delete-${product.id}`} onClick={() => remove(product.id)}><Trash2 size={16} /></IconButton></div></div>)}</div> : <EmptyInventory onAdd={() => navigate('/inventory/add')} />}</main></Shell>;
}

function EmptyInventory({ onAdd }: { onAdd: () => void }) { return <div className="empty-state surface-card"><div className="empty-illustration"><Package size={32} /></div><h2>Your shelves are waiting.</h2><p>Add your first product to start tracking stock and value in one place.</p><Button onClick={onAdd} className="full-width"><Plus size={17} /> Add a product</Button></div>; }

function AddProduct() {
  const [, navigate] = useLocation(); const params = useParams<{ id: string }>(); const editing = params.id && params.id !== 'add'; const products = read<Product[]>('mp-products', initialProducts); const existing = products.find(p => p.id === params.id);
  const [form, setForm] = useState({ name: existing?.name || '', category: existing?.category || 'Prepared food', price: String(existing?.price || ''), cost: String(existing?.cost || ''), stock: String(existing?.stock || ''), unit: existing?.unit || 'piece' });
  const update = (key: keyof typeof form, value: string) => setForm(f => ({ ...f, [key]: value }));
  const submit = (e: React.FormEvent) => { e.preventDefault(); const next: Product = { id: existing?.id || `p${Date.now()}`, name: form.name, category: form.category, price: Number(form.price), cost: Number(form.cost), stock: Number(form.stock), unit: form.unit }; write('mp-products', editing ? products.map(p => p.id === next.id ? next : p) : [...products, next]); navigate('/inventory'); };
  return <Shell><AppHeader title={editing ? 'Edit product' : 'Add product'} back={editing ? `/inventory/${params.id}` : '/inventory'} /><main className="screen-content form-page"><span className="eyebrow">{editing ? 'UPDATE YOUR CATALOG' : 'NEW PRODUCT'}</span><h1>{editing ? 'Keep it current.' : 'What are you selling?'}</h1><p className="muted">Add the details you reach for most often. You can always change them later.</p><form className="form-stack" onSubmit={submit}><label>Product name<input value={form.name} onChange={e => update('name', e.target.value)} placeholder="e.g. Jollof Rice" required data-testid="input-product-name" /></label><label>Category<select value={form.category} onChange={e => update('category', e.target.value)}><option>Prepared food</option><option>Drinks</option><option>Retail</option><option>Services</option></select></label><div className="two-fields"><label>Selling price<input type="number" value={form.price} onChange={e => update('price', e.target.value)} placeholder="0" required /></label><label>Cost price<input type="number" value={form.cost} onChange={e => update('cost', e.target.value)} placeholder="0" required /></label></div><div className="two-fields"><label>Current stock<input type="number" value={form.stock} onChange={e => update('stock', e.target.value)} placeholder="0" required /></label><label>Unit<select value={form.unit} onChange={e => update('unit', e.target.value)}><option>piece</option><option>plate</option><option>bottle</option><option>pack</option></select></label></div><Button type="submit" className="full-width">{editing ? 'Save changes' : 'Add product'} <Check size={17} /></Button></form></main></Shell>;
}

function ProductDetails() {
  const [, navigate] = useLocation(); const { id } = useParams<{ id: string }>(); const product = read<Product[]>('mp-products', initialProducts).find(p => p.id === id) || initialProducts[0];
  return <Shell><AppHeader title="Product details" back="/inventory" action={<IconButton label="more-product" onClick={() => navigate(`/inventory/${product.id}/edit`)}><MoreHorizontal size={21} /></IconButton>} /><main className="screen-content product-detail"><div className="detail-product-icon"><ShoppingBag size={34} /></div><span className="eyebrow">{product.category}</span><h1>{product.name}</h1><div className="detail-price">{naira(product.price)} <small>/ {product.unit}</small></div><div className="detail-grid"><div><span className="label muted">IN STOCK</span><strong className={product.stock < 10 ? 'warn-text' : ''}>{product.stock}</strong><small>{product.unit}s available</small></div><div><span className="label muted">MARGIN</span><strong>{naira(product.price - product.cost)}</strong><small>per {product.unit}</small></div></div><div className="detail-panel surface-card"><div className="section-heading"><h2>Stock level</h2><span className={product.stock < 10 ? 'warn-text' : 'muted'}>{product.stock < 10 ? 'Running low' : 'Healthy'}</span></div><div className={`big-progress progress ${product.stock < 10 ? 'warning' : ''}`}><i style={{ width: `${Math.min(product.stock / 36 * 100, 100)}%` }} /></div><p className="body-sm muted">Last updated today at 9:14 AM</p></div><Button onClick={() => navigate(`/inventory/${product.id}/edit`)} className="full-width"><Edit3 size={17} /> Edit product</Button></main></Shell>;
}

function TransactionRow({ transaction, onClick }: { transaction: Transaction; onClick?: () => void }) {
  return <button onClick={onClick} className="transaction-row" data-testid={`row-transaction-${transaction.id}`}><span className={`transaction-mark ${transaction.status}`}><Receipt size={16} /></span><span className="transaction-info"><strong>{transaction.item}</strong><small>{transaction.date} · {transaction.customer}</small></span><span className="transaction-amount"><b>{naira(transaction.total)}</b><small>{transaction.status === 'paid' ? 'Paid' : 'Pending'}</small></span><ChevronRight size={17} className="chevron" /></button>;
}
function Transactions() {
  const [, navigate] = useLocation(); const [query, setQuery] = useState(''); const transactions = initialTransactions.filter(t => t.item.toLowerCase().includes(query.toLowerCase()));
  return <Shell><AppHeader /><main className="screen-content"><div className="page-heading"><div><span className="eyebrow">MONEY IN, MONEY OUT</span><h1>Transactions</h1></div><IconButton label="new-transaction" onClick={() => navigate('/assistant/voice')}><Plus size={21} /></IconButton></div><div className="search-box"><Search size={18} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search transactions…" /></div><div className="transaction-total surface-card"><span className="label muted">THIS MONTH</span><strong>₦186,400</strong><span className="stat-trend"><TrendingUp size={13} /> +18.2% from last month</span></div><div className="section-heading"><h2>Recent activity</h2><Button variant="ghost" onClick={() => undefined}><Filter size={15} /> Filter</Button></div><div className="transaction-list">{transactions.map(t => <TransactionRow key={t.id} transaction={t} onClick={() => navigate(`/transactions/${t.id}`)} />)}</div></main></Shell>;
}
function TransactionDetails() {
  const [, navigate] = useLocation(); const { id } = useParams<{ id: string }>(); const transaction = initialTransactions.find(t => t.id === id) || initialTransactions[0];
  return <Shell><AppHeader title="Transaction details" back="/transactions" /><main className="screen-content transaction-detail"><div className="detail-receipt"><div className="receipt-icon"><Check size={27} /></div><span className="eyebrow">SALE RECORDED</span><h1>{naira(transaction.total)}</h1><p>{transaction.date}</p></div><div className="receipt-card surface-card"><div className="receipt-card-head"><span>Item</span><span>Amount</span></div><div className="receipt-item"><div><strong>{transaction.item}</strong><small>{transaction.quantity} items</small></div><b>{naira(transaction.total)}</b></div><div className="receipt-line"><span>Payment status</span><b className="paid-text"><Check size={14} /> Paid</b></div><div className="receipt-line"><span>Customer</span><b>{transaction.customer}</b></div></div><Button className="full-width" onClick={() => navigate(`/transactions/${transaction.id}/confirm`)}>Record another sale <Plus size={17} /></Button></main></Shell>;
}
function TransactionConfirmation() { const [, navigate] = useLocation(); return <Shell><main className="confirmation-page"><div className="confirm-check"><Check size={38} /></div><span className="eyebrow">ALL DONE</span><h1>Sale recorded.</h1><p>Your numbers are up to date and your inventory has been adjusted.</p><div className="confirm-summary surface-card"><div><span className="label muted">TOTAL SALE</span><strong>₦12,000</strong></div><div className="confirm-summary-row"><span>Jollof Rice + Chicken</span><b>2 items</b></div><div className="confirm-summary-row"><span>Estimated profit</span><b className="paid-text">₦4,300</b></div></div><Button onClick={() => navigate('/')} className="full-width">Back to home <ArrowRight size={17} /></Button><Button variant="ghost" onClick={() => navigate('/transactions')} className="full-width">See all transactions</Button></main></Shell>; }

function Analytics() {
  const [period, setPeriod] = useState('This week'); return <Shell><AppHeader title="Profit analytics" back="/" /><main className="screen-content analytics-page"><span className="eyebrow">THE BIG PICTURE</span><h1>Your profit, clearly.</h1><div className="period-tabs">{['This week', 'This month', '3 months'].map(item => <button key={item} className={period === item ? 'selected' : ''} onClick={() => setPeriod(item)}>{item}</button>)}</div><div className="analytics-hero surface-card"><span className="label muted">NET PROFIT · {period.toUpperCase()}</span><strong>{period === 'This week' ? '₦72,850' : period === 'This month' ? '₦286,450' : '₦804,200'}</strong><span className="stat-trend"><TrendingUp size={14} /> 14.8% vs previous period</span><div className="chart"><i style={{ height: '32%' }} /><i style={{ height: '47%' }} /><i style={{ height: '38%' }} /><i style={{ height: '66%' }} /><i style={{ height: '54%' }} /><i className="today" style={{ height: '84%' }} /><i style={{ height: '72%' }} /></div><div className="chart-labels"><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span></div></div><div className="stats-grid analytics-stats"><StatCard label="SALES" value="₦186,400" /><StatCard label="EXPENSES" value="₦113,550" tone="rose" /></div><div className="insight-callout"><Lightbulb size={19} /><div><b>Your Fridays are your best days.</b><p>Sales are 32% higher than your weekly average. Keep your most popular dishes ready.</p></div></div><Link href="/insights" className="list-link surface-card"><span className="icon-tile mint"><Sparkles size={17} /></span><span><b>Business insights</b><small>3 observations from your numbers</small></span><ChevronRight size={18} /></Link></main></Shell>;
}
function Insights() { return <Shell><AppHeader title="Business insights" back="/analytics" /><main className="screen-content"><span className="eyebrow">A CLOSER LOOK</span><h1>Worth knowing.</h1><p className="muted">A few patterns MerchantPal spotted in your recent activity.</p><div className="insight-list"><div className="insight-card surface-card"><div className="insight-number">01</div><Lightbulb size={19} /><h2>Friday is your strongest day</h2><p>Weekly sales are 32% higher on Fridays. Your customers seem to arrive ready for a full meal.</p><Link href="/inventory">Check your stock <ArrowRight size={15} /></Link></div><div className="insight-card surface-card"><div className="insight-number">02</div><TrendingUp size={19} /><h2>Drinks bring a healthy margin</h2><p>Chapman and bottled water account for 24% of sales but 36% of your profit.</p><Link href="/inventory">View products <ArrowRight size={15} /></Link></div><div className="insight-card surface-card"><div className="insight-number">03</div><Zap size={19} /><h2>One reorder could help</h2><p>Grilled Chicken is moving quickly. You may run out before your next busy day.</p><Link href="/inventory/p2">See grilled chicken <ArrowRight size={15} /></Link></div></div></main></Shell>; }

function Notifications() {
  const [readAll, setReadAll] = useState(false); const notes = [{ icon: TrendingUp, title: 'A good sales day', body: 'Today’s sales are 12.4% above your usual Tuesday.', time: '2 hours ago', tone: 'mint' }, { icon: Package, title: 'Stock is running low', body: 'Grilled Chicken has 7 pieces left.', time: '4 hours ago', tone: 'amber' }, { icon: Sparkles, title: 'New insight ready', body: 'MerchantPal found 3 patterns in your numbers.', time: 'Yesterday', tone: 'blue' }];
  return <Shell><AppHeader title="Notifications" back="/" /><main className="screen-content"><div className="page-heading"><div><span className="eyebrow">KEEPING YOU IN THE LOOP</span><h1>Notifications</h1></div><Button variant="ghost" onClick={() => setReadAll(true)}>Mark all read</Button></div><div className="notification-list">{notes.map((note, i) => { const Icon = note.icon; return <div className={`notification-item ${i === 0 && !readAll ? 'unread' : ''}`} key={note.title}><span className={`notification-icon ${note.tone}`}><Icon size={18} /></span><div><b>{note.title}</b><p>{note.body}</p><small>{note.time}</small></div>{i === 0 && !readAll && <i className="unread-dot" />}</div>; })}</div></main></Shell>;
}

function Profile() {
  const [, navigate] = useLocation(); const [business, setBusiness] = useState(getCurrentUser()); const [offlineOnly, setOfflineOnly] = useState(true); const [installEvent, setInstallEvent] = useState<any>(null);
  useEffect(() => { const onInstall = (event: Event) => { event.preventDefault(); setInstallEvent(event); }; window.addEventListener('beforeinstallprompt', onInstall); return () => window.removeEventListener('beforeinstallprompt', onInstall); }, []);
  const install = async () => { if (!installEvent) return; await installEvent.prompt(); setInstallEvent(null); };
  return <Shell><AppHeader /><main className="screen-content profile-page"><div className="profile-head"><div className="avatar">AY</div><div><span className="eyebrow">YOUR ACCOUNT</span><h1>{business.name}</h1><p>{business.business}</p></div><IconButton label="edit-profile" onClick={() => setBusiness({ ...business, business: business.business === 'Amina’s Kitchen' ? 'Amina’s Kitchen & More' : 'Amina’s Kitchen' })}><Edit3 size={17} /></IconButton></div><div className="profile-section"><span className="label muted">BUSINESS</span><div className="settings-list"><Link href="/setup" className="settings-row"><span className="setting-icon mint"><ShoppingBag size={18} /></span><span><b>Business details</b><small>Update your business information</small></span><ChevronRight size={18} /></Link><Link href="/analytics" className="settings-row"><span className="setting-icon blue"><BarChart3 size={18} /></span><span><b>Profit analytics</b><small>See how your business is doing</small></span><ChevronRight size={18} /></Link></div></div><div className="profile-section"><span className="label muted">PREFERENCES</span><div className="settings-list"><div className="settings-row"><span className="setting-icon amber"><WifiOff size={18} /></span><span><b>Offline-first mode</b><small>Keep working without internet</small></span><button className={`toggle ${offlineOnly ? 'on' : ''}`} onClick={() => setOfflineOnly(!offlineOnly)} aria-label="toggle offline mode"><i /></button></div><Link href="/notifications" className="settings-row"><span className="setting-icon rose"><Bell size={18} /></span><span><b>Notifications</b><small>Stock alerts and business updates</small></span><ChevronRight size={18} /></Link></div></div><div className="profile-section"><span className="label muted">SUPPORT</span><div className="settings-list"><button className="settings-row"><span className="setting-icon blue"><CircleHelp size={18} /></span><span><b>Help & feedback</b><small>We’re here when you need us</small></span><ChevronRight size={18} /></button><button className="settings-row logout" onClick={() => navigate('/welcome')}><span className="setting-icon rose"><LogOut size={18} /></span><span><b>Log out</b><small>Come back soon</small></span><ChevronRight size={18} /></button></div></div><p className="profile-version">MerchantPal v1.0.0 · Made for small businesses</p></main></Shell>;
  return <Shell><AppHeader /><main className="screen-content profile-page"><div className="profile-head"><div className="avatar">AY</div><div><span className="eyebrow">YOUR ACCOUNT</span><h1>{business.name}</h1><p>{business.business}</p></div><IconButton label="edit-profile" onClick={() => setBusiness({ ...business, business: business.business === 'Amina’s Kitchen' ? 'Amina’s Kitchen & More' : 'Amina’s Kitchen' })}><Edit3 size={17} /></IconButton></div><div className="profile-section"><span className="label muted">BUSINESS</span><div className="settings-list"><Link href="/setup" className="settings-row"><span className="setting-icon mint"><ShoppingBag size={18} /></span><span><b>Business details</b><small>Update your business information</small></span><ChevronRight size={18} /></Link><Link href="/analytics" className="settings-row"><span className="setting-icon blue"><BarChart3 size={18} /></span><span><b>Profit analytics</b><small>See how your business is doing</small></span><ChevronRight size={18} /></Link></div></div><div className="profile-section"><span className="label muted">PREFERENCES</span><div className="settings-list">{installEvent && <button className="settings-row" onClick={install}><span className="setting-icon mint"><Download size={18} /></span><span><b>Install MerchantPal</b><small>Add it to your home screen</small></span><ChevronRight size={18} /></button>}<div className="settings-row"><span className="setting-icon amber"><WifiOff size={18} /></span><span><b>Offline-first mode</b><small>Keep working without internet</small></span><button className={`toggle ${offlineOnly ? 'on' : ''}`} onClick={() => setOfflineOnly(!offlineOnly)} aria-label="toggle offline mode"><i /></button></div><Link href="/notifications" className="settings-row"><span className="setting-icon rose"><Bell size={18} /></span><span><b>Notifications</b><small>Stock alerts and business updates</small></span><ChevronRight size={18} /></Link></div></div><div className="profile-section"><span className="label muted">SUPPORT</span><div className="settings-list"><button className="settings-row" onClick={() => window.alert('Help is available offline. Tell us what you need when you are next connected.')}><span className="setting-icon blue"><CircleHelp size={18} /></span><span><b>Help & feedback</b><small>We’re here when you need us</small></span><ChevronRight size={18} /></button><button className="settings-row logout" onClick={() => navigate('/welcome')}><span className="setting-icon rose"><LogOut size={18} /></span><span><b>Log out</b><small>Come back soon</small></span><ChevronRight size={18} /></button></div></div><p className="profile-version">MerchantPal v1.0.0 · Made for small businesses</p></main></Shell>;
}

function Offline() { const [, navigate] = useLocation(); return <PublicFrame><div className="offline-page"><div className="offline-icon"><WifiOff size={32} /></div><span className="eyebrow">NO CONNECTION</span><h1>You’re offline,<br />but still in business.</h1><p>MerchantPal saves your work on this device, so you can keep recording sales and checking stock.</p><div className="offline-points"><span><Check size={16} />Your local data is safe</span><span><Check size={16} />Sales will sync when you’re back</span></div><Button onClick={() => navigate('/')} className="full-width">Continue offline <ArrowRight size={17} /></Button></div></PublicFrame>; }
function NotFoundPage() { return <PublicFrame><div className="empty-state"><div className="empty-illustration"><CircleHelp size={32} /></div><h1>Page not found</h1><p>That page isn’t part of today’s numbers.</p><Link href="/" className="mp-button mp-primary full-width">Back to home</Link></div></PublicFrame>; }

function Router() {
  return <ErrorBoundary><Switch>
    <Route path="/welcome" component={Welcome} /><Route path="/login" component={() => <Login />} /><Route path="/signup" component={() => <Login signup />} /><Route path="/setup" component={Setup} />
    <Route path="/" component={Dashboard} /><Route path="/assistant" component={Assistant} /><Route path="/assistant/voice" component={VoiceRecording} /><Route path="/assistant/clarify" component={Clarify} />
    <Route path="/inventory" component={Inventory} /><Route path="/inventory/empty" component={() => <Shell><AppHeader title="Inventory" back="/inventory" /><main className="screen-content"><EmptyInventory onAdd={() => undefined} /></main></Shell>} /><Route path="/inventory/add" component={AddProduct} /><Route path="/inventory/:id/edit" component={AddProduct} /><Route path="/inventory/:id" component={ProductDetails} />
    <Route path="/transactions" component={Transactions} /><Route path="/transactions/empty" component={() => <Shell><AppHeader title="Transactions" back="/" /><main className="screen-content"><div className="empty-state surface-card"><div className="empty-illustration"><Receipt size={32} /></div><h2>No sales yet.</h2><p>Record your first sale with MerchantPal Assistant.</p><Link href="/assistant/voice" className="mp-button mp-primary full-width">Record a sale <Mic size={17} /></Link></div></main></Shell>} /><Route path="/transactions/:id/confirm" component={TransactionConfirmation} /><Route path="/transactions/:id" component={TransactionDetails} />
    <Route path="/analytics" component={Analytics} /><Route path="/insights" component={Insights} /><Route path="/notifications" component={Notifications} /><Route path="/profile" component={Profile} /><Route path="/offline" component={Offline} /><Route component={NotFoundPage} />
  </Switch></ErrorBoundary>;
}
function App() { return <Router />; }
export default App;