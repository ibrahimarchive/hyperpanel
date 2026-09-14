/**
 * HyperPanel — Monitoring Page
 */
let monitoringWs = null;

async function renderMonitoring() {
    const content = document.getElementById('page-content');
    content.innerHTML = `
        <div class="page-header"><div class="page-header-left"><h1>Monitoring</h1><p>Real-time server performance metrics</p></div></div>
        <div class="grid grid-2" style="margin-bottom:var(--space-5)">
            <div class="card"><div class="card-header"><h3>CPU Usage</h3><span id="mon-cpu-val" class="badge badge-neutral">—</span></div><div class="card-body"><div class="progress" style="height:12px"><div class="progress-bar" id="mon-cpu-bar" style="width:0%"></div></div><div style="margin-top:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)" id="mon-cpu-info">Loading...</div></div></div>
            <div class="card"><div class="card-header"><h3>Memory Usage</h3><span id="mon-mem-val" class="badge badge-neutral">—</span></div><div class="card-body"><div class="progress" style="height:12px"><div class="progress-bar" id="mon-mem-bar" style="width:0%"></div></div><div style="margin-top:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)" id="mon-mem-info">Loading...</div></div></div>
            <div class="card"><div class="card-header"><h3>Disk Usage</h3><span id="mon-disk-val" class="badge badge-neutral">—</span></div><div class="card-body"><div class="progress" style="height:12px"><div class="progress-bar" id="mon-disk-bar" style="width:0%"></div></div><div style="margin-top:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)" id="mon-disk-info">Loading...</div></div></div>
            <div class="card"><div class="card-header"><h3>Network I/O</h3><span id="mon-net-val" class="badge badge-neutral">—</span></div><div class="card-body"><div style="display:flex;gap:var(--space-6)"><div><div style="font-size:var(--text-xs);color:var(--text-tertiary)">↓ Download</div><div id="mon-net-in" style="font-size:var(--text-lg);font-weight:var(--font-bold)">—</div></div><div><div style="font-size:var(--text-xs);color:var(--text-tertiary)">↑ Upload</div><div id="mon-net-out" style="font-size:var(--text-lg);font-weight:var(--font-bold)">—</div></div></div></div></div>
        </div>
        <div class="card"><div class="card-header"><h3>Top Processes</h3><button class="btn btn-ghost btn-sm" onclick="loadProcesses()">↻ Refresh</button></div><div class="card-body" style="padding:0" id="process-table">Loading...</div></div>`;

    startMonitoringWs();
    loadProcesses();
}

function startMonitoringWs() {
    if (monitoringWs) { monitoringWs.close(); }
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    try {
        monitoringWs = new WebSocket(`${protocol}//${location.host}/ws/monitoring`);
        monitoringWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateMonitoringUI(data);
        };
        monitoringWs.onerror = () => { /* Fallback to polling */ startPolling(); };
    } catch (e) { startPolling(); }
}

function startPolling() {
    const poll = async () => {
        if (Router.currentRoute !== '/monitoring') return;
        try { const stats = await API.get('/api/dashboard/stats'); updateMonitoringUI(stats); } catch (e) {}
        setTimeout(poll, 3000);
    };
    poll();
}

function updateMonitoringUI(data) {
    const cpuBar = document.getElementById('mon-cpu-bar');
    const cpuVal = document.getElementById('mon-cpu-val');
    const cpuInfo = document.getElementById('mon-cpu-info');
    if (cpuBar) {
        const cpu = data.cpu;
        cpuBar.style.width = cpu.usage_percent + '%';
        cpuBar.className = 'progress-bar ' + (cpu.usage_percent > 80 ? 'danger' : cpu.usage_percent > 60 ? 'warning' : 'success');
        cpuVal.textContent = cpu.usage_percent + '%';
        cpuInfo.textContent = `${cpu.cores} cores · Load: ${cpu.load_avg_1}, ${cpu.load_avg_5}, ${cpu.load_avg_15}`;
    }
    const memBar = document.getElementById('mon-mem-bar');
    if (memBar && data.memory) {
        memBar.style.width = data.memory.usage_percent + '%';
        memBar.className = 'progress-bar ' + (data.memory.usage_percent > 80 ? 'danger' : data.memory.usage_percent > 60 ? 'warning' : 'success');
        document.getElementById('mon-mem-val').textContent = data.memory.usage_percent + '%';
        document.getElementById('mon-mem-info').textContent = `${data.memory.used_mb.toFixed(0)} / ${data.memory.total_mb.toFixed(0)} MB used`;
    }
    const diskBar = document.getElementById('mon-disk-bar');
    if (diskBar && data.disk) {
        diskBar.style.width = data.disk.usage_percent + '%';
        diskBar.className = 'progress-bar ' + (data.disk.usage_percent > 80 ? 'danger' : data.disk.usage_percent > 60 ? 'warning' : 'success');
        document.getElementById('mon-disk-val').textContent = data.disk.usage_percent + '%';
        document.getElementById('mon-disk-info').textContent = `${data.disk.used_gb} / ${data.disk.total_gb} GB used`;
    }
    if (data.network) {
        document.getElementById('mon-net-val').textContent = data.network.bandwidth_in_mbps + ' Mbps';
        document.getElementById('mon-net-in').textContent = formatBytes(data.network.bytes_recv);
        document.getElementById('mon-net-out').textContent = formatBytes(data.network.bytes_sent);
    }
}

async function loadProcesses() {
    try {
        const processes = await API.get('/api/dashboard/processes');
        const el = document.getElementById('process-table');
        el.innerHTML = `<table class="table"><thead><tr><th>PID</th><th>Name</th><th>User</th><th>CPU %</th><th>Memory %</th><th>Status</th></tr></thead><tbody>
            ${processes.slice(0, 20).map(p => `<tr><td>${p.pid}</td><td><strong>${p.name}</strong></td><td>${p.user}</td><td>${p.cpu}%</td><td>${p.memory}%</td><td><span class="badge ${p.status === 'running' ? 'badge-success' : 'badge-neutral'}">${p.status}</span></td></tr>`).join('')}
        </tbody></table>`;
    } catch (e) { document.getElementById('process-table').innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`; }
}
