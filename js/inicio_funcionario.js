// =========================================================
// ARRAY DOS ITENS
// =========================================================

let itens = [];


// =========================================================
// ELEMENTOS
// =========================================================

const form =
    document.getElementById("formProducao");

const btnAdicionar =
    document.getElementById("btnAdicionar");

const listaItens =
    document.getElementById("listaItens");

const totalItens =
    document.getElementById("totalItens");

const mensagem =
    document.getElementById("mensagem");


// =========================================================
// ADICIONAR ITEM
// =========================================================

function adicionarItem() {

    const generoElement =
        document.querySelector(
            'input[name="genero"]:checked'
        );


    const tamanhoElement =
        document.getElementById("tamanho");


    const quantidadeElement =
        document.getElementById("quantidade");


    // -----------------------------------------------------
    // VALIDA GÊNERO
    // -----------------------------------------------------

    if (!generoElement) {

        alert(
            "Selecione o gênero."
        );

        return;
    }


    // -----------------------------------------------------
    // VALIDA TAMANHO
    // -----------------------------------------------------

    if (!tamanhoElement.value) {

        alert(
            "Selecione o tamanho."
        );

        return;
    }


    // -----------------------------------------------------
    // QUANTIDADE
    // -----------------------------------------------------

    const quantidade =
        parseInt(
            quantidadeElement.value
        );


    if (
        isNaN(quantidade) ||
        quantidade <= 0
    ) {

        alert(
            "Informe uma quantidade válida."
        );

        return;
    }


    // -----------------------------------------------------
    // CRIA ITEM
    // -----------------------------------------------------

    const novoItem = {

        genero:
            generoElement.value,

        tamanho:
            tamanhoElement.value,

        quantidade:
            quantidade

    };


    // -----------------------------------------------------
    // ADICIONA AO ARRAY
    // -----------------------------------------------------

    itens.push(
        novoItem
    );


    // -----------------------------------------------------
    // ATUALIZA CARRINHO
    // -----------------------------------------------------

    atualizarCarrinho();


    // -----------------------------------------------------
    // LIMPA CAMPOS
    // -----------------------------------------------------

    quantidadeElement.value = "";

    tamanhoElement.value = "";

    generoElement.checked = false;

}


// =========================================================
// ATUALIZAR CARRINHO
// =========================================================

function atualizarCarrinho() {

    listaItens.innerHTML = "";


    // -----------------------------------------------------
    // NENHUM ITEM
    // -----------------------------------------------------

    if (itens.length === 0) {

        listaItens.innerHTML = `

            <p class="text-muted mb-0">

                Nenhum item adicionado.

            </p>

        `;


        totalItens.textContent = "0";

        return;
    }


    // -----------------------------------------------------
    // CRIA LISTA
    // -----------------------------------------------------

    let total = 0;


    itens.forEach(
        function(item, index) {

            total +=
                item.quantidade;


            const linha =
                document.createElement("div");


            linha.className =
                "d-flex justify-content-between align-items-center border-bottom py-2";


            linha.innerHTML = `

                <div>

                    <strong>
                        ${item.genero}
                    </strong>

                    <span class="text-muted">
                        -
                    </span>

                    Tamanho
                    <strong>
                        ${item.tamanho}
                    </strong>

                    <span class="text-muted">
                        -
                    </span>

                    <strong>
                        ${item.quantidade}
                    </strong>
                    peças

                </div>


                <button
                    type="button"
                    class="btn btn-sm btn-danger"
                    onclick="removerItem(${index})"
                >

                    Remover

                </button>

            `;


            listaItens.appendChild(
                linha
            );

        }
    );


    // -----------------------------------------------------
    // TOTAL
    // -----------------------------------------------------

    totalItens.textContent =
        total;

}


// =========================================================
// REMOVER ITEM
// =========================================================

function removerItem(index) {

    itens.splice(
        index,
        1
    );


    atualizarCarrinho();

}


// =========================================================
// ENVIAR RELATÓRIO
// =========================================================

async function enviarRelatorio() {

    // -----------------------------------------------------
    // LIMPA MENSAGEM
    // -----------------------------------------------------

    mensagem.innerHTML = "";


    // -----------------------------------------------------
    // CAMPOS
    // -----------------------------------------------------

    const dataProducao =
        document.getElementById(
            "data_producao"
        ).value;


    const etapa =
        document.getElementById(
            "etapa"
        ).value;


    const produto =
        document.getElementById(
            "produto"
        ).value;




    const observacao =
        document.getElementById(
            "observacao"
        ).value;


    // -----------------------------------------------------
    // VALIDA DATA
    // -----------------------------------------------------

    if (!dataProducao) {

        mostrarErro(
            "Informe a data da produção."
        );

        return;
    }


    // -----------------------------------------------------
    // VALIDA ETAPA
    // -----------------------------------------------------

    if (!etapa) {

        mostrarErro(
            "Selecione a etapa."
        );

        return;
    }


    // -----------------------------------------------------
    // VALIDA PRODUTO
    // -----------------------------------------------------

    if (!produto) {

        mostrarErro(
            "Selecione o produto."
        );

        return;
    }


   

    // -----------------------------------------------------
    // VALIDA ITENS
    // -----------------------------------------------------

    if (itens.length === 0) {

        mostrarErro(
            "Adicione pelo menos um item ao relatório."
        );

        return;
    }


    // -----------------------------------------------------
    // MONTA JSON
    // -----------------------------------------------------

    const dados = {

        data_producao:
            dataProducao,

        etapa:
            etapa,

        produto:
            produto,
        observacao:
            observacao,

        itens:
            itens

    };


    // -----------------------------------------------------
    // DESABILITA BOTÃO
    // -----------------------------------------------------

    const btnSalvar =
        document.getElementById(
            "btnSalvar"
        );


    btnSalvar.disabled = true;

    btnSalvar.textContent =
        "Salvando...";


    try {

        // -------------------------------------------------
        // ENVIA PARA FLASK
        // -------------------------------------------------

        const resposta =
            await fetch(
                "/api/producoes",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            dados
                        )

                }
            );


        // -------------------------------------------------
        // CONVERTE RESPOSTA
        // -------------------------------------------------

        const resultado =
            await resposta.json();


        // -------------------------------------------------
        // ERRO
        // -------------------------------------------------

        if (!resposta.ok) {

            mostrarErro(
                resultado.erro ||
                "Erro ao salvar relatório."
            );

            return;
        }


        // -------------------------------------------------
        // SUCESSO
        // -------------------------------------------------

        mostrarSucesso(
            resultado.mensagem
        );


        // -------------------------------------------------
        // AGUARDA UM POUCO
        // E RECARREGA
        // -------------------------------------------------

        setTimeout(
            function() {

                window.location.reload();

            },
            1200
        );


    }
    catch (erro) {

        console.error(
            erro
        );


        mostrarErro(
            "Não foi possível conectar ao servidor."
        );

    }
    finally {

        btnSalvar.disabled = false;

        btnSalvar.textContent =
            "Salvar relatório";

    }

}


// =========================================================
// MENSAGEM DE ERRO
// =========================================================

function mostrarErro(texto) {

    mensagem.innerHTML = `

        <div class="alert alert-danger">

            ${texto}

        </div>

    `;

}


// =========================================================
// MENSAGEM DE SUCESSO
// =========================================================

function mostrarSucesso(texto) {

    mensagem.innerHTML = `

        <div class="alert alert-success">

            ${texto}

        </div>

    `;

}


// =========================================================
// EVENTO - ADICIONAR ITEM
// =========================================================

btnAdicionar.addEventListener(
    "click",
    adicionarItem
);


// =========================================================
// EVENTO - ENVIAR FORMULÁRIO
// =========================================================

form.addEventListener(
    "submit",
    function(event) {

        event.preventDefault();

        enviarRelatorio();

    }
);


// =========================================================
// DEFINE DATA ATUAL
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        const campoData =
            document.getElementById(
                "data_producao"
            );


        if (campoData) {

            const hoje =
                new Date();


            const ano =
                hoje.getFullYear();


            const mes =
                String(
                    hoje.getMonth() + 1
                ).padStart(
                    2,
                    "0"
                );


            const dia =
                String(
                    hoje.getDate()
                ).padStart(
                    2,
                    "0"
                );


            campoData.value =
                `${ano}-${mes}-${dia}`;

        }

    }
);