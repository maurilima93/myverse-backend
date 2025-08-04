# MyVerse Backend - AWS RDS

Backend Flask para a rede social de entretenimento MyVerse, configurado para usar PostgreSQL na AWS RDS.

## Funcionalidades

- ✅ **Autenticação JWT** - Sistema completo de login/registro
- ✅ **AWS RDS PostgreSQL** - Banco de dados robusto e escalável na AWS
- ✅ **APIs Externas** - Integração com TMDb (filmes/séries) e IGDB (jogos)
- ✅ **Sistema de Fóruns** - Discussões e comentários aninhados
- ✅ **Preferências de Usuário** - Sistema de recomendações personalizado
- ✅ **Sistema de Favoritos** - Salvar conteúdo preferido
- ✅ **CORS Configurado** - Pronto para frontend React

## Configuração AWS RDS

Este backend está configurado para conectar ao seu PostgreSQL na AWS RDS:
- **Host**: personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com
- **Database**: personal-feed
- **User**: admin1
- **SSL**: Obrigatório (configurado automaticamente)

## Deploy no Railway

1. **Conectar repositório** no Railway
2. **Configurar variáveis de ambiente**:
   - `SECRET_KEY` - Chave secreta do Flask
   - `JWT_SECRET_KEY` - Chave secreta do JWT
   - `DB_HOST` - personal-feed.c3yc0my6ywu9.sa-east-1.rds.amazonaws.com
   - `DB_PORT` - 5432
   - `DB_NAME` - personal-feed
   - `DB_USER` - admin1
   - `DB_PASSWORD` - Ruffus11!
   - `TMDB_API_KEY` - (Opcional) Chave da API TMDb
   - `IGDB_CLIENT_ID` - (Opcional) ID do cliente IGDB
   - `IGDB_ACCESS_TOKEN` - (Opcional) Token de acesso IGDB

3. **Deploy automático** - Railway detecta o Procfile e faz deploy

## Tecnologias

- **Flask** - Framework web Python
- **SQLAlchemy** - ORM para banco de dados
- **AWS RDS PostgreSQL** - Banco de dados principal
- **JWT** - Autenticação segura
- **Gunicorn** - Servidor WSGI para produção

## Instalação Local

```bash
# Clonar repositório
git clone <repository-url>
cd myverse-backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações (já preenchido com AWS RDS)

# Executar aplicação
python src/main.py
```

## Estrutura do Projeto

```
src/
├── main.py              # Aplicação Flask principal (configurado para AWS RDS)
├── models/
│   └── database.py      # Modelos SQLAlchemy
├── routes/
│   ├── auth.py          # Rotas de autenticação
│   ├── content.py       # Rotas de conteúdo
│   ├── user.py          # Rotas de usuário
│   └── forum.py         # Rotas do fórum
└── services/
    ├── tmdb_service.py  # Integração TMDb
    └── igdb_service.py  # Integração IGDB
```

## Configuração de Segurança AWS

- ✅ **SSL/TLS obrigatório** para conexões com RDS
- ✅ **Connection pooling** configurado
- ✅ **Timeout de conexão** otimizado
- ✅ **Pool pre-ping** para conexões saudáveis

## APIs Disponíveis

### Autenticação
- `POST /api/auth/register` - Registrar usuário
- `POST /api/auth/login` - Login
- `GET /api/auth/profile` - Perfil do usuário

### Conteúdo
- `GET /api/content/search` - Pesquisar conteúdo
- `GET /api/content/trending` - Conteúdo em alta
- `GET /api/content/recommendations` - Recomendações personalizadas

### Health Check
- `GET /health` - Status da aplicação e conexão com AWS RDS
- `GET /` - Informações da API

## Monitoramento

- **Health Check**: `GET /health` - Inclui status da conexão AWS RDS
- **Logs**: Disponíveis no Railway dashboard
- **Database**: Monitoramento via AWS CloudWatch

## Backup e Segurança

- **AWS RDS**: Backups automáticos configurados
- **SSL**: Conexões criptografadas obrigatórias
- **Senhas**: Hasheadas com Werkzeug
- **JWT**: Tokens seguros para autenticação

