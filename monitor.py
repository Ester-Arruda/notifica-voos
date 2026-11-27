"""Consulta o Google Flights (via SerpApi) e envia e-mail quando o preço fica abaixo do limite."""
import json
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage


def buscar(voo):
    params = {
        "engine": "google_flights",
        "api_key": os.environ["SERPAPI_KEY"],
        "departure_id": voo["origem"],
        "arrival_id": voo["destino"],
        "outbound_date": voo["data_ida"],
        "type": "1" if voo.get("data_volta") else "2",  # 1 = ida e volta, 2 = só ida
        "adults": voo.get("adultos", 1),
        "currency": "BRL",
        "hl": "pt-br",
        "gl": "br",
        "deep_search": "true",  # resultados mais próximos dos exibidos no navegador
    }
    if voo.get("data_volta"):
        params["return_date"] = voo["data_volta"]
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as resposta:
        dados = json.load(resposta)
    if dados.get("error"):
        raise RuntimeError(dados["error"])
    return dados


def datas(inicio, fim):
    d = date.fromisoformat(inicio)
    ultima = date.fromisoformat(fim or inicio)
    if ultima < d:
        raise ValueError(f"intervalo de datas invertido: {inicio} até {fim}")
    while d <= ultima:
        yield d.isoformat()
        d += timedelta(days=1)


def combinacoes(voo, hoje):
    """Todas as combinações de ida e volta ainda válidas."""
    voltas = [None]
    if voo.get("data_volta"):
        voltas = list(datas(voo["data_volta"], voo.get("data_volta_ate")))
    return [
        {**voo, "data_ida": ida, "data_volta": volta}
        for ida in datas(voo["data_ida"], voo.get("data_ida_ate"))
        for volta in voltas
        if date.fromisoformat(ida) >= hoje and (volta is None or volta >= ida)
    ]


def lote(itens, tamanho, agora):
    """Reveza as combinações entre as execuções (02h, 12h e 18h UTC), sem guardar estado."""
    if len(itens) <= tamanho:
        return itens
    turno = 0 if agora.hour < 12 else 1 if agora.hour < 18 else 2
    inicio = (agora.date().toordinal() * 3 + turno) * tamanho
    return [itens[(inicio + i) % len(itens)] for i in range(tamanho)]


def ofertas_abaixo(dados, limite):
    todas = dados.get("best_flights", []) + dados.get("other_flights", [])
    boas = [o for o in todas if o.get("price") and o["price"] < limite]
    return sorted(boas, key=lambda o: o["price"])


def descrever(voo, ofertas, link):
    datas = voo["data_ida"] + (f" a {voo['data_volta']}" if voo.get("data_volta") else " (só ida)")
    linhas = [f"{voo['origem']} -> {voo['destino']} | {datas} | limite R$ {voo['preco_maximo']}"]
    for oferta in ofertas[:5]:
        trechos = oferta["flights"]
        companhias = ", ".join(sorted({t.get("airline", "?") for t in trechos}))
        saida = trechos[0]["departure_airport"].get("time", "?")
        linhas.append(
            f"  R$ {oferta['price']} | {companhias} | saída {saida} | {len(trechos) - 1} conexão(ões)"
        )
    linhas.append(f"  Ver no Google Flights: {link}")
    return "\n".join(linhas)


def enviar_email(corpo):
    remetente = os.environ["EMAIL_REMETENTE"]
    msg = EmailMessage()
    msg["Subject"] = "Passagem abaixo do seu limite"
    msg["From"] = remetente
    msg["To"] = os.environ.get("EMAIL_DESTINO") or remetente
    msg.set_content(corpo)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(remetente, os.environ["EMAIL_SENHA_APP"])
        smtp.send_message(msg)


def main():
    with open("config.json", encoding="utf-8") as arquivo:
        config = json.load(arquivo)
    por_execucao = config.get("buscas_por_execucao", 2)  # por viagem

    agora = datetime.now(timezone.utc)
    hoje = agora.astimezone(timezone(timedelta(hours=-3))).date()
    alertas, falhas = [], 0

    for viagem in config["voos"]:
        todas = combinacoes(viagem, hoje)
        if not todas:
            print(f"{viagem['origem']}-{viagem['destino']}: nenhuma data futura, ignorando")
            continue
        for voo in lote(todas, por_execucao, agora):
            rota = f"{voo['origem']}-{voo['destino']} ida {voo['data_ida']} volta {voo['data_volta']}"
            try:
                dados = buscar(voo)
                ofertas = ofertas_abaixo(dados, voo["preco_maximo"])
                print(f"{rota}: {len(ofertas)} oferta(s) abaixo de R$ {voo['preco_maximo']}")
                if ofertas:
                    link = dados.get("search_metadata", {}).get("google_flights_url", "")
                    alertas.append(descrever(voo, ofertas, link))
            except Exception as erro:  # uma busca com problema não impede as outras
                falhas += 1
                print(f"{rota}: erro na consulta: {erro}")

    if alertas:
        enviar_email("\n\n".join(alertas))
        print("E-mail enviado")
    if falhas:
        sys.exit(1)  # marca a execução como falha no GitHub


if __name__ == "__main__":
    main()