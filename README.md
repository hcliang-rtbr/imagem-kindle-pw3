# kindle-dash-clima

Gera automaticamente uma imagem de previsão do tempo para um Kindle jailbroken usar como painel e-ink. O GitHub Actions roda o script a cada 30 minutos, commita o `dash.png` no repositório, e o Kindle busca essa imagem por HTTPS.

Sem servidor próprio, sem notebook ligado, custo zero.

---

## Resolução

| Modelo | Largura | Altura |
|---|---|---|
| Paperwhite 3 (300 ppi) | 1072 | 1448 |
| Paperwhite 2 (212 ppi) | 758 | 1024 |

O padrão é PW3. Para PW2, altere no topo do `generate_dash.py`:

```python
LARGURA = 758
ALTURA = 1024
```

Para conferir a resolução do seu aparelho, rode `eips -i` no Kindle.

---

## Instalação

### 1. Criar o repositório

1. No GitHub, clique em **New repository**.
2. Nome: `kindle-dash-clima`. Visibilidade: **Public** (necessário para o Kindle baixar sem autenticação).
3. Crie o repositório.

### 2. Enviar os arquivos

Use **Add file → Upload files** e envie:

```
generate_dash.py
README.md
.github/workflows/dash.yml
```

Para criar a pasta do workflow pela interface web, use **Add file → Create new file** e digite o caminho completo `.github/workflows/dash.yml` — o GitHub cria as pastas automaticamente ao digitar as barras.

### 3. Liberar a escrita para o Actions

Em **Settings → Actions → General → Workflow permissions**, marque **Read and write permissions** e salve. Sem isso o workflow não consegue commitar a imagem.

### 4. Rodar a primeira vez

Vá em **Actions → Gerar dashboard → Run workflow**. Ao terminar, o arquivo `dash.png` aparece na raiz do repositório.

### 5. Sua URL

```
https://raw.githubusercontent.com/SEU-USUARIO/kindle-dash-clima/main/dash.png
```

Abra no navegador para confirmar que a imagem carrega.

### 6. Apontar o Kindle

Edite `dashboard/local/fetch-dashboard.sh` no Kindle deixando apenas:

```sh
#!/usr/bin/env sh
"$(dirname "$0")/../xh" -d -q -o "$1" get https://raw.githubusercontent.com/SEU-USUARIO/kindle-dash-clima/main/dash.png
```

Salve em **UTF-8 sem BOM** com fim de linha **Unix (LF)**. No Notepad++: *Formatar → Converter para UTF-8 sem BOM* e *Editar → Conversão final de linha → Converter para formato UNIX*.

Ejete o Kindle, reinicie e abra **KUAL → kindle-dash → Start**.

---

## Personalização

Tudo fica no topo do `generate_dash.py`:

```python
LATITUDE = -23.0903            # troque de cidade aqui
LONGITUDE = -47.2181
CIDADE = "INDAIATUBA - SP"
TZ_NOME = "America/Sao_Paulo"
TZ_OFFSET = -3                 # apenas o relogio do cabecalho
```

Coordenadas de qualquer cidade: https://open-meteo.com/en/docs (campo de busca por nome).

Para mudar a frequência, edite o `cron` em `.github/workflows/dash.yml`. O horário é **UTC**, não horário de Brasília.

---

## Observações

- O agendamento do GitHub Actions não é pontual: atrasos de alguns minutos são normais, e em períodos de fila o intervalo pode esticar.
- A API Open-Meteo atualiza os dados de hora em hora, então intervalos menores que 60 minutos não trazem informação nova.
- Repositórios públicos têm Actions gratuito sem limite de minutos.
- O commit automático gera histórico. Se incomodar, o `dash.png` pode ser publicado via GitHub Pages a partir de um branch separado.

## Fonte dos dados

Previsão: [Open-Meteo](https://open-meteo.com/) — API gratuita, sem cadastro nem chave.
