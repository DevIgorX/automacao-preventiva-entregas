        const allData = {{ data | tojson }};
        const totalCard = document.getElementById('total-card');
        const finalizadosCard = document.getElementById('finalizados-card');
        const pendentesCard = document.getElementById('pendentes-card');
        const tableTitle = document.getElementById('table-title');
        const tableBody = document.getElementById('pedidos-table-body');
        const cards = [totalCard, finalizadosCard, pendentesCard];

        function renderTable(pedidos, title) {
            tableBody.innerHTML = '';
            tableTitle.innerText = title;
            if (pedidos.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum pedido encontrado para esta categoria.</td></tr>';
                return;
            }
            pedidos.forEach(pedido => {
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
                        <td>${pedido['Cidade Cliente']}</td>
                        <td>${pedido.pedido_gemco}</td>
                        <td>${pedido.Entregador}</td>
                        <td><span class="badge ${badgeClass}">${status}</span></td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        }

        function setActiveCard(activeCard) {
            if (activeCard) {
                cards.forEach(card => card.classList.remove('active'));
                activeCard.classList.add('active');
            } else {
                cards.forEach(card => card.classList.remove('active'));
            }
        }

        totalCard.addEventListener('click', () => {
            setActiveCard(totalCard);
            renderTable(allData.lista_total, 'Lista Completa de Pedidos');
        });

        finalizadosCard.addEventListener('click', () => {
            setActiveCard(finalizadosCard);
            renderTable(allData.lista_finalizados, 'Detalhes dos Pedidos Finalizados');
        });

        pendentesCard.addEventListener('click', () => {
            setActiveCard(pendentesCard);
            renderTable(allData.lista_pendentes, 'Detalhes dos Pedidos Pendentes');
        });

        document.addEventListener('DOMContentLoaded', () => {
            renderTable(allData.lista_pendentes, 'Detalhes dos Pedidos Pendentes');
            setActiveCard(null); 
        });