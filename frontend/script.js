// URL base da nossa API Python/FastAPI (Porta 8001)
const API_URL = "http://127.0.0.1:8001";

// Executa ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
  carregarDadosOng();
  carregarAnimais();
});

// Busca os dados da ONG na rota GET /ong
async function carregarDadosOng() {
  try {
    const response = await fetch(`${API_URL}/ong`);
    if (!response.ok) throw new Error("Erro ao carregar dados da ONG");
    const ong = await response.json();

    document.getElementById("ong-nome").textContent = ong.nome;
    document.getElementById("ong-descricao").textContent = ong.descricao;
  } catch (error) {
    console.error("Erro:", error);
  }
}

// Busca a lista de animais na rota GET /animais (com ou sem filtro por espécie)
async function carregarAnimais(especie = "") {
  const container = document.getElementById("lista-animais");
  container.innerHTML = "<p>Carregando pets...</p>";

  try {
    let url = `${API_URL}/animais`;
    if (especie) {
      url += `?especie=${especie}`;
    }

    const response = await fetch(url);
    if (!response.ok) throw new Error("Erro ao buscar lista de animais");
    const animais = await response.json();

    container.innerHTML = ""; // Limpa a mensagem de carregamento

    if (animais.length === 0) {
      container.innerHTML = "<p>Nenhum pet encontrado para esta categoria no momento.</p>";
      return;
    }

    // Renderiza cada card de animal retornado pelo banco
    animais.forEach(animal => {
      const card = document.createElement("div");
      card.className = "card-animal";

      // Foto padrão caso o animal não tenha URL cadastrada
      const foto = animal.foto_url || "https://via.placeholder.com/300x200?text=Sem+Foto";

      card.innerHTML = `
        <img src="${foto}" alt="${animal.nome}">
        <div class="card-corpo">
          <h3>${animal.nome}</h3>
          <p><strong>Espécie:</strong> ${animal.especie}</p>
          <p><strong>Porte:</strong> ${animal.porte}</p>
          <p><strong>Idade:</strong> ${animal.idade_aproximada || 'Não informada'}</p>
          <p class="descricao">${animal.descricao || 'Sem descrição informada.'}</p>
          <button class="btn-adotar" onclick="selecionarPet(${animal.id}, '${animal.nome}')">Quero Adotar</button>
        </div>
      `;

      container.appendChild(card);
    });
  } catch (error) {
    console.error("Erro:", error);
    container.innerHTML = "<p>Erro ao carregar os pets. Verifique se a API está rodando no terminal!</p>";
  }
}

function selecionarPet(id, nome) {
  alert(`Você selecionou o pet: ${nome} (ID: ${id}). Em breve abriremos o formulário de adoção!`);
}