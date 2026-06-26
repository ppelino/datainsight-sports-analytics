const API = 'https://datainsight-sports-analytics.onrender.com';

let token = localStorage.getItem('token');
let chart;

const $ = s => document.querySelector(s);

const authHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
});

async function api(path, opts = {}) {
    const r = await fetch(API + path, opts);

    if (!r.ok) {
        let msg = 'Erro';
        try {
            const data = await r.json();
            msg = data.detail || msg;
        } catch {}
        throw new Error(msg);
    }

    return r.json();
}

function formObj(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function show(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    $('#' + id).classList.remove('hidden');
    refresh();
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    location.reload();
}

async function register() {
    try {
        const r = await api('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: $('#name').value,
                email: $('#email').value,
                password: $('#password').value
            })
        });

        token = r.token;
        localStorage.setItem('token', token);
        boot();
    } catch (e) {
        alert(e.message);
    }
}

async function login() {
    try {
        const r = await api('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email: $('#email').value,
                password: $('#password').value
            })
        });

        token = r.token;
        localStorage.setItem('token', token);
        boot();
    } catch (e) {
        alert(e.message);
    }
}

async function boot() {
    if (!token) return;

    $('#auth').classList.add('hidden');
    $('#app').classList.remove('hidden');

    await refresh();
}

async function refresh() {
    if (!token) return;

    await Promise.all([
        loadTeams(),
        loadAthletes(),
        loadMatches(),
        loadDashboard(),
        loadScout(),
        loadOpponents(),
        loadPlans()
    ]);
}

function opt(select, data, label) {
    document.querySelectorAll(select).forEach(s => {
        const val = s.value;

        s.innerHTML = '<option value="">Selecione</option>' +
            data.map(x => `<option value="${x.id}">${label(x)}</option>`).join('');

        s.value = val;
    });
}

function setForm(formSelector, data) {
    const form = document.querySelector(formSelector);

    Object.keys(data).forEach(k => {
        if (form.elements[k]) {
            form.elements[k].value = data[k] ?? '';
        }
    });

    form.dataset.editId = data.id;
    form.querySelector('button').textContent = 'Atualizar';

    window.scrollTo({
        top: form.offsetTop - 120,
        behavior: 'smooth'
    });
}

function clearForm(form) {
    form.reset();
    delete form.dataset.editId;
    form.querySelector('button').textContent = form.dataset.label || 'Salvar';
}

async function excluir(path, nome) {
    if (!confirm(`Deseja excluir ${nome}?`)) return;

    try {
        await api(path, {
            method: 'DELETE',
            headers: authHeaders()
        });

        await refresh();
    } catch (e) {
        alert(e.message);
    }
}

/* TIMES */
async function loadTeams() {
    const data = await api('/api/teams', {
        headers: authHeaders()
    });

    opt('select[name="team_id"]', data, x => x.name);

    $('#teamList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.name}</b><br>
            <small>${x.category || ''} - ${x.city || ''} - Técnico: ${x.coach || ''}</small>
            <p>${x.notes || ''}</p>
            <button onclick='setForm("#teams form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="baixarTeamPDF(${x.id})">PDF</button>
            <button onclick="excluir('/api/teams/${x.id}','este time')">Excluir</button>
        </div>
    `).join('');
}

async function saveTeam(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;
    const method = id ? 'PUT' : 'POST';
    const path = id ? `/api/teams/${id}` : '/api/teams';

    await api(path, {
        method,
        headers: authHeaders(),
        body: JSON.stringify(formObj(form))
    });

    clearForm(form);
    refresh();
}

/* ATLETAS */
async function loadAthletes() {
    const data = await api('/api/athletes', {
        headers: authHeaders()
    });

    opt('select[name="athlete_id"]', data, x => x.name + ' - ' + (x.position || ''));

    $('#athleteList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.name}</b><br>
            <small>${x.position || ''} | ${x.dominant_foot || ''} | ${x.age || 0} anos | ${x.height || 0}m | ${x.weight || 0}kg</small>
            <p>
                <b>Fortes:</b> ${x.strengths || ''}<br>
                <b>Melhorar:</b> ${x.weaknesses || ''}
            </p>
            <button onclick='setForm("#athletes form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="baixarAthletePDF(${x.id})">PDF</button>
            <button onclick="excluir('/api/athletes/${x.id}','este atleta')">Excluir</button>
        </div>
    `).join('');
}

async function saveAthlete(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;
    const o = formObj(form);

    o.team_id = Number(o.team_id || 0);
    o.age = Number(o.age || 0);
    o.height = parseFloat(o.height || 0);
    o.weight = parseFloat(o.weight || 0);

    await api(id ? `/api/athletes/${id}` : '/api/athletes', {
        method: id ? 'PUT' : 'POST',
        headers: authHeaders(),
        body: JSON.stringify(o)
    });

    clearForm(form);
    refresh();
}

/* JOGOS */
async function loadMatches() {
    const data = await api('/api/matches', {
        headers: authHeaders()
    });

    opt('select[name="match_id"]', data, x => `${x.match_date} - ${x.opponent}`);

    $('#matchList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.match_date} - ${x.opponent}</b><br>
            <small>${x.competition || ''} | ${x.location || ''} | ${x.formation || ''}</small>
            <p>Placar: ${x.goals_for} x ${x.goals_against}<br>${x.notes || ''}</p>
            <button onclick='setForm("#matches form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="baixarMatchPDF(${x.id})">PDF</button>
            <button onclick="excluir('/api/matches/${x.id}','este jogo')">Excluir</button>
        </div>
    `).join('');
}

async function saveMatch(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;
    const o = formObj(form);

    o.team_id = Number(o.team_id || 0);
    o.goals_for = Number(o.goals_for || 0);
    o.goals_against = Number(o.goals_against || 0);

    await api(id ? `/api/matches/${id}` : '/api/matches', {
        method: id ? 'PUT' : 'POST',
        headers: authHeaders(),
        body: JSON.stringify(o)
    });

    clearForm(form);
    refresh();
}

/* SCOUT */
async function loadScout() {
    const data = await api('/api/scout', {
        headers: authHeaders()
    });

    $('#scoutList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.minute}' - ${x.event_type}</b><br>
            <small>${x.zone || ''} | ${x.result || ''}</small>
            <p>${x.notes || ''}</p>
            <button onclick='setForm("#scout form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="excluir('/api/scout/${x.id}','este evento')">Excluir</button>
        </div>
    `).join('');
}

async function saveScout(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;
    const o = formObj(form);

    o.match_id = Number(o.match_id || 0);
    o.athlete_id = o.athlete_id ? Number(o.athlete_id) : null;
    o.minute = Number(o.minute || 0);

    await api(id ? `/api/scout/${id}` : '/api/scout', {
        method: id ? 'PUT' : 'POST',
        headers: authHeaders(),
        body: JSON.stringify(o)
    });

    clearForm(form);
    refresh();
}

/* ADVERSÁRIOS */
async function loadOpponents() {
    const data = await api('/api/opponents', {
        headers: authHeaders()
    });

    $('#opponentList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.opponent}</b><br>
            <small>Formação: ${x.base_formation || ''} | Lado forte: ${x.attack_side || ''}</small>
            <p>
                <b>Fortes:</b> ${x.strengths || ''}<br>
                <b>Fracos:</b> ${x.weaknesses || ''}<br>
                <b>Como faz gols:</b> ${x.how_scores || ''}<br>
                <b>Como sofre:</b> ${x.how_concedes || ''}
            </p>
            <button onclick='setForm("#opponents form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="baixarOpponentPDF(${x.id})">PDF</button>
            <button onclick="excluir('/api/opponents/${x.id}','esta análise')">Excluir</button>
        </div>
    `).join('');
}

async function saveOpponent(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;

    await api(id ? `/api/opponents/${id}` : '/api/opponents', {
        method: id ? 'PUT' : 'POST',
        headers: authHeaders(),
        body: JSON.stringify(formObj(form))
    });

    clearForm(form);
    refresh();
}

/* PLANOS DE JOGO */
async function loadPlans() {
    const data = await api('/api/gameplans', {
        headers: authHeaders()
    });

    $('#planList').innerHTML = data.map(x => `
        <div class="item">
            <b>${x.opponent} - ${x.recommended_formation || ''}</b>
            <p>
                <b>Defesa:</b> ${x.defensive_strategy || ''}<br>
                <b>Ataque:</b> ${x.offensive_strategy || ''}<br>
                <b>Marcação:</b> ${x.individual_marking || ''}<br>
                <b>Bola parada:</b> ${x.set_piece_plan || ''}<br>
                <b>Substituições:</b> ${x.substitutions || ''}<br>
                <b>Sugestão:</b> ${x.ai_suggestion || ''}
            </p>
            <button onclick='setForm("#plans form", ${JSON.stringify(x)})'>Editar</button>
            <button onclick="baixarPlanoPDF(${x.id})">PDF</button>
            <button onclick="excluir('/api/gameplans/${x.id}','este plano')">Excluir</button>
        </div>
    `).join('');
}

async function savePlan(e) {
    e.preventDefault();

    const form = e.target;
    const id = form.dataset.editId;

    await api(id ? `/api/gameplans/${id}` : '/api/gameplans', {
        method: id ? 'PUT' : 'POST',
        headers: authHeaders(),
        body: JSON.stringify(formObj(form))
    });

    clearForm(form);
    refresh();
}


async function baixarPDF(path, nomeArquivo) {
    const r = await fetch(`${API}${path}`, {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    });

    if (!r.ok) {
        alert('Erro ao gerar PDF');
        return;
    }

    const blob = await r.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nomeArquivo;
    a.click();
    window.URL.revokeObjectURL(url);
}

function baixarTeamPDF(id) {
    baixarPDF(`/api/teams/${id}/pdf`, `time_${id}.pdf`);
}

function baixarAthletePDF(id) {
    baixarPDF(`/api/athletes/${id}/pdf`, `atleta_${id}.pdf`);
}

function baixarMatchPDF(id) {
    baixarPDF(`/api/matches/${id}/pdf`, `jogo_${id}.pdf`);
}

function baixarOpponentPDF(id) {
    baixarPDF(`/api/opponents/${id}/pdf`, `adversario_${id}.pdf`);
}

function baixarScoutPDF() {
    baixarPDF('/api/scout/pdf', 'scout.pdf');
}

async function baixarPlanoPDF(id) {
    const r = await fetch(`${API}/api/gameplans/${id}/pdf`, {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    });

    if (!r.ok) {
        alert('Erro ao gerar PDF');
        return;
    }

    const blob = await r.blob();
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
}

/* DASHBOARD */
async function loadDashboard() {
    const d = await api('/api/dashboard', {
        headers: authHeaders()
    });

    $('#cards').innerHTML = [
        ['⚽ Times', d.teams],
        ['🏃 Atletas', d.athletes],
        ['🏆 Jogos', d.matches],
        ['✅ Vitórias', d.wins],
        ['🤝 Empates', d.draws],
        ['❌ Derrotas', d.losses],
        ['🥅 Gols pró', d.goals_for],
        ['🛡️ Gols contra', d.goals_against],
        ['📊 Saldo', d.saldo],
        ['🔥 Aproveitamento', (d.aproveitamento || 0) + '%'],
        ['⚽ Média GP', d.media_gols_pro || 0],
        ['🧤 Média GC', d.media_gols_contra || 0]
    ].map(x => `
        <div class="metric">
            <span>${x[0]}</span>
            <b>${x[1]}</b>
        </div>
    `).join('');

    const labels = Object.keys(d.event_counts || {});
    const vals = Object.values(d.event_counts || {});

    if (chart) chart.destroy();

    chart = new Chart($('#chart'), {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['Sem scout'],
            datasets: [{
                label: 'Eventos de scout',
                data: vals.length ? vals : [0]
            }]
        },
     options: {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
        legend: {
            display: false
        },
        title: {
            display: true,
            text: 'Eventos de Scout por Tipo'
        }
    },

    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                precision: 0
            }
        }
    }
} 
    });

    if (!document.querySelector('#dashExtras')) {
        $('#dash').insertAdjacentHTML('beforeend', `
            <div id="dashExtras" class="grid" style="margin-top:25px;"></div>
        `);
    }

    $('#dashExtras').innerHTML = `
        <div class="item">
            <b>🏆 Últimos jogos</b>
            ${
                d.last_matches && d.last_matches.length
                ? d.last_matches.map(m => `
                    <p>${m.date} - ${m.opponent} | ${m.score} | ${m.formation || ''}</p>
                `).join('')
                : '<p>Nenhum jogo cadastrado ainda.</p>'
            }
        </div>

        <div class="item">
            <b>🥇 Ranking de atletas</b>
            ${
                d.ranking_athletes && d.ranking_athletes.length
                ? d.ranking_athletes.map((a, i) => `
                    <p>${i + 1}. ${a.name} - ${a.events} eventos</p>
                `).join('')
                : '<p>Nenhum evento de atleta registrado ainda.</p>'
            }
        </div>

        <div class="item">
            <b>🗺️ Zonas mais usadas</b>
            ${
                d.zone_counts && Object.keys(d.zone_counts).length
                ? Object.entries(d.zone_counts).map(([zone, total]) => `
                    <p>${zone}: ${total} ações</p>
                `).join('')
                : '<p>Nenhuma zona registrada ainda.</p>'
            }
        </div>
    `;
}
async function baixarScoutCSV() {

    const r = await fetch(`${API}/api/scout/csv`, {
        headers: {
            Authorization: 'Bearer ' + token
        }
    });

    if (!r.ok) {
        alert("Erro ao exportar CSV");
        return;
    }

    const blob = await r.blob();

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');

    a.href = url;
    a.download = "Scout.csv";

    a.click();

    window.URL.revokeObjectURL(url);
}

boot();

