const API_URL = "http://127.0.0.1:8001";
let listaAnimaisGlobal = []; // Guarda a lista completa para pesquisas rápidas
let especieFiltroAtual = "";

document.addEventListener("DOMContentLoaded", () => {
  carregarDadosOng();
  carregarAnimais();
});

// Busca os dados da ONG no back-end
async function carregarDadosOng() {
  try {
    const response = await fetch(`${API_URL}/ong`);
    if (!response.ok) throw new Error("Erro ao carregar dados da ONG");
    const ong = await response.json();

    document.getElementById("ong-nome").textContent = ong.nome;
    document.getElementById("ong-descricao").textContent = ong.descricao;

    const contatosContainer = document.getElementById("ong-contatos");
    contatosContainer.innerHTML = `
      <span>📍 ${ong.endereco || 'São Paulo, SP'}</span>
      <span>📞 ${ong.telefone || '(11) 99999-8888'}</span>
    `;
  } catch (error) {
    console.error("Erro ONG:", error);
  }
}

// Busca os animais na API FastAPI
async function carregarAnimais(especie = "") {
  especieFiltroAtual = especie;
  const container = document.getElementById("lista-animais");
  container.innerHTML = `<div class="loading-spinner"><p>A carregar os nossos amiguinhos...</p></div>`;

  try {
    let url = `${API_URL}/animais`;
    if (especie) url += `?especie=${especie}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error("Erro ao listar animais");
    
    listaAnimaisGlobal = await response.json();
    renderizarCards(listaAnimaisGlobal);
  } catch (error) {
    console.error("Erro Animais:", error);
    container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #ef4444;">Não foi possível carregar os animais. Verifique se o backend está ligado na porta 8001!</p>`;
  }
}

// Desenha os cards na tela
function renderizarCards(animais) {
  const container = document.getElementById("lista-animais");
  container.innerHTML = "";

  if (animais.length === 0) {
    container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #64748b; padding: 40px 0;">Nenhum pet encontrado com os filtros selecionados.</p>`;
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
          ${animal.vacinado ? '<span class="tag tag-vacinado">✓ Vacinado</span>' : ''}
          ${animal.castrado ? '<span class="tag tag-castrado">✓ Castrado</span>' : ''}
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

// Filtro instantâneo pelo campo de texto
function filtrarPorNome() {
  const termo = document.getElementById("input-pesquisa").value.toLowerCase();
  const filtrados = listaAnimaisGlobal.filter(a => 
    a.nome.toLowerCase().includes(termo) || 
    a.porte.toLowerCase().includes(termo)
  );
  renderizarCards(filtrados);
}

// Alternar botões de filtro por espécie
function filtrarEspecie(especie, elementoBotao) {
  document.querySelectorAll(".btn-filtro").forEach(btn => btn.classList.remove("active"));
  elementoBotao.classList.add("active");
  carregarAnimais(especie);
}

// Abre formulário e faz scroll suave
function selecionarPet(id, nome) {
  document.getElementById("secao-formulario").style.display = "block";
  document.getElementById("nome-pet-selecionado").textContent = nome;
  document.getElementById("animal-id").value = id;
  document.getElementById("secao-formulario").scrollIntoView({ behavior: 'smooth' });
}

function fecharFormulario() {
  document.getElementById("secao-formulario").style.display = "none";
  document.getElementById("form-adocao").reset();
}

// Consulta ViaCEP
async function buscarCep(cep) {
  const cepLimpo = cep.replace(/\D/g, '');
  const statusCep = document.getElementById("status-cep");

  if (cepLimpo.length !== 8) {
    statusCep.textContent = "Digite um CEP válido com 8 dígitos.";
    statusCep.style.color = "#ef4444";
    return;
  }

  statusCep.textContent = "A procurar endereço...";
  statusCep.style.color = "#0284c7";

  try {
    const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
    const data = await response.json();

    if (data.erro) {
      statusCep.textContent = "CEP não encontrado!";
      statusCep.style.color = "#ef4444";
    } else {
      statusCep.textContent = "Endereço localizado!";
      statusCep.style.color = "#166534";
      document.getElementById("logradouro").value = data.logradouro;
      document.getElementById("bairro").value = data.bairro;
      document.getElementById("cidade").value = `${data.localidade} - ${data.uf}`;
    }
  } catch (error) {
    console.error("Erro ViaCEP:", error);
    statusCep.textContent = "Erro ao ligar ao serviço de CEP.";
    statusCep.style.color = "#ef4444";
  }
}

// Envio da Solicitação (POST /solicitacoes)
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

    if (!response.ok) throw new Error("Erro ao enviar solicitação");
    const resultado = await response.json();

    alert(resultado.mensagem);
    fecharFormulario();
  } catch (error) {
    console.error("Erro no envio:", error);
    alert("Não foi possível enviar a solicitação. Tente novamente.");
  }
}