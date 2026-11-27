"""Acorda o serviço e chama o scraper de concursos (substitui o workflow do GitHub Actions)."""
import sys
import time
import urllib.request

BASE = "https://concurso-monitor-9pm1.onrender.com"


def chamar(caminho):
    # urlopen gera exceção em respostas 4xx/5xx, como o curl --fail
    with urllib.request.urlopen(BASE + caminho, timeout=200) as resposta:
        return resposta.status


def main():
    try:
        print("Ping:", chamar("/"), flush=True)
    except Exception as erro:  # o ping só serve para acordar o serviço
        print("Ping falhou, seguindo:", erro, flush=True)

    for tentativa in range(1, 4):  # 1 tentativa + 2 repetições
        try:
            print("Scraper executado, status", chamar("/scraper/run"), flush=True)
            return
        except Exception as erro:
            print(f"Tentativa {tentativa} falhou: {erro}", flush=True)
            if tentativa < 3:
                time.sleep(15)
    sys.exit(1)


if __name__ == "__main__":
    main()