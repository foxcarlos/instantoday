#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from daemon import runner
import os
import sys
import dbf
import datetime
from rutinas.varias import *
import zmq
import ConfigParser
import urllib
import urllib2

class smsCitas():
    def __init__(self):

        self.nombreArchivoConf = 'dt.cfg'
        self.fc = ConfigParser.ConfigParser()

        #Propiedades de la Clase
        self.archivoLog = ''
        self.tiempo = 10

        self.configInicial()
        self.configDemonio()
        # self.configPG()

    def configInicial(self):
        '''Metodo que permite extraer todos los parametros
        del archivo de configuracion pyloro.cfg que se
        utilizara en todo el script'''

        #Obtiene Informacion del archivo de Configuracion .cfg
        self.ruta_arch_conf = os.path.dirname(sys.argv[0])
        self.archivo_configuracion = os.path.join(self.ruta_arch_conf, self.nombreArchivoConf)
        self.fc.read(self.archivo_configuracion)

        #Obtiene el nombre del archivo .log para uso del Logging
        seccion = 'RUTAS'
        opcion = 'archivo_log'
        self.archivoLog = self.fc.get(seccion, opcion)

    def configDemonio(self):
        '''Configuiracion del Demonio'''

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/tmp/dolartoday.pid'
        self.pidfile_timeout = 5

    def configLog(self):
        '''Metodo que configura los Logs de error tanto el nombre
        del archivo como su ubicacion asi como tambien los
        metodos y formato de salida'''

        #Extrae de la clase la propiedad que contiene el nombre del archivo log
        nombreArchivoLog = self.archivoLog
        self.logger = logging.getLogger("DolarToDay")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s--> %(asctime)s - %(name)s:  %(message)s", datefmt='%d/%m/%Y %I:%M:%S %p')
        handler = logging.FileHandler(nombreArchivoLog)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        return handler

    def enviarWebService(self, numero, mensaje):
        ''' parametros 2, (string:NumeroTelefono, string:MensajeSMS)
        Metodo que permite enviar via web service a pyLoroWeb un SMS
        a cualquier telefono movil
        '''

        print(numero, mensaje)
        url = 'http://10.121.6.12/mensaje'
        data = urllib.urlencode({'numero' : numero, 'mensaje'  : mensaje})
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        respuesta = response.read()
        return respuesta

    def enviarSocket(self, registros, campoTabla):
        '''Parametros 2: (tupla, string):
        (Registros, "String:Nombre del Campo de la Tabla que se actualizara")

        Este Metodo recorre una lista de las personas que se le enviara el
        mensaje SMS de Cita Nueva, Recordatorio o Cita Cancelada para
        luego enviarla via ip por Socket a (el o los) Servidores serverZMQ
        NOTA: Cuando se envia al ServidorZMQ este devuelve mediante self.socket.recv()
        ('1') si todo salio bien o ('0') en caso de fallar'''

        pg = ConectarPG(self.cadconex)

        for fila in registros:
            id, numero, mensaje = fila
            msg = '{0}^{1}'.format(numero, mensaje)

            #Se extrae y muestra en el .log solo una parte del mensaje
            self.logger.info(msg[:100])

            noEnviado = self.enviarWebService(numero, mensaje)
            nombreServidor = 'http://10.121.6.12/mensaje'

            # Antes el nombre del servidor lo devolvia self.socket.recv() ahora no
            #self.logger.info(noEnviado)

            if int(noEnviado):
                #POSTGRES
                cad_update = "update med_citas_consulta set %s =\
                    '%s' where id = %s" % \
                    (campoTabla, datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S'), id)
                try:
                    pg.ejecutar(cad_update)
                    pg.conn.commit()
                except:
                    logger.error('Ocurrio un error al momento de actualizar la tabla')
                time.sleep(self.tiempo)
                # FIN POSTGRES
            else:
                self.logger.warn('Houston Tenemos un Problema con el ID:{0},\
                    no se pudo enviar el SMS dede el Servidor {1}'.format(id, nombreServidor))

        pg.cur.close()
        pg.conn.close()

    def hoy(self):
        '''Metodo que permite procesar y enviar sms a los pacientes que
        han tomado citas nuevas'''

        self.logger.info('Proceso Iniciado <Citas Nuevas>')
        r = self.consultarCitasNuevas()
        final = self.procesarCitas(r, 'nuevas')
        self.enviarSocket(final, 'sms_fecha_cita_nueva')
        self.logger.info('Proceso Terminado <Citas Nuevas>')
        return True


    def run(self):
        ''' Este metodo es el que permite ejecutar el hilo del demonio'''

        #En Desuso
        #self.zmqConectar()
        while True:
            self.logger.debug("Debug message")
            #self.logger.info("Info message")
            #self.logger.warn("Warning message")
            #self.logger.error("Error message")

            self.cancelar()
            time.sleep(60)

            self.hoy()
            time.sleep(60)

            self.recordar()
            time.sleep(60)

#Instancio la Clase
app = smsCitas()
handler = app.configLog()
daemon_runner = runner.DaemonRunner(app)

#Esto garantiza que el identificador de archivo logger no quede cerrada durante daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
