from flask import Flask, request, send_from_directory, render_template, Response
from flask_restful import Resource, Api
#from sqlalchemy import create_engine
import sqlite3
from json import dumps
from flask.ext.jsonpify import jsonify
import funcoes
import sys
from subprocess import call
from os import walk
server_path = '/home/daniel/Desktop/sarra'
sys.path.append(server_path)
import execSimul
id_simulacao = 0

path_simulacoes = server_path + "/simulacoes"
db_path = server_path + "/sarra.db"

estados_centroides = [('AC',-9.032,-70.620),('AL',-9.813,-36.782),('AM',-4.407,-64.116),('AP',1.476,-51.636),('BA',-12.486,-41.353),('CE',-5.327,-39.594),('DF',-15.767,-47.681),('ES',-19.783,-40.474),('GO',-16.358,-49.878),('MA',-5.415,-45.483),('MG',-18.704,-44.648),('MS',-20.690,-55.020),('MT',-12.915,-55.898),('PA',-4.75,-52.426),('PB',-7.380,-36.958),('PE',-8.250,-38.057),('PI',-7.336,-42.407),('PR',-24.863,-51.636),('RJ',-22.407,-42.539),('RN',-5.983,-36.650),('RO',-11.325,-63.105),('RR',1.432,-61.303),('RS',-29.551,-53.086),('SC',-26.957,-51.020),('SE',-10.461,-37.397),('SP',-22.401,-48.691),('TO',-10.030,-48.296)]

#socket_path = "sqlite:///" + db_path
#db_connect = create_engine(socket_path)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

app = Flask(__name__)
api = Api(app)



#conn = db_connect.connect()
#query_culturas = conn.execute('''
query_culturas = cursor.execute('''
SELECT cultura.nome, configuracaoRegional.nomeConfiguracao, configuracaoRegional.id, grupo.nome, grupo.ID
FROM cultura, configuracaoRegional, grupo
WHERE cultura.id = configuracaoRegional.culturaID
AND configuracaoRegional.id = grupo.culturaRegiao
''')

tuplas_culturas = cursor.fetchall()
frase_culturas = ""
for tupla in tuplas_culturas:
    frase_culturas = frase_culturas + str(tupla[0]) + ",," +  str(tupla[1]) + ",," +  str(tupla[2]) + ",," + str(tupla[3]) + ",," + str(tupla[4]) + ";;"


#query_estados = conn.execute('''
query_estados = cursor.execute('''
SELECT estado.sigla
FROM estado
''')


tuplas_estados = cursor.fetchall()
frase_estados = ""
for tupla in tuplas_estados:
    frase_estados = frase_estados + str(tupla[0]) + ","

conn.close()

class Principal(Resource):
    def get(self):
        pagina = render_template('index.html')
        return Response(pagina, mimetype='text/html')

class DispSim(Resource):
    def get(self):
        pagina = render_template('dispsim.html',tuplas_culturas=frase_culturas,tuplas_estados=frase_estados)
        return Response(pagina, mimetype='text/html')

    def post(self):
        estado = request.form.get('estados')
        inisim = request.form.get('datainisim')
        dataplan = request.form.get('dataplantio')
        anos = request.form.get('anos')
        solo = request.form.get('solo')
        cultura = request.form.get('culturas')
        confreg = request.form.get('confreg')
        grupo = request.form.get('grupo')
        estoqueini = request.form.get('estoqueini')
        chuvalim = request.form.get('chuvalimite')
        mulch = request.form.get('mulch')
        rusurf = request.form.get('rusurf')
        cad = request.form.get('reservautil')
        escsup = request.form.get('escoamentosup')

        for tupla in tuplas_culturas:
        	if tupla[0] == cultura and tupla[1] == confreg and tupla[3] == grupo:
        	        idgrupo = tupla[4]


        inisim_mes,inisim_dia = inisim.split("/")
        dataplan_mes,dataplan_dia = inisim.split("/")
        anoini,anofinal = anos.split(":")
        inisim = '2000-' + inisim_mes + '-' + inisim_dia
        dataplan = '2000-' + dataplan_mes + '-' + dataplan_dia
        anos = [ano for ano in range(int(anoini),int(anofinal))]
        execSimul.simular(estado, inisim, dataplan, solo, idgrupo, estoqueini, chuvalim, mulch, rusurf, cad, escsup, anos,db_path,'agritempo')


class Analise(Resource):
    def get(self):
        data_paths = []

        for (dirpath, dirnames, filenames) in walk(path_simulacoes):
            culturas = dirnames
            break
        for cultura in culturas:
            cult_path = path_simulacoes + '/' + cultura
            for (dirpath, dirnames, filenames) in walk(cult_path):
                estados = dirnames
                break
            for estado in estados:
                estado_path = cult_path + '/' + estado
                for (dirpath, dirnames, filenames) in walk(estado_path):
                    dadosmeteoro = dirnames
                    break
                for dado in dadosmeteoro:
                    dado_path = estado_path + '/' + dado
                    for (dirpath, dirnames, filenames) in walk(dado_path):
                        datasini = dirnames
                        break
                    for data in datasini:
                        data_paths.append([cultura,estado,dado,data])

        frase_data_paths = ""
        for tupla in data_paths:
            frase_data_paths = frase_data_paths + str(tupla[0]) + ",," +  str(tupla[1]) + ",," +  str(tupla[2]) + ",," + str(tupla[3]) + ";;"


        pagina = render_template('analise.html',data_paths=frase_data_paths)
        return Response(pagina, mimetype='text/html')

    def post(self):
        global id_simulacao
        id_simulacao = id_simulacao + 1
        arquivo_csv = "EtrEtmInter_"+str(id_simulacao)+".csv"
        cultura = request.form.get('culturas')
        estado = request.form.get('estados')
        dado = request.form.get('dados')
        inisim = request.form.get('inisim')
        interpolacao = request.form.get('interp')
        opcao = request.form.get('opcao')
        path_res = path_simulacoes + "/" + cultura + "/" + estado + "/" + dado + "/" + inisim
        for estado_c in estados_centroides:
            if(estado_c[0]==estado):
                centroide = estado_c
        output_path = server_path + "/interfaces/templates/"
        path_res_csv = path_res + "/total.csv"
        script_interp_r = server_path + "/interfaces/templates/interp.R"
        call(["Rscript", script_interp_r , path_res_csv, estado, arquivo_csv,interpolacao,server_path,output_path,db_path])

        if(opcao=="Download"):
            path_file = server_path + "/interfaces/templates/"
            return send_from_directory(directory=path_file, filename=arquivo_csv)
        else:
            sigla="BR."+estado
            pagina = render_template('mapgen.html',centroide_lat=str(centroide[1]),centroide_long=str(centroide[2]),arquivo_csv=arquivo_csv,estado=sigla)
            return Response(pagina, mimetype='text/html')

class brasil_json(Resource):
    def get(self):
        file_path = server_path + "/interfaces/templates"
        return send_from_directory(directory=file_path, filename="BRA_adm1.json")
class etretminter(Resource):
    def get(self,etretm):
        file_path = server_path + "/interfaces/templates"
        return send_from_directory(directory=file_path, filename=etretm)

app.url_map.converters['etretm'] = etretminter
api.add_resource(Principal, '/') # Route_1
api.add_resource(DispSim, '/dispara_simulacao')
api.add_resource(Analise, '/analise')
api.add_resource(brasil_json, '/BRA_adm1.json')
api.add_resource(etretminter, '/<etretm>')


if __name__ == '__main__':
    app.run(port='5002')
