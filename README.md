# Mob (TemAi)

Marketplace Django para descobrir produtos e estabelecimentos locais.

## Requisitos

- Python 3.12+ (ver `runtime.txt`)
- MySQL 8+ em execução local (`127.0.0.1:3306`)

## Arranque rápido (Windows)

```powershell
cd W:\GitHub\TemAi
.\scripts\setup_local.ps1
.\scripts\run_local.ps1
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Testar no telemóvel (hotspot)

1. Ativa o **Hotspot Wi-Fi** no telemóvel e liga o notebook a essa rede.
2. Descobre o IP do notebook:

```powershell
ipconfig
```

Procura em **Wireless LAN adapter Wi-Fi** o `IPv4 Address` (ex.: `192.168.43.120`).

3. Edita o ficheiro `.env` e adiciona o teu IP:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.43.120
CSRF_TRUSTED_ORIGINS=http://192.168.43.120:8000
```

Substitui `192.168.43.120` pelo IP real do teu notebook.

4. Inicia o servidor na rede:

```powershell
.\scripts\run_network.ps1
```

Ou manualmente:

```powershell
python manage.py runserver 0.0.0.0:8000
```

5. No telemóvel, abre no navegador:

```
http://192.168.43.120:8000/
```

> **Nota:** O `CSRF_TRUSTED_ORIGINS` é necessário para login e formulários funcionarem pelo IP. Só usa `ALLOWED_HOSTS=*` em testes rápidos — não é recomendado.

## Arranque manual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edita .env com a senha do teu MySQL

python manage.py setup_database
python manage.py runserver
```

## Variáveis de ambiente (local)

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Chave Django |
| `DEBUG` | `True` em desenvolvimento |
| `DB_NAME` | Nome da base (default: `mob`) |
| `DB_USER` | Utilizador MySQL |
| `DB_PASSWORD` | Senha MySQL |
| `DB_HOST` | Host MySQL (default: `127.0.0.1`) |
| `DB_PORT` | Porta MySQL (default: `3306`) |

Em produção (Render), a app usa `DATABASE_URL` (PostgreSQL). Não defines `DATABASE_URL` em local — o MySQL é usado automaticamente.

## Estrutura

```
apps/          # Django apps (main, vendor, admin_panel)
config/        # settings, urls, wsgi
scripts/       # setup e arranque local (PowerShell)
docs/          # guia de utilização (opcional)
```

## Comandos úteis

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py assign_admin email@exemplo.com
python manage.py test
```

## Upload de imagens

Sem credenciais Cloudinary, os ficheiros são guardados em `media/`. Em produção, configura `CLOUDINARY_*` no painel do Render.
