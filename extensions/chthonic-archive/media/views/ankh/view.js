const vscode = acquireVsCodeApi();
const hmrKey = 'chthonic.hmr.ankh.reloadCount';
const reloadCount = Number(sessionStorage.getItem(hmrKey) || '0');
const sections = {{sectionsJsonInlined}};
const listEl = document.getElementById('list');
const searchEl = document.getElementById('search');
const countEl = document.getElementById('count');
let activeItem = null;
let activeKind = 'all';

const kindIcons = { heading: '§', entity: '⚙', tier: '♔', xref: '→', anchor: '⚓', mention: '◆' };

function render(filter) {
    const q = (filter || '').toLowerCase();
    let filtered = sections;
    if (activeKind !== 'all') {
        filtered = filtered.filter(s => s.k === activeKind);
    }
    if (q) {
        filtered = filtered.filter(s =>
            s.t.toLowerCase().includes(q) ||
            (s.s && s.s.toLowerCase().includes(q)) ||
            (s.g && s.g.toLowerCase().includes(q))
        );
    }

    listEl.innerHTML = '';
    activeItem = null;
    countEl.textContent = filtered.length + ' / ' + sections.length + ' entries';

    filtered.forEach(sec => {
        const div = document.createElement('div');
        div.className = 'section-item l' + sec.l;
        div.setAttribute('data-kind', sec.k);
        const icon = kindIcons[sec.k] || '';
        div.innerHTML =
            '<div class="section-title"><span class="kind-icon">' + icon + '</span>' + escHtml(sec.t) + '</div>' +
            '<div class="snippet">' + escHtml(sec.s || '') + '</div>' +
            '<span class="open-link">Open in editor ↗</span>';

        div.querySelector('.section-title').addEventListener('click', () => {
            if (activeItem === div) {
                activeItem.classList.remove('active');
                activeItem = null;
            } else {
                if (activeItem) { activeItem.classList.remove('active'); }
                div.classList.add('active');
                activeItem = div;
            }
        });

        div.querySelector('.open-link').addEventListener('click', (e) => {
            e.stopPropagation();
            vscode.postMessage({ type: 'open', line: sec.n });
        });

        listEl.appendChild(div);
    });
}

function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeKind = btn.getAttribute('data-kind');
        render(searchEl.value);
    });
});

searchEl.addEventListener('input', () => render(searchEl.value));
render('');

function postHmrLoaded() {
    vscode.postMessage({
        type: 'webviewHmr.loaded',
        surface: 'ankh',
        reloadCount,
        html: document.documentElement.outerHTML,
    });
}

window.addEventListener('message', (event) => {
    if (event.data?.type !== 'reload') {
        return;
    }
    sessionStorage.setItem(hmrKey, String(reloadCount + 1));
    vscode.postMessage({ type: 'webviewHmr.reloadRequested', surface: 'ankh' });
    setTimeout(() => location.reload(), 100);
});

postHmrLoaded();
