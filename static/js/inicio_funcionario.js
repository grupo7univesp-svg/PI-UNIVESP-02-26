const form = document.getElementById("formProducao");
const mensagem = document.getElementById("mensagem");
const tamanhos = ["p", "m", "g", "gg", "xg"];

function valorQuantidade(tamanho) {
    const campo = document.getElementById(`quantidade_${tamanho}`);
    const valor = parseInt(campo.value || "0", 10);
    return Number.isNaN(valor) ? 0 : valor;
}

function atualizarTotal() {
    const total = tamanhos.reduce((soma, tamanho) => soma + Math.max(0, valorQuantidade(tamanho)), 0);
    document.getElementById("totalRelatorio").textContent = total;
}

tamanhos.forEach(tamanho => {
    document.getElementById(`quantidade_${tamanho}`).addEventListener("input", atualizarTotal);
});

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    mensagem.innerHTML = "";

    const dados = {
        data_producao: document.getElementById("data_producao").value,
        quantidade_p: valorQuantidade("p"),
        quantidade_m: valorQuantidade("m"),
        quantidade_g: valorQuantidade("g"),
        quantidade_gg: valorQuantidade("gg"),
        quantidade_xg: valorQuantidade("xg")
    };

    if (!dados.data_producao) {
        mostrarErro("Informe a data da produção.");
        return;
    }

    const total = dados.quantidade_p + dados.quantidade_m + dados.quantidade_g + dados.quantidade_gg + dados.quantidade_xg;
    if (total <= 0) {
        mostrarErro("Informe a quantidade de pelo menos um tamanho.");
        return;
    }

    const btnSalvar = document.getElementById("btnSalvar");
    btnSalvar.disabled = true;
    btnSalvar.textContent = "Enviando...";

    try {
        const resposta = await fetch("/api/producoes", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(dados)
        });
        const resultado = await resposta.json();
        if (!resposta.ok) {
            mostrarErro(resultado.erro || "Erro ao salvar relatório.");
            return;
        }
        mensagem.innerHTML = `<div class="alert alert-success">${resultado.mensagem}</div>`;
        setTimeout(() => window.location.reload(), 800);
    } catch (erro) {
        console.error(erro);
        mostrarErro("Não foi possível conectar ao servidor.");
    } finally {
        btnSalvar.disabled = false;
        btnSalvar.textContent = "Enviar relatório";
    }
});

function mostrarErro(texto) {
    mensagem.innerHTML = `<div class="alert alert-danger">${texto}</div>`;
}

async function abrirDetalhes(relatorioId) {
    const carregando = document.getElementById("detalhesCarregando");
    const conteudo = document.getElementById("detalhesConteudo");
    const erro = document.getElementById("detalhesErro");
    carregando.style.display = "block";
    conteudo.style.display = "none";
    erro.style.display = "none";

    try {
        const resposta = await fetch(`/api/producoes/relatorio/${relatorioId}`);
        if (!resposta.ok) throw new Error("Erro ao buscar relatório");
        const dados = await resposta.json();
        document.getElementById("detalheData").textContent = dados.data;
        document.getElementById("detalheTotal").textContent = dados.total_geral;
        document.getElementById("detalhesTamanhos").innerHTML = ["P", "M", "G", "GG", "XG"]
            .map(t => `<tr><td>${t}</td><td>${dados.quantidades[t]}</td></tr>`).join("");
        carregando.style.display = "none";
        conteudo.style.display = "block";
    } catch (e) {
        console.error(e);
        carregando.style.display = "none";
        erro.style.display = "block";
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const campoData = document.getElementById("data_producao");
    if (campoData && !campoData.value) {
        const hoje = new Date();
        const local = new Date(hoje.getTime() - hoje.getTimezoneOffset() * 60000);
        campoData.value = local.toISOString().split("T")[0];
    }
    atualizarTotal();
});
