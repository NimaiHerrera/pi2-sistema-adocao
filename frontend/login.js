/**
 * Lógica da Tela de Login Administrativo
 * Projeto Integrador II - Univesp
 */

const API_URL = "http://127.0.0.1:8001";

// Se o usuário já estiver autenticado, redireciona direto para o painel admin
document.addEventListener("DOMContentLoaded", () => {
  if (sessionStorage.getItem("admin_autenticado") === "true") {
    window.location.href = "admin.html";
  }
});

/**
 * Função executada ao enviar o formulário de login
 */
async function efetuarLogin(event) {
  event.preventDefault();

  const usuarioInput = document.getElementById("usuario").value.trim();
  const senhaInput = document.getElementById("senha").value;
  const msgErro = document.getElementById("mensagem-erro");

  // Esconde mensagem de erro anterior
  msgErro.style.display = "none";

  try {
    const response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usuario: usuarioInput,
        senha: senhaInput
      })
    });

    if (!response.ok) {
      throw new Error("Credenciais inválidas");
    }

    const data = await response.json();

    if (data.autenticado) {
      // Salva o estado de login na sessão
      sessionStorage.setItem("admin_autenticado", "true");
      sessionStorage.setItem("admin_usuario", data.usuario);

      // Redireciona para o Painel Administrativo
      window.location.href = "admin.html";
    }
  } catch (error) {
    console.error("Erro no login:", error);
    msgErro.textContent = "Usuário ou senha incorretos!";
    msgErro.style.display = "block";
  }
}