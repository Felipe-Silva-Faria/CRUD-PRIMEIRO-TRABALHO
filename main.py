import argparse
import runpy
import sys

from utilitarios.auditoria import ativar_log_json
from utilitarios.log import configurar_logs


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRUD de Ativos de TI - versao 4.0")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--local", action="store_true", help="usa so o arquivo local, sem a API")
    grupo.add_argument("--classica", action="store_true", help="abre a interface antiga")
    args = parser.parse_args(argv)

    if args.classica:
        runpy.run_module("main_classico", run_name="__main__")
        return 0

    configurar_logs()
    ativar_log_json()
    from interface.moderna.inicializacao import iniciar

    iniciar(modo_local=args.local)
    return 0


if __name__ == "__main__":
    sys.exit(main())
