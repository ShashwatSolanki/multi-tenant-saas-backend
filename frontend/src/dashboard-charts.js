const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = async path => {
  const token = localStorage.getItem('aegis_token');
  const res = await fetch(`${API}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!res.ok) throw new Error('Analytics unavailable');
  return res.json();
};

const labels = {
  todo: 'To do',
  in_progress: 'In progress',
  done: 'Done',
  high: 'High',
  medium: 'Medium',
  low: 'Low'
};

const palettes = {
  status: ['#111827', '#6b7280', '#d1d5db'],
  priority: ['#111827', '#6b7280', '#d1d5db'],
  lifecycle: ['#374151', '#d1d5db'],
  team: ['#374151', '#d1d5db']
};

const countBy = (items, key, values) => values.map(value => ({
  label: labels[value] || value,
  value: items.filter(item => item[key] === value).length
}));

const chart = (title, subtitle, rows, palette) => {
  const total = rows.reduce((sum, row) => sum + row.value, 0);
  let cursor = 0;
  const gradient = total
    ? rows.map((row, i) => {
        const start = cursor;
        cursor += (row.value / total) * 360;
        return `${palette[i]} ${start}deg ${cursor}deg`;
      }).join(', ')
    : '#e5e7eb 0deg 360deg';

  return `
    <section class="analytics-card">
      <div class="analytics-head">
        <div><h3>${title}</h3><p>${subtitle}</p></div>
        <span>${total} total</span>
      </div>
      <div class="analytics-body">
        <div class="donut" style="background:conic-gradient(${gradient})">
          <div class="donut-hole"><strong>${total}</strong><small>items</small></div>
        </div>
        <div class="analytics-legend">
          ${rows.map((row, i) => `
            <div class="legend-row">
              <span><i style="background:${palette[i]}"></i>${row.label}</span>
              <b>${row.value}</b>
            </div>`).join('')}
        </div>
      </div>
    </section>`;
};

let loading = false;
let lastDashboard = false;

const isDashboard = () => document.querySelector('.main .eyebrow')?.textContent?.trim() === 'DASHBOARD';

async function renderAnalytics() {
  const stats = document.querySelector('.main .stats');
  const dashboard = isDashboard();

  if (!dashboard || !stats) {
    document.querySelector('.aegis-analytics')?.remove();
    lastDashboard = false;
    return;
  }

  if (document.querySelector('.aegis-analytics') || loading) return;
  loading = true;

  try {
    const [projects, users] = await Promise.all([api('/projects'), api('/users')]);
    const taskLists = await Promise.all(projects.map(project => api(`/projects/${project.project_id}/tasks`)));
    const tasks = taskLists.flat();

    if (!isDashboard()) return;

    const analytics = document.createElement('div');
    analytics.className = 'aegis-analytics';
    analytics.innerHTML = `
      <div class="analytics-title">
        <div><p class="eyebrow">WORKSPACE ANALYTICS</p><h3>At a glance</h3></div>
        <span>Live workspace data</span>
      </div>
      <div class="analytics-grid">
        ${chart('Task status', 'Current task distribution.', countBy(tasks, 'status', ['todo', 'in_progress', 'done']), palettes.status)}
        ${chart('Task priority', 'Priority mix across visible tasks.', countBy(tasks, 'priority', ['high', 'medium', 'low']), palettes.priority)}
        ${chart('Project lifecycle', 'Active versus archived projects.', [
          { label: 'Active', value: projects.filter(p => p.status !== 'archived').length },
          { label: 'Archived', value: projects.filter(p => p.status === 'archived').length }
        ], palettes.lifecycle)}
        ${chart('Team status', 'Active versus inactive users.', [
          { label: 'Active', value: users.filter(u => u.is_active).length },
          { label: 'Inactive', value: users.filter(u => !u.is_active).length }
        ], palettes.team)}
      </div>`;

    stats.insertAdjacentElement('afterend', analytics);
    lastDashboard = true;
  } catch (_) {
    // Analytics are supplementary and never block the dashboard.
  } finally {
    loading = false;
  }
}

const style = document.createElement('style');
style.textContent = `
.aegis-analytics { margin-top: 28px; }
.analytics-title { display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:14px; }
.analytics-title h3 { margin:2px 0 0; }
.analytics-title > span { font-size:11px; color:#9ca3af; }
.analytics-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
.analytics-card { background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:16px; box-shadow:0 4px 16px rgba(17,24,39,.04); }
.analytics-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
.analytics-head h3 { margin:0; font-size:13px; }
.analytics-head p { margin:4px 0 0; color:#9ca3af; font-size:10px; }
.analytics-head > span { background:#f3f4f6; color:#6b7280; border-radius:999px; padding:4px 7px; font-size:9px; white-space:nowrap; }
.analytics-body { display:flex; align-items:center; gap:22px; padding-top:16px; }
.donut { width:104px; height:104px; flex:0 0 104px; border-radius:50%; display:grid; place-items:center; box-shadow:inset 0 0 0 1px rgba(17,24,39,.04); }
.donut-hole { width:58px; height:58px; border-radius:50%; background:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.donut-hole strong { font-size:18px; line-height:18px; color:#111827; }
.donut-hole small { color:#9ca3af; font-size:8px; margin-top:2px; }
.analytics-legend { flex:1; display:flex; flex-direction:column; gap:9px; }
.legend-row { display:flex; justify-content:space-between; align-items:center; font-size:10px; color:#6b7280; }
.legend-row span { display:flex; align-items:center; gap:7px; }
.legend-row i { width:8px; height:8px; border-radius:50%; display:inline-block; }
.legend-row b { color:#111827; font-size:11px; }
@media (max-width:760px) { .analytics-grid { grid-template-columns:1fr; } }
`;
document.head.appendChild(style);

const observer = new MutationObserver(() => {
  const dashboard = isDashboard();
  if (!dashboard && (lastDashboard || document.querySelector('.aegis-analytics'))) {
    document.querySelector('.aegis-analytics')?.remove();
    lastDashboard = false;
  }
  if (dashboard && !document.querySelector('.aegis-analytics')) renderAnalytics();
});
observer.observe(document.body, { childList: true, subtree: true });
renderAnalytics();
