import requests
import json

# Configurações da API do Zabbix
zabbix_url = "https://zabbix-ti.redeunifique.com.br/api_jsonrpc.php"
zabbix_token = "096c9437b2b8da68487da4095bbd6f48dd9964318e4810a348b4eee385c93a63"

# Lista de host groups que você quer consultar
host_groups = [
    "UNIFIQUE/5G-CORE/SERVIDORES/LINUX", "UNIFIQUE/CGR/SERVIDORES/LINUX",
    "UNIFIQUE/DEV-5G-BOSS/SERVIDORES/LINUX", "UNIFIQUE/DEV-CORPORATIVO/SERVIDORES/LINUX",
    "UNIFIQUE/DEV-SUSTENTACAO/SERVIDORES/LINUX", "UNIFIQUE/MONITORAMENTO/SERVIDORES/LINUX",
    "UNIFIQUE/SUPORTE/SERVIDORES/LINUX", "UNIFIQUE/TELEFONIA/SERVIDORES/LINUX",
    "UNIFIQUE/TI/SERVIDORES/LINUX"
]

headers = {
    "Content-Type": "application/json-rpc"
}

# Função para obter o ID do grupo pelo nome
def get_group_id(group_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": ["groupid"],
            "filter": {"name": [group_name]}
        },
        "auth": zabbix_token,
        "id": 1
    }
    response = requests.post(zabbix_url, data=json.dumps(payload), headers=headers)
    result = response.json()["result"]
    return result[0]["groupid"] if result else None

# Criar estrutura de inventário dinâmico
inventory = {
    "_meta": {
        "hostvars": {}
    }
}

for group in host_groups:
    group_id = get_group_id(group)
    if not group_id:
        print(f"Grupo '{group}' não encontrado no Zabbix.")
        continue

    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "name"],
            "groupids": group_id,
            "selectInterfaces": ["ip"],
            "selectTags": "extend",
            "searchWildcardsEnabled": 1,
            "tags": [
                {"tag": "CLIENTE", "value": "UNIFIQUE"},
                {"tag": "TIPO", "value": "SERVIDORES"},
                {"tag": "SO", "value": "LINUX"}
            ]
        },
        "auth": zabbix_token,
        "id": 1
    }

    response = requests.post(zabbix_url, data=json.dumps(payload), headers=headers)
    hosts = response.json()["result"]

    group_key = group.lower().replace(" ", "_")
    inventory[group_key] = {"hosts": []}

    for host in hosts:
        visible_name = host.get("name", host["host"])  # usa o nome visível se disponível
        ip = host["interfaces"][0]["ip"] if host.get("interfaces") else None
        if ip:
            inventory[group_key]["hosts"].append(ip)
            inventory["_meta"]["hostvars"][ip] = {"hostname": visible_name}

# Salvar em arquivo JSON
with open("inventario_awx.json", "w") as f:
    json.dump(inventory, f, indent=2)

print("Inventário salvo como 'inventario_awx.json'")
