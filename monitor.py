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
        voos = json.load(arquivo)["voos"]

    hoje = datetime.now(timezone(timedelta(hours=-3))).date()
    alertas, falhas = [], 0

    for voo in voos:
        rota = f"{voo['origem']}-{voo['destino']} {voo['data_ida']}"
        if date.fromisoformat(voo["data_ida"]) < hoje:
            print(f"{rota}: data já passou, ignorando")
            continue
        try:
            dados = buscar(voo)
            ofertas = ofertas_abaixo(dados, voo["preco_maximo"])
            print(f"{rota}: {len(ofertas)} oferta(s) abaixo de R$ {voo['preco_maximo']}")
            if ofertas:
                link = dados.get("search_metadata", {}).get("google_flights_url", "")
                alertas.append(descrever(voo, ofertas, link))
        except Exception as erro:  # uma rota com problema não impede as outras
            falhas += 1
            print(f"{rota}: erro na consulta: {erro}")

    if alertas:
        enviar_email("\n\n".join(alertas))
        print("E-mail enviado")
    if falhas:
        sys.exit(1)  # marca a execução como falha no GitHub


if __name__ == "__main__":
    main()
