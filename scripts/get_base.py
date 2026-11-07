import json
import pandas as pd
with open("data/data.json", encoding="utf-8") as f:
    raw = json.load(f)
df = pd.DataFrame([
    {"nivel_m": float(nivel.removesuffix("m").replace("_", ".")), "bairro": bairro, **valores}
    for nivel, bairros in raw.items()
    for bairro, valores in bairros.items()
    ])

def limpeza_json_(json_):
    novo_json = {}
    aux = 0
    for bairro, val in json_['10_0m'].items():
        novo_json[bairro] = {
                            "total_buildings": val['total_buildings'],
                            "affected_buildings": [],
                            #"percentage": [],
                            "population": val['population'],
                            "affected_population": {}
                        }

    for nivel, bairros in json_.items():
        print(nivel)
        for bairro, valores in bairros.items():
            af_p = valores['affected_population']
            brr = novo_json[bairro]
            dict_afp = brr['affected_population']
            l_afb = brr['affected_buildings']
            if af_p > 0:
                if not dict_afp:
                    af_b = valores['affected_buildings']
                    
                    dict_afp[nivel] = af_p
                    l_afb.append(af_b)
                elif list(dict_afp.values())[-1] != af_p:
                    af_b = valores['affected_buildings']

                    dict_afp[nivel] = af_p
                    l_afb.append(af_b)
                
    with open("dados/dados_limpos.json", "w", encoding="utf-8") as arquivo:
        json.dump(novo_json, arquivo, indent=4, ensure_ascii=False)                    

                
                

limpeza_json_(raw)