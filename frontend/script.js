const API_URL = "http://127.0.0.1:8001";
let listaAnimaisGlobal = [];
let especieFiltroAtual = "";

document.addEventListener("DOMContentLoaded", () => {
  carregarDadosOng();
  carregarAnimais();
});

// 1. Busca os dados da ONG no back-end
async function carregarDadosOng() {
  try {
    const response = await fetch(`${API_URL}/ong`);
    if (!response.ok) throw new Error("Erro ao carregar dados da ONG");
    const ong = await response.json();

    const elNome = document.getElementById("ong-nome");
    const elDesc = document.getElementById("ong-descricao");
    const contatosContainer = document.getElementById("ong-contatos");

    if (elNome) elNome.textContent = ong.nome || "ONG Pancinha Feliz da Lili";
    if (elDesc) elDesc.textContent = ong.descricao || "Adoção responsável de pets";

    if (contatosContainer) {
      contatosContainer.innerHTML = `
        <span>📍 ${ong.endereco || 'Mauá - SP'}</span>
        <span>📞 ${ong.telefone || '(11) 97319-0676'}</span>
      `;
    }
  } catch (error) {
    console.error("Erro ONG:", error);
  }
}

// 2. Busca os animais na API FastAPI
async function carregarAnimais(especie = "") {
  especieFiltroAtual = especie;
  const container = document.getElementById("lista-animais");
  if (!container) return;

  container.innerHTML = `<div class="loading-spinner"><p>A procurar pets disponíveis no abrigo...</p></div>`;

  try {
    let url = `${API_URL}/animais`;
    if (especie) url += `?especie=${especie}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error("Erro ao listar animais");
    
    listaAnimaisGlobal = await response.json();
    renderizarCards(listaAnimaisGlobal);
  } catch (error) {
    console.error("Erro Animais:", error);
    container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #ef4444; padding: 30px 0;">Não foi possível carregar os animais. Verifique se o backend está ativo na porta 8001!</p>`;
  }
}

// 3. Desenha os cards na tela
function renderizarCards(animais) {
  const container = document.getElementById("lista-animais");
  if (!container) return;

  container.innerHTML = "";

  if (!animais || animais.length === 0) {
    container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #64748b; padding: 40px 0;">Nenhum pet encontrado no abrigo com os filtros selecionados.</p>`;
    return;
  }

  animais.forEach(animal => {
    const card = document.createElement("div");
    card.className = "card-animal";

    const foto = animal.foto_url || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=500";

    card.innerHTML = `
      <div class="card-imagem-container">
        <img src="${foto}" alt="${animal.nome}">
        <span class="badge-especie">${animal.especie}</span>
      </div>
      <div class="card-corpo">
        <h3>${animal.nome}</h3>
        
        <div class="tags-saude">
          ${animal.vacinado ? '<span class="tag vacinado">✓ Vacinado</span>' : ''}
          ${animal.castrado ? '<span class="tag castrado">✓ Castrado</span>' : ''}
        </div>

        <p class="info-linha"><strong>Porte:</strong> ${animal.porte}</p>
        <p class="info-linha"><strong>Idade:</strong> ${animal.idade_aproximada || 'Não informada'}</p>
        
        <p class="descricao">${animal.descricao || 'Sem descrição cadastrada.'}</p>
        
        <button class="btn-adotar" onclick="selecionarPet(${animal.id}, '${animal.nome}')">Quero Adotar</button>
      </div>
    `;

    container.appendChild(card);
  });
}

// 4. Filtro por nome
function filtrarPorNome() {
  const input = document.getElementById("input-pesquisa");
  if (!input) return;

  const termo = input.value.toLowerCase();
  const filtrados = listaAnimaisGlobal.filter(a => 
    a.nome.toLowerCase().includes(termo) || 
    a.porte.toLowerCase().includes(termo)
  );
  renderizarCards(filtrados);
}

// 5. Filtro por botões de espécie
function filtrarEspecie(especie, elementoBotao) {
  document.querySelectorAll(".btn-filtro").forEach(btn => btn.classList.remove("active"));
  if (elementoBotao) elementoBotao.classList.add("active");
  carregarAnimais(especie);
}

// 6. Seleção do pet e abertura do formulário
function selecionarPet(id, nome) {
  const secaoForm = document.getElementById("secao-formulario");
  if (secaoForm) {
    secaoForm.style.display = "block";
    document.getElementById("nome-pet-selecionado").textContent = nome;
    document.getElementById("animal-id").value = id;
    secaoForm.scrollIntoView({ behavior: 'smooth' });
  }
}

function fecharFormulario() {
  const secaoForm = document.getElementById("secao-formulario");
  if (secaoForm) secaoForm.style.display = "none";
  const form = document.getElementById("form-adocao");
  if (form) form.reset();
}

// 7. Consulta de CEP via ViaCEP
async function buscarCep(cep) {
  const cepLimpo = cep.replace(/\D/g, '');
  const statusCep = document.getElementById("status-cep");

  if (cepLimpo.length !== 8) {
    if (statusCep) {
      statusCep.textContent = "Digite um CEP válido com 8 dígitos.";
      statusCep.style.color = "#ef4444";
    }
    return;
  }

  if (statusCep) {
    statusCep.textContent = "A procurar endereço...";
    statusCep.style.color = "#0284c7";
  }

  try {
    const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
    const data = await response.json();

    if (data.erro) {
      if (statusCep) {
        statusCep.textContent = "CEP não encontrado!";
        statusCep.style.color = "#ef4444";
      }
    } else {
      if (statusCep) {
        statusCep.textContent = "Endereço localizado!";
        statusCep.style.color = "#166534";
      }
      document.getElementById("logradouro").value = data.logradouro;
      document.getElementById("bairro").value = data.bairro;
      document.getElementById("cidade").value = `${data.localidade} - ${data.uf}`;
    }
  } catch (error) {
    console.error("Erro ViaCEP:", error);
    if (statusCep) {
      statusCep.textContent = "Erro ao ligar ao serviço de CEP.";
      statusCep.style.color = "#ef4444";
    }
  }
}

// 8. Envio da Solicitação
async function enviarFormulario(event) {
  event.preventDefault();

  const dadosFormulario = {
    nome: document.getElementById("nome").value,
    cpf: document.getElementById("cpf").value,
    telefone: document.getElementById("telefone").value,
    cep: document.getElementById("cep").value,
    animal_id: parseInt(document.getElementById("animal-id").value)
  };

  try {
    const response = await fetch(`${API_URL}/solicitacoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dadosFormulario)
    });

    if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);

    const resultado = await response.json();
    alert(resultado.mensagem || "Solicitação enviada com sucesso!");
    fecharFormulario();

  } catch (error) {
    console.error("Erro no envio:", error);
    alert("Não foi possível enviar a solicitação. Verifique se o backend está ativo!");
  }
}

/* --- FUNÇÕES DO MODAL PIX --- */
function abrirModalPix() {
  const modal = document.getElementById("modal-pix");
  if (modal) modal.style.display = "flex";
}

function fecharModalPix() {
  const modal = document.getElementById("modal-pix");
  if (modal) modal.style.display = "none";
  const status = document.getElementById("status-copia");
  if (status) status.style.display = "none";
}

function copiarChavePix() {
  const inputChave = document.getElementById("chave-pix-input");
  if (!inputChave) return;

  inputChave.select();
  inputChave.setSelectionRange(0, 99999);

  navigator.clipboard.writeText(inputChave.value).then(() => {
    const status = document.getElementById("status-copia");
    if (status) {
      status.style.display = "block";
      setTimeout(() => {
        status.style.display = "none";
      }, 3000);
    }
  }).catch(err => {
    console.error("Erro ao copiar:", err);
  });
}