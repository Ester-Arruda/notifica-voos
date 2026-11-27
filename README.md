# Monitor de passagens aéreas

Consulta preços do Google Flights 2 vezes ao dia e envia um e-mail quando encontra passagens abaixo do valor definido.

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
| Schedule | `0 0,12 * * *` |
| Instance Type | 512 MB |
| Auto-Deploy | On Commit |

O Render usa UTC. O agendamento acima corresponde a **09h e 21h de Brasília**.

## Exemplo de `config.json`

```json
{
  "buscas_por_execucao": 4,
  "voos": [
    {
      "origem": "GIG",
      "destino": "POA",
      "data_ida": "2026-12-18",
      "data_ida_ate": "2026-12-19",
      "data_volta": "2026-12-27",
      "data_volta_ate": "2026-12-28",
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

**Configuração atual: 2 datas de ida e 2 de volta por viagem**, que dão 4 combinações. Como `buscas_por_execucao` também é 4, todas as combinações são consultadas em **cada** execução, sem rodízio.

| Ida \ Volta | 27/12 | 28/12 |
|---|---|---|
| **18/12** | 1 | 2 |
| **19/12** | 3 | 4 |

Com 2 execuções ao dia, são 8 buscas por dia e cada combinação é verificada a cada cerca de 12 horas.

Se quiser comparar mais datas, o script não bloqueia intervalos maiores. Com 3 ida × 3 volta (9 combinações) e `buscas_por_execucao: 4`, as combinações passam a ser consultadas em rodízio, e cada uma é verificada a cada cerca de 27 horas. O consumo de buscas é o mesmo.

## Limites de uso e custos

Valores consultados em 27/11/2026. Confira as páginas oficiais, pois podem mudar.

### SerpApi (plano gratuito)

- 250 buscas por mês e até 50 por hora.
- Cada combinação de datas consultada é uma busca.

| Viagens | `buscas_por_execucao` | Buscas em um mês de 31 dias | Cabe no plano grátis? |
|---|---|---|---|
| 1 | 4 | até 248 | Sim, quase sem sobra |
| 1 | 3 | até 186 | Sim |
| 2 | 2 | até 248 | Sim, quase sem sobra |
| 2 | 1 | até 124 | Sim |
| 1 | 5 | até 310 | Não |
| 2 | 3 | até 372 | Não |

Execuções manuais (**Trigger Run**) também consomem buscas. Com a configuração atual (1 viagem, 4 por execução) sobram cerca de 2 buscas por mês, então um único teste manual já consome 4. Antes de testar, confira o saldo no painel da SerpApi. Se a cota acabar, o monitor para de consultar até ela renovar.

### Render

- Workspace Hobby: US$ 0.
- Cron Job: mínimo de US$ 1 por mês, sem contar impostos e câmbio.

Referências: [preços da SerpApi](https://serpapi.com/pricing), [preços do Render](https://render.com/pricing) e [Cron Jobs no Render](https://render.com/docs/cronjobs).

## Como testar

1. Faça o commit e aguarde o deploy.
2. No Render, abra **Runs → Trigger Run**.
3. Confira nos logs as datas consultadas e a quantidade de ofertas.

Cada Trigger Run consulta as 4 combinações e gasta 4 buscas.

O e-mail só é enviado quando há oferta abaixo do limite. O assunto é **"Passagem abaixo do seu limite"**.

## Observações

- Enquanto houver preço abaixo do limite, o alerta pode se repetir.
- Cada e-mail traz as 4 combinações consultadas naquela execução.
- Uma promoção que dure menos de 12 horas pode passar despercebida entre uma execução e outra.
- Confirme o preço no Google Flights antes de comprar.
