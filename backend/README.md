# API REST — Petal & Stem

Backend acadêmico local em Python 3.11+, FastAPI, Pydantic e SQLite. O catálogo
e as regras reproduzem a loja existente: preços em USD, área ilustrativa de
Portland e calendário no fuso `America/Los_Angeles`.

## Executar

Na raiz `petal-and-stem`:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

No Linux/macOS, use `.venv/bin/python` no lugar de `.venv\Scripts\python.exe`.
As versões de dependências declaradas são as usadas na validação do backend.

| Endereço | Conteúdo |
| --- | --- |
| `/cliente` | Cliente HTML/JavaScript que consome a API via `fetch()` |
| `/conta.html` | Cadastro, login, perfil da conta e logout |
| `/docs` | Swagger UI com requisições de teste e esquemas JSON |
| `/redoc` | Outra visualização do contrato |
| `/openapi.json` | Contrato OpenAPI exportável em JSON |
| `/` | Loja original estática, com carrinho local independente |

O cliente `/cliente` e a API funcionam localmente. Swagger UI e ReDoc carregam
suas bibliotecas de um CDN e precisam de acesso à internet; o contrato JSON
continua acessível sem isso.

## Endpoints

Base: `http://127.0.0.1:8010`. Corpos e respostas da API usam JSON.

| Método | Endpoint | Sucesso | Função |
| --- | --- | --- | --- |
| POST | `/api/auth/cadastro` | 201 | Criar conta de cliente e iniciar sessão |
| POST | `/api/auth/login` | 200 | Entrar com e-mail e senha |
| GET | `/api/auth/me` | 200 | Consultar conta e token CSRF da sessão |
| POST | `/api/auth/logout` | 204 | Revogar a sessão e remover o cookie |
| GET | `/api/health` | 200 | Verificar aplicação e banco |
| GET | `/api/produtos` | 200 | Listar produtos; filtros opcionais `color` e `budget` |
| GET | `/api/produtos/{product_id}` | 200 | Consultar produto pelo identificador textual |
| GET | `/api/produtos/{product_id}/datas` | 200 | Datas e motivos de indisponibilidade |
| GET | `/api/entrega/{zip_code}` | 200 | Frete por buquê para o ZIP informado |
| POST | `/api/pedidos` | 201 | Validar e criar pedido; cabeçalho `Location` aponta para consulta |
| GET | `/api/pedidos` | 200 | Listar pedidos com `status`, `limit` e `offset` opcionais |
| GET | `/api/pedidos/{order_id}` | 200 | Consultar pedido por UUID |
| PATCH | `/api/pedidos/{order_id}/status` | 200 | Alterar estado respeitando as transições |

`budget` é o preço base máximo do produto em dólares, por exemplo
`/api/produtos?color=cream&budget=50`. Não inclui tamanho, vaso ou frete.
Na lista de pedidos, `limit` tem padrão 20 e aceita 1–100; `offset` tem padrão 0.
A resposta contém `items`, `total`, `limit` e `offset`; `total` respeita o filtro
de estado e a ordenação é da criação mais recente para a mais antiga.

## Contas, sessões e permissões

Abra `/conta.html` para criar uma conta ou entrar. O cadastro aceita:

```json
{"name":"Ana Flores","email":"ana@example.com","password":"uma-frase-com-10-ou-mais-caracteres"}
```

No login, envie apenas `email` e `password`. Nome deve ter de 2 a 100 caracteres;
e-mail até 254; senha de cadastro de 10 a 128. O e-mail é normalizado para
minúsculas; a senha preserva espaços. Campos adicionais, incluindo `role`, são
rejeitados. O cadastro público sempre cria uma conta `customer`.

Cadastro e login retornam `user` (id, nome, e-mail, papel e criação) e
`csrf_token`, além de definir o cookie `petal_session` com `HttpOnly`,
`SameSite=Lax` e validade de oito horas. O identificador aleatório da sessão
nunca é enviado no JSON ou guardado no localStorage. O banco guarda apenas seu
hash SHA-256. `/me` permite recuperar o token CSRF após recarregar a página.

As senhas usam PBKDF2-HMAC-SHA256 com 600.000 iterações e salt aleatório.
Após cinco falhas de login para um e-mail dentro da janela de 15 minutos, a
API retorna 429 até a janela terminar. O logout revoga a sessão no banco,
invalidando também cópias do cookie. As respostas de contas e pedidos usam
`Cache-Control: no-store`.

| Ação | Público | Cliente | Administrador |
| --- | --- | --- | --- |
| Consultar catálogo, frete e datas | Sim | Sim | Sim |
| Criar pedido | Não | Em sua conta | Em sua conta |
| Listar e consultar pedidos | Não | Apenas próprios | Todos, inclusive legados |
| Cancelar pedido antes do envio | Não | Apenas próprios | Todos |
| Avançar etapas do pedido | Não | Não | Sim |

Requisições de escrita autenticadas (`POST /api/pedidos`, `PATCH` de estado e
`POST /api/auth/logout`) exigem o cookie e o cabeçalho `X-CSRF-Token`, obtido
na resposta de login, cadastro ou `/me`. O frontend faz isso automaticamente
em `dist/auth-api.js`, usando `fetch` com `credentials: 'include'`. Origens
estranhas são rejeitadas. A API responde 401 sem sessão, 403 sem permissão ou
CSRF válido e 404 ao tentar acessar o pedido de outra pessoa.

Não há administrador padrão. Promova uma conta cadastrada pelo terminal local:

```powershell
.venv\Scripts\python.exe -m backend.create_admin --email ana@example.com --promote
```

Também é possível criar uma conta administrativa nova com
`python -m backend.create_admin`; o comando solicita nome, e-mail e senha,
sem colocar a senha na linha de comando. A criação/promoção administrativa
não está exposta por endpoints públicos.

Por padrão, o cookie permite o HTTP local. Em uma hospedagem HTTPS, configure
`PETAL_COOKIE_SECURE=true` e os endereços permitidos na configuração da aplicação.
As páginas funcionam diretamente na porta 8010. No desenvolvimento com Node na
porta 4173, `scripts/serve.mjs` encaminha `/api/`, `/cliente` e a documentação
para o backend na porta 8010. Uma hospedagem apenas estática não executa o login.

No Swagger, entre primeiro em `/conta.html` no mesmo endereço do servidor e
abra `/docs`. O navegador já enviará o cookie; preencha `X-CSRF-Token` nas
operações de escrita com o valor retornado por `/api/auth/me`.

## Formatos JSON

Exemplo de produto (trecho; o contrato contém todos os campos descritivos):

```json
{
  "id": "sunday-morning",
  "name": "Manhã de Domingo",
  "price": 48.0,
  "price_cents": 4800,
  "lead": 2,
  "color": "cream"
}
```

Criação de pedido:

```json
{
  "items": [
    {
      "product": "sunday-morning",
      "size": "classic",
      "quantity": 2,
      "vase": true,
      "zip": "97201",
      "date": "2026-11-21",
      "message": "Para você!",
      "color": "pink",
      "description": "Um buquê delicado com flores rosas, folhagens leves e papel kraft."
    }
  ]
}
```

A data acima é ilustrativa: antes de enviar, consulte
`GET /api/produtos/sunday-morning/datas` e use uma data com `available: true`.
O calendário depende do dia atual no fuso do estúdio.

`items` aceita entre 1 e 30 itens. Por item:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `product` | string | Identificador de produto existente; obrigatório |
| `size` | string | Pequeno (`petite`), Médio (`classic`) ou Grande (`abundant`); padrão `classic` |
| `quantity` | inteiro | 1–9; padrão 1; strings, booleanos e frações são rejeitados |
| `vase` | booleano | `true` ou `false`; padrão `false` |
| `zip` | string | Cinco algarismos, entre `97201` e `97206`; obrigatório |
| `date` | string | Data válida `YYYY-MM-DD`; obrigatória |
| `message` | string | Até 240 caracteres; padrão vazio |
| `color` | string | Valor de `colors` do produto; padrão `original` |
| `description` | string | De 10 a 1000 caracteres quando enviada; descrição do arranjo imaginado |

As páginas da loja e do cliente solicitam a descrição do buquê obrigatoriamente,
separada da mensagem do cartão. A API permite omitir `description` para manter
compatibilidade com clientes anteriores; nesse caso, o valor salvo é vazio.
As cores são `original` (paleta da foto), `yellow` (amarelo), `pink` (rosa),
`white` (branco), `red` (vermelho) e `lilac` (lilás), conforme a lista `colors`
de cada produto. Girassóis aceitam `original`, `yellow`, `white` e `pink`;
nesses buquês a cor orienta as flores de apoio e a embalagem, preservando os
girassóis amarelos. Cores e descrição não alteram o preço.

Campos adicionais são rejeitados, inclusive preços e totais enviados pelo
cliente. Os identificadores locais dos itens do carrinho da loja não devem ser
enviados; monte um corpo apenas com os campos acima.

Resposta de criação/consulta (UUID e horários ilustrativos):

```json
{
  "id": "a2ad42d5-37ba-4b96-9e75-f61a5f864462",
  "user_id": "0f8883ae-0d69-42d0-8bb0-4e28e3e6472c",
  "status": "recebido",
  "currency": "USD",
  "subtotal_cents": 17200,
  "delivery_cents": 1200,
  "total_cents": 18400,
  "created_at": "2026-11-17T15:00:00Z",
  "updated_at": "2026-11-17T15:00:00Z",
  "items": [
    {
      "id": 1,
      "product_id": "sunday-morning",
      "product_name": "Manhã de Domingo",
      "size": "classic",
      "quantity": 2,
      "vase": true,
      "zip": "97201",
      "date": "2026-11-21",
      "message": "Para você!",
      "color": "pink",
      "description": "Um buquê delicado com flores rosas, folhagens leves e papel kraft.",
      "unit_price_cents": 8600,
      "delivery_fee_cents": 600,
      "line_total_cents": 18400
    }
  ]
}
```

Todos os campos com sufixo `_cents` são inteiros em centavos de USD. Por exemplo,
18400 corresponde a US$ 184,00. `unit_price_cents` inclui tamanho e vaso;
`line_total_cents` inclui o frete multiplicado pela quantidade. Nomes e preços
são registrados no item do pedido, preservando o histórico mesmo que o catálogo
seja alterado depois. Os horários são UTC; as datas de entrega são datas locais.

Consulta de frete:

```json
{"zip": "97201", "currency": "USD", "fee_cents": 600}
```

Elemento da lista de datas:

```json
{"date": "2026-11-21", "available": true, "reason": null}
```

Atualização de estado:

```json
{"status": "em_preparacao"}
```

Fluxo: `recebido → em_preparacao → enviado → entregue`. É possível ir para
`cancelado` a partir de `recebido` ou `em_preparacao`. `entregue` e `cancelado`
são terminais. Repetir o estado atual é permitido e não altera o horário.

## Regras de entrega e preço

- Tamanhos: Pequeno sem acréscimo; Médio +2000 centavos; Grande +4000.
- Vaso: +1800 centavos por buquê.
- Frete por buquê: 600 centavos nos ZIPs 97201–97202; 900 nos ZIPs 97203–97206.
- Antecedência: dois dias; Espírito Livre exige cinco.
- Domingo e segunda-feira fechados; limite de agendamento de 30 dias.
- O dia dez dias à frente está lotado na simulação se cair em dia de funcionamento.
- O servidor valida novamente as datas no envio do pedido. Uma data consultada
  antes pode ficar inválida depois da virada do dia.
- A gravação é atômica: um item inválido impede a criação do pedido inteiro.

## Erros

| HTTP | Situação |
| --- | --- |
| 401 | Sessão ausente/expirada ou credenciais inválidas |
| 403 | CSRF/origem inválida ou ação reservada ao administrador |
| 404 | Produto ou pedido inexistente |
| 409 | Transição de estado não permitida |
| 422 | JSON, tipos, campos, quantidades, UUID ou entrega inválidos |
| 503 | Banco temporariamente indisponível |
| 429 | Limite de tentativas de login excedido |

```json
{
  "error": {
    "code": "invalid_status_transition",
    "message": "Não é permitido mudar de recebido para entregue."
  }
}
```

Erros de estrutura retornam `code: "validation_error"` e uma lista `details`
com `location`, `message` e `type`, sem repetir os valores enviados pelo cliente.

## Teste de ponta a ponta pelo PowerShell

Com o servidor ativo:

```powershell
$petalBase = 'http://127.0.0.1:8010'
$petalCredentials = Get-Credential -Message 'Entre com uma conta já cadastrada'
$petalLoginBody = @{ email = $petalCredentials.UserName; password = $petalCredentials.GetNetworkCredential().Password } | ConvertTo-Json
$petalAuth = Invoke-RestMethod "$petalBase/api/auth/login" -Method Post -ContentType 'application/json' -Body $petalLoginBody -SessionVariable petalSession
$petalHeaders = @{ 'X-CSRF-Token' = $petalAuth.csrf_token }
$petalDates = Invoke-RestMethod "$petalBase/api/produtos/sunday-morning/datas"
$petalDate = ($petalDates | Where-Object { $_.available } | Select-Object -First 1).date
$petalBody = @{ items = @(@{
  product = 'sunday-morning'
  size = 'classic'
  quantity = 1
  vase = $false
  zip = '97201'
  date = $petalDate
  message = 'Pedido demonstrativo'
}) } | ConvertTo-Json -Depth 5
$petalOrder = Invoke-RestMethod "$petalBase/api/pedidos" -Method Post -ContentType 'application/json' -Body $petalBody -WebSession $petalSession -Headers $petalHeaders
Invoke-RestMethod "$petalBase/api/pedidos/$($petalOrder.id)" -WebSession $petalSession
Invoke-RestMethod "$petalBase/api/pedidos/$($petalOrder.id)/status" -Method Patch -ContentType 'application/json' -Body '{"status":"cancelado"}' -WebSession $petalSession -Headers $petalHeaders
```

## Persistência e organização

O banco padrão é `backend/data/store.sqlite3`, criado no início do servidor,
com tabelas `products`, `orders`, `order_items`, `users`, `sessions` e
`auth_attempts`. O catálogo inicial é a cópia
versionada `backend/catalog.json`, extraída do catálogo atual da loja. A carga
inicial insere produtos ausentes e sincroniza nomes e textos descritivos do
catálogo versionado em português, sem sobrescrever preços ou prazos existentes.
Os nomes e valores registrados em pedidos anteriores permanecem inalterados.
Na inicialização, uma migração aditiva inclui `color` e `description` nos itens
de bancos anteriores. Os pedidos existentes mantêm seus preços e nomes e
recebem `original` e descrição vazia. Reiniciar não duplica as colunas.
Outra migração inclui `orders.user_id` como referência a `users`. Pedidos
anteriores ficam com proprietário nulo e só são acessíveis a administradores;
eles não são atribuídos automaticamente a quem se cadastrar primeiro.

É possível usar outro caminho pela variável de ambiente `PETAL_DB_PATH`:

```powershell
$env:PETAL_DB_PATH = 'C:\caminho\para\meu-banco.sqlite3'
```

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Configuração da aplicação, CORS e registro das rotas e erros |
| `routes/` | URLs, métodos HTTP, parâmetros, respostas e chamada dos controllers |
| `controllers/` | Regras de entrega, filtros, preços, estados e coordenação das transações |
| `queries/` | SQL parametrizado e conversão dos registros do banco |
| `schemas/` | Contratos Pydantic de entrada e saída e validação de tipos |
| `dependencies.py` | Injeção do banco e dos controllers por requisição |
| `security.py` | Hash de senhas, verificação e parâmetros de sessão |
| `create_admin.py` | Criação/promoção administrativa pelo terminal local |
| `exceptions.py` / `exception_handlers.py` | Erros de negócio e sua conversão para HTTP JSON |
| `database.py` | Conexões e transações SQLite e inicialização do esquema e catálogo |
| `schema.sql` | Tabelas, relacionamentos, restrições e índices |
| `catalog.json` | Dados iniciais dos cinco buquês, incluindo girassóis |
| `client.html` / `client.js` | Cliente REST demonstrativo |
| `../tests/test_backend.py` | Testes HTTP com banco temporário |

A organização por recurso se repete nas camadas:

```text
backend/
├── main.py
├── database.py
├── dependencies.py
├── exceptions.py
├── exception_handlers.py
├── routes/
│   ├── products.py
│   ├── auth.py
│   ├── orders.py
│   ├── delivery.py
│   ├── system.py
│   └── pages.py
├── controllers/
│   ├── auth.py
│   ├── products.py
│   ├── orders.py
│   ├── delivery.py
│   └── system.py
├── queries/
│   ├── auth.py
│   ├── products.py
│   ├── orders.py
│   └── system.py
└── schemas/
    ├── auth.py
    ├── common.py
    ├── products.py
    ├── orders.py
    ├── delivery.py
    └── errors.py
```

Fluxo de uma requisição: **rota → schema de entrada → controller → query →
SQLite → schema de saída → resposta JSON**. O FastAPI usa os schemas para
validar o corpo antes da chamada do controller e documentar o contrato OpenAPI.
As rotas não executam SQL; os controllers não dependem do FastAPI e não contêm
consultas SQL. As queries recebem a conexão fornecida pelo controller, sem abrir
ou confirmar transações próprias. `Database.transaction()` controla commit e
rollback para que todas as consultas de uma operação usem a mesma transação.

`routes/pages.py` serve apenas os arquivos do cliente demonstrativo. Em
`database.py`, os comandos de infraestrutura (PRAGMA, BEGIN e criação do esquema)
continuam junto ao gerenciamento de conexões; a carga dos produtos usa as queries.

As contas e os pedidos têm autenticação e autorização conforme a seção acima.
Não há recuperação de senha por e-mail, verificação de e-mail ou MFA nesta versão.
Não há pagamentos,
estoque real, assinaturas ou serviço de entrega. Repetir um POST cria outro pedido;
o cliente bloqueia o botão durante o envio, mas não há idempotência entre requisições.

A página `/cliente` é o cliente integrado desta API. A interface original
`dist/app.js` permanece independente: seu catálogo e carrinho continuam locais.
CORS permite os endereços Node de desenvolvimento `http://127.0.0.1:4173` e
`http://localhost:4173`, caso a integração da loja seja feita depois.

## Verificação

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

Os testes criam bancos temporários e cobrem cálculos, dados inválidos, transações,
persistência, histórico de preços, paginação, estados, entrega, CORS e contrato
OpenAPI. Referências: [testes FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
e [inicialização por lifespan](https://fastapi.tiangolo.com/advanced/events/).
As decisões de autenticação também consultam as referências oficiais
[OWASP: armazenamento de senhas](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
e [OWASP: proteção CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

Para testar o cliente em Microsoft Edge com Playwright, instale as dependências
Node (`npm install`) e execute `npm run test:api-browser`. O teste inicia seu
próprio servidor na porta 8001 e usa um banco separado em uma pasta temporária.
Para os scripts `npm run dev:api` e `npm run test:api`, o comando `python` deve
apontar para o ambiente em que as dependências Python foram instaladas.

Para a apresentação acadêmica, veja os [diagramas](../docs/DIAGRAMAS.md).
No ZIP de entrega, inclua `backend/`, `dist/`, `docs/`, `tests/`, `scripts/`,
README, arquivos de dependências e licenças. Exclua `.git/`, `.venv/`,
`node_modules/`, bancos gerados e caches; os dados iniciais são recriados pelo servidor.

O empacotamento pode ser feito com:

```powershell
python scripts/package-project.py
```

O arquivo `petal-and-stem-entrega.zip` é criado na pasta acima do projeto. Para
gerar outra entrega sem substituir a anterior, use `--output outro-nome.zip`.
