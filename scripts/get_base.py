import json

with open("dados/data.json", encoding="utf-8") as f:
    raw = json.load(f)

def perc_(x,total):
    return ((x*100)/total)/100

def limpeza_json_(json_):
    novo_json = {}
    for bairro, val in json_['10_0m'].items():
        novo_json[bairro] = {
                            "total_buildings": val['total_buildings'],
                            "affected_buildings": [],
                            "population": val['population'],
                            "affected_population": {}
                        }

    for nivel, bairros in json_.items():
        for bairro, valores in bairros.items():
            brr = novo_json[bairro]
            p = valores['population']
            total_b = valores['total_buildings']
            af_b = valores['affected_buildings']
            l_afb = brr['affected_buildings']
            dict_afp = brr['affected_population']
            if af_b > 0:
                perc = perc_(af_b,total_b)
                af_p = 0
                if not dict_afp:
                    af_p = round(p*perc)
                    dict_afp[nivel] = af_p
                    l_afb.append(af_b)
                elif l_afb[-1] != af_b:
                    af_p = round(p*perc)

                    dict_afp[nivel] = af_p
                    l_afb.append(af_b)
                
    with open("dados/dados_limpos.json", "w", encoding="utf-8") as arquivo:
        json.dump(novo_json, arquivo, indent=4, ensure_ascii=False)                    

                
                

limpeza_json_(raw)