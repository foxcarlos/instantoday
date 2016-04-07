import requests
import json

def consultaParalelo():
    ''' '''
    r =  requests.get('https://s3.amazonaws.com/dolartoday/data.json')
    devuelto = r.json()
    valorTransfrencia = devuelto['USD']['transferencia']
    valorFecha = devuelto['_timestamp']['fecha']
    return valorTransfrencia, valorFecha

def notificar(numero='', mensaje=''):
    ''' '''

    if mensaje and numero:
        datos = {'numero': numero, 'mensaje': mensaje}
        url = 'http://foxcarlos.no-ip.biz/externo'
        cabecera = {'content-type': 'application/json'}

        sms = requests.post(url, data=json.dumps(datos), headers=cabecera)
        return sms

'''
    mensaje = 'El Valor del Dolar segun DolarToday es:{0}'.format(valorTransfrencia)
    datos = {'numero':'04246379541', 'mensaje':mensaje}
    url = 'http://foxcarlos.no-ip.biz/externo'
    cabecera = {'content-type': 'application/json'}

    sms = requests.post(url, data=json.dumps(datos), headers=cabecera)
    print(sms)'''
    #consultaParalelo()
