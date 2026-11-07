"""
FONTE: https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv
(OBS.: É NECESSÁRIO TER A BASE BAIXADA LOCALMENTE ANTES (O SCRIPT NÃO PUXA A API))

USO:
    python extrair_atlas_digital.py entrada.xlsx
    python extrair_atlas_digital.py entrada.xlsx -o saida.xlsx
    python extrair_atlas_digital.py base_grande.csv -o saida.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

UF = "RS"
DATA_INICIO = pd.Timestamp(year=2024, month=4, day=21)
DATA_FIM = pd.Timestamp(year=2024, month=5, day=21)

COL_UF = "Sigla_UF"
COL_DATA_EVENTO = "Data_Evento"
COL_DATA_REGISTRO = "Data_Registro"

FORMATO_DATA = "%m/%d/%Y"
FORMATO_DATA_EXCEL = "mm/dd/yyyy"

COLUNAS_TEXTO = ["Protocolo_S2iD", "Setores Censitários"]

TEXTO_NULL = "(null)"


def converter_data(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    return pd.to_datetime(serie, format=FORMATO_DATA, errors="coerce")


def ler_arquivo(caminho: Path) -> pd.DataFrame:
    sufixo = caminho.suffix.lower()
    if sufixo in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(caminho, dtype={c: str for c in COLUNAS_TEXTO})
    if sufixo in (".csv", ".txt"):
        return pd.read_csv(caminho, dtype={c: str for c in COLUNAS_TEXTO},
                           sep=None, engine="python", encoding_errors="replace")
    sys.exit(f"Formato não suportado: {sufixo}")


def padronizar_nomes_colunas(df: pd.DataFrame) -> pd.DataFrame:
    mapa = {}
    for alvo in (COL_UF, COL_DATA_EVENTO, COL_DATA_REGISTRO):
        for c in df.columns:
            if str(c).strip().lower() == alvo.lower() and c != alvo:
                mapa[c] = alvo
    return df.rename(columns=mapa)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path, help="arquivo de entrada (.xlsx ou .csv)")
    ap.add_argument("-o", "--saida", type=Path, default=None,
                    help="arquivo de saída (padrão: <entrada>_RS_abr-mai2024.xlsx)")
    args = ap.parse_args()

    if not args.entrada.exists():
        sys.exit(f"Arquivo não encontrado: {args.entrada}")

    saida = args.saida or args.entrada.with_name(
        f"{args.entrada.stem}_RS_abr-mai2024.xlsx")

    df = padronizar_nomes_colunas(ler_arquivo(args.entrada))

    for col in (COL_UF, COL_DATA_EVENTO):
        if col not in df.columns:
            sys.exit(f"Coluna obrigatória ausente: {col}\n"
                     f"Colunas encontradas: {list(df.columns)}")

    total = len(df)

    df[COL_DATA_EVENTO] = converter_data(df[COL_DATA_EVENTO])

    invalidas = df[COL_DATA_EVENTO].isna().sum()
    if invalidas:
        print(f"Aviso: {invalidas} linha(s) com {COL_DATA_EVENTO} vazia/inválida "
              f"(serão excluídas).")

    eh_rs = df[COL_UF].astype(str).str.strip().str.upper() == UF
    data = df[COL_DATA_EVENTO].dt.normalize()
    no_periodo = data.between(DATA_INICIO, DATA_FIM)

    resultado = df[eh_rs & no_periodo].copy()

    for col in resultado.select_dtypes(include=["object", "string"]).columns:
        em_branco = resultado[col].astype(str).str.strip() == ""
        resultado.loc[em_branco & resultado[col].notna(), col] = pd.NA


    if saida.suffix.lower() == ".csv":
        for col in resultado.columns:
            if pd.api.types.is_datetime64_any_dtype(resultado[col]):
                resultado[col] = resultado[col].dt.strftime(FORMATO_DATA)
        resultado.to_csv(saida, index=False, encoding="utf-8-sig", na_rep=TEXTO_NULL)
    else:
        with pd.ExcelWriter(saida, engine="openpyxl") as writer:
            resultado.to_excel(writer, index=False, sheet_name="RS_abr-mai2024",
                              na_rep=TEXTO_NULL)
            ws = writer.sheets["RS_abr-mai2024"]
            for idx, col in enumerate(resultado.columns, start=1):
                if pd.api.types.is_datetime64_any_dtype(resultado[col]):
                    for linha in range(2, len(resultado) + 2):
                        ws.cell(row=linha, column=idx).number_format = FORMATO_DATA_EXCEL

    print(f"Linhas lidas:        {total}")
    print(f"Linhas extraídas:    {len(resultado)}")
    print(f"Arquivo gerado:      {saida}")


if __name__ == "__main__":
    main()