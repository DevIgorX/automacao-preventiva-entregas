document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const btnSidebar = document.getElementById('sidebarCollapse');

    // --- LÓGICA DO TOGGLE INTELIGENTE ---
    // Verifica se a URL atual contém '/analisar_dados' ou '/resultado'
    const isResultadoPage = window.location.pathname.includes('/analisar_dados') || 
                            window.location.pathname.includes('/resultado');

    if (isResultadoPage && sidebar) {
        // Adiciona a classe que encolhe a barra lateral automaticamente
        sidebar.classList.add('active');
    }

    // --- MANTÉM O CONTROLE MANUAL ---
    if (btnSidebar && sidebar) {
        btnSidebar.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
    }
});



const allData = {{ data | tojson }};

// Variáveis globais de controle
let currentRawData = []; // Dados crus da aba selecionada (sem filtro)
let currentFilteredData = []; // Dados após filtro

const tableBody = document.getElementById('pedidos-table-body');
const tableTitle = document.getElementById('table-title');

// Referências aos cards
const totalCard = document.getElementById('total-card');
const finalizadosCard = document.getElementById('finalizados-card');
const pendentesCard = document.getElementById('pendentes-card');
const cards = [totalCard, finalizadosCard, pendentesCard];

// ============================================================
// FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO DA TABELA
// ============================================================
function renderTable(pedidos) {
    tableBody.innerHTML = '';
    
    if (!pedidos || pedidos.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum pedido encontrado com os filtros atuais.</td></tr>';
        return;
    }

    // Limite de renderização para não travar o navegador se houver milhares de linhas
    const limite = 500; 
    const dadosParaExibir = pedidos.slice(0, limite);

    dadosParaExibir.forEach(pedido => {
        let status = pedido.Tipo || 'N/A';
        let badgeClass = 'bg-secondary';

        if (status.includes('Entrega Realizada')) {
            badgeClass = 'bg-success';
        } else if (status.includes('Pendente') || status.includes('Saiu para Entrega') || status.includes('Tentativa')) {
            badgeClass = 'bg-warning text-dark';
        } else if (status.includes('devolvida')) {
            badgeClass = 'bg-danger';
        }

        const row = `
            <tr>
                <td>${pedido['cidade_cliente']}</td>
                <td>${pedido['PEDIDO 1P/FULL']}</td>
                <td>${pedido.Entregador}</td>
                <td><span class="badge ${badgeClass}">${status}</span></td>
            </tr>
        `;
        tableBody.innerHTML += row;
    });

    if (pedidos.length > limite) {
        tableBody.innerHTML += `<tr><td colspan="4" class="text-center text-muted">... e mais ${pedidos.length - limite} registros. Baixe o Excel para ver tudo.</td></tr>`;
    }
}

// ============================================================
// LÓGICA DOS FILTROS ESTILO EXCEL
// ============================================================

// Gera os checkboxes dentro dos dropdowns baseados nos dados atuais
function generateFilters(data) {
    // Mapeamento ID do filtro -> Chave no Objeto JSON
    const filterMap = {
        'filter-cidade': 'cidade_cliente',
        'filter-entregador': 'Entregador',
        'filter-status': 'Tipo'
    };

    for (const [elementId, dataKey] of Object.entries(filterMap)) {
        const container = document.getElementById(elementId);
        container.innerHTML = ''; // Limpa opções antigas

        // Pega valores únicos e ordena
        const uniqueValues = [...new Set(data.map(item => item[dataKey] || 'Vazio'))].sort();

        // Adiciona opção "Selecionar Tudo"
        const divAll = document.createElement('div');
        divAll.className = 'form-check border-bottom pb-2 mb-2';
        divAll.innerHTML = `
            <input class="form-check-input select-all" type="checkbox" value="all" id="all-${elementId}" checked>
            <label class="form-check-label fw-bold" for="all-${elementId}">
                (Selecionar Tudo)
            </label>
        `;
        container.appendChild(divAll);

        // Adiciona os checkboxes individuais
        uniqueValues.forEach((val, index) => {
            const div = document.createElement('div');
            div.className = 'form-check filter-option';
            // Cria um ID único seguro para HTML
            const safeId = `${elementId}-${index}`;
            
            div.innerHTML = `
                <input class="form-check-input filter-checkbox" type="checkbox" value="${val}" data-key="${dataKey}" id="${safeId}" checked>
                <label class="form-check-label" for="${safeId}">
                    ${val}
                </label>
            `;
            container.appendChild(div);
        });

        // Evento para "Selecionar Tudo"
        const selectAllCheckbox = divAll.querySelector('.select-all');
        selectAllCheckbox.addEventListener('change', (e) => {
            const checkboxes = container.querySelectorAll('.filter-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            applyFilters();
        });

        // Eventos para checkboxes individuais (para atualizar a tabela)
        const individualCheckboxes = container.querySelectorAll('.filter-checkbox');
        individualCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                // Se desmarcar um, desmarca o "Selecionar Tudo"
                if (!cb.checked) selectAllCheckbox.checked = false;
                applyFilters();
            });
        });
    }
}

// Aplica os filtros selecionados sobre o 'currentRawData'
function applyFilters() {
    // Coleta o estado atual dos filtros
    const activeFilters = {
        'cidade_cliente': [],
        'Entregador': [],
        'Tipo': []
    };

    // Verifica quais checkboxes estão marcados
    document.querySelectorAll('.filter-checkbox:checked').forEach(cb => {
        const key = cb.dataset.key;
        if (activeFilters[key]) {
            activeFilters[key].push(cb.value);
        }
    });

    // Filtra os dados
    currentFilteredData = currentRawData.filter(item => {
        const cidadeMatch = activeFilters['cidade_cliente'].includes(item['cidade_cliente'] || 'Vazio');
        const entregadorMatch = activeFilters['Entregador'].includes(item['Entregador'] || 'Vazio');
        const statusMatch = activeFilters['Tipo'].includes(item['Tipo'] || 'Vazio');
        
        return cidadeMatch && entregadorMatch && statusMatch;
    });

    renderTable(currentFilteredData);
}

// ============================================================
// CONTROLE DE ABAS (CARDS)
// ============================================================

function switchDataSet(dataset, title, activeCard) {
    // 1. Atualiza o visual dos cards
    cards.forEach(card => card.classList.remove('active'));
    if(activeCard) activeCard.classList.add('active');

    // 2. Atualiza Título
    tableTitle.innerText = title;

    // 3. Define os dados globais atuais e reinicia filtros
    currentRawData = dataset; 
    generateFilters(currentRawData); // Recria os filtros com base nos novos dados
    
    // 4. Aplica filtros (que inicialmente estarão todos marcados) e renderiza
    applyFilters(); 
}

// Event Listeners dos Cards
totalCard.addEventListener('click', () => {
    switchDataSet(allData.lista_total, 'Lista Completa de Pedidos', totalCard);
});

finalizadosCard.addEventListener('click', () => {
    switchDataSet(allData.lista_finalizados, 'Detalhes dos Pedidos Finalizados', finalizadosCard);
});

pendentesCard.addEventListener('click', () => {
    switchDataSet(allData.lista_pendentes, 'Detalhes dos Pedidos Pendentes', pendentesCard);
});

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Começa exibindo os pendentes
    switchDataSet(allData.lista_pendentes, 'Detalhes dos Pedidos Pendentes', pendentesCard);
});
