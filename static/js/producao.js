let itens = [];

function adicionarItem() {
    const generoEl = document.querySelector('input[name="genero"]:checked');
    const tamanhoEl = document.querySelector('input[name="tamanho"]:checked');
    const quantidadeEl = document.getElementById("quantidade");

    // Valida se os campos foram selecionados/preenchidos
    if (!generoEl || !tamanhoEl || !quantidadeEl.value) {
        alert("Preencha todos os campos obrigatórios (Gênero, Tamanho e Quantidade).");
        return;
    }

    const quantidade = parseInt(quantidadeEl.value);

    if (isNaN(quantidade) || quantidade <= 0) {
        alert("Informe uma quantidade válida.");
        return;
    }

    itens.push({
        genero: generoEl.value,
        tamanho: tamanhoEl.value,
        quantidade: quantidade
    });

    // Se houver função de atualizar a tela/carrinho, chame-a aqui:
    if (typeof atualizarCarrinho === "function") {
        atualizarCarrinho();
    }
}