const API_URL = "http://127.0.0.1:8001";

document.addEventListener("DOMContentLoaded", () => {
  carregarSolicitacoes();
  carregarAnimaisAdmin();
});

// Carrega as solicitações de adoção recebidas
async function carregarSolicitacoes() {
  const tbody = document.getElementById("tabela-solicitacoes");
  try {
    const response = await fetch(`${API_URL}/solicitacoes`);
    const solicitacoes = await response.json();

    tbody.innerHTML = "";
    if (solicitacoes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6">Nenhuma solicitação recebida até o momento.</td></tr>`;
      return;
    }

    solicitacoes.forEach(sol => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${sol.id}</td>
        <td><strong>${sol.adotante.nome}</strong><br><small>CPF: ${sol.adotante.cpf}</small></td>
        <td>${sol.adotante.telefone}<br><small>CEP: ${sol.adotante.cep}</small></td>
        <td>${sol.animal.nome} (${sol.animal.especie})</td>
        <td><span class="tag">${sol.status.toUpperCase()}</span></td>
        <td>
          <button class="btn-acao btn-aprovar" onclick="atualizarStatus(${sol.id}, 'aprovado')">✓</button>
          <button class="btn-acao btn-recusar" onclick="atualizarStatus(${sol.id}, 'recusado')">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Erro ao carregar solicitações:", error);
  }
}

// Atualiza o status da solicitação
async function atualizarStatus(id, novoStatus) {
  try {
    const response = await fetch(`${API_URL}/solicitacoes/${id}?novo_status=${novoStatus}`, {
      method: "PATCH"
    });
    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarSolicitacoes();
  } catch (error) {
    alert("Erro ao atualizar status.");
  }
}

// Carrega os animais para permitir remoção
async function carregarAnimaisAdmin() {
  const tbody = document.getElementById("tabela-animais-admin");
  try {
    const response = await fetch(`${API_URL}/animais`);
    const animais = await response.json();

    tbody.innerHTML = "";
    animais.forEach(animal => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${animal.id}</td>
        <td><strong>${animal.nome}</strong></td>
        <td>${animal.especie}</td>
        <td>${animal.porte}</td>
        <td>
          <button class="btn-acao btn-remover" onclick="removerPet(${animal.id}, '${animal.nome}')">Remover Pet</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Erro ao carregar animais:", error);
  }
}

// Remove um pet do banco
async function removerPet(id, nome) {
  if (!confirm(`Tem certeza que deseja remover o pet '${nome}' do sistema?`)) return;

  try {
    const response = await fetch(`${API_URL}/animais/${id}`, {
      method: "DELETE"
    });
    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarAnimaisAdmin();
  } catch (error) {
    alert("Erro ao remover o pet.");
  }
}