from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_httpauth import HTTPBasicAuth
import subprocess
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

USERS = {
    "admin": "Hu82+1265"
}

@auth.verify_password
def verify_password(username, password):
    return USERS.get(username) == password

@app.route("/")
@auth.login_required
def index():
    status = subprocess.run(
        ["systemctl", "is-active", "openvpn-server@manual"],
        capture_output=True,
        text=True
    ).stdout.strip()

    if status == "active":
        status = "ONLINE"
    else:
        status = "OFFLINE"

    return render_template("index.html", status=status)


@app.route("/clientes")
@auth.login_required
def clientes():
    pasta = "/etc/openvpn/manual-easy-rsa/pki/issued"

    online = {}
    lista = []

    online_text = subprocess.run(
        ["sudo", "cat", "/run/openvpn-server/manual-status.log"],
        capture_output=True,
        text=True
    ).stdout

    for linha in online_text.splitlines():
        if linha.startswith("CLIENT_LIST"):
            partes = linha.split()
            if len(partes) >= 4:
                online[partes[1]] = partes[3]

    for f in os.listdir(pasta):
        if not f.endswith(".crt") or f == "server.crt":
            continue

        nome = f[:-4]

        estado = "ONLINE" if nome in online else "OFFLINE"
        ipvpn = online.get(nome, "-")

        rede = "-"

        ccd = f"/etc/openvpn/ccd/{nome}"
        if os.path.exists(ccd):
            redes = []

            with open(ccd) as ficheiro:
                for linha in ficheiro:
                    linha = linha.strip()

                    if linha.startswith("ifconfig-push "):
                       partes = linha.split()
                       if len(partes) >= 2:
                           ipvpn = partes[1]

                    if linha.startswith("# rede_local="):
                        redes.append(linha.split("=",1)[1].strip())

                    elif linha.startswith("iroute"):
                        partes = linha.split()
                        if len(partes) >= 2:
                            redes.append(partes[1])

            if redes:
                rede = ", ".join(redes)

        lista.append({
            "nome": nome,
            "estado": estado,
            "ipvpn": ipvpn,
            "rede": rede
        })

    return render_template(
        "clientes.html",
        clientes=sorted(lista, key=lambda x: x["nome"].lower())
    )


from flask import request

@app.route("/criar", methods=["GET", "POST"])
@auth.login_required
def criar():
    if request.method == "POST":
        nome = request.form["nome"]
        tipo = request.form["tipo"]

        if tipo == "casa":
            rede = request.form["rede_casa"]
            subprocess.run([
                "sudo",
                "/usr/local/bin/criar-cliente-ovpn-web",
                nome,
                tipo,
                rede
            ])

        elif tipo == "fora":
            subprocess.run([
                "sudo",
                "/usr/local/bin/criar-cliente-ovpn-web",
                nome,
                tipo
            ])

        elif tipo == "glinet":
            redes = request.form["redes"]
            subprocess.run([
                "sudo",
                "/usr/local/bin/criar-cliente-ovpn-web",
                nome,
                tipo,
                redes
            ])

        return f"Cliente {nome} criado com sucesso.<br><br><a href='/clientes'>Ver clientes</a>"

    return render_template("criar.html")

@app.route("/download/<cliente>/<tipo>")
@auth.login_required
def download(cliente, tipo):
    import os

    if tipo == "vpn":
        ficheiro = f"/home/ubuntu/{cliente}.ovpn"
    elif tipo == "vps":
        ficheiro = f"/home/ubuntu/{cliente}-vps.ovpn"
    else:
        return "Tipo invÃƒÆ’Ã‚Â¡lido", 404

    if not os.path.exists(ficheiro):
        return "Ficheiro nÃƒÆ’Ã‚Â£o encontrado", 404

    return send_file(ficheiro, as_attachment=True)

@app.route("/apagar/<cliente>", methods=["POST"])
@auth.login_required
def apagar_cliente(cliente):
    subprocess.run(
        [
            "sudo",
            "/usr/local/bin/criar-cliente-ovpn-web",
            "remover",
            cliente,
        ],
        check=True,
    )
    return redirect(url_for("clientes"))

app.run(host="0.0.0.0", port=5000)

