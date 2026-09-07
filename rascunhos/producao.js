let itens = [];

function adicionarItem() {
    const produtoEl = document.getElementById("produto");
    const generoEl = document.querySelector('input[name="genero"]:checked');
    const tamanhoEl = document.querySelector('input[name="tamanho"]:checked');
    const quantidadeEl = document.getElementById("quantidade");

    // Validação
    if (
        !produtoEl.value ||
        !generoEl ||
        !tamanhoEl ||
        !quantidadeEl.value
    ) {
        alert("Preencha todos os campos obrigatórios (Modelo, Gênero, Tamanho e Quantidade).");
        return;
    }

    const quantidade = parseInt(quantidadeEl.value);

    if (isNaN(quantidade) || quantidade <= 0) {
        alert("Informe uma quantidade válida.");
        return;
    }

    itens.push({
        produto: produtoEl.value,
        genero: generoEl.value,
        tamanho: tamanhoEl.value,
        quantidade: quantidade
    });

    if (typeof atualizarCarrinho === "function") {
        atualizarCarrinho();
    }
}


function abrirModal() {

    const modal =
        document.getElementById("modal");

    modal.style.display = "flex";
}


function fecharModal() {

    const modal =
        document.getElementById("modal");

    modal.style.display = "none";
}