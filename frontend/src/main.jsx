import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LayoutDashboard, FolderKanban, Users, ClipboardList, ShieldCheck, LogOut, Plus, RefreshCw, MessageSquare, CheckCircle2 } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request(path, options = {}) {
  const token = localStorage.getItem('aegis_token');
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ tenant_name: '', full_name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const submit = async (e) => {
    e.preventDefault(); setError('');
    try {
      const data = await request(`/auth/${mode === 'login' ? 'login' : 'register'}`, { method: 'POST', body: JSON.stringify(form) });
      localStorage.setItem('aegis_token', data.access_token); onLogin();
    } catch (err) { setError(err.message); }
  };
  return <main className="auth-shell"><section className="auth-card">
    <div className="brand-mark">A</div><p className="eyebrow">PROJECT AEGIS</p><h1>Secure workspaces,<br/>built for teams.</h1><p className="muted">Multi-tenant project management with isolation, RBAC and auditability.</p>
    <form onSubmit={submit}>{mode === 'register' && <><input placeholder="Organization name" value={form.tenant_name} onChange={e=>setForm({...form,tenant_name:e.target.value})}/><input placeholder="Your full name" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></>}<input type="email" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input type="password" placeholder="Password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/><button className="primary">{mode === 'login' ? 'Sign in' : 'Create workspace'}</button></form>
    {error && <div className="error">{error}</div>}<button className="link" onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login'?'Create a new workspace':'Already have an account? Sign in'}</button>
  </section></main>;
}

function App() {
  const [authenticated, setAuthenticated] = useState(!!localStorage.getItem('aegis_token'));
  if (!authenticated) return <Auth onLogin={()=>setAuthenticated(true)} />;
  return <Dashboard onLogout={()=>{localStorage.removeItem('aegis_token');setAuthenticated(false)}}/>;
}

function Dashboard({ onLogout }) {
  const [tab, setTab] = useState('dashboard');
  const [me, setMe] = useState(null), [projects, setProjects] = useState([]), [users, setUsers] = useState([]), [logs, setLogs] = useState([]), [tasks, setTasks] = useState([]);
  const [error, setError] = useState('');
  const load = async () => { try { setError(''); const [m,p,u] = await Promise.all([request('/me'),request('/projects'),request('/users')]); setMe(m);setProjects(p);setUsers(u); const all=[]; for(const project of p){ const ts=await request(`/projects/${project.project_id}/tasks`); all.push(...ts.map(t=>({...t,project_name:project.name}))); } setTasks(all); } catch(e){setError(e.message)} };
  useEffect(()=>{load()},[]);
  const loadLogs=async()=>{try{setLogs(await request('/audit-logs'))}catch(e){setError(e.message)}};
  const createProject=async()=>{const name=prompt('Project name');if(!name)return;try{await request('/projects',{method:'POST',body:JSON.stringify({name})});load()}catch(e){setError(e.message)}};
  const createTask=async(project)=>{const title=prompt(`New task for ${project.name}`);if(!title)return;try{await request(`/projects/${project.project_id}/tasks`,{method:'POST',body:JSON.stringify({title})});load()}catch(e){setError(e.message)}};
  const nav=[['dashboard','Dashboard',LayoutDashboard],['projects','Projects',FolderKanban],['tasks','Tasks',ClipboardList],['team','Team',Users],['audit','Audit logs',ShieldCheck]];
  const content = tab==='dashboard' ? <Home projects={projects} tasks={tasks} users={users} onProject={createProject}/> : tab==='projects' ? <Projects projects={projects} onAdd={createProject} onTask={createTask}/> : tab==='tasks' ? <Tasks tasks={tasks}/> : tab==='team' ? <Team users={users} me={me}/> : <Audit logs={logs} load={loadLogs}/>;
  return <div className="app-shell"><aside><div className="logo"><span>A</span><b>AEGIS</b></div><div className="tenant">{me?.tenant_id ? 'TENANT WORKSPACE' : 'WORKSPACE'}<strong>{me?.full_name || 'Loading...'}</strong></div><nav>{nav.map(([id,label,Icon])=><button key={id} className={tab===id?'active':''} onClick={()=>{setTab(id);if(id==='audit')loadLogs()}}><Icon size={18}/>{label}</button>)}</nav><button className="logout" onClick={onLogout}><LogOut size={18}/>Sign out</button></aside><main className="main"><header><div><p className="eyebrow">{tab.toUpperCase()}</p><h2>{tab==='dashboard'?'Good to see you.':tab==='audit'?'Security & activity':'Workspace'}</h2></div><button className="icon-btn" onClick={load}><RefreshCw size={18}/></button></header>{error&&<div className="error banner">{error}</div>}{content}</main></div>;
}

const Stat=({label,value,icon:Icon})=><div className="stat"><div className="stat-icon"><Icon size={19}/></div><div><small>{label}</small><strong>{value}</strong></div></div>;
function Home({projects,tasks,users,onProject}){return <><div className="stats"><Stat label="Projects" value={projects.length} icon={FolderKanban}/><Stat label="Open tasks" value={tasks.filter(t=>t.status!=='done').length} icon={ClipboardList}/><Stat label="Team members" value={users.length} icon={Users}/><Stat label="Completed" value={tasks.filter(t=>t.status==='done').length} icon={CheckCircle2}/></div><div className="section-head"><div><h3>Projects</h3><p className="muted">Your tenant-scoped project portfolio.</p></div><button className="primary small" onClick={onProject}><Plus size={16}/>New project</button></div><div className="cards">{projects.slice(0,6).map(p=><div className="project-card" key={p.project_id}><div className="project-top"><span className="dot"/><span className="pill">{p.status}</span></div><h3>{p.name}</h3><p>{p.description || 'No description yet.'}</p><div className="card-foot"><span>{tasks.filter(t=>t.project_id===p.project_id).length} tasks</span><span>{new Date(p.created_at).toLocaleDateString()}</span></div></div>)}{!projects.length&&<Empty text="No projects yet. Create your first workspace project."/>}</div></>}
function Projects({projects,onAdd,onTask}){return <><div className="section-head"><div><h3>All projects</h3><p className="muted">Projects are isolated by tenant.</p></div><button className="primary small" onClick={onAdd}><Plus size={16}/>New project</button></div><div className="table">{projects.map(p=><div className="row" key={p.project_id}><div><strong>{p.name}</strong><span>{p.description||'No description'}</span></div><span className="pill">{p.status}</span><button className="ghost" onClick={()=>onTask(p)}><Plus size={15}/>Task</button></div>)}{!projects.length&&<Empty text="No projects found."/>}</div></>}
function Tasks({tasks}){return <><div className="section-head"><div><h3>Task board</h3><p className="muted">Every task is resolved through its tenant-scoped project.</p></div></div><div className="task-grid">{['todo','in_progress','done'].map(status=><div className="task-col" key={status}><div className="col-title"><span>{status.replace('_',' ')}</span><b>{tasks.filter(t=>t.status===status).length}</b></div>{tasks.filter(t=>t.status===status).map(t=><div className="task" key={t.task_id}><strong>{t.title}</strong><span>{t.project_name}</span><small>{t.priority} priority</small></div>)}</div>)}</div></>}
function Team({users,me}){return <><div className="section-head"><div><h3>Team</h3><p className="muted">Current tenant members and roles.</p></div></div><div className="table">{users.map(u=><div className="row" key={u.user_id}><div className="avatar">{u.full_name?.[0]}</div><div className="user-main"><strong>{u.full_name}</strong><span>{u.email}</span></div><span className="role">{u.role}</span></div>)}</div></>}
function Audit({logs,load}){return <><div className="section-head"><div><h3>Audit logs</h3><p className="muted">Security events visible to Owners and Admins.</p></div><button className="ghost" onClick={load}><RefreshCw size={15}/>Refresh</button></div><div className="table">{logs.map(l=><div className="row" key={l.audit_id}><div className="audit-icon"><ShieldCheck size={16}/></div><div className="user-main"><strong>{l.action} · {l.entity_type}</strong><span>{l.description||'Activity recorded'}</span></div><span>{new Date(l.created_at).toLocaleString()}</span></div>)}{!logs.length&&<Empty text="No audit entries yet."/>}</div></>}
const Empty=({text})=><div className="empty">{text}</div>;

createRoot(document.getElementById('root')).render(<App/>);
