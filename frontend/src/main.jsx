import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LayoutDashboard, FolderKanban, Users, ClipboardList, ShieldCheck, LogOut, Plus } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function api(path, options = {}) {
  const token = localStorage.getItem('aegis_token');
  const res = await fetch(`${API}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function Auth({ done }) {
  const [register, setRegister] = useState(false), [form, setForm] = useState({ tenant_name:'', full_name:'', email:'', password:'' }), [error, setError] = useState('');
  async function submit(e) { e.preventDefault(); try { const data = await api(register ? '/auth/register' : '/auth/login', { method:'POST', body:JSON.stringify(form) }); localStorage.setItem('aegis_token', data.access_token); done(); } catch (err) { setError(err.message); } }
  return <main className="auth"><div className="auth-card"><div className="mark">A</div><p className="eyebrow">PROJECT AEGIS</p><h1>Secure workspaces,<br/>built for teams.</h1><p className="muted">Multi-tenant project management with strict isolation, RBAC and auditability.</p><form onSubmit={submit}>{register && <><input placeholder="Organization name" onChange={e=>setForm({...form,tenant_name:e.target.value})}/><input placeholder="Full name" onChange={e=>setForm({...form,full_name:e.target.value})}/></>}<input type="email" placeholder="Email" onChange={e=>setForm({...form,email:e.target.value})}/><input type="password" placeholder="Password" onChange={e=>setForm({...form,password:e.target.value})}/><button className="primary">{register?'Create workspace':'Sign in'}</button></form>{error&&<div className="error">{error}</div>}<button className="link" onClick={()=>setRegister(!register)}>{register?'Already registered? Sign in':'Create a new workspace'}</button></div></main>;
}

function Dashboard({ logout }) {
  const [tab,setTab]=useState('dashboard'), [me,setMe]=useState(null), [projects,setProjects]=useState([]), [users,setUsers]=useState([]), [tasks,setTasks]=useState([]), [logs,setLogs]=useState([]), [error,setError]=useState('');
  const load=async()=>{try{setError('');const [m,p,u]=await Promise.all([api('/me'),api('/projects'),api('/users')]);setMe(m);setProjects(p);setUsers(u);const all=[];for(const project of p){const ts=await api(`/projects/${project.project_id}/tasks`);all.push(...ts.map(t=>({...t,project_name:project.name})))}setTasks(all)}catch(e){setError(e.message)}};
  useEffect(()=>{load()},[]);
  const audit=async()=>{try{setLogs(await api('/audit-logs'))}catch(e){setError(e.message)}};
  const newProject=async()=>{const name=prompt('Project name');if(name)try{await api('/projects',{method:'POST',body:JSON.stringify({name})});load()}catch(e){setError(e.message)}};
  const newTask=async p=>{const title=prompt('Task title');if(title)try{await api(`/projects/${p.project_id}/tasks`,{method:'POST',body:JSON.stringify({title})});load()}catch(e){setError(e.message)}};
  const nav=[['dashboard','Dashboard',LayoutDashboard],['projects','Projects',FolderKanban],['tasks','Tasks',ClipboardList],['team','Team',Users],['audit','Audit logs',ShieldCheck]];
  return <div className="shell"><aside><div className="logo"><b>A</b> AEGIS</div><div className="tenant">WORKSPACE<strong>{me?.full_name||'Loading...'}</strong></div><nav>{nav.map(([id,label,Icon])=><button className={tab===id?'active':''} onClick={()=>{setTab(id);if(id==='audit')audit()}}><Icon size={17}/>{label}</button>)}</nav><button className="logout" onClick={logout}><LogOut size={17}/>Sign out</button></aside><main className="main"><header><div><p className="eyebrow">{tab.toUpperCase()}</p><h2>{tab==='dashboard'?'Good to see you.':'Workspace'}</h2></div><button className="icon" onClick={load}>↻</button></header>{error&&<div className="error">{error}</div>}{tab==='dashboard'&&<Home projects={projects} tasks={tasks} users={users} add={newProject}/>} {tab==='projects'&&<Projects projects={projects} add={newProject} task={newTask}/>} {tab==='tasks'&&<Tasks tasks={tasks}/>} {tab==='team'&&<Team users={users}/>} {tab==='audit'&&<Audit logs={logs}/>}</main></div>;
}
const Stat=({label,value,Icon})=><div className="stat"><Icon size={18}/><div><small>{label}</small><strong>{value}</strong></div></div>;
function Home({projects,tasks,users,add}){return <><div className="stats"><Stat label="Projects" value={projects.length} Icon={FolderKanban}/><Stat label="Open tasks" value={tasks.filter(t=>t.status!=='done').length} Icon={ClipboardList}/><Stat label="Team members" value={users.length} Icon={Users}/><Stat label="Completed" value={tasks.filter(t=>t.status==='done').length} Icon={ShieldCheck}/></div><div className="head"><div><h3>Projects</h3><p className="muted">Your tenant-scoped portfolio.</p></div><button className="primary small" onClick={add}><Plus size={15}/>New project</button></div><div className="cards">{projects.map(p=><article className="card" key={p.project_id}><span className="pill">{p.status}</span><h3>{p.name}</h3><p>{p.description||'No description yet.'}</p></article>)}{!projects.length&&<Empty text="No projects yet. Create your first project."/>}</div></>}
function Projects({projects,add,task}){return <><div className="head"><div><h3>All projects</h3><p className="muted">Projects are isolated by tenant.</p></div><button className="primary small" onClick={add}><Plus size={15}/>New project</button></div><div className="table">{projects.map(p=><div className="row" key={p.project_id}><div><b>{p.name}</b><span>{p.description||'No description'}</span></div><span className="pill">{p.status}</span><button className="ghost" onClick={()=>task(p)}>+ Task</button></div>)}{!projects.length&&<Empty text="No projects found."/>}</div></>}
function Tasks({tasks}){return <><div className="head"><div><h3>Task board</h3><p className="muted">Tenant-scoped project tasks.</p></div></div><div className="task-grid">{['todo','in_progress','done'].map(s=><div className="col" key={s}><b>{s.replace('_',' ')}</b>{tasks.filter(t=>t.status===s).map(t=><article className="task" key={t.task_id}><strong>{t.title}</strong><span>{t.project_name}</span><small>{t.priority} priority</small></article>)}</div>)}</div></>}
function Team({users}){return <><div className="head"><div><h3>Team</h3><p className="muted">Current tenant members and roles.</p></div></div><div className="table">{users.map(u=><div className="row" key={u.user_id}><div className="avatar">{u.full_name[0]}</div><div><b>{u.full_name}</b><span>{u.email}</span></div><span className="role">{u.role}</span></div>)}</div></>}
function Audit({logs}){return <><div className="head"><div><h3>Audit logs</h3><p className="muted">Security events for Owners and Admins.</p></div></div><div className="table">{logs.map(l=><div className="row" key={l.audit_id}><ShieldCheck size={16}/><div><b>{l.action} · {l.entity_type}</b><span>{l.description}</span></div><small>{new Date(l.created_at).toLocaleString()}</small></div>)}{!logs.length&&<Empty text="No audit entries yet."/>}</div></>}
const Empty=({text})=><div className="empty">{text}</div>;
function App(){const [ok,setOk]=useState(!!localStorage.getItem('aegis_token'));return ok?<Dashboard logout={()=>{localStorage.removeItem('aegis_token');setOk(false)}}/>:<Auth done={()=>setOk(true)}/>}

createRoot(document.getElementById('root')).render(<App/>);
