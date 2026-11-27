# Monitor de passagens aéreas

Consulta preços do Google Flights 3 vezes ao dia e envia um e-mail quando encontra passagens abaixo do valor definido.

## O que é usado

- **[Render](https://render.com)**: executa o script como Cron Job.
- **[SerpApi](https://serpapi.com)**: fornece os resultados do Google Flights. O script não acessa o site diretamente.
- **Gmail**: envia o alerta, usando uma senha de app.
- **GitHub**: guarda o código que o Render executa.

## Arquivos

| Arquivo | Função |
|---|---|
| `monitor.py` | Faz as buscas e envia o e-mail |
| `config.json` | Viagens, datas e preço máximo |
| `requirements.txt` | Exigido pelo comando de build (não há dependências externas) |

## Configuração no Render

| Campo | Valor |
|---|---|
| Tipo de serviço | Cron Job |
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Command | `python monitor.py` |
| Schedule | `0 2,12,18 * * *` |
| Instance Type | 512 MB |
| Auto-Deploy | On Commit |

O Render usa UTC. O agendamento acima corresponde a **09h, 15h e 23h de Brasília**.

## Exemplo de `config.json`

```json
{
  "buscas_por_execucao": 2,
  "voos": [
    {
      "origem": "GIG",
      "destino": "POA",
      "data_ida": "2026-12-18",
      "data_ida_ate": "2026-12-20",
      "data_volta": "2026-12-27",
      "data_volta_ate": "2026-12-29",
      "adultos": 1,
      "preco_maximo": 4000
    }
  ]
}
```

| Campo | Significado |
|---|---|
| `origem`, `destino` | Códigos dos aeroportos |
| `data_ida`, `data_ida_ate` | Primeira e última data de ida (`AAAA-MM-DD`) |
| `data_volta`, `data_volta_ate` | Primeira e última data de volta |
| `adultos` | Número de passageiros adultos |
| `preco_maximo` | Alerta para preços **abaixo** deste valor, em reais |
| `buscas_por_execucao` | Combinações consultadas por viagem em cada execução |

Para uma data única, remova o campo `_ate`. Para só ida, remova `data_volta` e `data_volta_ate`.

## Quantas datas podem ser consultadas

**Recomendado: até 3 datas de ida e 3 de volta por viagem.** O script não bloqueia intervalos maiores.

O exemplo gera 9 combinações:

| Ida \ Volta | 27/12 | 28/12 | 29/12 |
|---|---|---|---|
| **18/12** | 1 | 2 | 3 |
| **19/12** | 4 | 5 | 6 |
| **20/12** | 7 | 8 | 9 |

As combinações são consultadas em rodízio. Com 2 por execução, todas são verificadas em cerca de 1 dia e meio. Intervalos maiores aumentam esse tempo.

## Limites de uso e custos

Valores consultados em 27/11/2026. Confira as páginas oficiais, pois podem mudar.

### SerpApi (plano gratuito)

- 250 buscas por mês e até 50 por hora.
- Cada combinação de datas consultada é uma busca.

| Viagens | `buscas_por_execucao` | Buscas em um mês de 31 dias | Cabe no plano grátis? |
|---|---|---|---|
| 1 | 2 | até 186 | Sim |
| 2 | 1 | até 186 | Sim |
| 2 | 2 | até 372 | Não |
| 1 | 3 | até 279 | Não |

Execuções manuais (**Trigger Run**) também consomem buscas.

### Render

- Workspace Hobby: US$ 0.
- Cron Job: mínimo de US$ 1 por mês, sem contar impostos e câmbio.

Referências: [preços da SerpApi](https://serpapi.com/pricing), [preços do Render](https://render.com/pricing) e [Cron Jobs no Render](https://render.com/docs/cronjobs).

## Como testar

1. Faça o commit e aguarde o deploy.
2. No Render, abra **Runs → Trigger Run**.
3. Confira nos logs as datas consultadas e a quantidade de ofertas.

O e-mail só é enviado quando há oferta abaixo do limite. O assunto é **"Passagem abaixo do seu limite"**.

## Observações

- Enquanto houver preço abaixo do limite, o alerta pode se repetir.
- Cada e-mail traz apenas as combinações consultadas naquela execução.
- Confirme o preço no Google Flights antes de comprar.
