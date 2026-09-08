import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity, CheckCircle2, ClipboardList, FolderKanban, LayoutDashboard,
  LogOut, Plus, RefreshCw, ShieldCheck, Users, X
} from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function api(path, options = {}) {
  const token = localStorage.getItem('aegis_token');
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) };
  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function Auth({ done }) {
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState({ tenant_name: '', full_name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  async function submit(e) {
    e.preventDefault(); setError('');
    try {
      const data = await api(register ? '/auth/register' : '/auth/login', { method: 'POST', body: JSON.stringify(form) });
      localStorage.setItem('aegis_token', data.access_token); done();
    } catch (err) { setError(err.message); }
  }
  return <main className="auth"><div className="auth-card">
    <div className="mark">A</div><p className="eyebrow">PROJECT AEGIS</p>
    <h1>Secure workspaces,<br />built for teams.</h1>
    <p className="muted">Multi-tenant project management with strict isolation, RBAC and auditability.</p>
    <form onSubmit={submit}>
      {register && <><input required placeholder="Organization name" value={form.tenant_name} onChange={set('tenant_name')} /><input required placeholder="Full name" value={form.full_name} onChange={set('full_name')} /></>}
      <input required type="email" placeholder="Email" value={form.email} onChange={set('email')} />
      <input required type="password" minLength="8" placeholder="Password" value={form.password} onChange={set('password')} />
      <button className="primary">{register ? 'Create workspace' : 'Sign in'}</button>
    </form>
    {error && <div className="error">{error}</div>}
    <button className="link" onClick={() => { setRegister(!register); setError(''); }}>{register ? 'Already registered? Sign in' : 'Create a new workspace'}</button>
  </div></main>;
}

function Modal({ title, children, onClose }) { return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><h3>{title}</h3><button className="icon-btn" onClick={onClose}><X size={17} /></button></div>{children}</div></div>; }

function Dashboard({ logout }) {
  const [tab, setTab] = useState('dashboard');
  const [me, setMe] = useState(null), [tenant, setTenant] = useState(null), [projects, setProjects] = useState([]), [users, setUsers] = useState([]), [tasks, setTasks] = useState([]), [logs, setLogs] = useState([]);
  const [error, setError] = useState(''), [modal, setModal] = useState(null), [busy, setBusy] = useState(false);
  const canManage = me?.role === 'Owner' || me?.role === 'Admin';
  const canCreateAdmin = me?.role === 'Owner';

  const load = async () => {
    try {
      setError(''); const [m, t, p, u] = await Promise.all([api('/me'), api('/tenant'), api('/projects'), api('/users')]);
      setMe(m); setTenant(t); setProjects(p); setUsers(u);
      const all = (await Promise.all(p.map(async (project) => (await api(`/projects/${project.project_id}/tasks`)).map((task) => ({ ...task, project_name: project.name }))))).flat();
      setTasks(all);
      if (tab === 'audit' && canManage) setLogs(await api('/audit-logs'));
    } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);
  useEffect(() => { if (tab === 'audit' && canManage) api('/audit-logs').then(setLogs).catch((e) => setError(e.message)); }, [tab, canManage]);

  async function createUser(data) { setBusy(true); try { await api('/users', { method: 'POST', body: JSON.stringify(data) }); setModal(null); await load(); } catch (e) { setError(e.message); } finally { setBusy(false); } }
  async function createProject(data) { setBusy(true); try { await api('/projects', { method: 'POST', body: JSON.stringify(data) }); setModal(null); await load(); } catch (e) { setError(e.message); } finally { setBusy(false); } }
  async function createTask(projectId, data) { setBusy(true); try { await api(`/projects/${projectId}/tasks`, { method: 'POST', body: JSON.stringify(data) }); setModal(null); await load(); } catch (e) { setError(e.message); } finally { setBusy(false); } }

  const nav = [['dashboard', 'Dashboard', LayoutDashboard], ['projects', 'Projects', FolderKanban], ['tasks', 'Tasks', ClipboardList], ['team', 'Team & roles', Users], ['tenant', 'Tenant verification', ShieldCheck], ['audit', 'Audit logs', Activity]];
  return <div className="shell">
    <aside><div className="logo"><b>A</b> AEGIS</div><div className="tenant"><span>WORKSPACE</span><strong>{tenant?.name || 'Loading...'}</strong><small>{me?.role || ''}</small></div>
      <nav>{nav.map(([id, label, Icon]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon size={17} />{label}</button>)}</nav>
      <button className="logout" onClick={logout}><LogOut size={17} />Sign out</button>
    </aside>
    <main className="main"><header><div><p className="eyebrow">{tab.replace('-', ' ').toUpperCase()}</p><h2>{tab === 'dashboard' ? `Good to see you, ${me?.full_name?.split(' ')[0] || ''}.` : nav.find((n) => n[0] === tab)?.[1]}</h2></div><button className="icon-btn" onClick={load} title="Refresh"><RefreshCw size={17} /></button></header>
      {error && <div className="error banner">{error}<button onClick={() => setError('')}>Dismiss</button></div>}
      {tab === 'dashboard' && <Home projects={projects} tasks={tasks} users={users} canManage={canManage} addProject={() => setModal('project')} />}
      {tab === 'projects' && <Projects projects={projects} canManage={canManage} addProject={() => setModal('project')} addTask={(p) => setModal({ type: 'task', project: p })} />}
      {tab === 'tasks' && <Tasks tasks={tasks} canManage={canManage} />}
      {tab === 'team' && <Team users={users} me={me} canManage={canManage} canCreateAdmin={canCreateAdmin} addUser={() => setModal('user')} />}
      {tab === 'tenant' && <Tenant tenant={tenant} refresh={async () => setTenant(await api('/tenant'))} />}
      {tab === 'audit' && <Audit logs={logs} canManage={canManage} />}
    </main>
    {modal === 'project' && <ProjectForm users={users} busy={busy} onClose={() => setModal(null)} onSubmit={createProject} />}
    {modal === 'user' && <UserForm busy={busy} canCreateAdmin={canCreateAdmin} onClose={() => setModal(null)} onSubmit={createUser} />}
    {modal?.type === 'task' && <TaskForm project={modal.project} users={users} busy={busy} onClose={() => setModal(null)} onSubmit={(data) => createTask(modal.project.project_id, data)} />}
  </div>;
}

const Stat = ({ label, value, Icon }) => <div className="stat"><div className="stat-icon"><Icon size={18} /></div><div><small>{label}</small><strong>{value}</strong></div></div>;
function Home({ projects, tasks, users, canManage, addProject }) { return <>
  <div className="stats"><Stat label="Projects" value={projects.length} Icon={FolderKanban} /><Stat label="Open tasks" value={tasks.filter(t => t.status !== 'done').length} Icon={ClipboardList} /><Stat label="Team members" value={users.length} Icon={Users} /><Stat label="Completed" value={tasks.filter(t => t.status === 'done').length} Icon={CheckCircle2} /></div>
  <div className="section-head"><div><h3>Projects</h3><p className="muted">Your tenant-scoped portfolio.</p></div>{canManage && <button className="primary small" onClick={addProject}><Plus size={15} />New project</button>}</div>
  <div className="cards">{projects.map(p => <article className="project-card" key={p.project_id}><div className="project-top"><span className="pill">{p.status}</span><span className="dot" /></div><h3>{p.name}</h3><p>{p.description || 'No description yet.'}</p><div className="card-foot"><span>Tenant scoped</span><span>{tasks.filter(t => t.project_id === p.project_id).length} tasks</span></div></article>)}{!projects.length && <Empty text="No projects yet. Create your first project." />}</div>
</>; }

function Projects({ projects, canManage, addProject, addTask }) { return <><div className="section-head"><div><h3>All projects</h3><p className="muted">Descriptions, managers and tenant isolation.</p></div>{canManage && <button className="primary small" onClick={addProject}><Plus size={15} />New project</button>}</div><div className="table">{projects.map(p => <div className="row" key={p.project_id}><div><strong>{p.name}</strong><span>{p.description || 'No description'}</span></div><span className="pill">{p.status}</span>{canManage && <button className="ghost" onClick={() => addTask(p)}>+ Task</button>}</div>)}{!projects.length && <Empty text="No projects found." />}</div></>; }

function Tasks({ tasks, canManage }) { const [sort, setSort] = useState('priority'); const priority = { high: 0, medium: 1, low: 2 }; const sorted = useMemo(() => [...tasks].sort((a, b) => sort === 'priority' ? priority[a.priority] - priority[b.priority] : a.title.localeCompare(b.title)), [tasks, sort]); return <>
  <div className="section-head"><div><h3>Task board</h3><p className="muted">High priority first. Task creation is restricted to Owners and Admins.</p></div><select value={sort} onChange={e => setSort(e.target.value)}><option value="priority">Priority order</option><option value="title">Title order</option></select></div>
  <div className="task-grid">{['todo', 'in_progress', 'done'].map(s => <div className="task-col" key={s}><div className="col-title"><span>{s.replace('_', ' ')}</span><b>{sorted.filter(t => t.status === s).length}</b></div>{sorted.filter(t => t.status === s).map(t => <article className={`task priority-${t.priority}`} key={t.task_id}><div className="task-head"><strong>{t.title}</strong><span className={`priority ${t.priority}`}>{t.priority}</span></div><span>{t.project_name}</span><small>{t.description || 'No description'}</small></article>)}</div>)}</div>
  {!canManage && <p className="permission-note">Member accounts can view tasks and update tasks they are assigned to or created, but cannot create new tasks.</p>}
 </>; }

function Team({ users, me, canManage, canCreateAdmin, addUser }) { return <><div className="section-head"><div><h3>Team & roles</h3><p className="muted">Workspace members and their RBAC roles.</p></div>{canManage && <button className="primary small" onClick={addUser}><Plus size={15} />Add user</button>}</div><div className="table">{users.map(u => <div className="row" key={u.user_id}><div className="avatar">{u.full_name?.[0]?.toUpperCase()}</div><div className="user-main"><strong>{u.full_name}{u.user_id === me?.user_id ? ' (you)' : ''}</strong><span>{u.email}</span></div><span className={`role ${u.role.toLowerCase()}`}>{u.role}</span></div>)}</div><div className="role-grid"><div><b>Owner</b><span>Full workspace administration</span></div><div><b>Admin</b><span>Manage users, projects and tasks</span></div><div><b>Member</b><span>Work on assigned/created tasks</span></div></div>{canCreateAdmin && <p className="permission-note">As Owner, you can create Admin or Member accounts. Admins can create Members only.</p>}</>; }

function Tenant({ tenant, refresh }) { const [checking, setChecking] = useState(false); async function verify() { setChecking(true); try { await refresh(); } finally { setChecking(false); } } return <div className="tenant-page"><div className="verification-card"><div className="verify-icon"><ShieldCheck size={24} /></div><p className="eyebrow">TENANT IDENTITY</p><h3>{tenant?.name}</h3><p className="muted">{tenant?.description || 'No workspace description configured.'}</p><code>{tenant?.tenant_id}</code><div className="checks">{Object.entries(tenant?.verification || {}).map(([key, value]) => <div key={key}><CheckCircle2 size={17} /><span>{key.replaceAll('_', ' ')}</span><b>{value ? 'PASS' : 'FAIL'}</b></div>)}</div><button className="primary" onClick={verify} disabled={checking}>{checking ? 'Verifying...' : 'Verify tenant context'}</button><p className="muted tiny">Verification confirms the authenticated user's tenant claim resolves to the same tenant record in the database.</p></div></div>; }
function Audit({ logs, canManage }) { if (!canManage) return <Empty text="Audit logs are restricted to Owners and Admins." />; return <><div className="section-head"><div><h3>Audit logs</h3><p className="muted">Security events for this tenant.</p></div></div><div className="table">{logs.map(l => <div className="row" key={l.audit_id}><div className="audit-icon"><ShieldCheck size={16} /></div><div className="user-main"><strong>{l.action} · {l.entity_type}</strong><span>{l.description}</span></div><small>{new Date(l.created_at).toLocaleString()}</small></div>)}{!logs.length && <Empty text="No audit entries yet." />}</div></>; }
const Empty = ({ text }) => <div className="empty">{text}</div>;

function ProjectForm({ users, busy, onClose, onSubmit }) { const [form, setForm] = useState({ name: '', description: '', manager_id: '' }); return <Modal title="Create project" onClose={onClose}><form className="modal-form" onSubmit={e => { e.preventDefault(); onSubmit({ ...form, manager_id: form.manager_id || null }); }}><label>Project name<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label><label>Description<textarea rows="4" placeholder="What is this project about?" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label><label>Manager<select value={form.manager_id} onChange={e => setForm({ ...form, manager_id: e.target.value })}><option value="">No manager</option>{users.map(u => <option key={u.user_id} value={u.user_id}>{u.full_name} · {u.role}</option>)}</select></label><button className="primary" disabled={busy}>{busy ? 'Creating...' : 'Create project'}</button></form></Modal>; }
function UserForm({ busy, canCreateAdmin, onClose, onSubmit }) { const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'Member' }); return <Modal title="Add workspace user" onClose={onClose}><form className="modal-form" onSubmit={e => { e.preventDefault(); onSubmit(form); }}><label>Full name<input required value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} /></label><label>Email<input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>Temporary password<input required minLength="8" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label><label>Role<select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option value="Member">Member</option>{canCreateAdmin && <option value="Admin">Admin</option>}</select></label><button className="primary" disabled={busy}>{busy ? 'Adding...' : 'Add user'}</button></form></Modal>; }
function TaskForm({ project, users, busy, onClose, onSubmit }) { const [form, setForm] = useState({ title: '', description: '', priority: 'medium', assignee_id: '' }); return <Modal title={`Create task · ${project.name}`} onClose={onClose}><form className="modal-form" onSubmit={e => { e.preventDefault(); onSubmit({ ...form, assignee_id: form.assignee_id || null }); }}><label>Task title<input required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label><label>Description<textarea rows="3" placeholder="Task details" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label><div className="form-grid"><label>Priority<select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label><label>Assignee<select value={form.assignee_id} onChange={e => setForm({ ...form, assignee_id: e.target.value })}><option value="">Unassigned</option>{users.map(u => <option key={u.user_id} value={u.user_id}>{u.full_name} · {u.role}</option>)}</select></label></div><button className="primary" disabled={busy}>{busy ? 'Creating...' : 'Create task'}</button></form></Modal>; }

function App() { const [ok, setOk] = useState(!!localStorage.getItem('aegis_token')); return ok ? <Dashboard logout={() => { localStorage.removeItem('aegis_token'); setOk(false); }} /> : <Auth done={() => setOk(true)} />; }
createRoot(document.getElementById('root')).render(<App />);
