# [WEB + ANÁLISE] Sistema de Monitoramento de Performance de Entregas
Sistema desenvolvido para automatizar e aprimorar o monitoramento de performance da transportadora Porta-a-Porta. A ferramenta cruza dados de planilhas de "preventiva" com relatórios de status do aplicativo "Mobile Entregas" do Magazine Luiza para gerar análises de performance.

# Funcionalidades
**1. Interface de Upload de Arquivos**
* O software fornece uma página web simples para o upload dos dois arquivos necessários: o relatório de "preventiva" (que começa com `cd-etapa...`) e o relatório de status do "Mobile Entregas".
* **Impacto:** Elimina a necessidade de processos manuais (como salvar arquivos em pastas de rede específicas ou enviar por e-mail), centralizando a operação em um único local.

**2. Análise e Cruzamento de Dados**
* O backend executa um script em Pandas que automaticamente lê os arquivos (`.csv`, `.xlsx`, `.xls`), limpa os nomes das colunas, e cruza as duas planilhas usando o número do pedido (`pedido_gemco`) como chave.
* **Impacto:** Reduz drasticamente o tempo de análise de horas (usando `PROCV` no Excel) para segundos. Garante 100% de precisão no cruzamento, eliminando falhas humanas.

**3. Dashboard de Performance**
* Gera uma página de resultados em tempo real com os principais KPIs da operação: Total de Pedidos, Pedidos Finalizados, Pendentes para Cobrar, e um medidor de Performance Atual vs. Meta (96.00%).
* **Impacto:** Fornece uma visão gerencial imediata e clara do status da operação, permitindo tomadas de decisão rápidas.

**4. Tabelas Interativas e Relatório de Ação**
* Os cartões do dashboard são clicáveis e filtram a tabela de pedidos (Pendentes, Finalizados, Total).
* Simultaneamente, um relatório detalhado em Excel (`Resultado_Monitoramento.xlsx`) é gerado na pasta `dados/` com abas separadas para "Pendentes" e "Finalizados".
* **Impacto:** Facilita a auditoria e a cobrança de status dos motoristas. A aba "Pendentes" serve como uma lista de trabalho pronta para a equipe de monitoramento.
  
## Forma de execução em ambiente de Desenvolvimento

Use Python na versão 3.7+ com as bibliotecas:

```bash
# Instale as dependências listadas no requirements.txt
pip install pandas openpyxl xlrd flask

# Como executa o servidor de desenvolvimento do Flask
Na pasta raiz do projeto digite: python -m app.main
