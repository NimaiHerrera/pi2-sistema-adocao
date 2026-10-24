const API_URL = "http://127.0.0.1:8001";
const SENHA_MESTRE = "pancinha123"; // Senha simples para controle do admin no MVP

// Executa a verificação de acesso assim que a página carregar
document.addEventListener("DOMContentLoaded", () => {
  verificarAcessoAdmin();
});

// Verifica se o usuário já inseriu a senha nesta sessão
function verificarAcessoAdmin() {
  const autenticado = sessionStorage.getItem("admin_autenticado");

  if (!autenticado) {
    const senhaDigitada = prompt("🔒 Área Restrita da ONG Pancinha Feliz da Lili\n\nPor favor, digite a senha de administrador:");

    if (senhaDigitada === SENHA_MESTRE) {
      sessionStorage.setItem("admin_autenticado", "true");
      alert("✅ Acesso concedido ao Painel Administrativo!");
      inicializarPainel();
    } else {
      alert("❌ Senha incorreta! A redirecionar para a vitrine pública.");
      window.location.href = "index.html";
    }
  } else {
    inicializarPainel();
  }
}

// Carrega os dados das tabelas administrativas após autenticar
function inicializarPainel() {
  carregarSolicitacoes();
  carregarAnimaisAdmin();
}

// 1. Carrega as solicitações de adoção recebidas
async function carregarSolicitacoes() {
  const tbody = document.getElementById("tabela-solicitacoes");
  if (!tbody) return;

  try {
    const response = await fetch(`${API_URL}/solicitacoes`);
    if (!response.ok) throw new Error("Erro ao carregar solicitações");
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
        <td><span class="tag ${sol.status.toLowerCase()}">${sol.status.toUpperCase()}</span></td>
        <td>
          <button class="btn-acao btn-aprovar" onclick="atualizarStatus(${sol.id}, 'aprovado')" title="Aprovar">✓</button>
          <button class="btn-acao btn-recusar" onclick="atualizarStatus(${sol.id}, 'recusado')" title="Recusar">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Erro ao carregar solicitações:", error);
    tbody.innerHTML = `<tr><td colspan="6">Erro ao conectar à API na porta 8001.</td></tr>`;
  }
}

// 2. Atualiza o status da solicitação (Aprovado / Recusado)
async function atualizarStatus(id, novoStatus) {
  try {
    const response = await fetch(`${API_URL}/solicitacoes/${id}?novo_status=${novoStatus}`, {
      method: "PATCH"
    });
    if (!response.ok) throw new Error("Erro ao atualizar status");
    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarSolicitacoes();
  } catch (error) {
    alert("Erro ao atualizar o status da solicitação.");
  }
}

// 3. Carrega os animais para permitir remoção
async function carregarAnimaisAdmin() {
  const tbody = document.getElementById("tabela-animais-admin");
  if (!tbody) return;

  try {
    const response = await fetch(`${API_URL}/animais`);
    if (!response.ok) throw new Error("Erro ao carregar animais");
    const animais = await response.json();

    tbody.innerHTML = "";
    if (animais.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5">Nenhum animal cadastrado no abrigo no momento.</td></tr>`;
      return;
    }

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
    console.error("Erro ao carregar animais no admin:", error);
    tbody.innerHTML = `<tr><td colspan="5">Erro ao carregar animais do banco.</td></tr>`;
  }
}

// 4. Remove um pet do banco SQLite
async function removerPet(id, nome) {
  if (!confirm(`Tem certeza de que deseja remover o pet '${nome}' do sistema?`)) return;

  try {
    const response = await fetch(`${API_URL}/animais/${id}`, {
      method: "DELETE"
    });
    if (!response.ok) throw new Error("Erro ao remover pet");
    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarAnimaisAdmin();
  } catch (error) {
    alert("Erro ao remover o pet.");
  }
}

// Função para encerrar a sessão administrativa (Sair)
function logoutAdmin() {
  sessionStorage.removeItem("admin_autenticado");
  window.location.href = "index.html";
}