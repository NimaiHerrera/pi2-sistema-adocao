/**
 * Lógica do Painel Administrativo da ONG
 * Projeto Integrador II - Univesp
 */

const API_URL = "http://127.0.0.1:8001";

document.addEventListener("DOMContentLoaded", () => {
  // Proteção da página: se não estiver logado, redireciona para login.html
  const usuarioAutenticado = sessionStorage.getItem("admin_autenticado");
  
  if (usuarioAutenticado !== "true") {
    window.location.href = "login.html";
    return;
  }

  carregarSolicitacoes();
  carregarAnimaisAdmin();
});

/**
 * Função para encerrar a sessão (Logout)
 */
function efetuarLogout() {
  if (confirm("Deseja realmente sair do Painel Administrativo?")) {
    sessionStorage.removeItem("admin_autenticado");
    sessionStorage.removeItem("admin_usuario");
    window.location.href = "login.html";
  }
}

/**
 * 1. Converte a imagem enviada via upload de arquivo para Base64 e exibe pré-visualização
 */
function previewFoto(event) {
  const file = event.target.files[0];
  const labelNome = document.getElementById("nome-arquivo-selecionado");
  const containerPreview = document.getElementById("container-preview");
  const imgPreview = document.getElementById("img-preview");
  const inputBase64 = document.getElementById("cad-foto-base64");

  if (file) {
    labelNome.textContent = file.name;

    const reader = new FileReader();
    reader.onload = function (e) {
      const base64String = e.target.result;
      imgPreview.src = base64String;
      inputBase64.value = base64String;
      containerPreview.style.display = "block";
    };
    reader.readAsDataURL(file);
  } else {
    labelNome.textContent = "Nenhum arquivo selecionado";
    containerPreview.style.display = "none";
    inputBase64.value = "";
  }
}

/**
 * 2. Cadastra um novo animal no sistema
 */
async function cadastrarNovoPet(event) {
  event.preventDefault();

  const fotoUpload = document.getElementById("cad-foto-base64").value;
  const fotoPadrao = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=500";

  const novoPet = {
    nome: document.getElementById("cad-nome").value,
    especie: document.getElementById("cad-especie").value,
    porte: document.getElementById("cad-porte").value,
    idade_aproximada: document.getElementById("cad-idade").value,
    foto_url: fotoUpload || fotoPadrao,
    descricao: document.getElementById("cad-descricao").value,
    vacinado: document.getElementById("cad-vacinado").checked,
    castrado: document.getElementById("cad-castrado").checked
  };

  try {
    const response = await fetch(`${API_URL}/animais`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(novoPet)
    });

    if (!response.ok) throw new Error("Erro ao salvar o animal.");

    const resultado = await response.json();
    alert(`🎉 Pet '${resultado.pet.nome}' cadastrado e publicado na vitrine pública!`);

    // Limpa o formulário e pré-visualização
    document.getElementById("form-cadastrar-pet").reset();
    document.getElementById("container-preview").style.display = "none";
    document.getElementById("nome-arquivo-selecionado").textContent = "Nenhum arquivo selecionado";
    document.getElementById("cad-foto-base64").value = "";

    // Atualiza a tabela de gestão de animais
    carregarAnimaisAdmin();

  } catch (error) {
    console.error("Erro no cadastro:", error);
    alert("Não foi possível cadastrar o pet. Verifique se o servidor backend está ativo.");
  }
}

/**
 * 3. Carrega e exibe a tabela de solicitações de adoção recebidas
 */
async function carregarSolicitacoes() {
  const tbody = document.getElementById("tabela-solicitacoes");
  if (!tbody) return;

  try {
    const response = await fetch(`${API_URL}/solicitacoes`);
    const solicitacoes = await response.json();

    tbody.innerHTML = "";
    if (!solicitacoes || solicitacoes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b;">Nenhuma solicitação recebida até o momento.</td></tr>`;
      return;
    }

    solicitacoes.forEach(sol => {
      const tr = document.createElement("tr");
      const statusLower = sol.status.toLowerCase();
      const corStatus = statusLower === 'aprovado' ? '#166534' : (statusLower === 'recusado' ? '#ef4444' : '#d97706');

      // Se for pendente, exibe os botões de ação (Aprovar / Recusar).
      // Se já foi finalizado (aprovado/recusado), exibe o botão de Excluir Registro.
      let botoesAcao = "";
      if (statusLower === 'pendente') {
        botoesAcao = `
          <button class="btn-acao btn-aprovar" title="Aprovar Adoção" onclick="atualizarStatus(${sol.id}, 'aprovado')">✓ Aprovar</button>
          <button class="btn-acao btn-recusar" title="Recusar Adoção" onclick="atualizarStatus(${sol.id}, 'recusado')">✕ Recusar</button>
        `;
      } else {
        botoesAcao = `
          <button class="btn-acao btn-remover" title="Excluir Registro" onclick="removerSolicitacao(${sol.id})">🗑️ Excluir</button>
        `;
      }

      tr.innerHTML = `
        <td>${sol.id}</td>
        <td><strong>${sol.adotante.nome}</strong><br><small>CPF: ${sol.adotante.cpf}</small></td>
        <td>${sol.adotante.telefone}<br><small>CEP: ${sol.adotante.cep}</small></td>
        <td>${sol.animal ? sol.animal.nome + ' (' + sol.animal.especie + ')' : 'Pet removido'}</td>
        <td><span style="font-weight: bold; color: ${corStatus}">${sol.status.toUpperCase()}</span></td>
        <td>${botoesAcao}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Erro ao carregar solicitações:", error);
    tbody.innerHTML = `<tr><td colspan="6" style="color: #ef4444; text-align: center;">Erro ao carregar solicitações.</td></tr>`;
  }
}

/**
 * 4. Atualiza o status da solicitação ('aprovado' ou 'recusado')
 */
async function atualizarStatus(id, novoStatus) {
  try {
    const response = await fetch(`${API_URL}/solicitacoes/${id}?novo_status=${novoStatus}`, {
      method: "PATCH"
    });

    if (!response.ok) throw new Error("Erro na requisição.");

    const resultado = await response.json();
    alert(resultado.mensagem);

    // Atualiza ambas as tabelas
    carregarSolicitacoes();
    carregarAnimaisAdmin();
  } catch (error) {
    console.error("Erro ao atualizar status:", error);
    alert("Não foi possível atualizar o status da solicitação.");
  }
}

/**
 * 5. Carrega a lista de animais na tabela de exclusão/gestão
 */
async function carregarAnimaisAdmin() {
  const tbody = document.getElementById("tabela-animais-admin");
  if (!tbody) return;

  try {
    const response = await fetch(`${API_URL}/animais`);
    const animais = await response.json();

    tbody.innerHTML = "";
    if (!animais || animais.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b;">Nenhum animal cadastrado ou disponível no momento.</td></tr>`;
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
          <button class="btn-acao btn-remover" onclick="removerPet(${animal.id}, '${animal.nome}')">🗑️ Remover Pet</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Erro ao carregar animais no admin:", error);
  }
}

/**
 * 6. Exclui permanentemente um animal do banco de dados
 */
async function removerPet(id, nome) {
  if (!confirm(`Tem certeza que deseja remover o pet '${nome}' do sistema permanentemente?`)) return;

  try {
    const response = await fetch(`${API_URL}/animais/${id}`, {
      method: "DELETE"
    });

    if (!response.ok) throw new Error("Erro ao remover pet.");

    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarAnimaisAdmin();
  } catch (error) {
    console.error("Erro na remoção:", error);
    alert("Erro ao remover o pet.");
  }
}

/**
 * Remove uma solicitação já finalizada do banco de dados
 */
async function removerSolicitacao(id) {
  if (!confirm(`Tem certeza que deseja excluir o registro da solicitação #${id}?`)) return;

  try {
    const response = await fetch(`${API_URL}/solicitacoes/${id}`, {
      method: "DELETE"
    });

    if (!response.ok) throw new Error("Erro ao remover solicitação.");

    const resultado = await response.json();
    alert(resultado.mensagem);
    carregarSolicitacoes(); // Atualiza a tabela imediatamente
  } catch (error) {
    console.error("Erro na remoção:", error);
    alert("Erro ao excluir a solicitação.");
  }
}