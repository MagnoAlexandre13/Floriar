# Diagramas — Petal & Stem

O escopo destes artefatos é o backend e o cliente REST local em `/cliente`.
O cliente pode consultar produtos, criar e acompanhar pedidos e demonstrar a
atualização dos estados. Não há pagamento nem entrega real. O cliente precisa
entrar na conta para criar ou consultar seus pedidos. O administrador consulta
todos os pedidos e atualiza as etapas; o cliente pode cancelar os próprios
pedidos antes do envio. O catálogo permanece público.

## Casos de uso (UML em PlantUML)

O bloco abaixo usa a notação de casos de uso do PlantUML. Para gerar uma imagem,
abra-o em um renderizador PlantUML; editores sem esse suporte mostrarão o código.

```plantuml
@startuml
left to right direction
actor Cliente
actor "Operador (demonstração)" as Operador
rectangle "Petal & Stem — API REST" {
  usecase "Criar conta" as Cadastro
  usecase "Entrar na conta" as Login
  usecase "Sair da conta" as Logout
  usecase "Consultar catálogo" as Catalogo
  usecase "Consultar produto" as Produto
  usecase "Consultar frete e datas" as Entrega
  usecase "Criar pedido demonstrativo" as Criar
  usecase "Validar itens e calcular total" as Validar
  usecase "Consultar pedido" as Consultar
  usecase "Listar pedidos" as Listar
  usecase "Atualizar estado" as Atualizar
}
Cliente --> Catalogo
Cliente --> Cadastro
Cliente --> Login
Cliente --> Logout
Cliente --> Produto
Cliente --> Entrega
Cliente --> Criar
Cliente --> Consultar
Criar ..> Validar : <<include>>
Operador --> Listar
Operador --> Consultar
Operador --> Atualizar
Operador --> Login
Operador --> Logout
@enduml
```

## DER (Mermaid)

As entidades correspondem às tabelas de `backend/schema.sql`. `details` guarda
os atributos descritivos do produto como JSON; os preços e os relacionamentos
que participam das regras são colunas próprias. O nome e os valores no item
preservam o histórico da compra.

```mermaid
erDiagram
    users ||--o{ sessions : "possui"
    users |o--o{ orders : "realiza"
    products ||--o{ order_items : "compõe"
    orders ||--|{ order_items : "contém"
    users {
        TEXT id PK "UUID"
        TEXT name
        TEXT email UK
        TEXT password_hash
        TEXT role "customer ou admin"
        TEXT created_at
    }
    sessions {
        TEXT token_hash PK
        TEXT user_id FK
        TEXT csrf_token
        INTEGER expires_at
        INTEGER created_at
    }
    auth_attempts {
        TEXT key_hash PK "Hash do e-mail normalizado"
        INTEGER failures
        INTEGER window_start
    }
    products {
        TEXT id PK
        TEXT name
        INTEGER price_cents
        INTEGER lead_days
        TEXT details "JSON descritivo"
    }
    orders {
        TEXT id PK "UUID"
        TEXT user_id FK "Nulo apenas em pedidos legados"
        TEXT status
        TEXT currency
        INTEGER subtotal_cents
        INTEGER delivery_cents
        INTEGER total_cents
        TEXT created_at
        TEXT updated_at
    }
    order_items {
        INTEGER id PK
        TEXT order_id FK
        TEXT product_id FK
        TEXT product_name
        TEXT size
        INTEGER quantity
        INTEGER vase "0 ou 1"
        TEXT zip
        TEXT date
        TEXT message
        TEXT color
        TEXT description
        INTEGER unit_price_cents
        INTEGER delivery_fee_cents
        INTEGER line_total_cents
    }
```

Todo pedido novo recebe o usuário autenticado como proprietário. A relação
opcional com `users` existe para preservar pedidos anteriores à autenticação;
esses pedidos são visíveis apenas a administradores. `auth_attempts` controla
tentativas por hash do e-mail, inclusive quando a conta não existe, sem relação
obrigatória com `users`. As sessões expiram após oito horas e são revogadas no logout.

## Classes (Mermaid)

Diagrama simplificado das classes implementadas. Os schemas de saída são
modelos Pydantic, e a persistência usa SQL parametrizado, sem ORM. As rotas
delegam aos controllers, que usam queries e a infraestrutura `Database`.

```mermaid
classDiagram
    class AuthController {
        +Database database
        +create_user(payload, role)
        +login(payload, previous_token)
        +start_session(user, previous_token)
        +authenticate(token)
        +logout(session)
    }
    class AuthQueries {
        +user_by_email(connection, email)
        +insert_user(connection, user)
        +insert_session(connection, session)
        +session(connection, digest, now)
        +revoke_session(connection, digest)
    }
    class User {
        +str id
        +str name
        +str email
        +str role
        +datetime created_at
    }
    class Database {
        +Path path
        +initialize()
        +connect()
        +transaction(write)
    }
    class ProductController {
        +Database database
        +products(color, budget)
        +product(product_id)
    }
    class DeliveryController {
        +ProductController products
        +dates(product_id)
        +quote(zip_code)
    }
    class OrderController {
        +Database database
        +create_order(payload, actor)
        +order(order_id, actor)
        +orders(status, limit, offset, actor)
        +update_status(order_id, target, actor)
    }
    class SystemController {
        +Database database
        +health()
    }
    class ProductQueries {
        +list_products(connection)
        +get_product(connection, product_id)
        +seed_catalog(connection, products)
    }
    class OrderQueries {
        +get_order(connection, order_id)
        +list_order_ids(connection, status, limit, offset)
        +count_orders(connection, status)
        +insert_order(connection, order)
        +insert_items(connection, order_id, items)
        +update_status(connection, order_id, status, updated_at)
    }
    class SystemQueries {
        +check_health(connection)
    }
    class Product {
        +str id
        +str name
        +int price_cents
        +int lead
    }
    class OrderCreate {
        +OrderItemCreate[] items
    }
    class OrderItemCreate {
        +str product
        +str size
        +int quantity
        +bool vase
        +str zip
        +str date
        +str message
        +str color
        +str description
    }
    class Order {
        +str id
        +str user_id
        +OrderStatus status
        +str currency
        +int subtotal_cents
        +int delivery_cents
        +int total_cents
        +datetime created_at
        +datetime updated_at
    }
    class OrderItem {
        +int id
        +str product_id
        +str product_name
        +str size
        +int quantity
        +bool vase
        +str zip
        +date date
        +str message
        +str color
        +str description
        +int unit_price_cents
        +int delivery_fee_cents
        +int line_total_cents
    }
    class OrderStatus {
        <<enumeration>>
        recebido
        em_preparacao
        enviado
        entregue
        cancelado
    }
    ProductController --> Database : usa
    AuthController --> Database : usa
    AuthController ..> AuthQueries : persiste contas e sessões
    AuthController ..> User : retorna dados públicos
    Order --> User : proprietário
    ProductController ..> ProductQueries : consulta
    ProductController ..> Product : retorna dados
    DeliveryController --> ProductController : consulta produto
    OrderController --> Database : coordena transações
    OrderController ..> OrderQueries : persiste e consulta
    OrderController ..> ProductQueries : consulta preços
    OrderController ..> OrderCreate : recebe dados validados
    SystemController --> Database : usa
    SystemController ..> SystemQueries : consulta
    OrderCreate "1" *-- "1..30" OrderItemCreate
    Order "1" *-- "1..30" OrderItem
    Order --> OrderStatus
    OrderItem --> Product : product_id
```

## Transição de estados (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> recebido : POST /api/pedidos
    recebido --> em_preparacao : PATCH status
    recebido --> cancelado : PATCH status
    em_preparacao --> enviado : PATCH status
    em_preparacao --> cancelado : PATCH status
    enviado --> entregue : PATCH status
    entregue --> [*]
    cancelado --> [*]
```

Transições não desenhadas retornam HTTP 409. Repetir o estado atual retorna
HTTP 200 sem alteração. A leitura do estado e sua atualização são realizadas
na mesma transação SQLite para evitar transições concorrentes inconsistentes.

## Sequência de criação de pedido (Mermaid)

```mermaid
sequenceDiagram
    actor Pessoa
    participant Cliente as Cliente HTML/JS
    participant API as Rotas FastAPI e schemas
    participant Controle as OrderController
    participant Queries as ProductQueries e OrderQueries
    participant Banco as SQLite
    Pessoa->>Cliente: Escolher produto e entrega
    Cliente->>API: GET /api/produtos e /datas
    API-->>Cliente: 200 JSON
    Pessoa->>Cliente: Criar pedido demonstrativo
    Cliente->>API: POST /api/pedidos (JSON, cookie e CSRF)
    API->>API: Validar sessão, CSRF e usuário
    API->>API: Validar contrato Pydantic
    API->>Controle: create_order(payload)
    Controle->>Banco: BEGIN IMMEDIATE via Database
    Controle->>Queries: get_product(conexão, produto)
    Queries->>Banco: SELECT produtos
    Banco-->>Queries: Preços e antecedência
    Queries-->>Controle: Produto
    Controle->>Controle: Validar entrega e calcular em centavos
    alt Todos os itens válidos
        Controle->>Queries: insert_order e insert_items
        Queries->>Banco: INSERT pedido e itens
        Controle->>Banco: COMMIT via Database
        Controle-->>API: Pedido completo
        API-->>Cliente: 201 JSON + Location
        Cliente-->>Pessoa: Identificador e total
    else Produto ou entrega inválidos
        Controle->>Banco: ROLLBACK via Database
        Controle-->>API: ShopError
        API-->>Cliente: 404 ou 422 JSON
        Cliente-->>Pessoa: Mensagem de erro
    end
```
