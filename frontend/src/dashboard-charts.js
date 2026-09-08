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

const countBy = (items, key, values) => values.map(value => ({
  label: labels[value] || value,
  value: items.filter(item => item[key] === value).length
}));

const maxValue = rows => Math.max(1, ...rows.map(row => row.value));

const chart = (title, subtitle, rows) => `
  <section class="analytics-card">
    <div class="analytics-head"><div><h3>${title}</h3><p>${subtitle}</p></div><span>${rows.reduce((sum, row) => sum + row.value, 0)} total</span></div>
    <div class="bar-chart">
      ${rows.map(row => `
        <div class="bar-row">
          <div class="bar-label"><span>${row.label}</span><b>${row.value}</b></div>
          <div class="bar-track"><div class="bar-fill" style="width:${Math.round((row.value / maxValue(rows)) * 100)}%"></div></div>
        </div>`).join('')}
    </div>
  </section>`;

async function renderAnalytics() {
  const main = document.querySelector('.main');
  const stats = document.querySelector('.stats');
  if (!main || !stats || document.querySelector('.aegis-analytics')) return;

  try {
    const [projects, users] = await Promise.all([api('/projects'), api('/users')]);
    const taskLists = await Promise.all(projects.map(project => api(`/projects/${project.project_id}/tasks`)));
    const tasks = taskLists.flat();
    const analytics = document.createElement('div');
    analytics.className = 'aegis-analytics';
    analytics.innerHTML = `
      <div class="analytics-title"><div><p class="eyebrow">WORKSPACE ANALYTICS</p><h3>At a glance</h3></div><span>Live workspace data</span></div>
      <div class="analytics-grid">
        ${chart('Task status', 'Work currently visible in your workspace.', countBy(tasks, 'status', ['todo', 'in_progress', 'done']))}
        ${chart('Task priority', 'Priority distribution across visible tasks.', countBy(tasks, 'priority', ['high', 'medium', 'low']))}
        ${chart('Project lifecycle', 'Active versus archived projects.', [
          { label: 'Active', value: projects.filter(project => project.status !== 'archived').length },
          { label: 'Archived', value: projects.filter(project => project.status === 'archived').length }
        ])}
        ${chart('Team status', 'Active and inactive workspace users.', [
          { label: 'Active', value: users.filter(user => user.is_active).length },
          { label: 'Inactive', value: users.filter(user => !user.is_active).length }
        ])}
      </div>`;
    stats.insertAdjacentElement('afterend', analytics);
  } catch (_) {
    // Analytics are supplementary; never interfere with the main dashboard.
  }
}

const observer = new MutationObserver(() => {
  const dashboard = document.querySelector('.stats');
  if (dashboard && !document.querySelector('.aegis-analytics')) renderAnalytics();
});

observer.observe(document.body, { childList: true, subtree: true });
setInterval(() => {
  if (document.querySelector('.stats') && !document.querySelector('.aegis-analytics')) renderAnalytics();
}, 10000);
